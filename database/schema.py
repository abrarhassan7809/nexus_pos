from .connection import get_db
from utils.security import hash_pw


def init_db() -> None:
    """Initialise database schema and seed demo data."""
    conn = get_db()
    c = conn.cursor()

    # ── Tables ────────────────────────────────────────────────────
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        username   TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        role       TEXT NOT NULL DEFAULT 'cashier',
        full_name  TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS categories (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        category_id INTEGER REFERENCES categories(id),
        price       REAL NOT NULL,
        cost        REAL NOT NULL DEFAULT 0,
        stock       INTEGER NOT NULL DEFAULT 0,
        low_stock   INTEGER NOT NULL DEFAULT 5,
        barcode     TEXT UNIQUE,
        unit        TEXT DEFAULT 'pcs',
        active      INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS orders (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no     TEXT UNIQUE NOT NULL,
        cashier_id   INTEGER REFERENCES users(id),
        subtotal     REAL NOT NULL DEFAULT 0,
        discount     REAL NOT NULL DEFAULT 0,
        tax_rate     REAL NOT NULL DEFAULT 0,
        tax_amount   REAL NOT NULL DEFAULT 0,
        total        REAL NOT NULL DEFAULT 0,
        paid         REAL NOT NULL DEFAULT 0,
        change       REAL NOT NULL DEFAULT 0,
        payment_type TEXT DEFAULT 'cash',
        note         TEXT DEFAULT '',
        status       TEXT DEFAULT 'completed',
        created_at   TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id     INTEGER REFERENCES orders(id) ON DELETE CASCADE,
        product_id   INTEGER REFERENCES products(id),
        product_name TEXT NOT NULL,
        qty          INTEGER NOT NULL,
        price        REAL NOT NULL,
        discount     REAL NOT NULL DEFAULT 0,
        subtotal     REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS inventory_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER REFERENCES products(id),
        change     INTEGER NOT NULL,
        reason     TEXT DEFAULT '',
        user_id    INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    # ── Seed: users ───────────────────────────────────────────────
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
        ("admin", hash_pw("admin123"), "admin", "Administrator"),
    )
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
        ("cashier", hash_pw("cash123"), "cashier", "John Cashier"),
    )

    # ── Seed: categories ──────────────────────────────────────────
    for cat in ["Beverages", "Food", "Electronics", "Clothing", "Household"]:
        c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    conn.commit()

    # ── Seed: products ────────────────────────────────────────────
    demo_products = [
        ("Espresso Coffee", 1, 3.50, 1.20, 50, 10, "BEV001", "cup"),
        ("Green Tea",       1, 2.50, 0.80, 40,  8, "BEV002", "cup"),
        ("Orange Juice",    1, 4.00, 1.50, 30,  5, "BEV003", "cup"),
        ("Mineral Water",   1, 1.50, 0.40, 100,15, "BEV004", "btl"),
        ("Cheese Burger",   2, 8.99, 3.50, 25,  5, "FOD001", "pcs"),
        ("Caesar Salad",    2, 7.50, 2.80, 20,  4, "FOD002", "pcs"),
        ("Club Sandwich",   2, 6.99, 2.60, 22,  4, "FOD003", "pcs"),
        ("French Fries",    2, 3.99, 1.20, 35,  6, "FOD004", "pcs"),
        ("USB Cable",       3, 9.99, 4.00, 60, 10, "ELC001", "pcs"),
        ("Phone Stand",     3,12.99, 5.00, 40,  8, "ELC002", "pcs"),
        ("Wireless Mouse",  3,24.99,10.00, 15,  3, "ELC003", "pcs"),
        ("T-Shirt (M)",     4,14.99, 6.00, 30,  5, "CLT001", "pcs"),
        ("Cap",             4, 9.99, 3.50, 25,  4, "CLT002", "pcs"),
        ("Detergent",       5, 5.99, 2.00, 45,  8, "HHS001", "btl"),
        ("Tissue Box",      5, 2.99, 0.90, 60, 10, "HHS002", "box"),
    ]
    for p in demo_products:
        c.execute(
            """INSERT OR IGNORE INTO products
               (name, category_id, price, cost, stock, low_stock, barcode, unit)
               VALUES (?,?,?,?,?,?,?,?)""",
            p,
        )
    conn.commit()
    conn.close()
