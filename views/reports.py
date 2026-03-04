from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QTableWidgetItem,
                               QComboBox, QSpinBox)
from PySide6.QtGui import QFont
from datetime import datetime
from database.queries import ReportQueries
from utils.theme import THEME
from widgets.base import SectionTitle, styled_table
from widgets.charts import WeeklyBarChart, TopProductsChart


class ReportsTab(QWidget):
    """Analytics hub — weekly, top products, daily breakdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        lay.setContentsMargins(12, 12, 12, 12)

        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Reports & Analytics"))
        hdr.addStretch()
        ref_btn = QPushButton("🔄  Refresh")
        ref_btn.clicked.connect(self.refresh)
        hdr.addWidget(ref_btn)
        lay.addLayout(hdr)

        inner = QTabWidget()
        inner.addTab(self._build_weekly_tab(),   "📅  Weekly Sales")
        inner.addTab(self._build_products_tab(), "🏆  Top Products")
        inner.addTab(self._build_daily_tab(),    "📆  Daily Breakdown")
        lay.addWidget(inner)

    # ── Sub-tabs ──────────────────────────────────────────────────
    def _build_weekly_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(12, 12, 12, 12)

        lbl = QLabel("Last 7 Days — Revenue by Day")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")
        lay.addWidget(lbl)

        self._weekly_chart = WeeklyBarChart()
        lay.addWidget(self._weekly_chart)

        self._weekly_tbl = styled_table(
            ["Day", "Orders", "Revenue", "Avg Order Value"]
        )
        self._weekly_tbl.setMaximumHeight(200)
        lay.addWidget(self._weekly_tbl)
        return w

    def _build_products_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(12, 12, 12, 12)

        lbl = QLabel("Top 10 Products by Revenue (this month)")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")
        lay.addWidget(lbl)

        self._top_chart = TopProductsChart()
        lay.addWidget(self._top_chart)
        return w

    def _build_daily_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(12, 12, 12, 12)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Select Month:"))
        self._month_combo = QComboBox()
        for i in range(1, 13):
            self._month_combo.addItem(datetime(2000, i, 1).strftime("%B"), i)
        self._month_combo.setCurrentIndex(datetime.now().month - 1)

        self._year_spin = QSpinBox()
        self._year_spin.setRange(2020, 2099)
        self._year_spin.setValue(datetime.now().year)

        go_btn = QPushButton("Load"); go_btn.setObjectName("accent_btn")
        go_btn.clicked.connect(self._load_daily)

        hdr.addWidget(self._month_combo)
        hdr.addWidget(self._year_spin)
        hdr.addWidget(go_btn)
        hdr.addStretch()
        lay.addLayout(hdr)

        self._daily_tbl = styled_table(
            ["Date", "Orders", "Revenue", "Discount Given",
             "Tax Collected", "Items Sold"]
        )
        lay.addWidget(self._daily_tbl)
        return w

    # ── Data ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._load_weekly()
        self._load_top_products()
        self._load_daily()

    def _load_weekly(self) -> None:
        data = ReportQueries.weekly_sales(days=7)
        self._weekly_chart.set_data(data)

        self._weekly_tbl.setRowCount(0)
        for d in data:
            ri = self._weekly_tbl.rowCount()
            self._weekly_tbl.insertRow(ri)
            for ci, txt in enumerate(
                [d["day"], str(d["orders"]),
                 f"${d['revenue']:,.2f}", f"${d['avg']:.2f}"]
            ):
                self._weekly_tbl.setItem(ri, ci, QTableWidgetItem(txt))

    def _load_top_products(self) -> None:
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        data = ReportQueries.top_products(month_start=month_start, limit=10)
        self._top_chart.set_data(data)

    def _load_daily(self) -> None:
        m = self._month_combo.currentData()
        y = self._year_spin.value()
        rows = ReportQueries.daily_breakdown(year=y, month=m)

        self._daily_tbl.setRowCount(0)
        for r in rows:
            ri = self._daily_tbl.rowCount()
            self._daily_tbl.insertRow(ri)
            for ci, txt in enumerate(
                [r["day"], str(r["cnt"]),
                 f"${r['rev']:.2f}", f"${r['disc']:.2f}",
                 f"${r['tax']:.2f}", str(r["items"] or 0)]
            ):
                self._daily_tbl.setItem(ri, ci, QTableWidgetItem(txt))
