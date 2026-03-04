from datetime import datetime
from .connection import get_db
from utils.security import hash_pw


# ═══════════════════════════════════════════════════════════════════
#  USER QUERIES
# ═══════════════════════════════════════════════════════════════════
class UserQueries:
    @staticmethod
    def authenticate(username: str, password: str) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hash_pw(password)),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all() -> list[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create(username: str, full_name: str, role: str, password: str) -> None:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, full_name, role, password) VALUES (?,?,?,?)",
            (username, full_name, role, hash_pw(password)),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update(user_id: int, username: str, full_name: str,
               role: str, password: str | None = None) -> None:
        conn = get_db()
        if password:
            conn.execute(
                "UPDATE users SET username=?, full_name=?, role=?, password=? WHERE id=?",
                (username, full_name, role, hash_pw(password), user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET username=?, full_name=?, role=? WHERE id=?",
                (username, full_name, role, user_id),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(user_id: int) -> None:
        conn = get_db()
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def change_password(user_id: int, new_password: str) -> None:
        conn = get_db()
        conn.execute(
            "UPDATE users SET password=? WHERE id=?",
            (hash_pw(new_password), user_id),
        )
        conn.commit()
        conn.close()


# ═══════════════════════════════════════════════════════════════════
#  PRODUCT QUERIES
# ═══════════════════════════════════════════════════════════════════
class ProductQueries:
    @staticmethod
    def get_all(search: str = "", category_id: int = 0) -> list[dict]:
        conn = get_db()
        sql = """SELECT p.*, c.name as cat_name
                 FROM products p
                 LEFT JOIN categories c ON p.category_id = c.id
                 WHERE p.active = 1"""
        params: list = []
        if category_id:
            sql += " AND p.category_id=?"
            params.append(category_id)
        if search:
            sql += " AND (LOWER(p.name) LIKE ? OR p.barcode LIKE ?)"
            params += [f"%{search.lower()}%", f"%{search}%"]
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_categories() -> list[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create(name: str, category_id: int, price: float, cost: float,
               stock: int, low_stock: int, unit: str, barcode: str | None) -> None:
        conn = get_db()
        conn.execute(
            """INSERT INTO products
               (name, category_id, price, cost, stock, low_stock, unit, barcode)
               VALUES (?,?,?,?,?,?,?,?)""",
            (name, category_id, price, cost, stock, low_stock, unit, barcode or None),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update(product_id: int, name: str, category_id: int, price: float,
               cost: float, stock: int, low_stock: int,
               unit: str, barcode: str | None) -> None:
        conn = get_db()
        conn.execute(
            """UPDATE products
               SET name=?, category_id=?, price=?, cost=?,
                   stock=?, low_stock=?, unit=?, barcode=?
               WHERE id=?""",
            (name, category_id, price, cost, stock, low_stock,
             unit, barcode or None, product_id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def deactivate(product_id: int) -> None:
        conn = get_db()
        conn.execute("UPDATE products SET active=0 WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def adjust_stock(product_id: int, change: int,
                     reason: str, user_id: int) -> None:
        conn = get_db()
        conn.execute(
            "UPDATE products SET stock = stock + ? WHERE id=?",
            (change, product_id),
        )
        conn.execute(
            """INSERT INTO inventory_log (product_id, change, reason, user_id)
               VALUES (?,?,?,?)""",
            (product_id, change, reason, user_id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_stock_log(product_id: int | None = None) -> list[dict]:
        conn = get_db()
        if product_id:
            rows = conn.execute(
                """SELECT l.*, p.name as pname, u.username
                   FROM inventory_log l
                   JOIN products p ON l.product_id = p.id
                   LEFT JOIN users u ON l.user_id = u.id
                   WHERE l.product_id = ?
                   ORDER BY l.created_at DESC LIMIT 200""",
                (product_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT l.*, p.name as pname, u.username
                   FROM inventory_log l
                   JOIN products p ON l.product_id = p.id
                   LEFT JOIN users u ON l.user_id = u.id
                   ORDER BY l.created_at DESC LIMIT 200"""
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_low_stock(limit: int = 15) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            """SELECT name, stock, low_stock FROM products
               WHERE active=1 AND stock <= low_stock
               ORDER BY stock ASC LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_inventory_stats() -> dict:
        conn = get_db()
        rows = conn.execute(
            "SELECT stock, low_stock, cost FROM products WHERE active=1"
        ).fetchall()
        conn.close()
        total = len(rows)
        low   = sum(1 for r in rows if 0 < r["stock"] <= r["low_stock"])
        out   = sum(1 for r in rows if r["stock"] == 0)
        value = sum(r["cost"] * r["stock"] for r in rows)
        return {"total": total, "low": low, "out": out, "value": value}


# ═══════════════════════════════════════════════════════════════════
#  ORDER QUERIES
# ═══════════════════════════════════════════════════════════════════
class OrderQueries:
    @staticmethod
    def next_order_no() -> str:
        conn = get_db()
        n = conn.execute("SELECT COUNT(*) as n FROM orders").fetchone()["n"] + 1
        conn.close()
        return f"ORD-{datetime.now().strftime('%Y%m%d')}-{n:04d}"

    @staticmethod
    def save_order(order_data: dict, cart_items: list[dict]) -> int:
        """
        Persist a new order + items; deduct stock; write inventory log.
        Returns the new order id.
        """
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute(
                """INSERT INTO orders
                   (order_no, cashier_id, subtotal, discount, tax_rate,
                    tax_amount, total, paid, change, payment_type, note)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    order_data["order_no"],
                    order_data["cashier_id"],
                    order_data["subtotal"],
                    order_data["discount"],
                    order_data["tax_rate"],
                    order_data["tax_amount"],
                    order_data["total"],
                    order_data["paid"],
                    order_data["change"],
                    order_data["payment_type"],
                    order_data["note"],
                ),
            )
            order_id = c.lastrowid

            for item in cart_items:
                c.execute(
                    """INSERT INTO order_items
                       (order_id, product_id, product_name, qty, price, discount, subtotal)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        order_id,
                        item["id"],
                        item["name"],
                        item["qty"],
                        item["price"],
                        item["disc"],
                        item["subtotal"],
                    ),
                )
                c.execute(
                    "UPDATE products SET stock = stock - ? WHERE id=?",
                    (item["qty"], item["id"]),
                )
                c.execute(
                    """INSERT INTO inventory_log (product_id, change, reason, user_id)
                       VALUES (?,?,?,?)""",
                    (
                        item["id"],
                        -item["qty"],
                        f"Sale #{order_data['order_no']}",
                        order_data["cashier_id"],
                    ),
                )
            conn.commit()
            return order_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def get_order(order_id: int) -> dict | None:
        conn = get_db()
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_order_items(order_id: int) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM order_items WHERE order_id=?", (order_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_orders(date_from: str, date_to: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            """SELECT o.*, u.username, u.full_name,
               (SELECT COUNT(*) FROM order_items WHERE order_id=o.id) as item_count
               FROM orders o
               LEFT JOIN users u ON o.cashier_id = u.id
               WHERE o.created_at >= ? AND o.created_at <= ?
               ORDER BY o.created_at DESC""",
            (date_from, date_to + " 23:59:59"),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def void_order(order_id: int) -> None:
        conn = get_db()
        conn.execute("UPDATE orders SET status='void' WHERE id=?", (order_id,))
        items = conn.execute(
            "SELECT * FROM order_items WHERE order_id=?", (order_id,)
        ).fetchall()
        for it in items:
            conn.execute(
                "UPDATE products SET stock = stock + ? WHERE id=?",
                (it["qty"], it["product_id"]),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def get_recent(limit: int = 8) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            """SELECT order_no, created_at, total, payment_type
               FROM orders ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_today_stats(today: str) -> dict:
        conn = get_db()
        row = conn.execute(
            """SELECT COUNT(*) as cnt, COALESCE(SUM(total),0) as rev
               FROM orders WHERE DATE(created_at)=? AND status='completed'""",
            (today,),
        ).fetchone()
        items = conn.execute(
            """SELECT COALESCE(SUM(oi.qty),0) as n
               FROM order_items oi
               JOIN orders o ON oi.order_id=o.id
               WHERE DATE(o.created_at)=? AND o.status='completed'""",
            (today,),
        ).fetchone()
        conn.close()
        cnt = row["cnt"] or 0
        rev = row["rev"] or 0
        return {
            "orders": cnt,
            "revenue": rev,
            "items": items["n"],
            "avg": rev / cnt if cnt else 0,
        }


# ═══════════════════════════════════════════════════════════════════
#  INVENTORY QUERIES  (alias — thin wrapper kept for clarity)
# ═══════════════════════════════════════════════════════════════════
class InventoryQueries:
    get_stock_log    = staticmethod(ProductQueries.get_stock_log)
    get_low_stock    = staticmethod(ProductQueries.get_low_stock)
    get_stats        = staticmethod(ProductQueries.get_inventory_stats)
    adjust_stock     = staticmethod(ProductQueries.adjust_stock)


# ═══════════════════════════════════════════════════════════════════
#  REPORT QUERIES
# ═══════════════════════════════════════════════════════════════════
class ReportQueries:
    @staticmethod
    def weekly_sales(days: int = 7) -> list[dict]:
        from datetime import date, timedelta
        conn = get_db()
        today = date.today()
        result = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            row = conn.execute(
                """SELECT COUNT(*) as cnt, COALESCE(SUM(total),0) as rev
                   FROM orders WHERE DATE(created_at)=? AND status='completed'""",
                (d.strftime("%Y-%m-%d"),),
            ).fetchone()
            result.append(
                {
                    "day": d.strftime("%a %d"),
                    "orders": row["cnt"],
                    "revenue": row["rev"],
                    "avg": row["rev"] / row["cnt"] if row["cnt"] else 0,
                }
            )
        conn.close()
        return result

    @staticmethod
    def top_products(month_start: str, limit: int = 10) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            """SELECT oi.product_name,
               SUM(oi.qty) as total_qty,
               SUM(oi.subtotal) as total_rev
               FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               WHERE o.status='completed' AND DATE(o.created_at) >= ?
               GROUP BY oi.product_name
               ORDER BY total_rev DESC LIMIT ?""",
            (month_start, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def daily_breakdown(year: int, month: int) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            """SELECT DATE(created_at) as day,
               COUNT(*) as cnt,
               SUM(total) as rev,
               SUM(discount) as disc,
               SUM(tax_amount) as tax,
               (SELECT SUM(qty) FROM order_items oi
                WHERE oi.order_id IN
                  (SELECT id FROM orders o2
                   WHERE DATE(o2.created_at) = DATE(o.created_at)
                   AND o2.status = 'completed')) as items
               FROM orders o
               WHERE strftime('%Y', created_at) = ?
               AND   strftime('%m', created_at) = ?
               AND   status = 'completed'
               GROUP BY DATE(created_at)
               ORDER BY day""",
            (str(year), f"{month:02d}"),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def sales_profit(date_from: str, date_to: str) -> dict:
        conn = get_db()
        rows = conn.execute(
            """SELECT oi.qty, oi.subtotal, p.cost
               FROM order_items oi
               JOIN products p ON oi.product_id = p.id
               JOIN orders o   ON oi.order_id   = o.id
               WHERE o.created_at >= ? AND o.created_at <= ?
               AND   o.status = 'completed'""",
            (date_from, date_to + " 23:59:59"),
        ).fetchall()
        conn.close()
        profit = sum(r["subtotal"] - r["cost"] * r["qty"] for r in rows)
        return {"gross_profit": profit}
