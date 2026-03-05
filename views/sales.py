from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QDateEdit, QFileDialog, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from database import OrderQueries
from utils import format_currency, short_date, export_csv, today_str
from utils.theme import THEME as T
from widgets import styled_table, make_table_item, SectionTitle


class OrderDetailDialog(QDialog):
    def __init__(self, order, items, user, parent=None):
        super().__init__(parent)
        self._order = order
        self._items = items
        self._user  = user
        self.setWindowTitle(f"Order — {order['order_no']}")
        self.setMinimumSize(500, 500)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Info grid
        info = QHBoxLayout()
        left = QVBoxLayout(); left.setSpacing(4)
        right = QVBoxLayout(); right.setSpacing(4)
        for label, val in [("Order:", self._order['order_no']),
                           ("Date:", short_date(self._order['created_at'])),
                           ("Cashier:", self._order['username'] or '—'),
                           ("Method:", self._order['pay_method'].upper())]:
            row = QHBoxLayout()
            lbl = QLabel(f"<b>{label}</b>")
            lbl.setFixedWidth(60)
            row.addWidget(lbl)
            row.addWidget(QLabel(val))
            left.addLayout(row)

        for label, val, color in [
            ("Status:",   self._order['status'].upper(),              T['success'] if self._order['status']=='completed' else T['danger']),
            ("Subtotal:", format_currency(self._order['subtotal']),   None),
            ("Discount:", format_currency(self._order['discount']),   T['warning']),
            ("Tax:",      format_currency(self._order['tax']),        None),
            ("TOTAL:",    format_currency(self._order['total']),      T['success']),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"<b>{label}</b>")
            lbl.setFixedWidth(70)
            val_lbl = QLabel(val)
            if color:
                val_lbl.setStyleSheet(f"color: {color}; font-weight: 600;")
            row.addWidget(lbl)
            row.addWidget(val_lbl)
            right.addLayout(row)

        info.addLayout(left)
        info.addSpacing(20)
        info.addLayout(right)
        info.addStretch()
        layout.addLayout(info)

        # Items table: Product(stretch), Price, Qty, Subtotal fixed
        tbl = styled_table(["Product", "Unit Price", "Qty", "Subtotal"],
                           col_widths=[None, 90, 60, 90], stretch_col=0)
        tbl.setRowCount(len(self._items))
        RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        for i, item in enumerate(self._items):
            tbl.setItem(i, 0, QTableWidgetItem(item['name']))
            tbl.setItem(i, 1, make_table_item(format_currency(item['price']),  RIGHT))
            tbl.setItem(i, 2, make_table_item(str(item['qty']),                CENTER))
            tbl.setItem(i, 3, make_table_item(format_currency(item['subtotal']), RIGHT,
                                              T['success']))
        layout.addWidget(tbl)

        # Buttons
        btn_row = QHBoxLayout()
        if self._order['status'] == 'completed' and self._user['role'] == 'admin':
            void_btn = QPushButton("Void Order")
            void_btn.setObjectName("danger")
            void_btn.clicked.connect(self._void)
            btn_row.addWidget(void_btn)
        btn_row.addStretch()

        print_btn = QPushButton("🖨  Print")
        print_btn.setObjectName("ghost")
        print_btn.clicked.connect(self._print)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(print_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _void(self):
        if QMessageBox.question(
                self, "Void Order",
                f"Void {self._order['order_no']}?\nStock will be restored.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            OrderQueries.void_order(self._order['id'], self._user['id'])
            self.accept()

    def _print(self):
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        from PySide6.QtGui import QTextDocument
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            lines = [
                f"Order: {self._order['order_no']}",
                f"Date:  {self._order['created_at'][:19]}",
                f"{'—'*36}",
            ]
            for item in self._items:
                lines.append(f"{item['name']} x{item['qty']}  {format_currency(item['subtotal'])}")
            lines += [
                f"{'—'*36}",
                f"Total:  {format_currency(self._order['total'])}",
                f"Paid:   {format_currency(self._order['payment'])}",
                f"Change: {format_currency(self._order['change_due'])}",
            ]
            doc = QTextDocument()
            doc.setPlainText("\n".join(lines))
            doc.print_(printer)


class SalesTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._orders = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Sales History"))
        hdr.addStretch()
        layout.addLayout(hdr)

        # Filters
        filters = QHBoxLayout()
        filters.setSpacing(8)
        filters.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setFixedHeight(34)
        filters.addWidget(self.date_from)

        filters.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedHeight(34)
        filters.addWidget(self.date_to)

        filters.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "completed", "voided"])
        self.status_combo.setFixedHeight(34)
        filters.addWidget(self.status_combo)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("primary")
        search_btn.setFixedHeight(34)
        search_btn.clicked.connect(self.refresh)
        filters.addWidget(search_btn)
        filters.addStretch()

        export_btn = QPushButton("📊  Export CSV")
        export_btn.setObjectName("ghost")
        export_btn.setFixedHeight(34)
        export_btn.clicked.connect(self._export)
        filters.addWidget(export_btn)
        layout.addLayout(filters)

        # Summary strip
        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px;")
        layout.addWidget(self.summary_lbl)

        # Table
        # Order#=150, Cashier=90, Subtotal=90, Disc=80, Tax=80, Total=90, Method=80, Status=80, Date=stretch
        self.table = styled_table(
            ["Order #", "Cashier", "Subtotal", "Discount", "Tax", "Total", "Method", "Status", "Date"],
            col_widths=[150, 90, 90, 80, 80, 90, 80, 75, None],
            stretch_col=8
        )
        self.table.cellDoubleClicked.connect(self._open_order)
        layout.addWidget(self.table)

        hint = QLabel("Double-click a row to view order details.")
        hint.setStyleSheet(f"color: {T['text_dim']}; font-size: 11px;")
        layout.addWidget(hint)

    def refresh(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to   = self.date_to.date().toString("yyyy-MM-dd")
        status    = self.status_combo.currentText()
        status    = None if status == "All" else status

        self._orders = list(OrderQueries.get_all(date_from, date_to, status))

        RIGHT  = Qt.AlignmentFlag.AlignRight  | Qt.AlignmentFlag.AlignVCenter
        CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        self.table.setRowCount(0)
        self.table.setRowCount(len(self._orders))

        total_rev = 0.0
        for i, o in enumerate(self._orders):
            self.table.setItem(i, 0, QTableWidgetItem(o['order_no']))
            self.table.setItem(i, 1, QTableWidgetItem(o['username'] or '—'))
            self.table.setItem(i, 2, make_table_item(format_currency(o['subtotal']),  RIGHT))
            self.table.setItem(i, 3, make_table_item(format_currency(o['discount']),  RIGHT, T['warning']))
            self.table.setItem(i, 4, make_table_item(format_currency(o['tax']),       RIGHT))
            self.table.setItem(i, 5, make_table_item(format_currency(o['total']),     RIGHT, T['success']))
            self.table.setItem(i, 6, make_table_item(o['pay_method'].upper(),         CENTER))
            status_color = T['success'] if o['status'] == 'completed' else T['danger']
            self.table.setItem(i, 7, make_table_item(o['status'].upper(), CENTER, status_color))
            self.table.setItem(i, 8, QTableWidgetItem(short_date(o['created_at'])))
            if o['status'] == 'completed':
                total_rev += o['total']

        count = sum(1 for o in self._orders if o['status'] == 'completed')
        self.summary_lbl.setText(
            f"Showing {len(self._orders)} orders  ·  "
            f"Completed: {count}  ·  "
            f"Revenue: {format_currency(total_rev)}"
        )

    def _open_order(self, row, col):
        if row >= len(self._orders):
            return
        o = self._orders[row]
        order, items = OrderQueries.get_by_id(o['id'])
        dlg = OrderDetailDialog(dict(order), [dict(i) for i in items], self._user, self)
        dlg.exec()
        self.refresh()

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", f"sales_{today_str()}.csv", "CSV Files (*.csv)")
        if path and self._orders:
            headers = ["order_no", "username", "subtotal", "discount", "tax",
                       "total", "pay_method", "status", "created_at"]
            export_csv(self._orders, headers, path)
            QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
