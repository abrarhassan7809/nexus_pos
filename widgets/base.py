from PySide6.QtWidgets import (QLabel, QFrame, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from utils.theme import THEME


# ── Section Title ─────────────────────────────────────────────────
class SectionTitle(QLabel):
    """Bold page-level heading."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.setStyleSheet(f"color: {THEME['text_primary']}; padding: 4px 0;")


# ── KPI Stat Card ─────────────────────────────────────────────────
class StatCard(QFrame):
    """
    A styled card displaying an icon, a big value label, and a title label.

    Usage::

        card = StatCard("Revenue Today", "$0.00", icon="$", color=THEME["success"])
        card.set_value("$1,234.56")
    """

    def __init__(self, title: str, value: str = "—",
                 icon: str = "●", color: str | None = None, parent=None):
        super().__init__(parent)
        color = color or THEME["accent"]
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: {THEME['bg_card']};
                border: 1px solid {THEME['border']};
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setSpacing(4)

        # Icon row
        top = QHBoxLayout()
        ico_lbl = QLabel(icon)
        ico_lbl.setFont(QFont("Segoe UI", 20))
        ico_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        top.addWidget(ico_lbl)
        top.addStretch()
        lay.addLayout(top)

        # Value
        self._val_lbl = QLabel(str(value))
        self._val_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._val_lbl.setStyleSheet(
            f"color: {THEME['text_primary']}; background: transparent;"
        )
        lay.addWidget(self._val_lbl)

        # Title
        title_lbl = QLabel(title.upper())
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet(
            f"color: {THEME['text_secondary']}; letter-spacing: 1px; background: transparent;"
        )
        lay.addWidget(title_lbl)

    def set_value(self, value) -> None:
        """Update the displayed value."""
        self._val_lbl.setText(str(value))


# ── Horizontal Divider ────────────────────────────────────────────
class Divider(QFrame):
    """Thin horizontal separator line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(
            f"color: {THEME['border']}; background: {THEME['border']}; max-height: 1px;"
        )


# ── Table Factory ─────────────────────────────────────────────────
def styled_table(columns: list[str]) -> QTableWidget:
    """
    Return a QTableWidget pre-configured with the app's visual style.

    Args:
        columns: list of column header labels.
    """
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.horizontalHeader().setStretchLastSection(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(True)
    return table
