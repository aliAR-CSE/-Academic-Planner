from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QToolButton, QCheckBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from ring_widget import CompletionRing

CARD_QSS = """
QFrame#card {{
    background: white;
    border: 1px solid #E3E0D6;
    border-radius: 16px;
}}
QFrame#header {{
    border: none;
}}
QLabel#courseName {{
    font-size: 14px;
    font-weight: 600;
    color: #1E2420;
}}
QLabel#courseName:hover {{
    text-decoration: underline;
}}
QLabel#gradeLabel {{
    color: #5C6660;
    font-size: 12px;
}}
QToolButton#addBtn, QToolButton#caretBtn {{
    border: 1px solid #E3E0D6;
    border-radius: 13px;
    background: transparent;
    color: #5C6660;
}}
QToolButton#addBtn:hover, QToolButton#caretBtn:hover {{
    border-color: {accent};
    color: {accent};
}}
QFrame#swatch {{
    background: {accent};
    border-radius: 5px;
}}
"""

ROW_QSS = """
QLabel#aName {{ font-size: 13px; }}
QLabel#aDue, QLabel#aWeight {{ color: #5C6660; font-size: 12px; }}
QLabel#aName[done="true"] {{ color: #5C6660; text-decoration: line-through; }}
QPushButton#doneBtn {{
    border-radius: 10px;
    border: 1.5px solid {accent};
    background: transparent;
    color: {accent};
    font-size: 11px;
}}
QPushButton#doneBtn[done="true"] {{
    background: {accent};
    color: white;
}}
"""


class AssessmentRow(QFrame):
    toggled = pyqtSignal(str)     # assessment name
    edit_requested = pyqtSignal(str)

    def __init__(self, assessment, accent: str, parent=None):
        super().__init__(parent)
        self.assessment = assessment
        self.setStyleSheet(ROW_QSS.format(accent=accent))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 6, 10, 6)

        self.done_btn = QPushButton("\u2713" if assessment.is_completed else "")
        self.done_btn.setObjectName("doneBtn")
        self.done_btn.setProperty("done", assessment.is_completed)
        self.done_btn.setFixedSize(20, 20)
        self.done_btn.clicked.connect(lambda: self.toggled.emit(assessment.name))
        layout.addWidget(self.done_btn)

        self.name_label = QLabel(assessment.name)
        self.name_label.setObjectName("aName")
        self.name_label.setProperty("done", assessment.is_completed)
        layout.addWidget(self.name_label, 2)

        due_label = QLabel(assessment.due_date.strftime("%b %-d"))
        due_label.setObjectName("aDue")
        layout.addWidget(due_label, 1)

        weight_label = QLabel(f"{assessment.weight:g}%")
        weight_label.setObjectName("aWeight")
        weight_label.setAlignment(Qt.AlignRight)
        layout.addWidget(weight_label)

        edit_btn = QPushButton("\u270e")
        edit_btn.setFixedWidth(24)
        edit_btn.setFlat(True)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(assessment.name))
        layout.addWidget(edit_btn)


class CourseCard(QFrame):
    """One collapsible course card: header row (add/name/ring/grade/expand)
    plus a list of AssessmentRow children."""

    add_assessment_requested = pyqtSignal(str)          # course_id
    edit_course_requested = pyqtSignal(str)              # course_id
    edit_assessment_requested = pyqtSignal(str, str)     # course_id, assessment name
    toggle_assessment_requested = pyqtSignal(str, str)   # course_id, assessment name
    show_hidden_changed = pyqtSignal(str, bool)          # course_id, checked

    def __init__(self, course, show_hidden: bool = False, expanded: bool = False, parent=None):
        super().__init__(parent)
        self.course = course
        self.show_hidden = show_hidden
        self.expanded = expanded
        self.setObjectName("card")
        self.setStyleSheet(CARD_QSS.format(accent=course.color))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(14, 10, 14, 10)

        add_btn = QToolButton()
        add_btn.setObjectName("addBtn")
        add_btn.setText("+")
        add_btn.setFixedSize(26, 26)
        add_btn.setToolTip("Add assessment")
        add_btn.clicked.connect(lambda: self.add_assessment_requested.emit(self.course.id))
        h.addWidget(add_btn)

        swatch = QFrame()
        swatch.setObjectName("swatch")
        swatch.setFixedSize(10, 10)
        h.addWidget(swatch)

        name_label = QLabel(course.name)
        name_label.setObjectName("courseName")
        name_label.setCursor(Qt.PointingHandCursor)
        name_label.mousePressEvent = lambda e: self.edit_course_requested.emit(self.course.id)
        h.addWidget(name_label, 1)

        self.ring = CompletionRing(course.get_completion_rate(), course.color)
        h.addWidget(self.ring)

        self.grade_label = QLabel(f"{course.get_grade():.0f}%")
        self.grade_label.setObjectName("gradeLabel")
        self.grade_label.setFixedWidth(36)
        self.grade_label.setAlignment(Qt.AlignRight)
        h.addWidget(self.grade_label)

        self.caret_btn = QToolButton()
        self.caret_btn.setObjectName("caretBtn")
        self.caret_btn.setText("\u25b8")
        self.caret_btn.setFixedSize(22, 22)
        self.caret_btn.clicked.connect(self.toggle_expanded)
        h.addWidget(self.caret_btn)

        header.mousePressEvent = lambda e: self.toggle_expanded()
        outer.addWidget(header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        outer.addWidget(self.body)

        self._populate_rows()
        self.body.setVisible(self.expanded)
        self._update_caret()

    def _populate_rows(self):
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        visible = self.course.sorted_assessments(include_completed=self.show_hidden)
        if not visible:
            empty = QLabel("No assessments to show" if self.course.assessments else "No assessments yet")
            empty.setStyleSheet("color:#5C6660; font-size:12px; padding: 8px 14px 8px 28px;")
            self.body_layout.addWidget(empty)
        for assessment in visible:
            row = AssessmentRow(assessment, self.course.color)
            row.toggled.connect(lambda n: self.toggle_assessment_requested.emit(self.course.id, n))
            row.edit_requested.connect(lambda n: self.edit_assessment_requested.emit(self.course.id, n))
            self.body_layout.addWidget(row)

        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(14, 6, 14, 8)
        cb = QCheckBox("Show completed assessments")
        cb.setChecked(self.show_hidden)
        cb.setStyleSheet("color:#5C6660; font-size:11.5px;")
        cb.stateChanged.connect(lambda state: self._on_show_hidden(state))
        toggle_row.addWidget(cb)
        toggle_row.addStretch()
        wrap = QWidget()
        wrap.setLayout(toggle_row)
        self.body_layout.addWidget(wrap)

    def _on_show_hidden(self, state):
        self.show_hidden = state == Qt.Checked
        self._populate_rows()
        self.show_hidden_changed.emit(self.course.id, self.show_hidden)

    def toggle_expanded(self):
        self.expanded = not self.expanded
        self.body.setVisible(self.expanded)
        self._update_caret()

    def _update_caret(self):
        self.caret_btn.setText("\u25be" if self.expanded else "\u25b8")

    def refresh(self, course):
        """Re-render this card in place after the underlying course changed."""
        self.course = course
        self.setStyleSheet(CARD_QSS.format(accent=course.color))
        self.ring.set_value(course.get_completion_rate(), course.color)
        self.grade_label.setText(f"{course.get_grade():.0f}%")
        self._populate_rows()
