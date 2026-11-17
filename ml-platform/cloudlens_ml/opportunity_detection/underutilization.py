"""Rule-based underutilization signal (baseline v1).

This is a *signal*, not a recommendation to resize. It says "the CPU evidence is consistent with an
oversized resource, investigate". Whether a smaller configuration is feasible, compatible and cheaper
is decided by the backend's deterministic engine.

Decision rule uses tail percentiles, never the mean: a batch workload can have a tiny mean and still
saturate the CPU for an hour a day. Memory, network and IO are not evaluated here and the result says so.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from cloudlens_ml.contracts import (
    AnalysisResult,
    AnalysisType,
    DataProvenance,
    RecommendationSignal,
)
from cloudlens_ml.preprocessing import Series, quality, window

MODEL_VERSION = "underutilization-rule-v1"


@dataclass(frozen=True)
class UnderutilizationConfig:
    """Defaults are placeholders pending a product decision, not tuned values.

    They are not fitted to any dataset. Changing them changes `model_version` semantics, so bump it.
    """

    min_days: float = 14.0
    min_coverage: float = 0.90
    max_gap_days: float = 2.0
    p95_limit: float = 30.0
    p99_limit: float = 60.0


def detect_underutilization(
    series: Series,
    provenance: DataProvenance,
    *,
    config: UnderutilizationConfig = UnderutilizationConfig(),  # noqa: B008 - frozen, safe as default
    evidence_ids: Sequence[str] | None = None,
) -> AnalysisResult:
    q = quality(series)
    w = window(series)
    ppd = series.points_per_day
    observed_days = q.observed_points / ppd
    ids = (
        list(evidence_ids)
        if evidence_ids
        else [
            f"{provenance.dataset_id}:{series.resource_id}:{series.metric}:{w.start.isoformat()}/{w.end.isoformat()}"
        ]
    )
    reasons = ["memory_metrics_not_evaluated"]

    insufficient: list[str] = []
    if q.observed_points == 0:
        insufficient.append("no_data")
    else:
        if w.days < config.min_days or observed_days < config.min_days * config.min_coverage:
            insufficient.append("window_too_short")
        if q.coverage < config.min_coverage:
            insufficient.append("coverage_too_low")
        if q.longest_gap_points / ppd > config.max_gap_days:
            insufficient.append("gap_too_long")

    def result(
        detected: bool | None,
        signal: RecommendationSignal,
        obs: dict[str, float],
        score: float | None,
        why: list[str],
    ):
        return AnalysisResult(
            resource_id=series.resource_id,
            analysis_type=AnalysisType.UNDERUTILIZATION,
            detected=detected,
            score=score,
            observations=obs,
            recommendation_signal=signal,
            evidence_ids=ids if detected else [],
            reasons=why + reasons,
            observation_window=w,
            data_quality=q,
            data_provenance=provenance,
            model_version=MODEL_VERSION,
        )

    if insufficient:
        return result(
            None,
            RecommendationSignal.INSUFFICIENT_EVIDENCE,
            {"observation_days": round(observed_days, 3), "coverage": round(q.coverage, 4)},
            None,
            insufficient,
        )

    v = series.values[~np.isnan(series.values)]
    p50, p95, p99 = (float(x) for x in np.quantile(v, [0.5, 0.95, 0.99]))
    obs = {
        "mean_cpu": round(float(v.mean()), 3),  # reported for context; never used in the decision
        "p50_cpu": round(p50, 3),
        "p95_cpu": round(p95, 3),
        "p99_cpu": round(p99, 3),
        "max_cpu": round(float(v.max()), 3),
        "observation_days": round(observed_days, 3),
        "coverage": round(q.coverage, 4),
    }
    p95_ok, p99_ok = p95 <= config.p95_limit, p99 <= config.p99_limit
    if p95_ok and p99_ok:
        margin = min((config.p95_limit - p95) / config.p95_limit, (config.p99_limit - p99) / config.p99_limit)
        return result(
            True,
            RecommendationSignal.INVESTIGATE_RIGHTSIZING,
            obs,
            float(np.clip(margin, 0, 1)),
            ["p95_below_limit", "p99_below_limit"],
        )

    why = [] + ([] if p95_ok else ["p95_above_limit"]) + ([] if p99_ok else ["p99_above_limit"])
    return result(False, RecommendationSignal.NO_ACTION, obs, 0.0, why)
