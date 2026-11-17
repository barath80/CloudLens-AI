# Draft GitHub issue: Decide pooled vs per-tenant ML models (tenant isolation)

**Owner:** Engineer 2 (multi-tenancy, backend). **Informed:** Engineer 1 (ML).
**Needed before:** any fitted ML model (Isolation Forest, gradient boosting, clustering, fine-tuned LLM, RAG index) is used with customer data. Not needed for the current stateless baselines.

## Terms
- **Per-tenant model:** one model fitted only on one organization's data and used only for that organization.
- **Pooled model:** one model fitted on data from many organizations, used for all.

## Trade-offs
| | Per-tenant | Pooled |
|---|---|---|
| Isolation | Strong: no cross-tenant data influence | Weak: a model can memorize or leak patterns across tenants |
| Cold start | Poor: new tenants have little history | Good: useful from day one |
| Accuracy | Fits the tenant's own workloads | More data, but workloads may not transfer |
| Cost and ops | Many small models to version, store, retrain | One model, simpler operations |
| Compliance | Easy to explain and to delete a tenant's influence | Needs consent, de-identification and a deletion story |

## Questions to answer
1. Are customers' contracts and our privacy stance compatible with using their data to improve a shared model? Opt-in, opt-out or never?
2. If pooled: what de-identification, aggregation or minimum-tenant thresholds are required? How do we honour a deletion request (retrain, or prove no influence)?
3. If per-tenant: where are models stored, how are they versioned and encrypted, and what happens for tenants with too little history (fall back to stateless baselines)?
4. Hybrid option: pooled model trained only on public traces and simulated priors, then per-tenant calibration. Acceptable?
5. For RAG/LLM: per-tenant document indexes with enforced retrieval filters (already a project rule). Any shared knowledge base limited to public AWS documentation?

## Interim position (no decision needed to proceed)
ML baselines stay stateless and per-resource. No model is fitted across tenants until this issue is resolved.

## Acceptance
A short ADR stating the chosen approach, data-use consent model, storage and deletion behaviour, and the test that proves tenant A's data cannot affect tenant B's outputs.
