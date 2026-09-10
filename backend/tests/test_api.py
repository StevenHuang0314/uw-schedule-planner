from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_search_finds_comp_sci_300():
    r = client.get("/api/courses/search", params={"q": "COMP SCI 300"})
    assert r.status_code == 200
    results = r.json()
    assert any(c["designation"] == "COMP SCI 300" for c in results)


def test_get_course_by_designation():
    r = client.get("/api/courses/COMP%20SCI%20300")
    assert r.status_code == 200
    assert r.json()["title"]


def test_get_unknown_course_returns_null():
    r = client.get("/api/courses/NOT A REAL COURSE 999")
    assert r.status_code == 200
    assert r.json() is None


def test_schedule_endpoint_with_real_courses():
    r = client.post(
        "/api/schedule",
        json={
            "courses": ["COMP SCI 300", "MATH 222"],
            "preferences": {"maxResults": 3},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["unresolved"] == []
    # There may or may not be a conflict-free combo depending on live data,
    # but the request itself must always succeed and be well-formed.
    assert "schedules" in body
    for option in body["schedules"]:
        assert len(option["courses"]) == 2


def test_schedule_endpoint_reports_unresolved_course():
    r = client.post(
        "/api/schedule",
        json={"courses": ["NOT A REAL COURSE 999"], "preferences": {}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["unresolved"] == ["NOT A REAL COURSE 999"]
    assert body["schedules"] == []
