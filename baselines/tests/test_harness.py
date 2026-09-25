import argparse
import contextlib
import json
import os
import functools
import signal
import sys
import time
import types
from pathlib import Path

import pandas as pd
import pytest
import numpy as np

from baselines import compare_odeformer_equivalence
from baselines import harness
from baselines import run_odeformer_grid
from baselines import run_odeformer_grid_k8s
from baselines import run_odeformer_repeatability
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
        "reconstruction_prediction_outcome",
        "reconstruction_r2_dimension_status",
        "reconstruction_r2_zero_reason",
        "reconstruction_integration_error_type",
        "reconstruction_integration_error_message",
        "generalization_prediction_outcome",
        "generalization_r2_dimension_status",
        "generalization_r2_zero_reason",
        "generalization_integration_error_type",
        "generalization_integration_error_message",
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


def test_r2_diagnostics_preserve_zero_convention_on_invalid_predictions_from_export() -> None:
    cell = first_multidimensional_cell()
    reference = cell.state
    cases = [
        (None, "none", "prediction_none"),
        (np.full(reference.shape, np.nan), "nonfinite", "prediction_nonfinite"),
        (reference[:, :1].copy(), "wrong_shape", "prediction_wrong_shape"),
    ]
    for prediction, outcome, reason in cases:
        scores = harness.aggregate_r2(reference, prediction)
        fields = harness.r2_diagnostic_fields("generalization", reference, prediction)
        assert scores == {"r2_arithmetic_mean": 0.0, "r2_variance_weighted": 0.0}
        assert fields["generalization_prediction_outcome"] == outcome
        assert json.loads(fields["generalization_r2_dimension_status"]) == ["zero_convention"] * reference.shape[1]
        assert json.loads(fields["generalization_r2_zero_reason"]) == [reason] * reference.shape[1]


def test_r2_diagnostics_name_odeformer_nan_sentinel_from_export() -> None:
    cell = first_multidimensional_cell()
    sentinel = np.full(cell.state.shape[0], np.nan)
    scores = harness.aggregate_r2(cell.state, sentinel)
    fields = harness.r2_diagnostic_fields("generalization", cell.state, sentinel)
    assert scores == {"r2_arithmetic_mean": 0.0, "r2_variance_weighted": 0.0}
    assert fields["generalization_prediction_outcome"] == "odeformer_nan_sentinel"
    assert json.loads(fields["generalization_r2_zero_reason"]) == ["prediction_odeformer_nan_sentinel"] * cell.state.shape[1]


@pytest.mark.skipif(not hasattr(signal, "SIGALRM"), reason="signal timeout equivalence requires SIGALRM")
def test_odeformer_timeout_hook_matches_original_timer_semantics() -> None:
    class MyTimeoutError(BaseException):
        pass

    def original_timeout(seconds=10, error_message=os.strerror(62)):
        def decorator(func):
            def _handle_timeout(repeat_id, signum, frame):
                signal.signal(signal.SIGALRM, functools.partial(_handle_timeout, repeat_id + 1))
                signal.setitimer(signal.ITIMER_REAL, seconds)
                raise MyTimeoutError(error_message)

            def wrapper(*args, **kwargs):
                old_signal = signal.signal(signal.SIGALRM, functools.partial(_handle_timeout, 0))
                old_time_left = signal.getitimer(signal.ITIMER_REAL)[0]
                assert type(old_time_left) is float and old_time_left >= 0
                if 0 < old_time_left < seconds:
                    signal.setitimer(signal.ITIMER_REAL, old_time_left)
                else:
                    signal.setitimer(signal.ITIMER_REAL, seconds)
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                finally:
                    if old_time_left == 0:
                        signal.setitimer(signal.ITIMER_REAL, 0)
                    else:
                        time_elapsed = time.time() - start_time
                        signal.signal(signal.SIGALRM, old_signal)
                        signal.setitimer(signal.ITIMER_REAL, max(0, old_time_left - time_elapsed))
                return result

            return functools.wraps(func)(wrapper)

        return decorator

    def slow() -> str:
        time.sleep(0.2)
        return "done"

    counts = {"value": 0}
    copied = harness.odeformer_timeout_with_hook(
        0.05,
        on_timeout=lambda: counts.__setitem__("value", counts["value"] + 1),
        error_type=MyTimeoutError,
        error_message=os.strerror(62),
    )(slow)
    reference = original_timeout(0.05)(slow)
    with pytest.raises(MyTimeoutError):
        reference()
    with pytest.raises(MyTimeoutError):
        copied()
    assert counts["value"] == 1
    assert signal.getitimer(signal.ITIMER_REAL)[0] == 0.0

    def fast() -> str:
        return "done"

    assert harness.odeformer_timeout_with_hook(0.1, error_type=MyTimeoutError)(fast)() == "done"
    assert signal.getitimer(signal.ITIMER_REAL)[0] == 0.0

    signal.setitimer(signal.ITIMER_REAL, 0.2)
    try:
        started = time.time()
        assert harness.odeformer_timeout_with_hook(1.0, error_type=MyTimeoutError)(fast)() == "done"
        restored = signal.getitimer(signal.ITIMER_REAL)[0]
        assert 0.0 < restored <= max(0.2 - (time.time() - started), 0.2)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@pytest.mark.skipif(not hasattr(signal, "SIGALRM"), reason="signal timeout handling requires SIGALRM")
def test_odeformer_timeout_hook_counts_when_naked_except_returns_none() -> None:
    class MyTimeoutError(BaseException):
        pass

    counts = {"value": 0}

    @harness.odeformer_timeout_with_hook(
        0.05,
        on_timeout=lambda: counts.__setitem__("value", counts["value"] + 1),
        error_type=MyTimeoutError,
    )
    def catches_timeout() -> None:
        try:
            time.sleep(0.2)
        except BaseException:
            return None
        return None

    assert catches_timeout() is None
    assert counts["value"] == 1


def test_odeformer_timeout_patch_counts_and_restores(monkeypatch) -> None:
    class MyTimeoutError(Exception):
        pass

    def timeout(seconds):
        def decorate(fn):
            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                return fn(*args, **kwargs)

            wrapped.timeout_seconds = seconds
            return wrapped

        return decorate

    def fake_timeout_with_hook(seconds, on_timeout, error_type):
        def decorate(fn):
            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except error_type:
                    on_timeout()
                    raise

            wrapped.timeout_seconds = seconds
            return wrapped

        return decorate

    def original_impl(*_args, **_kwargs):
        raise MyTimeoutError("timeout")

    original = timeout(1.0)(original_impl)
    odeformer_mod = types.ModuleType("odeformer")
    envs_mod = types.ModuleType("odeformer.envs")
    generators_mod = types.ModuleType("odeformer.envs.generators")
    utils_mod = types.ModuleType("odeformer.utils")
    generators_mod._integrate_ode = original
    envs_mod.generators = generators_mod
    utils_mod.MyTimeoutError = MyTimeoutError
    utils_mod.timeout = timeout
    monkeypatch.setitem(sys.modules, "odeformer", odeformer_mod)
    monkeypatch.setitem(sys.modules, "odeformer.envs", envs_mod)
    monkeypatch.setitem(sys.modules, "odeformer.envs.generators", generators_mod)
    monkeypatch.setitem(sys.modules, "odeformer.utils", utils_mod)
    monkeypatch.setattr(harness, "odeformer_timeout_with_hook", fake_timeout_with_hook)

    adapter = object.__new__(harness.ODEFormerAdapter)
    adapter.config = {"integration_timeout_seconds": 10.0}
    adapter.integration_timeout_seconds = adapter._configured_integration_timeout_seconds()
    adapter._timeout_counts = adapter.empty_timeout_counts()
    adapter._integration_outcome_counts = harness.empty_odeformer_integration_outcome_counts()
    adapter._timeout_phase = "fit_candidate_ranking"
    adapter._generators_module = None
    adapter._original_integrate_ode = None
    adapter._original_integrate_ode_wrapped = None
    adapter._install_integration_timeout_patch()

    assert generators_mod._integrate_ode is not original
    assert generators_mod._integrate_ode.timeout_seconds == 10.0
    with pytest.raises(MyTimeoutError):
        generators_mod._integrate_ode()
    fields = adapter.timeout_count_fields()
    assert fields["odeformer_integration_timeout_count_fit_candidate_ranking"] == 1
    assert fields["odeformer_integration_fit_candidate_ranking_call_count"] == 1
    adapter.close()
    assert generators_mod._integrate_ode is original


def test_odeformer_adapter_preserves_none_prediction_for_outcome_and_r2() -> None:
    cell = first_multidimensional_cell()
    adapter = object.__new__(harness.ODEFormerAdapter)
    adapter.model = types.SimpleNamespace(integrate_prediction=lambda *_args, **_kwargs: None)

    prediction = adapter.integrate_expression(cell, "x_0")
    scores = harness.aggregate_r2(cell.state, prediction)
    fields = harness.r2_diagnostic_fields("reconstruction", cell.state, prediction)

    assert prediction is None
    assert scores == {"r2_arithmetic_mean": 0.0, "r2_variance_weighted": 0.0}
    assert fields["reconstruction_prediction_outcome"] == "none"


def test_odeformer_constant_optimization_preserves_none_fit_prediction(monkeypatch) -> None:
    cell = first_multidimensional_cell()

    class FakeConstantOptimizer:
        def __init__(self, **_kwargs):
            pass

        def optimize(self):
            return "x_0", [1.0], None

    def fake_minimize(*_args, **_kwargs):
        return types.SimpleNamespace(nit=3, nfev=5, message="done")

    FakeConstantOptimizer.optimize.__globals__["minimize"] = fake_minimize
    module = types.ModuleType("param_optimizer")
    module.ConstantOptimizer = FakeConstantOptimizer
    monkeypatch.setitem(sys.modules, "param_optimizer", module)

    adapter = object.__new__(harness.ODEFormerAdapter)
    adapter.config = {
        "constant_optimization_init_random": False,
        "constant_optimization_objective": "r2",
        "constant_optimization_eval_objective": "r2",
        "constant_optimization_track_eval_history": True,
    }

    @contextlib.contextmanager
    def phase(_name):
        yield

    adapter.timeout_phase = phase
    optimized = adapter.optimize_constants("x_0", cell)

    assert optimized["fit_prediction"] is None
    assert optimized["params"] == [1.0]


def test_r2_diagnostics_report_reference_without_variance_from_export() -> None:
    cell = first_multidimensional_cell()
    reference = cell.state.copy()
    reference[:, 0] = 0.0
    prediction = reference.copy()
    scores = harness.r2_by_dimension(reference, prediction)
    fields = harness.r2_diagnostic_fields("reconstruction", reference, prediction)
    statuses = json.loads(fields["reconstruction_r2_dimension_status"])
    reasons = json.loads(fields["reconstruction_r2_zero_reason"])
    assert scores[0] == 0.0
    assert fields["reconstruction_prediction_outcome"] == "finite"
    assert statuses[0] == "zero_convention"
    assert reasons[0] == "reference_no_variance"


def test_r2_diagnostics_keep_regular_case_unchanged_from_export() -> None:
    cell = first_multidimensional_cell()
    reference = cell.state
    scores = harness.aggregate_r2(reference, reference.copy())
    fields = harness.r2_diagnostic_fields("reconstruction", reference, reference.copy())
    assert scores == {"r2_arithmetic_mean": 1.0, "r2_variance_weighted": 1.0}
    assert fields["reconstruction_prediction_outcome"] == "finite"
    assert json.loads(fields["reconstruction_r2_dimension_status"]) == ["regular"] * reference.shape[1]
    assert json.loads(fields["reconstruction_r2_zero_reason"]) == [""] * reference.shape[1]


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


def write_repeatability_pair(base: Path, environment_id: str, index: int, changed: bool) -> None:
    record = {
        "system_id": index,
        "fit_initial_condition_set": 1,
        "generalization_initial_condition_set": 2,
        "odeformer_config_id": "beam10_noopt",
        "odeformer_environment_id": environment_id,
        "dimension": 1 + (index % 2),
        "reconstruction_r2_variance_weighted": 1.0,
        "generalization_r2_variance_weighted": 1.0,
        "odeformer_model_raw": "x_0",
        "environment": json.dumps({"torch": "2.0.0+cpu" if environment_id == "reference" else "2.14.0+cpu"}),
    }
    repeat = dict(record)
    if changed:
        repeat["odeformer_model_raw"] = f"x_0 + {index}"
    for run_name, item in [(environment_id, record), (f"{environment_id}_wp_n23", repeat)]:
        path = base / run_name / "records" / f"system_{index:03d}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(item, sort_keys=True) + "\n", encoding="utf-8")


def make_repeatability_fixture(base: Path) -> None:
    for index in range(1, 19):
        write_repeatability_pair(base, "reference", index, True)
    for index in range(19, 23):
        write_repeatability_pair(base, "reference", index, False)
    for index in range(101, 113):
        write_repeatability_pair(base, "candidate", index, True)
    for index in range(113, 117):
        write_repeatability_pair(base, "candidate", index, False)


def repeatability_args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    values = {
        "mode": "faithful",
        "repetitions": 1,
        "shards": 1,
        "shard_index": None,
        "max_hours": 1.0,
        "output_dir": str(tmp_path / "run"),
        "environment_id": "reference",
        "expected_changed": 30,
        "control_seed": 20260924,
        "limit_cells": None,
        "derive_only": False,
        "collect": False,
        "compare_modes": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_repeatability_cell_derivation_counts_by_environment(tmp_path: Path, monkeypatch) -> None:
    make_repeatability_fixture(tmp_path)
    monkeypatch.setattr(run_odeformer_repeatability, "BASE_DIR", tmp_path)
    changed, controls = run_odeformer_repeatability.derive_cells()
    changed_by_environment = pd.Series([item["environment_id"] for item in changed]).value_counts().to_dict()
    controls_by_environment = pd.Series([item["environment_id"] for item in controls]).value_counts().to_dict()
    assert changed_by_environment == {"reference": 18, "candidate": 12}
    assert controls_by_environment == {"reference": 4, "candidate": 4}


def test_repeatability_wrong_environment_aborts_before_first_cell(tmp_path: Path, monkeypatch) -> None:
    make_repeatability_fixture(tmp_path / "records")
    monkeypatch.setattr(run_odeformer_repeatability, "BASE_DIR", tmp_path / "records")
    monkeypatch.setattr(run_odeformer_repeatability, "installed_environment_signature", lambda: {"torch": "2.14.0+cpu"})

    def unexpected_run(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("cell execution must not start after an environment mismatch")

    monkeypatch.setattr(run_odeformer_repeatability, "run_one_cell", unexpected_run)
    with pytest.raises(RuntimeError, match="installed environment does not match reference"):
        run_odeformer_repeatability.run(repeatability_args(tmp_path))


def test_repeatability_collect_merges_shards_and_not_run_records(tmp_path: Path) -> None:
    out_dir = tmp_path / "reference_faithful_2"
    selected_cells = [
        {
            "environment_id": "reference",
            "system_id": 1,
            "fit_initial_condition_set": 1,
            "generalization_initial_condition_set": 2,
            "odeformer_config_id": "beam10_noopt",
            "selection_reason": "changed",
        },
        {
            "environment_id": "reference",
            "system_id": 2,
            "fit_initial_condition_set": 1,
            "generalization_initial_condition_set": 2,
            "odeformer_config_id": "beam10_noopt",
            "selection_reason": "control",
        },
    ]
    (out_dir / "records").mkdir(parents=True)
    (out_dir / "selected_cells.json").write_text(json.dumps(selected_cells), encoding="utf-8")
    for repetition in [1, 2]:
        for cell in selected_cells:
            record = {
                **cell,
                "repeatability_mode": "faithful",
                "repeatability_repetition": repetition,
                "repeatability_selection_reason": cell["selection_reason"],
                "status": "success",
                "odeformer_model_raw": "x_0",
                "reconstruction_r2_variance_weighted": 1.0,
                "generalization_r2_variance_weighted": 1.0,
            }
            if repetition == 2 and cell["system_id"] == 2:
                record["status"] = "not_run_global_time_limit"
            path = out_dir / "records" / run_odeformer_repeatability.repeatability_record_name(cell, repetition, "faithful")
            path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    path = run_odeformer_repeatability.collect(out_dir, repetitions=2)
    records = read_jsonl(path)
    summary = json.loads((out_dir / "collection_summary.json").read_text(encoding="utf-8"))
    assert len(records) == 4
    assert summary == {
        "expected_cell_repetitions": 4,
        "missing_count": 0,
        "not_run_global_time_limit_count": 1,
        "record_count": 4,
    }


def test_repeatability_compare_modes_uses_environment_mode_shards_pattern(tmp_path: Path) -> None:
    columns = {
        "all_bitwise_identical": [True],
        "timeout_count_min": [0],
        "timeout_count_max": [0],
        "r2_gt_0_9_flip": [False],
    }
    for name in ["reference_faithful_4", "candidate_lifted_1", "derive_probe_30"]:
        directory = tmp_path / name
        directory.mkdir()
        pd.DataFrame(columns).to_csv(directory / "cell_summary.csv", index=False)
    path = run_odeformer_repeatability.compare_modes(tmp_path)
    frame = pd.read_csv(path)
    assert set(frame["run"]) == {"reference_faithful_4", "candidate_lifted_1"}
    assert set(frame["environment_id"]) == {"reference", "candidate"}


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


def test_odeformer_grid_rerun_timeouts_is_explicit(tmp_path: Path) -> None:
    path = tmp_path / "records" / "cell.json"
    run_odeformer_grid.atomic_write_json(path, {"status": "timeout", "odeformer_config_id": "beam10_noopt"})
    assert run_odeformer_grid.complete_record(path) is True
    assert run_odeformer_grid.complete_record(path, rerun_timeouts=True) is False


def test_odeformer_grid_repetition_uses_own_subdirectory(tmp_path: Path, monkeypatch) -> None:
    def fake_build(config):
        return object()

    def fake_run(system, fit_cell, target_cell, config, adapter):
        return make_grid_record(fit_cell, target_cell, config)

    monkeypatch.setattr(harness, "build_odeformer_adapter", fake_build)
    monkeypatch.setattr(harness, "run_odeformer_record_with_adapter", fake_run)
    kwargs = {
        "output_dir": str(tmp_path / "grid"),
        "system_ids": {1},
        "config_ids": {"beam10_noopt"},
        "limit": 1,
    }
    default_path = run_odeformer_grid.run(harness.REPO_ROOT / "baselines" / "configs" / "odeformer_grid.json", **kwargs)
    repetition_path = run_odeformer_grid.run(harness.REPO_ROOT / "baselines" / "configs" / "odeformer_grid.json", **kwargs, repetition=2)

    assert default_path == tmp_path / "grid" / "records.jsonl"
    assert repetition_path == tmp_path / "grid" / "rep_002" / "records.jsonl"
    assert (tmp_path / "grid" / "records").is_dir()
    assert (tmp_path / "grid" / "rep_002" / "records").is_dir()
    assert read_jsonl(repetition_path)[0]["odeformer_grid_repetition"] == 2


def test_odeformer_grid_rejects_non_faithful_timeout(tmp_path: Path) -> None:
    config = json.loads((harness.REPO_ROOT / "baselines" / "configs" / "odeformer_grid.json").read_text(encoding="utf-8"))
    config["timeout_seconds_per_cell"] = 1
    config_path = tmp_path / "non_faithful.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="faithful mode"):
        run_odeformer_grid.run(config_path, str(tmp_path / "grid"), system_ids={1}, config_ids={"beam10_noopt"}, limit=1)


def test_odeformer_grid_completion_index_mapping() -> None:
    assert run_odeformer_grid_k8s.completion_to_repetition_shard(0) == (1, 0)
    assert run_odeformer_grid_k8s.completion_to_repetition_shard(41) == (1, 41)
    assert run_odeformer_grid_k8s.completion_to_repetition_shard(42) == (2, 0)
    assert run_odeformer_grid_k8s.completion_to_repetition_shard(125) == (3, 41)


def test_odeformer_grid_shards_cover_504_cells_once() -> None:
    config = run_odeformer_grid.load_json(harness.REPO_ROOT / "baselines" / "configs" / "odeformer_grid.json")
    systems = harness.selected_systems(benchmark(), config)
    configs = run_odeformer_grid.selected_config_objects(config, None)
    cells = [(system, 1, 2) for system in systems] + [(system, 2, 1) for system in systems]
    seen = []
    for shard_index in range(42):
        shard = run_odeformer_grid.shard_cells(cells, shard_index, 42)
        seen.extend(
            (int(system["id"]), fit_ic, target_ic, str(ode_config["config_id"]))
            for system, fit_ic, target_ic in shard
            for ode_config in configs
        )
    assert len(seen) == 504
    assert len(set(seen)) == 504


def test_odeformer_grid_collect_rejects_incomplete_repetition(tmp_path: Path) -> None:
    for rep, count in [(1, 2), (2, 1), (3, 2)]:
        records_dir = tmp_path / "grid" / f"rep_{rep:03d}" / "records"
        records_dir.mkdir(parents=True)
        for index in range(count):
            record = {
                "system_id": index + 1,
                "fit_initial_condition_set": 1,
                "generalization_initial_condition_set": 2,
                "odeformer_config_id": "beam10_noopt",
                "odeformer_grid_repetition": rep,
                "status": "success",
                "odeformer_model_raw": "x_0",
                "reconstruction_r2_variance_weighted": 1.0,
                "generalization_r2_variance_weighted": 1.0,
            }
            (records_dir / f"cell_{index}.json").write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(ValueError, match="repetition 2 incomplete"):
        run_odeformer_grid.collect_repetitions(tmp_path / "grid", expected_per_repetition=2, repetitions=3)


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
        for key in list(record):
            if key.startswith("reconstruction_prediction_") or key.startswith("generalization_prediction_"):
                del record[key]
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
    assert set(summary["reconstruction_prediction_not_captured_count"]) == {2}
    assert int(identity["paired_cell_count"].sum()) == 2
    assert int(identity["identical_expression_count"].sum()) == 1


def test_odeformer_summary_counts_prediction_outcomes_from_export_records(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "source"))
    records = [record for record in read_jsonl(path) if record["method"] == "odeformer"][:2]
    for idx, record in enumerate(records):
        record["status"] = "success"
        record["odeformer_environment_id"] = "reference"
        record["odeformer_config_id"] = "beam10_noopt"
        record["reconstruction_prediction_outcome"] = "finite" if idx == 0 else "odeformer_nan_sentinel"
        record["generalization_prediction_outcome"] = "wrong_shape"
    reference = tmp_path / "reference.jsonl"
    reference.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    paths = summarize_odeformer_grid.run(reference, None, tmp_path / "summary")
    summary = pd.read_csv(paths["summary"])
    assert int(summary["reconstruction_prediction_finite_count"].sum()) == 1
    assert int(summary["reconstruction_prediction_odeformer_nan_sentinel_count"].sum()) == 1
    assert int(summary["reconstruction_prediction_not_captured_count"].sum()) == 0
    assert int(summary["generalization_prediction_wrong_shape_count"].sum()) == 2
