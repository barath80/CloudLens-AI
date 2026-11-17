# CloudLens AI — Project Overview

> Source: *CloudLens AI — Final Technology Stack & Architecture Decisions*, v1.0 (17 Nov 2026).
> Technical detail lives in [DESIGN.md](DESIGN.md); rules for AI assistants in [CLAUDE.md](CLAUDE.md).

## 1. What it is

CloudLens AI is an AWS-first, multi-tenant SaaS platform for cloud cost intelligence. It helps organizations understand cloud expenditure and identify lower-cost configurations **without violating mandatory performance, reliability, compatibility, availability, or security requirements**.

> **Core principle:** find the lowest-cost configuration that satisfies every mandatory workload constraint. Never trade away a requirement to produce a cheaper recommendation.

**Audience:** cloud engineers, FinOps teams, engineering managers.

## 2. Status

The architecture is an **approved design baseline**. It is not a claim that anything is implemented, load-tested or deployed. Stage 1 (foundation) is the current work; see the roadmap below.

## 3. Product requirements

1. Import and reconcile actual billing exports, including updated or corrected data.
2. Discover AWS resources, preserving account, region, identity and configuration context.
3. Collect and retain utilization metrics with observation periods and source provenance.
4. Attribute costs to resources where source data permits; explicitly mark shared or unattributed costs.
5. Retrieve and version public pricing, distinguishing it from customer-specific effective rates.
6. Generate alternative configurations and validate compatibility, workload, security and availability constraints.
7. Calculate costs and savings reproducibly with deterministic backend logic.
8. Explain recommendations with traceable evidence and validated structured AI output.
9. Support multiple organizations with strict tenant isolation and auditable user actions.
10. Require explicit human approval before any cloud modification.
11. Verify post-change performance, reliability and realized savings from subsequent evidence.

## 4. Scope

- **In scope (initial):** AWS only; EC2, EBS and S3 inventory; CUR 2.0 billing; CloudWatch metrics; AWS Price List API.
- **Out of scope / deferred:** other cloud providers, automatic cloud changes (never allowed without approval), self-hosted LLMs, fine-tuning, RAG, Kafka, Kubernetes, microservices.

## 5. Technology summary

| Area | Selection |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui, React Router, TanStack Query, React Hook Form + Zod, Apache ECharts |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Operational DB | PostgreSQL (RDS in production); NUMERIC for money |
| Data lake | S3, Parquet, PyArrow, Polars, Glue Data Catalog, Athena |
| AWS integration | Boto3, STS AssumeRole, CUR 2.0 / Data Exports, CloudWatch, Price List API |
| Background work | SQS (+ DLQ), EventBridge, ECS Fargate workers |
| AI | LLM API first behind an adapter; open-weight, fine-tuning, RAG only when measurement justifies |
| Deployment | Docker, ECS Fargate, RDS, S3 + CloudFront, ECR, Terraform, GitHub Actions |
| Security | IAM, Secrets Manager, KMS, TLS |
| Observability | CloudWatch, OpenTelemetry |
| Testing | Pytest, Vitest, React Testing Library, Playwright, Botocore Stubber / Moto |

## 6. Implementation roadmap

| # | Focus | Key technologies |
|---|---|---|
| 1 | Foundation and domain model | React, TS, Vite, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker |
| 2 | Billing data foundation | CUR 2.0, S3, Parquet, PyArrow, Polars, PostgreSQL summaries |
| 3 | AWS account and inventory integration | STS AssumeRole, Boto3, EC2, EBS, S3 inventory |
| 4 | Metrics and pricing | CloudWatch, workload requirements, Price List API |
| 5 | Analytical querying and cost intelligence | Glue, Athena, attribution and anomaly services |
| 6 | Optimization engine | Candidate generation, constraints, compatibility, Decimal cost calculation |
| 7 | AI and recommendation workflows | LLM API, evidence validation, evaluation dataset, model adapter |
| 8 | Production hardening and deployment | SQS, ECS Fargate, RDS, CloudFront, Terraform, GitHub Actions, monitoring |

The order is a build sequence, not permission to delay foundational decisions: repository and interfaces are designed for the full target architecture while only the current stage is implemented.

## 7. Explicitly deferred or rejected

| Technology | Decision | Reason |
|---|---|---|
| Next.js | Not selected | Client-rendered authenticated dashboard; no SSR/SEO need |
| MongoDB | Not primary DB | Relational integrity and transactions favor PostgreSQL |
| Celery + Redis | Deferred | SQS + Fargate cover async work |
| Kafka | Deferred | No high-throughput streaming requirement |
| Kubernetes / EKS | Not selected | Fargate has lower operational overhead |
| Microservices | Not selected | Modular monolith is simpler at this stage |
| Pandas / NumPy | Optional | Polars is primary; NumPy never for monetary arithmetic |
| LangChain / agent frameworks | Deferred | Direct model integration suffices |
| Vector DB / RAG | Conditional | Only for a demonstrated changing knowledge base |
| ClickHouse, TimescaleDB | Deferred | S3 + Parquet + Athena + PostgreSQL suffice; benchmark first |

## 8. Governance

A proposed substitution must state: (1) the requirement unmet by the current choice, (2) alternatives considered, (3) functional and operational trade-offs, (4) security and data-migration implications, (5) cost and complexity impact, (6) a measurable reason to adopt. Record material changes as ADRs in `docs/adr/` (context, decision, alternatives, consequences, conditions for reconsideration).

| ADR | Decision |
|---|---|
| 001 | React + TypeScript + Vite frontend |
| 002 | Python + FastAPI backend |
| 003 | PostgreSQL + SQLAlchemy 2 + Alembic |
| 004 | S3 + Parquet analytical data lake |
| 005 | Polars + PyArrow processing; Athena + Glue analytics |
| 006 | AWS-first provider adapter architecture |
| 007 | CUR 2.0 billing and CloudWatch metrics sources |
| 008 | STS AssumeRole for customer AWS access |
| 009 | SQS + EventBridge + ECS Fargate background processing |
| 010 | Deterministic optimization with staged, evidence-grounded AI |
| 011 | Modular monolith as initial architecture |
| 012 | ECS Fargate + RDS + Terraform deployment baseline |
| 013 | Human approval required before cloud changes |

## 9. Production-readiness gates

Production readiness must be demonstrated through implementation, security review, representative load tests, billing reconciliation and end-to-end acceptance tests. Capacity claims require benchmarks on representative customer data.

## 10. Glossary

- **CUR 2.0 / Data Exports** — AWS detailed billing export; preferred billing source.
- **Unblended / amortized / net / effective cost** — distinct cost measures; each feature must declare which it uses.
- **Effective rate** — what the customer actually pays (discounts, commitments); differs from public list price.
- **NEEDS_VALIDATION** — candidate status when a mandatory requirement is unknown or evidence is insufficient.
- **Estimated vs realized savings** — projected before a change vs verified from later evidence; stored and shown separately.
- **Evidence object** — bounded, validated facts, calculations, assumptions and source references given to the LLM.
- **Shared / unattributed cost** — cost the export cannot tie to a resource.
