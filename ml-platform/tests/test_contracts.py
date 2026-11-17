import pytest
from pydantic import ValidationError

from cloudlens_ml.contracts import (
    AnalysisResult,
    AnalysisType,
    DataQuality,
    ObservationWindow,
    RecommendationSignal,
)
from tests.helpers import PROV, T0

W = ObservationWindow(start=T0, end=T0, days=0)
Q = DataQuality(expected_points=1, observed_points=1, coverage=1.0, longest_gap_points=0)


def make(**kw):
    base = dict(
        resource_id="r",
        analysis_type=AnalysisType.UNDERUTILIZATION,
        detected=False,
        recommendation_signal=RecommendationSignal.NO_ACTION,
        observation_window=W,
        data_quality=Q,
        data_provenance=PROV,
        model_version="t",
    )
    base.update(kw)
    return AnalysisResult(**base)


def test_valid_negative_result():
    assert make().detected is False


def test_positive_detection_requires_evidence():
    with pytest.raises(ValidationError):
        make(detected=True, recommendation_signal=RecommendationSignal.INVESTIGATE_RIGHTSIZING)
    assert make(
        detected=True, recommendation_signal=RecommendationSignal.INVESTIGATE_RIGHTSIZING, evidence_ids=["e1"]
    )


def test_insufficient_evidence_must_have_no_verdict():
    with pytest.raises(ValidationError):
        make(detected=False, recommendation_signal=RecommendationSignal.INSUFFICIENT_EVIDENCE)
    with pytest.raises(ValidationError):
        make(detected=None, recommendation_signal=RecommendationSignal.NO_ACTION)
    assert make(detected=None, recommendation_signal=RecommendationSignal.INSUFFICIENT_EVIDENCE)


def test_confidence_requires_calibration():
    with pytest.raises(ValidationError):
        make(confidence=0.9)
    assert make(confidence=0.9, confidence_calibrated=True).confidence == 0.9


def test_signal_vocabulary_cannot_authorize_change():
    allowed = {s.value for s in RecommendationSignal}
    assert allowed == {"investigate_rightsizing", "no_action", "insufficient_evidence"}


def test_results_are_immutable():
    with pytest.raises(ValidationError):
        make().detected = True
