#!/usr/bin/env python3
"""
Fetch real course/section data from UW-Madison's public Course Search &
Enroll API and write per-subject JSON files to data/raw/, ready for
scripts/merge_raw.py to combine into data/courses.json.

This talks to https://public.enroll.wisc.edu/api/search/v1/*, the same
(undocumented, but public and unauthenticated) API the official Course
Search & Enroll website itself uses. It was reverse-engineered by opening
https://public.enroll.wisc.edu/search in a browser with devtools' Network
tab open and watching the requests fire:

  GET  /api/search/v1/terms
        -> [{"termCode": "1272", "shortDescription": "2026 Fall", ...}, ...]

  GET  /api/search/v1/subjects
        -> {"<termCode>": [{"subjectCode": "266",
                             "formalDescription": "COMPUTER SCIENCES"}, ...]}

  POST /api/search/v1
        body: {"selectedTerm": "<termCode>", "queryString": "",
               "filters": [{"term": {"subject.subjectCode": "<code>"}}],
               "sortOrder": "CATALOG_NUMBER", "page": <n>, "pageSize": 100}
        -> {"found": <int>, "hits": [<course>, ...]}
        (page through until len(collected) >= found)

  GET  /api/search/v1/enrollmentPackages/<termCode>/<subjectCode>/<courseId>
        -> [<package>, ...]   (one entry per lecture/discussion "package";
                                courseId comes from the search hit, NOT the
                                catalog number)

Usage:
    python scripts/fetch_courses.py --subjects 266,600,932 --term 1272
    python scripts/fetch_courses.py --subjects 266,600,932   # auto-picks the
                                                              # current term
    python scripts/fetch_courses.py --list-subjects          # see all codes

Be a good citizen: this script rate-limits itself (default 8 concurrent
requests, small per-request delay) and only hits a public, read-only,
unauthenticated endpoint that the course search website itself calls from
every visitor's browser. Don't crank concurrency way up.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import time

import requests

BASE = "https://public.enroll.wisc.edu/api/search/v1"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def get_current_term() -> str:
    terms = requests.get(f"{BASE}/terms", timeout=15).json()
    # terms are returned with the soonest/current term(s) available for
    # search; pick the first that isn't marked as a past term.
    for t in terms:
        if not t.get("pastTerm"):
            return t["termCode"]
    return terms[0]["termCode"]


def get_subjects(term: str) -> dict[str, str]:
    """Returns {formalDescription: subjectCode} for the given term."""
    data = requests.get(f"{BASE}/subjects", timeout=15).json()
    entries = data.get(term) or data.get("0000") or []
    return {e["formalDescription"]: e["subjectCode"] for e in entries}


def search_all_courses(term: str, subject_code: str, page_size: int = 100) -> list[dict]:
    collected: list[dict] = []
    page = 1
    while True:
        body = {
            "selectedTerm": term,
            "queryString": "",
            "filters": [{"term": {"subject.subjectCode": subject_code}}],
            "sortOrder": "CATALOG_NUMBER",
            "page": page,
            "pageSize": page_size,
        }
        resp = requests.post(BASE, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        collected.extend(data.get("hits", []))
        if len(collected) >= data.get("found", 0) or not data.get("hits"):
            break
        page += 1
    return collected


def fetch_enrollment_packages(term: str, subject_code: str, course_id: str) -> list[dict]:
    url = f"{BASE}/enrollmentPackages/{term}/{subject_code}/{course_id}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def minify_package(course_id: str, pkg: dict) -> dict:
    status = pkg.get("packageEnrollmentStatus") or {}
    sections = []
    for s in pkg.get("sections", []):
        instr = s.get("instructor")
        instr_name = None
        if instr and instr.get("name"):
            instr_name = f"{instr['name'].get('first') or ''} {instr['name'].get('last') or ''}".strip()
        meetings = []
        for m in s.get("classMeetings", []):
            if m.get("meetingType") != "CLASS" or not m.get("meetingDaysList"):
                continue
            building = m.get("building") or {}
            meetings.append(
                {
                    "days": [d[:3] for d in m["meetingDaysList"]],
                    "start": round(m["meetingTimeStart"] / 60000),
                    "end": round(m["meetingTimeEnd"] / 60000),
                    "bldg": building.get("buildingName"),
                    "room": s.get("room") or m.get("room"),
                }
            )
        sections.append(
            {"type": s.get("type"), "num": s.get("sectionNumber"), "instr": instr_name, "meetings": meetings}
        )
    return {
        "courseId": course_id,
        "pkgId": pkg.get("id"),
        "status": status.get("status"),
        "seats": status.get("availableSeats"),
        "waitlist": status.get("waitlistTotal"),
        "sections": sections,
    }


def fetch_subject(term: str, subject_code: str, concurrency: int = 8) -> dict:
    courses = search_all_courses(term, subject_code)
    courses = [c for c in courses if c.get("currentlyTaught") and c.get("maximumCredits", 0) > 0]

    packages: list[dict] = []

    def worker(course):
        try:
            pkgs = fetch_enrollment_packages(term, subject_code, course["courseId"])
            return [minify_package(course["courseId"], p) for p in pkgs]
        except requests.RequestException as e:
            print(f"  ! failed {course.get('courseDesignation')}: {e}", file=sys.stderr)
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        for result in pool.map(worker, courses):
            packages.extend(result)

    course_out = [
        {
            "subjectCode": c["subject"]["subjectCode"],
            "subjectShort": c["subject"]["shortDescription"],
            "catalogNumber": c["catalogNumber"],
            "courseId": c["courseId"],
            "title": c["title"],
            "minCredits": c["minimumCredits"],
            "maxCredits": c["maximumCredits"],
            "designation": c["courseDesignation"],
        }
        for c in courses
    ]
    return {"courses": course_out, "packages": packages}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--term", help="Term code, e.g. 1272. Defaults to the current term.")
    parser.add_argument("--subjects", help="Comma-separated subject codes, e.g. 266,600,932")
    parser.add_argument("--list-subjects", action="store_true", help="Print all subject codes for the term and exit")
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()

    term = args.term or get_current_term()
    print(f"Using term {term}")

    if args.list_subjects:
        subjects = get_subjects(term)
        for name, code in sorted(subjects.items()):
            print(f"{code}\t{name}")
        return

    if not args.subjects:
        parser.error("--subjects is required (or use --list-subjects to see options)")

    os.makedirs(OUT_DIR, exist_ok=True)
    codes = [c.strip() for c in args.subjects.split(",") if c.strip()]
    subjects_by_code = {v: k for k, v in get_subjects(term).items()}

    for code in codes:
        name = subjects_by_code.get(code, code)
        print(f"Fetching {name} ({code})...")
        t0 = time.time()
        data = fetch_subject(term, code, concurrency=args.concurrency)
        elapsed = time.time() - t0
        safe_name = "".join(ch if ch.isalnum() else "" for ch in name.split()[0]) or code
        out_path = os.path.join(OUT_DIR, f"{code}_{safe_name.upper()}.json")
        with open(out_path, "w") as f:
            json.dump(data, f)
        print(f"  -> {out_path}: {len(data['courses'])} courses, {len(data['packages'])} packages ({elapsed:.1f}s)")

    print("\nDone. Now run: python scripts/merge_raw.py")


if __name__ == "__main__":
    main()
