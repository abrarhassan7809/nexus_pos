THEME = {
    # Base
    "bg":           "#0F1117",
    "surface":      "#1A1D27",
    "surface2":     "#222535",
    "surface3":     "#2A2E40",
    "border":       "#2E3248",
    # Accent
    "accent":       "#6C63FF",
    "accent_hover": "#7C74FF",
    "accent_light": "#3D3880",
    # Semantic
    "success":      "#22C55E",
    "warning":      "#F59E0B",
    "danger":       "#EF4444",
    "info":         "#3B82F6",
    # Text
    "text":         "#E8EAF0",
    "text_muted":   "#7B82A0",
    "text_dim":     "#4B5070",
    # Misc
    "radius":       "8px",
    "radius_sm":    "4px",
    "radius_lg":    "12px",
}

T = THEME

STYLESHEET = f"""
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
QLabel#title {{ font-size: 22px; font-weight: 700; color: {T['text']}; }}
QLabel#subtitle {{ font-size: 13px; color: {T['text_muted']}; }}
QLabel#section {{ font-size: 11px; font-weight: 700; color: {T['text_muted']};
                  letter-spacing: 1.5px; text-transform: uppercase; }}

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
QPushButton:pressed {{ background-color: {T['accent_light']}; }}
QPushButton:disabled {{ color: {T['text_dim']}; border-color: {T['surface3']}; }}

QPushButton#primary {{
    background-color: {T['accent']};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#primary:hover {{ background-color: {T['accent_hover']}; }}

QPushButton#success {{
    background-color: {T['success']};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#success:hover {{ background-color: #16A34A; }}

QPushButton#danger {{
    background-color: {T['danger']};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#danger:hover {{ background-color: #DC2626; }}

QPushButton#warning {{
    background-color: {T['warning']};
    color: #111;
    border: none;
    font-weight: 600;
}}

QPushButton#ghost {{
    background: transparent;
    border: 1px solid {T['border']};
    color: {T['text_muted']};
}}
QPushButton#ghost:hover {{
    background: {T['surface2']};
    color: {T['text']};
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
    background: {T['surface3']};
    border: none;
    width: 20px;
}}

QComboBox {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    padding: 7px 12px;
}}
QComboBox:focus {{ border-color: {T['accent']}; }}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    selection-background-color: {T['accent']};
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
QCalendarWidget QAbstractItemView {{ background: {T['surface2']}; color: {T['text']}; }}

/* ─── TABLE ───────────────────────────────────── */
QTableWidget, QTableView {{
    background-color: {T['surface']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: {T['radius']};
    gridline-color: {T['surface3']};
    selection-background-color: {T['accent_light']};
}}
QTableWidget::item, QTableView::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {T['accent_light']};
    color: white;
}}
QHeaderView::section {{
    background-color: {T['surface2']};
    color: {T['text_muted']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
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
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
    color: {T['text_muted']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {T['text_muted']};
    font-size: 11px;
    letter-spacing: 1px;
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
QDialog {{
    background-color: {T['surface']};
}}

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
QMenu::item:selected {{ background-color: {T['accent']}; }}

/* ─── CHECKBOX ────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {T['text']};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {T['border']};
    border-radius: 4px;
    background: {T['surface2']};
}}
QCheckBox::indicator:checked {{
    background: {T['accent']};
    border-color: {T['accent']};
}}

/* ─── PROGRESS BAR ────────────────────────────── */
QProgressBar {{
    background: {T['surface2']};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {T['accent']};
    border-radius: 4px;
}}

/* ─── SPLITTER ────────────────────────────────── */
QSplitter::handle {{
    background: {T['border']};
    width: 1px;
    height: 1px;
}}

/* ─── TOOLTIP ─────────────────────────────────── */
QToolTip {{
    background-color: {T['surface2']};
    color: {T['text']};
    border: 1px solid {T['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
"""
