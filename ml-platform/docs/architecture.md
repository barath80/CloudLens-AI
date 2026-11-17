# ML Platform Architecture

## Boundary
```
Backend (Engineer 2)                          ml-platform (Engineer 1)
--------------------                          ------------------------
CloudWatch/CUR ingestion, storage   -->  validated metric rows (+ ids)
                                              preprocessing -> detection / forecasting
ai_adapter (thin)  <--  AnalysisResult / ForecastResult (signals + evidence ids)
deterministic engine: candidates, constraints, cost, ranking
LLM explanation (validated evidence only)
```
- ML never sees credentials, never calls AWS, never writes to the application database. The backend fetches data and persists results.
- ML never returns authoritative money values and never recommends a specific configuration.
- `ml-platform` must not import `backend/app`; `backend` may import `cloudlens_ml` (library-first).

## Integration shape (proposal, agree with Engineer 2)
Start as an in-process library called from `backend/app/services/ai_adapter/`. Split into a separate service only when a measured need appears (independent scaling, heavy dependencies such as PyTorch, or GPU inference). Keeping the contract in `cloudlens_ml.contracts` makes that split a transport change, not a redesign.

## Layers
1. **Contracts**: Pydantic models, schema-versioned, with validators that forbid inconsistent results (e.g. a positive detection without evidence).
2. **Preprocessing**: rows to a regular grid. Missing stays NaN; out-of-range is rejected, not clipped; duplicates and misaligned timestamps are errors.
3. **Models**: pure functions of a series. Baselines first; a more complex model must beat them under the protocol in [evaluation.md](evaluation.md).
4. **Evaluation**: metrics and a rolling-origin protocol with no look-ahead (tested).
5. **Experiments**: each benchmark writes a JSON run record with dataset hash, git commit, config and metrics.

## Tenant isolation
Not designed yet. Whether models are fitted per tenant or on pooled data is an open decision owned by Engineer 2 (see [issues/pooled-vs-per-tenant.md](issues/pooled-vs-per-tenant.md)). Phase 1 baselines are stateless and use only the one resource's own history, so they carry no cross-tenant risk.
