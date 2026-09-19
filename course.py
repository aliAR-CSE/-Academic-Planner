import uuid
from datetime import date
from assessment import Assessment

DEFAULT_COLOR = "#2A6F6F"

class Course:

    def __init__(self, name: str, color: str = DEFAULT_COLOR, course_id: str | None = None):
        self.id = course_id or uuid.uuid4().hex
        self.name = name
        self.color = color
        self.assessments = []   # creates an empty list of assessments

    def update_name(self, name = None):
        """Changes the name of a course"""
        if name is not None:
            self.name = name

    def set_color(self, color: str):
        """Changes the display color of a course"""
        self.color = color
        
    def add_assessment(self, name: str, assessment_type: str, due_date: date, weight: float) -> Assessment:
        """Creates and adds a new lab/test to an existing list of assessments"""
        new_assessment = Assessment(name, assessment_type, due_date, weight)
        self.assessments.append(new_assessment)
        return new_assessment

    def remove_assessment(self, name: str) -> bool:
        """Searches and removes a lab/test from the course"""
        for assessment in self.assessments:
            if assessment.name == name:
                self.assessments.remove(assessment)
                return True
        return False
    
    def sorted_assessments(self, include_completed: bool = True) -> list:
        """Returns assessments ordered soonest-due first, optionally excluding ones already marked completed"""
        pool = self.assessments if include_completed else [a for a in self.assessments if not a.is_completed]
        return sorted(pool, key=lambda a: a.due_date)
    
    def get_grade(self) -> float:
        """Calculates the grade earned for the course.
        Returns 0 if no assessments are completed"""
        points_earned = 0
        weight_completed = 0
        for assessment in self.assessments:
            if assessment.grade_earned is not None:
                points_earned += assessment.grade_earned * assessment.weight
                weight_completed += assessment.weight
        if weight_completed == 0:
            return 0
        return points_earned / weight_completed
    
    def get_completion_rate(self) -> float:
        """Returns the % of assessments marked completed"""
        completed_count = sum(1 for a in self.assessments if a.is_completed)
        total = len(self.assessments)
        if total == 0:
            return 0
        return 100 * completed_count / total
    
    def to_dict(self) -> dict:
        """Converts a Course object to a dictionary, including all of its assessments"""
        return {"name": self.name, "assessments": [a.to_dict() for a in self.assessments],}
    
    @classmethod
    def from_dict(cls, data: dict) -> "Course":
        """Builds a Course object (and its Assessments) from a dictionary
        (the inverse of to_dict)"""
        course = cls(data["name"])
        course.assessments = [Assessment.from_dict(a) for a in data["assessments"]]
        return course

    def __repr__(self):
        return f"Course(name={self.name!r}, assessments={len(self.assessments)})"