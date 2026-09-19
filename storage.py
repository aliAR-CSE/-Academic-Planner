import json
from course import Course
import os

FILE_NAME = "data.JSON"


def save_courses(file_path: str, courses: list[Course]):
    """Converts a list of Course objects Into a list of dictionaries, then saves it to a JSON file"""
    data = []
    for course in courses:
        data.append(course.to_dict())
    with open(file_path, "w", encoding = 'utf-8') as file:
        json.dump(data, file, ensure_ascii = False, indent = 4)

def load_courses(file_path: str) -> list[Course]:
    """Converts JSON into a list of Course object"""
    if not os.path.exists(file_path):
        with open(file_path, "x") as file:
            json.dump([], file, ensure_ascii=False, indent=4)
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        data_list = json.load(file)

    return [Course.from_dict(course_data) for course_data in data_list]