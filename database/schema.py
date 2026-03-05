from .connection import get_db
import bcrypt


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'cashier',
    full_name   TEXT    NOT NULL DEFAULT '',
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sku          TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    category_id  INTEGER REFERENCES categories(id),
    price        REAL    NOT NULL DEFAULT 0,
    cost         REAL    NOT NULL DEFAULT 0,
    stock        INTEGER NOT NULL DEFAULT 0,
    low_stock    INTEGER NOT NULL DEFAULT 10,
    unit         TEXT    NOT NULL DEFAULT 'pcs',
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stock_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    change      INTEGER NOT NULL,
    reason      TEXT    NOT NULL DEFAULT '',
    user_id     INTEGER REFERENCES users(id),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no     TEXT    NOT NULL UNIQUE,
    user_id      INTEGER REFERENCES users(id),
    subtotal     REAL    NOT NULL DEFAULT 0,
    discount     REAL    NOT NULL DEFAULT 0,
    tax          REAL    NOT NULL DEFAULT 0,
    total        REAL    NOT NULL DEFAULT 0,
    payment      REAL    NOT NULL DEFAULT 0,
    change_due   REAL    NOT NULL DEFAULT 0,
    pay_method   TEXT    NOT NULL DEFAULT 'cash',
    status       TEXT    NOT NULL DEFAULT 'completed',
    note         TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    name       TEXT    NOT NULL,
    price      REAL    NOT NULL,
    qty        INTEGER NOT NULL,
    subtotal   REAL    NOT NULL
);
"""


SEED_CATEGORIES_PRODUCTS_SQL = """
INSERT OR IGNORE INTO categories (name) VALUES
  ('Beverages'), ('Snacks'), ('Dairy'), ('Bakery'), ('Canned Goods'),
  ('Personal Care'), ('Cleaning'), ('Frozen'), ('Produce'), ('Tobacco');

INSERT OR IGNORE INTO products (sku, name, category_id, price, cost, stock, low_stock, unit)
VALUES
  ('BEV001','Coca-Cola 1.5L',       1, 2.50, 1.20, 120, 20, 'btl'),
  ('BEV002','Mineral Water 500ml',  1, 0.80, 0.30, 200, 30, 'btl'),
  ('BEV003','Orange Juice 1L',      1, 3.20, 1.80, 80,  15, 'btl'),
  ('BEV004','Energy Drink 250ml',   1, 2.00, 0.90, 60,  10, 'can'),
  ('SNK001','Potato Chips 100g',    2, 1.50, 0.70, 150, 25, 'pck'),
  ('SNK002','Chocolate Bar 50g',    2, 1.20, 0.55, 100, 20, 'pcs'),
  ('SNK003','Crackers 200g',        2, 2.00, 0.95, 90,  15, 'pck'),
  ('DAI001','Fresh Milk 1L',        3, 2.80, 1.60, 60,  15, 'btl'),
  ('DAI002','Yogurt 200g',          3, 1.80, 0.90, 45,  10, 'cup'),
  ('DAI003','Cheddar Cheese 200g',  3, 4.50, 2.50, 30,  8,  'pck'),
  ('BAK001','White Bread Loaf',     4, 2.20, 1.00, 40,  10, 'pcs'),
  ('BAK002','Croissant',            4, 1.50, 0.70, 25,  8,  'pcs'),
  ('CAN001','Tuna Can 185g',        5, 1.80, 0.85, 80,  15, 'can'),
  ('CAN002','Tomato Sauce 400g',    5, 1.40, 0.65, 70,  15, 'can'),
  ('PER001','Shampoo 200ml',        6, 3.50, 1.80, 50,  10, 'btl'),
  ('PER002','Soap Bar 100g',        6, 1.00, 0.45, 100, 20, 'pcs'),
  ('CLN001','Dish Soap 500ml',      7, 2.50, 1.20, 55,  10, 'btl'),
  ('FRZ001','Ice Cream 500ml',      8, 4.00, 2.00, 30,  8,  'tub'),
  ('PRD001','Banana 1kg',           9, 1.20, 0.60, 80,  15, 'kg'),
  ('PRD002','Apple 1kg',            9, 2.50, 1.30, 60,  12, 'kg');
"""


def init_db():
    conn = get_db()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.executescript(SEED_CATEGORIES_PRODUCTS_SQL)

        # Seed default users with properly hashed passwords (only if not already present)
        existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing == 0:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                ("admin", _hash("admin123"), "admin", "System Admin")
            )
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                ("cashier1", _hash("admin123"), "cashier", "Jane Cashier")
            )

        conn.commit()
    finally:
        conn.close()