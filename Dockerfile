FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home appuser
COPY --chown=appuser . .

ARG GIT_SHA=local
ENV GIT_SHA=$GIT_SHA

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python init_db.py && gunicorn app:app --bind 0.0.0.0:8000 --access-logfile - --access-logformat '%(h)s \"%(r)s\" %(s)s %(M)sms'"]
