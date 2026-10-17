FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The pipeline passes the commit SHA in, so the footer and /health show
# which version is running
ARG GIT_SHA=local
ENV GIT_SHA=$GIT_SHA

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Create the table first, then start gunicorn.
# The access log prints the request time in ms (%(M)s) at the end of each
# line, so CloudWatch can turn it into a latency metric later.
CMD ["sh", "-c", "python init_db.py && exec gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --access-logfile - --access-logformat '%(h)s \"%(r)s\" %(s)s %(M)sms'"]
