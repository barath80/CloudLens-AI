import numpy as np

from cloudlens_ml.forecasting import forecast, registry
from cloudlens_ml.forecasting.baselines import empirical_interval, naive_last, seasonal_mean
from tests.helpers import PROV, daily_profile, series


def test_seasonal_naive_exact_on_perfectly_periodic_series():
    y = np.array(daily_profile(10))
    pred = seasonal_mean(y, 24, period=24, k=1)
    expected = np.array([10.0 + (h % 24) for h in range(len(y), len(y) + 24)])
    assert np.allclose(pred, expected)


def test_seasonal_mean_averages_last_k_seasons():
    y = np.concatenate([np.full(24, 10.0), np.full(24, 20.0), np.full(24, 30.0)])
    assert np.allclose(seasonal_mean(y, 24, period=24, k=2), 25.0)
    assert np.allclose(seasonal_mean(y, 24, period=24, k=1), 30.0)


def test_missing_history_gives_nan_not_zero():
    y = np.full(48, np.nan)
    assert np.isnan(seasonal_mean(y, 24, period=24, k=2)).all()
    assert np.isnan(naive_last(y, 3)).all()


def test_gaps_in_history_are_skipped_in_the_mean():
    y = np.concatenate([np.full(24, 10.0), np.full(24, np.nan), np.full(24, 30.0)])
    assert np.allclose(seasonal_mean(y, 24, period=24, k=2), 30.0)  # only the observed season counts


def test_no_lookahead_predictions_ignore_the_future():
    """Forecasts made at an origin must not change when data after the origin changes."""
    rng = np.random.default_rng(1)
    y = rng.uniform(0, 100, 24 * 20)
    origin = 24 * 15
    for spec in registry(24).values():
        before = spec.predict(y[:origin], 24)
        y2 = y.copy()
        y2[origin:] = 999.0
        after = spec.predict(y2[:origin], 24)
        assert np.array_equal(before, after, equal_nan=True), spec.name


def test_forecast_result_shape_and_interval_ordering():
    rng = np.random.default_rng(2)
    base = np.array(daily_profile(21, lambda h: 30 + 10 * np.sin(2 * np.pi * h / 24)))
    r = forecast(
        series(list(base + rng.normal(0, 2, len(base)))),
        model="seasonal_mean_daily_7",
        horizon=24,
        provenance=PROV,
    )
    assert len(r.point) == len(r.lower) == len(r.upper) == len(r.timestamps) == 24
    assert all(lo <= p <= hi for lo, p, hi in zip(r.lower, r.point, r.upper, strict=True))
    assert r.data_provenance.source.value == "simulated" and r.model_version == "seasonal_mean_daily_7-v1"


def test_insufficient_history_returns_reason_not_numbers():
    r = forecast(series([5.0] * 30), model="seasonal_naive_daily", horizon=24, provenance=PROV)
    assert r.reasons == ["insufficient_history"] and all(p is None for p in r.point)


def test_interval_needs_enough_residuals():
    assert empirical_interval(lambda h, n: np.zeros(n), np.zeros(30), 24) is None


def test_forecast_timestamps_continue_after_the_window():
    s = series([5.0] * (24 * 10))
    r = forecast(s, model="naive_last", horizon=3, provenance=PROV)
    assert r.timestamps[0] == s.end
