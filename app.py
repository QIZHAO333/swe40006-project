import os
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, abort, redirect, render_template, request, url_for

import db
from validation import validate_session

app = Flask(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")
GIT_SHA = os.environ.get("GIT_SHA", "local")
TIMEZONE = ZoneInfo(os.environ.get("APP_TIMEZONE", "Australia/Melbourne"))


def now_local():
    # Naive datetime in local time, so it can be compared with the date and
    # time columns in the database
    return datetime.now(TIMEZONE).replace(tzinfo=None)


@app.context_processor
def footer_info():
    return {"app_env": APP_ENV, "git_sha": GIT_SHA[:7]}


@app.route("/")
def index():
    unit = request.args.get("unit", "").strip().upper()
    now = now_local()
    upcoming, past = [], []
    for s in db.list_sessions(unit or None):
        if datetime.combine(s["session_date"], s["start_time"]) >= now:
            upcoming.append(s)
        else:
            past.append(s)
    past.reverse()  # most recent past session first
    return render_template("index.html", upcoming=upcoming, past=past, unit=unit)


@app.route("/sessions/new", methods=["GET", "POST"])
def new_session():
    form = request.form if request.method == "POST" else {}
    errors = []
    if request.method == "POST":
        data, errors = validate_session(form, now_local())
        if not errors and db.room_taken(data["room"], data["session_date"], data["start_time"]):
            errors.append("That room is already booked at that date and time.")
        if not errors:
            db.add_session(data)
            return redirect(url_for("index"))
    return render_template("form.html", title="Post a study session", form=form, errors=errors)


@app.route("/sessions/<int:session_id>/edit", methods=["GET", "POST"])
def edit_session(session_id):
    session = db.get_session(session_id)
    if session is None:
        abort(404)

    errors = []
    if request.method == "POST":
        form = request.form
        data, errors = validate_session(form, now_local())
        if not errors and db.room_taken(
            data["room"], data["session_date"], data["start_time"], ignore_id=session_id
        ):
            errors.append("That room is already booked at that date and time.")
        if not errors:
            db.update_session(session_id, data)
            return redirect(url_for("index"))
    else:
        form = {
            "unit_code": session["unit_code"],
            "topic": session["topic"],
            "room": session["room"],
            "session_date": session["session_date"].isoformat(),
            "start_time": session["start_time"].strftime("%H:%M"),
        }
    return render_template("form.html", title="Edit study session", form=form, errors=errors)


@app.route("/sessions/<int:session_id>/delete", methods=["GET", "POST"])
def delete_session(session_id):
    session = db.get_session(session_id)
    if session is None:
        abort(404)
    if request.method == "POST":
        db.delete_session(session_id)
        return redirect(url_for("index"))
    return render_template("confirm_delete.html", s=session)


@app.route("/health")
def health():
    try:
        db.check_db()
    except Exception:
        return {"status": "error", "database": "unreachable"}, 503
    return {"status": "ok", "database": "ok", "env": APP_ENV, "sha": GIT_SHA}
