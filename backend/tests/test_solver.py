from app.models import Course, Meeting, Package, Preferences, Section
from app.solver import filter_candidates, solve


def make_course(designation, packages):
    return Course(
        courseId=designation.replace(" ", "_"),
        designation=designation,
        subjectCode="000",
        subjectShort=designation.split()[0],
        catalogNumber=designation.split()[-1],
        title=f"Intro to {designation}",
        minCredits=3,
        maxCredits=3,
        packages=packages,
    )


def make_package(pkg_id, days, start, end, status="OPEN", seats=10):
    return Package(
        packageId=pkg_id,
        status=status,
        seats=seats,
        waitlist=0,
        sections=[
            Section(
                type="LEC",
                num="001",
                instructor="Test Instructor",
                meetings=[Meeting(days=days, start=start, end=end)],
            )
        ],
    )


def test_no_conflict_two_courses_returns_a_schedule():
    course_a = make_course("TEST 100", [make_package("A1", ["MON", "WED"], 540, 590)])
    course_b = make_course("TEST 200", [make_package("B1", ["TUE", "THU"], 600, 650)])
    prefs = Preferences()
    candidates = [(course_a, filter_candidates(course_a, prefs)), (course_b, filter_candidates(course_b, prefs))]
    results = solve(candidates, prefs)
    assert len(results) == 1
    designations = {c.designation for c in results[0].courses}
    assert designations == {"TEST 100", "TEST 200"}


def test_only_conflicting_sections_yields_no_schedule():
    course_a = make_course("TEST 100", [make_package("A1", ["MON", "WED"], 540, 590)])
    course_b = make_course("TEST 200", [make_package("B1", ["MON", "WED"], 560, 610)])  # overlaps A1
    prefs = Preferences()
    candidates = [(course_a, filter_candidates(course_a, prefs)), (course_b, filter_candidates(course_b, prefs))]
    results = solve(candidates, prefs)
    assert results == []


def test_solver_picks_conflict_free_alternative_when_available():
    course_a = make_course("TEST 100", [make_package("A1", ["MON"], 540, 590)])
    course_b = make_course(
        "TEST 200",
        [
            make_package("B1", ["MON"], 560, 610),  # conflicts with A1
            make_package("B2", ["TUE"], 560, 610),  # no conflict
        ],
    )
    prefs = Preferences()
    candidates = [(course_a, filter_candidates(course_a, prefs)), (course_b, filter_candidates(course_b, prefs))]
    results = solve(candidates, prefs)
    assert len(results) == 1
    chosen_ids = {c.packageId for c in results[0].courses}
    assert chosen_ids == {"A1", "B2"}


def test_avoid_days_hard_filter():
    course = make_course(
        "TEST 100",
        [
            make_package("A1", ["FRI"], 540, 590),
            make_package("A2", ["TUE"], 540, 590),
        ],
    )
    prefs = Preferences(avoidDays=["FRI"])
    candidates = filter_candidates(course, prefs)
    assert [p.packageId for p in candidates] == ["A2"]


def test_earliest_latest_hard_filter():
    course = make_course(
        "TEST 100",
        [
            make_package("EARLY", ["MON"], 480, 530),  # 8:00-8:50
            make_package("MID", ["MON"], 600, 650),  # 10:00-10:50
        ],
    )
    prefs = Preferences(earliest="09:00", latest="17:00")
    candidates = filter_candidates(course, prefs)
    assert [p.packageId for p in candidates] == ["MID"]


def test_waitlisted_excluded_unless_allowed():
    course = make_course("TEST 100", [make_package("W1", ["MON"], 540, 590, status="WAITLISTED")])
    strict = Preferences(allowWaitlisted=False)
    lenient = Preferences(allowWaitlisted=True)
    assert filter_candidates(course, strict) == []
    assert len(filter_candidates(course, lenient)) == 1


def test_closed_always_excluded():
    course = make_course("TEST 100", [make_package("C1", ["MON"], 540, 590, status="CLOSED")])
    prefs = Preferences(allowWaitlisted=True)
    assert filter_candidates(course, prefs) == []


def test_async_course_has_no_meetings_and_never_conflicts():
    course_a = make_course(
        "TEST 100",
        [
            Package(packageId="ASYNC", status="OPEN", seats=5, waitlist=0, sections=[
                Section(type="LEC", num="001", instructor="Someone", meetings=[])
            ])
        ],
    )
    course_b = make_course("TEST 200", [make_package("B1", ["MON"], 540, 590)])
    prefs = Preferences()
    candidates = [(course_a, filter_candidates(course_a, prefs)), (course_b, filter_candidates(course_b, prefs))]
    results = solve(candidates, prefs)
    assert len(results) == 1
    assert results[0].gapMinutes == 0


def test_max_results_respected():
    # three mutually non-conflicting sections for a single course-slot pair
    # across two courses, each course offering multiple non-conflicting
    # options so several distinct combinations exist.
    course_a = make_course(
        "TEST 100",
        [
            make_package("A1", ["MON"], 480, 530),
            make_package("A2", ["MON"], 600, 650),
            make_package("A3", ["MON"], 720, 770),
        ],
    )
    course_b = make_course(
        "TEST 200",
        [
            make_package("B1", ["TUE"], 480, 530),
            make_package("B2", ["TUE"], 600, 650),
        ],
    )
    prefs = Preferences(maxResults=2)
    candidates = [(course_a, filter_candidates(course_a, prefs)), (course_b, filter_candidates(course_b, prefs))]
    results = solve(candidates, prefs)
    assert len(results) == 2
