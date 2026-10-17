import re
from datetime import date, datetime, time

# Swinburne unit codes look like SWE40006: 3 letters then 5 digits
UNIT_CODE_PATTERN = re.compile(r"^[A-Z]{3}\d{5}$")


def validate_session(form, now):
    """Check the form fields. Returns (cleaned_data, errors).

    `now` is passed in so tests can control what "the past" means.
    """
    errors = []
    data = {
        "unit_code": form.get("unit_code", "").strip().upper(),
        "topic": form.get("topic", "").strip(),
        "room": form.get("room", "").strip(),
        "session_date": None,
        "start_time": None,
    }

    if not data["unit_code"]:
        errors.append("Unit code is required.")
    elif not UNIT_CODE_PATTERN.match(data["unit_code"]):
        errors.append("Unit code must be 3 letters and 5 numbers, for example SWE40006.")

    if not data["topic"]:
        errors.append("Topic is required.")
    elif len(data["topic"]) > 100:
        errors.append("Topic must be 100 characters or less.")

    if not data["room"]:
        errors.append("Room is required.")
    elif len(data["room"]) > 30:
        errors.append("Room must be 30 characters or less.")

    try:
        data["session_date"] = date.fromisoformat(form.get("session_date", ""))
    except ValueError:
        errors.append("Date is required.")

    try:
        data["start_time"] = time.fromisoformat(form.get("start_time", ""))
    except ValueError:
        errors.append("Start time is required.")

    if data["session_date"] and data["start_time"]:
        starts = datetime.combine(data["session_date"], data["start_time"])
        if starts < now:
            errors.append("The session can't be in the past.")

    return data, errors
