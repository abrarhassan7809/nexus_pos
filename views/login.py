from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QLinearGradient, QBrush
from database import UserQueries
from utils import verify_pw
from utils.theme import THEME as T


class _InputField(QFrame):
    """Labelled input with visible border, icon slot, and focus glow."""

    def __init__(self, label: str, placeholder: str,
                 password: bool = False, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("inputField")
        self._focused = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        # Label
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {T['text_muted']}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 1.5px; background: transparent;"
        )
        outer.addWidget(lbl)

        # Input wrapper — gives us the bordered box
        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        wrapper.setStyleSheet(
            f"QFrame#inputWrapper {{"
            f"  background: {T['surface2']};"
            f"  border: 1.5px solid {T['border']};"
            f"  border-radius: 8px;"
            f"}}"
        )
        wrapper.setFixedHeight(46)
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(
                f"font-size: 15px; color: {T['text_dim']}; background: transparent;")
            icon_lbl.setFixedWidth(20)
            row.addWidget(icon_lbl)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setStyleSheet(
            "QLineEdit {"
            "  background: transparent;"
            "  border: none;"
            f"  color: {T['text']};"
            "  font-size: 13px;"
            "  padding: 0;"
            "}"
            "QLineEdit::placeholder {"
            f"  color: {T['text_dim']};"
            "}"
        )
        row.addWidget(self.input)

        # Eye toggle for password
        if password:
            self._eye_btn = QPushButton("👁")
            self._eye_btn.setFixedSize(28, 28)
            self._eye_btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; "
                f"color: {T['text_dim']}; font-size: 14px; }}"
                f"QPushButton:hover {{ color: {T['text']}; }}"
            )
            self._eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._eye_btn.clicked.connect(self._toggle_echo)
            row.addWidget(self._eye_btn)

        outer.addWidget(wrapper)
        self._wrapper = wrapper

        # Focus glow via event filter on the inner QLineEdit
        self.input.installEventFilter(self)

    def _toggle_echo(self):
        if self.input.echoMode() == QLineEdit.EchoMode.Password:
            self.input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._eye_btn.setText("🔒")
        else:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye_btn.setText("👁")

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self.input:
            if event.type() == QEvent.Type.FocusIn:
                self._wrapper.setStyleSheet(
                    f"QFrame#inputWrapper {{"
                    f"  background: {T['surface']};"
                    f"  border: 1.5px solid {T['accent']};"
                    f"  border-radius: 8px;"
                    f"}}"
                )
            elif event.type() == QEvent.Type.FocusOut:
                self._wrapper.setStyleSheet(
                    f"QFrame#inputWrapper {{"
                    f"  background: {T['surface2']};"
                    f"  border: 1.5px solid {T['border']};"
                    f"  border-radius: 8px;"
                    f"}}"
                )
        return super().eventFilter(obj, event)

    def text(self) -> str:
        return self.input.text()

    def clear(self):
        self.input.clear()

    def setFocus(self):
        self.input.setFocus()

    def set_error(self, has_error: bool):
        color = T['danger'] if has_error else T['border']
        self._wrapper.setStyleSheet(
            f"QFrame#inputWrapper {{"
            f"  background: {T['surface2']};"
            f"  border: 1.5px solid {color};"
            f"  border-radius: 8px;"
            f"}}"
        )


class LoginDialog(QDialog):
    login_success = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nexus POS — Sign In")
        self.setFixedSize(440, 560)
        # Keep native window frame (title bar + close button)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.MSWindowsFixedSizeDialogHint
        )
        self._user = None
        self._build_ui()
        self._center_on_screen()

    def _center_on_screen(self):
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.x() + (screen.width()  - self.width())  // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Accent bar across top ──────────────────────────────────────────────
        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T['accent']}, stop:0.6 {T['info']}, stop:1 {T['success']});"
        )
        root.addWidget(accent_bar)

        # ── Main content area ──────────────────────────────────────────────────
        content = QFrame()
        content.setStyleSheet(f"QFrame {{ background: {T['surface']}; border: none; }}")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(48, 44, 48, 36)
        cl.setSpacing(0)

        # Brand
        brand = QLabel("NEXUS")
        brand.setFont(QFont("Segoe UI", 30, QFont.Weight.Black))
        brand.setStyleSheet(
            f"color: {T['accent']}; letter-spacing: 10px; background: transparent;")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(brand)

        tagline = QLabel("POINT  OF  SALE")
        tagline.setStyleSheet(
            f"color: {T['text_dim']}; font-size: 10px; letter-spacing: 5px; "
            f"font-weight: 600; background: transparent;"
        )
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(tagline)

        cl.addSpacing(10)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {T['border']}; background: {T['border']};")
        sep.setFixedHeight(1)
        cl.addWidget(sep)

        cl.addSpacing(28)

        # Welcome text
        welcome = QLabel("Welcome back")
        welcome.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {T['text']}; background: transparent;")
        cl.addWidget(welcome)

        sub = QLabel("Sign in to your account to continue")
        sub.setStyleSheet(
            f"font-size: 12px; color: {T['text_muted']}; background: transparent;")
        cl.addWidget(sub)

        cl.addSpacing(28)

        # Username field
        self.username_field = _InputField(
            "USERNAME", "Enter your username", icon="👤")
        self.username_field.input.returnPressed.connect(
            lambda: self.password_field.setFocus())
        cl.addWidget(self.username_field)

        cl.addSpacing(16)

        # Password field
        self.password_field = _InputField(
            "PASSWORD", "Enter your password", password=True, icon="🔑")
        self.password_field.input.returnPressed.connect(self._do_login)
        cl.addWidget(self.password_field)

        cl.addSpacing(8)

        # Error label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(
            f"color: {T['danger']}; font-size: 12px; background: transparent;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setFixedHeight(18)
        cl.addWidget(self.error_lbl)

        cl.addSpacing(20)

        # Sign in button
        self.login_btn = QPushButton("SIGN  IN")
        self.login_btn.setFixedHeight(48)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {T['accent']}, stop:1 {T['accent_hover']});"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: 8px;"
            f"  font-size: 14px;"
            f"  font-weight: 700;"
            f"  letter-spacing: 3px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {T['accent_hover']}, stop:1 {T['accent']});"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {T['accent_light']};"
            f"}}"
        )
        self.login_btn.clicked.connect(self._do_login)
        cl.addWidget(self.login_btn)

        cl.addStretch()

        # Footer
        footer_sep = QFrame()
        footer_sep.setFrameShape(QFrame.Shape.HLine)
        footer_sep.setStyleSheet(f"color: {T['surface3']}; background: {T['surface3']};")
        footer_sep.setFixedHeight(1)
        cl.addWidget(footer_sep)
        cl.addSpacing(14)

        footer = QLabel("Default credentials:  admin  /  admin123")
        footer.setStyleSheet(
            f"color: {T['text_dim']}; font-size: 11px; background: transparent;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(footer)

        root.addWidget(content)

    def _do_login(self):
        username = self.username_field.text().strip()
        password = self.password_field.text()

        # Reset error states
        self.error_lbl.setText("")
        self.username_field.set_error(False)
        self.password_field.set_error(False)

        if not username:
            self.username_field.set_error(True)
            self.error_lbl.setText("Username is required.")
            self.username_field.setFocus()
            return

        if not password:
            self.password_field.set_error(True)
            self.error_lbl.setText("Password is required.")
            self.password_field.setFocus()
            return

        user = UserQueries.get_by_username(username)
        if user and verify_pw(password, user["password"]):
            self._user = user
            self.login_success.emit(user)
            self.accept()
        else:
            self.username_field.set_error(True)
            self.password_field.set_error(True)
            self.error_lbl.setText("Invalid username or password.")
            self.password_field.clear()
            self.password_field.setFocus()

    def get_user(self):
        return self._user