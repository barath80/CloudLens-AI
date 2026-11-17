# Database Design

PostgreSQL via SQLAlchemy 2; schema owned by Alembic (`backend/migrations`). Initial migration: `0001`.

## Conventions
- UUID primary keys (`uuid4`, generated in the application).
- `created_at` / `updated_at` as `timestamptz` with server defaults.
- Foreign keys with explicit `ON DELETE` behaviour. Enums stored as constrained strings (`native_enum=False`) so adding a value is a simple migration.
- Money columns, when introduced, must be `NUMERIC` with Python `Decimal`; none exist yet.
- JSONB only for flexible metadata (`audit_logs.details`).

## Tables

```
users ──< organization_members >── organizations
                                        │
                                        ├──< cloud_accounts
                                        └──< audit_logs >── users (actor)
```

| Table | Key columns | Constraints and indexes |
|---|---|---|
| `users` | `email`, `password_hash` (argon2), `full_name`, `is_active` | unique index on `email` (stored lower-case) |
| `organizations` | `name`, `slug` | unique index on `slug` |
| `organization_members` | `organization_id`, `user_id`, `role` | unique (`organization_id`, `user_id`); FKs cascade; indexes on both FKs |
| `cloud_accounts` | `organization_id`, `provider`, `account_id`, `name`, `role_arn`, `external_id`, `status` | unique (`organization_id`, `provider`, `account_id`); unique `external_id`; FK cascade |
| `audit_logs` | `organization_id?`, `actor_user_id?`, `action`, `target_type?`, `target_id?`, `details` JSONB | index (`organization_id`, `created_at`); index on `action`; FKs `SET NULL` so history survives deletions |

## Tenant isolation
- Repositories for tenant data take `organization_id` on every query (`CloudAccountRepository`).
- The API resolves membership once per request (`get_org_member`) and passes the membership down.
- The same AWS account may be registered by different organizations; uniqueness is per organization.
- Cross-tenant tests live in `backend/tests/test_cloud_accounts.py`.
- **Not yet done:** PostgreSQL Row-Level Security as a second layer. Planned before the first sensitive billing data lands.

## Security notes
- `cloud_accounts` stores a role ARN and external ID only. No AWS credentials are ever stored.
- `audit_logs` is append-only by convention. Database-level enforcement (revoked UPDATE/DELETE) is deferred.

## Prepared for later stages
Billing imports and summaries, resources, metric summaries, pricing snapshots, recommendations, approvals and job state will be added as new migrations. Raw billing and metric facts go to S3/Parquet, not PostgreSQL.
