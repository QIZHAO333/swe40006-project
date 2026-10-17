# Study Board

SWE40006 group project, CL06_Fri10:30_G02.

Study Board lets students post study sessions for a unit so others can join. You can post, edit and delete a session, filter by unit code, and see upcoming and past sessions in separate lists. Each session books one of the rooms for a start and end time. Every room has a weekly calendar, and the app refuses any booking that overlaps one already in that room.

Built with Flask, gunicorn and PostgreSQL 16, all running in Docker Compose.

## What you need

- Docker Desktop (it comes with Docker Compose)
- Git

You don't need Python or PostgreSQL on your laptop. Everything runs inside the containers.

## First time setup

```bash
git clone <repo-url>
cd study-board
cp .env.example .env
```

On Windows (PowerShell) use `copy .env.example .env` instead of `cp`.

You can leave the values in `.env` as they are for local work. Never commit `.env`. It is already in `.gitignore`.

## Run the app

```bash
docker compose up --build
```

Then open http://localhost:8000.

Check it is working at http://localhost:8000/health. You should see `"status": "ok"` and `"database": "ok"`.

Press `Ctrl+C` to stop it.

## Useful commands

| What | Command |
|------|---------|
| Run in the background | `docker compose up -d --build` |
| See the logs | `docker compose logs -f web` |
| Stop | `docker compose down` |
| Stop and wipe the database | `docker compose down -v` |
| Open a SQL shell | `docker compose exec db psql -U studyboard -d studyboard` |
| Run Ruff | `docker compose run --rm web sh -c "pip install -q --user ruff && python -m ruff check ."` |

The database lives in a Docker volume called `pgdata`, so your sessions are still there after `docker compose down`. Only `down -v` deletes them.

## Environment variables

| Variable | What it does | Local value |
|----------|--------------|-------------|
| `POSTGRES_USER` | Database user | `studyboard` |
| `POSTGRES_PASSWORD` | Database password | `change-me` |
| `POSTGRES_DB` | Database name | `studyboard` |
| `APP_ENV` | Shown in the footer and `/health` | `development` |
| `WEB_PORT` | Port on your laptop | `8000` |
| `GIT_SHA` | Build argument. The pipeline sets it to the commit SHA | `local` |

Staging and Production use the same files with their own `.env` and a real password.

## Project files

```
app.py              Flask routes
db.py               All the SQL (psycopg 3)
validation.py       Form checks, kept separate so it is easy to unit test
init_db.py          Creates the table when the container starts
templates/          HTML pages (Jinja)
static/style.css    Styling
Dockerfile          Builds the web image
docker-compose.yml  Web + PostgreSQL
```

## Pages

| URL | What it does |
|-----|--------------|
| `/` | Upcoming and past sessions. `/?unit=SWE40006` filters |
| `/sessions/new` | Post a session |
| `/sessions/<id>/edit` | Edit a session |
| `/sessions/<id>/delete` | Confirm page, then delete |
| `/rooms` | List of bookable rooms |
| `/rooms/<id>` | Weekly calendar for a room. `?week=2026-10-20` picks the week |
| `/health` | Returns JSON. Checks the database connection |

## Form rules

- Unit code must be 3 letters and 5 numbers, like `SWE40006`. Lowercase is turned into uppercase.
- Topic (max 100 characters) and a room are required.
- Date, start time and end time are required. The end must be after the start, and the session can't be in the past.
- Rooms can be booked between 07:00 and 22:00.
- A booking can't overlap another booking in the same room. Back to back is fine, so 10:00 to 12:00 and 12:00 to 13:00 can both go in.

The rooms are added when the app starts. To change them, edit the `ROOMS` list in `db.py`.

## Common problems

- **Port 8000 already in use:** set `WEB_PORT=8001` in `.env` and open http://localhost:8001.
- **`/health` says the database is unreachable:** run `docker compose ps` and check `db` shows as healthy. `docker compose logs db` shows why it failed.
- **Error about a missing column after pulling new code:** the table layout changed. Run `docker compose down -v` and start again. This deletes your local data.
- **Changed the password in `.env` and now it won't connect:** PostgreSQL only reads the password the first time it creates the volume. Run `docker compose down -v` and start again. This deletes your local data.
