import os
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect, sync_playwright


def booking_row(page, topic):
    return page.locator("tbody tr").filter(
        has=page.get_by_role("cell", name=topic, exact=True)
    )


def fill_booking(page, form):
    page.locator("#unit_code").fill(form["unit_code"])
    page.locator("#topic").fill(form["topic"])
    page.locator("#room_id").select_option(form["room_id"])
    page.locator("#session_date").fill(form["session_date"])
    page.locator("#start_time").fill(form["start_time"])
    page.locator("#end_time").fill(form["end_time"])


@pytest.fixture
def site():
    url = os.environ.get("STAGING_URL", "").rstrip("/")
    if not url:
        pytest.fail("STAGING_URL must be set.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(base_url=url)
        page = context.new_page()
        page.set_default_timeout(15000)
        topics = []

        try:
            response = page.request.get(f"{url}/health")
            assert response.status == 200
            health = response.json()
            assert health["env"] == "staging"
            assert health["database"] == "ok"

            yield page, topics
        finally:
            try:
                for topic in topics:
                    page.goto("/")
                    row = booking_row(page, topic)
                    if row.count() == 1:
                        row.get_by_role("link", name="Delete", exact=True).click()
                        with page.expect_navigation():
                            page.locator(
                                'form button, form input[type="submit"]'
                            ).click()
                        expect(booking_row(page, topic)).to_have_count(0)
            finally:
                context.close()
                browser.close()


@pytest.fixture
def booking(site):
    page, topics = site
    page.goto("/sessions/new")

    room_id = page.locator(
        '#room_id option:not([value=""])'
    ).first.get_attribute("value")
    assert room_id, "No rooms are available."

    token = uuid4().hex
    topic = f"Chamodi E2E {token}"
    topics.extend([topic, f"{topic} edited", f"{topic} overlap"])

    # Different future dates reduce clashes with other team members.
    today = datetime.now(ZoneInfo("Australia/Melbourne")).date()
    future_day = today + timedelta(days=60 + int(token[:4], 16) % 300)

    return {
        "unit_code": "SWE40006",
        "topic": topic,
        "room_id": room_id,
        "session_date": future_day.isoformat(),
        "start_time": "10:00",
        "end_time": "11:00",
    }


def test_create_edit_overlap_and_delete(site, booking):
    page, _ = site
    original_topic = booking["topic"]

    # Create through the browser form.
    fill_booking(page, booking)
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()

    row = booking_row(page, original_topic)
    expect(row).to_have_count(1)
    expect(row).to_contain_text("10:00 to 11:00")

    # Edit through the booking's own Edit link.
    row.get_by_role("link", name="Edit", exact=True).click()
    edited_topic = f"{original_topic} edited"
    page.locator("#topic").fill(edited_topic)
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()

    expect(booking_row(page, original_topic)).to_have_count(0)
    expect(booking_row(page, edited_topic)).to_have_count(1)

    # Reject another booking that overlaps this booking.
    page.goto("/sessions/new")
    overlapping = {
        **booking,
        "topic": f"{original_topic} overlap",
        "start_time": "10:30",
        "end_time": "11:30",
    }
    fill_booking(page, overlapping)
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()

    expect(page.locator(".errors")).to_contain_text("already booked")
    page.goto("/")
    expect(booking_row(page, overlapping["topic"])).to_have_count(0)
    expect(booking_row(page, edited_topic)).to_have_count(1)

    # Visiting Delete must only show confirmation.
    row = booking_row(page, edited_topic)
    row.get_by_role("link", name="Delete", exact=True).click()
    delete_url = page.url
    page.goto("/")
    expect(booking_row(page, edited_topic)).to_have_count(1)

    # Confirm deletion, then verify it persisted after reloading.
    page.goto(delete_url)
    with page.expect_navigation():
        page.locator('form button, form input[type="submit"]').click()

    expect(booking_row(page, edited_topic)).to_have_count(0)
    page.reload()
    expect(booking_row(page, edited_topic)).to_have_count(0)


@pytest.mark.parametrize(
    ("changes", "expected_error"),
    [
        ({"unit_code": "BAD"}, "Unit code must be"),
        ({"topic": ""}, "Topic is required."),
        ({"room_id": ""}, "Choose a room."),
        ({"end_time": "09:00"}, "End time must be after"),
        ({"start_time": "06:00"}, "Rooms can only be booked"),
        ({"session_date": "2020-01-01"}, "The session can't be in the past."),
    ],
)
def test_invalid_booking_is_not_saved(site, booking, changes, expected_error):
    page, _ = site
    invalid_form = {**booking, **changes}
    fill_booking(page, invalid_form)

    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()

    expect(page.locator(".errors")).to_contain_text(expected_error)

    # A validation message alone is insufficient: check nothing was saved.
    page.goto("/")
    expect(booking_row(page, booking["topic"])).to_have_count(0)
