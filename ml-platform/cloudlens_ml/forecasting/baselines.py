"""Forecasting baselines. Simple, explainable, and the bar any later model must beat.

All models are pure functions of `history` (float array, NaN = missing). They never fill gaps with zero:
if no value is available for a step the prediction is NaN, and the evaluator counts it as an abstention.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

Predictor = Callable[[np.ndarray, int], np.ndarray]


def naive_last(history: np.ndarray, horizon: int) -> np.ndarray:
    seen = history[~np.isnan(history)]
    return np.full(horizon, seen[-1] if len(seen) else np.nan)


def seasonal_mean(history: np.ndarray, horizon: int, *, period: int, k: int) -> np.ndarray:
    """Mean of the same phase over the last `k` seasons (k=1 is seasonal naive). NaN if none observed."""
    n = len(history)
    out = np.full(horizon, np.nan)
    for h in range(horizon):
        target = n + h
        idx = [target - m * period for m in range(1, k + 1)]
        vals = np.array([history[i] for i in idx if 0 <= i < n], dtype=float)
        vals = vals[~np.isnan(vals)]
        if len(vals):
            out[h] = vals.mean()
    return out


@dataclass(frozen=True)
class ModelSpec:
    name: str
    version: str
    min_points: int  # observed points needed before the model will forecast
    predict: Predictor


def registry(points_per_day: int = 24) -> dict[str, ModelSpec]:
    day, week = points_per_day, 7 * points_per_day
    return {
        "naive_last": ModelSpec("naive_last", "naive_last-v1", 1, naive_last),
        "seasonal_naive_daily": ModelSpec(
            "seasonal_naive_daily",
            "seasonal_naive_daily-v1",
            2 * day,
            lambda h, n: seasonal_mean(h, n, period=day, k=1),
        ),
        "seasonal_mean_daily_7": ModelSpec(
            "seasonal_mean_daily_7",
            "seasonal_mean_daily_7-v1",
            2 * day,
            lambda h, n: seasonal_mean(h, n, period=day, k=7),
        ),
        "seasonal_mean_weekly_2": ModelSpec(
            "seasonal_mean_weekly_2",
            "seasonal_mean_weekly_2-v1",
            2 * week,
            lambda h, n: seasonal_mean(h, n, period=week, k=2),
        ),
    }


def empirical_interval(
    predict: Predictor,
    history: np.ndarray,
    horizon: int,
    *,
    level: float = 0.8,
    n_origins: int = 7,
    min_residuals: int = 30,
) -> tuple[float, float] | None:
    """Residual-quantile offsets (lo, hi) from earlier day-ahead forecasts on the *training* history only."""
    residuals: list[float] = []
    for j in range(1, n_origins + 1):
        origin = len(history) - j * horizon
        if origin < horizon:
            break
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            pred = predict(history[:origin], horizon)
        actual = history[origin : origin + horizon]
        diff = actual - pred
        residuals.extend(diff[~np.isnan(diff)].tolist())
    if len(residuals) < min_residuals:
        return None
    alpha = (1 - level) / 2
    lo, hi = np.quantile(residuals, [alpha, 1 - alpha])
    return float(lo), float(hi)
