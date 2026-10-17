import os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, abort, redirect, render_template, request, url_for

import db
from validation import validate_session

app = Flask(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")
GIT_SHA = os.environ.get("GIT_SHA", "local")


def now():
    return datetime.now(ZoneInfo("Australia/Melbourne")).replace(tzinfo=None)


def check_form(form, session_id=None):
    data, errors = validate_session(form, now())
    if not errors and db.get_room(data["room_id"]) is None:
        errors.append("Choose a room.")
    if not errors:
        clash = db.find_clash(
            data["room_id"], data["session_date"], data["start_time"], data["end_time"],
            session_id,
        )
        if clash:
            errors.append(
                f"That room is already booked from {clash['start_time']:%H:%M}"
                f" to {clash['end_time']:%H:%M} on that day."
            )
    return data, errors


def show_form(title, form, errors):
    return render_template(
        "form.html", title=title, form=form, errors=errors, rooms=db.list_rooms()
    )


@app.context_processor
def footer_info():
    return {"app_env": APP_ENV, "git_sha": GIT_SHA[:7]}


@app.route("/")
def index():
    unit = request.args.get("unit", "").strip().upper()
    upcoming, past = [], []
    for s in db.list_sessions(unit):
        if datetime.combine(s["session_date"], s["end_time"]) >= now():
            upcoming.append(s)
        else:
            past.insert(0, s)
    return render_template("index.html", upcoming=upcoming, past=past, unit=unit)


@app.route("/sessions/new", methods=["GET", "POST"])
def new_session():
    form, errors = {"room_id": request.args.get("room_id", "")}, []
    if request.method == "POST":
        form = request.form
        data, errors = check_form(form)
        if not errors:
            db.add_session(data)
            return redirect(url_for("index"))
    return show_form("Post a study session", form, errors)


@app.route("/sessions/<int:session_id>/edit", methods=["GET", "POST"])
def edit_session(session_id):
    s = db.get_session(session_id)
    if s is None:
        abort(404)

    errors = []
    if request.method == "POST":
        form = request.form
        data, errors = check_form(form, session_id)
        if not errors:
            db.update_session(session_id, data)
            return redirect(url_for("index"))
    else:
        form = dict(s)
        form["start_time"] = s["start_time"].strftime("%H:%M")
        form["end_time"] = s["end_time"].strftime("%H:%M")
    return show_form("Edit study session", form, errors)


@app.route("/sessions/<int:session_id>/delete", methods=["GET", "POST"])
def delete_session(session_id):
    s = db.get_session(session_id)
    if s is None:
        abort(404)
    if request.method == "POST":
        db.delete_session(session_id)
        return redirect(url_for("index"))
    return render_template("confirm_delete.html", s=s)


@app.route("/rooms")
def rooms():
    return render_template("rooms.html", rooms=db.list_rooms())


@app.route("/rooms/<int:room_id>")
def room_calendar(room_id):
    room = db.get_room(room_id)
    if room is None:
        abort(404)

    try:
        day = date.fromisoformat(request.args.get("week", ""))
    except ValueError:
        day = now().date()
    monday = day - timedelta(days=day.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]
    sessions = db.room_sessions(room_id, days[0], days[-1])

    rows = []
    for hour in range(7, 22):
        slot_start, slot_end = time(hour), time(hour + 1)
        cells = []
        for d in days:
            booked = None
            for s in sessions:
                if (s["session_date"] == d and s["start_time"] < slot_end
                        and s["end_time"] > slot_start):
                    booked = s
            cells.append(booked)
        rows.append((slot_start, cells))

    return render_template(
        "room_calendar.html",
        room=room,
        days=days,
        rows=rows,
        prev_week=monday - timedelta(days=7),
        next_week=monday + timedelta(days=7),
    )


@app.route("/health")
def health():
    try:
        db.check_db()
    except Exception:
        return {"status": "error", "database": "unreachable"}, 503
    return {"status": "ok", "database": "ok", "env": APP_ENV, "sha": GIT_SHA}
