import os
from urllib.request import urlopen

import pytest


@pytest.fixture
def staging_url():
    url = os.environ.get("STAGING_URL", "").rstrip("/")
    if not url:
        pytest.fail("Set STAGING_URL to the staging website address.")
    return url


@pytest.mark.parametrize(
    ("path", "expected_text"),
    [
        ("/", "Upcoming sessions"),
        ("/rooms", "Rooms"),
        ("/sessions/new", 'name="unit_code"'),
    ],
)
def test_staging_pages(staging_url, path, expected_text):
    with urlopen(f"{staging_url}{path}", timeout=20) as response:
        assert response.status == 200
        html = response.read().decode("utf-8")

    assert expected_text in html


def test_staging_health(staging_url):
    import json

    with urlopen(f"{staging_url}/health", timeout=20) as response:
        assert response.status == 200
        health = json.load(response)

    assert health["status"] == "ok"
    assert health["database"] == "ok"
    assert health["env"] == "staging"
