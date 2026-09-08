from typing import Optional

from fastapi import APIRouter, Query

from app.data_store import get_data_store
from app.models import Course, Term

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/term", response_model=Term)
def get_term() -> Term:
    return get_data_store().catalog.term


@router.get("/search", response_model=list[Course])
def search_courses(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50)) -> list[Course]:
    return get_data_store().search(q, limit=limit)


@router.get("/{designation}", response_model=Optional[Course])
def get_course(designation: str) -> Optional[Course]:
    return get_data_store().find(designation)
