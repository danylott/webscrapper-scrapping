from dataclasses import dataclass
from enum import Enum
from typing import List

import requests
from bs4 import BeautifulSoup

HOME_URL = "https://mate.academy/"


class CourseType(Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"


@dataclass
class Course:
    name: str
    short_description: str
    type: CourseType


def parse_single_course(course_soup: BeautifulSoup, course_type: CourseType) -> Course:
    return Course(
        name=course_soup.select_one("a > span").text,
        short_description=course_soup.select_one("div > p").text,
        type=course_type
    )


def parse_section_courses(section_soup: BeautifulSoup, course_type: CourseType) -> List[Course]:
    return [
        parse_single_course(course_soup, course_type)
        for course_soup in section_soup.select("[class^=CourseCard_cardContainer]")
    ]


def get_all_courses() -> List[Course]:
    page = requests.get(HOME_URL).content
    soup = BeautifulSoup(page, "html.parser")

    return [
        *parse_section_courses(soup.select_one("#full-time > .large-6"), CourseType.FULL_TIME),
        *parse_section_courses(soup.select_one("#part-time > .large-6"), CourseType.PART_TIME),
    ]


def main():
    print(get_all_courses())


if __name__ == '__main__':
    main()
