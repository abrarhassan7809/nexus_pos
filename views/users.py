from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QMessageBox,
                               QDialog, QFormLayout, QLineEdit, QComboBox, QInputDialog, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from database.queries import UserQueries
from utils.theme import THEME
from widgets.base import SectionTitle, styled_table


# ═══════════════════════════════════════════════════════════════════
#  USERS TAB
# ═══════════════════════════════════════════════════════════════════
class UsersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        lay.setContentsMargins(12, 12, 12, 12)

        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("User Management"))
        hdr.addStretch()
        add_btn = QPushButton("➕  Add User"); add_btn.setObjectName("accent_btn")
        add_btn.clicked.connect(self._add)
        hdr.addWidget(add_btn)
        lay.addLayout(hdr)

        self._tbl = styled_table(["ID", "Username", "Full Name", "Role", "Created At"])
        self._tbl.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        lay.addWidget(self._tbl)

        br = QHBoxLayout()
        edit_btn = QPushButton("✏  Edit");             edit_btn.clicked.connect(self._edit)
        del_btn  = QPushButton("🗑  Delete");            del_btn.setObjectName("danger_btn"); del_btn.clicked.connect(self._delete)
        pw_btn   = QPushButton("🔑  Change Password"); pw_btn.clicked.connect(self._change_pw)
        br.addWidget(edit_btn); br.addWidget(del_btn); br.addWidget(pw_btn); br.addStretch()
        lay.addLayout(br)

    # ── Data ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._tbl.setRowCount(0)
        for r in UserQueries.get_all():
            ri = self._tbl.rowCount()
            self._tbl.insertRow(ri)
            cells = [str(r["id"]), r["username"], r["full_name"] or "",
                     r["role"], r["created_at"][:16]]
            for ci, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                item.setData(Qt.ItemDataRole.UserRole, r)
                if ci == 3:
                    col = THEME["accent"] if r["role"] == "admin" else THEME["success"]
                    item.setForeground(QColor(col))
                self._tbl.setItem(ri, ci, item)

    def _selected(self) -> dict | None:
        row = self._tbl.currentRow()
        if row < 0:
            return None
        return self._tbl.item(row, 0).data(Qt.ItemDataRole.UserRole)

    # ── Slots ─────────────────────────────────────────────────────
    def _add(self) -> None:
        if UserDialog(parent=self).exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit(self) -> None:
        u = self._selected()
        if not u:
            return
        if UserDialog(user=u, parent=self).exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete(self) -> None:
        u = self._selected()
        if not u:
            return
        if u["username"] == "admin":
            QMessageBox.warning(self, "Protected",
                                "Cannot delete the main admin account.")
            return
        if (QMessageBox.question(
            self, "Delete", f"Delete user '{u['username']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes):
            UserQueries.delete(u["id"])
            self.refresh()

    def _change_pw(self) -> None:
        u = self._selected()
        if not u:
            return
        pw, ok = QInputDialog.getText(
            self, "Change Password",
            f"New password for {u['username']}:",
            QLineEdit.EchoMode.Password,
        )
        if ok and pw:
            UserQueries.change_password(u["id"], pw)
            QMessageBox.information(self, "Done", "Password updated.")


# ═══════════════════════════════════════════════════════════════════
#  USER DIALOG
# ═══════════════════════════════════════════════════════════════════
class UserDialog(QDialog):
    def __init__(self, user: dict | None = None, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Add User" if not user else "Edit User")
        self.setFixedSize(360, 300)
        self._build()
        if user:
            self._fill(user)

    def _build(self) -> None:
        lay = QFormLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(24, 24, 24, 24)

        self._uname = QLineEdit(); self._uname.setFixedHeight(34)
        self._fname = QLineEdit(); self._fname.setFixedHeight(34)
        self._role  = QComboBox(); self._role.addItems(["cashier", "admin"]); self._role.setFixedHeight(34)
        self._pw    = QLineEdit(); self._pw.setEchoMode(QLineEdit.EchoMode.Password); self._pw.setFixedHeight(34)
        self._pw.setPlaceholderText(
            "Leave blank to keep current" if self.user else "Required"
        )

        lay.addRow("Username *", self._uname)
        lay.addRow("Full Name",  self._fname)
        lay.addRow("Role",       self._role)
        lay.addRow("Password",   self._pw)

        btns = QHBoxLayout()
        ok = QPushButton("Save"); ok.setObjectName("accent_btn"); ok.clicked.connect(self._save)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        lay.addRow(btns)

    def _fill(self, u: dict) -> None:
        self._uname.setText(u["username"])
        self._fname.setText(u["full_name"] or "")
        idx = self._role.findText(u["role"])
        if idx >= 0:
            self._role.setCurrentIndex(idx)

    def _save(self) -> None:
        uname = self._uname.text().strip()
        if not uname:
            QMessageBox.warning(self, "Validation", "Username is required.")
            return
        if not self.user and not self._pw.text():
            QMessageBox.warning(self, "Validation", "Password is required.")
            return
        try:
            if self.user:
                UserQueries.update(
                    self.user["id"], uname,
                    self._fname.text(), self._role.currentText(),
                    self._pw.text() or None,
                )
            else:
                UserQueries.create(
                    uname, self._fname.text(),
                    self._role.currentText(), self._pw.text(),
                )
            self.accept()
        except Exception as e:
            if "UNIQUE" in str(e):
                QMessageBox.warning(self, "Duplicate",
                                    f"Username '{uname}' already exists.")
            else:
                QMessageBox.critical(self, "Error", str(e))
