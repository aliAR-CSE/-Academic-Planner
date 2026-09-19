from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QScrollArea, QPushButton, QLabel, QDesktopWidget,
                              QMessageBox)
from PyQt5.QtCore import Qt

from controller import PlannerController
from course_card import CourseCard
from calendar_view import CalendarPanel
from dialogs import CourseDialog, AssessmentDialog

BG_STYLE = "background: #F6F5F1;"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coursework Planner")
        self.controller = PlannerController()
        self.cards = {}  # course_id -> CourseCard

        self.resize(1180, 720)
        self.center()
        self._init_ui()
        self._rebuild_courses()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _init_ui(self):
        central = QWidget()
        central.setStyleSheet(BG_STYLE)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)

        title = QLabel("Coursework Planner")
        title.setStyleSheet("font-size:22px; font-weight:700; color:#1E2420;")
        subtitle = QLabel("Track courses, assessments, and deadlines in one place.")
        subtitle.setStyleSheet("color:#5C6660; margin-bottom:8px;")
        root.addWidget(title)
        root.addWidget(subtitle)

        columns = QHBoxLayout()
        columns.setSpacing(20)
        root.addLayout(columns)

        # ---- left column: courses ----
        left = QVBoxLayout()
        head = QHBoxLayout()
        courses_label = QLabel("Courses")
        courses_label.setStyleSheet("font-size:15px; font-weight:600;")
        add_course_btn = QPushButton("+ Add course")
        add_course_btn.setStyleSheet(
            "background:#1E2420; color:white; border-radius:14px; padding:6px 14px;"
        )
        add_course_btn.clicked.connect(self.on_add_course)
        head.addWidget(courses_label)
        head.addStretch()
        head.addWidget(add_course_btn)
        left.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        self.course_list_widget = QWidget()
        self.course_list_layout = QVBoxLayout(self.course_list_widget)
        self.course_list_layout.setSpacing(10)
        self.course_list_layout.addStretch()
        scroll.setWidget(self.course_list_widget)
        left.addWidget(scroll)

        left_wrap = QWidget()
        left_wrap.setLayout(left)
        columns.addWidget(left_wrap, 3)

        # ---- right column: calendar ----
        self.calendar_panel = CalendarPanel(self.controller)
        columns.addWidget(self.calendar_panel, 2)

    # ---------------------------------------------------------------
    def _rebuild_courses(self):
        # clear existing cards
        for card in self.cards.values():
            card.setParent(None)
        self.cards.clear()

        for i in range(self.course_list_layout.count() - 1, -1, -1):
            item = self.course_list_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        for course in self.controller.courses:
            card = CourseCard(course)
            card.add_assessment_requested.connect(self.on_add_assessment)
            card.edit_course_requested.connect(self.on_edit_course)
            card.edit_assessment_requested.connect(self.on_edit_assessment)
            card.toggle_assessment_requested.connect(self.on_toggle_assessment)
            self.course_list_layout.insertWidget(self.course_list_layout.count() - 1, card)
            self.cards[course.id] = card

        self.calendar_panel.refresh()

    def _refresh_course(self, course_id):
        course = self.controller.get_course(course_id)
        card = self.cards.get(course_id)
        if course and card:
            card.refresh(course)
        self.calendar_panel.refresh()

    # ---------------------------------------------------------------
    # course actions
    def on_add_course(self):
        dlg = CourseDialog(self)
        if dlg.exec_():
            name, color = dlg.values()
            self.controller.add_course(name, color)
            self._rebuild_courses()

    def on_edit_course(self, course_id):
        course = self.controller.get_course(course_id)
        if not course:
            return
        dlg = CourseDialog(self, name=course.name, color=course.color)
        delete_btn = QPushButton("Delete course")
        delete_btn.setStyleSheet("color:#B3261E;")
        dlg.layout().addRow(delete_btn)

        def do_delete():
            confirm = QMessageBox.question(
                self, "Delete course",
                f"Delete \"{course.name}\" and all of its assessments?"
            )
            if confirm == QMessageBox.Yes:
                self.controller.remove_course(course_id)
                dlg.reject()
                self._rebuild_courses()

        delete_btn.clicked.connect(do_delete)

        if dlg.exec_():
            name, color = dlg.values()
            self.controller.rename_course(course_id, name)
            self.controller.set_course_color(course_id, color)
            self._refresh_course(course_id)

    # assessment actions
    def on_add_assessment(self, course_id):
        dlg = AssessmentDialog(self, show_grade=False)
        if dlg.exec_():
            v = dlg.values()
            self.controller.add_assessment(
                course_id, v["name"], v["assessment_type"], v["due_date"], v["weight"]
            )
            self._refresh_course(course_id)

    def on_edit_assessment(self, course_id, name):
        course = self.controller.get_course(course_id)
        assessment = next((a for a in course.assessments if a.name == name), None)
        if not assessment:
            return
        dlg = AssessmentDialog(
            self, name=assessment.name, assessment_type=assessment.assessment_type,
            due_date=assessment.due_date, weight=assessment.weight,
            grade_earned=assessment.grade_earned, show_grade=True,
        )
        delete_btn = QPushButton("Delete assessment")
        delete_btn.setStyleSheet("color:#B3261E;")
        dlg.layout().addRow(delete_btn)

        def do_delete():
            self.controller.remove_assessment(course_id, name)
            dlg.reject()
            self._refresh_course(course_id)

        delete_btn.clicked.connect(do_delete)

        if dlg.exec_():
            v = dlg.values()
            self.controller.update_assessment(
                course_id, name,
                name=v["name"], assessment_type=v["assessment_type"],
                due_date=v["due_date"], weight=v["weight"],
            )
            if v["grade_earned"] is not None:
                self.controller.set_grade(course_id, v["name"], v["grade_earned"])
            self._refresh_course(course_id)

    def on_toggle_assessment(self, course_id, name):
        self.controller.toggle_assessment_done(course_id, name)
        self._refresh_course(course_id)
