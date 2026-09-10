from fastapi import APIRouter

from app.data_store import get_data_store
from app.models import ScheduleRequest, ScheduleResponse
from app.solver import filter_candidates, solve

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("", response_model=ScheduleResponse)
def build_schedules(req: ScheduleRequest) -> ScheduleResponse:
    store = get_data_store()

    unresolved: list[str] = []
    infeasible: list[str] = []
    courses_with_candidates = []

    for designation in req.courses:
        course = store.find(designation)
        if course is None:
            unresolved.append(designation)
            continue
        candidates = filter_candidates(course, req.preferences)
        if not candidates:
            infeasible.append(course.designation)
            continue
        courses_with_candidates.append((course, candidates))

    schedules = []
    if courses_with_candidates and not infeasible:
        schedules = solve(courses_with_candidates, req.preferences)

    return ScheduleResponse(
        requested=req.courses,
        unresolved=unresolved,
        infeasibleCourses=infeasible,
        schedules=schedules,
    )
