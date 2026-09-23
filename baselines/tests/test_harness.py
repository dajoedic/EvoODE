import json
from pathlib import Path

import pandas as pd

from baselines import compare_odeformer_equivalence
from baselines import harness
from baselines import run_odeformer_grid
from baselines import summarize_odeformer_grid


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


def make_grid_record(fit_cell: harness.TrajectoryCell, target_cell: harness.TrajectoryCell, config: dict[str, object], status: str = "success") -> dict[str, object]:
    record = harness.base_record("odeformer", config, fit_cell, target_cell)
    r2 = {"r2_arithmetic_mean": 1.0, "r2_variance_weighted": 1.0}
    record.update(
        {
            **harness.odeformer_schema_defaults(config),
            "status": status,
            "model": "x_0",
            "reconstruction_status": status,
            "generalization_status": status,
            "odeformer_model_raw": "x_0",
            "odeformer_model_canonical": "x_0",
            "odeformer_expression_before_optimization": "x_0",
            "odeformer_expression_after_optimization": "x_0",
            "odeformer_fitted_constants": "[]",
            "odeformer_candidates_evaluated": 1,
            "odeformer_optimization_status": "not_requested",
            "odeformer_optimization_nit": 0,
            "odeformer_optimization_nfev": 0,
            "odeformer_optimization_stop_reason": "",
            **{f"reconstruction_{key}": value for key, value in r2.items()},
            **{f"generalization_{key}": value for key, value in r2.items()},
            **{f"reconstruction_before_optimization_{key}": value for key, value in r2.items()},
            **{f"generalization_before_optimization_{key}": value for key, value in r2.items()},
            **{f"reconstruction_after_optimization_{key}": value for key, value in r2.items()},
            **{f"generalization_after_optimization_{key}": value for key, value in r2.items()},
        }
    )
    return record


def test_odeformer_grid_resumes_complete_records_from_real_export(tmp_path: Path, monkeypatch) -> None:
    calls = {"count": 0}

    def fake_build(config):
        return object()

    def fake_run(system, fit_cell, target_cell, config, adapter):
        calls["count"] += 1
        return make_grid_record(fit_cell, target_cell, config)

    monkeypatch.setattr(harness, "build_odeformer_adapter", fake_build)
    monkeypatch.setattr(harness, "run_odeformer_record_with_adapter", fake_run)
    kwargs = {
        "output_dir": str(tmp_path / "grid"),
        "system_ids": {1},
        "config_ids": {"beam10_noopt"},
        "limit": 1,
    }
    first = run_odeformer_grid.run(harness.REPO_ROOT / "baselines" / "configs" / "odeformer_grid.json", **kwargs)
    second = run_odeformer_grid.run(harness.REPO_ROOT / "baselines" / "configs" / "odeformer_grid.json", **kwargs)
    assert first == second
    assert calls["count"] == 1
    records = read_jsonl(first)
    assert len(records) == 1
    assert records[0]["odeformer_config_id"] == "beam10_noopt"


def test_odeformer_grid_atomic_write_ignores_partial_tmp(tmp_path: Path) -> None:
    records_dir = tmp_path / "records"
    path = records_dir / "cell.json"
    run_odeformer_grid.atomic_write_json(path, {"status": "success", "odeformer_config_id": "beam10_noopt"})
    (records_dir / ".cell.json.999.tmp").write_text("{", encoding="utf-8")
    assert run_odeformer_grid.complete_record(path) is True
    assert run_odeformer_grid.complete_record(records_dir / ".cell.json.999.tmp") is False


def test_odeformer_grid_marks_timeout_from_real_export(tmp_path: Path, monkeypatch) -> None:
    def fake_build(config):
        return object()

    def fake_run(system, fit_cell, target_cell, config, adapter):
        return make_grid_record(fit_cell, target_cell, config)

    monkeypatch.setattr(harness, "build_odeformer_adapter", fake_build)
    monkeypatch.setattr(harness, "run_odeformer_record_with_adapter", fake_run)
    config = json.loads((harness.REPO_ROOT / "baselines" / "configs" / "odeformer_grid.json").read_text(encoding="utf-8"))
    config["timeout_seconds_per_cell"] = -1
    config_path = tmp_path / "timeout_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    path = run_odeformer_grid.run(config_path, str(tmp_path / "grid"), system_ids={1}, config_ids={"beam10_noopt"}, limit=1)
    records = read_jsonl(path)
    assert records[0]["status"] == "timeout"
    assert records[0]["error_type"] == "Timeout"


def test_odeformer_summary_counts_and_expression_identity_from_export_records(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "source"))
    records = [record for record in read_jsonl(path) if record["method"] == "odeformer"][:2]
    for idx, record in enumerate(records):
        record["status"] = "success"
        record["odeformer_environment_id"] = "reference"
        record["odeformer_config_id"] = "beam10_noopt"
        record["odeformer_model_canonical"] = "x_0" if idx == 0 else "x_0 + 1"
        record["reconstruction_r2_arithmetic_mean"] = 0.95
        record["reconstruction_r2_variance_weighted"] = 0.95
        record["generalization_r2_arithmetic_mean"] = 0.25
        record["generalization_r2_variance_weighted"] = 0.25
    reference = tmp_path / "reference.jsonl"
    reference.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    candidate_records = [dict(record, odeformer_environment_id="candidate") for record in records]
    candidate_records[1]["odeformer_model_canonical"] = "x_0 - 1"
    candidate = tmp_path / "candidate.jsonl"
    candidate.write_text("\n".join(json.dumps(record, sort_keys=True) for record in candidate_records) + "\n", encoding="utf-8")
    paths = summarize_odeformer_grid.run(reference, candidate, tmp_path / "summary")
    summary = pd.read_csv(paths["summary"])
    identity = pd.read_csv(paths["expression_identity"])
    assert set(summary["environment_id"]) == {"reference", "candidate"}
    assert set(summary["reconstruction_r2_arithmetic_gt_0_9_count"]) == {2}
    assert set(summary["generalization_r2_arithmetic_gt_0_9_count"]) == {0}
    assert int(identity["paired_cell_count"].sum()) == 2
    assert int(identity["identical_expression_count"].sum()) == 1
