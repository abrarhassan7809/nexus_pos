from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidgetItem,
                               QMessageBox, QDialog, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QHeaderView,
                               QInputDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from database.queries import ProductQueries
from utils.theme import THEME
from widgets.base import SectionTitle, StatCard, styled_table


# ═══════════════════════════════════════════════════════════════════
#  INVENTORY TAB
# ═══════════════════════════════════════════════════════════════════
class InventoryTab(QWidget):
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        lay.setContentsMargins(12, 12, 12, 12)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Inventory Management"))
        hdr.addStretch()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search…")
        self._search.setFixedWidth(220); self._search.setFixedHeight(34)
        self._search.textChanged.connect(self.refresh)
        hdr.addWidget(self._search)
        lay.addLayout(hdr)

        # Stat cards
        sr = QHBoxLayout()
        self._c_total = StatCard("Total Products", "—", "📦", THEME["accent"])
        self._c_low   = StatCard("Low Stock",      "—", "⚠",  THEME["warning"])
        self._c_out   = StatCard("Out of Stock",   "—", "✖",  THEME["danger"])
        self._c_val   = StatCard("Inventory Value","—", "$",  THEME["success"])
        for c in [self._c_total, self._c_low, self._c_out, self._c_val]:
            sr.addWidget(c)
        lay.addLayout(sr)

        # Action buttons
        br = QHBoxLayout()
        add_btn  = QPushButton("➕  Add Product");   add_btn.setObjectName("accent_btn"); add_btn.clicked.connect(self._add)
        edit_btn = QPushButton("✏  Edit");            edit_btn.clicked.connect(self._edit)
        del_btn  = QPushButton("🗑  Delete");          del_btn.setObjectName("danger_btn"); del_btn.clicked.connect(self._delete)
        adj_btn  = QPushButton("📥  Adjust Stock");   adj_btn.clicked.connect(self._adjust)
        log_btn  = QPushButton("📋  Stock Log");       log_btn.clicked.connect(self._show_log)
        for b in [add_btn, edit_btn, del_btn, adj_btn, log_btn]:
            br.addWidget(b)
        br.addStretch()
        lay.addLayout(br)

        # Product table
        self._tbl = styled_table(
            ["ID", "Product", "Category", "Price", "Cost",
             "Stock", "Low Stk", "Unit", "Barcode", "Status"]
        )
        self._tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._tbl.setColumnWidth(0, 40)
        lay.addWidget(self._tbl)

    # ── Data ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        q    = self._search.text().strip()
        rows = ProductQueries.get_all(search=q)
        s    = ProductQueries.get_inventory_stats()

        self._c_total.set_value(s["total"])
        self._c_low.set_value(s["low"])
        self._c_out.set_value(s["out"])
        self._c_val.set_value(f"${s['value']:,.2f}")

        self._tbl.setRowCount(0)
        for r in rows:
            ri = self._tbl.rowCount()
            self._tbl.insertRow(ri)
            status, color = "OK", None
            if r["stock"] == 0:
                status, color = "OUT", QColor(THEME["danger"])
            elif r["stock"] <= r["low_stock"]:
                status, color = "LOW", QColor(THEME["warning"])
            cells = [
                str(r["id"]), r["name"], r["cat_name"] or "",
                f"${r['price']:.2f}", f"${r['cost']:.2f}",
                str(r["stock"]), str(r["low_stock"]),
                r["unit"], r["barcode"] or "", status,
            ]
            for ci, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                item.setData(Qt.ItemDataRole.UserRole, r)
                if color and ci in (5, 9):
                    item.setForeground(color)
                self._tbl.setItem(ri, ci, item)

    def _selected(self) -> dict | None:
        row = self._tbl.currentRow()
        if row < 0:
            return None
        return self._tbl.item(row, 0).data(Qt.ItemDataRole.UserRole)

    # ── Slots ─────────────────────────────────────────────────────
    def _add(self) -> None:
        if ProductDialog(parent=self).exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit(self) -> None:
        p = self._selected()
        if not p:
            QMessageBox.information(self, "Select", "Please select a product.")
            return
        if ProductDialog(product=p, parent=self).exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete(self) -> None:
        p = self._selected()
        if not p:
            return
        if (QMessageBox.question(self, "Delete", f"Deactivate '{p['name']}'?",
                                 QMessageBox.StandardButton.Yes |
                                 QMessageBox.StandardButton.No)
                == QMessageBox.StandardButton.Yes):
            ProductQueries.deactivate(p["id"])
            self.refresh()

    def _adjust(self) -> None:
        p = self._selected()
        if not p:
            QMessageBox.information(self, "Select", "Please select a product.")
            return
        if StockAdjustDialog(p, self.current_user, self).exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _show_log(self) -> None:
        p = self._selected()
        StockLogDialog(p, self).exec()


# ═══════════════════════════════════════════════════════════════════
#  PRODUCT DIALOG
# ═══════════════════════════════════════════════════════════════════
class ProductDialog(QDialog):
    def __init__(self, product: dict | None = None, parent=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Add Product" if not product else "Edit Product")
        self.setFixedSize(480, 500)
        self._build()
        if product:
            self._fill(product)

    def _build(self) -> None:
        lay = QFormLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(24, 24, 24, 24)

        self._name    = QLineEdit();      self._name.setFixedHeight(34)
        self._price   = QDoubleSpinBox(); self._price.setRange(0,99999); self._price.setPrefix("$"); self._price.setFixedHeight(34)
        self._cost    = QDoubleSpinBox(); self._cost.setRange(0,99999);  self._cost.setPrefix("$"); self._cost.setFixedHeight(34)
        self._stock   = QSpinBox();       self._stock.setRange(0,999999); self._stock.setFixedHeight(34)
        self._low     = QSpinBox();       self._low.setRange(0,9999); self._low.setValue(5); self._low.setFixedHeight(34)
        self._unit    = QLineEdit("pcs"); self._unit.setFixedHeight(34)
        self._barcode = QLineEdit();      self._barcode.setFixedHeight(34)

        self._cat = QComboBox(); self._cat.setFixedHeight(34)
        for c in ProductQueries.get_categories():
            self._cat.addItem(c["name"], c["id"])

        lay.addRow("Product Name *", self._name)
        lay.addRow("Category",        self._cat)
        lay.addRow("Sale Price *",    self._price)
        lay.addRow("Cost Price",      self._cost)
        lay.addRow("Stock Qty",       self._stock)
        lay.addRow("Low Stock Alert", self._low)
        lay.addRow("Unit",            self._unit)
        lay.addRow("Barcode",         self._barcode)

        btns = QHBoxLayout()
        ok = QPushButton("Save"); ok.setObjectName("accent_btn"); ok.clicked.connect(self._save)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        lay.addRow(btns)

    def _fill(self, p: dict) -> None:
        self._name.setText(p["name"])
        self._price.setValue(p["price"])
        self._cost.setValue(p["cost"])
        self._stock.setValue(p["stock"])
        self._low.setValue(p["low_stock"])
        self._unit.setText(p["unit"])
        self._barcode.setText(p["barcode"] or "")
        for i in range(self._cat.count()):
            if self._cat.itemData(i) == p["category_id"]:
                self._cat.setCurrentIndex(i)
                break

    def _save(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return
        try:
            if self.product:
                ProductQueries.update(
                    self.product["id"], name, self._cat.currentData(),
                    self._price.value(), self._cost.value(),
                    self._stock.value(), self._low.value(),
                    self._unit.text(), self._barcode.text() or None,
                )
            else:
                ProductQueries.create(
                    name, self._cat.currentData(),
                    self._price.value(), self._cost.value(),
                    self._stock.value(), self._low.value(),
                    self._unit.text(), self._barcode.text() or None,
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ═══════════════════════════════════════════════════════════════════
#  STOCK ADJUST DIALOG
# ═══════════════════════════════════════════════════════════════════
class StockAdjustDialog(QDialog):
    def __init__(self, product: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.product = product
        self.current_user = current_user
        self.setWindowTitle("Adjust Stock")
        self.setFixedSize(360, 250)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.addWidget(QLabel(f"<b>{self.product['name']}</b>"))
        lay.addWidget(QLabel(
            f"Current Stock: <b>{self.product['stock']} {self.product['unit']}</b>"
        ))

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Adjustment:"))
        self._adj = QSpinBox(); self._adj.setRange(-99999, 99999); self._adj.setValue(0); self._adj.setFixedHeight(34)
        r1.addWidget(self._adj)
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Reason:"))
        self._reason = QLineEdit(); self._reason.setPlaceholderText("e.g. Restock, Damage…")
        r2.addWidget(self._reason)
        lay.addLayout(r2)

        btns = QHBoxLayout()
        ok = QPushButton("Apply"); ok.setObjectName("accent_btn"); ok.clicked.connect(self._apply)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        lay.addLayout(btns)

    def _apply(self) -> None:
        adj = self._adj.value()
        if adj == 0:
            return
        if self.product["stock"] + adj < 0:
            QMessageBox.warning(self, "Invalid", "Stock cannot go negative.")
            return
        ProductQueries.adjust_stock(
            self.product["id"], adj,
            self._reason.text() or "Manual Adjustment",
            self.current_user["id"],
        )
        self.accept()


# ═══════════════════════════════════════════════════════════════════
#  STOCK LOG DIALOG
# ═══════════════════════════════════════════════════════════════════
class StockLogDialog(QDialog):
    def __init__(self, product: dict | None = None, parent=None):
        super().__init__(parent)
        self.product = product
        title = f"Stock Log — {product['name']}" if product else "Stock Log — All Products"
        self.setWindowTitle(title)
        self.resize(700, 480)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        self._tbl = styled_table(["Date", "Product", "Change", "Reason", "User"])
        self._tbl.setColumnWidth(0, 150); self._tbl.setColumnWidth(1, 160)
        self._tbl.setColumnWidth(2, 70);  self._tbl.setColumnWidth(3, 180)
        lay.addWidget(self._tbl)
        close_btn = QPushButton("Close"); close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)
        self._load()

    def _load(self) -> None:
        pid = self.product["id"] if self.product else None
        rows = ProductQueries.get_stock_log(product_id=pid)
        self._tbl.setRowCount(0)
        for r in rows:
            ri = self._tbl.rowCount()
            self._tbl.insertRow(ri)
            chg = r["change"]
            cells = [r["created_at"], r["pname"],
                     f"{'+' if chg > 0 else ''}{chg}",
                     r["reason"], r["username"] or ""]
            for ci, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                if ci == 2:
                    item.setForeground(
                        QColor(THEME["success"] if chg > 0 else THEME["danger"])
                    )
                self._tbl.setItem(ri, ci, item)
