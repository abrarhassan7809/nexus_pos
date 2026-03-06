from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPainterPath
from database import UserQueries
from utils import verify_pw
from utils.theme import ThemeManager as _TM


def _T() -> dict:
    return _TM().palette


# ─── Styled input field ────────────────────────────────────────────────────────
class _InputField(QFrame):
    def __init__(self, label: str, placeholder: str,
                 password: bool = False, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("inputField")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {_T()['text_muted']}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 1.5px; background: transparent;"
        )
        outer.addWidget(lbl)

        self._wrapper = QFrame()
        self._wrapper.setObjectName("inputWrapper")
        self._wrapper.setFixedHeight(46)
        self._set_wrapper_style(focused=False, error=False)

        row = QHBoxLayout(self._wrapper)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(
                f"font-size: 15px; color: {_T()['text_dim']}; background: transparent;")
            icon_lbl.setFixedWidth(20)
            row.addWidget(icon_lbl)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setStyleSheet(
            "QLineEdit { background: transparent; border: none; "
            f"color: {_T()['text']}; font-size: 13px; padding: 0; }}"
            f"QLineEdit::placeholder {{ color: {_T()['text_dim']}; }}"
        )
        row.addWidget(self.input)

        if password:
            self._eye_btn = QPushButton("👁")
            self._eye_btn.setFixedSize(28, 28)
            self._eye_btn.setStyleSheet(
                f"QPushButton {{ background: transparent; border: none; "
                f"color: {_T()['text_dim']}; font-size: 14px; }}"
                f"QPushButton:hover {{ color: {_T()['text']}; }}"
            )
            self._eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._eye_btn.clicked.connect(self._toggle_echo)
            row.addWidget(self._eye_btn)

        outer.addWidget(self._wrapper)
        self.input.installEventFilter(self)

    def _set_wrapper_style(self, focused: bool, error: bool):
        T = _T()
        border = T['danger'] if error else (T['accent'] if focused else T['border'])
        bg     = T['surface'] if focused else T['surface2']
        self._wrapper.setStyleSheet(
            f"QFrame#inputWrapper {{"
            f"  background: {bg};"
            f"  border: 1.5px solid {border};"
            f"  border-radius: 8px;"
            f"}}"
        )

    def _toggle_echo(self):
        if self.input.echoMode() == QLineEdit.EchoMode.Password:
            self.input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._eye_btn.setText("🔒")
        else:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye_btn.setText("👁")

    def eventFilter(self, obj, event):
        if obj is self.input:
            if event.type() == QEvent.Type.FocusIn:
                self._set_wrapper_style(focused=True,  error=False)
            elif event.type() == QEvent.Type.FocusOut:
                self._set_wrapper_style(focused=False, error=False)
        return super().eventFilter(obj, event)

    def text(self)  -> str: return self.input.text()
    def clear(self):        self.input.clear()
    def setFocus(self):     self.input.setFocus()

    def set_error(self, has_error: bool):
        self._set_wrapper_style(focused=False, error=has_error)


# ─── Full-screen background widget ────────────────────────────────────────────
class _Background(QWidget):
    """Paints a gradient background that fills the entire dialog."""
    def paintEvent(self, event):
        T = _T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Main background gradient (top-left dark → bottom-right slightly lighter)
        grad = QLinearGradient(0, 0, W, H)
        if _TM().is_dark():
            grad.setColorAt(0.0, QColor("#0A0C14"))
            grad.setColorAt(0.5, QColor("#0F1117"))
            grad.setColorAt(1.0, QColor("#141828"))
        else:
            grad.setColorAt(0.0, QColor("#E8EBF8"))
            grad.setColorAt(0.5, QColor("#F0F2F8"))
            grad.setColorAt(1.0, QColor("#E2E6F4"))
        p.fillRect(0, 0, W, H, grad)

        # Decorative accent circles (subtle, top-right and bottom-left)
        accent = QColor(T['accent'])
        accent.setAlpha(18)
        p.setBrush(accent)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(W - 280, -120, 420, 420)

        accent2 = QColor(T['info'])
        accent2.setAlpha(12)
        p.setBrush(accent2)
        p.drawEllipse(-140, H - 260, 380, 380)

        p.end()


# ─── Login card ────────────────────────────────────────────────────────────────
class _LoginCard(QFrame):
    """The centred white/dark card that holds the login form."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loginCard")
        self.setFixedWidth(420)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self._apply_style()
        _TM().theme_changed.connect(lambda _: self._apply_style())

    def _apply_style(self):
        T = _T()
        self.setStyleSheet(
            f"QFrame#loginCard {{"
            f"  background: {T['surface']};"
            f"  border: 1px solid {T['border']};"
            f"  border-radius: 16px;"
            f"}}"
        )


# ─── Login Dialog (full-screen) ────────────────────────────────────────────────
class LoginDialog(QDialog):
    login_success = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nexus POS — Sign In")

        # Full screen, no frame
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint
        )
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)

        self._user = None
        self._build_ui()

    def _build_ui(self):
        T = _T()

        # Full-screen background
        bg = _Background(self)
        bg.setGeometry(self.rect())

        # Card centred on the background
        card = _LoginCard(bg)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(44, 40, 44, 36)
        card_layout.setSpacing(0)

        # ── Top accent bar inside card ─────────────────────────────────────────
        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T['accent']}, stop:0.6 {T['info']}, stop:1 {T['success']});"
            f"border-radius: 2px;"
        )
        card_layout.addWidget(accent_bar)
        card_layout.addSpacing(28)

        # ── Brand ──────────────────────────────────────────────────────────────
        brand = QLabel("NEXUS")
        brand.setFont(QFont("Segoe UI", 30, QFont.Weight.Black))
        brand.setStyleSheet(
            f"color: {T['accent']}; letter-spacing: 10px; background: transparent;")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(brand)

        tagline = QLabel("POINT  OF  SALE")
        tagline.setStyleSheet(
            f"color: {T['text_dim']}; font-size: 10px; letter-spacing: 5px; "
            f"font-weight: 600; background: transparent;"
        )
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(tagline)

        card_layout.addSpacing(28)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {T['border']}; background: {T['border']};")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        card_layout.addSpacing(24)

        # ── Welcome text ───────────────────────────────────────────────────────
        welcome = QLabel("Welcome back")
        welcome.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {T['text']}; background: transparent;")
        card_layout.addWidget(welcome)

        sub = QLabel("Sign in to your account to continue")
        sub.setStyleSheet(
            f"font-size: 12px; color: {T['text_muted']}; background: transparent;")
        card_layout.addWidget(sub)

        card_layout.addSpacing(24)

        # ── Fields ─────────────────────────────────────────────────────────────
        self.username_field = _InputField("USERNAME", "Enter your username", icon="👤")
        self.username_field.input.returnPressed.connect(
            lambda: self.password_field.setFocus())
        card_layout.addWidget(self.username_field)

        card_layout.addSpacing(14)

        self.password_field = _InputField(
            "PASSWORD", "Enter your password", password=True, icon="🔑")
        self.password_field.input.returnPressed.connect(self._do_login)
        card_layout.addWidget(self.password_field)

        card_layout.addSpacing(8)

        # ── Error label ────────────────────────────────────────────────────────
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(
            f"color: {T['danger']}; font-size: 12px; background: transparent;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setFixedHeight(18)
        card_layout.addWidget(self.error_lbl)

        card_layout.addSpacing(18)

        # ── Sign in button ─────────────────────────────────────────────────────
        self.login_btn = QPushButton("SIGN  IN")
        self.login_btn.setFixedHeight(48)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {T['accent']}, stop:1 {T['accent_hover']});"
            f"  color: white; border: none; border-radius: 8px;"
            f"  font-size: 14px; font-weight: 700; letter-spacing: 3px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {T['accent_hover']}, stop:1 {T['accent']});"
            f"}}"
            f"QPushButton:pressed {{ background: {T['accent_light']}; }}"
        )
        self.login_btn.clicked.connect(self._do_login)
        card_layout.addWidget(self.login_btn)

        card_layout.addSpacing(24)

        # ── Footer ─────────────────────────────────────────────────────────────
        footer_sep = QFrame()
        footer_sep.setFrameShape(QFrame.Shape.HLine)
        footer_sep.setStyleSheet(
            f"color: {T['surface3']}; background: {T['surface3']};")
        footer_sep.setFixedHeight(1)
        card_layout.addWidget(footer_sep)
        card_layout.addSpacing(14)

        footer = QLabel("Default credentials:  admin  /  admin123")
        footer.setStyleSheet(
            f"color: {T['text_dim']}; font-size: 11px; background: transparent;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(footer)

        # ── Position card in the centre of the background ──────────────────────
        card.adjustSize()
        self._card = card
        self._bg   = bg
        self._center_card()

        # ── Quit button (bottom-right of screen) ──────────────────────────────
        quit_btn = QPushButton("✕  Quit", self)
        quit_btn.setObjectName("ghost")
        quit_btn.setFixedSize(90, 32)
        quit_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: 1px solid {T['border']};"
            f"color: {T['text_muted']}; border-radius: 6px; font-size: 12px; }}"
            f"QPushButton:hover {{ background: {T['surface2']}; color: {T['text']}; }}"
        )
        quit_btn.clicked.connect(self.reject)
        self._quit_btn = quit_btn
        self._position_quit_btn()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_bg'):
            self._bg.setGeometry(self.rect())
            self._center_card()
            self._position_quit_btn()

    def _center_card(self):
        if not hasattr(self, '_card'):
            return
        self._card.adjustSize()
        cw = self._card.width()
        ch = self._card.height()
        x  = (self.width()  - cw) // 2
        y  = (self.height() - ch) // 2
        self._card.move(x, y)

    def _position_quit_btn(self):
        if not hasattr(self, '_quit_btn'):
            return
        self._quit_btn.move(self.width() - 106, self.height() - 48)

    def keyPressEvent(self, event):
        # Allow Escape to close
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    # ── Auth ───────────────────────────────────────────────────────────────────
    def _do_login(self):
        username = self.username_field.text().strip()
        password = self.password_field.text()

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