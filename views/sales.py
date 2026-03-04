from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidgetItem, QMessageBox,
                               QDialog, QFileDialog, QDateEdit, QHeaderView)
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
from database.queries import OrderQueries, ReportQueries
from utils.theme import THEME
from utils.helpers import export_csv
from widgets.base import SectionTitle, StatCard, styled_table
from .pos import ReceiptDialog


class SalesTab(QWidget):
    """Full sales record viewer with filter, stats, and export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows_cache: list[dict] = []
        self._build_ui()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        lay.setContentsMargins(12, 12, 12, 12)

        # Header + filters
        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Sales Records"))
        hdr.addStretch()

        self._from = QDateEdit(QDate.currentDate().addDays(-30))
        self._from.setDisplayFormat("yyyy-MM-dd"); self._from.setCalendarPopup(True); self._from.setFixedHeight(34)

        self._to = QDateEdit(QDate.currentDate())
        self._to.setDisplayFormat("yyyy-MM-dd"); self._to.setCalendarPopup(True); self._to.setFixedHeight(34)

        flt_btn = QPushButton("🔍  Filter"); flt_btn.setObjectName("accent_btn"); flt_btn.setFixedHeight(34); flt_btn.clicked.connect(self.refresh)
        exp_btn = QPushButton("📤  Export CSV"); exp_btn.setFixedHeight(34); exp_btn.clicked.connect(self._export)

        hdr.addWidget(QLabel("From:")); hdr.addWidget(self._from)
        hdr.addWidget(QLabel("To:"));   hdr.addWidget(self._to)
        hdr.addWidget(flt_btn); hdr.addWidget(exp_btn)
        lay.addLayout(hdr)

        # KPI cards
        sr = QHBoxLayout()
        self._c_orders  = StatCard("Orders",       "—", "🧾", THEME["accent"])
        self._c_revenue = StatCard("Revenue",       "—", "$",  THEME["success"])
        self._c_profit  = StatCard("Gross Profit",  "—", "📈", THEME["warning"])
        self._c_avg     = StatCard("Avg Order",     "—", "⌀",  THEME["text_secondary"])
        for c in [self._c_orders, self._c_revenue, self._c_profit, self._c_avg]:
            sr.addWidget(c)
        lay.addLayout(sr)

        # Orders table
        self._tbl = styled_table(
            ["Order No", "Date", "Cashier", "Items",
             "Subtotal", "Discount", "Tax", "Total", "Payment", "Status"]
        )
        self._tbl.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tbl.doubleClicked.connect(self._view_order)
        lay.addWidget(self._tbl)

        # Row actions
        br = QHBoxLayout()
        view_btn = QPushButton("👁  View Receipt"); view_btn.clicked.connect(self._view_order)
        void_btn = QPushButton("⊗  Void Order"); void_btn.setObjectName("danger_btn"); void_btn.clicked.connect(self._void_order)
        br.addWidget(view_btn); br.addWidget(void_btn); br.addStretch()
        lay.addLayout(br)

    # ── Data ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        d_from = self._from.date().toString("yyyy-MM-dd")
        d_to   = self._to.date().toString("yyyy-MM-dd")

        rows = OrderQueries.get_orders(d_from, d_to)
        completed = [r for r in rows if r["status"] == "completed"]
        total_rev = sum(r["total"] for r in completed)
        profit    = ReportQueries.sales_profit(d_from, d_to)["gross_profit"]
        avg       = total_rev / len(completed) if completed else 0

        self._c_orders.set_value(len(rows))
        self._c_revenue.set_value(f"${total_rev:,.2f}")
        self._c_profit.set_value(f"${profit:,.2f}")
        self._c_avg.set_value(f"${avg:.2f}")

        self._rows_cache = rows
        self._tbl.setRowCount(0)
        for r in rows:
            ri = self._tbl.rowCount()
            self._tbl.insertRow(ri)
            cashier = r.get("full_name") or r.get("username") or "—"
            cells = [
                r["order_no"], r["created_at"][:16], cashier,
                str(r["item_count"]),
                f"${r['subtotal']:.2f}", f"${r['discount']:.2f}",
                f"${r['tax_amount']:.2f}", f"${r['total']:.2f}",
                r["payment_type"], r["status"],
            ]
            for ci, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                item.setData(0x0100, r)       # Qt.ItemDataRole.UserRole
                if ci == 9 and r["status"] == "void":
                    item.setForeground(QColor(THEME["danger"]))
                self._tbl.setItem(ri, ci, item)

    def _selected(self) -> dict | None:
        row = self._tbl.currentRow()
        if row < 0:
            return None
        return self._tbl.item(row, 0).data(0x0100)

    # ── Actions ───────────────────────────────────────────────────
    def _view_order(self) -> None:
        o = self._selected()
        if not o:
            return
        items = OrderQueries.get_order_items(o["id"])
        ReceiptDialog(o, items, self).exec()

    def _void_order(self) -> None:
        o = self._selected()
        if not o:
            return
        if o["status"] == "void":
            QMessageBox.information(self, "Already Voided",
                                    "This order is already voided.")
            return
        if (QMessageBox.question(
            self, "Void Order",
            f"Void order {o['order_no']}?\nThis will restore stock.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes):
            OrderQueries.void_order(o["id"])
            self.refresh()

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Sales CSV",
            f"sales_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return
        headers = [
            "Order No", "Date", "Cashier", "Items", "Subtotal",
            "Discount", "Tax", "Total", "Payment", "Status",
        ]
        data_rows = [
            [
                r["order_no"], r["created_at"][:16],
                r.get("username") or "",
                r["item_count"],
                f"{r['subtotal']:.2f}", f"{r['discount']:.2f}",
                f"{r['tax_amount']:.2f}", f"{r['total']:.2f}",
                r["payment_type"], r["status"],
            ]
            for r in self._rows_cache
        ]
        export_csv(path, headers, data_rows)
        QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
