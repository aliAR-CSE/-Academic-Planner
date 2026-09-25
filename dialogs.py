from datetime import date

from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QPushButton,
                              QDialogButtonBox, QColorDialog, QHBoxLayout,
                              QDateEdit, QDoubleSpinBox, QComboBox, QLabel,
                              QMessageBox)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor

from course import DEFAULT_COLOR

SWATCHES = ["#2A6F6F", "#C9622F", "#4C5FD5", "#B08A18", "#A63D5C", "#4E8B3E"]
ASSESSMENT_TYPES = ["Assignment", "Quiz", "Test", "Exam", "Lab", "Project"]


class ColorPicker(QHBoxLayout):
    """A row of clickable swatches plus a '...' button for a custom color."""

    def __init__(self, initial=DEFAULT_COLOR):
        super().__init__()
        self.color = initial
        self._buttons = []
        for hex_color in SWATCHES:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setCheckable(True)
            btn.setStyleSheet(self._style(hex_color))
            btn.clicked.connect(lambda _, c=hex_color: self._pick(c))
            self._buttons.append((hex_color, btn))
            self.addWidget(btn)
        more = QPushButton("...")
        more.setFixedSize(28, 22)
        more.clicked.connect(self._pick_custom)
        self.addWidget(more)
        self._sync_checked()

    def _style(self, hex_color):
        return f"background:{hex_color}; border-radius:11px; border:1px solid #0002;"

    def _pick(self, hex_color):
        self.color = hex_color
        self._sync_checked()

    def _pick_custom(self):
        c = QColorDialog.getColor(QColor(self.color))
        if c.isValid():
            self.color = c.name()
            self._sync_checked()

    def _sync_checked(self):
        for hex_color, btn in self._buttons:
            btn.setChecked(hex_color.lower() == self.color.lower())


class CourseDialog(QDialog):
    """Add or edit a course's name and color."""

    def __init__(self, parent=None, name="", color=DEFAULT_COLOR):
        super().__init__(parent)
        self.setWindowTitle("Course")
        self.name_edit = QLineEdit(name)
        self.color_picker = ColorPicker(color)

        form = QFormLayout(self)
        form.addRow("Name", self.name_edit)
        form.addRow("Color", self.color_picker)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Missing name", "Please enter a course name.")
            return
        self.accept()

    def values(self):
        return self.name_edit.text().strip(), self.color_picker.color


class AssessmentDialog(QDialog):
    """Add or edit an assessment. Grade field is only shown/used once the
    assessment already exists (editing), since a brand-new one has no grade yet."""

    def __init__(self, parent=None, name="", assessment_type="Assignment",
                 due_date: date | None = None, weight: float = 10.0,
                 grade_earned: float | None = None, show_grade=False):
        super().__init__(parent)
        self.setWindowTitle("Assessment")

        self.name_edit = QLineEdit(name)
        self.type_combo = QComboBox()
        self.type_combo.addItems(ASSESSMENT_TYPES)
        self.type_combo.setEditable(True)
        if assessment_type:
            self.type_combo.setCurrentText(assessment_type)

        self.due_edit = QDateEdit()
        self.due_edit.setCalendarPopup(True)
        if due_date:
            self.due_edit.setDate(QDate(due_date.year, due_date.month, due_date.day))
        else:
            self.due_edit.setDate(QDate.currentDate())

        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0, 100)
        self.weight_spin.setSuffix(" %")
        self.weight_spin.setValue(weight)

        form = QFormLayout(self)
        form.addRow("Name", self.name_edit)
        form.addRow("Type", self.type_combo)
        form.addRow("Due date", self.due_edit)
        form.addRow("Weight", self.weight_spin)

        self.grade_spin = None
        if show_grade:
            self.grade_spin = QDoubleSpinBox()
            self.grade_spin.setRange(0, 200)  # allow bonus marks over 100
            self.grade_spin.setSuffix(" %")
            self.grade_spin.setSpecialValueText("Not graded")
            self.grade_spin.setValue(grade_earned if grade_earned is not None else 0)
            form.addRow("Grade earned", self.grade_spin)
            form.addRow(QLabel("Leave at 0 / \"Not graded\" if ungraded."))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Missing name", "Please enter an assessment name.")
            return
        self.accept()

    def values(self):
        grade = None
        if self.grade_spin is not None and self.grade_spin.value() > 0:
            grade = self.grade_spin.value()
        return {
            "name": self.name_edit.text().strip(),
            "assessment_type": self.type_combo.currentText().strip(),
            "due_date": self.due_edit.date().toPyDate(),
            "weight": self.weight_spin.value(),
            "grade_earned": grade,
        }
