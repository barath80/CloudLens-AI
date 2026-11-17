"""Evaluation metrics. Pure numpy so they are easy to verify by hand.

Missing values (NaN) in either input are excluded pairwise and reported separately, never zero-filled.
"""

from __future__ import annotations

import numpy as np

MAPE_MIN_ACTUAL = 1.0  # CPU percent. MAPE explodes near zero, so it is computed only where actual >= this.


def _pairs(actual: np.ndarray, pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a, p = np.asarray(actual, float), np.asarray(pred, float)
    m = ~(np.isnan(a) | np.isnan(p))
    return a[m], p[m]


def mae(actual: np.ndarray, pred: np.ndarray) -> float:
    a, p = _pairs(actual, pred)
    return float(np.mean(np.abs(a - p))) if len(a) else float("nan")


def rmse(actual: np.ndarray, pred: np.ndarray) -> float:
    a, p = _pairs(actual, pred)
    return float(np.sqrt(np.mean((a - p) ** 2))) if len(a) else float("nan")


def mape(actual: np.ndarray, pred: np.ndarray, min_actual: float = MAPE_MIN_ACTUAL) -> float:
    """Percent error over points with actual >= min_actual. NaN if there are none."""
    a, p = _pairs(actual, pred)
    m = a >= min_actual
    return float(np.mean(np.abs(a[m] - p[m]) / a[m]) * 100) if m.any() else float("nan")


def interval_coverage(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    a, lo, hi = (np.asarray(x, float) for x in (actual, lower, upper))
    m = ~(np.isnan(a) | np.isnan(lo) | np.isnan(hi))
    return float(np.mean((a[m] >= lo[m]) & (a[m] <= hi[m]))) if m.any() else float("nan")


def prediction_availability(actual: np.ndarray, pred: np.ndarray) -> float:
    """Share of points with an observed actual for which the model produced a prediction."""
    a, p = np.asarray(actual, float), np.asarray(pred, float)
    have = ~np.isnan(a)
    return float(np.mean(~np.isnan(p[have]))) if have.any() else float("nan")


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec == prec and rec == rec and (prec + rec) else float("nan")
    return prec, rec, f1


def average_precision(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Area under the precision-recall curve (step-wise, as in standard average precision)."""
    y = np.asarray(y_true, bool)
    s = np.asarray(scores, float)
    if not y.any():
        return float("nan")
    order = np.argsort(-s, kind="stable")
    y = y[order]
    tp = np.cumsum(y)
    precision = tp / np.arange(1, len(y) + 1)
    return float(np.sum(precision[y]) / y.sum())
