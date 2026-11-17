import math

import numpy as np

from cloudlens_ml.evaluation import (
    average_precision,
    interval_coverage,
    mae,
    mape,
    precision_recall_f1,
    prediction_availability,
    rmse,
)

A = np.array([10.0, 20.0, 30.0, 40.0])
P = np.array([12.0, 18.0, 33.0, 36.0])


def test_error_metrics_hand_computed():
    assert math.isclose(mae(A, P), (2 + 2 + 3 + 4) / 4)
    assert math.isclose(rmse(A, P), math.sqrt((4 + 4 + 9 + 16) / 4))
    assert math.isclose(mape(A, P), np.mean([0.2, 0.1, 0.1, 0.1]) * 100)


def test_nan_pairs_are_excluded_not_zeroed():
    a = np.array([10.0, np.nan, 30.0])
    p = np.array([12.0, 5.0, np.nan])
    assert mae(a, p) == 2.0
    assert prediction_availability(a, p) == 0.5


def test_mape_ignores_near_zero_actuals():
    assert math.isclose(mape(np.array([0.0, 10.0]), np.array([5.0, 11.0])), 10.0)
    assert math.isnan(mape(np.array([0.0]), np.array([1.0])))


def test_interval_coverage():
    assert interval_coverage(A, A - 1, A + 1) == 1.0
    assert interval_coverage(A, A + 1, A + 2) == 0.0


def test_precision_recall_f1():
    p, r, f = precision_recall_f1(tp=8, fp=2, fn=2)
    assert (p, r) == (0.8, 0.8) and math.isclose(f, 0.8)
    assert all(math.isnan(x) for x in precision_recall_f1(0, 0, 0))


def test_average_precision_known_values():
    assert average_precision(np.array([1, 1, 0, 0]), np.array([0.9, 0.8, 0.2, 0.1])) == 1.0
    # ranking [pos, neg, pos]: precisions at positives = 1/1 and 2/3 -> AP = (1 + 2/3) / 2
    assert math.isclose(average_precision(np.array([1, 0, 1]), np.array([0.9, 0.8, 0.7])), (1 + 2 / 3) / 2)
    assert math.isnan(average_precision(np.array([0, 0]), np.array([0.5, 0.4])))
