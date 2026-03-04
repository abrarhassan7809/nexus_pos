THEME: dict[str, str] = {
    "bg_dark":        "#0D0F14",
    "bg_panel":       "#141820",
    "bg_card":        "#1C2130",
    "bg_input":       "#222840",
    "border":         "#2E3A55",
    "accent":         "#FF6B35",
    "accent_dark":    "#CC4A1A",
    "accent_soft":    "#FF8C5A",
    "success":        "#00D68F",
    "warning":        "#FFAA00",
    "danger":         "#FF3860",
    "text_primary":   "#EAEDF5",
    "text_secondary": "#8892AA",
    "text_muted":     "#505870",
    "highlight":      "#2A3560",
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background: {THEME['bg_dark']};
}}
QWidget {{
    background: {THEME['bg_dark']};
    color: {THEME['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 13px;
}}
QLabel {{
    background: transparent;
    color: {THEME['text_primary']};
}}
QPushButton {{
    background: {THEME['bg_card']};
    color: {THEME['text_primary']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {THEME['highlight']};
    border-color: {THEME['accent']};
    color: {THEME['accent_soft']};
}}
QPushButton:pressed {{ background: {THEME['accent_dark']}; }}
QPushButton#accent_btn {{
    background: {THEME['accent']};
    color: #fff;
    border: none;
    font-size: 14px;
    font-weight: 700;
    padding: 10px 24px;
    border-radius: 7px;
}}
QPushButton#accent_btn:hover {{
    background: {THEME['accent_soft']};
    color: {THEME['bg_dark']};
}}
QPushButton#danger_btn {{
    background: {THEME['danger']};
    color: #fff;
    border: none;
    border-radius: 6px;
    font-weight: 700;
}}
QPushButton#danger_btn:hover {{ background: #ff6680; }}
QPushButton#success_btn {{
    background: {THEME['success']};
    color: {THEME['bg_dark']};
    border: none;
    border-radius: 6px;
    font-weight: 700;
}}
QPushButton#success_btn:hover {{ background: #33e8aa; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background: {THEME['bg_input']};
    color: {THEME['text_primary']};
    border: 1px solid {THEME['border']};
    border-radius: 5px;
    padding: 7px 10px;
    selection-background-color: {THEME['accent']};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus {{
    border-color: {THEME['accent']};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {THEME['bg_card']};
    color: {THEME['text_primary']};
    border: 1px solid {THEME['border']};
    selection-background-color: {THEME['accent']};
}}
QTableWidget {{
    background: {THEME['bg_panel']};
    color: {THEME['text_primary']};
    gridline-color: {THEME['border']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    alternate-background-color: {THEME['bg_card']};
}}
QTableWidget::item:selected {{
    background: {THEME['highlight']};
    color: {THEME['accent_soft']};
}}
QHeaderView::section {{
    background: {THEME['bg_card']};
    color: {THEME['accent_soft']};
    border: none;
    border-bottom: 2px solid {THEME['accent']};
    padding: 8px 10px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QTabWidget::pane {{
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    background: {THEME['bg_panel']};
}}
QTabBar::tab {{
    background: {THEME['bg_card']};
    color: {THEME['text_secondary']};
    border: 1px solid {THEME['border']};
    border-bottom: none;
    padding: 10px 22px;
    font-weight: 600;
    border-radius: 5px 5px 0 0;
    margin-right: 3px;
}}
QTabBar::tab:selected {{
    background: {THEME['bg_panel']};
    color: {THEME['accent']};
    border-bottom: 2px solid {THEME['accent']};
}}
QGroupBox {{
    border: 1px solid {THEME['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    font-weight: 700;
    color: {THEME['accent_soft']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {THEME['accent_soft']};
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QScrollBar:vertical {{
    background: {THEME['bg_panel']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {THEME['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {THEME['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QTextEdit, QPlainTextEdit {{
    background: {THEME['bg_input']};
    color: {THEME['text_primary']};
    border: 1px solid {THEME['border']};
    border-radius: 5px;
    padding: 6px;
}}
QMessageBox {{
    background: {THEME['bg_panel']};
}}
QMessageBox QLabel {{ color: {THEME['text_primary']}; }}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {THEME['border']};
}}
QSplitter::handle {{
    background: {THEME['border']};
}}
QMenuBar {{
    background: {THEME['bg_panel']};
    color: {THEME['text_primary']};
    border-bottom: 1px solid {THEME['border']};
}}
QMenuBar::item:selected {{
    background: {THEME['highlight']};
    color: {THEME['accent']};
}}
QMenu {{
    background: {THEME['bg_card']};
    color: {THEME['text_primary']};
    border: 1px solid {THEME['border']};
}}
QMenu::item:selected {{
    background: {THEME['highlight']};
    color: {THEME['accent']};
}}
QStatusBar {{
    background: {THEME['bg_panel']};
    color: {THEME['text_secondary']};
    border-top: 1px solid {THEME['border']};
}}
QProgressBar {{
    background: {THEME['bg_input']};
    border: 1px solid {THEME['border']};
    border-radius: 4px;
    text-align: center;
    color: {THEME['text_primary']};
    font-weight: 700;
}}
QProgressBar::chunk {{
    background: {THEME['accent']};
    border-radius: 4px;
}}
"""
