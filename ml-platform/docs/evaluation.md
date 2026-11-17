# Evaluation and Experiment Strategy

## Evidence grades (every reported number must state its grade)

| Grade | Data | What it can support |
|---|---|---|
| G0 | Unit tests, hand-computed fixtures | Code is correct |
| G1 | **Simulated** data with generator labels | Pipeline runs, is deterministic, behaves as designed on constructed cases. **Not** accuracy |
| G2 | Public real traces (not AWS, not CloudLens) | Generic behaviour on real workloads; labelled as non-CloudLens |
| G3 | Real customer data, retrospective | Offline performance estimate |
| G4 | Prospective, outcome-verified (recommendation applied and measured) | Real-world performance claim |

Current results are **G1 only**. Claims of "works" require G3 or better.

## Protocol
- **Time-ordered evaluation only**: rolling origin; history never includes the forecast window (a test mutates the future and asserts identical forecasts).
- **Baselines first**: a model is adopted only if it beats the best simple baseline on the agreed metric across folds, with the margin reported. The naive mean-only detector is kept as a standing comparison.
- **Leakage checks**: no random shuffles on time series; no features computed over the full series; tenant/resource-disjoint splits once supervised models exist.
- **Metrics**: detection precision, recall, F1, average precision (PR-AUC proxy); forecasting MAE, RMSE, MAPE (only where actual >= 1% to avoid division blow-up) and **empirical interval coverage versus nominal**; abstention rate and wrong-abstention rate; prediction availability.
- **Missing data**: NaN pairs are excluded and reported; never zero-filled.
- **Later**: Recall@K and MRR for retrieval, factuality and citation support for LLM output, latency and cost, drift monitoring.

## Experiment tracking
Each benchmark writes `experiments/runs/<name>.json` containing: simulation banner, evidence grade, dataset manifest (seed, generator version, sha256), git commit, config, metrics and a caveat. Run records are committed so results are reviewable. MLflow is deferred until multiple people write runs or hyperparameter search appears (ADR-ML-001).

## Known limitations of the current G1 benchmark
- Detection labels come from the generator's own assumptions, so perfect agreement is partly circular. The informative result is the comparison against the mean-only baseline and correct abstention, both true by construction.
- Forecast errors reflect simulated seasonality. The ranking of baselines may change on real workloads.
- Thresholds are untuned placeholders.
