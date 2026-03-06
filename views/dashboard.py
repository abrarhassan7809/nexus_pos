from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from database import ReportQueries, ProductQueries
from utils import format_currency, short_date
from utils.theme import ThemeManager as _TM
T = _TM().palette
from widgets import StatCard, SectionTitle, SectionSubtitle, Divider, WeeklyBarChart
from widgets.base import ThemedTable


def _make_inner_table(cols: list[str], col_widths: list[int] | None = None):
    """Compact table for use inside dashboard cards — auto-themed."""
    from widgets.base import styled_table
    return styled_table(cols, col_widths=col_widths)


class DashboardTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._build_ui()
        self.refresh()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(30_000)

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main = QVBoxLayout(container)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(16)

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = SectionTitle("Dashboard")
        hdr.addWidget(title)
        hdr.addStretch()
        self.refresh_btn = QPushButton("⟳  Refresh")
        self.refresh_btn.setObjectName("ghost")
        self.refresh_btn.setFixedHeight(32)
        self.refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(self.refresh_btn)
        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px;")
        hdr.addWidget(self.time_lbl)
        main.addLayout(hdr)

        sub = SectionSubtitle(
            f"Welcome back, {self._user['full_name'] or self._user['username']}!")
        main.addWidget(sub)

        # ── Stat cards ─────────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self.card_today    = StatCard("Today's Sales",    "—", T['accent'],    "💰")
        self.card_tx       = StatCard("Transactions",     "—", T['info'],      "🧾")
        self.card_month    = StatCard("Monthly Revenue",  "—", T['success'],   "📈")
        self.card_low      = StatCard("Low Stock Items",  "—", T['warning'],   "⚠️")
        self.card_products = StatCard("Active Products",  "—", T['text_muted'],"📦")
        for c in [self.card_today, self.card_tx, self.card_month,
                  self.card_low, self.card_products]:
            cards_row.addWidget(c)
        main.addLayout(cards_row)

        # ── Charts row ─────────────────────────────────────────────────────────
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        weekly_card = QFrame()
        weekly_card.setObjectName("card")
        wc_layout = QVBoxLayout(weekly_card)
        wc_layout.setContentsMargins(14, 14, 14, 14)
        wc_layout.setSpacing(8)
        wc_lbl = QLabel("📊  7-Day Revenue")
        wc_lbl.setStyleSheet("font-weight: 600;")
        wc_layout.addWidget(wc_lbl)
        wc_layout.addWidget(Divider())
        self.weekly_chart = WeeklyBarChart()
        self.weekly_chart.setMinimumHeight(180)
        wc_layout.addWidget(self.weekly_chart)
        charts_row.addWidget(weekly_card, 3)

        low_card = QFrame()
        low_card.setObjectName("card")
        lc_layout = QVBoxLayout(low_card)
        lc_layout.setContentsMargins(14, 14, 14, 14)
        lc_layout.setSpacing(8)
        lc_lbl = QLabel("⚠️  Low Stock Alert")
        lc_lbl.setStyleSheet("font-weight: 600;")
        lc_layout.addWidget(lc_lbl)
        lc_layout.addWidget(Divider())

        # Low stock table: Product stretches, Stock and Min are fixed-width
        self.low_table = _make_inner_table(
            ["Product", "Stock", "Min"],
            col_widths=[None, 60, 50]   # Product=stretch(last override below), Stock=60, Min=50
        )
        # Override: stretch Product (col 0), fix the others
        hdr = self.low_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.low_table.setColumnWidth(1, 60)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.low_table.setColumnWidth(2, 50)
        self.low_table.setMinimumHeight(180)
        lc_layout.addWidget(self.low_table)
        charts_row.addWidget(low_card, 2)
        main.addLayout(charts_row)

        # ── Recent transactions ────────────────────────────────────────────────
        rec_card = QFrame()
        rec_card.setObjectName("card")
        rc_layout = QVBoxLayout(rec_card)
        rc_layout.setContentsMargins(14, 14, 14, 14)
        rc_layout.setSpacing(8)
        rc_lbl = QLabel("🕐  Recent Transactions")
        rc_lbl.setStyleSheet("font-weight: 600;")
        rc_layout.addWidget(rc_lbl)
        rc_layout.addWidget(Divider())

        # Order#=140 fixed, Cashier=100 fixed, Total=90 fixed, Method=80 fixed, Time=stretch
        self.recent_table = _make_inner_table(
            ["Order #", "Cashier", "Total", "Method", "Time"]
        )
        h2 = self.recent_table.horizontalHeader()
        h2.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.recent_table.setColumnWidth(0, 150)
        h2.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.recent_table.setColumnWidth(1, 100)
        h2.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.recent_table.setColumnWidth(2, 90)
        h2.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.recent_table.setColumnWidth(3, 80)
        h2.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.recent_table.setMinimumHeight(200)

        rc_layout.addWidget(self.recent_table)
        main.addWidget(rec_card)
        main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        from datetime import datetime
        self.time_lbl.setText(datetime.now().strftime("Updated: %H:%M:%S"))

        stats = ReportQueries.dashboard_stats()
        self.card_today.set_value(format_currency(stats['today_sales']))
        self.card_tx.set_value(str(stats['today_tx']))
        self.card_month.set_value(format_currency(stats['month_sales']))
        self.card_low.set_value(str(stats['low_stock_count']))
        self.card_products.set_value(str(stats['product_count']))

        # Weekly chart
        weekly = ReportQueries.weekly_sales(1)
        self.weekly_chart.set_data([(r['day'], r['revenue']) for r in weekly])

        # Low stock table
        low = ProductQueries.get_low_stock()
        self.low_table.setRowCount(len(low))
        for i, r in enumerate(low):
            self.low_table.setItem(i, 0, QTableWidgetItem(r['name']))
            qty_item = QTableWidgetItem(str(r['stock']))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            qty_item.setForeground(QColor(T['danger']))
            self.low_table.setItem(i, 1, qty_item)
            min_item = QTableWidgetItem(str(r['low_stock']))
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.low_table.setItem(i, 2, min_item)

        # Recent orders
        from database import OrderQueries
        orders = OrderQueries.get_all()[:10]
        self.recent_table.setRowCount(len(orders))
        for i, o in enumerate(orders):
            self.recent_table.setItem(i, 0, QTableWidgetItem(o['order_no']))
            self.recent_table.setItem(i, 1, QTableWidgetItem(o['username'] or '—'))
            total_item = QTableWidgetItem(format_currency(o['total']))
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_item.setForeground(QColor(T['success']))
            self.recent_table.setItem(i, 2, total_item)
            method_item = QTableWidgetItem(o['pay_method'].upper())
            method_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.recent_table.setItem(i, 3, method_item)
            self.recent_table.setItem(i, 4, QTableWidgetItem(short_date(o['created_at'])))
