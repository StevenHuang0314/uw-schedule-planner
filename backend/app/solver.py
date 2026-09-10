"""Schedule solver.

Modeled as a constraint satisfaction / optimization problem and solved with
Google OR-Tools' CP-SAT solver:

  - One boolean decision variable per (course, package) candidate.
  - Exactly one package chosen per requested course.
  - Pairwise conflict constraints forbid choosing two packages whose class
    meetings overlap in time on a shared day.
  - A soft objective rewards compact schedules (less idle time between
    classes) when the caller asks for it, plus a small bonus for open
    (non-waitlisted) seats.

To return several distinct ranked options rather than just the single best
one, we solve, record the winning combination, forbid it, and re-solve --
repeated up to `preferences.maxResults` times. Each re-solve is cheap because
the problem is small (at most a few candidates per course).
"""
from __future__ import annotations

from itertools import combinations

from ortools.sat.python import cp_model

from app.models import Course, Meeting, Package, Preferences, ScheduleOption, ScheduledCourse, ScheduledMeeting

DAY_ORDER = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _hhmm_to_minutes(value: str) -> int:
    h, m = value.split(":")
    return int(h) * 60 + int(m)


def _meetings_overlap(a: Meeting, b: Meeting) -> bool:
    if not set(a.days) & set(b.days):
        return False
    return a.start < b.end and b.start < a.end


def _packages_conflict(a: Package, b: Package) -> bool:
    for ma in a.all_meetings:
        for mb in b.all_meetings:
            if _meetings_overlap(ma, mb):
                return True
    return False


def _package_satisfies_hard_prefs(pkg: Package, prefs: Preferences) -> bool:
    if pkg.status == "CLOSED":
        return False
    if pkg.status == "WAITLISTED" and not prefs.allowWaitlisted:
        return False
    earliest = _hhmm_to_minutes(prefs.earliest) if prefs.earliest else None
    latest = _hhmm_to_minutes(prefs.latest) if prefs.latest else None
    avoid = set(prefs.avoidDays)
    for m in pkg.all_meetings:
        if avoid & set(m.days):
            return False
        if earliest is not None and m.start < earliest:
            return False
        if latest is not None and m.end > latest:
            return False
    return True


def _gap_minutes_for_combo(packages: list[Package]) -> int:
    """Sum, over each day, of idle minutes strictly between consecutive classes."""
    by_day: dict[str, list[tuple[int, int]]] = {d: [] for d in DAY_ORDER}
    for pkg in packages:
        for m in pkg.all_meetings:
            for d in m.days:
                by_day[d].append((m.start, m.end))
    total_gap = 0
    for intervals in by_day.values():
        intervals.sort()
        for (s1, e1), (s2, e2) in zip(intervals, intervals[1:]):
            if s2 > e1:
                total_gap += s2 - e1
    return total_gap


def _days_with_classes(packages: list[Package]) -> int:
    days: set[str] = set()
    for pkg in packages:
        for m in pkg.all_meetings:
            days.update(m.days)
    return len(days)


def _build_schedule_option(course_pkg_pairs: list[tuple[Course, Package]]) -> ScheduleOption:
    packages = [p for _, p in course_pkg_pairs]
    gap = _gap_minutes_for_combo(packages)
    days = _days_with_classes(packages)
    total_credits = sum(c.maxCredits for c, _ in course_pkg_pairs)
    open_bonus = sum(1 for p in packages if p.status == "OPEN")
    # Lower gap is better; more open seats is better. Combine into one score
    # (higher = better) that's easy to sort by.
    score = open_bonus * 10 - gap * 0.05

    scheduled_courses = []
    meetings_out = []
    for course, pkg in course_pkg_pairs:
        scheduled_courses.append(
            ScheduledCourse(
                designation=course.designation,
                title=course.title,
                credits=course.maxCredits,
                packageId=pkg.packageId,
                status=pkg.status,
                seats=pkg.seats,
                waitlist=pkg.waitlist,
                sections=pkg.sections,
                isAsynchronous=pkg.is_asynchronous,
            )
        )
        for section in pkg.sections:
            for m in section.meetings:
                meetings_out.append(
                    ScheduledMeeting(
                        designation=course.designation,
                        title=course.title,
                        sectionType=section.type,
                        sectionNum=section.num,
                        instructor=section.instructor,
                        days=m.days,
                        start=m.start,
                        end=m.end,
                        bldg=m.bldg,
                        room=m.room,
                    )
                )

    return ScheduleOption(
        courses=scheduled_courses,
        meetings=meetings_out,
        totalCredits=total_credits,
        score=score,
        gapMinutes=gap,
        daysWithClasses=days,
    )


def solve(
    courses_with_candidates: list[tuple[Course, list[Package]]],
    preferences: Preferences,
) -> list[ScheduleOption]:
    """courses_with_candidates: for each requested course, the course object
    and the list of its packages that already satisfy hard preferences
    (see _package_satisfies_hard_prefs, applied by the caller).

    Returns up to preferences.maxResults distinct ScheduleOptions, best first.
    Returns an empty list if no combination of packages is conflict-free.
    """
    n = len(courses_with_candidates)
    if n == 0:
        return []

    model = cp_model.CpModel()
    # choice_vars[i][j] = 1 if package j chosen for course i
    choice_vars: list[list[cp_model.IntVar]] = []
    for i, (course, candidates) in enumerate(courses_with_candidates):
        row = [model.NewBoolVar(f"c{i}_p{j}") for j in range(len(candidates))]
        choice_vars.append(row)
        model.Add(sum(row) == 1)

    # Pairwise conflict constraints between every candidate pair across
    # different courses.
    for i, j in combinations(range(n), 2):
        _, cand_i = courses_with_candidates[i]
        _, cand_j = courses_with_candidates[j]
        for a, pkg_a in enumerate(cand_i):
            for b, pkg_b in enumerate(cand_j):
                if _packages_conflict(pkg_a, pkg_b):
                    model.Add(choice_vars[i][a] + choice_vars[j][b] <= 1)

    # Soft objective: reward open seats, and (if requested) compact
    # schedules. Gap minutes aren't linear in the choice vars in general, so
    # we approximate by scoring complete combinations post-hoc across a
    # bounded number of top solutions instead of encoding gaps directly in
    # the CP-SAT objective -- see the re-solve loop below, which asks CP-SAT
    # for feasible (not necessarily gap-optimal) combinations and then ranks
    # them by the real score function.
    open_terms = []
    for i, (course, candidates) in enumerate(courses_with_candidates):
        for j, pkg in enumerate(candidates):
            if pkg.status == "OPEN":
                open_terms.append(choice_vars[i][j])
    if open_terms:
        model.Maximize(sum(open_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2.0
    solver.parameters.num_search_workers = 4

    results: list[ScheduleOption] = []
    seen_combos: set[tuple[str, ...]] = set()
    max_results = preferences.maxResults
    # Pull a pool of candidate feasible combinations (more than maxResults),
    # then rank by the real score and keep the top N -- this way the
    # gap-minimization preference actually influences which options are
    # surfaced even though it wasn't part of the CP-SAT objective itself.
    pool: list[list[tuple[Course, Package]]] = []
    pool_target = max_results * 4

    for _ in range(pool_target):
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            break
        combo: list[tuple[Course, Package]] = []
        combo_ids = []
        for i, (course, candidates) in enumerate(courses_with_candidates):
            for j, pkg in enumerate(candidates):
                if solver.Value(choice_vars[i][j]):
                    combo.append((course, pkg))
                    combo_ids.append(pkg.packageId)
                    break
        key = tuple(sorted(combo_ids))
        if key not in seen_combos:
            seen_combos.add(key)
            pool.append(combo)
        # forbid this exact combination and search again
        forbid_terms = []
        for i, (course, candidates) in enumerate(courses_with_candidates):
            for j, pkg in enumerate(candidates):
                if solver.Value(choice_vars[i][j]):
                    forbid_terms.append(choice_vars[i][j])
        model.Add(sum(forbid_terms) <= len(forbid_terms) - 1)
        if len(pool) >= pool_target:
            break

    options = [_build_schedule_option(combo) for combo in pool]
    if preferences.minimizeGaps:
        options.sort(key=lambda o: (-o.score, o.gapMinutes))
    else:
        options.sort(key=lambda o: -o.score)
    return options[:max_results]


def filter_candidates(course: Course, preferences: Preferences) -> list[Package]:
    return [p for p in course.packages if _package_satisfies_hard_prefs(p, preferences)]
