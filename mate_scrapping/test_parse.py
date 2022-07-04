from mate_scrapping.parse import get_all_courses, CourseType


FOR_SURE_THIS_COURSES = [
    "QA",
    "Java",
    "Python",
]  # frontend is web development sometimes


def test_get_all_courses():
    all_courses = get_all_courses()

    for course_type in CourseType:
        course_names = [
            course.name for course in all_courses if course.type == course_type
        ]

        for course in FOR_SURE_THIS_COURSES:
            assert any(
                course.lower() in course_name.lower() for course_name in course_names
            ), f"Course '{course}' have not been parsed for '{course_type}'"
