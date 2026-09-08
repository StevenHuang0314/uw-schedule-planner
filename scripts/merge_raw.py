"""
Merge the per-subject raw JSON files in data/raw/ (produced either by
scripts/fetch_courses.py or by the one-off browser-based capture used to seed
this repo) into a single normalized dataset at data/courses.json.

Output shape:
{
  "term": {"code": "1272", "name": "Fall 2026"},
  "generatedAt": "...",
  "courses": [
    {
      "courseId": "024795",
      "designation": "COMP SCI 300",
      "subjectCode": "266",
      "subjectShort": "COMP SCI",
      "catalogNumber": "300",
      "title": "Programming II",
      "minCredits": 3,
      "maxCredits": 3,
      "packages": [
        {
          "packageId": "29366",
          "status": "WAITLISTED",
          "seats": 0,
          "waitlist": 0,
          "sections": [
            {
              "type": "LEC",
              "num": "003",
              "instructor": "Ben Jacobsen",
              "meetings": [
                {"days": ["MON","WED","FRI"], "start": 1020, "end": 1070, "bldg": "Computer Sciences", "room": "1325"}
              ]
            }
          ]
        }
      ]
    }
  ]
}

start/end are minutes since midnight (local time), e.g. 1020 = 17:00.
"""
import json
import glob
import sys
from datetime import datetime, timezone

RAW_GLOB = "data/raw/*.json"
OUT_PATH = "data/courses.json"
TERM_CODE = "1272"
TERM_NAME = "Fall 2026"


def main():
    files = sorted(glob.glob(RAW_GLOB))
    if not files:
        print(f"No raw files found matching {RAW_GLOB}", file=sys.stderr)
        sys.exit(1)

    by_course_id = {}
    for path in files:
        with open(path) as f:
            data = json.load(f)
        course_meta = {c["courseId"]: c for c in data["courses"]}
        packages_by_course = {}
        for pkg in data["packages"]:
            packages_by_course.setdefault(pkg["courseId"], []).append(
                {
                    "packageId": pkg["pkgId"],
                    "status": pkg["status"],
                    "seats": pkg["seats"],
                    "waitlist": pkg["waitlist"],
                    "sections": [
                        {
                            "type": s["type"],
                            "num": s["num"],
                            "instructor": s["instr"],
                            "meetings": s["meetings"],
                        }
                        for s in pkg["sections"]
                    ],
                }
            )

        for course_id, meta in course_meta.items():
            by_course_id[course_id] = {
                "courseId": course_id,
                "designation": meta["designation"],
                "subjectCode": meta["subjectCode"],
                "subjectShort": meta["subjectShort"],
                "catalogNumber": meta["catalogNumber"],
                "title": meta["title"],
                "minCredits": meta["minCredits"],
                "maxCredits": meta["maxCredits"],
                "packages": packages_by_course.get(course_id, []),
            }

    courses = sorted(
        by_course_id.values(),
        key=lambda c: (c["subjectShort"], int(c["catalogNumber"]) if c["catalogNumber"].isdigit() else 0),
    )
    # drop courses with zero schedulable packages (no sections at all)
    courses = [c for c in courses if c["packages"]]

    out = {
        "term": {"code": TERM_CODE, "name": TERM_NAME},
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "courses": courses,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=None, separators=(",", ":"))

    total_packages = sum(len(c["packages"]) for c in courses)
    print(f"Wrote {OUT_PATH}: {len(courses)} courses, {total_packages} packages")


if __name__ == "__main__":
    main()
