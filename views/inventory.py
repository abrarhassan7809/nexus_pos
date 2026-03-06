from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QDialog, QFormLayout, QComboBox,
    QSpinBox, QDoubleSpinBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from database import ProductQueries
from utils import format_currency, short_date
from utils.theme import ThemeManager as _TM
T = _TM().palette
from widgets import styled_table, make_table_item, SectionTitle


# ─── Product Dialog ────────────────────────────────────────────────────────────
class ProductDialog(QDialog):
    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self._product = product
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumWidth(400)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(QLabel("<b>Edit Product</b>" if self._product else "<b>Add New Product</b>"))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.sku = QLineEdit(self._product['sku'] if self._product else "")
        self.sku.setPlaceholderText("e.g. BEV001")
        form.addRow("SKU *:", self.sku)

        self.name = QLineEdit(self._product['name'] if self._product else "")
        self.name.setPlaceholderText("Product name")
        form.addRow("Name *:", self.name)

        self.category = QComboBox()
        cats = ProductQueries.get_categories()
        for c in cats:
            self.category.addItem(c['name'], c['id'])
        if self._product and self._product['category_id']:
            idx = self.category.findData(self._product['category_id'])
            if idx >= 0:
                self.category.setCurrentIndex(idx)
        form.addRow("Category:", self.category)

        self.price = QDoubleSpinBox()
        self.price.setRange(0, 999999)
        self.price.setDecimals(2)
        self.price.setValue(self._product['price'] if self._product else 0)
        form.addRow("Selling Price *:", self.price)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 999999)
        self.cost.setDecimals(2)
        self.cost.setValue(self._product['cost'] if self._product else 0)
        form.addRow("Cost Price:", self.cost)

        self.stock = QSpinBox()
        self.stock.setRange(0, 999999)
        self.stock.setValue(self._product['stock'] if self._product else 0)
        form.addRow("Stock:", self.stock)

        self.low_stock = QSpinBox()
        self.low_stock.setRange(0, 999999)
        self.low_stock.setValue(self._product['low_stock'] if self._product else 10)
        form.addRow("Low Stock Alert:", self.low_stock)

        self.unit = QLineEdit(self._product['unit'] if self._product else "pcs")
        form.addRow("Unit:", self.unit)
        layout.addLayout(form)

        btns = QHBoxLayout()
        save = QPushButton("Save Product")
        save.setObjectName("primary")
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if not self.sku.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Validation", "SKU and Name are required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            'sku': self.sku.text().strip(),
            'name': self.name.text().strip(),
            'category_id': self.category.currentData(),
            'price': self.price.value(),
            'cost': self.cost.value(),
            'stock': self.stock.value(),
            'low_stock': self.low_stock.value(),
            'unit': self.unit.text().strip() or 'pcs',
        }


# ─── Stock Adjust Dialog ───────────────────────────────────────────────────────
class StockAdjustDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self._product = product
        self.setWindowTitle(f"Adjust Stock — {product['name']}")
        self.setFixedSize(360, 200)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(
            QLabel(f"Current stock: <b>{self._product['stock']} {self._product['unit']}</b>"))

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.change_spin = QSpinBox()
        self.change_spin.setRange(-9999, 9999)
        self.change_spin.setValue(0)
        form.addRow("Change (+ add / − remove):", self.change_spin)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g. New delivery, Damage, Correction")
        form.addRow("Reason:", self.reason_input)
        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Apply")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

    def get_values(self):
        return self.change_spin.value(), self.reason_input.text().strip() or "Manual adjustment"


# ─── Stock Log Dialog ──────────────────────────────────────────────────────────
class StockLogDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Stock History — {product['name']}")
        self.setMinimumSize(560, 420)
        self._product = product
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Change=70 fixed, Reason=stretch, User=100 fixed, Date=160 fixed
        tbl = styled_table(["Change", "Reason", "User", "Date"],
                           col_widths=[70, None, 100, 160], stretch_col=1)
        rows = ProductQueries.get_stock_log(self._product['id'])
        tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            color = T['success'] if r['change'] > 0 else T['danger']
            ch_text = f"+{r['change']}" if r['change'] > 0 else str(r['change'])
            ch = make_table_item(ch_text,
                                 Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                                 color)
            tbl.setItem(i, 0, ch)
            tbl.setItem(i, 1, QTableWidgetItem(r['reason']))
            tbl.setItem(i, 2, QTableWidgetItem(r['username'] or '—'))
            tbl.setItem(i, 3, QTableWidgetItem(short_date(r['created_at'])))
        layout.addWidget(tbl)

        close = QPushButton("Close")
        close.setObjectName("ghost")
        close.setFixedWidth(80)
        close.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close)
        layout.addLayout(btn_row)


# ─── Inventory Tab ─────────────────────────────────────────────────────────────
class InventoryTab(QWidget):
    products_changed = Signal()   # emitted after any add/edit/delete/stock-adjust

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._all_products = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ── Header row ─────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        hdr.addWidget(SectionTitle("Inventory"))
        hdr.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search name / SKU…")
        self.search.setFixedHeight(34)
        self.search.setMinimumWidth(160)
        self.search.setMaximumWidth(260)
        self.search.textChanged.connect(self._filter)
        hdr.addWidget(self.search)

        self.cat_filter = QComboBox()
        self.cat_filter.setFixedHeight(34)
        self.cat_filter.addItem("All Categories", None)
        cats = ProductQueries.get_categories()
        for c in cats:
            self.cat_filter.addItem(c['name'], c['id'])
        self.cat_filter.currentIndexChanged.connect(self._filter)
        hdr.addWidget(self.cat_filter)

        refresh_btn = QPushButton("⟳")
        refresh_btn.setObjectName("ghost")
        refresh_btn.setFixedSize(50, 34)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(refresh_btn)

        add_btn = QPushButton("＋  Add Product")
        add_btn.setObjectName("primary")
        add_btn.setFixedHeight(34)
        add_btn.clicked.connect(self._add_product)
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        # ── Stats strip ────────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        self.total_lbl = QLabel()
        self.total_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px;")
        self.low_lbl = QLabel()
        self.low_lbl.setStyleSheet(f"color: {T['warning']}; font-size: 12px;")
        stats_row.addWidget(self.total_lbl)
        stats_row.addSpacing(16)
        stats_row.addWidget(self.low_lbl)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # ── Table ──────────────────────────────────────────────────────────────
        # Columns: SKU | Name(stretch) | Category | Price | Cost | Stock | Unit | Alert | Actions
        self.table = styled_table(
            ["SKU", "Name", "Category", "Price", "Cost", "Stock", "Unit", "Min", "Actions"],
            col_widths=[80, None, 110, 100, 100, 100, 80, 80, 250],
            stretch_col=1
        )
        layout.addWidget(self.table)

    def refresh(self):
        self._all_products = list(ProductQueries.get_all())
        self._populate(self._all_products)
        total = len(self._all_products)
        low = sum(1 for p in self._all_products if p['stock'] <= p['low_stock'])
        self.total_lbl.setText(f"Total: {total} products")
        self.low_lbl.setText(f"⚠  Low stock: {low}" if low else "")

    def _filter(self):
        search = self.search.text().lower()
        cat_id = self.cat_filter.currentData()
        filtered = [
            p for p in self._all_products
            if (search in p['name'].lower() or search in p['sku'].lower())
            and (cat_id is None or p['category_id'] == cat_id)
        ]
        self._populate(filtered)

    def _populate(self, products):
        RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        self.table.setRowCount(0)          # clear first to avoid stale cells
        self.table.setRowCount(len(products))

        for i, p in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(p['sku']))
            self.table.setItem(i, 1, QTableWidgetItem(p['name']))
            self.table.setItem(i, 2, QTableWidgetItem(p['category_name'] or '—'))
            self.table.setItem(i, 3, make_table_item(format_currency(p['price']), RIGHT))
            self.table.setItem(i, 4, make_table_item(format_currency(p['cost']),  RIGHT,
                                                     T['text_muted']))
            stock_color = T['danger'] if p['stock'] <= p['low_stock'] else T['success']
            self.table.setItem(i, 5, make_table_item(str(p['stock']), CENTER, stock_color))
            self.table.setItem(i, 6, make_table_item(p['unit'],       CENTER))
            self.table.setItem(i, 7, make_table_item(str(p['low_stock']), CENTER))

            # ── Action buttons cell ────────────────────────────────────────────
            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 1, 2, 1)
            btn_l.setSpacing(2)

            for label, obj_name, slot in [
                ("Edit",  "ghost",   lambda _, pid=p['id']: self._edit_product(pid)),
                ("Stock", "warning", lambda _, pid=p['id']: self._adjust_stock(pid)),
                ("Log",   "ghost",   lambda _, pid=p['id']: self._show_log(pid)),
                ("Del",   "danger",  lambda _, pid=p['id']: self._delete_product(pid)),
            ]:
                btn = QPushButton(label)
                btn.setFixedWidth(50)
                btn.setFixedHeight(30)
                btn.setObjectName(obj_name)

                # Add custom styling to reduce internal padding
                btn.setStyleSheet(f"""
                        QPushButton#{obj_name} {{
                            padding: 2px 6px;
                            font-size: 11px;
                        }}
                    """)

                btn.clicked.connect(slot)
                btn_l.addWidget(btn)

            self.table.setCellWidget(i, 8, btn_w)

    def _add_product(self):
        dlg = ProductDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                ProductQueries.create(**dlg.get_data())
                self.refresh()
                self.products_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_product(self, product_id):
        p = ProductQueries.get_by_id(product_id)
        if not p:
            return
        dlg = ProductDialog(dict(p), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                ProductQueries.update(product_id, **dlg.get_data())
                self.refresh()
                self.products_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _adjust_stock(self, product_id):
        p = ProductQueries.get_by_id(product_id)
        if not p:
            return
        dlg = StockAdjustDialog(dict(p), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            change, reason = dlg.get_values()
            if change == 0:
                return
            ProductQueries.adjust_stock(product_id, change, reason, self._user['id'])
            self.refresh()
            self.products_changed.emit()

    def _show_log(self, product_id):
        p = ProductQueries.get_by_id(product_id)
        if not p:
            return
        StockLogDialog(dict(p), self).exec()

    def _delete_product(self, product_id):
        if QMessageBox.question(
                self, "Confirm Delete", "Deactivate this product?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            ProductQueries.deactivate(product_id)
            self.refresh()
            self.products_changed.emit()
