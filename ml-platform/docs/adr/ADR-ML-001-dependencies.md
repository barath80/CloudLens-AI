# ADR-ML-001: Minimal dependencies, with explicit triggers for more

Status: accepted (Phase 0/1)

## Context
The core stack lists Polars and PyArrow and treats NumPy as optional. The ML brief names scikit-learn, LightGBM, statsmodels, Prophet, PyTorch, Transformers, PEFT, TRL, bitsandbytes, vLLM, MLflow, sentence-transformers, FAISS. Adding them now would add weight and attack surface with no measured benefit.

## Decision
`ml-platform` is its own package with its own environment; none of its dependencies enter the backend image. Current runtime dependencies:

| Package | Why |
|---|---|
| pydantic | Result contracts and validation (already in the core stack) |
| polars | Frame handling (already in the core stack) |
| numpy | Percentiles and rolling forecast arithmetic. Not used for authoritative money (see contracts decision 4) |
| tzdata | Windows has no IANA tz database; Polars needs one for tz-aware timestamps |

## Deferred, with the trigger that justifies each
| Package | Trigger |
|---|---|
| scikit-learn | A baseline is beaten on a G2+ dataset by Isolation Forest, LOF, K-Means or DBSCAN, with margin |
| statsmodels / Prophet | Seasonal baselines show a repeatable gap on real data that ETS or SARIMA closes |
| LightGBM / XGBoost | Outcome labels exist and a tabular classifier beats the rule baseline |
| MLflow | More than one contributor writing runs, or hyperparameter search. Until then JSON run records are committed |
| torch, transformers, peft, trl, bitsandbytes, vllm | Phase 3 failure analysis shows API prompting is insufficient (quality, cost, latency or data governance) |
| sentence-transformers, FAISS, pgvector | Phase 3/4 shows retrieval is needed and keyword/SQL search measurably fails |

## Consequences
Smaller, auditable surface and faster CI. Cost: the first non-trivial model requires an ADR update and a short review.
