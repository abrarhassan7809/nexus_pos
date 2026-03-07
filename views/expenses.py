from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QTextEdit, QMessageBox, QScrollArea,
    QGridLayout, QSizePolicy, QDateEdit, QButtonGroup,
    QRadioButton, QTableWidgetItem, QHeaderView, QColorDialog
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor, QFont
from database import ExpenseQueries
from utils import format_currency, today_str, short_date
from utils.theme import ThemeManager as _TM
from widgets import styled_table, make_table_item, SectionTitle, StatCard, Divider

def _T():
    return _TM().palette


# ─── Category Dialog ───────────────────────────────────────────────────────────
class CategoryDialog(QDialog):
    ICONS = ['💸','🏠','💡','📦','👤','📣','🔧','🍔','🚗','📱',
             '🏥','📚','✈️','🎯','💼','🛒','⚡','🔒','🎨','🖥️']

    def __init__(self, category=None, parent=None):
        super().__init__(parent)
        self._cat  = category
        self._color = category['color'] if category else '#6C63FF'
        self.setWindowTitle("Edit Category" if category else "New Category")
        self.setFixedSize(380, 320)
        self._build()

    def _build(self):
        T = _T()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel(
            f"<b>{'Edit' if self._cat else 'New'} Expense Category</b>"))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit(self._cat['name'] if self._cat else "")
        self.name_input.setPlaceholderText("e.g. Rent, Utilities…")
        form.addRow("Name *:", self.name_input)

        # Icon picker
        self.icon_combo = QComboBox()
        for icon in self.ICONS:
            self.icon_combo.addItem(icon, icon)
        if self._cat:
            idx = self.icon_combo.findData(self._cat['icon'])
            if idx >= 0:
                self.icon_combo.setCurrentIndex(idx)
        form.addRow("Icon:", self.icon_combo)

        # Color picker button
        color_row = QHBoxLayout()
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(80, 28)
        self._color_btn.clicked.connect(self._pick_color)
        self._apply_color_btn()
        self._color_label = QLabel(self._color)
        self._color_label.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px;")
        color_row.addWidget(self._color_btn)
        color_row.addWidget(self._color_label)
        color_row.addStretch()
        form.addRow("Color:", color_row)
        layout.addLayout(form)

        layout.addStretch()
        btns = QHBoxLayout()
        save = QPushButton("Save")
        save.setObjectName("primary")
        save.setFixedHeight(34)
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(34)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, "Pick Category Color")
        if c.isValid():
            self._color = c.name()
            self._apply_color_btn()
            self._color_label.setText(self._color)

    def _apply_color_btn(self):
        self._color_btn.setStyleSheet(
            f"QPushButton {{ background: {self._color}; border-radius: 4px; "
            f"border: 1px solid #ffffff33; }}")

    def _save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Category name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            'name':  self.name_input.text().strip(),
            'icon':  self.icon_combo.currentData(),
            'color': self._color,
        }


# ─── Add Expense / Budget Dialog ───────────────────────────────────────────────
class AddExpenseDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self.setWindowTitle("Add Expense / Budget Entry")
        self.setMinimumWidth(440)
        self._build()

    def _build(self):
        T = _T()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<b>New Entry</b>"))

        # ── Type selector ──────────────────────────────────────────────────────
        type_frame = QFrame()
        type_frame.setStyleSheet(
            f"QFrame {{ background: {T['surface2']}; border-radius: 8px; "
            f"border: 1px solid {T['border']}; padding: 4px; }}")
        type_row = QHBoxLayout(type_frame)
        type_row.setSpacing(4)
        type_row.setContentsMargins(6, 6, 6, 6)

        self._type_group = QButtonGroup(self)
        for label, value, color in [
            ("💸  Expense",      "expense",    T['danger']),
            ("➕  Add Budget",   "budget_add", T['success']),
            ("➖  Sub Budget",   "budget_sub", T['warning']),
        ]:
            rb = QRadioButton(label)
            rb.setProperty("type_value", value)
            rb.setStyleSheet(f"""
                QRadioButton {{ color: {T['text']}; font-size: 12px; padding: 6px 10px; }}
                QRadioButton::indicator {{ width: 0; height: 0; }}
                QRadioButton:checked {{ background: {color}33; border-radius: 6px;
                                        color: {color}; font-weight: 700; }}
            """)
            self._type_group.addButton(rb)
            type_row.addWidget(rb)
            if value == "expense":
                rb.setChecked(True)
        layout.addWidget(type_frame)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Monthly Rent, Electricity Bill…")
        self.title_input.setFixedHeight(34)
        form.addRow("Title *:", self.title_input)

        # Category
        self.cat_combo = QComboBox()
        self.cat_combo.setFixedHeight(34)
        self._load_categories()
        form.addRow("Category *:", self.cat_combo)

        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 9_999_999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(0.00)
        self.amount_spin.setFixedHeight(34)
        self.amount_spin.setPrefix("$ ")
        form.addRow("Amount *:", self.amount_spin)

        # Note
        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Optional note or description…")
        self.note_input.setFixedHeight(64)
        form.addRow("Note:", self.note_input)

        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout()
        save = QPushButton("Add Entry")
        save.setObjectName("primary")
        save.setFixedHeight(36)
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(36)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _load_categories(self):
        self.cat_combo.clear()
        for c in ExpenseQueries.get_categories():
            self.cat_combo.addItem(f"{c['icon']}  {c['name']}", c['id'])

    def _save(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation", "Title is required.")
            return
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Validation", "Amount must be greater than 0.")
            return
        if self.cat_combo.currentData() is None:
            QMessageBox.warning(self, "Validation", "Please select a category.")
            return
        self.accept()

    def get_type(self) -> str:
        for btn in self._type_group.buttons():
            if btn.isChecked():
                return btn.property("type_value")
        return "expense"

    def get_data(self) -> dict:
        return {
            'category_id': self.cat_combo.currentData(),
            'title':       self.title_input.text().strip(),
            'amount':      self.amount_spin.value(),
            'type_':       self.get_type(),
            'note':        self.note_input.toPlainText().strip(),
            'user_id':     self._user['id'],
        }


# ─── Expenses Tab ──────────────────────────────────────────────────────────────
class ExpensesTab(QWidget):
    budget_changed = Signal()   # emitted when budget or expenses change

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        T = _T()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Expense Manager"))
        hdr.addStretch()

        cat_btn = QPushButton("🏷  Manage Categories")
        cat_btn.setObjectName("ghost")
        cat_btn.setFixedHeight(34)
        cat_btn.clicked.connect(self._manage_categories)
        hdr.addWidget(cat_btn)

        add_btn = QPushButton("＋  Add Entry")
        add_btn.setObjectName("primary")
        add_btn.setFixedHeight(34)
        add_btn.clicked.connect(self._add_entry)
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        # ── Stat cards ─────────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self.card_budget  = StatCard("Current Budget",    "—", T['accent'],  "💰")
        self.card_today   = StatCard("Today's Expenses",  "—", T['danger'],  "📉")
        self.card_month   = StatCard("This Month",        "—", T['warning'], "📅")
        self.card_net     = StatCard("Net (Sales − Exp)", "—", T['success'], "📈")
        for c in [self.card_budget, self.card_today, self.card_month, self.card_net]:
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # ── Category breakdown ─────────────────────────────────────────────────
        breakdown_card = QFrame()
        breakdown_card.setObjectName("card")
        bc_layout = QVBoxLayout(breakdown_card)
        bc_layout.setContentsMargins(14, 12, 14, 12)
        bc_layout.setSpacing(8)

        bc_hdr = QHBoxLayout()
        bc_hdr.addWidget(QLabel("📊  This Month by Category"))
        bc_hdr.addStretch()
        bc_layout.addLayout(bc_hdr)
        bc_layout.addWidget(Divider())

        self.category_bar_widget = QWidget()
        self.category_bar_layout = QVBoxLayout(self.category_bar_widget)
        self.category_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.category_bar_layout.setSpacing(6)
        bc_layout.addWidget(self.category_bar_widget)
        layout.addWidget(breakdown_card)

        # ── Expense list ───────────────────────────────────────────────────────
        list_card = QFrame()
        list_card.setObjectName("card")
        lc = QVBoxLayout(list_card)
        lc.setContentsMargins(14, 12, 14, 12)
        lc.setSpacing(8)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        filter_row.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setFixedHeight(32)
        filter_row.addWidget(self.date_from)

        filter_row.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedHeight(32)
        filter_row.addWidget(self.date_to)

        filter_row.addWidget(QLabel("Category:"))
        self.cat_filter = QComboBox()
        self.cat_filter.setFixedHeight(32)
        self.cat_filter.addItem("All Categories", None)
        filter_row.addWidget(self.cat_filter)

        filter_row.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.setFixedHeight(32)
        self.type_filter.addItems(["All", "Expense", "Budget Add", "Budget Sub"])
        filter_row.addWidget(self.type_filter)

        go_btn = QPushButton("Filter")
        go_btn.setObjectName("primary")
        go_btn.setFixedHeight(32)
        go_btn.clicked.connect(self._load_table)
        filter_row.addWidget(go_btn)
        filter_row.addStretch()
        lc.addLayout(filter_row)

        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px;")
        lc.addWidget(self.summary_lbl)
        lc.addWidget(Divider())

        # Table: Date | Type | Category | Title | Amount | Note | Actions
        self.exp_table = styled_table(
            ["Date", "Type", "Category", "Title", "Amount", "Note", ""],
            col_widths=[120, 100, 120, None, 100, 140, 60],
            stretch_col=3
        )
        self.exp_table.setMinimumHeight(260)
        lc.addWidget(self.exp_table)
        layout.addWidget(list_card)
        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ── Refresh ────────────────────────────────────────────────────────────────
    def refresh(self):
        T = _T()
        stats = ExpenseQueries.dashboard_stats()

        self.card_budget.set_value(format_currency(stats['budget']))
        # Budget card color: green if positive, red if negative
        budget_color = T['success'] if stats['budget'] >= 0 else T['danger']
        self.card_budget.set_accent(budget_color)

        self.card_today.set_value(format_currency(stats['today_exp']))
        self.card_month.set_value(format_currency(stats['month_exp']))

        # Net = this month's sales - this month's expenses (query separately)
        from database.connection import get_db
        conn = get_db()
        try:
            month_sales = conn.execute(
                """SELECT COALESCE(SUM(total),0) FROM orders
                   WHERE status='completed'
                   AND strftime('%Y-%m',created_at)=strftime('%Y-%m','now')"""
            ).fetchone()[0]
        finally:
            conn.close()
        net = month_sales - stats['month_exp']
        net_color = T['success'] if net >= 0 else T['danger']
        self.card_net.set_value(format_currency(net))
        self.card_net.set_accent(net_color)

        # ── Category breakdown bars ────────────────────────────────────────────
        while self.category_bar_layout.count():
            item = self.category_bar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        by_cat = stats.get('by_cat', [])
        max_amt = max((c['total'] for c in by_cat if c['total'] > 0), default=1)

        for cat in by_cat:
            if cat['total'] <= 0:
                continue
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(8)

            icon_name = QLabel(f"{cat['icon']}  {cat['name']}")
            icon_name.setFixedWidth(130)
            icon_name.setStyleSheet(f"font-size: 12px; color: {T['text']};")
            row_l.addWidget(icon_name)

            # Progress bar
            bar_bg = QFrame()
            bar_bg.setFixedHeight(16)
            bar_bg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            bar_bg.setStyleSheet(
                f"QFrame {{ background: {T['surface2']}; border-radius: 8px; }}")
            bar_bg_layout = QHBoxLayout(bar_bg)
            bar_bg_layout.setContentsMargins(0, 0, 0, 0)
            bar_bg_layout.setSpacing(0)

            pct = cat['total'] / max_amt
            bar_fill = QFrame()
            bar_fill.setFixedHeight(16)
            bar_fill.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            bar_fill.setFixedWidth(max(8, int(pct * 280)))
            bar_fill.setStyleSheet(
                f"QFrame {{ background: {cat['color']}; border-radius: 8px; }}")
            bar_bg_layout.addWidget(bar_fill)
            bar_bg_layout.addStretch()
            row_l.addWidget(bar_bg, 1)

            amt_lbl = QLabel(format_currency(cat['total']))
            amt_lbl.setFixedWidth(90)
            amt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            amt_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {cat['color']};")
            row_l.addWidget(amt_lbl)
            self.category_bar_layout.addWidget(row_w)

        if not any(c['total'] > 0 for c in by_cat):
            no_data = QLabel("No expenses this month.")
            no_data.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px; padding: 8px;")
            self.category_bar_layout.addWidget(no_data)

        # ── Refresh category filter combo ──────────────────────────────────────
        current_cat = self.cat_filter.currentData()
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories", None)
        for c in ExpenseQueries.get_categories():
            self.cat_filter.addItem(f"{c['icon']}  {c['name']}", c['id'])
        if current_cat:
            idx = self.cat_filter.findData(current_cat)
            if idx >= 0:
                self.cat_filter.setCurrentIndex(idx)

        self._load_table()

    def _load_table(self):
        T = _T()
        RIGHT  = Qt.AlignmentFlag.AlignRight  | Qt.AlignmentFlag.AlignVCenter
        CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        date_from   = self.date_from.date().toString("yyyy-MM-dd")
        date_to     = self.date_to.date().toString("yyyy-MM-dd")
        cat_id      = self.cat_filter.currentData()
        type_filter = self.type_filter.currentText()

        type_map = {
            "Expense":    "expense",
            "Budget Add": "budget_add",
            "Budget Sub": "budget_sub",
        }
        filter_type = type_map.get(type_filter)

        rows = ExpenseQueries.get_all(date_from, date_to, cat_id)
        if filter_type:
            rows = [r for r in rows if r['type'] == filter_type]

        self._table_rows = list(rows)
        self.exp_table.setRowCount(0)
        self.exp_table.setRowCount(len(rows))

        type_labels = {
            'expense':    ('💸 Expense',    T['danger']),
            'budget_add': ('➕ Add Budget', T['success']),
            'budget_sub': ('➖ Sub Budget', T['warning']),
        }
        total_expense = sum(r['amount'] for r in rows if r['type'] == 'expense')
        total_added   = sum(r['amount'] for r in rows if r['type'] == 'budget_add')

        for i, r in enumerate(rows):
            date_item = QTableWidgetItem(short_date(r['created_at']))
            self.exp_table.setItem(i, 0, date_item)

            type_lbl, type_color = type_labels.get(r['type'], (r['type'], T['text']))
            self.exp_table.setItem(i, 1, make_table_item(type_lbl, CENTER, type_color))

            cat_text = f"{r['cat_icon']}  {r['cat_name']}" if r['cat_name'] else '—'
            self.exp_table.setItem(i, 2, QTableWidgetItem(cat_text))

            self.exp_table.setItem(i, 3, QTableWidgetItem(r['title']))

            amt_color = T['danger'] if r['type'] == 'expense' else T['success']
            prefix = '-' if r['type'] in ('expense', 'budget_sub') else '+'
            self.exp_table.setItem(i, 4, make_table_item(
                f"{prefix}{format_currency(r['amount'])}", RIGHT, amt_color))

            self.exp_table.setItem(i, 5, QTableWidgetItem(r['note'] or '—'))

            # Delete button
            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(32, 26)
            del_btn.setObjectName("danger")
            del_btn.setToolTip("Delete entry (reverses budget effect)")
            del_btn.clicked.connect(lambda _, rid=r['id']: self._delete_entry(rid))
            self.exp_table.setCellWidget(i, 6, del_btn)

        self.summary_lbl.setText(
            f"Showing {len(rows)} records  ·  "
            f"Total expenses: {format_currency(total_expense)}  ·  "
            f"Budget added: {format_currency(total_added)}"
        )

    # ── Actions ────────────────────────────────────────────────────────────────
    def _add_entry(self):
        dlg = AddExpenseDialog(self._user, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                ExpenseQueries.create(**dlg.get_data())
                self.refresh()
                self.budget_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_entry(self, expense_id: int):
        if QMessageBox.question(
            self, "Delete Entry",
            "Delete this entry?\nThe budget balance will be reversed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            ExpenseQueries.delete(expense_id)
            self.refresh()
            self.budget_changed.emit()

    def _manage_categories(self):
        dlg = _CategoryManagerDialog(self)
        dlg.exec()
        self.refresh()  # reload category filter after managing


# ─── Category Manager Dialog ───────────────────────────────────────────────────
class _CategoryManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Expense Categories")
        self.setMinimumSize(500, 420)
        self._build()
        self._load()

    def _build(self):
        T = _T()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("<b>Expense Categories</b>"))
        hdr.addStretch()
        add_btn = QPushButton("＋  New Category")
        add_btn.setObjectName("primary")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._add)
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        self.table = styled_table(
            ["Icon", "Name", "Color", "Actions"],
            col_widths=[50, None, 100, 130],
            stretch_col=1
        )
        layout.addWidget(self.table)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("ghost")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load(self):
        T = _T()
        CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        cats = list(ExpenseQueries.get_categories())
        self.table.setRowCount(0)
        self.table.setRowCount(len(cats))
        for i, c in enumerate(cats):
            self.table.setItem(i, 0, make_table_item(c['icon'], CENTER))
            self.table.setItem(i, 1, QTableWidgetItem(c['name']))
            color_lbl = make_table_item(c['color'], CENTER, c['color'])
            self.table.setItem(i, 2, color_lbl)

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 1, 2, 1)
            btn_l.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("ghost")
            edit_btn.setFixedWidth(50)
            edit_btn.setFixedHeight(30)
            edit_btn.setStyleSheet("""
                QPushButton#ghost {
                    padding: 2px 4px;
                    font-size: 11px;
                }
            """)
            edit_btn.clicked.connect(lambda _, cat=dict(c): self._edit(cat))

            del_btn = QPushButton("Del")
            del_btn.setObjectName("danger")
            del_btn.setFixedWidth(50)
            del_btn.setFixedHeight(30)
            del_btn.setStyleSheet("""
                QPushButton#ghost {
                    padding: 2px 4px;
                    font-size: 11px;
                }
            """)
            del_btn.clicked.connect(lambda _, cid=c['id']: self._delete(cid))

            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            self.table.setCellWidget(i, 3, btn_w)

    def _add(self):
        dlg = CategoryDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                ExpenseQueries.create_category(d['name'], d['color'], d['icon'])
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit(self, cat: dict):
        dlg = CategoryDialog(cat, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                ExpenseQueries.update_category(cat['id'], d['name'], d['color'], d['icon'])
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete(self, cat_id: int):
        if QMessageBox.question(
            self, "Delete Category",
            "Delete this category?\nExpenses in this category will also be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            try:
                ExpenseQueries.delete_category(cat_id)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))