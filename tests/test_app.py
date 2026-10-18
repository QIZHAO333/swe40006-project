import pytest

import app as study_board


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(study_board.app.config, "TESTING", True)
    monkeypatch.setattr(study_board, "sessions", [])

    with study_board.app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert study_board.TITLE in response.get_data(as_text=True)
    assert 'action="/add"' in response.get_data(as_text=True)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"

def test_add_session_redirects_home(client):
    response = client.post(
        "/add",
        data={
            "unit": "SWE40006",
            "topic": "CI testing",
            "when": "Library, 2:30 pm",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert len(study_board.sessions) == 1


def test_added_session_appears_on_home_page(client):
    response = client.post(
        "/add",
        data={
            "unit": "SWE40006",
            "topic": "CI testing",
            "when": "Library, 2:30 pm",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "SWE40006 - CI testing - Library, 2:30 pm" in html