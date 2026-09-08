"""Pydantic schemas shared across the API.

These mirror the shape of data/courses.json (see scripts/merge_raw.py for how
that file is produced).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Day = Literal["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
PackageStatus = Literal["OPEN", "WAITLISTED", "CLOSED"]


class Meeting(BaseModel):
    days: list[Day]
    start: int  # minutes since midnight
    end: int  # minutes since midnight
    bldg: Optional[str] = None
    room: Optional[str] = None


class Section(BaseModel):
    type: str  # LEC, DIS, LAB, SEM, ...
    num: str
    instructor: Optional[str] = None
    meetings: list[Meeting] = Field(default_factory=list)


class Package(BaseModel):
    packageId: str
    status: PackageStatus
    seats: int
    waitlist: int
    sections: list[Section]

    @property
    def all_meetings(self) -> list[Meeting]:
        return [m for s in self.sections for m in s.meetings]

    @property
    def is_asynchronous(self) -> bool:
        return len(self.all_meetings) == 0


class Course(BaseModel):
    courseId: str
    designation: str  # e.g. "COMP SCI 300"
    subjectCode: str
    subjectShort: str
    catalogNumber: str
    title: str
    minCredits: int
    maxCredits: int
    packages: list[Package]


class Term(BaseModel):
    code: str
    name: str


class CourseCatalog(BaseModel):
    term: Term
    generatedAt: str
    courses: list[Course]
