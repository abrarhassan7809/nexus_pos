from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QLinearGradient)
from utils.theme import THEME


# ── Palette for multi-series bar charts ──────────────────────────
_PALETTE = [
    THEME["accent"],  THEME["success"], THEME["warning"],
    "#9B59B6", "#3498DB", "#E74C3C",
    "#1ABC9C", "#F39C12", "#2ECC71", "#E67E22",
]


# ═══════════════════════════════════════════════════════════════════
class WeeklyBarChart(QWidget):
    """
    Vertical bar chart showing daily revenue for the last N days.

    Call ``set_data(days_data)`` with a list of dicts:
        [{"day": "Mon 01", "revenue": 123.45, "orders": 5, "avg": 24.69}, ...]
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = []
        self.setMinimumHeight(240)
        self.setStyleSheet(
            f"background: {THEME['bg_card']}; border-radius: 8px;"
        )

    def set_data(self, data: list[dict]) -> None:
        self._data = data
        self.update()

    def paintEvent(self, _event):
        if not self._data:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        PAD_L, PAD_R, PAD_T, PAD_B = 64, 20, 24, 42

        max_rev = max((d["revenue"] for d in self._data), default=1) or 1
        n = len(self._data)
        slot_w = (W - PAD_L - PAD_R) / n
        bar_w  = int(slot_w * 0.55)
        chart_h = H - PAD_T - PAD_B

        # Grid lines + Y axis labels
        for i in range(5):
            gy = PAD_T + chart_h * i // 4
            p.setPen(QPen(QColor(THEME["border"]), 1))
            p.drawLine(PAD_L, gy, W - PAD_R, gy)
            p.setPen(QColor(THEME["text_muted"]))
            p.setFont(QFont("Segoe UI", 8))
            label = f"${max_rev * (4 - i) / 4:,.0f}"
            p.drawText(2, gy - 6, PAD_L - 6, 14,
                       int(Qt.AlignmentFlag.AlignRight), label)

        # Bars
        for i, d in enumerate(self._data):
            bx = int(PAD_L + i * slot_w + (slot_w - bar_w) / 2)
            bh = int((d["revenue"] / max_rev) * chart_h)
            by = H - PAD_B - bh

            grad = QLinearGradient(bx, by, bx, H - PAD_B)
            grad.setColorAt(0, QColor(THEME["accent"]))
            grad.setColorAt(1, QColor(THEME["accent_dark"]))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(bx, by, bar_w, bh, 4, 4)

            # Value above bar
            if bh > 0:
                p.setPen(QColor(THEME["text_primary"]))
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                p.drawText(bx, by - 16, bar_w, 14,
                           int(Qt.AlignmentFlag.AlignCenter),
                           f"${d['revenue']:,.0f}")

            # Day label below bar
            p.setPen(QColor(THEME["text_secondary"]))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(bx, H - PAD_B + 6, bar_w, 16,
                       int(Qt.AlignmentFlag.AlignCenter), d["day"])

        p.end()


# ═══════════════════════════════════════════════════════════════════
class TopProductsChart(QWidget):
    """
    Horizontal bar chart for top-N products by revenue.

    Call ``set_data(rows)`` with a list of dicts:
        [{"product_name": "...", "total_rev": 999.0, "total_qty": 42}, ...]
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = []
        self.setMinimumHeight(300)
        self.setStyleSheet(
            f"background: {THEME['bg_card']}; border-radius: 8px;"
        )

    def set_data(self, data: list[dict]) -> None:
        self._data = data
        self.update()

    def paintEvent(self, _event):
        if not self._data:
            p = QPainter(self)
            p.setPen(QColor(THEME["text_muted"]))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No data for this period")
            p.end()
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        PAD = 16
        row_h = min(38, (H - PAD * 2) // max(len(self._data), 1))
        max_rev = max(d["total_rev"] for d in self._data) or 1
        bar_area = W - 240 - PAD * 2   # space left for bars

        for i, d in enumerate(self._data):
            y = PAD + i * row_h
            bar_w = int((d["total_rev"] / max_rev) * bar_area)
            color = QColor(_PALETTE[i % len(_PALETTE)])

            # Product name
            p.setPen(QColor(THEME["text_primary"]))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(PAD, y, 155, row_h - 4,
                       int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       d["product_name"][:22])

            # Horizontal bar
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(170 + PAD, y + 5, max(bar_w, 4), row_h - 12, 3, 3)

            # Revenue + qty label
            p.setPen(QColor(THEME["text_secondary"]))
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(W - 95, y, 88, row_h - 4,
                       int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                       f"${d['total_rev']:,.2f}  ({int(d['total_qty'])})")

        p.end()
