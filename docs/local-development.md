# Local Development

Prerequisites: Docker with Compose v2, Python 3.12, Node 24+ (only for running outside Docker).

## 1. Configure

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(24))"   # -> POSTGRES_PASSWORD (also put it in DATABASE_URL)
python -c "import secrets; print(secrets.token_urlsafe(48))"   # -> JWT_SECRET_KEY (must be >= 32 chars)
```

`.env` is git-ignored. The backend refuses to start with a missing or weak `JWT_SECRET_KEY`. If host port 5432 is
taken or blocked (it is on some Windows machines), change `POSTGRES_PORT` and the port in `DATABASE_URL`.
Use `127.0.0.1` rather than `localhost` in `DATABASE_URL`; `localhost` can resolve to IPv6 and hang.

## 2. Run everything in Docker

```bash
docker compose up --build                     # db -> backend (runs migrations) -> frontend
# development with hot reload:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000/api/v1 (docs at `/api/docs`) |
| PostgreSQL | 127.0.0.1:`POSTGRES_PORT` (data in the `pgdata` volume) |

Check: `curl http://127.0.0.1:8000/api/v1/health/ready`. Reset the database with `docker compose down -v`.

## 3. Run services on the host

```bash
docker compose up -d db

cd backend
python -m venv .venv && .venv/Scripts/activate          # Windows; use .venv/bin/activate elsewhere
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload

cd frontend
npm ci
npm run dev
```

## 4. Tests and checks

```bash
# backend (needs the db service running; uses a separate `cloudlens_test` database)
cd backend && python -m pytest && ruff check .

# frontend
cd frontend
npm run typecheck && npm test && npm run lint && npm run build
npx playwright install chromium    # once
npm run e2e                        # smoke tests, backend mocked
```

## 5. Migrations

```bash
cd backend
alembic revision --autogenerate -m "describe change"   # review the generated file before committing
alembic upgrade head
alembic downgrade -1
```

The test suite fails if the models and migrations drift apart. Never edit the schema by hand.
