from datetime import timedelta
from collections import defaultdict

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget,
                              QPushButton, QLabel, QStackedWidget, QScrollArea,
                              QFrame, QSizePolicy)
from PyQt5.QtGui import QPainter, QColor, QTextCharFormat
from PyQt5.QtCore import Qt, QDate


class MonthCalendar(QCalendarWidget):
    """Standard month grid; each day gets small colored dots, one per
    course that has an assessment due that day."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setStyleSheet("""
            QCalendarWidget QToolButton { color: #1E2420; background: transparent; }
            QCalendarWidget QAbstractItemView:enabled { color: #1E2420; }
        """)

    def _dots_for(self, qdate: QDate):
        py_date = qdate.toPyDate()
        colors = []
        for course, assessment in self.controller.all_assessments_with_course():
            if assessment.due_date == py_date:
                colors.append(course.color)
        return colors

    def paintCell(self, painter: QPainter, rect, date: QDate):
        super().paintCell(painter, rect, date)
        colors = self._dots_for(date)
        if not colors:
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        dot_r = 3
        gap = 3
        total_w = len(colors) * (2 * dot_r) + (len(colors) - 1) * gap
        x = rect.center().x() - total_w / 2 + dot_r
        y = rect.bottom() - 8
        for color in colors:
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x - dot_r), int(y - dot_r), dot_r * 2, dot_r * 2)
            x += 2 * dot_r + gap
        painter.restore()

    def refresh(self):
        self.updateCells()


class WeekView(QWidget):
    """Shows the 7 days of the current week as columns. Each column lists
    the assessments due that day as colored chips. Note: Assessment only
    stores a due *date*, not a time of day, so this shows due-day chips
    rather than an hour-by-hour schedule."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.anchor = QDate.currentDate()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        nav = QHBoxLayout()
        prev_btn = QPushButton("\u2039")
        next_btn = QPushButton("\u203a")
        for b in (prev_btn, next_btn):
            b.setFixedWidth(28)
        prev_btn.clicked.connect(lambda: self._shift(-7))
        next_btn.clicked.connect(lambda: self._shift(7))
        self.range_label = QLabel()
        self.range_label.setStyleSheet("font-weight:600;")
        nav.addWidget(prev_btn)
        nav.addWidget(self.range_label, 1, Qt.AlignCenter)
        nav.addWidget(next_btn)
        outer.addLayout(nav)

        self.days_row = QHBoxLayout()
        self.days_row.setSpacing(6)
        outer.addLayout(self.days_row)

        self.refresh()

    def _shift(self, days):
        self.anchor = self.anchor.addDays(days)
        self.refresh()

    def _week_start(self):
        # Monday as the first day of the week
        dow = self.anchor.dayOfWeek()  # 1=Mon .. 7=Sun
        return self.anchor.addDays(-(dow - 1))

    def refresh(self):
        while self.days_row.count():
            item = self.days_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        start = self._week_start()
        end = start.addDays(6)
        self.range_label.setText(f"{start.toString('MMM d')} \u2013 {end.toString('MMM d')}")

        due_map = defaultdict(list)
        for course, assessment in self.controller.all_assessments_with_course():
            due_map[assessment.due_date].append((course, assessment))

        today = QDate.currentDate()
        for i in range(7):
            qd = start.addDays(i)
            col = QFrame()
            col.setStyleSheet(
                "background:%s; border-radius:10px;" % ("#F6F5F1" if qd == today else "transparent")
            )
            v = QVBoxLayout(col)
            v.setContentsMargins(4, 4, 4, 4)
            header = QLabel(qd.toString("ddd d"))
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("font-size:11px; color:#5C6660; font-weight:600;")
            v.addWidget(header)

            for course, assessment in due_map.get(qd.toPyDate(), []):
                chip = QLabel(f"{assessment.name}\n{course.name}")
                chip.setWordWrap(True)
                chip.setStyleSheet(
                    f"background:{course.color}; color:white; border-radius:6px; "
                    f"padding:4px; font-size:10px;"
                )
                v.addWidget(chip)
            v.addStretch()
            col.setMinimumHeight(220)
            self.days_row.addWidget(col, 1)


class CalendarPanel(QFrame):
    """The right-hand panel: a Month/Week toggle above the active view."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setStyleSheet("""
            QFrame#calPanel { background:white; border:1px solid #E3E0D6; border-radius:16px; }
        """)
        self.setObjectName("calPanel")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)

        head = QHBoxLayout()
        title = QLabel("Calendar")
        title.setStyleSheet("font-size:15px; font-weight:600;")
        head.addWidget(title)
        head.addStretch()

        self.month_btn = QPushButton("Month")
        self.week_btn = QPushButton("Week")
        for b in (self.month_btn, self.week_btn):
            b.setCheckable(True)
            b.setFixedHeight(26)
            b.setStyleSheet("""
                QPushButton { border:1px solid #E3E0D6; padding:2px 12px; }
                QPushButton:checked { background:#1E2420; color:white; }
            """)
        self.month_btn.setChecked(True)
        self.month_btn.clicked.connect(lambda: self._set_view(0))
        self.week_btn.clicked.connect(lambda: self._set_view(1))
        head.addWidget(self.month_btn)
        head.addWidget(self.week_btn)
        outer.addLayout(head)

        self.stack = QStackedWidget()
        self.month_view = MonthCalendar(controller)
        self.week_view = WeekView(controller)
        self.stack.addWidget(self.month_view)
        self.stack.addWidget(self.week_view)
        outer.addWidget(self.stack)

    def _set_view(self, index):
        self.month_btn.setChecked(index == 0)
        self.week_btn.setChecked(index == 1)
        self.stack.setCurrentIndex(index)

    def refresh(self):
        self.month_view.refresh()
        self.week_view.refresh()
