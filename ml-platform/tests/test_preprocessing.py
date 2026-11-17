from datetime import timedelta

import numpy as np
import polars as pl
import pytest

from cloudlens_ml.preprocessing import SeriesValidationError, build_series, quality, window
from tests.helpers import T0, frame, series


def test_gaps_stay_missing_not_zero():
    s = series([10, None, None, 20])
    assert np.isnan(s.values[1]) and np.isnan(s.values[2])
    q = quality(s)
    assert (q.expected_points, q.observed_points, q.longest_gap_points) == (4, 2, 2)
    assert q.coverage == 0.5


def test_missing_timestamps_are_reindexed_as_missing():
    df = frame([1, 2, 3, 4]).filter(pl.col("timestamp") != T0 + timedelta(hours=2))
    s = build_series(df, resource_id="r", metric="m")
    assert len(s) == 4 and np.isnan(s.values[2])


def test_out_of_range_rejected_not_clipped():
    s = series([10, 150, -5, 20])
    assert np.isnan(s.values[1]) and np.isnan(s.values[2])
    assert s.invalid_points == 2 and quality(s).invalid_points == 2


def test_duplicate_timestamps_rejected():
    df = pl.concat([frame([1, 2]), frame([3])])
    with pytest.raises(SeriesValidationError, match="duplicate"):
        build_series(df, resource_id="r", metric="m")


def test_naive_timestamps_rejected():
    df = pl.DataFrame({"timestamp": [T0.replace(tzinfo=None)], "value": [1.0]})
    with pytest.raises(SeriesValidationError, match="timezone"):
        build_series(df, resource_id="r", metric="m")


def test_misaligned_grid_rejected():
    df = pl.concat([frame([1]), frame([2], start=T0 + timedelta(minutes=90))])
    with pytest.raises(SeriesValidationError, match="aligned"):
        build_series(df, resource_id="r", metric="m")


def test_missing_columns_and_empty_rejected():
    with pytest.raises(SeriesValidationError):
        build_series(pl.DataFrame({"x": [1]}), resource_id="r", metric="m")
    with pytest.raises(SeriesValidationError):
        build_series(frame([]), resource_id="r", metric="m")


def test_window_days():
    assert window(series([1.0] * 48)).days == 2.0
