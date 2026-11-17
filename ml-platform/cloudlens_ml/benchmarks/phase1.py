"""Phase 1 benchmark on SIMULATED utilization data.

Run:  python -m cloudlens_ml.benchmarks.phase1

Writes a JSON run record under experiments/runs/. Every record and every printed report carries the
simulation banner. These numbers check pipeline behaviour; they are not real-world performance.
"""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from cloudlens_ml.contracts import DataProvenance, DataSource, RecommendationSignal
from cloudlens_ml.evaluation import (
    average_precision,
    interval_coverage,
    mae,
    mape,
    precision_recall_f1,
    prediction_availability,
    rmse,
)
from cloudlens_ml.forecasting import registry
from cloudlens_ml.forecasting.baselines import empirical_interval
from cloudlens_ml.opportunity_detection import MODEL_VERSION, UnderutilizationConfig, detect_underutilization
from cloudlens_ml.preprocessing import build_series
from cloudlens_ml.simulation import SIMULATION_BANNER, STEP_MINUTES, SimulatedDataset, generate

ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "experiments" / "runs"
MEAN_ONLY_LIMIT = 20.0  # comparison baseline only


def _series_for(ds: SimulatedDataset, rid: str):
    rows = ds.data.filter(ds.data["resource_id"] == rid)
    return build_series(rows, resource_id=rid, metric="cpu_utilization_percent", step_minutes=STEP_MINUTES)


def provenance(ds: SimulatedDataset) -> DataProvenance:
    return DataProvenance(
        source=DataSource.SIMULATED,
        dataset_id=ds.dataset_id,
        dataset_version=str(ds.manifest["sha256"])[:12],
        note=SIMULATION_BANNER,
    )


def run_detection(ds: SimulatedDataset) -> dict[str, object]:
    prov = provenance(ds)
    cfg = UnderutilizationConfig()
    rows = []
    for rid, expected in ds.labels.select("resource_id", "expected_outcome").iter_rows():
        s = _series_for(ds, rid)
        res = detect_underutilization(s, prov, config=cfg)
        v = s.values[~np.isnan(s.values)]
        mean_only = bool(v.mean() < MEAN_ONLY_LIMIT) if len(v) else None
        rows.append((rid, expected, res, mean_only))

    def counts(pred_pos):
        tp = sum(1 for _, e, r, m in rows if pred_pos(r, m) and e == "underutilized")
        fp = sum(1 for _, e, r, m in rows if pred_pos(r, m) and e != "underutilized")
        fn = sum(1 for _, e, r, m in rows if not pred_pos(r, m) and e == "underutilized")
        return tp, fp, fn

    out: dict[str, object] = {}
    for name, fn in {
        "rule_v1_percentile": lambda r, m: r.detected is True,
        "baseline_mean_only": lambda r, m: m is True,
    }.items():
        tp, fp, fn_ = counts(fn)
        p, r_, f1 = precision_recall_f1(tp, fp, fn_)
        out[name] = {"tp": tp, "fp": fp, "fn": fn_, "precision": p, "recall": r_, "f1": f1}

    abst = [(e, r.recommendation_signal) for _, e, r, _ in rows]
    out["abstention"] = {
        "expected_insufficient": sum(1 for e, _ in abst if e == "insufficient_evidence"),
        "abstained_correctly": sum(
            1
            for e, s in abst
            if e == "insufficient_evidence" and s is RecommendationSignal.INSUFFICIENT_EVIDENCE
        ),
        "abstained_when_evidence_sufficient": sum(
            1
            for e, s in abst
            if e != "insufficient_evidence" and s is RecommendationSignal.INSUFFICIENT_EVIDENCE
        ),
    }
    decided = [(e, r.score) for _, e, r, _ in rows if r.score is not None]
    out["average_precision_rule_v1"] = average_precision(
        np.array([e == "underutilized" for e, _ in decided]), np.array([s for _, s in decided])
    )
    out["n_resources"] = len(rows)
    out["config"] = cfg.__dict__
    out["model_version"] = MODEL_VERSION
    return out


def run_forecasting(ds: SimulatedDataset, *, horizon: int = 24, initial_days: int = 14) -> dict[str, object]:
    """Rolling-origin, time-ordered evaluation. History never includes the forecast window."""
    specs = registry(24)
    acc: dict[str, dict[str, list[np.ndarray]]] = {n: {"a": [], "p": [], "lo": [], "hi": []} for n in specs}
    eligible = ds.labels.filter(
        ds.labels["archetype"].is_in(["idle", "steady_low", "busy_diurnal", "spiky_batch", "ramping"])
    )
    for rid in eligible["resource_id"].to_list():
        y = _series_for(ds, rid).values
        for origin in range(initial_days * 24, len(y) - horizon + 1, horizon):
            hist, actual = y[:origin], y[origin : origin + horizon]
            for name, spec in specs.items():
                if int((~np.isnan(hist)).sum()) < spec.min_points:
                    continue
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    pred = spec.predict(hist, horizon)
                    off = empirical_interval(spec.predict, hist, horizon)
                lo = np.clip(pred + off[0], 0, 100) if off else np.full(horizon, np.nan)
                hi = np.clip(pred + off[1], 0, 100) if off else np.full(horizon, np.nan)
                a = acc[name]
                a["a"].append(actual)
                a["p"].append(np.clip(pred, 0, 100))
                a["lo"].append(lo)
                a["hi"].append(hi)

    out: dict[str, object] = {}
    for name, a in acc.items():
        if not a["a"]:
            out[name] = {"note": "no eligible folds"}
            continue
        A, P, LO, HI = (np.concatenate(a[k]) for k in ("a", "p", "lo", "hi"))
        out[name] = {
            "mae": mae(A, P),
            "rmse": rmse(A, P),
            "mape_actual_ge_1pct": mape(A, P),
            "interval_80_empirical_coverage": interval_coverage(A, LO, HI),
            "prediction_availability": prediction_availability(A, P),
            "evaluations": len(a["a"]),
        }
    out["protocol"] = {
        "horizon_points": horizon,
        "initial_days": initial_days,
        "step": "rolling origin, stride = horizon",
    }
    return out


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def run(seed: int = 42, write: bool = True) -> dict[str, object]:
    ds = generate(seed=seed)
    record: dict[str, object] = {
        "banner": SIMULATION_BANNER,
        "evidence_grade": "simulated_pipeline_check",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "dataset": ds.manifest,
        "detection": run_detection(ds),
        "forecasting": run_forecasting(ds),
        "caveat": (
            "Labels come from the generator's own assumptions, so detection agreement is partly "
            "circular. Forecast errors reflect simulated seasonality. Neither is real-world performance."
        ),
    }
    if write:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        path = RUNS_DIR / f"phase1_{ds.dataset_id}_{str(ds.manifest['sha256'])[:8]}.json"
        path.write_text(json.dumps(record, indent=2, default=float))
        record["_path"] = str(path)
    return record


def _fmt(x: object) -> str:
    return f"{x:.3f}" if isinstance(x, float) else str(x)


if __name__ == "__main__":
    rec = run(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 42)
    print("=" * 100, f"\n{SIMULATION_BANNER}\n", "=" * 100, sep="")
    print(f"dataset {rec['dataset']['dataset_id']}  sha256 {str(rec['dataset']['sha256'])[:12]}")  # type: ignore[index]
    det = rec["detection"]
    print("\nDETECTION (positive class = underutilized)")
    for k in ("rule_v1_percentile", "baseline_mean_only"):
        d = det[k]  # type: ignore[index]
        print(
            f"  {k:22s} "
            + "  ".join(f"{m}={_fmt(d[m])}" for m in ("tp", "fp", "fn", "precision", "recall", "f1"))
        )
    print(f"  abstention: {det['abstention']}")  # type: ignore[index]
    print("\nFORECASTING (rolling origin, 24h horizon)")
    for name, m in rec["forecasting"].items():  # type: ignore[union-attr]
        if name != "protocol":
            print(f"  {name:24s} " + "  ".join(f"{k}={_fmt(v)}" for k, v in m.items()))
    print(f"\nrecord: {rec.get('_path')}\n{rec['caveat']}")
