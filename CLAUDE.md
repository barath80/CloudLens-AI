# CLAUDE.md

CloudLens AI: AWS-first, multi-tenant SaaS for cloud cost intelligence. Finds the lowest-cost configuration that satisfies **every** mandatory workload constraint. Details: [PROJECT.md](PROJECT.md) (what/why), [DESIGN.md](DESIGN.md) (how), [docs/](docs/).

Status: greenfield, Stage 1 foundation. The architecture is an approved baseline, not an implemented system. Never describe unbuilt features as working.

## Stack (approved baseline)
- Frontend: React, TypeScript (strict), Vite, Tailwind, shadcn/ui, React Router, TanStack Query, React Hook Form + Zod, Apache ECharts
- Backend: Python, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL
- Later: S3/Parquet/Polars/Athena, Boto3 + STS, SQS/EventBridge/ECS Fargate, Terraform
- Tests: Pytest, Vitest, React Testing Library, Playwright
- Do not add Redis, Celery, Kafka, Kubernetes, vector DBs, agent frameworks, or microservices without a documented requirement and an ADR in `docs/adr/`.

## Non-negotiable rules
- Money: PostgreSQL `NUMERIC` and Python `Decimal` only. Never float.
- The LLM never calculates financial totals, generates candidates, decides feasibility, or approves changes. Those are deterministic backend code. Model output is schema- and evidence-validated; the deterministic result is always preserved.
- Never treat missing metrics as zero. Never recommend rightsizing from average CPU alone. Unknown mandatory requirement ⇒ `NEEDS_VALIDATION`.
- Never use public list prices as a substitute for the customer's actual billing rates.
- Store and show estimated and realized savings separately.
- No cloud modification without explicit human approval.
- Tenant isolation: every query on tenant data is organization-scoped; add cross-tenant tests.
- Secrets never go in git, the frontend, logs, or queue messages. Don't store customers' permanent AWS keys (STS AssumeRole with external ID only).
- Schema changes only through Alembic migrations.
- Workers must be idempotent; queue messages carry ids, not data.
- Tests must never touch production cloud resources.

## Conventions
- Backend: routes are thin (validate, delegate); business logic in `services/`; DB access in `repositories/`; use FastAPI `Depends` for injection; type hints everywhere; parameterized queries; JSONB only for flexible provider metadata.
- Frontend: feature-oriented folders; server state via TanStack Query; no authoritative cost or savings calculation in the browser; every major screen has loading, error and empty states; validate untrusted network data at runtime.
- Keep AWS-specific logic behind adapters in `backend/app/integrations/aws`.
- Demo data must be clearly labelled as a placeholder, never presented as real customer data.
- Match surrounding code style; avoid unnecessary dependencies; don't ship placeholder code disguised as finished features.
- When the stack or an architectural decision changes, update PROJECT.md / DESIGN.md and add an ADR.

## Commands
Full setup in [docs/local-development.md](docs/local-development.md). Verified commands:

- Run all: `docker compose up --build` (needs `.env` from `.env.example`)
- Backend (from `backend/`, venv active, db service running): `python -m pytest`, `ruff check .`, `alembic upgrade head`, `alembic revision --autogenerate -m "msg"`
- Frontend (from `frontend/`): `npm run typecheck`, `npm test`, `npm run lint`, `npm run build`, `npm run e2e`
- Use `127.0.0.1`, not `localhost`, in `DATABASE_URL` (IPv6 resolution can hang).
- UI components come from shadcn/ui (`npx shadcn@latest add <name>`); they use the `cn` helper in `src/lib/utils.ts` (clsx + tailwind-merge). Do not install the npm package named `cn`.
