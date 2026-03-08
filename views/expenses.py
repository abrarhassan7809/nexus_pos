from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QMessageBox, QScrollArea,
    QSizePolicy, QDateEdit, QTableWidgetItem, QHeaderView,
    QColorDialog, QSplitter
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor
from database import ExpenseQueries
from utils import format_currency, today_str, short_date
from utils.theme import ThemeManager as _TM
from widgets import styled_table, make_table_item, SectionTitle, StatCard, Divider

def _T():
    return _TM().palette


# ── Category Add/Edit Dialog ───────────────────────────────────────────────────
class _CategoryDialog(QDialog):
    ICONS = ['💸','🏠','💡','📦','👤','📣','🔧','🍔','🚗','📱',
             '🏥','📚','✈️','🎯','💼','🛒','⚡','🔒','🎨','🖥️']
    COLORS = ['#EF4444','#F59E0B','#6C63FF','#3B82F6','#22C55E',
              '#F97316','#8B5CF6','#EC4899','#14B8A6','#64748B']

    def __init__(self, category=None, parent=None):
        super().__init__(parent)
        self._cat   = category
        self._color = category['color'] if category else self.COLORS[0]
        self.setWindowTitle("Edit Category" if category else "Add Category")
        self.setFixedSize(400, 290)
        self._build()

    def _build(self):
        T = _T()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        title = QLabel("Edit Category" if self._cat else "New Expense Category")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.name_input = QLineEdit(self._cat['name'] if self._cat else "")
        self.name_input.setPlaceholderText("e.g. Rent, Electricity, Salaries…")
        self.name_input.setFixedHeight(36)
        form.addRow("Name:", self.name_input)

        self.icon_combo = QComboBox()
        self.icon_combo.setFixedHeight(36)
        for icon in self.ICONS:
            self.icon_combo.addItem(icon, icon)
        if self._cat:
            idx = self.icon_combo.findData(self._cat['icon'])
            if idx >= 0:
                self.icon_combo.setCurrentIndex(idx)
        form.addRow("Icon:", self.icon_combo)

        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        self._color_btns = []
        for hex_color in self.COLORS:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setProperty("hex", hex_color)
            btn.clicked.connect(lambda _, c=hex_color: self._select_color(c))
            self._color_btns.append(btn)
            color_row.addWidget(btn)
        color_row.addStretch()
        custom_btn = QPushButton("…")
        custom_btn.setFixedSize(26, 26)
        custom_btn.setToolTip("Pick custom color")
        custom_btn.clicked.connect(self._pick_custom)
        color_row.addWidget(custom_btn)
        form.addRow("Color:", color_row)
        layout.addLayout(form)
        self._refresh_swatches()

        layout.addStretch()
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(36)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save Category")
        save.setObjectName("primary")
        save.setFixedHeight(36)
        save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _select_color(self, color):
        self._color = color
        self._refresh_swatches()

    def _pick_custom(self):
        c = QColorDialog.getColor(QColor(self._color), self, "Pick Color")
        if c.isValid():
            self._color = c.name()
            self._refresh_swatches()

    def _refresh_swatches(self):
        for btn in self._color_btns:
            hc = btn.property("hex")
            selected = (hc == self._color)
            border = "3px solid white" if selected else "2px solid transparent"
            btn.setStyleSheet(
                f"QPushButton {{ background: {hc}; border-radius: 13px; border: {border}; }}")

    def _save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Required", "Please enter a category name.")
            return
        self.accept()

    def get_data(self):
        return {'name': self.name_input.text().strip(),
                'icon': self.icon_combo.currentData(),
                'color': self._color}


# ── Add Expense Dialog ─────────────────────────────────────────────────────────
class _AddExpenseDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self.setWindowTitle("Record Expense")
        self.setFixedSize(460, 320)
        self._build()

    def _build(self):
        T = _T()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        title = QLabel("Record New Expense")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        sub = QLabel("This will be deducted from your available budget.")
        sub.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px;")
        layout.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Monthly Rent, Electricity Bill…")
        self.title_input.setFixedHeight(36)
        form.addRow("Description:", self.title_input)

        self.cat_combo = QComboBox()
        self.cat_combo.setFixedHeight(36)
        for c in ExpenseQueries.get_categories():
            self.cat_combo.addItem(f"{c['icon']}  {c['name']}", c['id'])
        form.addRow("Category:", self.cat_combo)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 9_999_999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(0.00)
        self.amount_spin.setFixedHeight(36)
        self.amount_spin.setPrefix("$ ")
        form.addRow("Amount:", self.amount_spin)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note…")
        self.note_input.setFixedHeight(36)
        form.addRow("Note:", self.note_input)
        layout.addLayout(form)

        layout.addStretch()
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(38)
        cancel.clicked.connect(self.reject)
        save = QPushButton("💸  Record Expense")
        save.setObjectName("danger")
        save.setFixedHeight(38)
        save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Required", "Please enter a description.")
            return
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Required", "Amount must be greater than zero.")
            return
        if self.cat_combo.currentData() is None:
            QMessageBox.warning(self, "Required", "Please select a category.")
            return
        self.accept()

    def get_data(self):
        return {'category_id': self.cat_combo.currentData(),
                'title':       self.title_input.text().strip(),
                'amount':      self.amount_spin.value(),
                'type_':       'expense',
                'note':        self.note_input.text().strip(),
                'user_id':     self._user['id']}


# ── Add Budget Dialog ──────────────────────────────────────────────────────────
class _BudgetDialog(QDialog):
    def __init__(self, user, current_balance, parent=None):
        super().__init__(parent)
        self._user    = user
        self._balance = current_balance
        self.setWindowTitle("Add Money to Budget")
        self.setFixedSize(420, 260)
        self._build()

    def _build(self):
        T = _T()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        title = QLabel("Add Money to Budget")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        color = T['success'] if self._balance >= 0 else T['danger']
        current = QLabel(f"Current balance:  {format_currency(self._balance)}")
        current.setStyleSheet(f"font-size: 13px; color: {color}; font-weight: 600;")
        layout.addWidget(current)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 9_999_999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setFixedHeight(36)
        self.amount_spin.setPrefix("$ ")
        form.addRow("Amount:", self.amount_spin)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("e.g. Monthly budget, Initial capital…")
        self.note_input.setFixedHeight(36)
        form.addRow("Note:", self.note_input)
        layout.addLayout(form)

        layout.addStretch()
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(38)
        cancel.clicked.connect(self.reject)
        save = QPushButton("➕  Add to Budget")
        save.setObjectName("primary")
        save.setFixedHeight(38)
        save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Required", "Amount must be greater than zero.")
            return
        self.accept()

    def get_data(self):
        cats = ExpenseQueries.get_categories()
        cat_id = cats[-1]['id'] if cats else 1   # use last category (usually "Other")
        return {'category_id': cat_id,
                'title':       self.note_input.text().strip() or "Budget top-up",
                'amount':      self.amount_spin.value(),
                'type_':       'budget_add',
                'note':        '',
                'user_id':     self._user['id']}


# ── Expenses Tab — main view ───────────────────────────────────────────────────
class ExpensesTab(QWidget):
    budget_changed = Signal()

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        T = _T()
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Expense Manager"))
        hdr.addStretch()
        budget_btn = QPushButton("➕  Add Budget")
        budget_btn.setObjectName("primary")
        budget_btn.setFixedHeight(36)
        budget_btn.setToolTip("Top up your available business budget")
        budget_btn.clicked.connect(self._add_budget)
        hdr.addWidget(budget_btn)
        add_btn = QPushButton("💸  Record Expense")
        add_btn.setObjectName("danger")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_expense)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)

        # Stat cards
        cards = QHBoxLayout()
        cards.setSpacing(10)
        self.card_budget = StatCard("Available Budget", "—", T['accent'],  "💰")
        self.card_today  = StatCard("Today's Spending", "—", T['danger'],  "📉")
        self.card_month  = StatCard("This Month",       "—", T['warning'], "📅")
        self.card_net    = StatCard("Net Profit",        "—", T['success'], "📈")
        for c in [self.card_budget, self.card_today, self.card_month, self.card_net]:
            cards.addWidget(c)
        root.addLayout(cards)

        # Splitter: categories on left, expenses on right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # ── Left: Category panel ───────────────────────────────────────────────
        left = QFrame()
        left.setObjectName("card")
        left.setMinimumWidth(210)
        left.setMaximumWidth(270)
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(12, 12, 12, 12)
        left_l.setSpacing(6)

        cat_hdr = QHBoxLayout()
        cat_title = QLabel("Categories")
        cat_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        cat_hdr.addWidget(cat_title)
        cat_hdr.addStretch()
        new_cat_btn = QPushButton("＋")
        new_cat_btn.setObjectName("ghost")
        new_cat_btn.setFixedSize(50, 35)
        new_cat_btn.setToolTip("Add new category")
        new_cat_btn.clicked.connect(self._add_category)
        cat_hdr.addWidget(new_cat_btn)
        left_l.addLayout(cat_hdr)
        left_l.addWidget(Divider())

        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._cat_container = QWidget()
        self._cat_layout = QVBoxLayout(self._cat_container)
        self._cat_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_layout.setSpacing(4)
        self._cat_layout.addStretch()
        cat_scroll.setWidget(self._cat_container)
        left_l.addWidget(cat_scroll)
        splitter.addWidget(left)

        # ── Right: Expenses list ───────────────────────────────────────────────
        right = QFrame()
        right.setObjectName("card")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(14, 14, 14, 14)
        right_l.setSpacing(8)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)
        filter_bar.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setFixedHeight(32)
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedHeight(32)
        filter_bar.addWidget(self.date_to)
        filter_bar.addWidget(QLabel("Category:"))
        self.cat_filter = QComboBox()
        self.cat_filter.setFixedHeight(32)
        self.cat_filter.setMinimumWidth(130)
        self.cat_filter.addItem("All Categories", None)
        filter_bar.addWidget(self.cat_filter)
        go_btn = QPushButton("Apply")
        go_btn.setObjectName("ghost")
        go_btn.setFixedHeight(32)
        go_btn.clicked.connect(self._load_table)
        filter_bar.addWidget(go_btn)
        filter_bar.addStretch()
        right_l.addLayout(filter_bar)

        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px;")
        right_l.addWidget(self.summary_lbl)
        right_l.addWidget(Divider())

        # Table: Date | Category | Description | Amount | Note | Delete
        self.exp_table = styled_table(
            ["Date", "Category", "Description", "Amount", "Note", ""],
            col_widths=[150, 150, None, 100, 150, 60],
            stretch_col=2
        )
        self.exp_table.setMinimumHeight(260)
        right_l.addWidget(self.exp_table)
        splitter.addWidget(right)

        splitter.setSizes([240, 700])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)

    # ── Refresh ────────────────────────────────────────────────────────────────
    def refresh(self):
        T = _T()
        stats = ExpenseQueries.dashboard_stats()

        budget = stats['budget']
        self.card_budget.set_value(format_currency(budget))
        self.card_budget.set_accent(T['success'] if budget >= 0 else T['danger'])
        self.card_today.set_value(format_currency(stats['today_exp']))
        self.card_month.set_value(format_currency(stats['month_exp']))

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
        self.card_net.set_value(format_currency(net))
        self.card_net.set_accent(T['success'] if net >= 0 else T['danger'])

        self._rebuild_cat_panel(stats)

        current = self.cat_filter.currentData()
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories", None)
        for c in ExpenseQueries.get_categories():
            self.cat_filter.addItem(f"{c['icon']}  {c['name']}", c['id'])
        if current:
            idx = self.cat_filter.findData(current)
            if idx >= 0:
                self.cat_filter.setCurrentIndex(idx)

        self._load_table()

    def _rebuild_cat_panel(self, stats):
        T = _T()
        by_cat  = {c['name']: c for c in stats.get('by_cat', [])}
        cats    = list(ExpenseQueries.get_categories())
        max_amt = max((c['total'] for c in stats.get('by_cat', []) if c['total'] > 0), default=1)

        # Remove all but the trailing stretch
        while self._cat_layout.count() > 1:
            item = self._cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not cats:
            empty = QLabel("No categories.\nClick ＋ to add one.")
            empty.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px; padding: 8px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cat_layout.insertWidget(0, empty)
            return

        for cat in cats:
            spent = by_cat.get(cat['name'], {}).get('total', 0.0)
            color = cat['color']

            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ border-radius: 8px; background: {T['surface2']}; border: none; }}"
                f"QFrame:hover {{ background: {T['surface3']}; }}")
            card_l = QVBoxLayout(card)
            card_l.setContentsMargins(10, 8, 10, 6)
            card_l.setSpacing(4)

            # Icon + name + amount
            top = QHBoxLayout()
            icon_name = QLabel(f"{cat['icon']}  {cat['name']}")
            icon_name.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: {T['text']};"
                f" background: transparent; border: none;")
            top.addWidget(icon_name)
            top.addStretch()
            amt = QLabel(format_currency(spent))
            amt.setStyleSheet(
                f"font-size: 11px; font-weight: 700; color: {color};"
                f" background: transparent; border: none;")
            top.addWidget(amt)
            card_l.addLayout(top)

            # Progress bar (this month's spending)
            pct = min(1.0, spent / max_amt) if spent > 0 else 0
            bar_bg = QFrame()
            bar_bg.setFixedHeight(4)
            bar_bg.setStyleSheet(
                f"QFrame {{ background: {T['surface']}; border-radius: 2px; border: none; }}")
            bar_bg_l = QHBoxLayout(bar_bg)
            bar_bg_l.setContentsMargins(0, 0, 0, 0)
            bar_bg_l.setSpacing(0)
            if pct > 0:
                fill = QFrame()
                fill.setFixedHeight(4)
                fill.setFixedWidth(max(4, int(pct * 170)))
                fill.setStyleSheet(
                    f"QFrame {{ background: {color}; border-radius: 2px; border: none; }}")
                bar_bg_l.addWidget(fill)
            bar_bg_l.addStretch()
            card_l.addWidget(bar_bg)

            # Edit / Delete buttons
            btn_row = QHBoxLayout()
            btn_row.setSpacing(4)
            btn_row.addStretch()
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("ghost")
            edit_btn.setFixedHeight(22)
            edit_btn.setFixedWidth(44)
            edit_btn.setStyleSheet("font-size: 10px; padding: 0 4px;")
            edit_btn.clicked.connect(lambda _, c=dict(cat): self._edit_category(c))
            del_btn = QPushButton("Del")
            del_btn.setObjectName("danger")
            del_btn.setFixedHeight(22)
            del_btn.setFixedWidth(36)
            del_btn.setStyleSheet("font-size: 10px; padding: 0 4px;")
            del_btn.clicked.connect(lambda _, cid=cat['id']: self._delete_category(cid))
            btn_row.addWidget(edit_btn)
            btn_row.addWidget(del_btn)
            card_l.addLayout(btn_row)

            self._cat_layout.insertWidget(self._cat_layout.count() - 1, card)

    def _load_table(self):
        T = _T()
        RIGHT  = Qt.AlignmentFlag.AlignRight  | Qt.AlignmentFlag.AlignVCenter

        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to   = self.date_to.date().toString("yyyy-MM-dd")
        cat_id    = self.cat_filter.currentData()

        rows = [r for r in ExpenseQueries.get_all(date_from, date_to, cat_id)
                if r['type'] == 'expense']

        self.exp_table.setRowCount(0)
        self.exp_table.setRowCount(len(rows))
        total = sum(r['amount'] for r in rows)

        for i, r in enumerate(rows):
            self.exp_table.setItem(i, 0, QTableWidgetItem(short_date(r['created_at'])))
            cat_txt = f"{r['cat_icon']}  {r['cat_name']}" if r['cat_name'] else '—'
            self.exp_table.setItem(i, 1, QTableWidgetItem(cat_txt))
            self.exp_table.setItem(i, 2, QTableWidgetItem(r['title']))
            self.exp_table.setItem(i, 3, make_table_item(
                format_currency(r['amount']), RIGHT, T['danger']))
            self.exp_table.setItem(i, 4, QTableWidgetItem(r['note'] or '—'))

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(40, 40)
            del_btn.setObjectName("danger")
            del_btn.setToolTip("Delete this expense")
            del_btn.clicked.connect(lambda _, rid=r['id']: self._delete_expense(rid))
            self.exp_table.setCellWidget(i, 5, del_btn)

        n = len(rows)
        self.summary_lbl.setText(
            f"{n} expense{'s' if n != 1 else ''}  ·  Total spent: {format_currency(total)}")

    # ── Actions ────────────────────────────────────────────────────────────────
    def _add_expense(self):
        dlg = _AddExpenseDialog(self._user, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                ExpenseQueries.create(**dlg.get_data())
                self.refresh()
                self.budget_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _add_budget(self):
        balance = ExpenseQueries.get_budget()
        dlg = _BudgetDialog(self._user, balance, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                ExpenseQueries.create(**dlg.get_data())
                self.refresh()
                self.budget_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_expense(self, expense_id):
        if QMessageBox.question(
            self, "Delete Expense",
            "Delete this expense?\nThe amount will be refunded to your budget.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            ExpenseQueries.delete(expense_id)
            self.refresh()
            self.budget_changed.emit()

    def _add_category(self):
        dlg = _CategoryDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                ExpenseQueries.create_category(d['name'], d['color'], d['icon'])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_category(self, cat):
        dlg = _CategoryDialog(cat, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                ExpenseQueries.update_category(cat['id'], d['name'], d['color'], d['icon'])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_category(self, cat_id):
        if QMessageBox.question(
            self, "Delete Category",
            "Delete this category?\nAll expenses in it will also be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            try:
                ExpenseQueries.delete_category(cat_id)
                self.refresh()
                self.budget_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))