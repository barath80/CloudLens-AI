"""Integration contract v0.1: what ml-platform returns to the backend.

Design rules (see docs/contracts.md):
- Results are *signals with evidence*, never decisions. Feasibility, cost and approval belong to the
  deterministic backend engine.
- Missing or insufficient evidence is an explicit outcome (`insufficient_evidence`), not a guess.
- `confidence` is only populated when it has been calibrated against labelled outcomes. Until then a
  model reports an uncalibrated `score` for ranking.
- Every result states where its data came from. Simulated data can never be mistaken for real data.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "0.1.0"


class AnalysisType(StrEnum):
    UNDERUTILIZATION = "underutilization"
    FORECAST = "forecast"
    ANOMALY = "anomaly"


class RecommendationSignal(StrEnum):
    """Closed vocabulary. There is deliberately no "apply"/"resize" value: ML cannot authorize change."""

    INVESTIGATE_RIGHTSIZING = "investigate_rightsizing"
    NO_ACTION = "no_action"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class DataSource(StrEnum):
    SIMULATED = "simulated"
    PUBLIC_TRACE = "public_trace"
    CUSTOMER = "customer"


class DataProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: DataSource
    dataset_id: str
    dataset_version: str | None = None
    note: str | None = None


class DataQuality(BaseModel):
    model_config = ConfigDict(frozen=True)

    expected_points: int = Field(ge=0)
    observed_points: int = Field(ge=0)
    coverage: float = Field(ge=0, le=1)
    longest_gap_points: int = Field(ge=0)
    invalid_points: int = Field(
        default=0, ge=0, description="Present but rejected (e.g. out of range); treated as missing"
    )


class ObservationWindow(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: datetime
    end: datetime
    days: float = Field(ge=0)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = SCHEMA_VERSION
    resource_id: str
    analysis_type: AnalysisType
    detected: bool | None = Field(description="None when evidence was insufficient to decide")
    score: float | None = Field(
        default=None, ge=0, le=1, description="Uncalibrated ranking value, not a probability"
    )
    confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_calibrated: bool = False
    observations: dict[str, float] = Field(default_factory=dict)
    recommendation_signal: RecommendationSignal
    evidence_ids: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(
        default_factory=list, description="Machine-readable codes explaining the outcome"
    )
    observation_window: ObservationWindow
    data_quality: DataQuality
    data_provenance: DataProvenance
    model_version: str

    @model_validator(mode="after")
    def _check_consistency(self) -> AnalysisResult:
        if self.confidence is not None and not self.confidence_calibrated:
            raise ValueError("confidence may only be set when confidence_calibrated is True")
        insufficient = self.recommendation_signal is RecommendationSignal.INSUFFICIENT_EVIDENCE
        if insufficient != (self.detected is None):
            raise ValueError("detected must be None exactly when the signal is insufficient_evidence")
        if self.detected and not self.evidence_ids:
            raise ValueError("a positive detection must cite evidence_ids")
        if (self.detected is False) and self.recommendation_signal is not RecommendationSignal.NO_ACTION:
            raise ValueError("detected=False requires the no_action signal")
        return self


class ForecastResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = SCHEMA_VERSION
    resource_id: str
    metric: str
    analysis_type: AnalysisType = AnalysisType.FORECAST
    timestamps: list[datetime]
    point: list[float | None] = Field(description="None where the model cannot produce a value")
    lower: list[float | None]
    upper: list[float | None]
    interval_level: float = Field(gt=0, lt=1)
    interval_method: str
    evidence_ids: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    observation_window: ObservationWindow
    data_quality: DataQuality
    data_provenance: DataProvenance
    model_version: str

    @model_validator(mode="after")
    def _check_lengths(self) -> ForecastResult:
        n = len(self.timestamps)
        if not (len(self.point) == len(self.lower) == len(self.upper) == n):
            raise ValueError("timestamps, point, lower and upper must have equal length")
        return self
