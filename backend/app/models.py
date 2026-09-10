"""Pydantic schemas shared across the API.

These mirror the shape of data/courses.json (see scripts/merge_raw.py for how
that file is produced) plus the request/response contracts for the
/api/schedule endpoint.
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


# ---- API request/response models ----


class Preferences(BaseModel):
    earliest: Optional[str] = Field(default=None, description="HH:MM, e.g. '09:00'")
    latest: Optional[str] = Field(default=None, description="HH:MM, e.g. '18:00'")
    avoidDays: list[Day] = Field(default_factory=list)
    allowWaitlisted: bool = True
    minimizeGaps: bool = True
    maxResults: int = Field(default=5, ge=1, le=10)


class ScheduleRequest(BaseModel):
    courses: list[str] = Field(..., min_length=1, max_length=8, description="Course designations, e.g. ['COMP SCI 300', 'MATH 222']")
    preferences: Preferences = Field(default_factory=Preferences)


class ScheduledMeeting(BaseModel):
    designation: str
    title: str
    sectionType: str
    sectionNum: str
    instructor: Optional[str]
    days: list[Day]
    start: int
    end: int
    bldg: Optional[str]
    room: Optional[str]


class ScheduledCourse(BaseModel):
    designation: str
    title: str
    credits: int
    packageId: str
    status: PackageStatus
    seats: int
    waitlist: int
    sections: list[Section]
    isAsynchronous: bool


class ScheduleOption(BaseModel):
    courses: list[ScheduledCourse]
    meetings: list[ScheduledMeeting]
    totalCredits: int
    score: float
    gapMinutes: int
    daysWithClasses: int


class ScheduleResponse(BaseModel):
    requested: list[str]
    unresolved: list[str] = Field(default_factory=list, description="Requested course strings that did not match any course in the catalog")
    infeasibleCourses: list[str] = Field(default_factory=list, description="Courses matched but with no section satisfying the given preferences")
    schedules: list[ScheduleOption]
