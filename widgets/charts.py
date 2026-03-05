from __future__ import annotations
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QPainterPath
from utils.theme import THEME as T


class WeeklyBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[str, float]] = []
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_data(self, data: list[tuple[str, float]]):
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 54, 16, 16, 40
        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b

        max_val = max(v for _, v in self._data) or 1

        # Background
        p.fillRect(0, 0, W, H, QColor(T['surface']))

        # Grid lines
        grid_pen = QPen(QColor(T['border']))
        grid_pen.setWidth(1)
        p.setPen(grid_pen)
        steps = 4
        for i in range(steps + 1):
            y = pad_t + chart_h - int(chart_h * i / steps)
            p.drawLine(pad_l, y, W - pad_r, y)
            val = max_val * i / steps
            p.setPen(QColor(T['text_muted']))
            fnt = QFont(); fnt.setPointSize(8)
            p.setFont(fnt)
            p.drawText(2, y + 5, 48, 16, Qt.AlignmentFlag.AlignRight, f"${val:,.0f}")
            p.setPen(grid_pen)

        n = len(self._data)
        bar_w = max(10, min(50, (chart_w // n) - 10))
        gap = (chart_w - bar_w * n) // (n + 1)

        for i, (label, value) in enumerate(self._data):
            x = pad_l + gap + i * (bar_w + gap)
            bar_h = int(chart_h * value / max_val) if max_val else 0
            y = pad_t + chart_h - bar_h

            # Gradient bar
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, QColor(T['accent']))
            grad.setColorAt(1, QColor(T['accent_light']))
            path = QPainterPath()
            radius = 4
            path.addRoundedRect(x, y, bar_w, bar_h, radius, radius)
            p.fillPath(path, QBrush(grad))

            # Value label on top
            p.setPen(QColor(T['text_muted']))
            fnt2 = QFont(); fnt2.setPointSize(8)
            p.setFont(fnt2)
            p.drawText(x - 10, y - 14, bar_w + 20, 14,
                       Qt.AlignmentFlag.AlignHCenter, f"${value:,.0f}" if value >= 1 else "")

            # X-axis label
            p.setPen(QColor(T['text_muted']))
            p.drawText(x - 10, H - pad_b + 6, bar_w + 20, 20,
                       Qt.AlignmentFlag.AlignHCenter, label[-5:])

        p.end()


class TopProductsChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[str, float]] = []
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_data(self, data: list[tuple[str, float]]):
        self._data = data[:8]
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, QColor(T['surface']))

        max_val = max(v for _, v in self._data) or 1
        n = len(self._data)
        row_h = H // n
        pad_l, pad_r = 160, 80

        COLORS = [T['accent'], T['info'], T['success'], T['warning'],
                  "#A78BFA", "#34D399", "#F87171", "#60A5FA"]

        for i, (name, value) in enumerate(self._data):
            y = i * row_h
            bar_h = max(8, row_h - 14)
            bar_w = int((W - pad_l - pad_r) * value / max_val)

            # Name
            p.setPen(QColor(T['text']))
            fnt = QFont(); fnt.setPointSize(9)
            p.setFont(fnt)
            p.drawText(0, y + (row_h - 16) // 2, 152, 16,
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       name[:22])

            # Bar
            color = COLORS[i % len(COLORS)]
            path = QPainterPath()
            path.addRoundedRect(pad_l, y + (row_h - bar_h) // 2, bar_w, bar_h, 3, 3)
            p.fillPath(path, QColor(color))

            # Value
            p.setPen(QColor(T['text_muted']))
            p.drawText(pad_l + bar_w + 6, y + (row_h - 16) // 2, 70, 16,
                       Qt.AlignmentFlag.AlignLeft,
                       f"${value:,.0f}")

        p.end()
