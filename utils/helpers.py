import csv
from datetime import datetime
from pathlib import Path


def next_order_no() -> str:
    """
    Generate a human-readable order number.
    Pattern: ORD-YYYYMMDD-NNNN  (sequential per run; DB enforces uniqueness)
    """
    from database.connection import get_db  # lazy import avoids circular deps
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) as n FROM orders").fetchone()["n"] + 1
    conn.close()
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{n:04d}"


def format_currency(value: float, symbol: str = "$") -> str:
    """Format a float as a currency string: $1,234.56"""
    return f"{symbol}{value:,.2f}"


def export_csv(path: str | Path, headers: list[str], rows: list[list]) -> None:
    """Write *rows* (list of lists) to a CSV file at *path*."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
