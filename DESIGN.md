# CloudLens AI — Technical Design

> Companion to [PROJECT.md](PROJECT.md). Items marked **(proposed)** are not in the decision record and may change; everything else is an approved decision. Detail docs: [docs/](docs/).

## 1. Architecture style

AWS-first **modular monolith**. One FastAPI application plus independently scaled worker containers built from the same codebase. Modules are split by domain, not deployed separately without a measured reason. Provider-specific AWS logic sits behind adapters exposing normalized internal contracts so other clouds can be added later.

## 2. Runtime flow

```
React SPA ──HTTPS──▶ FastAPI (auth, RBAC, org scoping, job metadata)
                         │                     │
                         ▼                     ▼
                    PostgreSQL ◀──────── SQS ──▶ ECS Fargate workers
              (operational truth)          ▲        │  STS AssumeRole + Boto3
                         ▲        EventBridge       ▼
                         │         (schedules)   Customer AWS (inventory, CloudWatch)
                         │
   CUR 2.0 ─▶ S3 raw ─▶ ingestion ─▶ S3 curated Parquet ◀── Athena + Glue
                         │
        pricing + billing evidence ─▶ optimization engine ─▶ evidence object
                                                              │
                                      LLM adapter (explanation only) ─▶ validated output
                                                              │
                                      human approve/reject ─▶ audit trail ─▶ post-change verification
```

1. SPA calls versioned FastAPI endpoints.
2. FastAPI authenticates, checks org permissions, persists job metadata, queues long work.
3. EventBridge schedules recurring jobs; SQS delivers to Fargate workers.
4. Workers assume customer roles and pull inventory and CloudWatch data.
5. CUR 2.0 lands in S3; ingestion validates, normalizes, writes curated Parquet.
6. Athena queries large history; PostgreSQL holds operational records and dashboard summaries.
7. Pricing and billing evidence feed deterministic attribution and optimization.
8. Constraint engine filters infeasible candidates; cost engine ranks feasible ones.
9. Evidence generator builds a traceable recommendation; the AI layer explains it; backend validates the output.
10. Customer approves or rejects; decision and audit trail are recorded.
11. After a change is made under controlled procedures, post-change metrics and later billing verify realized savings.

## 3. Module layout (proposed)

Backend `app/`: `api/v1` (thin routes), `core` (config, db, security, logging, errors), `models`, `schemas`, `repositories` (all DB access, org-scoped), `services` (business logic), `integrations/aws` (adapters), `workers`, `ai` (provider interface), `utils`. Later domain packages: billing, inventory, metrics, pricing, optimization, recommendations, approvals.

Rules: routes validate and delegate; services hold business logic; repositories own queries; dependencies injected via FastAPI `Depends`.

## 4. Data architecture

| Store | Holds |
|---|---|
| PostgreSQL | users, orgs, memberships, cloud-account metadata, resource metadata, import metadata, derived summaries, pricing metadata, recommendations, approvals, audit events, authoritative job state |
| S3 + Parquet | original billing exports, raw metric/resource snapshots, normalized analytical datasets, pricing snapshots, archived evidence |

- **Placement rule:** raw billing and metric facts → S3/Parquet; application entities and derived summaries → PostgreSQL; Athena queries S3; PostgreSQL is the system of record.
- Relational constraints and FKs on key relationships; transactions around approvals, status changes, reconciliation.
- JSONB only for flexible provider-specific metadata.
- Money: PostgreSQL `NUMERIC` and Python `Decimal`. Never float. Polars/PyArrow are for transformation, not financial precision.
- S3: preserve source objects with checksums, import ids, timestamps, schema versions; separate raw / validated / curated; encryption, least-privilege policies, lifecycle and retention.
- Tenant isolation: organization-scoped queries now; Row-Level Security where appropriate (deferred past Stage 1). Indexes and partitioning only once data volume justifies them.
- Migrations only through Alembic.

## 5. AWS integration

- Customer creates a least-privilege **read-only cross-account IAM role** with a **unique external ID** per trust relationship.
- Backend calls STS AssumeRole, uses temporary credentials only, **verifies the assumed account identity** before accepting the connection, never stores permanent keys, never exposes credentials to the browser, audits connection events.
- Billing: CUR 2.0 / Data Exports (export configuration and resource-level availability verified per customer).
- Metrics: CloudWatch; memory metrics may need the CloudWatch Agent.
- Pricing: Price List API is public list pricing only — not the customer's effective rate.

### Billing accuracy rules
Preserve originals and provenance; idempotent reprocessing for late or corrected records; never double-count redelivered exports; declare the cost measure each feature uses; handle credits, refunds, discounts, commitments and currency where data allows; mark attribution unavailable/shared when resource ids are missing.

## 6. Background processing

SQS queues (with DLQs) for imports, inventory scans, metrics collection, investigations; EventBridge for schedules; Fargate workers scaled separately from the API. Workers are idempotent, use visibility timeouts and bounded retries, write explicit failure states. Job status lives in PostgreSQL. Messages carry ids/references, never large datasets or secrets; large payloads go via S3. Step Functions deferred. Celery/Redis not used.

## 7. Optimization engine (deterministic Python)

| Component | Responsibility |
|---|---|
| Opportunity Detector | find potential waste from validated evidence |
| Candidate Generator | alternatives from supported catalogs and rules |
| Compatibility Validator | architecture, region, platform, storage compatibility |
| Workload Constraint Engine | mandatory utilization, latency, availability, security constraints |
| Cost Calculator | comparable full costs from verified pricing and billing assumptions |
| Candidate Ranker | lowest-cost feasible candidate; preserve rejection reasons |

Unknown mandatory requirement or insufficient evidence ⇒ `NEEDS_VALIDATION` or rejected. Average CPU alone never justifies rightsizing; missing metrics are never treated as zero. Every recommendation stores evidence, assumptions, calculation version and rejection reasons. Estimated and realized savings are stored separately.

## 8. AI layer

- Stage-gated: **LLM API with structured outputs** → evaluate open-weight models → fine-tune only on a measured gap → RAG only for a changing knowledge base (vector index only if it beats keyword/SQL search).
- Provider and runtime sit behind an internal adapter (`app/ai`), so swapping API for open-weight needs no change to product services.
- Input is a bounded **evidence object** (verified facts, calculations, assumptions, quality indicators, source refs). The model summarizes and explains trade-offs only.
- Output is schema-validated and evidence-reference-validated; unsupported claims are rejected; the deterministic result is always preserved.
- The LLM **never** calculates financial totals, invents candidates, decides feasibility, or approves changes.

## 9. Frontend

React + TypeScript (strict) + Vite SPA; Tailwind + shadcn/ui; React Router; TanStack Query for server state (no extra client-state library until needed); React Hook Form + Zod for forms (backend validation stays authoritative); ECharts for time series. Feature-oriented folders, business rules out of presentation components, accessible loading/error/empty/success states, typed API contracts aligned with backend schemas, **no authoritative cost or savings math in the browser**.

Visual design tokens (colors, type scale) — **TBD**; start from shadcn defaults and adapt to a clean enterprise SaaS look. Demo data must be labelled as placeholders.

## 10. Security and governance

| Concern | Decision |
|---|---|
| Authentication | secure session/token auth with password controls |
| Authorization | backend-enforced RBAC, org-scoped |
| Tenant isolation | org-scoped queries + DB safeguards; explicit cross-tenant tests |
| AWS permissions | least-privilege read-only roles |
| Secrets | Secrets Manager; never committed, never in frontend or queue messages |
| Encryption | TLS in transit; KMS at rest |
| Audit | connections, imports, investigations, approvals, privileged actions |
| Human control | no automatic production changes |
| Reliability | idempotent jobs, retries, DLQs, backups, monitoring |

## 11. Environments and deployment

Local: Docker Compose, mocked AWS where practical. Dev and staging: isolated AWS resources, staging production-like. Production: ECS Fargate, private RDS, encrypted S3, managed queues, backups, controlled releases. Docker images in ECR; frontend on S3 + CloudFront; Terraform for infra; GitHub Actions for lint/test/build/security/deploy; CloudWatch + OpenTelemetry for observability. Databases and worker control interfaces are never public.

## 12. Testing

Pytest (backend, financial, validation), Vitest + RTL (frontend), Playwright (E2E), Botocore Stubber or Moto (AWS mocks). Deterministic fixtures with manually verified expectations. Mandatory areas: billing duplicates/corrections/credits/currency, resource-billing mapping, missing/stale metrics, percentile utilization, regional pricing, constraint violations, Decimal rounding and reproducibility, unsupported AI claims, tenant isolation and permissions, approvals and savings reconciliation. Tests never modify production cloud resources.
