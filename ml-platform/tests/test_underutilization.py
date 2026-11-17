import numpy as np

from cloudlens_ml.contracts import RecommendationSignal as Sig
from cloudlens_ml.opportunity_detection import detect_underutilization
from tests.helpers import PROV, series

DAYS = 20


def run(values):
    return detect_underutilization(series(values), PROV)


def test_low_steady_cpu_is_flagged_with_evidence():
    r = run([5.0] * (DAYS * 24))
    assert r.detected is True and r.recommendation_signal is Sig.INVESTIGATE_RIGHTSIZING
    assert r.evidence_ids and 0 < r.score <= 1
    assert r.confidence is None and r.confidence_calibrated is False  # uncalibrated: no fake confidence
    assert "memory_metrics_not_evaluated" in r.reasons


def test_low_mean_but_saturating_batch_is_not_flagged():
    """Mean ~14% but CPU hits 90% for 2 hours every day: must NOT be called underutilized."""
    y = [90.0 if (h % 24) in (2, 3) else 5.0 for h in range(DAYS * 24)]
    assert np.mean(y) < 20
    r = run(y)
    assert r.detected is False and r.recommendation_signal is Sig.NO_ACTION
    assert "p95_above_limit" in r.reasons or "p99_above_limit" in r.reasons


def test_single_hour_daily_burst_caught_by_p99():
    y = [95.0 if (h % 24) == 3 else 4.0 for h in range(DAYS * 24)]
    r = run(y)
    assert r.detected is False and "p99_above_limit" in r.reasons


def test_short_window_abstains():
    r = run([3.0] * (5 * 24))
    assert r.detected is None and r.recommendation_signal is Sig.INSUFFICIENT_EVIDENCE
    assert "window_too_short" in r.reasons and r.evidence_ids == [] and r.score is None


def test_low_coverage_abstains():
    y = [3.0] * (DAYS * 24)
    for i in range(0, len(y), 2):
        y[i] = None  # 50% missing
    r = run(y)
    assert r.recommendation_signal is Sig.INSUFFICIENT_EVIDENCE and "coverage_too_low" in r.reasons


def test_long_outage_abstains():
    y = [3.0] * (DAYS * 24)
    y[100 : 100 + 24 * 3] = [None] * (24 * 3)
    r = run(y)
    assert r.recommendation_signal is Sig.INSUFFICIENT_EVIDENCE and "gap_too_long" in r.reasons


def test_all_missing_abstains():
    r = run([None] * (DAYS * 24))
    assert r.recommendation_signal is Sig.INSUFFICIENT_EVIDENCE and "no_data" in r.reasons


def test_missing_values_are_not_treated_as_zero():
    """Same busy data with 5% random gaps must stay not-underutilized; zero-fill would still not flip it
    here, so assert the percentiles come only from observed points."""
    rng = np.random.default_rng(0)
    y = list(rng.uniform(60, 80, DAYS * 24))
    for i in rng.choice(len(y), size=len(y) // 20, replace=False):
        y[i] = None
    r = run(y)
    assert r.observations["p50_cpu"] > 55  # would collapse toward 0 if gaps were zero-filled
    assert r.detected is False


def test_result_carries_provenance_and_version():
    r = run([5.0] * (DAYS * 24))
    assert r.data_provenance.source.value == "simulated"
    assert r.model_version == "underutilization-rule-v1"
