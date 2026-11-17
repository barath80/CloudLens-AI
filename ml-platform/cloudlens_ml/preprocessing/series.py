"""Turn raw metric rows into a regular, validated time series.

Rule: missing data stays missing (NaN). It is never filled with zero, and out-of-range values are
rejected to NaN rather than clipped, so a bad sensor cannot masquerade as a real reading.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import polars as pl

from cloudlens_ml.contracts import DataQuality, ObservationWindow

REQUIRED_COLUMNS = {"timestamp", "value"}


class SeriesValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Series:
    resource_id: str
    metric: str
    start: datetime  # timezone-aware, aligned to the grid
    step_minutes: int
    values: np.ndarray  # float64, NaN = missing or rejected
    invalid_points: int = 0

    def __len__(self) -> int:
        return len(self.values)

    @property
    def points_per_day(self) -> int:
        return 24 * 60 // self.step_minutes

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.step_minutes * len(self.values))

    def timestamps(self) -> list[datetime]:
        step = timedelta(minutes=self.step_minutes)
        return [self.start + i * step for i in range(len(self.values))]


def build_series(
    df: pl.DataFrame,
    *,
    resource_id: str,
    metric: str,
    step_minutes: int = 60,
    valid_range: tuple[float, float] = (0.0, 100.0),
) -> Series:
    """Build a Series from rows of (timestamp, value). One resource and one metric per call."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise SeriesValidationError(f"missing columns: {sorted(missing)}")
    if df.is_empty():
        raise SeriesValidationError("no rows")
    ts_dtype = df.schema["timestamp"]
    if not isinstance(ts_dtype, pl.Datetime) or ts_dtype.time_zone is None:
        raise SeriesValidationError("timestamp must be a timezone-aware datetime")
    if df["timestamp"].is_null().any():
        raise SeriesValidationError("timestamp contains nulls")
    if df["timestamp"].is_duplicated().any():
        raise SeriesValidationError("duplicate timestamps")

    df = df.sort("timestamp")
    step = timedelta(minutes=step_minutes)
    first: datetime = df["timestamp"][0]
    stamps: list[datetime] = df["timestamp"].to_list()
    offsets = [(t - first) / step for t in stamps]
    if any(abs(o - round(o)) > 1e-9 for o in offsets):
        raise SeriesValidationError(f"timestamps are not aligned to a {step_minutes}-minute grid")

    n = int(round(offsets[-1])) + 1
    values = np.full(n, np.nan)
    raw = df["value"].cast(pl.Float64).to_numpy()  # nulls become NaN
    for off, v in zip(offsets, raw, strict=True):
        values[int(round(off))] = v

    lo, hi = valid_range
    present = ~np.isnan(values)
    bad = present & ((values < lo) | (values > hi) | ~np.isfinite(values))
    values[bad] = np.nan
    return Series(resource_id, metric, first, step_minutes, values, int(bad.sum()))


def quality(series: Series) -> DataQuality:
    observed = ~np.isnan(series.values)
    longest = run = 0
    for ok in observed:
        run = 0 if ok else run + 1
        longest = max(longest, run)
    n = len(series.values)
    return DataQuality(
        expected_points=n,
        observed_points=int(observed.sum()),
        coverage=float(observed.sum() / n) if n else 0.0,
        longest_gap_points=longest,
        invalid_points=series.invalid_points,
    )


def window(series: Series) -> ObservationWindow:
    return ObservationWindow(
        start=series.start, end=series.end, days=len(series.values) * series.step_minutes / (24 * 60)
    )
