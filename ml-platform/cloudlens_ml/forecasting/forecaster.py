from __future__ import annotations

from datetime import timedelta

import numpy as np

from cloudlens_ml.contracts import AnalysisType, DataProvenance, ForecastResult
from cloudlens_ml.forecasting.baselines import empirical_interval, registry
from cloudlens_ml.preprocessing import Series, quality, window


def forecast(
    series: Series,
    *,
    model: str,
    horizon: int,
    provenance: DataProvenance,
    level: float = 0.8,
    domain: tuple[float, float] | None = (0.0, 100.0),
) -> ForecastResult:
    """Forecast `horizon` steps. Returns None values and a reason code when history is insufficient."""
    spec = registry(series.points_per_day)[model]
    q, w = quality(series), window(series)
    step = timedelta(minutes=series.step_minutes)
    stamps = [series.end + i * step for i in range(horizon)]
    base = dict(
        resource_id=series.resource_id,
        metric=series.metric,
        timestamps=stamps,
        interval_level=level,
        interval_method="empirical_residual_quantiles_day_ahead",
        observation_window=w,
        data_quality=q,
        data_provenance=provenance,
        model_version=spec.version,
    )
    empty: list[float | None] = [None] * horizon
    if q.observed_points < spec.min_points:
        return ForecastResult(point=empty, lower=empty, upper=empty, reasons=["insufficient_history"], **base)  # type: ignore[arg-type]

    point = spec.predict(series.values, horizon)
    offsets = empirical_interval(spec.predict, series.values, horizon, level=level)
    reasons: list[str] = []
    if offsets is None:
        reasons.append("interval_unavailable_too_few_residuals")

    def clip(x: float) -> float:
        return float(np.clip(x, *domain)) if domain else float(x)

    pts = [None if np.isnan(p) else clip(p) for p in point]
    lo = [None if (p is None or offsets is None) else clip(p + offsets[0]) for p in point]
    hi = [None if (p is None or offsets is None) else clip(p + offsets[1]) for p in point]
    if any(p is None for p in pts):
        reasons.append("some_steps_have_no_prediction")
    return ForecastResult(point=pts, lower=lo, upper=hi, reasons=reasons, **base)  # type: ignore[arg-type]


__all__ = ["AnalysisType", "forecast"]
