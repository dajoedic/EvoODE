import json
from pathlib import Path

import pandas as pd

from baselines import compare_odeformer_equivalence
from baselines import harness


CONFIG = harness.REPO_ROOT / "baselines" / "configs" / "wp_n19_smoke.json"
EXPORT_DIR = harness.REPO_ROOT / "outputs" / "phase_c_trajectory_hashes" / "wp_c4c" / "trajectory_export"
BENCHMARK = harness.REPO_ROOT / "benchmarks" / "data" / "strogatz_extended.json"


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def benchmark() -> list[dict[str, object]]:
    return harness.load_benchmark(BENCHMARK)


def manifest() -> pd.DataFrame:
    return pd.read_csv(EXPORT_DIR / "trajectory_manifest.csv")


def first_multidimensional_cell() -> harness.TrajectoryCell:
    systems = benchmark()
    cells, _ = harness.load_exported_cells(EXPORT_DIR, systems)
    system_id = int(manifest().query("dimension >= 2").sort_values(["system_id", "initial_condition_set"]).iloc[0]["system_id"])
    return cells[(system_id, 1)]


def test_hash_mismatch_aborts_before_records(tmp_path: Path) -> None:
    try:
        harness.run(CONFIG, str(tmp_path / "out"), corrupt_manifest_hash=True)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("corrupt manifest hash should abort")


def test_method_failure_writes_error_record(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "out"), force_sindy_failure=True)
    records = read_jsonl(path)
    sindy_records = [record for record in records if record["method"] == "sindy"]
    assert sindy_records
    assert all(record["status"] == "error" for record in sindy_records)
    assert all(record["error_message"] for record in sindy_records)


def test_smoke_writes_sindy_and_odeformer_records(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "out"))
    frame = pd.read_csv(path.parent / "records.csv")
    assert set(frame["method"]) == {"sindy", "odeformer"}
    assert len(frame) == 12
    assert {
        "reconstruction_r2_arithmetic_mean",
        "reconstruction_r2_variance_weighted",
        "reconstruction_r2_arithmetic_mean_gt_0_9",
        "reconstruction_r2_variance_weighted_gt_0_9",
        "generalization_r2_arithmetic_mean_gt_0_9",
        "generalization_r2_variance_weighted_gt_0_9",
        "odeformer_model_raw",
        "odeformer_model_canonical",
        "odeformer_weight_sha256",
        "odeformer_candidates_evaluated",
        "odeformer_beam_size",
        "odeformer_beam_temperature",
        "odeformer_parameter_optimization_iterations",
    }.issubset(frame.columns)
    assert "reconstruction_r2_gt_0_9" not in frame.columns
    assert "generalization_r2_gt_0_9" not in frame.columns
    assert frame["dimension"].ge(2).any()
    multidimensional_sindy = frame[(frame["method"] == "sindy") & (frame["dimension"] >= 2)]
    assert (
        multidimensional_sindy["reconstruction_r2_arithmetic_mean"]
        != multidimensional_sindy["reconstruction_r2_variance_weighted"]
    ).any()
    assert (path.parent / "trajectory_check.csv").is_file()
    selection = json.loads((path.parent / "selected_systems.json").read_text(encoding="utf-8"))
    assert selection["systems"] == [
        {"dimension": 1, "system_id": 1},
        {"dimension": 1, "system_id": 2},
        {"dimension": 2, "system_id": 24},
    ]
    odeformer_records = frame[frame["method"] == "odeformer"]
    assert set(odeformer_records["status"]) == {"error"}
    assert odeformer_records["error_message"].str.contains("ODEFormer is not importable").all()
    assert set(odeformer_records["odeformer_beam_size"]) == {10}


def test_r2_aggregations_are_distinct_on_multidimensional_case() -> None:
    cell = first_multidimensional_cell()
    reference = cell.state
    prediction = reference.copy()
    prediction[:, 0] = reference[:, 0].mean()
    scores = harness.aggregate_r2(reference, prediction)
    assert scores["r2_arithmetic_mean"] != scores["r2_variance_weighted"]


def test_selection_without_filters_covers_all_manifest_rows() -> None:
    systems = benchmark()
    selected = harness.selected_systems(systems, {})
    selected_ids = {int(system["id"]) for system in selected}
    selected_rows = harness.selected_manifest_rows(manifest(), selected_ids)
    assert len(selected) == len(systems) == 63
    assert len(selected_rows) == len(manifest()) == 126


def test_selection_combines_dimension_id_and_limit_filters() -> None:
    systems = benchmark()
    selected = harness.selected_systems(systems, {"dimensions": [2, 3], "system_ids": [24, 25, 52], "max_systems": 2})
    assert [(int(system["id"]), int(system["dim"])) for system in selected] == [(24, 2), (25, 2)]


def test_odeformer_equivalence_compare_rule_uses_export_records(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "out"))
    result = compare_odeformer_equivalence.compare(path, path)
    assert result["passed"] is True
    assert result["reference_record_count"] == 6
    assert result["comparison_rule"]["constants"] == {"abs_tol": 1e-8, "rel_tol": 1e-8}


def test_odeformer_equivalence_compare_reports_r2_difference_from_export_records(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "out"))
    records = read_jsonl(path)
    candidate = tmp_path / "candidate.jsonl"
    odeformer_record = next(record for record in records if record["method"] == "odeformer")
    odeformer_record["reconstruction_r2_arithmetic_mean"] = 0.25
    candidate.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    result = compare_odeformer_equivalence.compare(path, candidate)
    assert result["passed"] is False
    assert result["findings"][0]["field"] == "reconstruction_r2_arithmetic_mean"
