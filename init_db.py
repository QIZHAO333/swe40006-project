"""Create the database table if it is not there yet.

Runs once when the web container starts, before gunicorn.
"""

import db

if __name__ == "__main__":
    db.init_db()
    print("Database ready")
