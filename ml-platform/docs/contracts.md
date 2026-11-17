# Integration Contract v0.1 (DRAFT for Engineer 2 review)

Source of truth: `cloudlens_ml/contracts/results.py`. Schema version `0.1.0`. This is a proposal; nothing in the backend depends on it yet.

## Calling the library
```python
series = build_series(rows, resource_id=..., metric="cpu_utilization_percent", step_minutes=60)
result = detect_underutilization(series, provenance, evidence_ids=[...backend metric record ids...])
fc     = forecast(series, model="seasonal_mean_daily_7", horizon=24, provenance=provenance)
```
`rows` is a Polars frame with `timestamp` (tz-aware UTC, aligned to the step) and `value` (null = missing).

## AnalysisResult

| Field | Meaning |
|---|---|
| `schema_version`, `model_version` | Contract and model versions; stored with every recommendation for reproducibility |
| `resource_id`, `analysis_type` | What was analysed (`underutilization`, `forecast`, `anomaly`) |
| `detected` | `true`, `false`, or `null` when evidence was insufficient |
| `recommendation_signal` | `investigate_rightsizing` \| `no_action` \| `insufficient_evidence`. Closed set; no change-authorizing value exists |
| `score` | Uncalibrated 0-1 ranking value. **Not a probability** |
| `confidence`, `confidence_calibrated` | `confidence` is only allowed when calibrated. Stays `null` until validated on real outcomes |
| `observations` | Numeric facts used (percentiles, days, coverage). Mean is reported for context only |
| `evidence_ids` | Backend metric record ids the result rests on. Required when `detected` is true |
| `reasons` | Machine-readable codes (`p99_above_limit`, `window_too_short`, `memory_metrics_not_evaluated`, ...) |
| `observation_window`, `data_quality` | Time span, coverage, longest gap, rejected points |
| `data_provenance` | `simulated` \| `public_trace` \| `customer`, dataset id and version |

Differences from the earlier illustrative example: `confidence` is nullable and gated; `score`, `reasons`, `data_quality`, `observation_window`, `data_provenance` and an explicit `insufficient_evidence` outcome were added.

Consistency rules enforced by validators: `detected=null` iff `insufficient_evidence`; `detected=false` requires `no_action`; `detected=true` requires evidence ids; results are immutable.

## ForecastResult
Timestamps, `point`, `lower`, `upper` (equal length; `null` where no prediction is possible), `interval_level`, `interval_method`, plus the same evidence/quality/provenance fields. Intervals are empirical residual quantiles from earlier day-ahead errors on the training history; their real coverage is measured in the benchmark, not assumed.

## Decisions needed from Engineer 2
1. **Location and style**: confirm `backend/app/services/ai_adapter/` and in-process library use for now.
2. **Evidence ids**: what identifies a metric record? Results should echo the backend's ids, not invent them. Until agreed, the library derives `dataset:resource:metric:window` ids.
3. **Who owns thresholds** (`p95_limit=30`, `p99_limit=60`, `min_days=14`, `min_coverage=0.9`)? They are placeholders, not tuned. They are product policy and should be configurable per organization or workload class.
4. **Money and floats**: the backend rule is Decimal/NUMERIC only. Statistical anomaly detection on cost series needs floating-point math. Proposal: floats only inside detection statistics, and results carry no money amounts, only ids and relative measures. Needs explicit agreement.
5. **Persistence**: ML returns results and the backend stores them (with `model_version`). Confirm ML never writes to PostgreSQL.
6. **Schema evolution**: additive changes bump the minor version; field removal or meaning changes bump the major version and need coordination.
7. **Change points**: resize, stop/start and instance-type changes must reach ML as events, otherwise a forecast or percentile may span two different machines.
