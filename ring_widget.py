from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRectF


class CompletionRing(QWidget):
    """Small circular progress ring. pct is 0-100. `color` is the
    course's accent color; the unfilled track is drawn in a neutral gray."""

    def __init__(self, pct: float = 0, color: str = "#2A6F6F", size: int = 34, parent=None):
        super().__init__(parent)
        self._pct = pct
        self._color = QColor(color)
        self._size = size
        self.setFixedSize(size, size)

    def set_value(self, pct: float, color: str = None):
        self._pct = pct
        if color:
            self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pad = 3
        rect = QRectF(pad, pad, self._size - 2 * pad, self._size - 2 * pad)

        track_pen = QPen(QColor("#DDDAD0"), 3.2)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        if self._pct > 0:
            fg_pen = QPen(self._color, 3.2)
            fg_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(fg_pen)
            span = int(360 * 16 * (self._pct / 100))
            painter.drawArc(rect, 90 * 16, -span)
        painter.end()
