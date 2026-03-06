from __future__ import annotations
from PySide6.QtCore import QObject, Signal

# ─────────────────────────────────────────────────────────────────────────────
# Palette definitions
# ─────────────────────────────────────────────────────────────────────────────

DARK_PALETTE = {
    "bg":           "#0F1117",
    "surface":      "#1A1D27",
    "surface2":     "#222535",
    "surface3":     "#2A2E40",
    "border":       "#2E3248",
    "accent":       "#6C63FF",
    "accent_hover": "#7C74FF",
    "accent_light": "#3D3880",
    "success":      "#22C55E",
    "warning":      "#F59E0B",
    "danger":       "#EF4444",
    "info":         "#3B82F6",
    "text":         "#E8EAF0",
    "text_muted":   "#7B82A0",
    "text_dim":     "#4B5070",
    "radius":       "8px",
    "radius_sm":    "4px",
    "radius_lg":    "12px",
}

LIGHT_PALETTE = {
    "bg":           "#F0F2F8",
    "surface":      "#FFFFFF",
    "surface2":     "#F5F6FA",
    "surface3":     "#E8EAF2",
    "border":       "#D0D4E8",
    "accent":       "#6C63FF",
    "accent_hover": "#574FD6",
    "accent_light": "#EAE8FF",
    "success":      "#16A34A",
    "warning":      "#D97706",
    "danger":       "#DC2626",
    "info":         "#2563EB",
    "text":         "#1A1D2E",
    "text_muted":   "#5B6080",
    "text_dim":     "#9BA3BF",
    "radius":       "8px",
    "radius_sm":    "4px",
    "radius_lg":    "12px",
}


# ─────────────────────────────────────────────────────────────────────────────
# Stylesheet builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_stylesheet(T: dict) -> str:
    return f"""
/* ─── GLOBAL ─────────────────────────────────── */
QWidget {{
    background-color: {T['bg']};
    color: {T['text']};
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 13px;
}}
QWidget:disabled {{ color: {T['text_dim']}; }}

/* ─── SCROLL BARS ─────────────────────────────── */
QScrollBar:vertical {{
    background: {T['surface']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {T['surface3']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {T['surface']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {T['surface3']};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ─── LABELS ──────────────────────────────────── */
QLabel {{ background: transparent; }}
QLabel#title    {{ font-size: 22px; font-weight: 700; color: {T['text']}; }}
QLabel#subtitle {{ font-size: 13px; color: {T['text_muted']}; }}
QLabel#section  {{ font-size: 11px; font-weight: 700; color: {T['text_muted']};
                   letter-spacing: 1.5px; }}

/* ─── BUTTONS ─────────────────────────────────── */
QPushButton {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    padding: 8px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {T['surface3']};
    border-color: {T['accent']};
}}
QPushButton:pressed  {{ background-color: {T['accent_light']}; }}
QPushButton:disabled {{ color: {T['text_dim']}; border-color: {T['surface3']}; }}

QPushButton#primary {{
    background-color: {T['accent']}; color: white; border: none; font-weight: 600;
}}
QPushButton#primary:hover   {{ background-color: {T['accent_hover']}; }}
QPushButton#primary:pressed {{ background-color: {T['accent_light']}; color: {T['text']}; }}

QPushButton#success {{
    background-color: {T['success']}; color: white; border: none; font-weight: 600;
}}
QPushButton#success:hover {{ background-color: #15803D; }}

QPushButton#danger {{
    background-color: {T['danger']}; color: white; border: none; font-weight: 600;
}}
QPushButton#danger:hover {{ background-color: #B91C1C; }}

QPushButton#warning {{
    background-color: {T['warning']}; color: #111; border: none; font-weight: 600;
}}
QPushButton#warning:hover {{ background-color: #B45309; color: white; }}

QPushButton#ghost {{
    background: transparent;
    border: 1px solid {T['border']};
    color: {T['text_muted']};
}}
QPushButton#ghost:hover {{
    background: {T['surface2']};
    color: {T['text']};
    border-color: {T['accent']};
}}

/* ─── INPUTS ──────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    padding: 7px 12px;
    selection-background-color: {T['accent']};
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {T['accent']};
    background-color: {T['surface']};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    padding: 6px 10px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {T['accent']}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {T['surface3']}; border: none; width: 20px;
}}

QComboBox {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    padding: 7px 12px;
}}
QComboBox:focus {{ border-color: {T['accent']}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    selection-background-color: {T['accent']};
    selection-color: white;
}}

QDateEdit {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    padding: 6px 10px;
}}
QDateEdit:focus {{ border-color: {T['accent']}; }}
QDateEdit::drop-down {{ border: none; width: 24px; }}
QCalendarWidget {{
    background-color: {T['surface2']};
    color: {T['text']};
}}
QCalendarWidget QToolButton {{ color: {T['text']}; background: transparent; }}
QCalendarWidget QAbstractItemView {{
    background: {T['surface2']}; color: {T['text']};
    selection-background-color: {T['accent']};
}}

/* ─── TABLE ───────────────────────────────────── */
QTableWidget, QTableView {{
    background-color: {T['surface']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    gridline-color: {T['surface3']};
    selection-background-color: {T['accent_light']};
    selection-color: {T['text']};
}}
QTableWidget::item, QTableView::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {T['accent_light']};
    color: {T['text']};
}}
QHeaderView::section {{
    background-color: {T['surface2']};
    color: {T['text_muted']};
    font-size: 11px; font-weight: 700; letter-spacing: 1px;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {T['border']};
    border-bottom: 1px solid {T['border']};
}}

/* ─── TABS ────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    background-color: {T['surface']};
}}
QTabBar::tab {{
    background-color: {T['surface']};
    color: {T['text_muted']};
    border: none;
    padding: 10px 20px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    color: {T['text']};
    border-bottom: 2px solid {T['accent']};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {T['text']};
    background-color: {T['surface2']};
}}

/* ─── GROUPBOX ────────────────────────────────── */
QGroupBox {{
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    margin-top: 12px; padding-top: 12px;
    font-weight: 600; color: {T['text_muted']};
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 12px; padding: 0 6px;
    color: {T['text_muted']}; font-size: 11px; letter-spacing: 1px;
}}

/* ─── FRAME / CARD ────────────────────────────── */
QFrame#card {{
    background-color: {T['surface']};
    border: 1px solid {T['border']};
    border-radius: {T['radius_lg']};
}}
QFrame#card2 {{
    background-color: {T['surface2']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
}}

/* ─── DIALOG ──────────────────────────────────── */
QDialog {{ background-color: {T['surface']}; }}

/* ─── STATUS BAR ──────────────────────────────── */
QStatusBar {{
    background-color: {T['surface']};
    color: {T['text_muted']};
    border-top: 1px solid {T['border']};
    font-size: 12px;
}}

/* ─── MENU BAR ────────────────────────────────── */
QMenuBar {{
    background-color: {T['surface']};
    color: {T['text']};
    border-bottom: 1px solid {T['border']};
}}
QMenuBar::item:selected {{ background-color: {T['surface2']}; }}
QMenu {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
}}
QMenu::item:selected {{ background-color: {T['accent']}; color: white; }}

/* ─── CHECKBOX ────────────────────────────────── */
QCheckBox {{ spacing: 8px; color: {T['text']}; background: transparent; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {T['border']};
    border-radius: 4px;
    background: {T['surface2']};
}}
QCheckBox::indicator:checked {{
    background: {T['accent']}; border-color: {T['accent']};
}}

/* ─── SPLITTER ────────────────────────────────── */
QSplitter::handle {{ background: {T['border']}; width: 1px; height: 1px; }}

/* ─── TOOLTIP ─────────────────────────────────── */
QToolTip {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# ThemeManager singleton
# ─────────────────────────────────────────────────────────────────────────────

class ThemeManager(QObject):
    """Singleton that holds the active theme and notifies on change."""
    theme_changed = Signal(str)          # emits "dark" or "light"
    _instance: "ThemeManager | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        super().__init__()
        self._mode = "dark"
        self._initialized = True

    # ── Public API ────────────────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self._mode

    @property
    def palette(self) -> dict:
        return DARK_PALETTE if self._mode == "dark" else LIGHT_PALETTE

    @property
    def stylesheet(self) -> str:
        return _build_stylesheet(self.palette)

    def is_dark(self) -> bool:
        return self._mode == "dark"

    def toggle(self):
        self._mode = "light" if self._mode == "dark" else "dark"
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.stylesheet)
        self.theme_changed.emit(self._mode)

    def apply(self):
        """Apply current theme to the running QApplication."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.stylesheet)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level convenience — keeps all existing imports working
# ─────────────────────────────────────────────────────────────────────────────

def get_theme() -> dict:
    return ThemeManager().palette

# Backwards-compatible aliases used throughout the codebase
THEME      = DARK_PALETTE          # static dark dict (legacy)
STYLESHEET = _build_stylesheet(DARK_PALETTE)   # legacy static string

# Live palette shortcut — use this in new code
T = ThemeManager().palette
