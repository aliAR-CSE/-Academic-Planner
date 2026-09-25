from datetime import date

from course import Course
from storage import load_courses, save_courses, FILE_NAME


class PlannerController:
    """Owns the in-memory list of courses and is the only object that
    talks to storage.py. The GUI should never touch Course/Assessment
    objects' internals directly or call storage.py itself -- it goes
    through here so the two layers stay decoupled."""

    def __init__(self, file_path: str = FILE_NAME):
        self.file_path = file_path
        self.courses: list[Course] = load_courses(file_path)

    # ---- persistence ----
    def save(self):
        save_courses(self.file_path, self.courses)

    # ---- course-level operations ----
    def add_course(self, name: str, color: str) -> Course:
        course = Course(name, color=color)
        self.courses.append(course)
        self.save()
        return course

    def remove_course(self, course_id: str) -> bool:
        course = self.get_course(course_id)
        if course is None:
            return False
        self.courses.remove(course)
        self.save()
        return True

    def get_course(self, course_id: str) -> Course | None:
        for course in self.courses:
            if course.id == course_id:
                return course
        return None

    def rename_course(self, course_id: str, name: str):
        course = self.get_course(course_id)
        if course:
            course.update_name(name)
            self.save()

    def set_course_color(self, course_id: str, color: str):
        course = self.get_course(course_id)
        if course:
            course.set_color(color)
            self.save()

    # ---- assessment-level operations ----
    def add_assessment(self, course_id: str, name: str, assessment_type: str,
                        due_date: date, weight: float):
        course = self.get_course(course_id)
        if course is None:
            return None
        assessment = course.add_assessment(name, assessment_type, due_date, weight)
        self.save()
        return assessment

    def update_assessment(self, course_id: str, old_name: str, **kwargs):
        course = self.get_course(course_id)
        if course is None:
            return False
        for assessment in course.assessments:
            if assessment.name == old_name:
                assessment.update(**kwargs)
                self.save()
                return True
        return False

    def remove_assessment(self, course_id: str, name: str) -> bool:
        course = self.get_course(course_id)
        if course is None:
            return False
        result = course.remove_assessment(name)
        if result:
            self.save()
        return result

    def toggle_assessment_done(self, course_id: str, name: str):
        course = self.get_course(course_id)
        if course is None:
            return
        for assessment in course.assessments:
            if assessment.name == name:
                if assessment.is_completed:
                    assessment.reopen()
                else:
                    assessment.complete()
                self.save()
                return

    def set_grade(self, course_id: str, name: str, grade: float):
        course = self.get_course(course_id)
        if course is None:
            return
        for assessment in course.assessments:
            if assessment.name == name:
                assessment.grade_earned = grade
                self.save()
                return

    # ---- aggregate views for the calendar ----
    def all_assessments_with_course(self):
        """Yields (course, assessment) pairs across every course, for
        anything (like the calendar) that needs a flat view."""
        for course in self.courses:
            for assessment in course.assessments:
                yield course, assessment
