"""WP-FA2 algorithm checks and controls on the permitted real inputs."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "analysis"))
from scripts.aggregate import run_sideproject_residual_growth as study


def test_sparse_target_and_enumeration():
    fit = study.WeakFit(np.eye(5), np.array([3., 0., 2., 0., 0.]))
    truth = {0, 2}
    q1 = study.q1_metrics(fit, truth)
    assert q1["q1_rank"] == 1
    assert q1["subset_count"] == math.comb(5, 2)
    result = study.q2_metrics(fit, truth, {0})
    assert result["g_added_indices"] == [2]
    assert result["g_q2a"] and result["g_q2b"]
    assert result["random_addition_probability"] == .25


def test_ties_against_truth_and_basis_order():
    fit = study.WeakFit(np.array([[1., 1., 0.], [0., 0., 1.]]), np.array([1., 0.]))
    result = study.q1_metrics(fit, {0})
    assert result["q1_rank"] == 2
    assert result["subset_count"] == math.comb(3, 1)
    assert fit.forward([], 1)[0] == [0]
    assert fit.backward({0, 1}, 1) == {1}  # Lowest removed index wins a tie.


def test_projection_distinguishes_g_from_omp():
    design = np.array([[1., 10., 0.], [0., 1., 1.], [0., 0., 1.]])
    fit = study.WeakFit(design, np.array([1., 1., 0.]))
    assert fit.forward({0}, 1, "g")[0] == [1]
    assert fit.forward({0}, 1, "omp")[0] == [2]


def test_auc_with_ties_and_undefined_groups():
    assert study.auc_counts([1., 2.], [0., 1.]) == (3.5, 4, .875)
    assert math.isnan(study.auc_counts([], [1.])[2])
    assert math.isnan(study.auc_counts([math.nan], [1.])[2])


def test_backward_runs_without_addition():
    fit = study.WeakFit(np.eye(4), np.array([3., 0., 2., 0.]))
    result = study.q2_metrics(fit, {0, 2}, {0, 1, 2, 3})
    assert result["m"] == 0
    assert result["g_added_indices"] == []
    assert result["g_final_indices"] == [0, 2]
    assert result["g_q2b"]
    assert result["rho"] == 0.


def test_qr_preserves_raw_design_sse_and_condition():
    # Fixed, ill-conditioned columns; no random fixture or Gram matrix.
    x = np.linspace(-1., 1., 60)
    design = np.column_stack([np.ones(60), x, x + 1.e-8 * x ** 2, x ** 3])
    target = np.sin(x) + .3
    fit = study.WeakFit(design, target)
    scaled = design / np.linalg.norm(design, axis=0)
    for support in ([], [0], [0, 1], [0, 1, 2, 3]):
        raw = target.copy()
        if support:
            a = scaled[:, support]
            raw -= a @ np.linalg.lstsq(a, target, rcond=None)[0]
        assert fit.sse(support) == pytest.approx(float(raw @ raw), rel=1.e-6, abs=1.e-15)
    assert fit.condition_number == pytest.approx(np.linalg.cond(scaled), rel=1.e-8)


def test_real_inventory_and_empty_start_f0_consistency():
    _, systems = study.load_exact_supports(REPO_ROOT / study.SUPPORT)
    study.verify_basis_consistency(systems)
    starts = study.load_starts(REPO_ROOT, systems)
    assert sum(r["cells_collapsed"] for r in starts) == 708
    assert all(r["s0"] == sorted(r["s0"]) for r in starts)
    selected = systems[:3]
    trajectories = study.load_exported_trajectories(REPO_ROOT / study.EXPORT, [int(s["system_id"]) for s in selected])
    count = 0
    for system in selected:
        names = [t.name for t in study.phasec_basis(int(system["dim"]))]
        for ic in (1, 2):
            trajectory = trajectories[int(system["system_id"]), ic]
            a, b, _ = study.build_design(trajectory.time, trajectory.state, 0, "weak", study.phasec_basis(int(system["dim"])))
            truth = {names.index(n) for n in system["support_terms"][0]}
            result = study.q2_metrics(study.WeakFit(a, b), truth, set())
            assert sorted(result["g_added_indices"]) == result["f0_indices"]
            assert result["g_final_indices"] == result["f0_indices"]
            count += 1
    assert count == 6


def test_inventory_error_derived_from_real_row(tmp_path):
    # Preserve the real inventory schema, visibly alter one actual exact row.
    frame = pd.read_csv(REPO_ROOT / study.INVENTORY)
    index = frame.index[(frame.kind == "pruned") & (frame["class"] == "exact")][0]
    frame.loc[index, "missing"] = 1
    target = tmp_path / study.INVENTORY
    target.parent.mkdir(parents=True)
    frame.to_csv(target, index=False)
    _, systems = study.load_exact_supports(REPO_ROOT / study.SUPPORT)
    with pytest.raises(ValueError, match="classification mismatch"):
        study.load_starts(tmp_path, systems)
