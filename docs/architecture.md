# Architecture (Stage 1)

The full target architecture and its rationale are in [../DESIGN.md](../DESIGN.md); product context in [../PROJECT.md](../PROJECT.md). This page records what Stage 1 actually builds and where it deviates.

## What exists

```
Browser ── React SPA (nginx in Docker) ──HTTP/JSON──▶ FastAPI ──SQLAlchemy──▶ PostgreSQL
```

Backend layers (`backend/app`):

| Layer | Responsibility |
|---|---|
| `api/v1` | Thin routes: parse, authorize through dependencies, delegate |
| `services` | Business rules, transactions, audit entries (`AuthService`, `CloudAccountService`) |
| `repositories` | All queries; tenant data is always organization-scoped |
| `models` / `schemas` | SQLAlchemy tables / Pydantic request and response contracts |
| `core` | Settings, DB session, security, logging, error handling |
| `ai` | Provider interface only. No vendor SDK and no behaviour yet |
| `integrations/aws`, `workers` | Empty packages reserved for later stages |

Frontend (`frontend/src`): `features/` (auth, dashboard, cloud-accounts, placeholders), `components/` (shadcn/ui plus shared state views), `layouts/`, `services/api.ts` (typed endpoints), `lib/api-client.ts` (single fetch wrapper with runtime Zod validation and normalized errors), `app/` (router, providers).

## Deviations from the brief and the decision record
- Monorepo lives at the repository root rather than a nested `cloudlens-ai/` folder.
- Added `backend/pyproject.toml` and `requirements-dev.txt` for ruff and pytest configuration.
- Authentication (register, login, JWT, argon2) is included because users and tenants need it; no refresh tokens or SSO.
- The browser keeps the JWT in `sessionStorage`. This is simple but readable by injected scripts; an httpOnly cookie is the intended hardening.
- Postgres is published on host port 55432 in the author's `.env` because 5432 was blocked; the default stays 5432.
- Both containers run as non-root; the frontend is served by `nginx-unprivileged` on 8080.

## Deliberately not built
Billing ingestion, STS AssumeRole, inventory, CloudWatch, pricing, Athena/Glue, SQS/EventBridge workers, the optimization engine, an LLM provider, Terraform resources, Row-Level Security, CI. Nothing in the UI presents these as working; the pages say so.

## AI boundary
`ExplanationProvider` (`backend/app/ai/provider.py`) is the only seam. The default implementation raises "not configured". When a provider is added it may only explain evidence the deterministic backend produced; it must never calculate totals, generate candidates, judge feasibility or approve changes.
