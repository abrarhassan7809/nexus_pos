from __future__ import annotations
from PySide6.QtWidgets import (
    QLabel, QFrame, QHBoxLayout, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QWidget, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from utils.theme import THEME as T


class SectionTitle(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("title")
        font = QFont()
        font.setPointSize(16)
        font.setWeight(QFont.Weight.Bold)
        self.setFont(font)


class SectionSubtitle(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("subtitle")


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"color: {T['border']}; background: {T['border']};")
        self.setFixedHeight(1)


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "—", color: str = None,
                 icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(120)
        self.setMinimumHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 16px; color: {color or T['accent']};")
            icon_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            top_row.addWidget(icon_lbl)
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("section")
        title_lbl.setWordWrap(True)
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size: 22px; font-weight: 700; color: {color or T['text']};"
        )
        self.value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.value_label)

        if color:
            accent_bar = QFrame()
            accent_bar.setFixedHeight(3)
            accent_bar.setStyleSheet(f"background: {color}; border-radius: 2px;")
            layout.addWidget(accent_bar)

    def set_value(self, v: str):
        self.value_label.setText(v)


def styled_table(columns: list[str], col_widths: list[int] | None = None,
                 stretch_col: int = -1) -> QTableWidget:
    """
    col_widths : pixel width for each column (Fixed mode); None columns use ResizeToContents.
    stretch_col: column index that fills remaining space (-1 = last column).
    """
    tbl = QTableWidget()
    tbl.setColumnCount(len(columns))
    tbl.setHorizontalHeaderLabels(columns)

    tbl.verticalHeader().setVisible(False)
    tbl.verticalHeader().setDefaultSectionSize(50)
    tbl.verticalHeader().setMinimumSectionSize(32)

    tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tbl.setAlternatingRowColors(True)
    tbl.setShowGrid(True)
    tbl.setWordWrap(False)
    tbl.setStyleSheet(
        f"QTableWidget {{ alternate-background-color: {T['surface2']}; "
        f"background-color: {T['surface']}; }}"
    )

    hdr = tbl.horizontalHeader()
    hdr.setHighlightSections(False)
    hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    n = len(columns)
    actual_stretch = stretch_col if stretch_col >= 0 else n - 1

    for i in range(n):
        if i == actual_stretch:
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        elif col_widths and i < len(col_widths) and col_widths[i] is not None:
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            tbl.setColumnWidth(i, col_widths[i])
        else:
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    tbl.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    tbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return tbl


def make_table_item(text: str,
                    align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    color: str = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(align)
    if color:
        item.setForeground(QColor(color))
    return item