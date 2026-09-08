from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import courses

app = FastAPI(
    title="UW-Madison Schedule Planner API",
    description="Real UW-Madison course data, served from an in-memory index.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before sharing this beyond local dev
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
