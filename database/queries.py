from __future__ import annotations
from typing import Optional
from .connection import get_db


# ──────────────────────────── USER QUERIES ────────────────────────────────────
class UserQueries:
    @staticmethod
    def get_by_username(username: str):
        conn = get_db()
        try:
            return conn.execute(
                "SELECT * FROM users WHERE username=? AND active=1", (username,)
            ).fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_all():
        conn = get_db()
        try:
            return conn.execute(
                "SELECT * FROM users ORDER BY role, username"
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def create(username, password_hash, role, full_name):
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                (username, password_hash, role, full_name)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update(user_id, username, password_hash, role, full_name, active):
        conn = get_db()
        try:
            if password_hash:
                conn.execute(
                    "UPDATE users SET username=?,password=?,role=?,full_name=?,active=? WHERE id=?",
                    (username, password_hash, role, full_name, active, user_id)
                )
            else:
                conn.execute(
                    "UPDATE users SET username=?,role=?,full_name=?,active=? WHERE id=?",
                    (username, role, full_name, active, user_id)
                )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete(user_id):
        conn = get_db()
        try:
            conn.execute("UPDATE users SET active=0 WHERE id=?", (user_id,))
            conn.commit()
        finally:
            conn.close()


# ──────────────────────────── PRODUCT QUERIES ─────────────────────────────────
class ProductQueries:
    @staticmethod
    def get_all(active_only=True):
        conn = get_db()
        try:
            q = """SELECT p.*, c.name AS category_name
                   FROM products p LEFT JOIN categories c ON p.category_id=c.id"""
            if active_only:
                q += " WHERE p.active=1"
            q += " ORDER BY p.name"
            return conn.execute(q).fetchall()
        finally:
            conn.close()

    @staticmethod
    def search(term: str):
        conn = get_db()
        try:
            like = f"%{term}%"
            return conn.execute(
                """SELECT p.*, c.name AS category_name
                   FROM products p LEFT JOIN categories c ON p.category_id=c.id
                   WHERE p.active=1 AND (p.name LIKE ? OR p.sku LIKE ?)
                   ORDER BY p.name""",
                (like, like)
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_by_id(product_id):
        conn = get_db()
        try:
            return conn.execute(
                """SELECT p.*, c.name AS category_name
                   FROM products p LEFT JOIN categories c ON p.category_id=c.id
                   WHERE p.id=?""", (product_id,)
            ).fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_low_stock():
        conn = get_db()
        try:
            return conn.execute(
                """SELECT p.*, c.name AS category_name
                   FROM products p LEFT JOIN categories c ON p.category_id=c.id
                   WHERE p.active=1 AND p.stock <= p.low_stock
                   ORDER BY p.stock"""
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def create(sku, name, category_id, price, cost, stock, low_stock, unit):
        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO products (sku,name,category_id,price,cost,stock,low_stock,unit)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (sku, name, category_id, price, cost, stock, low_stock, unit)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update(product_id, sku, name, category_id, price, cost, stock, low_stock, unit):
        conn = get_db()
        try:
            conn.execute(
                """UPDATE products SET sku=?,name=?,category_id=?,price=?,cost=?,
                   stock=?,low_stock=?,unit=? WHERE id=?""",
                (sku, name, category_id, price, cost, stock, low_stock, unit, product_id)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def adjust_stock(product_id, change, reason, user_id):
        conn = get_db()
        try:
            conn.execute(
                "UPDATE products SET stock = stock + ? WHERE id=?",
                (change, product_id)
            )
            conn.execute(
                "INSERT INTO stock_log (product_id,change,reason,user_id) VALUES (?,?,?,?)",
                (product_id, change, reason, user_id)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def deactivate(product_id):
        conn = get_db()
        try:
            conn.execute("UPDATE products SET active=0 WHERE id=?", (product_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_stock_log(product_id):
        conn = get_db()
        try:
            return conn.execute(
                """SELECT sl.*, u.username FROM stock_log sl
                   LEFT JOIN users u ON sl.user_id=u.id
                   WHERE sl.product_id=? ORDER BY sl.created_at DESC""",
                (product_id,)
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_categories():
        conn = get_db()
        try:
            return conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
        finally:
            conn.close()


# ──────────────────────────── ORDER QUERIES ───────────────────────────────────
class OrderQueries:
    @staticmethod
    def create_order(order_no, user_id, items, subtotal, discount, tax,
                     total, payment, change_due, pay_method, note=""):
        conn = get_db()
        try:
            cur = conn.execute(
                """INSERT INTO orders (order_no,user_id,subtotal,discount,tax,total,
                   payment,change_due,pay_method,note)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (order_no, user_id, subtotal, discount, tax, total,
                 payment, change_due, pay_method, note)
            )
            order_id = cur.lastrowid
            for item in items:
                conn.execute(
                    """INSERT INTO order_items (order_id,product_id,name,price,qty,subtotal)
                       VALUES (?,?,?,?,?,?)""",
                    (order_id, item['product_id'], item['name'],
                     item['price'], item['qty'], item['subtotal'])
                )
                conn.execute(
                    "UPDATE products SET stock = stock - ? WHERE id=?",
                    (item['qty'], item['product_id'])
                )
                conn.execute(
                    """INSERT INTO stock_log (product_id,change,reason,user_id)
                       VALUES (?,?,?,?)""",
                    (item['product_id'], -item['qty'], f"Sale #{order_no}", user_id)
                )
            conn.commit()
            return order_id
        finally:
            conn.close()

    @staticmethod
    def get_all(date_from=None, date_to=None, status=None):
        conn = get_db()
        try:
            q = """SELECT o.*, u.username FROM orders o
                   LEFT JOIN users u ON o.user_id=u.id WHERE 1=1"""
            params = []
            if date_from:
                q += " AND date(o.created_at) >= ?"
                params.append(date_from)
            if date_to:
                q += " AND date(o.created_at) <= ?"
                params.append(date_to)
            if status:
                q += " AND o.status=?"
                params.append(status)
            q += " ORDER BY o.created_at DESC"
            return conn.execute(q, params).fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_by_id(order_id):
        conn = get_db()
        try:
            order = conn.execute(
                """SELECT o.*, u.username FROM orders o
                   LEFT JOIN users u ON o.user_id=u.id WHERE o.id=?""",
                (order_id,)
            ).fetchone()
            items = conn.execute(
                "SELECT * FROM order_items WHERE order_id=?", (order_id,)
            ).fetchall()
            return order, items
        finally:
            conn.close()

    @staticmethod
    def void_order(order_id, user_id):
        conn = get_db()
        try:
            conn.execute(
                "UPDATE orders SET status='voided' WHERE id=?", (order_id,)
            )
            items = conn.execute(
                "SELECT * FROM order_items WHERE order_id=?", (order_id,)
            ).fetchall()
            for item in items:
                conn.execute(
                    "UPDATE products SET stock = stock + ? WHERE id=?",
                    (item['qty'], item['product_id'])
                )
                conn.execute(
                    """INSERT INTO stock_log (product_id,change,reason,user_id)
                       VALUES (?,?,?,?)""",
                    (item['product_id'], item['qty'], f"Void order #{item['order_id']}", user_id)
                )
            conn.commit()
        finally:
            conn.close()


# ──────────────────────────── REPORT QUERIES ──────────────────────────────────
class ReportQueries:
    @staticmethod
    def daily_summary(date_str: str):
        conn = get_db()
        try:
            row = conn.execute(
                """SELECT COUNT(*) as tx_count,
                          COALESCE(SUM(total),0) as revenue,
                          COALESCE(SUM(total - discount),0) as net_revenue
                   FROM orders WHERE date(created_at)=? AND status='completed'""",
                (date_str,)
            ).fetchone()
            return row
        finally:
            conn.close()

    @staticmethod
    def weekly_sales(weeks=1):
        conn = get_db()
        try:
            return conn.execute(
                """SELECT date(created_at) as day,
                          COALESCE(SUM(total),0) as revenue,
                          COUNT(*) as tx_count
                   FROM orders WHERE status='completed'
                     AND date(created_at) >= date('now',?)
                   GROUP BY day ORDER BY day""",
                (f"-{weeks*7} days",)
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def monthly_sales(year: int, month: int):
        conn = get_db()
        try:
            return conn.execute(
                """SELECT date(created_at) as day,
                          COALESCE(SUM(total),0) as revenue,
                          COUNT(*) as tx_count
                   FROM orders WHERE status='completed'
                     AND strftime('%Y',created_at)=?
                     AND strftime('%m',created_at)=?
                   GROUP BY day ORDER BY day""",
                (str(year), f"{month:02d}")
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def top_products(limit=10, date_from=None, date_to=None):
        conn = get_db()
        try:
            q = """SELECT oi.name, SUM(oi.qty) as total_qty,
                          SUM(oi.subtotal) as revenue
                   FROM order_items oi
                   JOIN orders o ON oi.order_id=o.id
                   WHERE o.status='completed'"""
            params = []
            if date_from:
                q += " AND date(o.created_at)>=?"
                params.append(date_from)
            if date_to:
                q += " AND date(o.created_at)<=?"
                params.append(date_to)
            q += f" GROUP BY oi.name ORDER BY revenue DESC LIMIT {limit}"
            return conn.execute(q, params).fetchall()
        finally:
            conn.close()

    @staticmethod
    def monthly_summary_list():
        conn = get_db()
        try:
            return conn.execute(
                """SELECT strftime('%Y-%m', created_at) as month,
                          COUNT(*) as tx_count,
                          SUM(total) as revenue,
                          SUM(discount) as discounts
                   FROM orders WHERE status='completed'
                   GROUP BY month ORDER BY month DESC"""
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def dashboard_stats():
        conn = get_db()
        try:
            today = conn.execute(
                """SELECT COALESCE(SUM(total),0) as total, COUNT(*) as count
                   FROM orders WHERE date(created_at)=date('now') AND status='completed'"""
            ).fetchone()
            month = conn.execute(
                """SELECT COALESCE(SUM(total),0) as total
                   FROM orders WHERE strftime('%Y-%m',created_at)=strftime('%Y-%m','now')
                   AND status='completed'"""
            ).fetchone()
            low = conn.execute(
                "SELECT COUNT(*) as count FROM products WHERE active=1 AND stock<=low_stock"
            ).fetchone()
            products = conn.execute(
                "SELECT COUNT(*) as count FROM products WHERE active=1"
            ).fetchone()
            return {
                'today_sales': today['total'],
                'today_tx': today['count'],
                'month_sales': month['total'],
                'low_stock_count': low['count'],
                'product_count': products['count'],
            }
        finally:
            conn.close()


# ──────────────────────────── EXPENSE QUERIES ─────────────────────────────────
class ExpenseQueries:

    # ── Categories ─────────────────────────────────────────────────────────────
    @staticmethod
    def get_categories():
        conn = get_db()
        try:
            return conn.execute(
                "SELECT * FROM expense_categories ORDER BY name"
            ).fetchall()
        finally:
            conn.close()

    @staticmethod
    def create_category(name: str, color: str, icon: str):
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO expense_categories (name, color, icon) VALUES (?,?,?)",
                (name, color, icon)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update_category(cat_id: int, name: str, color: str, icon: str):
        conn = get_db()
        try:
            conn.execute(
                "UPDATE expense_categories SET name=?, color=?, icon=? WHERE id=?",
                (name, color, icon, cat_id)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete_category(cat_id: int):
        conn = get_db()
        try:
            conn.execute("DELETE FROM expense_categories WHERE id=?", (cat_id,))
            conn.commit()
        finally:
            conn.close()

    # ── Expenses ───────────────────────────────────────────────────────────────
    @staticmethod
    def get_all(date_from: str = None, date_to: str = None,
                category_id: int = None) -> list:
        conn = get_db()
        try:
            q = """SELECT e.*, ec.name as cat_name, ec.color as cat_color,
                          ec.icon as cat_icon, u.username
                   FROM expenses e
                   LEFT JOIN expense_categories ec ON e.category_id = ec.id
                   LEFT JOIN users u ON e.user_id = u.id
                   WHERE 1=1"""
            params = []
            if date_from:
                q += " AND date(e.created_at) >= ?"; params.append(date_from)
            if date_to:
                q += " AND date(e.created_at) <= ?"; params.append(date_to)
            if category_id:
                q += " AND e.category_id = ?"; params.append(category_id)
            q += " ORDER BY e.created_at DESC"
            return conn.execute(q, params).fetchall()
        finally:
            conn.close()

    @staticmethod
    def create(category_id: int, title: str, amount: float,
               type_: str, note: str, user_id: int):
        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO expenses (category_id, title, amount, type, note, user_id)
                   VALUES (?,?,?,?,?,?)""",
                (category_id, title, amount, type_, note, user_id)
            )
            # Update budget balance
            if type_ == 'budget_add':
                conn.execute(
                    "UPDATE budget SET balance = balance + ?, updated_at = datetime('now') WHERE id=1",
                    (amount,)
                )
            elif type_ == 'budget_sub':
                conn.execute(
                    "UPDATE budget SET balance = balance - ?, updated_at = datetime('now') WHERE id=1",
                    (amount,)
                )
            elif type_ == 'expense':
                conn.execute(
                    "UPDATE budget SET balance = balance - ?, updated_at = datetime('now') WHERE id=1",
                    (amount,)
                )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete(expense_id: int):
        """Reverse the budget effect then delete the record."""
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT amount, type FROM expenses WHERE id=?", (expense_id,)
            ).fetchone()
            if row:
                amt, typ = row['amount'], row['type']
                # Reverse
                if typ == 'budget_add':
                    conn.execute(
                        "UPDATE budget SET balance = balance - ?, updated_at = datetime('now') WHERE id=1",
                        (amt,)
                    )
                elif typ in ('budget_sub', 'expense'):
                    conn.execute(
                        "UPDATE budget SET balance = balance + ?, updated_at = datetime('now') WHERE id=1",
                        (amt,)
                    )
                conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
                conn.commit()
        finally:
            conn.close()

    # ── Budget ─────────────────────────────────────────────────────────────────
    @staticmethod
    def get_budget() -> float:
        conn = get_db()
        try:
            row = conn.execute("SELECT balance FROM budget WHERE id=1").fetchone()
            return row['balance'] if row else 0.0
        finally:
            conn.close()

    # ── Dashboard stats ────────────────────────────────────────────────────────
    @staticmethod
    def dashboard_stats() -> dict:
        conn = get_db()
        try:
            budget = conn.execute(
                "SELECT balance FROM budget WHERE id=1"
            ).fetchone()
            today_exp = conn.execute(
                """SELECT COALESCE(SUM(amount),0) as total
                   FROM expenses WHERE type='expense'
                   AND date(created_at)=date('now')"""
            ).fetchone()
            month_exp = conn.execute(
                """SELECT COALESCE(SUM(amount),0) as total
                   FROM expenses WHERE type='expense'
                   AND strftime('%Y-%m',created_at)=strftime('%Y-%m','now')"""
            ).fetchone()
            by_cat = conn.execute(
                """SELECT ec.name, ec.color, ec.icon,
                          COALESCE(SUM(e.amount),0) as total
                   FROM expense_categories ec
                   LEFT JOIN expenses e ON e.category_id=ec.id
                       AND e.type='expense'
                       AND strftime('%Y-%m',e.created_at)=strftime('%Y-%m','now')
                   GROUP BY ec.id ORDER BY total DESC"""
            ).fetchall()
            return {
                'budget':    budget['balance'] if budget else 0.0,
                'today_exp': today_exp['total'],
                'month_exp': month_exp['total'],
                'by_cat':    [dict(r) for r in by_cat],
            }
        finally:
            conn.close()

    @staticmethod
    def monthly_expense_summary():
        conn = get_db()
        try:
            return conn.execute(
                """SELECT strftime('%Y-%m', created_at) as month,
                          COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) as expenses,
                          COALESCE(SUM(CASE WHEN type='budget_add' THEN amount ELSE 0 END),0) as added,
                          COALESCE(SUM(CASE WHEN type='budget_sub' THEN amount ELSE 0 END),0) as subtracted
                   FROM expenses
                   GROUP BY month ORDER BY month DESC LIMIT 12"""
            ).fetchall()
        finally:
            conn.close()