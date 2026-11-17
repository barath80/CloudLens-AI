# ADR-ML-002: Simulated data policy

Status: accepted

## Context
No real AWS, billing or customer data exists. We still need to build and test the pipeline.

## Decision
Simulated data is allowed for building and testing, under these rules:
1. Generators are deterministic (seed, generator version) and every dataset ships a manifest with `data_source: "simulated"`, the banner, and a content hash.
2. Resource ids are prefixed `sim-`; `DataProvenance.source = simulated` appears on every result built from it.
3. Every benchmark report and run record opens with the banner and carries `evidence_grade: simulated_pipeline_check` and a caveat about circular labels.
4. Simulated results are **never** quoted as accuracy, precision, recall or forecast error of the product. They may only support statements such as "the pipeline runs" or "a spiky workload with a low mean is not flagged".
5. Simulated data is never mixed into a training or evaluation set that contains real data.
6. When real or public-trace data arrives, the same protocol is re-run and only those results are used for performance claims.

## Consequences
Development is unblocked without risking a fabricated performance claim. Cost: Phase 1 conclusions are weak by design; the roadmap treats real data as the gate for Phase 2.
