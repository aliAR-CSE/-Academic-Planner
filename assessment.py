from datetime import date

class Assessment:

    def __init__(self, name: str, assessment_type: str, due_date: date, weight: float):
        self.name = name
        self.assessment_type = assessment_type
        self.due_date = due_date
        self.weight = weight
        self.grade_earned = None
        self.is_completed = False
        
    @property
    def weight(self):
        return self._weight
    
    @weight.setter
    def weight(self, value):
        if not (0 <= value <= 100):
            raise ValueError("weight must be between 0 and 100")
        self._weight = value
        
    @property
    def grade_earned(self):
        return self._grade_earned
    
    @grade_earned.setter
    def grade_earned(self, value):
        if value is not None and value < 0:
            raise ValueError("grade_earned cannot be negative")
        self._grade_earned = value

    def update(self, name=None, assessment_type=None, due_date=None, weight=None, grade_earned=None):
        """Updates the Assessment based on params"""
        if name is not None:
            self.name = name
        if assessment_type is not None:
            self.assessment_type = assessment_type
        if due_date is not None:
            self.due_date = due_date
        if weight is not None:
            self.weight = weight
        if grade_earned is not None:
            self.grade_earned = grade_earned

    def complete(self):
        """Marks the Assigment as completed"""
        self.is_completed = True

    def is_overdue(self):
        """Compares todays date and compares it to the due_date attribute 
        and returns True or Flase, the dates are formated as YYYY-MM-DD"""
        if self.is_completed is True:
            return False
        return date.today() > self.due_date # compares today's date as YYYY-MM-DD to a set due date
    
    def to_dict(self) -> dict:
        """Converts Assessment object to a dictionary 
        and changes the due_date to a string"""
        return {"name" : self.name, 
                    "assessment_type" : self.assessment_type, 
                    "due_date" : str(self.due_date), 
                    "weight" : self._weight, 
                    "grade_earned" : self._grade_earned, 
                    "is_completed" : self.is_completed}
        
    @classmethod
    def from_dict(cls, data: dict) -> "Assessment":
        """Builds an Assessment object from a dictionary
        (the inverse of to_dict)"""
        assessment = cls(
            data["name"],
            data["assessment_type"],
            date.fromisoformat(data["due_date"]),
            data["weight"],)
        assessment.grade_earned = data["grade_earned"]
        assessment.is_completed = data["is_completed"]
        return assessment
    
    def __repr__(self):
        return (f"Assessment(name={self.name!r}, assessment_type={self.assessment_type!r}, "
                f"weight={self._weight}, grade_earned={self._grade_earned}, "
                f"is_completed={self.is_completed})")