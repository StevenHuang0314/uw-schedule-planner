"""Loads data/courses.json once at process startup and builds lookup indices.

Kept deliberately simple: the dataset is small enough (a few thousand
sections) to live entirely in memory, so there's no database to provision or
migrate for this project. See scripts/fetch_courses.py to regenerate the
dataset from UW-Madison's public Course Search & Enroll API.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Optional

from app.models import Course, CourseCatalog

DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "courses.json"
)


class DataStore:
    def __init__(self, path: str = DEFAULT_DATA_PATH):
        with open(path) as f:
            raw = json.load(f)
        self.catalog = CourseCatalog.model_validate(raw)
        self._by_designation: dict[str, Course] = {
            self._normalize(c.designation): c for c in self.catalog.courses
        }
        self._by_course_id: dict[str, Course] = {c.courseId: c for c in self.catalog.courses}

    @staticmethod
    def _normalize(designation: str) -> str:
        return " ".join(designation.upper().split())

    def find(self, designation: str) -> Optional[Course]:
        return self._by_designation.get(self._normalize(designation))

    def search(self, query: str, limit: int = 20) -> list[Course]:
        q = query.strip().upper()
        if not q:
            return []
        exact = [c for c in self.catalog.courses if c.designation.upper().startswith(q)]
        if len(exact) >= limit:
            return exact[:limit]
        fuzzy = [
            c
            for c in self.catalog.courses
            if q in c.title.upper() or q in c.subjectShort.upper()
        ]
        seen = {c.courseId for c in exact}
        combined = exact + [c for c in fuzzy if c.courseId not in seen]
        return combined[:limit]

    @property
    def courses(self) -> list[Course]:
        return self.catalog.courses


@lru_cache(maxsize=1)
def get_data_store() -> DataStore:
    return DataStore()
