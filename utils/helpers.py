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


# ─── Order auto-save ───────────────────────────────────────────────────────────

def get_orders_dir() -> str:
    """
    Returns (and creates if needed) the orders/ folder next to main.py.
    Structure: orders/YYYY-MM/
    """
    base = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "receipts",
        datetime.now().strftime("%Y-%m"),
    )
    os.makedirs(base, exist_ok=True)
    return base


def save_order_txt(order: dict, items: list) -> str:
    folder = get_orders_dir()
    safe_no = order['order_no'].replace('/', '-').replace('\\', '-')
    path = os.path.join(folder, f"{safe_no}.txt")

    lines = [
        "=" * 40,
        "          NEXUS POS SYSTEM",
        "=" * 40,
        f"Order No : {order['order_no']}",
        f"Date     : {order.get('created_at', now_str())[:19]}",
        f"Cashier  : {order.get('username', '—')}",
        f"Method   : {order.get('pay_method', '').upper()}",
        "-" * 40,
    ]
    for item in items:
        lines.append(f"  {item['name'][:26]:<26} x{item['qty']}")
        lines.append(f"  {'':26} @ {format_currency(item['price'])} = {format_currency(item['subtotal'])}")

    lines += [
        "-" * 40,
        f"  Subtotal : {format_currency(order.get('subtotal', 0)):>10}",
        f"  Discount : {format_currency(order.get('discount', 0)):>10}",
        f"  Tax      : {format_currency(order.get('tax', 0)):>10}",
        f"  TOTAL    : {format_currency(order.get('total', 0)):>10}",
        f"  Payment  : {format_currency(order.get('payment', 0)):>10}",
        f"  Change   : {format_currency(order.get('change_due', 0)):>10}",
        "=" * 40,
        "    Thank you for your purchase!",
        "=" * 40,
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return path


def save_order_pdf(order: dict, items: list) -> str:
    try:
        from reportlab.lib.pagesizes import A6
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
    except ImportError:
        return ""

    folder = get_orders_dir()
    safe_no = order['order_no'].replace('/', '-').replace('\\', '-')
    path = os.path.join(folder, f"{safe_no}.pdf")

    doc = SimpleDocTemplate(
        path, pagesize=A6,
        topMargin=0.6*cm, bottomMargin=0.6*cm,
        leftMargin=0.8*cm, rightMargin=0.8*cm,
    )
    styles = getSampleStyleSheet()
    accent = colors.HexColor("#6C63FF")

    title_style  = ParagraphStyle("t",  parent=styles["Normal"],
                                   fontSize=14, fontName="Helvetica-Bold",
                                   textColor=accent, spaceAfter=2, alignment=1)
    sub_style    = ParagraphStyle("s",  parent=styles["Normal"],
                                   fontSize=8,  textColor=colors.grey, alignment=1)
    normal_style = ParagraphStyle("n",  parent=styles["Normal"], fontSize=8, spaceAfter=1)
    bold_style   = ParagraphStyle("b",  parent=styles["Normal"],
                                   fontSize=8,  fontName="Helvetica-Bold")
    total_style  = ParagraphStyle("tt", parent=styles["Normal"],
                                   fontSize=10, fontName="Helvetica-Bold",
                                   textColor=colors.HexColor("#22C55E"))
    hr = lambda: Paragraph("<hr/>", normal_style)

    story = [
        Paragraph("NEXUS POS", title_style),
        Paragraph("Point of Sale System", sub_style),
        Spacer(1, 0.2*cm),
        hr(),
        Paragraph(f"<b>Order:</b>  {order['order_no']}", normal_style),
        Paragraph(f"<b>Date:</b>   {order.get('created_at', now_str())[:19]}", normal_style),
        Paragraph(f"<b>Cashier:</b> {order.get('username', '—')}", normal_style),
        Paragraph(f"<b>Method:</b>  {order.get('pay_method', '').upper()}", normal_style),
        hr(),
    ]

    for item in items:
        story.append(Paragraph(
            f"{item['name']}  ×{item['qty']}  —  {format_currency(item['subtotal'])}",
            normal_style))
        story.append(Paragraph(
            f"&nbsp;&nbsp;&nbsp;@ {format_currency(item['price'])} each",
            ParagraphStyle("sm", parent=normal_style, textColor=colors.grey, fontSize=7)))

    story += [
        hr(),
        Paragraph(f"Subtotal: {format_currency(order.get('subtotal', 0))}", normal_style),
        Paragraph(f"Discount: {format_currency(order.get('discount', 0))}", normal_style),
        Paragraph(f"Tax:      {format_currency(order.get('tax', 0))}", normal_style),
        Spacer(1, 0.1*cm),
        Paragraph(f"TOTAL: {format_currency(order.get('total', 0))}", total_style),
        Spacer(1, 0.1*cm),
        Paragraph(f"Payment: {format_currency(order.get('payment', 0))}", normal_style),
        Paragraph(f"Change:  {format_currency(order.get('change_due', 0))}", normal_style),
        hr(),
        Paragraph("Thank you for your purchase!", sub_style),
    ]

    doc.build(story)
    return path