import re
from datetime import date, datetime, time

OPENS = time(7, 0)
CLOSES = time(22, 0)


def validate_session(form, now):
    errors = []
    data = {
        "unit_code": form.get("unit_code", "").strip().upper(),
        "topic": form.get("topic", "").strip(),
        "room_id": None,
        "session_date": None,
        "start_time": None,
        "end_time": None,
    }

    if not data["unit_code"]:
        errors.append("Unit code is required.")
    elif not re.fullmatch(r"[A-Z]{3}\d{5}", data["unit_code"]):
        errors.append("Unit code must be 3 letters and 5 numbers, for example SWE40006.")

    if not data["topic"]:
        errors.append("Topic is required.")
    elif len(data["topic"]) > 100:
        errors.append("Topic must be 100 characters or less.")

    try:
        data["room_id"] = int(form.get("room_id", ""))
    except ValueError:
        errors.append("Choose a room.")

    try:
        data["session_date"] = date.fromisoformat(form.get("session_date", ""))
    except ValueError:
        errors.append("Date is required.")

    try:
        data["start_time"] = time.fromisoformat(form.get("start_time", ""))
        data["end_time"] = time.fromisoformat(form.get("end_time", ""))
    except ValueError:
        errors.append("Start and end time are required.")
        return data, errors

    if data["end_time"] <= data["start_time"]:
        errors.append("End time must be after the start time.")
    elif data["start_time"] < OPENS or data["end_time"] > CLOSES:
        errors.append("Rooms can only be booked between 07:00 and 22:00.")

    if data["session_date"]:
        if datetime.combine(data["session_date"], data["start_time"]) < now:
            errors.append("The session can't be in the past.")

    return data, errors
