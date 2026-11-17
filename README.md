# CloudLens-AI
CloudLens AI is an AI-powered cloud cost intelligence platform designed to help engineering teams investigate unexpected cloud spending, identify its underlying causes, and make cost optimization decisions without compromising application reliability.

> **Status:** Stage 1 foundation. Authentication, multi-tenant organizations, a cloud-account registry and the dashboard shell work. Billing ingestion, AWS discovery, optimization and AI explanations are **not built yet**; see the [roadmap](docs/implementation-roadmap.md).

## Quick start

```bash
cp .env.example .env        # then set POSTGRES_PASSWORD and JWT_SECRET_KEY (see docs/local-development.md)
docker compose up --build
```

- App: http://localhost:5173
- API docs: http://localhost:8000/api/docs
- Readiness: http://localhost:8000/api/v1/health/ready

## Stack
React, TypeScript, Vite, Tailwind, shadcn/ui, TanStack Query | Python, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | PostgreSQL | Docker Compose. AWS data lake, workers and Terraform arrive in later stages.

## Documentation
- [PROJECT.md](PROJECT.md): product, requirements, scope, ADR index
- [DESIGN.md](DESIGN.md): target technical design
- [docs/architecture.md](docs/architecture.md): what Stage 1 builds and where it deviates
- [docs/database-design.md](docs/database-design.md), [docs/api-design.md](docs/api-design.md)
- [docs/local-development.md](docs/local-development.md): setup, run, test, migrate
- [CLAUDE.md](CLAUDE.md): rules for AI coding assistants

## Core principle
Find the lowest-cost configuration that satisfies every mandatory workload constraint. Never trade away security, availability, performance or reliability to make a recommendation cheaper. Cloud changes always require explicit human approval.
