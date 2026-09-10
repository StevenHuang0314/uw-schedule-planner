from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import courses, schedule

app = FastAPI(
    title="UW-Madison Schedule Planner API",
    description="Suggests conflict-free, preference-ranked class schedules from real UW-Madison course data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed frontend origin before sharing widely
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(schedule.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
