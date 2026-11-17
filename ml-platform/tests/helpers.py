from datetime import UTC, datetime, timedelta

import numpy as np
import polars as pl

from cloudlens_ml.contracts import DataProvenance, DataSource
from cloudlens_ml.preprocessing import Series, build_series

T0 = datetime(2025, 1, 6, tzinfo=UTC)
PROV = DataProvenance(source=DataSource.SIMULATED, dataset_id="unit-test", note="SIMULATED unit-test data")


def frame(values, *, step_minutes: int = 60, start: datetime = T0) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "timestamp": [start + timedelta(minutes=step_minutes * i) for i in range(len(values))],
            "value": [
                None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v) for v in values
            ],
        },
        schema={"timestamp": pl.Datetime("us", "UTC"), "value": pl.Float64},
    )


def series(values, rid: str = "r1") -> Series:
    return build_series(frame(values), resource_id=rid, metric="cpu_utilization_percent")


def daily_profile(days: int, fn=lambda h: 10.0 + (h % 24)) -> list[float]:
    return [fn(h) for h in range(days * 24)]
