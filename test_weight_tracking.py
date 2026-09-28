"""
Automated tests for weight tracking in the Coursework Planner app.
 
Covers Assessment weight validation/serialization, Course weighted-grade
math, and PlannerController persistence of weights via storage.py.
 
Run with:
    pytest test_weight_tracking.py -v
 
Only exercises the non-GUI layers (assessment.py, course.py, controller.py,
storage.py); PyQt5 is not required.
"""
import pytest
import json
from datetime import date, timedelta
 
from assessment import Assessment
from course import Course, DEFAULT_COLOR
from controller import PlannerController
 
 
TODAY = date.today()
 
 
def make_assessment(name="A1", weight=10.0, due_offset=7, grade=None,
                     assessment_type="Assignment"):
    a = Assessment(name, assessment_type, TODAY + timedelta(days=due_offset), weight)
    if grade is not None:
        a.grade_earned = grade
    return a
 
 
# ---------------------------------------------------------------------
# Assessment: weight validation
# ---------------------------------------------------------------------
 
class TestWeightValidation:
 
    @pytest.mark.parametrize("weight", [0, 0.0, 50, 33.3, 100, 100.0])
    def test_valid(self, weight):
        a = make_assessment(weight=weight)
        assert a.weight == weight
 
    @pytest.mark.parametrize("weight", [-0.01, -1, -100, 100.01, 101, 1000])
    def test_invalid_on_init(self, weight):
        with pytest.raises(ValueError):
            make_assessment(weight=weight)
 
    @pytest.mark.parametrize("weight", [-5, 150])
    def test_invalid_on_update(self, weight):
        a = make_assessment(weight=20)
        with pytest.raises(ValueError):
            a.update(weight=weight)
        assert a.weight == 20  # untouched after a failed update
 
    def test_update_none_keeps_weight(self):
        a = make_assessment(weight=25)
        a.update(name="renamed")  # weight kwarg omitted
        assert a.weight == 25
 
    def test_update_valid_changes_weight(self):
        a = make_assessment(weight=25)
        a.update(weight=40)
        assert a.weight == 40
 
 
# ---------------------------------------------------------------------
# Assessment: serialization keeps weight intact
# ---------------------------------------------------------------------
 
class TestWeightSerialization:
 
    @pytest.mark.parametrize("weight", [0, 12.5, 100])
    def test_to_dict(self, weight):
        a = make_assessment(weight=weight)
        assert a.to_dict()["weight"] == weight
 
    @pytest.mark.parametrize("weight", [0, 12.5, 100])
    def test_from_dict_round_trip(self, weight):
        a = make_assessment(weight=weight, grade=80)
        rebuilt = Assessment.from_dict(a.to_dict())
        assert rebuilt.weight == weight
 
    def test_from_dict_rejects_bad_weight(self):
        bad = {
            "name": "Bad",
            "assessment_type": "Quiz",
            "due_date": str(TODAY),
            "weight": 150,
            "grade_earned": None,
            "is_completed": False,
        }
        with pytest.raises(ValueError):
            Assessment.from_dict(bad)
 
    def test_json_round_trip(self):
        a = make_assessment(weight=17.5)
        blob = json.loads(json.dumps(a.to_dict()))
        rebuilt = Assessment.from_dict(blob)
        assert rebuilt.weight == 17.5
 
 
# ---------------------------------------------------------------------
# Course: weight-driven grade calculation
# ---------------------------------------------------------------------
 
class TestCourseGrade:
 
    def test_no_assessments(self):
        course = Course("Empty")
        assert course.get_grade() == 0
 
    def test_no_grades_yet(self):
        course = Course("Ungraded")
        course.add_assessment("A1", "Assignment", TODAY, 30)
        course.add_assessment("A2", "Quiz", TODAY, 70)
        assert course.get_grade() == 0
 
    def test_single_graded(self):
        course = Course("Solo")
        course.add_assessment("A1", "Assignment", TODAY, 40)
        course.assessments[0].grade_earned = 88
        assert course.get_grade() == pytest.approx(88)
 
    def test_weighted_average(self):
        course = Course("Two")
        course.add_assessment("A1", "Assignment", TODAY, 30)
        course.add_assessment("A2", "Test", TODAY, 70)
        course.assessments[0].grade_earned = 90   # 30% weight
        course.assessments[1].grade_earned = 70   # 70% weight
        expected = (90 * 30 + 70 * 70) / (30 + 70)
        assert course.get_grade() == pytest.approx(expected)
 
    def test_ungraded_excluded(self):
        course = Course("Mixed")
        course.add_assessment("A1", "Assignment", TODAY, 20)
        course.add_assessment("A2", "Quiz", TODAY, 30)
        course.add_assessment("A3", "Exam", TODAY, 50)
        course.assessments[0].grade_earned = 100  # A2, A3 stay ungraded
        assert course.get_grade() == pytest.approx(100)  # only A1's weight counts
 
    def test_weights_not_summing_to_100(self):
        # get_grade() normalizes by weight actually completed, so a
        # partial total (e.g. 60) must still average correctly.
        course = Course("Partial")
        course.add_assessment("A1", "Assignment", TODAY, 20)
        course.add_assessment("A2", "Quiz", TODAY, 40)
        course.assessments[0].grade_earned = 50
        course.assessments[1].grade_earned = 80
        expected = (50 * 20 + 80 * 40) / (20 + 40)
        assert course.get_grade() == pytest.approx(expected)
 
    def test_zero_weight_ignored(self):
        course = Course("ZeroWeight")
        course.add_assessment("Bonus", "Extra", TODAY, 0)
        course.add_assessment("Main", "Exam", TODAY, 100)
        course.assessments[0].grade_earned = 0
        course.assessments[1].grade_earned = 75
        assert course.get_grade() == pytest.approx(75)
 
 
# ---------------------------------------------------------------------
# Course: weight list stays consistent through add/remove
# ---------------------------------------------------------------------
 
class TestCourseWeightBookkeeping:
 
    def test_add_stores_weight(self):
        course = Course("C1")
        a = course.add_assessment("A1", "Assignment", TODAY, 15)
        assert a.weight == 15
        assert course.assessments[-1].weight == 15
 
    def test_add_rejects_bad_weight(self):
        course = Course("C1")
        with pytest.raises(ValueError):
            course.add_assessment("Bad", "Assignment", TODAY, 500)
        assert course.assessments == []
 
    def test_remove_drops_weight(self):
        course = Course("C1")
        course.add_assessment("A1", "Assignment", TODAY, 40)
        course.add_assessment("A2", "Quiz", TODAY, 60)
        course.assessments[0].grade_earned = 100
        course.assessments[1].grade_earned = 0
        assert course.remove_assessment("A2") is True
        assert course.get_grade() == pytest.approx(100)  # only A1 remains
 
    def test_total_weight(self):
        course = Course("C1")
        course.add_assessment("A1", "Assignment", TODAY, 25)
        course.add_assessment("A2", "Quiz", TODAY, 35)
        assert sum(a.weight for a in course.assessments) == 60
 
 
# ---------------------------------------------------------------------
# PlannerController: weight tracking survives add/update/remove +
# persistence to disk (JSON) and reload.
# ---------------------------------------------------------------------
 
@pytest.fixture
def controller(tmp_path):
    file_path = tmp_path / "data.json"
    return PlannerController(file_path=str(file_path))
 
 
class TestControllerWeights:
 
    def test_add_persists(self, controller):
        course = controller.add_course("SYSC4001", DEFAULT_COLOR)
        controller.add_assessment(course.id, "A01", "Assignment", TODAY, 12.5)
 
        reloaded = PlannerController(file_path=controller.file_path)
        assert reloaded.get_course(course.id).assessments[0].weight == 12.5
 
    def test_add_invalid_does_not_save(self, controller):
        course = controller.add_course("SYSC4001", DEFAULT_COLOR)
        with pytest.raises(ValueError):
            controller.add_assessment(course.id, "Bad", "Assignment", TODAY, -5)
        assert controller.get_course(course.id).assessments == []
 
    def test_update_persists(self, controller):
        course = controller.add_course("SYSC4001", DEFAULT_COLOR)
        controller.add_assessment(course.id, "A01", "Assignment", TODAY, 10)
        controller.update_assessment(course.id, "A01", weight=45)
 
        reloaded = PlannerController(file_path=controller.file_path)
        assert reloaded.get_course(course.id).assessments[0].weight == 45
 
    def test_update_invalid_raises(self, controller):
        course = controller.add_course("SYSC4001", DEFAULT_COLOR)
        controller.add_assessment(course.id, "A01", "Assignment", TODAY, 10)
        with pytest.raises(ValueError):
            controller.update_assessment(course.id, "A01", weight=999)
        assert controller.get_course(course.id).assessments[0].weight == 10
 
    def test_remove_updates_grade_base(self, controller):
        course = controller.add_course("SYSC4001", DEFAULT_COLOR)
        controller.add_assessment(course.id, "A01", "Assignment", TODAY, 40)
        controller.add_assessment(course.id, "A02", "Quiz", TODAY, 60)
        controller.set_grade(course.id, "A01", 100)
        controller.set_grade(course.id, "A02", 0)
 
        controller.remove_assessment(course.id, "A02")
 
        reloaded = PlannerController(file_path=controller.file_path)
        reloaded_course = reloaded.get_course(course.id)
        assert len(reloaded_course.assessments) == 1
        assert reloaded_course.get_grade() == pytest.approx(100)
 
    def test_independent_courses(self, controller):
        c1 = controller.add_course("SYSC4001", "#2A6F6F")
        c2 = controller.add_course("ELEC3509", "#C9622F")
        controller.add_assessment(c1.id, "A01", "Assignment", TODAY, 30)
        controller.add_assessment(c2.id, "L1", "Lab", TODAY, 90)
 
        reloaded = PlannerController(file_path=controller.file_path)
        w1 = reloaded.get_course(c1.id).assessments[0].weight
        w2 = reloaded.get_course(c2.id).assessments[0].weight
        assert (w1, w2) == (30, 90)
 
 
# ---------------------------------------------------------------------
# storage.py: direct JSON round-trip of weights (course-level)
# ---------------------------------------------------------------------
 
class TestStorageWeights:
 
    def test_save_load_round_trip(self, tmp_path):
        from storage import save_courses, load_courses
 
        file_path = str(tmp_path / "data.json")
        course = Course("SYSC4001")
        course.add_assessment("A01", "Assignment", TODAY, 10)
        course.add_assessment("A02", "Test", TODAY, 30)
        course.add_assessment("Final", "Exam", TODAY, 60)
 
        save_courses(file_path, [course])
        reloaded = load_courses(file_path)
 
        assert len(reloaded) == 1
        assert sorted(a.weight for a in reloaded[0].assessments) == [10, 30, 60]
 
    def test_json_is_well_formed(self, tmp_path):
        from storage import save_courses
 
        file_path = str(tmp_path / "data.json")
        course = Course("SYSC4001")
        course.add_assessment("A01", "Assignment", TODAY, 22.5)
        save_courses(file_path, [course])
 
        with open(file_path, encoding="utf-8") as f:
            raw = json.load(f)
        assert raw[0]["assessments"][0]["weight"] == 22.5
