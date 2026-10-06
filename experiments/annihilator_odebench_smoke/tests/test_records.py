import json
import concurrent.futures
from types import SimpleNamespace

import numpy as np

from experiments.annihilator_odebench_smoke.run import _annihilator_record, _baseline_record, _rng, run_command


def synthetic_system(system_id=3):
    t = np.linspace(0.0, 1.0, 5)
    return SimpleNamespace(
        system_id=system_id,
        init=(0.0, 1.0),
        t=t,
        x_train=(np.linspace(0.0, 1.0, 5), np.linspace(1.0, 2.0, 5)),
        numeric_rhs=lambda x: np.asarray(x, dtype=float) + np.asarray(x, dtype=float) ** 2,
    )


def synthetic_setup_row():
    t = np.linspace(0.0, 1.0, 5)
    return {
        "training_domain": {"xmin": 0.0, "xmax": 2.0, "R": 2.0, "mu": 1.0, "scale": 1.0},
        "test_initial_conditions": {"mid": 1.0, "hi": 2.5, "lo": 0.5},
        "test_trajectories": {"mid": t.tolist(), "hi": (2.5 + t).tolist(), "lo": (0.5 + t).tolist()},
    }


def test_record_fields_come_from_synthetic_baseline_path(monkeypatch):
    def fake_fit(_noisy, _t, _method):
        return {
            "coefficients": np.array([0.0, 1.0, 1.0]),
            "terms": ("1", "x", "x^2"),
            "active": np.array([False, True, True]),
            "threshold": 0.001,
            "aicc": 1.0,
            "rss": 1.0,
            "n_regression_rows": 10,
            "residual_source": "synthetic",
            "parameters": {"pysindy_version": "2.1.0"},
        }

    monkeypatch.setattr("experiments.annihilator_odebench_smoke.run.fit_pysindy_baseline", fake_fit)
    record = _baseline_record(synthetic_system(), synthetic_setup_row(), 0.0, 0, "sindy")
    assert record["method"] == "sindy"
    assert record["spec_version"] == 2
    assert record["pysindy_parameters"]["pysindy_version"] == "2.1.0"
    assert record["selected_terms"]
    assert {"term", "coefficient"} <= set(record["selected_terms"][0])
    assert "train_nrmse_x" in record
    assert "test_r2" in record


def test_baseline_noise_stream_differs_between_training_trajectories():
    system = synthetic_system()
    rng = _rng(60000, system.system_id, "sindy")
    noise_a = rng.standard_normal(system.x_train[0].size)
    noise_b = rng.standard_normal(system.x_train[1].size)
    assert not (noise_a == noise_b).all()


def test_annihilator_uses_uniform_2000_point_sample_and_reproducible_noise(monkeypatch):
    seen = []

    def fake_full_search(z, values, eta, seed, _settings, with_bootstrap=True):
        seen.append((z.copy(), values.copy(), eta, seed, with_bootstrap))
        return SimpleNamespace(
            selected_class=None,
            coeffs=None,
            tested_classes=1,
            aml_iterations=0,
            bootstrap_share=None,
            a1=False,
            a2=False,
            a3=False,
        )

    monkeypatch.setattr("experiments.annihilator_odebench_smoke.run.full_search", fake_full_search)
    reference = {"systems": {"3": {"reference_class": [1, 0], "reference_coeffs": [1.0, 0.0], "reference_n_exact": 1}}}
    first = _annihilator_record(synthetic_system(), synthetic_setup_row(), reference, 0.01, 60000)
    second = _annihilator_record(synthetic_system(), synthetic_setup_row(), reference, 0.01, 60000)
    z, values, eta, seed, with_bootstrap = seen[0]
    assert first["annihilator_sample_points"] == 2000
    assert first["spec_version"] == 2
    assert z.size == 2000
    assert np.allclose(z, np.linspace(-1.0, 1.0, 2000))
    assert eta == 0.01
    assert seed == 60000
    assert with_bootstrap is True
    assert np.allclose(values, seen[1][1])
    assert second["annihilator_sample_points"] == 2000


def test_parallel_run_log_contains_numeric_seconds(tmp_path, monkeypatch):
    results = tmp_path / "results"
    results.mkdir()
    (results / "setup.json").write_text(json.dumps({"systems": {"3": synthetic_setup_row()}}))
    (results / "reference.json").write_text(json.dumps({"systems": {"3": {"reference_class": [1, 0], "reference_coeffs": [1.0, 0.0], "reference_n_exact": 1}}}))

    def fake_compute(task):
        sid, eta, seed, method, _results = task
        return {"spec_version": 2, "system_id": sid, "eta": eta, "seed": seed, "method": method, "category": "TRUE_STRUCTURE", "nrmse_f": 0.0}

    class InlinePool:
        def __init__(self, max_workers):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, func, task):
            future = concurrent.futures.Future()
            future.set_result(func(task))
            return future

    monkeypatch.setattr("experiments.annihilator_odebench_smoke.run._compute_record_task", fake_compute)
    monkeypatch.setattr("experiments.annihilator_odebench_smoke.run.concurrent.futures.ProcessPoolExecutor", InlinePool)
    assert run_command(results, [3], [0.0], [0], ["sindy"], workers=2) == 1
    log_record = json.loads((results / "run.log").read_text().splitlines()[0])
    assert isinstance(log_record["seconds"], float)
