from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QFont
from PyQt5.QtWidgets import QTabBar

class TabBar(QTabBar):
    addTabRequested = pyqtSignal()
    closeTabRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plus_width = 18
        self._plus_margin = 6
        self._min_tab_width = 10
        self._max_tab_width = 100
        self.setCursor(Qt.ArrowCursor)
        self.setElideMode(Qt.ElideRight)
        self.setExpanding(False)
        self._last_plus_rect = QRect()

    def tabSizeHint(self, index): #rozmiar tabów
        base = super().tabSizeHint(index)
        count = max(1, self.count())
        total_w = max(0, self.width())
        reserved_for_plus = self._plus_width + 2 * self._plus_margin
        available_for_tabs = max(1, total_w - reserved_for_plus)

        per_tab = available_for_tabs // count
        w = int(min(self._max_tab_width, max(self._min_tab_width, per_tab), base.width()))

        base.setWidth(w)
        return base

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        last_rect = QRect(0,0,0,0)
        if self.count() > 0:
            last_rect = self.tabRect(self.count() - 1)
        plus_x = (last_rect.right() + 6) if last_rect.width() else 4

        plus_w = self._plus_width
        plus_h = self.height() - 8
        plus_y = 4
        plus_rect = QRect(plus_x, plus_y, plus_w, plus_h)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().window())

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(self.palette().mid().color())
        painter.setPen(pen)
        painter.drawRoundedRect(plus_rect, 4, 4)

        painter.setPen(self.palette().text().color())
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(plus_rect, Qt.AlignCenter, "+")

        painter.end()

        self._last_plus_rect = plus_rect

    def mouseReleaseEvent(self, event):
        pos = event.pos()
        if hasattr(self, "_last_plus_rect") and self._last_plus_rect.contains(pos):
            # emit signal to add a tab
            self.addTabRequested.emit()
            return
        if event.button() == Qt.MiddleButton:
            idx = self.tabAt(pos)
            if idx != -1:
                self.closeTabRequested.emit(idx)
                return
        super().mouseReleaseEvent(event)

    def minimumSizeHint(self):
        return super().minimumSizeHint()