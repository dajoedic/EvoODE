"""Q3 tests; P-04 fixtures are derived from an actual campaign record."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from scripts.aggregate.build_sideproject_q3_weak_starts import (
    flatten_parameters, weak_coefficients, phasec_basis, build_design,
)
from scripts.aggregate.aggregate_sideproject_q3 import (
    P04, load_p04, aggregate_units, summarize_rules, compare_loss, run,
    CONTROLS,
)
from scripts.aggregate.aggregate_phasec_restart_curve import best_start


@pytest.fixture
def real_record():
    # The field inventory and null values come from this real record, not a plan.
    path = P04 / "shard_001_of_036/starts.jsonl"
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


@pytest.fixture
def small_case(real_record):
    ref = copy.deepcopy(real_record)
    # Explicit controlled edits: one synthetic seed, prescribed start losses/R².
    ref["seed"] = 7
    for s in ref["reference_starts"]:
        s.update(loss=10.0, r2=0.9)
        s["fit_meta"]["loss_evals"] = 2
    ref["reference_starts"][2].update(loss=1.0, r2=0.91)
    ref["reference_starts"][9].update(loss=0.5, r2=0.95)
    unit = dict(unit_id="sys0001_ic1", system_id=ref["system_id"],
                initial_condition_set=ref["initial_condition_set"], dim=1,
                stratum="dim1", trajectory_sha256=ref["trajectory_hash"]["state_sha256"],
                equations=[dict(term_names=eq) for eq in ref["true_structure"]], p0=[11.0, -0.3])
    result = {k: copy.deepcopy(unit[k]) for k in ("unit_id", "system_id", "initial_condition_set", "dim", "stratum", "trajectory_sha256")}
    result["trajectory_control"] = dict(passed=True)
    result["W0"] = copy.deepcopy(ref["reference_starts"][0])
    result["W1"] = copy.deepcopy(ref["reference_starts"][2])
    return unit, result, ref


def test_parameter_order_two_equation_structure():
    active = [[3, 1], [2, 5]]  # StructureSpec preserves even unsorted stored order.
    coefficients = [{1: 1.25, 3: -2.0}, {5: 7.0, 2: 0.5}]
    assert flatten_parameters(active, coefficients) == [-2.0, 1.25, 0.5, 7.0]
    with pytest.raises(ValueError):
        flatten_parameters(active, coefficients[:1])
    # Evaluate the constructed RHS independently, equation by equation.
    phi = np.array([1.0, 2.0, 4.0, 8.0, 16.0])
    p = flatten_parameters(active, coefficients)
    assert np.dot(p[:2], phi[np.array(active[0]) - 1]) == -6.75
    assert np.dot(p[2:], phi[np.array(active[1]) - 1]) == 113.0


def test_exact_affine_linear_weak_coefficients():
    # x'=2; y'=1 - .75*x. State and weak integrands are exact polynomials.
    time = np.linspace(0, 2, 257)
    state = np.column_stack((0.5 + 2 * time, 2 + 0.625 * time - 0.75 * time**2))
    terms = phasec_basis(2)
    for eq, indices, expected in ((0, [0], [2.0]), (1, [0, 1], [1.0, -0.75])):
        design, target, _ = build_design(time, state, eq, "weak", terms)
        coef, sse = weak_coefficients(design, target, indices)
        np.testing.assert_allclose(coef, expected, rtol=1e-12, atol=1e-12)
        assert sse < 1e-25


def test_real_record_shape(real_record):
    assert "success" not in real_record
    assert "loss_evals" not in real_record["reference_starts"][0]
    assert isinstance(real_record["reference_starts"][0]["fit_meta"]["loss_evals"], int)
    assert real_record["error"] is None
    assert len(real_record["reference_starts"]) == 10


def test_best_of_k_uses_loss_and_preserves_first_tie(real_record):
    record = copy.deepcopy(real_record)
    starts = record["reference_starts"]
    for s in starts:
        s["loss"] = 20.0
    starts[1].update(loss=1.0, r2=-1.0)
    starts[2].update(loss=1.0, r2=1.0)
    starts[9]["loss"] = 0.5
    assert best_start(record, "reference", 1) is starts[0]
    assert best_start(record, "reference", 3) is starts[1]
    assert best_start(record, "reference", 10) is starts[9]


def test_aggregation_counts_evaluations_and_rules(small_case):
    unit, result, ref = small_case
    rows, rules = aggregate_units([unit], [result], [ref], require_complete=False)
    assert rows[0]["P04_seed7_best3_loss_evals_sum"] == 6
    assert rows[0]["P04_seed7_best10_loss_evals_sum"] == 20
    assert rows[0]["weak_abs_gt_10_count"] == 1
    assert rows[0]["W0_success"] is False  # Strict R² > 0.9.
    assert rows[0]["W1_vs_P04_seed7_best10_loss"] == "worse"
    assert all(r["decision"] == "pass" for r in rules)
    assert all((r["numerator"], r["denominator"], r["reference_numerator"], r["reference_denominator"]) == (1, 1, 1, 1) for r in rules)
    rows[0]["W1_success"] = False
    assert all(r["decision"] == "fail" for r in summarize_rules(rows, [7]))
    rows[0]["stratum"] = "dim3_bound_infeasible"
    assert all(r["decision"] == "reported_only" and r["passed"] is None for r in summarize_rules(rows, [7]))


def test_unit_vs_reference_cell_denominators(small_case):
    unit, result, ref = small_case
    refs = [copy.deepcopy(ref) for _ in range(3)]
    for record, seed in zip(refs, [7, 42, 123]):
        record["seed"] = seed
    rows, rules = aggregate_units([unit], [result], refs, require_complete=False)
    assert all(r["denominator"] == 1 and r["reference_denominator"] == 3 for r in rules)


@pytest.mark.parametrize("value,reference,expected", [(1.0, 1.0, "equal"), (1.0 + 5e-13, 1.0, "equal"), (2e-15, 1e-15, "worse"), (0.0, 0.0, "equal"), (0.5, 1.0, "better")])
def test_relative_loss_comparison(value, reference, expected):
    assert compare_loss(value, reference) == expected


def test_missing_duplicate_and_failed_controls_abort(small_case):
    unit, result, ref = small_case
    for results in ([], [result, result]):
        with pytest.raises(ValueError, match="Q3 units"):
            aggregate_units([unit], results, [ref], require_complete=False)
    with pytest.raises(ValueError, match="60"):
        aggregate_units([unit], [result], [ref])
    result["trajectory_control"]["passed"] = False
    with pytest.raises(ValueError, match="Trajectory control"):
        aggregate_units([unit], [result], [ref], require_complete=False)


def test_reference_uses_true_support_not_oracle(small_case):
    unit, result, ref = small_case
    ref["oracle_starts"] = None
    rows, _ = aggregate_units([unit], [result], [ref], require_complete=False)
    assert rows[0]["P04_seed7_best10_loss"] == 0.5
    ref["true_structure"] = [[]]
    with pytest.raises(ValueError, match="true structure"):
        aggregate_units([unit], [result], [ref], require_complete=False)


def test_load_real_p04():
    rows, paths = load_p04(P04)
    assert len(rows) == 180
    assert len(paths) == 36
    assert sum(r["oracle_is_true_subset"] for r in rows) == 101


def test_complete_real_shape_fixture_and_missing_unit():
    # Real support/export identities and real per-start schemas; W arms here are
    # explicitly copied P-04 values solely to test aggregation, never Q3 results.
    weak = json.loads((ROOT / "analysis/data/sideproject_residual_growth/q3_weak_starts.json").read_text(encoding="utf-8"))
    refs, _ = load_p04(P04)
    by_key = {(r["system_id"], r["initial_condition_set"], r["seed"]): r for r in refs}
    results = []
    for unit in weak["units"]:
        ref = by_key[unit["system_id"], unit["initial_condition_set"], 7]
        start = best_start(ref, "reference", 1)
        r = {k: copy.deepcopy(unit[k]) for k in ("unit_id", "system_id", "initial_condition_set", "dim", "stratum", "trajectory_sha256")}
        r.update(trajectory_control=dict(passed=True), W0=copy.deepcopy(start), W1=copy.deepcopy(start))
        if unit["unit_id"] in CONTROLS:
            r["random_start_control"] = dict(seed=7, passed=True, expected_loss=start["loss"], actual_loss=start["loss"])
        results.append(r)
    rows, rules = aggregate_units(weak["units"], results, refs)
    assert len(rows) == 60 and len(rules) == 10
    assert {r["stratum"]: r["denominator"] for r in rules} == dict(dim1=22, dim2=20, dim3_feasible=4, dim3_bound_infeasible=12, dim4=2)
    with pytest.raises(ValueError, match="Q3 units"):
        aggregate_units(weak["units"], results[:-1], refs)
    results[0]["random_start_control"]["actual_loss"] += 1
    with pytest.raises(ValueError, match="start-1 loss mismatch"):
        aggregate_units(weak["units"], results, refs)
