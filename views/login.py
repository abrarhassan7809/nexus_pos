from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from database.queries import UserQueries
from utils.theme import THEME


class LoginDialog(QDialog):
    """Application login dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NEXUS POS — Login")
        self.setFixedSize(420, 500)
        self.setModal(True)
        self.user_data: dict | None = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_banner())
        root.addWidget(self._build_form())

    def _build_banner(self) -> QFrame:
        banner = QFrame()
        banner.setFixedHeight(140)
        banner.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {THEME['bg_card']}, stop:1 #1A2540);"
        )
        lay = QVBoxLayout(banner)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel("⬡ NEXUS POS")
        logo.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        logo.setStyleSheet(
            f"color: {THEME['accent']}; background: transparent; letter-spacing: 3px;"
        )
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Point of Sale Management System")
        sub.setStyleSheet(
            f"color: {THEME['text_secondary']}; background: transparent; font-size: 12px;"
        )
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(logo)
        lay.addWidget(sub)
        return banner

    def _build_form(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"background: {THEME['bg_panel']};")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(14)

        title = QLabel("Welcome Back")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent;")

        self._user_input = QLineEdit()
        self._user_input.setPlaceholderText("Username")
        self._user_input.setText("admin")
        self._user_input.setFixedHeight(42)

        self._pw_input = QLineEdit()
        self._pw_input.setPlaceholderText("Password")
        self._pw_input.setText("admin123")
        self._pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_input.setFixedHeight(42)
        self._pw_input.returnPressed.connect(self._do_login)

        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet(
            f"color: {THEME['danger']}; background: transparent;"
        )
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        login_btn = QPushButton("  SIGN IN  →")
        login_btn.setObjectName("accent_btn")
        login_btn.setFixedHeight(44)
        login_btn.clicked.connect(self._do_login)

        hint = QLabel("🔑  admin / admin123   |   cashier / cash123")
        hint.setStyleSheet(
            f"color: {THEME['text_muted']}; background: transparent; font-size: 11px;"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(title)
        lay.addSpacing(4)
        lay.addWidget(QLabel("Username"))
        lay.addWidget(self._user_input)
        lay.addWidget(QLabel("Password"))
        lay.addWidget(self._pw_input)
        lay.addWidget(self._err_lbl)
        lay.addWidget(login_btn)
        lay.addStretch()
        lay.addWidget(hint)
        return frame

    # ── Slots ─────────────────────────────────────────────────────
    def _do_login(self) -> None:
        username = self._user_input.text().strip()
        password = self._pw_input.text()
        user = UserQueries.authenticate(username, password)
        if user:
            self.user_data = user
            self.accept()
        else:
            self._err_lbl.setText("Invalid username or password.")
            self._pw_input.clear()
            self._pw_input.setFocus()
