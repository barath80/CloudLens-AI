import json

import polars as pl

from cloudlens_ml.benchmarks import phase1
from cloudlens_ml.simulation import EXPECTED, SIMULATION_BANNER, Archetype, generate, save


def test_generation_is_deterministic_and_seed_sensitive():
    a, b, c = (
        generate(seed=1, per_archetype=2),
        generate(seed=1, per_archetype=2),
        generate(seed=2, per_archetype=2),
    )
    assert a.manifest["sha256"] == b.manifest["sha256"]
    assert a.data.equals(b.data)
    assert a.manifest["sha256"] != c.manifest["sha256"]


def test_dataset_is_labelled_simulated_everywhere(tmp_path):
    ds = generate(seed=3, per_archetype=1)
    assert ds.manifest["data_source"] == "simulated" and ds.manifest["banner"] == SIMULATION_BANNER
    assert ds.dataset_id.startswith("sim-")
    assert set(ds.labels["resource_id"].str.slice(0, 4)) == {"sim-"}
    save(ds, tmp_path)
    saved = json.loads((tmp_path / f"{ds.dataset_id}.manifest.json").read_text())
    assert saved["data_source"] == "simulated"


def test_every_archetype_has_an_expected_outcome_and_ground_truth_labels():
    ds = generate(seed=4, per_archetype=1)
    assert set(ds.labels["archetype"]) == {a.value for a in Archetype}
    for a in Archetype:
        got = ds.labels.filter(pl.col("archetype") == a.value)["expected_outcome"][0]
        assert got == EXPECTED[a].value


def test_values_in_range_and_gaps_present():
    ds = generate(seed=5, per_archetype=2)
    v = ds.data["value"].drop_nulls()
    assert v.min() >= 0 and v.max() <= 100
    assert ds.data["value"].null_count() > 0


def test_benchmark_record_is_flagged_simulated(tmp_path, monkeypatch):
    monkeypatch.setattr(phase1, "RUNS_DIR", tmp_path)
    rec = phase1.run(seed=7, write=True)
    assert rec["banner"] == SIMULATION_BANNER and rec["evidence_grade"] == "simulated_pipeline_check"
    written = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert written["dataset"]["data_source"] == "simulated"
    assert "NOT evidence" in written["banner"] and "circular" in written["caveat"]
    det = written["detection"]
    # The mean-only baseline must show the false positives the percentile rule avoids on spiky workloads.
    assert det["baseline_mean_only"]["fp"] > det["rule_v1_percentile"]["fp"]
    assert det["abstention"]["abstained_when_evidence_sufficient"] == 0
