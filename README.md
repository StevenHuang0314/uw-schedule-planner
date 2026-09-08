# UW-Madison Schedule Planner

A tool for UW-Madison students: give it a list of courses and it'll suggest
conflict-free class schedules, built from real, current section data instead
of a spreadsheet you build by hand every enrollment period.

## Status

Early days. So far:

- Real Fall 2026 course/section data (743 courses, 4,631 sections across 10
  subjects: COMP SCI, MATH, STAT, E C E, PHYSICS, ECON, ENGL, PSYCH, CHEM,
  COMM ARTS), pulled from UW-Madison's own public Course Search & Enroll API.
- A minimal FastAPI backend that loads that data into memory and serves
  course search over HTTP.

Not built yet: the actual scheduling/conflict logic, and a frontend. That's
next.

## How the data was collected

UW's Course Search & Enroll site (`public.enroll.wisc.edu`) doesn't publish
API docs, but it's just a normal web app calling its own JSON API from the
browser — so I opened it with devtools' Network tab open and watched what it
called:

```
GET  /api/search/v1/terms
GET  /api/search/v1/subjects
POST /api/search/v1                                  (search courses by subject)
GET  /api/search/v1/enrollmentPackages/<term>/<subject>/<courseId>   (sections + meeting times)
```

`scripts/fetch_courses.py` implements this end to end — full contract
documented at the top of the file. `scripts/merge_raw.py` combines the
per-subject output into `data/courses.json`, which the backend loads at
startup.

## Running it

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dir app
```

Then try:

```bash
curl http://localhost:8000/api/health
curl "http://localhost:8000/api/courses/search?q=comp+sci"
```

## Refreshing/extending the dataset

```bash
cd scripts
pip install -r requirements.txt
python fetch_courses.py --list-subjects
python fetch_courses.py --subjects 266,600,932
python merge_raw.py
```
