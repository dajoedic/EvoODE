import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baselines import harness
from baselines import run_pysr_noise
from baselines.tests.test_run_odeformer_noise import copy_real_export_fixture


class TrueEquationAdapter:
    def __init__(self, config):
        self.config = dict(config)
        self.fit_state_first_value = None

    def close(self):
        pass

    def fit_equations(self, fit_cell):
        self.fit_state_first_value = float(fit_cell.state[0, 0])
        return {
            "expression": "0.303030303030303 - 0.360750360750361*x_0",
            "candidate_count": 1,
            "derivative_target_shape": [512, 1],
            "selected_hyperparams": [{"finite_difference_order": 2, "smoother_window_length": None, "score": 1.0}],
        }

    def integrate_expression(self, cell, _expression):
        return cell.state.copy(), "success"


def test_pysr_symbolic_terms_use_shared_canonical_expansion() -> None:
    raw, pruned, outside = harness.symbolic_active_terms_by_equation("exp(x_0) + x_0*x_1 | sin(x_1)", 2)

    assert raw == [{"u1*u2"}, {"sin(u2)"}]
    assert pruned == [{"u1*u2"}, {"sin(u2)"}]
    assert outside == [["exp(x_0)"], []]


def test_run_pysr_record_with_fake_true_equation_hits_structure() -> None:
    time = np.linspace(0.0, 1.0, 512)
    state = np.exp(-time).reshape((-1, 1))
    cell = harness.TrajectoryCell(1, 1, 1, time, state, "time", "state")
    system = {"id": 1, "dim": 1, "substituted": [["0.303030303030303 - 0.360750360750361*x_0"]]}

    record = harness.run_pysr_record_with_adapter(system, cell, cell, harness.pysr_default_config(), TrueEquationAdapter({}))

    assert record["status"] == "success"
    assert record["reconstruction_r2_arithmetic_mean"] == 1.0
    assert record["generalization_r2_arithmetic_mean"] == 1.0
    assert record["structure_hit_raw"] is True
    assert record["structure_hit_pruned"] is True
    assert record["pysr_outside_basis_term_count"] == 0
    assert json.loads(record["pysr_selected_hyperparams"])[0]["finite_difference_order"] == 2


def test_pysr_hyper_grid_matches_odeformer_wrapper_shape() -> None:
    grid = harness.pysr_hyperparameter_grid(harness.pysr_default_config())

    assert len(grid) == 6
    assert {item["finite_difference_order"] for item in grid} == {2, 3, 4}
    assert {item["smoother_window_length"] for item in grid} == {None, 15}


def test_pysr_record_fits_only_observed_training_cell() -> None:
    fit_time = np.linspace(0.0, 1.0, 512)
    fit_state = np.exp(-fit_time).reshape((-1, 1))
    target_state = np.full_like(fit_state, 999.0)
    fit_cell = harness.TrajectoryCell(1, 1, 1, fit_time, fit_state, "time", "state")
    target_cell = harness.TrajectoryCell(1, 2, 1, fit_time, target_state, "time", "state")
    system = {"id": 1, "dim": 1, "substituted": [["0.303030303030303 - 0.360750360750361*x_0"]]}
    adapter = TrueEquationAdapter({})

    harness.run_pysr_record_with_adapter(system, fit_cell, target_cell, harness.pysr_default_config(), adapter)

    assert adapter.fit_state_first_value == float(fit_state[0, 0])
    assert adapter.fit_state_first_value != float(target_state[0, 0])


def test_noise_runner_writes_required_outputs_with_fake_adapter(tmp_path: Path, monkeypatch) -> None:
    index_path = copy_real_export_fixture(tmp_path)
    output_dir = tmp_path / "out"
    config_path = tmp_path / "pysr_config.json"
    config = json.loads((REPO_ROOT / "baselines" / "configs" / "pysr_faithful.json").read_text(encoding="utf-8"))
    config["seeds"] = [1]
    config_path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(harness, "build_pysr_adapter", lambda config: TrueEquationAdapter(config))

    paths = run_pysr_noise.run_noise_pysr(config_path, [index_path], output_dir, seeds=[1])
    details = pd.read_csv(paths["details"])
    checks = pd.read_csv(paths["export_checks"])
    summary = pd.read_csv(paths["summary"])

    assert set(paths) == {"details", "records", "summary", "export_checks"}
    assert len(details) == 2
    assert set(details["status"]) == {"success"}
    assert set(details["method"]) == {"pysr", "pysr_poly"}
    assert set(details["pysr_config_id"]) == {"pysr", "pysr_poly"}
    assert set(details["pysr_seed"]) == {1}
    assert set(details["reconstruction_r2_arithmetic_mean"]) == {1.0}
    assert set(details["generalization_r2_arithmetic_mean"]) == {1.0}
    assert set(details["pysr_unary_operators"]) == {
        '["cos","exp","sin","neg","log","sqrt"]',
        "[]",
    }
    assert details["pysr_structure_hit_raw"].astype(bool).all()
    assert bool(checks.loc[0, "hash_verified"])
    assert set(summary["method"]) == {"pysr", "pysr_poly"}
    assert set(summary["success_count"]) == {1}


def test_build_comparison_marks_missing_odeformer_source(tmp_path: Path) -> None:
    details = pd.DataFrame(
        [
            {
                "system_id": 1,
                "source_initial_condition_set": 1,
                "noise_sigma": 0.01,
                "subsample_rho": 0.0,
                "noise_realization": 1,
                "pysr_seed": 1,
            }
        ]
    )

    joined = run_pysr_noise.build_comparison(details, [], [], [])

    assert joined.loc[0, "evogrow_source_path"] == "missing"
    assert joined.loc[0, "sindy_source_path"] == "missing"
    assert joined.loc[0, "odeformer_source_path"] == "missing"
