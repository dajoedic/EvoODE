import json
import math
import pickle
from types import SimpleNamespace

import numpy as np

from experiments.annihilator_odebench_smoke import end2end


def _fake_worker_task_with_one_failure(task):
    sid, eta, seed, method, protocol, *_rest = task
    if method == "sindy":
        raise RuntimeError("synthetic worker failure")
    return (
        {
            "spec": end2end.SPEC,
            "system_id": int(sid),
            "eta": float(eta),
            "seed": int(seed),
            "method": method,
            "protocol": protocol,
        },
        0.01,
    )


def _fake_worker_task_success(task):
    sid, eta, seed, method, protocol, *_rest = task
    return (
        {
            "spec": end2end.SPEC,
            "system_id": int(sid),
            "eta": float(eta),
            "seed": int(seed),
            "method": method,
            "protocol": protocol,
            "payload": {"array_as_list": [1.0, 2.0], "finite": True},
        },
        0.01,
    )


def synthetic_system(system_id=3):
    t = np.linspace(0.0, 10.0, 11)
    return SimpleNamespace(
        system_id=system_id,
        init=(1.0, 2.0),
        t=t,
        x_train=(1.0 + t, 2.0 + t),
        numeric_rhs=lambda x: np.ones_like(np.asarray(x, dtype=float)),
    )


def test_shared_noisy_inputs_are_bit_equal_for_all_methods():
    system = synthetic_system()
    first = end2end.shared_noisy_trajectories(system, 0.01, 70000)
    method_payloads = {method: end2end.shared_noisy_trajectories(system, 0.01, 70000).noisy for method in end2end.METHODS}
    for method in end2end.METHODS:
        assert np.array_equal(method_payloads[method][0], first.noisy[0])
        assert np.array_equal(method_payloads[method][1], first.noisy[1])
    assert not np.array_equal(first.noise[0], first.noise[1])


def test_split_rule_is_t_le_8_and_t_gt_8():
    fit, val = end2end.split_mask(np.array([0.0, 8.0, 8.01, 10.0]))
    assert fit.tolist() == [True, True, False, False]
    assert val.tolist() == [False, False, True, True]


def test_tie_rule_prefers_simpler_candidate_within_relative_window():
    complex_row = end2end.CandidateResult({"complexity": 4}, lambda x: x, 1.0, None, {})
    simple_row = end2end.CandidateResult({"complexity": 2}, lambda x: x, 1.0005, None, {})
    assert end2end.select_candidate([complex_row, simple_row]) is simple_row


def test_refit_on_full_time_flag_is_recorded(monkeypatch):
    system = synthetic_system()
    setup = {"test_initial_conditions": {"mid": 1.0, "hi": 2.0, "lo": 3.0}, "test_trajectories": {"mid": system.x_train[0].tolist(), "hi": system.x_train[0].tolist(), "lo": system.x_train[0].tolist()}}
    reference = {"systems": {"3": {"reference_class": [1, 0], "reference_coeffs": [1.0, 0.0], "reference_n_exact": 1}}}
    selected = end2end.CandidateResult({"threshold": 0.1, "complexity": 1}, lambda x: np.ones_like(np.asarray(x, dtype=float)), 0.0, None, {})
    full_t_seen = []

    def fake_candidates(_system, _noisy, _train_indices, _method):
        return [selected]

    def fake_refit(full_system, _noisy, _train_indices, _method, _selected):
        full_t_seen.append(full_system.t.copy())
        return {
            "fhat": lambda x: np.ones_like(np.asarray(x, dtype=float)),
            "coefficients": np.array([1.0]),
            "terms": ("1",),
            "active": np.array([True]),
            "threshold": 0.1,
            "parameters": {},
        }

    monkeypatch.setattr(end2end, "baseline_candidates", fake_candidates)
    monkeypatch.setattr(end2end, "refit_baseline_full", fake_refit)
    record = end2end.fit_record(system, setup, reference, 0.0, 0, "sindy", "P1_from_AB1")
    assert record["spec"] == end2end.SPEC
    assert record["refit_on_full_time"] is True
    assert np.array_equal(full_t_seen[0], system.t)


def test_fit_record_removes_non_serializable_candidate_payload(monkeypatch):
    system = synthetic_system()
    setup = {"test_initial_conditions": {"mid": 1.0, "hi": 2.0, "lo": 3.0}, "test_trajectories": {"mid": system.x_train[0].tolist(), "hi": system.x_train[0].tolist(), "lo": system.x_train[0].tolist()}}
    reference = {"systems": {"3": {"reference_class": [1, 0], "reference_coeffs": [1.0, 0.0], "reference_n_exact": 1}}}
    selected = end2end.CandidateResult(
        {"threshold": 0.1, "complexity": 1, "fit": {"fhat": lambda x: x, "coefficients": np.array([1.0])}},
        lambda x: np.ones_like(np.asarray(x, dtype=float)),
        0.0,
        None,
        {},
    )

    monkeypatch.setattr(end2end, "baseline_candidates", lambda *_args: [selected])
    monkeypatch.setattr(
        end2end,
        "refit_baseline_full",
        lambda *_args: {
            "fhat": lambda x: np.ones_like(np.asarray(x, dtype=float)),
            "coefficients": np.array([1.0]),
            "terms": ("1",),
            "active": np.array([True]),
            "threshold": 0.1,
            "parameters": {},
        },
    )

    record = end2end.fit_record(system, setup, reference, 0.0, 0, "sindy", "P1_from_AB1")

    candidate = record["candidate_validations"][0]["candidate"]
    assert "fhat" not in candidate["fit"]
    assert candidate["fit"]["coefficients"] == [1.0]
    pickle.dumps(record)
    json.dumps(record, allow_nan=True)


def test_annihilator_refit_failure_is_recorded(monkeypatch):
    system = synthetic_system()
    setup = {"test_initial_conditions": {"mid": 1.0, "hi": 2.0, "lo": 3.0}, "test_trajectories": {"mid": system.x_train[0].tolist(), "hi": system.x_train[0].tolist(), "lo": system.x_train[0].tolist()}}
    reference = {"systems": {"3": {"reference_class": [1, 0], "reference_coeffs": [1.0, 0.0], "reference_n_exact": 1}}}
    selected = end2end.CandidateResult({"kind": "annihilator", "class": [1, 0], "complexity": 2}, lambda x: np.ones_like(np.asarray(x, dtype=float)), 0.0, None, {})

    monkeypatch.setattr(end2end, "annihilator_candidates", lambda *_args, **_kwargs: [selected])
    monkeypatch.setattr(end2end, "reference_for_system", lambda *_args: ((1, 0), [1.0], 1))
    monkeypatch.setattr(end2end, "n_exact_for_class", lambda *_args: 1)

    def fail_refit(*_args, **_kwargs):
        raise RuntimeError("spline failed")

    monkeypatch.setattr(end2end, "refit_annihilator_full", fail_refit)
    record = end2end.fit_record(system, setup, reference, 0.0, 0, "annihilator", "P1_from_AB1", spec=end2end.SPEC_V2)
    assert record["selected_model"]["refit_fail_reason"] == "refit_RuntimeError"
    assert record["reconstruction_r2"] == [-math.inf]


def test_resampling_averages_equal_x_values_and_uses_2000_points():
    x_grid, z_grid, f_grid = end2end.resample_state_derivative(np.array([2.0, 1.0, 1.0, 3.0]), np.array([20.0, 2.0, 4.0, 30.0]))
    assert x_grid.size == 2000
    assert z_grid.size == 2000
    assert f_grid.size == 2000
    assert x_grid[0] == 1.0
    assert x_grid[-1] == 3.0
    assert f_grid[0] == 3.0


def test_resampling_uses_cubic_spline_for_smooth_function_on_irregular_points():
    x = np.array([-1.0, -0.3, -0.3, 0.4, 1.7, 2.2])
    f = 0.25 * x**3 - 0.5 * x**2 + 2.0 * x - 1.0
    f[1] -= 0.125
    f[2] += 0.125
    x_grid, _z_grid, f_grid = end2end.resample_state_derivative(x, f, points=401)
    expected = 0.25 * x_grid**3 - 0.5 * x_grid**2 + 2.0 * x_grid - 1.0
    relative_error = np.linalg.norm(f_grid - expected) / np.linalg.norm(expected)
    assert relative_error < 1e-8


def test_v2_resampling_smooths_noisy_function_better_than_linear_interpolation():
    rng = np.random.default_rng(123)
    x = np.sort(rng.uniform(-2.0, 2.0, 1000))
    truth = np.sin(2.0 * x) + 0.2 * x
    noisy = truth + rng.normal(0.0, 0.2, x.size)
    x_grid, _z_grid, f_grid, info = end2end.resample_state_derivative_v2(x, noisy, points=500, bins=80)
    order = np.argsort(x)
    linear = np.interp(x_grid, x[order], noisy[order])
    expected = np.sin(2.0 * x_grid) + 0.2 * x_grid
    smooth_error = np.linalg.norm(f_grid - expected) / np.linalg.norm(expected)
    linear_error = np.linalg.norm(linear - expected) / np.linalg.norm(expected)
    assert smooth_error < 0.7 * linear_error
    assert info["method"] == "binned_smoothing_spline"
    assert info["smoothing_lambda"] == "gcv_lam_none" or isinstance(info["smoothing_lambda"], float)


def test_v2_resampling_handles_many_nearly_equal_x_values():
    cluster = np.linspace(0.999999, 1.000001, 300)
    spread = np.linspace(0.0, 2.0, 100)
    x = np.concatenate([cluster, spread])
    f = x**2
    x_grid, z_grid, f_grid, info = end2end.resample_state_derivative_v2(x, f, points=101, bins=40)
    assert x_grid.size == 101
    assert z_grid.size == 101
    assert np.all(np.isfinite(f_grid))
    assert info["nonempty_bins"] > 5


def test_sanity_exact_chain_documents_system_7_exception_without_failed_pass(monkeypatch, tmp_path):
    systems = {sid: SimpleNamespace(system_id=sid) for sid in (3, 7, 19, 21)}
    reference = {"systems": {str(sid): {"reference_class": [1, 0], "reference_coeffs": [1.0], "reference_n_exact": 1} for sid in systems}}
    (tmp_path / "setup.json").write_text("{}")
    (tmp_path / "reference.json").write_text("{}")
    monkeypatch.setattr(end2end, "_copy_setup_reference", lambda _results: None)
    monkeypatch.setattr(end2end, "synthetic_system", lambda: (SimpleNamespace(system_id=999), {}, reference))
    monkeypatch.setattr(end2end, "fit_record", lambda *_args, **_kwargs: {"selected_validation_nrmse_x": 0.0})
    monkeypatch.setattr(end2end, "load_systems", lambda: systems)
    monkeypatch.setattr(end2end, "load_json", lambda path: reference if path.name == "reference.json" else {})
    monkeypatch.setattr(end2end, "reference_for_system", lambda system, _ref: ((1, 0), [1.0], 1))
    monkeypatch.setattr(end2end, "shared_noisy_trajectories", lambda *_args: SimpleNamespace())
    monkeypatch.setattr(end2end, "annihilator_grid_from_training", lambda *_args, **_kwargs: (SimpleNamespace(), np.array([0.0, 1.0]), np.array([-1.0, 1.0]), np.array([1.0, 1.0]), {}))
    monkeypatch.setattr(end2end, "fit_annihilator_candidate", lambda *_args: (lambda x: x, {"aml_iterations": 1}, None))

    def fake_validation(system, _fhat, _noisy, _indices):
        if system.system_id == 7:
            return math.inf, "LEADING_ZERO_IN_TRAINING_DOMAIN"
        return 0.0, None

    monkeypatch.setattr(end2end, "validation_error", fake_validation)
    sanity = end2end.sanity_command(tmp_path)
    assert sanity["passed"] is True
    assert sanity["exact_derivative_reference_class"]["7"]["passed"] is False
    assert sanity["exact_derivative_reference_class"]["7"]["documented_exception"] is True


def test_v2_sanity_excludes_system_7_and_19_exceptions(monkeypatch, tmp_path):
    systems = {sid: SimpleNamespace(system_id=sid) for sid in (3, 7, 19, 21)}
    reference = {"systems": {str(sid): {"reference_class": [1, 0], "reference_coeffs": [1.0], "reference_n_exact": 1} for sid in systems}}
    (tmp_path / "setup.json").write_text("{}")
    (tmp_path / "reference.json").write_text("{}")
    monkeypatch.setattr(end2end, "_copy_setup_reference", lambda _results: None)
    monkeypatch.setattr(end2end, "synthetic_system", lambda: (SimpleNamespace(system_id=999), {}, reference))
    monkeypatch.setattr(end2end, "fit_record", lambda *_args, **_kwargs: {"selected_validation_nrmse_x": 0.0})
    monkeypatch.setattr(end2end, "load_systems", lambda: systems)
    monkeypatch.setattr(end2end, "load_json", lambda path: reference if path.name == "reference.json" else {})
    monkeypatch.setattr(end2end, "reference_for_system", lambda system, _ref: ((1, 0), [1.0], 1))
    monkeypatch.setattr(end2end, "shared_noisy_trajectories", lambda *_args: SimpleNamespace())
    monkeypatch.setattr(end2end, "annihilator_grid_from_training", lambda *_args, **_kwargs: (SimpleNamespace(), np.array([0.0, 1.0]), np.array([-1.0, 1.0]), np.array([1.0, 1.0]), {}))
    monkeypatch.setattr(end2end, "fit_annihilator_candidate", lambda *_args: (lambda x: x, {"aml_iterations": 1}, None))

    def fake_validation(system, _fhat, _noisy, _indices):
        if system.system_id in {7, 19}:
            return math.inf, "documented"
        return 0.0, None

    monkeypatch.setattr(end2end, "validation_error", fake_validation)
    sanity = end2end.sanity_command(tmp_path, spec=end2end.SPEC_V2)
    assert sanity["passed"] is True
    assert sanity["exact_derivative_reference_class"]["7"]["documented_exception"] is True
    assert sanity["exact_derivative_reference_class"]["19"]["documented_exception"] is True
    assert sanity["exact_derivative_reference_class"]["3"]["passed"] is True
    assert sanity["exact_derivative_reference_class"]["21"]["passed"] is True


def test_18_classes_are_filtered_from_v3_class_order():
    classes = end2end.e2e_classes()
    assert len(classes) == 18
    assert classes == tuple((r, d) for r, d in end2end.class_order() if (r + 1) * (d + 1) <= 12)
    assert classes[0] == (1, 0)
    assert classes[-1] == (5, 1)


def test_structure_exact_and_superset_for_baselines_and_annihilator(monkeypatch):
    assert end2end.baseline_category(3, {"x", "x^2"}) == (True, False, "exact")
    assert end2end.baseline_category(3, {"1", "x", "x^2"}) == (False, True, "true_plus")
    system = SimpleNamespace(system_id=3, sympy_expr=None)
    monkeypatch.setattr(end2end, "training_domain", lambda _system: SimpleNamespace(a=0.0, b=1.0))
    monkeypatch.setattr(end2end, "nullspace", lambda _expr, _domain, r, d: (1 if (r, d) == (2, 0) else 0, None))
    assert end2end.n_exact_for_class(system, (2, 0)) == 1


def test_decision_function_uses_synthetic_record_fields():
    records = []
    for sid in (3, 7, 19, 21):
        for seed in range(5):
            for method in end2end.METHODS:
                r2 = 0.8 if method == "annihilator" and sid == 21 else (0.95 if method == "annihilator" else 0.9)
                records.append(
                    {
                        "spec": end2end.SPEC,
                        "system_id": sid,
                        "eta": 0.01,
                        "seed": seed,
                        "method": method,
                        "protocol": "P2",
                        "generalization_r2": [r2, r2, r2],
                        "structure_exact": method != "sindy",
                    }
                )
    decision = end2end.evaluate_decision(records)
    assert decision["decision"] == end2end.DISCUSS_LABEL
    assert decision["G"] == 3
    assert decision["S"] is True


def test_failed_integration_maps_to_infinity_metrics():
    t = np.linspace(0.0, 10.0, 11)

    def bad_fhat(_x):
        raise RuntimeError("boom")

    pred, fail = end2end.integrate_fhat(t, bad_fhat, 1.0)
    assert pred is None
    assert fail == "RuntimeError"
    system = synthetic_system()
    rows = end2end.evaluate_items(system, bad_fhat, [("bad", 1.0, np.ones_like(t))])
    assert rows[0]["nrmse_x"] == math.inf
    assert rows[0]["r2"] == -math.inf


def test_run_command_real_process_pool_writes_serializable_synthetic_records(monkeypatch, tmp_path):
    monkeypatch.setattr(end2end, "SYSTEM_IDS", (999,))
    monkeypatch.setattr(end2end, "PROTOCOLS", ("P2",))
    monkeypatch.setattr(end2end, "_compute_record_task_with_seconds", _fake_worker_task_success)
    written = end2end.run_command(tmp_path, [999], [0.0], [0], list(end2end.METHODS), workers=2)
    records = end2end.load_records(tmp_path / "records.jsonl")

    assert written == 3
    assert len(records) == 3
    assert {record["method"] for record in records} == set(end2end.METHODS)
    for record in records:
        pickle.dumps(record)
        json.dumps(record, allow_nan=True)


def test_reuse_baselines_copies_only_baselines_without_duplicates(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    rows = [
        {"spec": end2end.SPEC, "system_id": 999, "eta": 0.0, "seed": 0, "method": "sindy", "protocol": "P2", "payload": 1},
        {"spec": end2end.SPEC, "system_id": 999, "eta": 0.0, "seed": 0, "method": "wsindy", "protocol": "P2", "payload": 2},
        {"spec": end2end.SPEC, "system_id": 999, "eta": 0.0, "seed": 0, "method": "annihilator", "protocol": "P2", "payload": 3},
    ]
    (source / "records.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))

    first = end2end.reuse_baselines(target, source, end2end.SPEC_V2)
    second = end2end.reuse_baselines(target, source, end2end.SPEC_V2)
    copied = end2end.load_records(target / "records.jsonl")

    assert first == 2
    assert second == 0
    assert {row["method"] for row in copied} == {"sindy", "wsindy"}
    assert all(row["spec"] == end2end.SPEC_V2 for row in copied)
    assert all(row["reused_from"] == "end2end_v1" for row in copied)


def test_reused_baseline_matches_recomputed_synthetic_record_except_reuse_fields(monkeypatch, tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    recomputed = _fake_worker_task_success((999, 0.0, 0, "sindy", "P2", target, end2end.SPEC_V2))[0]
    recomputed["spec"] = end2end.SPEC_V2
    source_record = dict(recomputed)
    source_record["spec"] = end2end.SPEC
    (source / "records.jsonl").write_text(json.dumps(source_record) + "\n")

    copied = end2end.reuse_baselines(target, source, end2end.SPEC_V2)
    reused = end2end.load_records(target / "records.jsonl")[0]
    comparable_reused = {k: v for k, v in reused.items() if k not in {"reused_from"}}

    assert copied == 1
    assert comparable_reused == recomputed


def test_run_command_real_process_pool_records_failed_task_and_continues(monkeypatch, tmp_path):
    monkeypatch.setattr(end2end, "SYSTEM_IDS", (999,))
    monkeypatch.setattr(end2end, "PROTOCOLS", ("P2",))
    monkeypatch.setattr(end2end, "_compute_record_task_with_seconds", _fake_worker_task_with_one_failure)

    written = end2end.run_command(tmp_path, [999], [0.0], [0], ["sindy", "wsindy"], workers=2)
    end2end._write_done_marker(tmp_path, written, end2end._LAST_RUN_FAILED_TASKS)

    records = end2end.load_records(tmp_path / "records.jsonl")
    failed = [json.loads(line) for line in (tmp_path / "failed_tasks.jsonl").read_text().splitlines()]
    done = json.loads((tmp_path / "DONE").read_text())
    run_log = (tmp_path / "run.log").read_text()

    assert written == 1
    assert len(records) == 1
    assert records[0]["method"] == "wsindy"
    assert len(failed) == 1
    assert failed[0]["method"] == "sindy"
    assert failed[0]["event"] == "task_failed"
    assert "synthetic worker failure" in failed[0]["traceback"]
    assert "synthetic worker failure" in run_log
    assert done["failed_tasks"] == 1
