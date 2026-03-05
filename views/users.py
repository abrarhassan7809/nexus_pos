from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from database import UserQueries
from utils import hash_pw, short_date
from utils.theme import THEME as T
from widgets import styled_table, make_table_item, SectionTitle


class UserDialog(QDialog):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self._user = user
        self.setWindowTitle("Edit User" if user else "Add User")
        self.setFixedSize(380, 300)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(QLabel("<b>Edit User</b>" if self._user else "<b>Add New User</b>"))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.username = QLineEdit(self._user['username'] if self._user else "")
        form.addRow("Username *:", self.username)

        self.full_name = QLineEdit(self._user['full_name'] if self._user else "")
        form.addRow("Full Name:", self.full_name)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Leave blank to keep current" if self._user else "Enter password")
        form.addRow("Password:", self.password)

        self.role = QComboBox()
        self.role.addItems(["cashier", "admin"])
        if self._user:
            self.role.setCurrentText(self._user['role'])
        form.addRow("Role:", self.role)

        self.active = QCheckBox("Active")
        self.active.setChecked(bool(self._user['active']) if self._user else True)
        form.addRow("Status:", self.active)
        layout.addLayout(form)

        btns = QHBoxLayout()
        save = QPushButton("Save")
        save.setObjectName("primary")
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if not self.username.text().strip():
            QMessageBox.warning(self, "Validation", "Username is required.")
            return
        if not self._user and not self.password.text():
            QMessageBox.warning(self, "Validation", "Password is required for new users.")
            return
        self.accept()

    def get_data(self) -> dict:
        pw = self.password.text()
        return {
            'username': self.username.text().strip(),
            'full_name': self.full_name.text().strip(),
            'password_hash': hash_pw(pw) if pw else None,
            'role': self.role.currentText(),
            'active': 1 if self.active.isChecked() else 0,
        }


class UsersTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("User Management"))
        hdr.addStretch()
        add_btn = QPushButton("＋  Add User")
        add_btn.setObjectName("primary")
        add_btn.setFixedHeight(34)
        add_btn.clicked.connect(self._add_user)
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        notice = QLabel("⚠  Admin-only section. Changes take effect immediately.")
        notice.setStyleSheet(
            f"color: {T['warning']}; font-size: 12px; "
            f"background: {T['surface2']}; padding: 8px 12px; "
            f"border-radius: 6px; border-left: 3px solid {T['warning']};"
        )
        layout.addWidget(notice)

        # ID=40, Username=120, FullName=stretch, Role=80, Status=75, Created=160, Actions=120
        self.table = styled_table(
            ["ID", "Username", "Full Name", "Role", "Status", "Created", "Actions"],
            col_widths=[40, 120, None, 100, 100, 160, 140],
            stretch_col=2
        )
        layout.addWidget(self.table)

    def refresh(self):
        CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        users = UserQueries.get_all()
        self.table.setRowCount(0)
        self.table.setRowCount(len(users))

        for i, u in enumerate(users):
            self.table.setItem(i, 0, make_table_item(str(u['id']), CENTER))
            self.table.setItem(i, 1, QTableWidgetItem(u['username']))
            self.table.setItem(i, 2, QTableWidgetItem(u['full_name'] or '—'))
            role_color = T['accent'] if u['role'] == 'admin' else T['text_muted']
            self.table.setItem(i, 3, make_table_item(u['role'].upper(), CENTER, role_color))
            status_color = T['success'] if u['active'] else T['danger']
            self.table.setItem(i, 4, make_table_item(
                "Active" if u['active'] else "Inactive", CENTER, status_color))
            self.table.setItem(i, 5, QTableWidgetItem(short_date(u['created_at'])))

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 1, 2, 1)
            btn_l.setSpacing(2)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(50)
            edit_btn.setFixedHeight(30)
            edit_btn.setObjectName("ghost")
            edit_btn.setStyleSheet("""
                QPushButton#ghost {
                    padding: 2px 4px;
                    font-size: 11px;
                }
            """)
            edit_btn.clicked.connect(lambda _, uid=u['id']: self._edit_user(uid))

            del_btn = QPushButton("Delete")
            del_btn.setFixedWidth(50)
            del_btn.setFixedHeight(30)
            del_btn.setObjectName("danger")
            del_btn.setEnabled(u['id'] != self._user['id'])
            del_btn.setStyleSheet("""
                QPushButton#danger {
                    padding: 2px 4px;
                    font-size: 11px;
                }
            """)
            del_btn.clicked.connect(lambda _, uid=u['id']: self._delete_user(uid))

            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            self.table.setCellWidget(i, 6, btn_w)

    def _add_user(self):
        dlg = UserDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                UserQueries.create(d['username'], d['password_hash'], d['role'], d['full_name'])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_user(self, user_id):
        users = {u['id']: u for u in UserQueries.get_all()}
        u = users.get(user_id)
        if not u:
            return
        dlg = UserDialog(dict(u), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                UserQueries.update(user_id, d['username'], d['password_hash'],
                                   d['role'], d['full_name'], d['active'])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_user(self, user_id):
        if QMessageBox.question(
                self, "Confirm", "Deactivate this user?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            UserQueries.delete(user_id)
            self.refresh()
