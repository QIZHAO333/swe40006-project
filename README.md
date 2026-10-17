# SWE40006 Study Board

Study Board is a Flask web application for creating and viewing university study sessions. It supports the SWE40006 Software Deployment and Evolution team project and will be deployed through a complete CI/CD pipeline.

## Planned features

- Create, edit and delete study sessions
- Store unit code, topic, room, date and start time
- Display upcoming and past sessions
- Filter sessions by unit code
- Validate form input and prevent room/time conflicts
- Provide a database-aware `/health` endpoint

## Planned DevOps toolchain

- GitHub for source control and pull requests
- GitHub Actions for CI and automated testing
- Docker and Docker Compose for consistent environments
- PostgreSQL for application data
- AWS EC2 for staging and production
- Amazon CloudWatch for production monitoring

## Current application

The repository currently contains the initial Flask application in `app.py`.

### Run locally

Install Flask, then run:

```powershell
flask --app app run --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000> in a browser. The health endpoint is available at <http://localhost:8000/health>.

## Git workflow

1. Pull the latest `main` branch.
2. Create a feature branch.
3. Commit and push the change.
4. Open a pull request.
5. Ask at least one team member to review it before merging.

Do not commit `.env` files, local databases, credentials or AWS private keys.

