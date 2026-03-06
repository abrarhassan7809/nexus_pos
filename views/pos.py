from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QHeaderView, QMessageBox, QScrollArea, QSplitter,
    QGridLayout, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from database import ProductQueries, OrderQueries
from utils import next_order_no, format_currency, now_str, save_order_txt, save_order_pdf
from utils.theme import ThemeManager as _TM
T = _TM().palette
from widgets import make_table_item
from widgets.base import ThemedTable


# ─── Edit Cart Item Dialog ─────────────────────────────────────────────────────
class EditCartItemDialog(QDialog):
    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Item")
        self.setFixedSize(320, 200)
        self._item = item
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(QLabel(f"<b>{self._item['name']}</b>"))

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setValue(self._item['qty'])
        form.addRow("Quantity:", self.qty_spin)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setValue(self._item['price'])
        form.addRow("Unit Price:", self.price_spin)
        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Update")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

    def get_values(self):
        return self.qty_spin.value(), self.price_spin.value()


# ─── Receipt Dialog ────────────────────────────────────────────────────────────
class ReceiptDialog(QDialog):
    """
    Shows the receipt after a sale.

    Buttons:
      🖨 Print     — send to printer, dialog stays open
      📄 Save PDF  — pick location, save PDF, dialog stays open
      💾 Save TXT  — pick location, save TXT, dialog stays open
      Cancel       — close dialog; caller decides whether to clear the cart
                     based on dialog result (Rejected = keep cart, Accepted = clear)

    The dialog returns:
      QDialog.DialogCode.Accepted  when user saves at least once (cart should clear)
      QDialog.DialogCode.Rejected  when user only cancels (cart stays)
    """

    def __init__(self, order_data: dict, items: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Receipt — {order_data['order_no']}")
        self.setMinimumSize(440, 580)
        self._order  = order_data
        self._items  = items
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Receipt content ────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(32, 28, 32, 20)
        cl.setSpacing(4)

        def lbl(text, bold=False, size=12,
                align=Qt.AlignmentFlag.AlignLeft, color=None):
            l = QLabel(text)
            l.setAlignment(align)
            style = f"font-size: {size}px;"
            if bold:  style += "font-weight: 700;"
            if color: style += f"color: {color};"
            l.setStyleSheet(style)
            return l

        cl.addWidget(lbl("NEXUS POS", True, 22,
                         Qt.AlignmentFlag.AlignCenter, T['accent']))
        cl.addWidget(lbl("Point of Sale System", False, 11,
                         Qt.AlignmentFlag.AlignCenter, T['text_muted']))
        cl.addSpacing(10)

        def hr():
            s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
            s.setStyleSheet(f"color: {T['border']};"); return s

        cl.addWidget(hr())
        cl.addWidget(lbl(f"Order:   {self._order['order_no']}", True))
        cl.addWidget(lbl(f"Date:    {self._order.get('created_at', now_str())[:19]}",
                         color=T['text_muted']))
        cl.addWidget(lbl(f"Cashier: {self._order.get('username', '—')}",
                         color=T['text_muted']))
        cl.addSpacing(6)
        cl.addWidget(hr())

        for item in self._items:
            row = QHBoxLayout()
            name_l = QLabel(f"{item['name']} ×{item['qty']}")
            name_l.setStyleSheet("font-size: 12px;")
            subtot = QLabel(format_currency(item['subtotal']))
            subtot.setStyleSheet("font-size: 12px; font-weight: 600;")
            subtot.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(name_l); row.addWidget(subtot)
            cl.addLayout(row)
            cl.addWidget(lbl(f"  @ {format_currency(item['price'])}",
                             color=T['text_muted'], size=11))

        cl.addSpacing(6)
        cl.addWidget(hr())

        def total_row(label, value, bold=False, color=None):
            row = QHBoxLayout()
            l = QLabel(label); v = QLabel(format_currency(value))
            v.setAlignment(Qt.AlignmentFlag.AlignRight)
            if bold:
                l.setStyleSheet("font-weight: 700; font-size: 14px;")
                v.setStyleSheet(f"font-weight: 700; font-size: 14px; "
                                f"color: {color or T['success']};")
            elif color:
                v.setStyleSheet(f"color: {color};")
            row.addWidget(l); row.addWidget(v)
            cl.addLayout(row)

        total_row("Subtotal:", self._order['subtotal'])
        if self._order['discount'] > 0:
            total_row("Discount:", -self._order['discount'], color=T['warning'])
        total_row("Tax:",      self._order['tax'])
        total_row("TOTAL:",    self._order['total'], True)
        total_row("Payment:",  self._order['payment'])
        total_row("Change:",   self._order['change_due'], color=T['info'])
        cl.addWidget(lbl(f"Method: {self._order['pay_method'].upper()}",
                         color=T['text_muted']))
        cl.addSpacing(14)
        cl.addWidget(lbl("Thank you for your purchase!", False, 12,
                         Qt.AlignmentFlag.AlignCenter, T['text_muted']))
        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # ── Separator ─────────────────────────────────────────────────────────
        sep_frame = QFrame()
        sep_frame.setFrameShape(QFrame.Shape.HLine)
        sep_frame.setStyleSheet(f"color: {T['border']};")
        layout.addWidget(sep_frame)

        # ── Button row ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(16, 10, 16, 14)
        btn_row.setSpacing(8)

        print_btn = QPushButton("🖨  Print")
        print_btn.setObjectName("ghost")
        print_btn.setFixedHeight(36)
        print_btn.clicked.connect(self._print_receipt)

        pdf_btn = QPushButton("📄  Save PDF")
        pdf_btn.setObjectName("primary")
        pdf_btn.setFixedHeight(36)
        pdf_btn.clicked.connect(self._save_pdf)

        txt_btn = QPushButton("💾  Save TXT")
        txt_btn.setObjectName("ghost")
        txt_btn.setFixedHeight(36)
        txt_btn.clicked.connect(self._save_txt)

        # Cancel always just closes the receipt — never clears the cart.
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("ghost")
        self._cancel_btn.setFixedHeight(36)
        self._cancel_btn.clicked.connect(self._on_cancel)

        btn_row.addWidget(print_btn)
        btn_row.addWidget(pdf_btn)
        btn_row.addWidget(txt_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

        # ── Status label (shows save confirmation inline) ──────────────────────
        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(
            f"color: {T['success']}; font-size: 11px; padding: 0 16px 6px;")
        self._status_lbl.setWordWrap(True)
        layout.addWidget(self._status_lbl)

    # ── Receipt text ──────────────────────────────────────────────────────────
    def _receipt_text(self) -> str:
        lines = ["=" * 40, "          NEXUS POS SYSTEM", "=" * 40,
                 f"Order:   {self._order['order_no']}",
                 f"Date:    {self._order.get('created_at', now_str())[:19]}",
                 f"Cashier: {self._order.get('username', '—')}",
                 f"Method:  {self._order.get('pay_method', '').upper()}",
                 "-" * 40]
        for item in self._items:
            lines.append(f"  {item['name'][:24]:<24} x{item['qty']}")
            lines.append(f"  @ {format_currency(item['price'])} = "
                         f"{format_currency(item['subtotal'])}")
        lines += ["-" * 40,
                  f"  Subtotal : {format_currency(self._order['subtotal']):>10}",
                  f"  Discount : {format_currency(self._order['discount']):>10}",
                  f"  Tax      : {format_currency(self._order['tax']):>10}",
                  f"  TOTAL    : {format_currency(self._order['total']):>10}",
                  f"  Payment  : {format_currency(self._order['payment']):>10}",
                  f"  Change   : {format_currency(self._order['change_due']):>10}",
                  "=" * 40, "    Thank you for your purchase!", "=" * 40]
        return "\n".join(lines)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _mark_saved(self, path: str):
        self._status_lbl.setText(f"✓  Saved: {path}")

    def _on_cancel(self):
        self.reject()

    def _print_receipt(self):
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QTextDocument, QPageSize
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            dlg = QPrintDialog(printer, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                doc = QTextDocument()
                doc.setPlainText(self._receipt_text())
                doc.print_(printer)
        except Exception as e:
            QMessageBox.warning(self, "Print Error", str(e))

    def _save_pdf(self):
        try:
            saved = save_order_pdf(self._order, self._items)
            if saved:
                self._mark_saved("Save Receipt as PDF")
            else:
                QMessageBox.warning(
                    self, "Missing Library",
                    "reportlab is not installed.\n\n"
                    "Run:  pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))

    def _save_txt(self):
        try:
            save_order_txt(self._order, self._items)
            self._mark_saved("Save Receipt as TXT")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))



# ─── POS Tab ───────────────────────────────────────────────────────────────────
class PosTab(QWidget):
    order_completed = Signal()

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._cart: list[dict] = []
        self._tax_rate = 0.08
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(2)

        # ── LEFT: Product catalog ──────────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 12, 6, 12)
        ll.setSpacing(8)

        # Search + category in one row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search product or SKU…")
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._filter_products)
        filter_row.addWidget(self.search_input, 3)

        self.cat_combo = QComboBox()
        self.cat_combo.setFixedHeight(36)
        self.cat_combo.setMinimumWidth(130)
        self.cat_combo.addItem("All Categories", None)
        for c in ProductQueries.get_categories():
            self.cat_combo.addItem(c['name'], c['id'])
        self.cat_combo.currentIndexChanged.connect(self._filter_products)
        filter_row.addWidget(self.cat_combo, 2)

        ll.addLayout(filter_row)

        self.product_scroll = QScrollArea()
        self.product_scroll.setWidgetResizable(True)
        self.product_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.product_container = QWidget()
        self.product_grid = QGridLayout(self.product_container)
        self.product_grid.setSpacing(8)
        self.product_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.product_scroll.setWidget(self.product_container)
        ll.addWidget(self.product_scroll)
        splitter.addWidget(left)

        # ── RIGHT: Cart ────────────────────────────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 12, 12, 12)
        rl.setSpacing(8)

        order_hdr = QHBoxLayout()
        self.order_lbl = QLabel("NEW ORDER")
        self.order_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {T['accent']};")
        order_hdr.addWidget(self.order_lbl)
        order_hdr.addStretch()
        self.order_no_lbl = QLabel("")
        self.order_no_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px;")
        order_hdr.addWidget(self.order_no_lbl)
        rl.addLayout(order_hdr)

        # Cart table — ThemedTable auto-updates colours on theme toggle
        self.cart_table = ThemedTable()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Price", "Qty", "Subtotal", ""])
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.verticalHeader().setDefaultSectionSize(34)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cart_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setShowGrid(True)

        ch = self.cart_table.horizontalHeader()
        ch.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        ch.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(1, 75)
        ch.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(2, 50)
        ch.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(3, 85)
        ch.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(4, 30)
        ch.setHighlightSections(False)
        self.cart_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.cart_table.setMinimumHeight(200)

        # FIX: connect ONCE here so it doesn't stack duplicate connections on every refresh
        self.cart_table.cellDoubleClicked.connect(self._edit_cart_item)
        rl.addWidget(self.cart_table)

        # Cart actions
        cart_act = QHBoxLayout()
        clear_btn = QPushButton("🗑  Clear Cart")
        clear_btn.setObjectName("danger")
        clear_btn.setFixedHeight(30)
        clear_btn.clicked.connect(self._clear_cart)
        cart_act.addWidget(clear_btn)
        cart_act.addStretch()
        hint = QLabel("Double-click item to edit")
        hint.setStyleSheet(f"color: {T['text_dim']}; font-size: 11px;")
        cart_act.addWidget(hint)
        rl.addLayout(cart_act)

        # Discount / tax row
        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("Discount ($):"))
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 999999)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setFixedWidth(90)
        self.discount_spin.setFixedHeight(32)
        self.discount_spin.valueChanged.connect(self._update_totals)
        disc_row.addWidget(self.discount_spin)
        disc_row.addStretch()
        disc_row.addWidget(QLabel(f"Tax ({int(self._tax_rate * 100)}%):"))
        self.tax_lbl = QLabel("$0.00")
        self.tax_lbl.setStyleSheet(f"color: {T['text_muted']};")
        disc_row.addWidget(self.tax_lbl)
        rl.addLayout(disc_row)

        # Summary card
        summary = QFrame()
        summary.setObjectName("card2")
        sl = QGridLayout(summary)
        sl.setContentsMargins(14, 10, 14, 10)
        sl.setSpacing(3)
        sl.setColumnStretch(0, 1)

        self.subtotal_lbl = QLabel("$0.00")
        sl.addWidget(QLabel("Subtotal:"), 0, 0)
        sl.addWidget(self.subtotal_lbl, 0, 1, Qt.AlignmentFlag.AlignRight)

        total_title = QLabel("TOTAL:")
        total_title.setStyleSheet("font-weight: 700; font-size: 15px;")
        self.total_lbl = QLabel("$0.00")
        self.total_lbl.setStyleSheet(
            f"font-size: 24px; font-weight: 900; color: {T['success']};")
        sl.addWidget(total_title, 1, 0)
        sl.addWidget(self.total_lbl, 1, 1, Qt.AlignmentFlag.AlignRight)
        rl.addWidget(summary)

        # Payment row
        pay_row = QHBoxLayout()
        pay_row.setSpacing(8)
        pay_row.addWidget(QLabel("Method:"))
        self.pay_method = QComboBox()
        self.pay_method.addItems(["Cash", "Card", "GCash", "PayMaya", "Other"])
        self.pay_method.setFixedHeight(32)
        pay_row.addWidget(self.pay_method)
        pay_row.addWidget(QLabel("Received:"))
        self.payment_spin = QDoubleSpinBox()
        self.payment_spin.setRange(0, 999999)
        self.payment_spin.setDecimals(2)
        self.payment_spin.setFixedHeight(32)
        self.payment_spin.setMinimumWidth(90)
        self.payment_spin.valueChanged.connect(self._update_change)
        pay_row.addWidget(self.payment_spin)
        pay_row.addWidget(QLabel("Change:"))
        self.change_lbl = QLabel("$0.00")
        self.change_lbl.setStyleSheet(f"color: {T['info']}; font-weight: 600;")
        pay_row.addWidget(self.change_lbl)
        rl.addLayout(pay_row)

        # Checkout button
        self.checkout_btn = QPushButton("✅  COMPLETE SALE")
        self.checkout_btn.setObjectName("success")
        self.checkout_btn.setFixedHeight(48)
        self.checkout_btn.setStyleSheet(
            f"QPushButton#success {{ font-size: 15px; font-weight: 700; "
            f"letter-spacing: 1px; border-radius: 10px; }}"
        )
        self.checkout_btn.clicked.connect(self._checkout)
        rl.addWidget(self.checkout_btn)

        splitter.addWidget(right)
        splitter.setSizes([560, 440])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(splitter)

        self._update_order_no()

    def _update_order_no(self):
        no = next_order_no()
        self.order_no_lbl.setText(f"#{no}")
        self._current_order_no = no

    # ── Product grid ───────────────────────────────────────────────────────────
    def _load_products(self, search="", category_id=None):
        while self.product_grid.count():
            item = self.product_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        products = ProductQueries.search(search) if search else ProductQueries.get_all()
        if category_id:
            products = [p for p in products if p['category_id'] == category_id]

        cols = 3
        for idx, product in enumerate(products):
            card = self._make_product_card(product)
            self.product_grid.addWidget(card, idx // cols, idx % cols)

    def _make_product_card(self, product) -> QFrame:
        card = QFrame()
        card.setObjectName("card2")
        card.setFixedHeight(86)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)

        name_lbl = QLabel(product['name'])
        name_lbl.setStyleSheet("font-weight: 600; font-size: 12px;")
        name_lbl.setWordWrap(True)
        lay.addWidget(name_lbl)

        price_lbl = QLabel(format_currency(product['price']))
        price_lbl.setStyleSheet(f"color: {T['success']}; font-weight: 700; font-size: 13px;")
        lay.addWidget(price_lbl)

        stock_color = T['danger'] if product['stock'] <= product['low_stock'] else T['text_muted']
        stock_lbl = QLabel(f"Stock: {product['stock']} {product['unit']}")
        stock_lbl.setStyleSheet(f"color: {stock_color}; font-size: 11px;")
        lay.addWidget(stock_lbl)

        def on_click(event, p=product):
            if p['stock'] <= 0:
                QMessageBox.warning(self, "Out of Stock", f"'{p['name']}' is out of stock.")
                return
            self._add_to_cart(p)

        card.mousePressEvent = on_click

        if product['stock'] <= 0:
            card.setStyleSheet(
                f"QFrame#card2 {{ background: {T['surface']}; "
                f"border: 1px solid {T['surface3']}; border-radius: 8px; }}")
            name_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #555;")

        return card

    def _filter_products(self):
        self._load_products(
            self.search_input.text().strip(),
            self.cat_combo.currentData()
        )

    # ── Cart logic ─────────────────────────────────────────────────────────────
    def _add_to_cart(self, product):
        for item in self._cart:
            if item['product_id'] == product['id']:
                if item['qty'] >= product['stock']:
                    QMessageBox.warning(self, "Stock Limit",
                                        f"Only {product['stock']} units available.")
                    return
                item['qty'] += 1
                item['subtotal'] = item['qty'] * item['price']
                self._refresh_cart()
                return
        self._cart.append({
            'product_id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'qty': 1,
            'subtotal': product['price'],
        })
        self._refresh_cart()

    def _refresh_cart(self):
        RIGHT  = Qt.AlignmentFlag.AlignRight  | Qt.AlignmentFlag.AlignVCenter
        CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        # FIX: block signals while repopulating to prevent cellDoubleClicked firing
        self.cart_table.blockSignals(True)
        self.cart_table.setRowCount(0)
        self.cart_table.setRowCount(len(self._cart))

        for i, item in enumerate(self._cart):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 1, make_table_item(
                format_currency(item['price']), RIGHT))
            self.cart_table.setItem(i, 2, make_table_item(str(item['qty']), CENTER))
            self.cart_table.setItem(i, 3, make_table_item(
                format_currency(item['subtotal']), RIGHT, T['success']))

            rm_btn = QPushButton("✕")
            rm_btn.setFixedSize(24, 24)
            rm_btn.setStyleSheet(
                f"QPushButton {{ background: {T['danger']}; color: white; "
                f"border: none; border-radius: 4px; font-size: 10px; }}")
            rm_btn.clicked.connect(lambda _, idx=i: self._remove_cart_item(idx))
            self.cart_table.setCellWidget(i, 4, rm_btn)

        self.cart_table.blockSignals(False)
        self._update_totals()

    def _edit_cart_item(self, row, col):
        # FIX: ignore clicks on the remove-button column
        if col == 4 or row >= len(self._cart):
            return
        dlg = EditCartItemDialog(self._cart[row], self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            qty, price = dlg.get_values()
            self._cart[row]['qty']      = qty
            self._cart[row]['price']    = price
            self._cart[row]['subtotal'] = qty * price
            self._refresh_cart()

    def _remove_cart_item(self, idx):
        if 0 <= idx < len(self._cart):
            self._cart.pop(idx)
            self._refresh_cart()

    def _clear_cart(self):
        if not self._cart:
            return
        if QMessageBox.question(
                self, "Clear Cart", "Clear all items?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self._cart.clear()
            self._refresh_cart()

    # ── Totals ─────────────────────────────────────────────────────────────────
    def _calc(self):
        subtotal = sum(i['subtotal'] for i in self._cart)
        discount = self.discount_spin.value()
        tax      = (subtotal - discount) * self._tax_rate
        total    = subtotal - discount + tax
        return subtotal, discount, tax, max(0.0, total)

    def _update_totals(self):
        subtotal, _, tax, total = self._calc()
        self.subtotal_lbl.setText(format_currency(subtotal))
        self.tax_lbl.setText(format_currency(tax))
        self.total_lbl.setText(format_currency(total))
        self._update_change()

    def _update_change(self):
        _, _, _, total = self._calc()
        payment = self.payment_spin.value()
        change  = payment - total
        self.change_lbl.setText(format_currency(max(0.0, change)))
        if change < 0 and self.pay_method.currentText() == "Cash":
            self.change_lbl.setStyleSheet(f"color: {T['danger']}; font-weight: 600;")
        else:
            self.change_lbl.setStyleSheet(f"color: {T['info']}; font-weight: 600;")

    # ── Checkout ───────────────────────────────────────────────────────────────
    def _checkout(self):
        if not self._cart:
            QMessageBox.warning(self, "Empty Cart", "Add items to the cart first.")
            return

        subtotal, discount, tax, total = self._calc()
        payment = self.payment_spin.value()
        method  = self.pay_method.currentText().lower()

        if method == "cash" and payment < total:
            QMessageBox.warning(
                self, "Insufficient Payment",
                f"Payment {format_currency(payment)} < Total {format_currency(total)}")
            return

        change   = max(0.0, payment - total)
        order_no = self._current_order_no

        order_id = OrderQueries.create_order(
            order_no=order_no, user_id=self._user['id'],
            items=self._cart, subtotal=subtotal, discount=discount,
            tax=tax, total=total, payment=payment,
            change_due=change, pay_method=method,
        )

        order, items = OrderQueries.get_by_id(order_id)
        order_dict   = dict(order)
        order_dict['username'] = self._user['username']
        item_dicts = [dict(i) for i in items]

        receipt = ReceiptDialog(order_dict, item_dicts, self)
        receipt.exec()  # result ignored — cart behaviour is always the same

        # Order is committed to DB. Clear cart and prepare next order.
        # The receipt dialog's Cancel button only closes the dialog window;
        # it does NOT undo the sale or affect the cart reset below.
        self._cart.clear()
        self.discount_spin.setValue(0)
        self.payment_spin.setValue(0)
        self._refresh_cart()
        self._update_order_no()
        self._load_products()
        self.order_completed.emit()