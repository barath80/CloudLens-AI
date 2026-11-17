"""SIMULATED CPU-utilization data with ground-truth labels.

    *** This is not real data. ***

What it is good for:
  - proving the pipeline runs end to end and is deterministic;
  - checking behaviours we can state by construction (e.g. a spiky workload with a low *mean* must
    not be flagged as underutilized; thin or gappy history must produce an abstention).

What it is NOT evidence of:
  - real-world accuracy, precision, recall or forecast error. Labels come from the same assumptions
    that shaped the data, so agreement here is partly circular. Never quote these numbers as model
    performance. See docs/adr/ADR-ML-002-simulated-data-policy.md.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

import numpy as np
import polars as pl

GENERATOR_VERSION = "1"
SIMULATION_BANNER = (
    "SIMULATED DATA - not real customer or AWS data. Results validate pipeline behaviour only and "
    "are NOT evidence of real-world performance."
)
# A Monday, fixed so the dataset is reproducible and not relative to "now".
START = datetime(2025, 1, 6, tzinfo=UTC)
STEP_MINUTES = 60


class Archetype(StrEnum):
    IDLE = "idle"
    STEADY_LOW = "steady_low"
    BUSY_DIURNAL = "busy_diurnal"
    SPIKY_BATCH = "spiky_batch"
    RAMPING = "ramping"
    SHORT_HISTORY = "short_history"
    GAPPY = "gappy"


class ExpectedOutcome(StrEnum):
    UNDERUTILIZED = "underutilized"
    NOT_UNDERUTILIZED = "not_underutilized"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


EXPECTED: dict[Archetype, ExpectedOutcome] = {
    Archetype.IDLE: ExpectedOutcome.UNDERUTILIZED,
    Archetype.STEADY_LOW: ExpectedOutcome.UNDERUTILIZED,
    Archetype.BUSY_DIURNAL: ExpectedOutcome.NOT_UNDERUTILIZED,
    Archetype.SPIKY_BATCH: ExpectedOutcome.NOT_UNDERUTILIZED,
    Archetype.RAMPING: ExpectedOutcome.NOT_UNDERUTILIZED,
    Archetype.SHORT_HISTORY: ExpectedOutcome.INSUFFICIENT_EVIDENCE,
    Archetype.GAPPY: ExpectedOutcome.INSUFFICIENT_EVIDENCE,
}


@dataclass(frozen=True)
class SimulatedDataset:
    data: pl.DataFrame  # resource_id, timestamp, value (null = missing)
    labels: pl.DataFrame  # resource_id, archetype, expected_outcome
    manifest: dict[str, object]

    @property
    def dataset_id(self) -> str:
        return str(self.manifest["dataset_id"])


def _shape(arch: Archetype, n: int, rng: np.random.Generator) -> np.ndarray:
    hours = np.arange(n)
    hod = hours % 24
    dow = (hours // 24) % 7
    weekend = np.where(dow >= 5, 0.6, 1.0)
    noise = rng.normal(0, 1, n)

    if arch is Archetype.IDLE or arch is Archetype.SHORT_HISTORY:
        base = rng.uniform(1, 4)
        y = base + 0.6 * noise
    elif arch is Archetype.STEADY_LOW or arch is Archetype.GAPPY:
        base = rng.uniform(8, 16)
        amp = rng.uniform(2, 5)
        y = base + amp * np.sin(2 * np.pi * (hod - 6) / 24) * weekend + 1.5 * noise
    elif arch is Archetype.BUSY_DIURNAL:
        base = rng.uniform(25, 40)
        amp = rng.uniform(20, 35)
        y = base + amp * np.clip(np.sin(2 * np.pi * (hod - 6) / 24), 0, None) * weekend + 3 * noise
    elif arch is Archetype.SPIKY_BATCH:
        # Low baseline, but a daily 2-hour burst to high CPU. The mean looks small; the tail does not.
        base = rng.uniform(3, 8)
        burst_hour = int(rng.integers(0, 22))
        burst = rng.uniform(70, 95)
        in_burst = (hod >= burst_hour) & (hod < burst_hour + 2)
        y = base + 1.0 * noise + np.where(in_burst, burst - base, 0.0)
    elif arch is Archetype.RAMPING:
        lo, hi = rng.uniform(8, 15), rng.uniform(65, 80)
        y = np.linspace(lo, hi, n) + 3 * noise
    else:  # pragma: no cover
        raise ValueError(arch)
    return np.clip(y, 0.0, 100.0)


def _apply_gaps(arch: Archetype, y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    y = y.copy()
    n = len(y)
    if arch is Archetype.GAPPY:
        # Remove ~40% of the window in a few long blocks, as after a collector outage.
        removed = 0
        target = int(0.4 * n)
        while removed < target:
            length = int(rng.integers(24, 96))
            start = int(rng.integers(0, max(1, n - length)))
            seg = y[start : start + length]
            removed += int(np.sum(~np.isnan(seg)))
            y[start : start + length] = np.nan
    else:
        mask = rng.random(n) < 0.01  # light random loss everywhere else
        y[mask] = np.nan
    return y


def generate(
    *,
    seed: int = 42,
    days: int = 30,
    per_archetype: int = 20,
    short_history_days: int = 5,
) -> SimulatedDataset:
    rng = np.random.default_rng(seed)
    frames: list[pl.DataFrame] = []
    label_rows: list[dict[str, str]] = []

    for arch in Archetype:
        for i in range(per_archetype):
            sub = np.random.default_rng(rng.integers(0, 2**32))
            n_days = short_history_days if arch is Archetype.SHORT_HISTORY else days
            n = n_days * 24
            y = _apply_gaps(arch, _shape(arch, n, sub), sub)
            rid = f"sim-{arch.value}-{i:03d}"
            frames.append(
                pl.DataFrame(
                    {
                        "resource_id": [rid] * n,
                        "timestamp": [START + timedelta(minutes=STEP_MINUTES * k) for k in range(n)],
                        "value": [None if np.isnan(v) else float(v) for v in y],
                    },
                    schema={
                        "resource_id": pl.String,
                        "timestamp": pl.Datetime("us", "UTC"),
                        "value": pl.Float64,
                    },
                )
            )
            label_rows.append(
                {"resource_id": rid, "archetype": arch.value, "expected_outcome": EXPECTED[arch].value}
            )

    data = pl.concat(frames)
    labels = pl.DataFrame(label_rows)
    digest = hashlib.sha256(
        data.write_csv().encode() + labels.write_csv().encode() + GENERATOR_VERSION.encode()
    ).hexdigest()
    manifest: dict[str, object] = {
        "data_source": "simulated",
        "banner": SIMULATION_BANNER,
        "dataset_id": f"sim-util-g{GENERATOR_VERSION}-seed{seed}",
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "days": days,
        "short_history_days": short_history_days,
        "per_archetype": per_archetype,
        "step_minutes": STEP_MINUTES,
        "metric": "cpu_utilization_percent",
        "archetypes": {a.value: EXPECTED[a].value for a in Archetype},
        "sha256": digest,
    }
    return SimulatedDataset(data, labels, manifest)


def save(ds: SimulatedDataset, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    ds.data.write_parquet(directory / f"{ds.dataset_id}.parquet")
    ds.labels.write_parquet(directory / f"{ds.dataset_id}.labels.parquet")
    (directory / f"{ds.dataset_id}.manifest.json").write_text(json.dumps(ds.manifest, indent=2))
