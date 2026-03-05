from __future__ import annotations
import csv
import os
from datetime import datetime
from database.connection import get_db


def next_order_no() -> str:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM orders WHERE date(created_at)=date('now')"
        ).fetchone()
        seq = (row["c"] or 0) + 1
        return f"ORD-{datetime.now().strftime('%Y%m%d')}-{seq:04d}"
    finally:
        conn.close()


def format_currency(amount: float, symbol: str = "$") -> str:
    return f"{symbol}{amount:,.2f}"


def export_csv(rows, headers: list[str], filepath: str):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row[h] if h in row.keys() else "" for h in headers])


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def short_date(dt_str: str) -> str:
    try:
        return datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y %H:%M")
    except Exception:
        return dt_str
