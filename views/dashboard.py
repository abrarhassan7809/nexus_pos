from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QTableWidgetItem)
from PySide6.QtGui import QFont, QColor
from database.queries import OrderQueries, ProductQueries
from utils.theme import THEME
from widgets.base import SectionTitle, StatCard, styled_table


class DashboardTab(QWidget):
    """Home dashboard showing today's stats and low-stock alerts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(12, 12, 12, 12)

        # Header row
        hdr = QHBoxLayout()
        self._greeting = SectionTitle("Dashboard")
        self._date_lbl = QLabel(datetime.now().strftime("%A, %B %d %Y"))
        self._date_lbl.setStyleSheet(
            f"color: {THEME['text_secondary']}; background: transparent;"
        )
        hdr.addWidget(self._greeting)
        hdr.addStretch()
        hdr.addWidget(self._date_lbl)
        lay.addLayout(hdr)

        # Today KPI cards
        today_grp = QGroupBox("TODAY")
        today_lay = QHBoxLayout(today_grp)
        self._c_orders  = StatCard("Orders Today",  "—", "🧾", THEME["accent"])
        self._c_revenue = StatCard("Revenue Today", "—", "$",  THEME["success"])
        self._c_items   = StatCard("Items Sold",    "—", "📦", THEME["warning"])
        self._c_avg     = StatCard("Avg Order",     "—", "⌀",  THEME["text_secondary"])
        for card in [self._c_orders, self._c_revenue, self._c_items, self._c_avg]:
            today_lay.addWidget(card)
        lay.addWidget(today_grp)

        # Bottom section
        bottom = QHBoxLayout()

        recent_grp = QGroupBox("RECENT ORDERS")
        rg_lay = QVBoxLayout(recent_grp)
        self._recent_tbl = styled_table(["Order No", "Time", "Total", "Payment"])
        self._recent_tbl.setMaximumHeight(260)
        rg_lay.addWidget(self._recent_tbl)

        alert_grp = QGroupBox("⚠  LOW STOCK ALERTS")
        ag_lay = QVBoxLayout(alert_grp)
        self._alert_tbl = styled_table(["Product", "Stock", "Low Alert"])
        self._alert_tbl.setMaximumHeight(260)
        ag_lay.addWidget(self._alert_tbl)

        bottom.addWidget(recent_grp, 3)
        bottom.addWidget(alert_grp, 2)
        lay.addLayout(bottom)

    # ── Data ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        stats = OrderQueries.get_today_stats(today)

        self._c_orders.set_value(stats["orders"])
        self._c_revenue.set_value(f"${stats['revenue']:,.2f}")
        self._c_items.set_value(stats["items"])
        self._c_avg.set_value(f"${stats['avg']:.2f}")

        # Recent orders table
        self._recent_tbl.setRowCount(0)
        for r in OrderQueries.get_recent(limit=8):
            ri = self._recent_tbl.rowCount()
            self._recent_tbl.insertRow(ri)
            for ci, txt in enumerate(
                [r["order_no"], r["created_at"][11:16],
                 f"${r['total']:.2f}", r["payment_type"]]
            ):
                self._recent_tbl.setItem(ri, ci, QTableWidgetItem(txt))

        # Low-stock alert table
        self._alert_tbl.setRowCount(0)
        for r in ProductQueries.get_low_stock(limit=15):
            ri = self._alert_tbl.rowCount()
            self._alert_tbl.insertRow(ri)
            cells = [r["name"], str(r["stock"]), str(r["low_stock"])]
            for ci, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                if ci == 1:
                    color = (
                        THEME["danger"] if r["stock"] == 0 else THEME["warning"]
                    )
                    item.setForeground(QColor(color))
                self._alert_tbl.setItem(ri, ci, item)
