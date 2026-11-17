# ML Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Architecture, contracts, data requirements, evaluation strategy, dependency ADRs, package scaffold | **Done** |
| 1 | Utilization pipeline on simulated data: preprocessing, underutilization rule baseline, forecasting baselines, metrics, benchmark and run records | **Done (G1 evidence only)** |
| 2 | Cost anomaly detection (robust statistical baselines first, then Isolation Forest if it beats them) and spend forecasting | Blocked on real CUR data; G2 public traces can unblock utilization work |
| 3 | LLM baseline: API provider behind `ExplanationProvider`, evaluation set of validated evidence objects, factuality and citation checks | Needs backend evidence objects |
| 4 | Escalation only on evidence: open-weight evaluation, then LoRA/QLoRA, then RAG with tenant-isolated retrieval | Gated by Phase 3 failure analysis |

## Next concrete steps
1. Engineer 2 reviews `docs/contracts.md` and answers the seven decisions.
2. Obtain one real dataset (see `data-requirements.md`) or approve G2 public-trace evaluation.
3. Add a G2 loader (public VM utilization trace) and re-run the Phase 1 protocol on it.
4. Calibrate or remove `score` once outcome labels exist.
5. Decide per-tenant vs pooled modelling before any fitted model ships.
