from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit, QComboBox, QSpinBox,
                               QDoubleSpinBox, QPushButton, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
                               QTextEdit, QFileDialog, QGridLayout, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
import datetime
from database.queries import ProductQueries, OrderQueries
from utils.theme import THEME
from utils.helpers import next_order_no
from widgets.base import Divider, styled_table
from PySide6.QtGui import QFont as _F
from PySide6.QtGui import QColor


# ═══════════════════════════════════════════════════════════════════
#  POS TAB
# ═══════════════════════════════════════════════════════════════════
class PosTab(QWidget):
    """
    Main POS tab.
    Left  → product browser.
    Right → TOP: cart orders table + action buttons (stretches).
            BOTTOM: totals + payment side-by-side + process button (fixed).
    """

    order_saved = Signal()

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.cart: list[dict] = []
        self._order_no = ""
        self._build_ui()
        self._load_products()

    # ─────────────────────────────────────────────────────────────
    #  TOP-LEVEL LAYOUT
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_product_panel())
        splitter.addWidget(self._build_order_panel())
        splitter.setSizes([620, 500])
        root.addWidget(splitter)
        self._new_order_no()

    # ─────────────────────────────────────────────────────────────
    #  LEFT — PRODUCT BROWSER
    # ─────────────────────────────────────────────────────────────
    def _build_product_panel(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        lay.setContentsMargins(0, 0, 0, 0)

        # Search + category filter
        filter_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search product or scan barcode…")
        self._search.setFixedHeight(38)
        self._search.textChanged.connect(self._filter_products)

        self._cat_combo = QComboBox()
        self._cat_combo.setFixedHeight(38)
        self._cat_combo.setFixedWidth(160)
        self._cat_combo.currentIndexChanged.connect(self._filter_products)

        filter_row.addWidget(self._search)
        filter_row.addWidget(self._cat_combo)
        lay.addLayout(filter_row)

        # Product table
        self._prod_tbl = styled_table(
            ["ID", "Product", "Category", "Price", "Stock", "Unit"]
        )
        self._prod_tbl.setColumnWidth(0,  40)
        self._prod_tbl.setColumnWidth(1, 180)
        self._prod_tbl.setColumnWidth(2, 110)
        self._prod_tbl.setColumnWidth(3,  75)
        self._prod_tbl.setColumnWidth(4,  60)
        self._prod_tbl.setColumnWidth(5,  50)
        self._prod_tbl.doubleClicked.connect(self._add_to_cart)
        lay.addWidget(self._prod_tbl, stretch=1)

        # Qty + Add button
        btn_row = QHBoxLayout()
        qty_lbl = QLabel("Qty:")
        qty_lbl.setStyleSheet("background: transparent;")
        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 9999)
        self._qty_spin.setValue(1)
        self._qty_spin.setFixedHeight(36)
        self._qty_spin.setFixedWidth(80)

        add_btn = QPushButton("＋  Add to Order")
        add_btn.setObjectName("accent_btn")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_to_cart)

        btn_row.addWidget(qty_lbl)
        btn_row.addWidget(self._qty_spin)
        btn_row.addSpacing(8)
        btn_row.addWidget(add_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        return w

    # ─────────────────────────────────────────────────────────────
    #  RIGHT — ORDER PANEL
    # ─────────────────────────────────────────────────────────────
    def _build_order_panel(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)

        # Cart section stretches to fill space
        lay.addWidget(self._build_cart_section(), stretch=1)
        # Summary + payment is fixed at bottom
        lay.addWidget(self._build_bottom_section())
        return w

    # ── CART SECTION (top, stretching) ────────────────────────────
    def _build_cart_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME['bg_panel']};
                border: 1px solid {THEME['border']};
                border-bottom: none;
                border-radius: 8px 8px 0 0;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setSpacing(6)
        lay.setContentsMargins(10, 10, 10, 8)

        # ── Header: title | items badge | order number ────────────
        hdr = QHBoxLayout()

        ttl = QLabel("🛒  Current Order")
        ttl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        ttl.setStyleSheet(
            f"color: {THEME['accent']}; background: transparent; border: none;"
        )

        self._items_badge = QLabel("0 items")
        self._items_badge.setStyleSheet(f"""
            background: {THEME['bg_input']};
            color: {THEME['text_secondary']};
            border: 1px solid {THEME['border']};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)

        self._ono_lbl = QLabel("")
        self._ono_lbl.setStyleSheet(
            f"color: {THEME['text_muted']}; background: transparent; "
            f"font-size: 11px; border: none;"
        )

        hdr.addWidget(ttl)
        hdr.addSpacing(8)
        hdr.addWidget(self._items_badge)
        hdr.addStretch()
        hdr.addWidget(self._ono_lbl)
        lay.addLayout(hdr)

        lay.addWidget(Divider())

        # ── Cart table ────────────────────────────────────────────
        self._cart_tbl = styled_table(
            ["#", "Product", "Unit Price", "Qty", "Disc %", "Subtotal"]
        )
        self._cart_tbl.setColumnWidth(0,  32)
        self._cart_tbl.setColumnWidth(1, 200)
        self._cart_tbl.setColumnWidth(2,  85)
        self._cart_tbl.setColumnWidth(3,  55)
        self._cart_tbl.setColumnWidth(4,  58)
        self._cart_tbl.setMinimumHeight(180)
        self._cart_tbl.setStyleSheet(
            "QTableWidget { border: none; border-radius: 0; background: transparent; }"
        )
        lay.addWidget(self._cart_tbl, stretch=1)

        lay.addWidget(Divider())

        # ── Cart action buttons ───────────────────────────────────
        cab = QHBoxLayout()
        cab.setSpacing(6)

        edit_btn = QPushButton("✏  Edit Item")
        edit_btn.setFixedHeight(30)
        edit_btn.clicked.connect(self._edit_item)

        remove_btn = QPushButton("🗑  Remove")
        remove_btn.setObjectName("danger_btn")
        remove_btn.setFixedHeight(30)
        remove_btn.clicked.connect(self._remove_item)

        clear_btn = QPushButton("✖  Clear All")
        clear_btn.setFixedHeight(30)
        clear_btn.clicked.connect(self._clear_cart)

        cab.addWidget(edit_btn)
        cab.addWidget(remove_btn)
        cab.addWidget(clear_btn)
        cab.addStretch()
        lay.addLayout(cab)

        return frame

    # ── BOTTOM SECTION (fixed height, two columns + process btn) ──
    def _build_bottom_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME['bg_card']};
                border: 1px solid {THEME['border']};
                border-top: 2px solid {THEME['accent']};
                border-radius: 0 0 8px 8px;
            }}
        """)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        # Two-column row: Totals | divider | Payment
        cols = QHBoxLayout()
        cols.setSpacing(14)
        cols.addWidget(self._build_totals_col(), stretch=1)
        cols.addWidget(_vline())
        cols.addWidget(self._build_payment_col(), stretch=1)
        outer.addLayout(cols)

        outer.addWidget(Divider())

        # Full-width process button
        proc_btn = QPushButton("  PROCESS ORDER  →")
        proc_btn.setObjectName("accent_btn")
        proc_btn.setFixedHeight(46)
        proc_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        proc_btn.clicked.connect(self._process_order)
        outer.addWidget(proc_btn)

        return frame

    # ── TOTALS COLUMN ─────────────────────────────────────────────
    def _build_totals_col(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        g = QGridLayout(w)
        g.setSpacing(5)
        g.setContentsMargins(0, 0, 0, 0)
        g.setColumnStretch(1, 1)

        def _lbl(text, bold=False, color=None):
            l = QLabel(text)
            c = color or THEME["text_secondary"]
            s = f"color: {c}; background: transparent;"
            if bold:
                s += " font-weight: 700;"
            l.setStyleSheet(s)
            return l

        def _val(attr, color=None, big=False):
            l = QLabel("$0.00")
            c = color or THEME["text_primary"]
            s = f"color: {c}; background: transparent; font-weight: 700;"
            if big:
                s += " font-size: 18px;"
            l.setStyleSheet(s)
            l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            setattr(self, attr, l)
            return l

        def _spin(attr, default=0.0):
            s = QDoubleSpinBox()
            s.setRange(0, 100)
            s.setSuffix(" %")
            s.setValue(default)
            s.setFixedHeight(28)
            s.setFixedWidth(88)
            s.valueChanged.connect(self._recalc)
            setattr(self, attr, s)
            return s

        g.addWidget(_lbl("Items"),            0, 0)
        g.addWidget(_val("_lbl_items"),        0, 1)
        g.addWidget(_lbl("Subtotal"),          1, 0)
        g.addWidget(_val("_lbl_subtotal"),     1, 1)
        g.addWidget(_lbl("Discount"),          2, 0)
        g.addWidget(_spin("_disc_spin", 0.0),  2, 1, Qt.AlignmentFlag.AlignRight)
        g.addWidget(_lbl("Tax Rate"),          3, 0)
        g.addWidget(_spin("_tax_spin", 8.0),   3, 1, Qt.AlignmentFlag.AlignRight)
        g.addWidget(_lbl("Tax Amount"),        4, 0)
        g.addWidget(_val("_lbl_tax"),          4, 1)

        sep = Divider()
        g.addWidget(sep, 5, 0, 1, 2)

        total_head = _lbl("TOTAL", bold=True, color=THEME["accent"])
        total_head.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        g.addWidget(total_head, 6, 0)
        g.addWidget(_val("_lbl_total", color=THEME["accent"], big=True), 6, 1)

        return w

    # ── PAYMENT COLUMN ────────────────────────────────────────────
    def _build_payment_col(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        g = QGridLayout(w)
        g.setSpacing(6)
        g.setContentsMargins(0, 0, 0, 0)
        g.setColumnStretch(1, 1)

        def _lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent;")
            return l

        # Payment type
        g.addWidget(_lbl("Payment"), 0, 0)
        self._pay_type = QComboBox()
        self._pay_type.addItems(["Cash", "Card", "E-Wallet", "Mixed"])
        self._pay_type.setFixedHeight(30)
        g.addWidget(self._pay_type, 0, 1)

        # Amount paid
        g.addWidget(_lbl("Amount Paid"), 1, 0)
        self._paid_spin = QDoubleSpinBox()
        self._paid_spin.setRange(0, 999999)
        self._paid_spin.setPrefix("$ ")
        self._paid_spin.setDecimals(2)
        self._paid_spin.setFixedHeight(30)
        self._paid_spin.valueChanged.connect(self._recalc_change)
        g.addWidget(self._paid_spin, 1, 1)

        # Change
        g.addWidget(_lbl("Change"), 2, 0)
        self._lbl_change = QLabel("$ 0.00")
        self._lbl_change.setStyleSheet(
            f"color: {THEME['success']}; font-weight: 700; "
            f"font-size: 15px; background: transparent;"
        )
        self._lbl_change.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        g.addWidget(self._lbl_change, 2, 1)

        # Note
        g.addWidget(_lbl("Note"), 3, 0)
        self._note_input = QLineEdit()
        self._note_input.setPlaceholderText("Order note (optional)")
        self._note_input.setFixedHeight(30)
        g.addWidget(self._note_input, 3, 1)

        return w

    # ─────────────────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────────────────
    def _new_order_no(self) -> None:
        self._order_no = next_order_no()
        self._ono_lbl.setText(self._order_no)

    def _load_products(self) -> None:
        self._cat_combo.blockSignals(True)
        self._cat_combo.clear()
        self._cat_combo.addItem("All Categories", 0)
        for cat in ProductQueries.get_categories():
            self._cat_combo.addItem(cat["name"], cat["id"])
        self._cat_combo.blockSignals(False)
        self._filter_products()

    def _filter_products(self) -> None:
        q      = self._search.text().strip()
        cat_id = self._cat_combo.currentData()
        rows   = ProductQueries.get_all(search=q, category_id=cat_id or 0)

        self._prod_tbl.setRowCount(0)
        for r in rows:
            ri = self._prod_tbl.rowCount()
            self._prod_tbl.insertRow(ri)
            cells = [
                str(r["id"]), r["name"], r["cat_name"] or "",
                f"${r['price']:.2f}", str(r["stock"]), r["unit"],
            ]
            for ci, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                item.setData(Qt.ItemDataRole.UserRole, r)
                if ci == 4:
                    if r["stock"] == 0:
                        item.setForeground(QColor(THEME["danger"]))
                    elif r["stock"] <= r["low_stock"]:
                        item.setForeground(QColor(THEME["warning"]))
                self._prod_tbl.setItem(ri, ci, item)

    # ─────────────────────────────────────────────────────────────
    #  CART OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def _add_to_cart(self) -> None:
        row = self._prod_tbl.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Product",
                                    "Please select a product first.")
            return
        pdata = self._prod_tbl.item(row, 0).data(Qt.ItemDataRole.UserRole)
        qty   = self._qty_spin.value()

        if pdata["stock"] < qty:
            QMessageBox.warning(self, "Low Stock",
                                f"Only {pdata['stock']} {pdata['unit']} in stock.")
            return

        # Merge with existing cart line
        for item in self.cart:
            if item["id"] == pdata["id"]:
                new_qty = item["qty"] + qty
                if pdata["stock"] < new_qty:
                    QMessageBox.warning(self, "Low Stock",
                                        f"Max available: {pdata['stock']}.")
                    return
                item["qty"] = new_qty
                item["subtotal"] = round(
                    item["price"] * item["qty"] * (1 - item["disc"] / 100), 2
                )
                self._refresh_cart()
                return

        self.cart.append({
            "id":       pdata["id"],
            "name":     pdata["name"],
            "unit":     pdata["unit"],
            "price":    pdata["price"],
            "qty":      qty,
            "disc":     0.0,
            "subtotal": round(pdata["price"] * qty, 2),
        })
        self._refresh_cart()

    def _refresh_cart(self) -> None:
        self._cart_tbl.setRowCount(0)
        for i, item in enumerate(self.cart):
            ri = self._cart_tbl.rowCount()
            self._cart_tbl.insertRow(ri)
            cells = [
                str(i + 1),
                item["name"],
                f"${item['price']:.2f}",
                str(item["qty"]),
                f"{item['disc']:.0f}%",
                f"${item['subtotal']:.2f}",
            ]
            for ci, txt in enumerate(cells):
                self._cart_tbl.setItem(ri, ci, QTableWidgetItem(txt))

        # Update badge
        n = sum(i["qty"] for i in self.cart)
        self._items_badge.setText(f"{n} item{'s' if n != 1 else ''}")
        self._recalc()

    def _edit_item(self) -> None:
        row = self._cart_tbl.currentRow()
        if row < 0:
            return
        item = self.cart[row]
        dlg = EditCartItemDialog(item, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item["qty"]      = dlg.qty
            item["disc"]     = dlg.disc
            item["subtotal"] = round(
                item["price"] * item["qty"] * (1 - item["disc"] / 100), 2
            )
            self._refresh_cart()

    def _remove_item(self) -> None:
        row = self._cart_tbl.currentRow()
        if row < 0:
            return
        del self.cart[row]
        self._refresh_cart()

    def _clear_cart(self) -> None:
        if not self.cart:
            return
        if (QMessageBox.question(
            self, "Clear Order", "Remove all items from the order?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes):
            self.cart.clear()
            self._refresh_cart()

    # ─────────────────────────────────────────────────────────────
    #  TOTALS CALCULATION
    # ─────────────────────────────────────────────────────────────
    def _recalc(self) -> None:
        subtotal = sum(i["subtotal"] for i in self.cart)
        disc_pct = self._disc_spin.value()
        disc_amt = subtotal * disc_pct / 100
        after    = subtotal - disc_amt
        tax_rate = self._tax_spin.value()
        tax_amt  = after * tax_rate / 100
        total    = after + tax_amt

        self._lbl_items.setText(str(sum(i["qty"] for i in self.cart)))
        self._lbl_subtotal.setText(f"${subtotal:.2f}")
        self._lbl_tax.setText(f"${tax_amt:.2f}")
        self._lbl_total.setText(f"${total:.2f}")
        self._paid_spin.setMinimum(total)
        self._recalc_change()

    def _recalc_change(self) -> None:
        try:
            total = float(self._lbl_total.text().replace("$", "").strip())
        except ValueError:
            total = 0.0
        change = max(0.0, self._paid_spin.value() - total)
        self._lbl_change.setText(f"$ {change:.2f}")

    # ─────────────────────────────────────────────────────────────
    #  PROCESS ORDER
    # ─────────────────────────────────────────────────────────────
    def _process_order(self) -> None:
        if not self.cart:
            QMessageBox.warning(self, "Empty Order",
                                "Add at least one item before processing.")
            return

        try:
            total = float(self._lbl_total.text().replace("$", "").strip())
        except ValueError:
            total = 0.0

        paid = self._paid_spin.value()
        if paid < total:
            QMessageBox.warning(
                self, "Insufficient Payment",
                f"Amount paid (${paid:.2f}) is less than total (${total:.2f}).",
            )
            return

        subtotal = sum(i["subtotal"] for i in self.cart)
        disc_pct = self._disc_spin.value()
        disc_amt = subtotal * disc_pct / 100
        tax_rate = self._tax_spin.value()
        tax_amt  = (subtotal - disc_amt) * tax_rate / 100
        change   = paid - total

        order_data = {
            "order_no":     self._order_no,
            "cashier_id":   self.current_user["id"],
            "subtotal":     subtotal,
            "discount":     disc_amt,
            "tax_rate":     tax_rate,
            "tax_amount":   tax_amt,
            "total":        total,
            "paid":         paid,
            "change":       change,
            "payment_type": self._pay_type.currentText(),
            "note":         self._note_input.text(),
        }
        try:
            order_id = OrderQueries.save_order(order_data, self.cart)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save order:\n{e}")
            return

        self.order_saved.emit()

        order_row  = OrderQueries.get_order(order_id)
        items_rows = OrderQueries.get_order_items(order_id)
        ReceiptDialog(order_row, items_rows, self).exec()

        # Reset for next order
        self.cart.clear()
        self._refresh_cart()
        self._disc_spin.setValue(0)
        self._paid_spin.setValue(0)
        self._note_input.clear()
        self._new_order_no()
        self._filter_products()


# ═══════════════════════════════════════════════════════════════════
#  VERTICAL LINE HELPER
# ═══════════════════════════════════════════════════════════════════
def _vline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setFixedWidth(1)
    f.setStyleSheet(f"background: {THEME['border']}; border: none; max-width: 1px;")
    return f


# ═══════════════════════════════════════════════════════════════════
#  EDIT CART ITEM DIALOG
# ═══════════════════════════════════════════════════════════════════
class EditCartItemDialog(QDialog):
    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Cart Item")
        self.setFixedSize(340, 220)
        self.qty  = item["qty"]
        self.disc = item["disc"]
        self._build(item)

    def _build(self, item: dict) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        name_lbl = QLabel(f"<b>{item['name']}</b>")
        name_lbl.setStyleSheet(
            f"font-size: 14px; color: {THEME['text_primary']}; background: transparent;"
        )
        price_lbl = QLabel(f"Unit price: ${item['price']:.2f} / {item['unit']}")
        price_lbl.setStyleSheet(
            f"color: {THEME['text_secondary']}; background: transparent;"
        )
        lay.addWidget(name_lbl)
        lay.addWidget(price_lbl)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Quantity:"))
        self._qty = QSpinBox()
        self._qty.setRange(1, 9999)
        self._qty.setValue(item["qty"])
        self._qty.setFixedHeight(32)
        r1.addWidget(self._qty)
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Discount %:"))
        self._disc = QDoubleSpinBox()
        self._disc.setRange(0, 100)
        self._disc.setSuffix(" %")
        self._disc.setValue(item["disc"])
        self._disc.setFixedHeight(32)
        r2.addWidget(self._disc)
        lay.addLayout(r2)

        btns = QHBoxLayout()
        ok     = QPushButton("Apply");  ok.setObjectName("accent_btn"); ok.clicked.connect(self._ok)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)

    def _ok(self) -> None:
        self.qty  = self._qty.value()
        self.disc = self._disc.value()
        self.accept()


# ═══════════════════════════════════════════════════════════════════
#  RECEIPT DIALOG
# ═══════════════════════════════════════════════════════════════════
class ReceiptDialog(QDialog):
    def __init__(self, order: dict, items: list[dict], parent=None):
        super().__init__(parent)
        self.order = order
        self.items = items
        self.setWindowTitle("Receipt")
        self.setFixedSize(480, 620)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        self._txt = QTextEdit()
        self._txt.setReadOnly(True)
        self._txt.setFont(QFont("Courier New", 11))
        self._txt.setHtml(self._html())
        lay.addWidget(self._txt)

        btns = QHBoxLayout()
        pb = QPushButton("🖨  Print");        pb.setObjectName("accent_btn"); pb.clicked.connect(self._print)
        sb = QPushButton("💾  Save as Text"); sb.clicked.connect(self._save)
        cb = QPushButton("✓  Close");         cb.setObjectName("success_btn"); cb.clicked.connect(self.accept)
        btns.addWidget(pb)
        btns.addWidget(sb)
        btns.addStretch()
        btns.addWidget(cb)
        lay.addLayout(btns)

    def _html(self) -> str:
        o = self.order
        items_html = ""
        for it in self.items:
            disc_str = f" (-{it['discount']:.0f}%)" if it["discount"] else ""
            items_html += (
                f"<tr><td>{it['product_name'][:22]}</td>"
                f"<td align='center'>{it['qty']}</td>"
                f"<td align='right'>${it['price']:.2f}{disc_str}</td>"
                f"<td align='right'>${it['subtotal']:.2f}</td></tr>"
            )
        return f"""<html><body style='font-family:Courier New;font-size:12px;
                background:#1C2130;color:#EAEDF5;padding:16px;'>
        <div style='text-align:center;'>
          <span style='font-size:20px;font-weight:bold;color:#FF6B35;'>⬡ NEXUS POS</span><br>
          <span style='color:#8892AA;'>Point of Sale System</span><br>
          <span style='color:#505870;'>─────────────────────────────────────</span>
        </div><br>
        <b>Order No:</b> {o['order_no']}<br>
        <b>Date:</b> {o['created_at']}<br>
        <b>Payment:</b> {o['payment_type']}<br>
        <span style='color:#505870;'>─────────────────────────────────────</span><br>
        <table width='100%' cellspacing='4'>
          <tr style='color:#FF8C5A;font-weight:bold;'>
            <td>Item</td><td align='center'>Qty</td>
            <td align='right'>Price</td><td align='right'>Total</td>
          </tr>{items_html}
        </table>
        <span style='color:#505870;'>─────────────────────────────────────</span><br>
        <table width='100%'>
          <tr><td>Subtotal:</td>
              <td align='right'>${o['subtotal']:.2f}</td></tr>
          <tr><td>Discount:</td>
              <td align='right' style='color:#FFAA00;'>-${o['discount']:.2f}</td></tr>
          <tr><td>Tax ({o['tax_rate']:.1f}%):</td>
              <td align='right'>${o['tax_amount']:.2f}</td></tr>
          <tr><td style='font-size:16px;font-weight:bold;color:#FF6B35;'>TOTAL:</td>
              <td align='right' style='font-size:16px;font-weight:bold;color:#FF6B35;'>
                ${o['total']:.2f}</td></tr>
          <tr><td>Paid:</td>
              <td align='right' style='color:#00D68F;'>${o['paid']:.2f}</td></tr>
          <tr><td>Change:</td>
              <td align='right' style='color:#00D68F;'>${o['change']:.2f}</td></tr>
        </table><br>
        <div style='text-align:center;color:#505870;'>
          {o.get('note', '') or ''}<br>
          ─────────────────────────────────────<br>
          Thank you for your purchase!
        </div></body></html>"""

    def _print(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            doc = QTextDocument()
            doc.setHtml(self._html())
            doc.print_(printer)

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt",
            f"receipt_{self.order['order_no']}.txt",
            "Text Files (*.txt)",
        )
        if path:
            with open(path, "w") as f:
                f.write(self._txt.toPlainText())
            QMessageBox.information(self, "Saved", f"Receipt saved:\n{path}")
