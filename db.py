import os

import psycopg
from psycopg.rows import dict_row

ROOMS = [
    ("ATC325", 8),
    ("EN101", 12),
    ("BA603", 6),
    ("AR104", 20),
    ("Library Group Room 1", 4),
]


def get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(30) UNIQUE NOT NULL,
                capacity INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id SERIAL PRIMARY KEY,
                unit_code VARCHAR(8) NOT NULL,
                topic VARCHAR(100) NOT NULL,
                room_id INTEGER NOT NULL REFERENCES rooms(id),
                session_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL
            )
        """)
        for name, capacity in ROOMS:
            conn.execute(
                "INSERT INTO rooms (name, capacity) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
                (name, capacity),
            )


SESSION_SELECT = (
    "SELECT s.*, r.name AS room FROM study_sessions s JOIN rooms r ON r.id = s.room_id"
)


def list_rooms():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM rooms ORDER BY name").fetchall()


def get_room(room_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM rooms WHERE id = %s", (room_id,)).fetchone()


def list_sessions(unit_code=""):
    with get_conn() as conn:
        if unit_code:
            return conn.execute(
                SESSION_SELECT + " WHERE s.unit_code = %s ORDER BY session_date, start_time",
                (unit_code,),
            ).fetchall()
        return conn.execute(SESSION_SELECT + " ORDER BY session_date, start_time").fetchall()


def room_sessions(room_id, first_day, last_day):
    with get_conn() as conn:
        return conn.execute(
            SESSION_SELECT + " WHERE s.room_id = %s AND session_date BETWEEN %s AND %s",
            (room_id, first_day, last_day),
        ).fetchall()


def get_session(session_id):
    with get_conn() as conn:
        return conn.execute(SESSION_SELECT + " WHERE s.id = %s", (session_id,)).fetchone()


def add_session(s):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO study_sessions"
            " (unit_code, topic, room_id, session_date, start_time, end_time)"
            " VALUES (%(unit_code)s, %(topic)s, %(room_id)s, %(session_date)s,"
            " %(start_time)s, %(end_time)s)",
            s,
        )


def update_session(session_id, s):
    with get_conn() as conn:
        conn.execute(
            "UPDATE study_sessions SET unit_code = %(unit_code)s, topic = %(topic)s,"
            " room_id = %(room_id)s, session_date = %(session_date)s,"
            " start_time = %(start_time)s, end_time = %(end_time)s WHERE id = %(id)s",
            {**s, "id": session_id},
        )


def delete_session(session_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM study_sessions WHERE id = %s", (session_id,))


def find_clash(room_id, session_date, start_time, end_time, session_id=None):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM study_sessions WHERE room_id = %s AND session_date = %s"
            " AND start_time < %s AND end_time > %s AND id <> %s ORDER BY start_time",
            (room_id, session_date, end_time, start_time, session_id or 0),
        ).fetchone()


def check_db():
    with get_conn() as conn:
        conn.execute("SELECT 1")
