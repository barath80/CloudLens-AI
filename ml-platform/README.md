# CloudLens ML Platform

The intelligence layer of CloudLens AI: it turns validated metric history into **signals with evidence**
(underutilization, forecasts, later anomalies). It does not calculate authoritative costs, decide feasibility,
or authorize change. Those belong to the backend's deterministic engine.

```
ML (this package):   detect -> predict -> classify -> score opportunities
Backend engine:      generate candidates -> validate constraints -> calculate cost -> rank feasible
AI explanation:      explain validated recommendations using evidence
```

> **Status: Phases 0 and 1 complete, on SIMULATED data only.** No real customer or AWS data has been used.
> Nothing here is evidence of real-world accuracy. See [docs/evaluation.md](docs/evaluation.md).

## Layout

| Path | Purpose |
|---|---|
| `cloudlens_ml/contracts/` | Result schemas shared with the backend (versioned, validated) |
| `cloudlens_ml/preprocessing/` | Raw rows to a regular series; gaps stay missing, never zero |
| `cloudlens_ml/opportunity_detection/` | Underutilization rule baseline (`underutilization-rule-v1`) |
| `cloudlens_ml/forecasting/` | Seasonal baselines with empirical prediction intervals |
| `cloudlens_ml/evaluation/` | Metrics (MAE, RMSE, MAPE, coverage, P/R/F1, average precision) |
| `cloudlens_ml/simulation/` | Labelled **simulated** utilization generator |
| `cloudlens_ml/benchmarks/` | Reproducible benchmark runner; writes `experiments/runs/*.json` |
| `datasets/`, `experiments/` | Generated data (git-ignored) and committed run records |
| `docs/` | Architecture, contracts, data requirements, evaluation, roadmap, ADRs |

Not yet created (out of scope until justified): `anomaly_detection/`, `clustering/`, `llm/`, `rag/`.
Subpackages live under one importable package, `cloudlens_ml`, to avoid generic top-level names like `forecasting`.

## Run

```bash
cd ml-platform
python -m venv .venv && .venv/Scripts/activate      # .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
python -m pytest                                    # ~1.5 min; includes a full benchmark run
ruff check .
python -m cloudlens_ml.benchmarks.phase1 [seed]     # prints a report headed by the simulation banner
```

## Rules this package follows
- Missing or insufficient evidence is an explicit outcome (`insufficient_evidence`), never a guess or a zero.
- The signal vocabulary has no "apply" or "resize" value: `investigate_rightsizing`, `no_action`, `insufficient_evidence`.
- `confidence` stays empty until it has been calibrated against real outcomes; models report an uncalibrated `score`.
- Every result names its data source. Simulated data cannot be mistaken for real data.
- It must not import from `backend/app`. The only integration point is `backend/app/services/ai_adapter/` (Engineer 2).
