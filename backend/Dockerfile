FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY app ./app
COPY migrations ./migrations

RUN useradd --system --uid 10001 cloudlens && chown -R cloudlens /srv/app
USER cloudlens
EXPOSE 8000

# Apply migrations, then serve. Fails fast (container exits) if the schema cannot be migrated.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
