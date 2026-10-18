from datetime import timedelta
from urllib.parse import urlparse
import os

import pytest

import app as study_board
import db


@pytest.fixture
def client():
    database_url = os.environ.get("DATABASE_URL", "")

    if urlparse(database_url).path != "/studyboard_test":
        pytest.fail("Tests must use the separate studyboard_test database.")

    db.init_db()

    with db.get_conn() as conn:
        conn.execute("DELETE FROM study_sessions")

    study_board.app.config["TESTING"] = True

    with study_board.app.test_client() as test_client:
        yield test_client

    with db.get_conn() as conn:
        conn.execute("DELETE FROM study_sessions")


@pytest.fixture
def session_form(client):
    room = db.list_rooms()[0]
    tomorrow = study_board.now().date() + timedelta(days=1)

    return {
        "unit_code": "SWE40006",
        "topic": "Chamodi CI test",
        "room_id": str(room["id"]),
        "session_date": tomorrow.isoformat(),
        "start_time": "10:00",
        "end_time": "11:00",
    }


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Upcoming sessions" in response.get_data(as_text=True)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.get_json()["database"] == "ok"


def test_add_session(client, session_form):
    response = client.post("/sessions/new", data=session_form)

    assert response.status_code == 302
    saved = db.list_sessions()
    assert len(saved) == 1
    assert saved[0]["topic"] == "Chamodi CI test"

    page = client.get("/")
    assert "Chamodi CI test" in page.get_data(as_text=True)


def test_edit_session(client, session_form):
    client.post("/sessions/new", data=session_form)
    session_id = db.list_sessions()[0]["id"]

    session_form["topic"] = "Updated CI topic"
    response = client.post(
        f"/sessions/{session_id}/edit",
        data=session_form,
    )

    assert response.status_code == 302
    assert db.get_session(session_id)["topic"] == "Updated CI topic"


def test_delete_requires_confirmation(client, session_form):
    client.post("/sessions/new", data=session_form)
    session_id = db.list_sessions()[0]["id"]

    confirmation = client.get(f"/sessions/{session_id}/delete")

    assert confirmation.status_code == 200
    assert db.get_session(session_id) is not None

    response = client.post(f"/sessions/{session_id}/delete")

    assert response.status_code == 302
    assert db.get_session(session_id) is None


def test_overlapping_booking_is_rejected(client, session_form):
    client.post("/sessions/new", data=session_form)

    overlapping = {
        **session_form,
        "topic": "Overlapping booking",
        "start_time": "10:30",
        "end_time": "11:30",
    }
    response = client.post("/sessions/new", data=overlapping)

    assert response.status_code == 200
    assert "already booked" in response.get_data(as_text=True)
    assert len(db.list_sessions()) == 1


def test_missing_topic_is_rejected(client, session_form):
    session_form["topic"] = ""

    response = client.post("/sessions/new", data=session_form)

    assert response.status_code == 200
    assert "Topic is required." in response.get_data(as_text=True)
    assert db.list_sessions() == []


def test_health_reports_database_failure(client, monkeypatch):
    def unavailable_database():
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(db, "check_db", unavailable_database)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json()["database"] == "unreachable"