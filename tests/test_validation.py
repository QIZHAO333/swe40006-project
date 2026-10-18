from datetime import datetime

import pytest

from validation import validate_session


NOW = datetime(2030, 1, 1, 9, 0)


@pytest.fixture
def valid_form():
    return {
        "unit_code": "swe40006",
        "topic": "Study session",
        "room_id": "1",
        "session_date": "2030-01-02",
        "start_time": "10:00",
        "end_time": "11:00",
    }


def test_valid_form_normalises_unit_code(valid_form):
    data, errors = validate_session(valid_form, NOW)

    assert errors == []
    assert data["unit_code"] == "SWE40006"
    assert data["room_id"] == 1


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("unit_code", "", "Unit code is required."),
        ("unit_code", "INVALID", "Unit code must be"),
        ("topic", "", "Topic is required."),
        ("topic", "x" * 101, "Topic must be 100 characters or less."),
        ("room_id", "", "Choose a room."),
        ("session_date", "", "Date is required."),
        ("start_time", "", "Start and end time are required."),
        ("end_time", "09:00", "End time must be after the start time."),
        ("start_time", "06:00", "Rooms can only be booked"),
        ("end_time", "23:00", "Rooms can only be booked"),
        ("session_date", "2029-12-31", "The session can't be in the past."),
    ],
)
def test_invalid_form_is_rejected(valid_form, field, value, expected):
    valid_form[field] = value

    _, errors = validate_session(valid_form, NOW)

    assert any(expected in error for error in errors)