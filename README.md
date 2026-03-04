# ⬡ NEXUS POS — Point of Sale Management System

A full-featured desktop POS application built with **Python + PySide6 / PyQt6**,
organised as a clean, modular project.

---

## 🚀 Quick Start

```bash
# 1. Install dependency
pip install PySide6       # or: pip install PyQt6

# 2. Run
python main.py
```

### Default Login Credentials
| Role    | Username | Password  |
|---------|----------|-----------|
| Admin   | `admin`  | `admin123`|
| Cashier | `cashier`| `cash123` |

---

## 📁 Project Structure

```
nexus_pos/
│
├── main.py                   ← Entry point — boots Qt, login, main window
│
├── database/
│   ├── __init__.py           ← Re-exports: get_db, init_db, *Queries
│   ├── connection.py         ← SQLite connection factory (DB_PATH defined here)
│   ├── schema.py             ← Table creation + seed data
│   └── queries.py            ← All SQL: UserQueries, ProductQueries,
│                                         OrderQueries, ReportQueries, ...
│
├── utils/
│   ├── __init__.py
│   ├── security.py           ← hash_pw(), is_admin()
│   ├── helpers.py            ← next_order_no(), format_currency(), export_csv()
│   └── theme.py              ← THEME dict + full Qt STYLESHEET string
│
├── widgets/
│   ├── __init__.py
│   ├── base.py               ← SectionTitle, StatCard, Divider, styled_table()
│   └── charts.py             ← WeeklyBarChart, TopProductsChart (pure QPainter)
│
├── views/
│   ├── __init__.py
│   ├── login.py              ← LoginDialog
│   ├── main_window.py        ← MainWindow (tabs + status bar)
│   ├── dashboard.py          ← DashboardTab
│   ├── pos.py                ← PosTab + EditCartItemDialog + ReceiptDialog
│   ├── inventory.py          ← InventoryTab + ProductDialog
│   │                            + StockAdjustDialog + StockLogDialog
│   ├── sales.py              ← SalesTab (filter, void, CSV export)
│   ├── reports.py            ← ReportsTab (weekly chart, top products, daily)
│   └── users.py              ← UsersTab + UserDialog  [admin only]
│
├── requirements.txt
├── README.md
└── nexus_pos.db              ← SQLite database (auto-created on first run)
```

---

## ✨ Features

### 🛒 POS / New Order (`views/pos.py`)
- Live product search + category filter
- Double-click or button to add to cart
- Edit per-item qty & discount
- Order-level discount %, configurable tax %
- Cash / Card / E-Wallet / Mixed payment
- Change calculation
- Printable / saveable HTML receipt

### 📦 Inventory Management (`views/inventory.py`)
- Add, edit, deactivate products (barcode, cost, unit, low-stock threshold)
- Colour-coded stock alerts (yellow = low, red = out)
- Manual stock adjustment + audit log
- Inventory value & stat cards

### 🧾 Sales Records (`views/sales.py`)
- Date-range filter, KPI summary cards
- View receipt for any past order
- Void order (restores stock)
- One-click CSV export

### 📊 Reports (`views/reports.py`)
- 7-day revenue bar chart (pure QPainter)
- Top-10 products horizontal bar chart
- Daily breakdown by month/year

### 👤 User Management (`views/users.py`) — admin only
- Add / edit / delete users
- Admin or Cashier role
- Change password

### 🔐 Security (`utils/security.py`)
- SHA-256 password hashing
- Role-based tab access
- Session logout

---

## 🗄 Database Schema

| Table | Purpose |
|---|---|
| `users` | Credentials & roles |
| `categories` | Product categories |
| `products` | Inventory items |
| `orders` | Completed transactions |
| `order_items` | Line items per order |
| `inventory_log` | All stock movements |

---

## 🖥 System Requirements
- Python **3.10+**
- **PySide6 ≥ 6.4** or **PyQt6 ≥ 6.4**
- Windows / macOS / Linux
