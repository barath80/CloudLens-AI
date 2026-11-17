# API Design

Base path `/api/v1`. Interactive docs at `/api/docs` (OpenAPI at `/api/openapi.json`). JSON only.

## Conventions
- **Auth:** `Authorization: Bearer <JWT>` (HS256, 60 min default). Tokens carry only the user id; organization access is looked up per request.
- **Tenancy:** tenant resources live under `/organizations/{org_id}/...`. The caller must be a member of that organization. Non-members receive **404**, identical to a missing organization, so IDs cannot be probed.
- **Roles:** `owner`, `admin`, `member`, `viewer`. Writing cloud accounts needs owner or admin; reading needs any role.
- **Errors:** every error uses one shape.

```json
{ "error": { "code": "validation_error", "message": "Request validation failed",
             "details": [{ "field": "password", "message": "String should have at least 12 characters" }] } }
```

| Status | Codes |
|---|---|
| 401 | `unauthorized` |
| 403 | `forbidden` |
| 404 | `not_found` |
| 409 | `email_taken`, `account_exists` |
| 422 | `validation_error` |
| 500 | `internal_error` (no internals leaked) |
| 503 | health endpoints only |

## Endpoints (Stage 1)

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health` | none | Liveness only; touches no dependency |
| GET | `/health/database` | none | `SELECT 1`; 503 if unreachable |
| GET | `/health/ready` | none | All dependencies; 503 if any failed |
| POST | `/auth/register` | none | Creates user, organization and owner membership; returns token |
| POST | `/auth/login` | none | Same error for unknown email and wrong password |
| GET | `/auth/me` | user | User and memberships |
| GET | `/organizations/{org_id}/cloud-accounts` | member | |
| POST | `/organizations/{org_id}/cloud-accounts` | owner/admin | Body: `name`, `account_id` (12 digits), `role_arn`. Generates a unique `external_id` |
| DELETE | `/organizations/{org_id}/cloud-accounts/{id}` | owner/admin | 204 |

Health responses never include connection strings, credentials or exception text.

## Not yet implemented
Role-change and member-invite endpoints, role-ARN verification via STS (cloud accounts stay `pending`), refresh tokens, rate limiting on auth endpoints, and all billing, inventory, recommendation and approval APIs.
