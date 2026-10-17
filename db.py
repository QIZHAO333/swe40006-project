import os

import psycopg
from psycopg.rows import dict_row

SCHEMA = """
CREATE TABLE IF NOT EXISTS study_sessions (
    id SERIAL PRIMARY KEY,
    unit_code VARCHAR(8) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    room VARCHAR(30) NOT NULL,
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def init_db():
    with get_conn() as conn:
        conn.execute(SCHEMA)


def list_sessions(unit_code=None):
    sql = "SELECT * FROM study_sessions"
    params = []
    if unit_code:
        sql += " WHERE unit_code = %s"
        params.append(unit_code)
    sql += " ORDER BY session_date, start_time"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def get_session(session_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM study_sessions WHERE id = %s", (session_id,)
        ).fetchone()


def add_session(s):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO study_sessions (unit_code, topic, room, session_date, start_time)"
            " VALUES (%s, %s, %s, %s, %s)",
            (s["unit_code"], s["topic"], s["room"], s["session_date"], s["start_time"]),
        )


def update_session(session_id, s):
    with get_conn() as conn:
        conn.execute(
            "UPDATE study_sessions SET unit_code = %s, topic = %s, room = %s,"
            " session_date = %s, start_time = %s WHERE id = %s",
            (s["unit_code"], s["topic"], s["room"], s["session_date"],
             s["start_time"], session_id),
        )


def delete_session(session_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM study_sessions WHERE id = %s", (session_id,))


def room_taken(room, session_date, start_time, ignore_id=None):
    # Same room, same date and same start time counts as a clash.
    # ignore_id lets a session keep its own slot when it is edited.
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM study_sessions WHERE LOWER(room) = LOWER(%s)"
            " AND session_date = %s AND start_time = %s AND id <> %s",
            (room, session_date, start_time, ignore_id or 0),
        ).fetchone()
    return row is not None


def check_db():
    with get_conn() as conn:
        conn.execute("SELECT 1")
