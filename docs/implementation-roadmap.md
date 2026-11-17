# Implementation Roadmap

Sequence from the decision record. Each stage should end with tests that pass and an updated doc set.

| # | Stage | Status | Main deliverables |
|---|---|---|---|
| 1 | Foundation and domain model | **Done** | Monorepo, FastAPI, Postgres, Alembic, auth, tenants, cloud-account registry, React shell, Docker Compose, tests |
| 2 | Billing data foundation | Next | CUR 2.0 import, S3 raw zone, Parquet via Polars/PyArrow, idempotent reprocessing, Decimal summaries in Postgres |
| 3 | AWS account and inventory | Planned | STS AssumeRole with external ID and identity verification, Boto3 adapters, EC2/EBS/S3 inventory |
| 4 | Metrics and pricing | Planned | CloudWatch collection with provenance, workload requirements, Price List snapshots (kept separate from effective rates) |
| 5 | Analytical querying | Planned | Glue Data Catalog, Athena, cost attribution (explicit shared/unattributed), anomaly services |
| 6 | Optimization engine | Planned | Detector, generator, compatibility and constraint validators, Decimal cost calculator, ranker with rejection reasons |
| 7 | AI and recommendations | Planned | Provider adapter, evidence object, output validation, evaluation set; open-weight, fine-tuning, RAG only if measured |
| 8 | Production hardening | Planned | SQS/EventBridge/Fargate workers, RDS, CloudFront, Terraform, GitHub Actions, observability |

## Known Stage 1 follow-ups
- Row-Level Security on tenant tables.
- Move the session token to an httpOnly cookie, add refresh tokens and login rate limiting.
- Member invitation and role management; multi-organization switching in the UI.
- CI workflow running backend and frontend checks.
- Split the ~500 kB frontend bundle further (the chart is already lazy-loaded).
- Replace remaining `oxlint` fast-refresh warnings by moving shared helpers out of component files.

## Rules that apply to every stage
Money is `NUMERIC`/`Decimal`. The LLM never calculates or decides. Missing metrics are not zero. Tenant access is organization-scoped and tested. Every stack change is recorded as an ADR in `docs/adr/`.
