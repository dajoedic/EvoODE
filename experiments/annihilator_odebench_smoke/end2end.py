"""End-to-end ODEBench comparison from shared noisy trajectories."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Iterable

import numpy as np
import pysindy as ps
import sympy as sp
from scipy.interpolate import CubicSpline
from scipy.integrate import solve_ivp

from experiments.annihilator_gate2a_v3.config import class_order
from experiments.annihilator_gate2a_v3.operator_search import aml_candidate
from experiments.annihilator_gate2a_v3.weak_operator import WeightContext

from .baselines import CaptureSTLSQ, allowed_library_terms, library_matrix, make_custom_library, object_parameters
from .catalog import Domain, ODESystem, load_systems, training_domain
from .config import ANNIHILATOR_SAMPLE_POINTS, SEARCH_SETTINGS, SINDY_THRESHOLDS, SYSTEM_IDS
from .fhat import basis_ivp_fhat
from .metrics import nrmse, r2_score
from .oracle import nullspace, reference_for_system


ROOT = Path(__file__).resolve().parent
RESULTS_E2E = ROOT / "results_e2e"
SPEC = "end2end_v1"
METHODS = ("annihilator", "sindy", "wsindy")
PROTOCOLS = ("P1_from_AB1", "P1_from_AB2", "P2")
NOISY_SEEDS = (70000, 70001, 70002, 70003, 70004)
VALIDATION_SPLIT_TIME = 8.0
SELECTION_TIE_REL = 1e-3
DISCUSS_LABEL = "weiter diskutieren"
END_LABEL = "beenden"
DECISION_ETA = 0.01
R2_SUCCESS_THRESHOLD = 0.9
DISCUSS_G_SYSTEMS = 3
_DROP_FROM_JSON = object()
_LAST_RUN_FAILED_TASKS = 0


@dataclass(frozen=True)
class TrajectorySet:
    clean: tuple[np.ndarray, ...]
    noisy: tuple[np.ndarray, ...]
    noise: tuple[np.ndarray, ...]


@dataclass(frozen=True)
class CandidateResult:
    candidate: dict
    fhat: Callable[[np.ndarray | float], np.ndarray] | None
    validation_error: float
    fail_reason: str | None
    counts: dict


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=True) + "\n")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _json_safe_value(value):
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return _json_safe_value(value.tolist())
    if callable(value):
        return _DROP_FROM_JSON
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            safe_item = _json_safe_value(item)
            if safe_item is not _DROP_FROM_JSON:
                out[str(key)] = safe_item
        return out
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            safe_item = _json_safe_value(item)
            if safe_item is not _DROP_FROM_JSON:
                out.append(safe_item)
        return out
    return str(value)


def _json_safe_record(record: dict) -> dict:
    return _json_safe_value(record)


def e2e_classes() -> tuple[tuple[int, int], ...]:
    return tuple((r, d) for r, d in class_order() if (r + 1) * (d + 1) <= 12)


def split_mask(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    t = np.asarray(t, dtype=float)
    return t <= VALIDATION_SPLIT_TIME, t > VALIDATION_SPLIT_TIME


def shared_noisy_trajectories(system: ODESystem, eta: float, seed: int) -> TrajectorySet:
    clean = tuple(np.asarray(row, dtype=float) for row in system.x_train)
    noisy = []
    noise = []
    for trajectory_index, values in enumerate(clean):
        rng = np.random.default_rng([int(seed), int(system.system_id), int(trajectory_index)])
        xi = np.zeros_like(values) if float(eta) == 0.0 else rng.normal(0.0, float(eta), values.size)
        noise.append(xi)
        noisy.append(values * (1.0 + xi))
    return TrajectorySet(clean=clean, noisy=tuple(noisy), noise=tuple(noise))


def protocol_training_indices(protocol: str) -> tuple[int, ...]:
    if protocol == "P1_from_AB1":
        return (0,)
    if protocol == "P1_from_AB2":
        return (1,)
    if protocol == "P2":
        return (0, 1)
    raise ValueError(f"unknown protocol: {protocol}")


def protocol_generalization_items(system: ODESystem, setup_row: dict, protocol: str) -> list[tuple[str, float, np.ndarray]]:
    if protocol == "P1_from_AB1":
        return [("AB2", float(system.init[1]), np.asarray(system.x_train[1], dtype=float))]
    if protocol == "P1_from_AB2":
        return [("AB1", float(system.init[0]), np.asarray(system.x_train[0], dtype=float))]
    if protocol == "P2":
        return [
            (name, float(setup_row["test_initial_conditions"][name]), np.asarray(setup_row["test_trajectories"][name], dtype=float))
            for name in ("mid", "hi", "lo")
        ]
    raise ValueError(f"unknown protocol: {protocol}")


def integrate_fhat(t: np.ndarray, fhat: Callable[[np.ndarray | float], np.ndarray], x0: float) -> tuple[np.ndarray | None, str | None]:
    try:
        t = np.asarray(t, dtype=float)

        def rhs(_t, y):
            value = np.asarray(fhat(float(y[0])), dtype=float).reshape(-1)[0]
            if not np.isfinite(value):
                raise FloatingPointError("non-finite rhs")
            return [float(value)]

        sol = solve_ivp(rhs, (float(t[0]), float(t[-1])), [float(x0)], t_eval=t, method="LSODA", rtol=1e-8, atol=1e-10)
        if not sol.success or not np.all(np.isfinite(sol.y[0])):
            return None, "integration_failed"
        return np.asarray(sol.y[0], dtype=float), None
    except Exception as exc:
        return None, type(exc).__name__


def validation_error(system: ODESystem, fhat: Callable[[np.ndarray | float], np.ndarray], noisy: TrajectorySet, train_indices: Iterable[int]) -> tuple[float, str | None]:
    _fit_mask, val_mask = split_mask(system.t)
    errors = []
    failures = []
    for idx in train_indices:
        pred, fail = integrate_fhat(system.t, fhat, float(system.init[idx]))
        if pred is None:
            failures.append(fail or "integration_failed")
            errors.append(math.inf)
        else:
            errors.append(nrmse(pred[val_mask], noisy.noisy[idx][val_mask]))
    value = float(np.mean(errors)) if errors else math.inf
    return value, ";".join(failures) if failures else None


def select_candidate(results: list[CandidateResult]) -> CandidateResult:
    if not results:
        raise ValueError("empty candidate list")
    best = results[0]
    for candidate in results[1:]:
        if candidate.validation_error < best.validation_error * (1.0 - SELECTION_TIE_REL):
            best = candidate
        elif abs(candidate.validation_error - best.validation_error) <= SELECTION_TIE_REL * max(abs(best.validation_error), np.finfo(float).tiny):
            if candidate.candidate["complexity"] < best.candidate["complexity"]:
                best = candidate
    return best


def _fit_baseline_on_indices(system: ODESystem, noisy: TrajectorySet, train_indices: tuple[int, ...], method: str, threshold: float):
    x_list = [np.asarray(noisy.noisy[idx], dtype=float).reshape(-1, 1) for idx in train_indices]
    fit_mask, _val_mask = split_mask(system.t)
    x_fit_list = [row[fit_mask] for row in x_list]
    terms = allowed_library_terms(np.concatenate([row.reshape(-1) for row in x_fit_list]))
    return _fit_baseline_arrays([row.reshape(-1) for row in x_fit_list], system.t[fit_mask], method, threshold, terms)


def _fit_baseline_arrays(trajectories: list[np.ndarray], t: np.ndarray, method: str, threshold: float, terms: tuple[str, ...]):
    x_list = [np.asarray(values, dtype=float).reshape(-1, 1) for values in trajectories]
    function_library = make_custom_library(terms)
    optimizer = CaptureSTLSQ(threshold=float(threshold), normalize_columns=True)
    if method == "sindy":
        differentiation = ps.SmoothedFiniteDifference()
        feature_library = function_library
    elif method == "wsindy":
        differentiation = ps.FiniteDifference()
        feature_library = ps.WeakPDELibrary(function_library=function_library, spatiotemporal_grid=np.asarray(t, dtype=float), K=200)
    else:
        raise ValueError(f"unknown baseline method: {method}")
    model = ps.SINDy(optimizer=optimizer, feature_library=feature_library, differentiation_method=differentiation)
    model.fit(x_list, t=np.asarray(t, dtype=float), feature_names=["x"])
    coef = np.asarray(model.coefficients()[0], dtype=float)
    names = tuple(model.get_feature_names())

    def fhat(x):
        mat, _ = library_matrix(np.asarray(x, dtype=float), names)
        return mat @ coef

    return {
        "fhat": fhat,
        "coefficients": coef,
        "terms": names,
        "active": np.abs(coef) > 0.0,
        "threshold": float(threshold),
        "parameters": {
            "pysindy_version": ps.__version__,
            "method": method,
            "library_terms": list(terms),
            "threshold": float(threshold),
            "model": object_parameters(model),
            "optimizer": object_parameters(optimizer),
            "differentiation_method": object_parameters(model.differentiation_method),
            "feature_library": object_parameters(feature_library),
            "function_library": object_parameters(function_library),
        },
    }


def baseline_candidates(system: ODESystem, noisy: TrajectorySet, train_indices: tuple[int, ...], method: str) -> list[CandidateResult]:
    out = []
    for threshold in SINDY_THRESHOLDS:
        candidate = {"kind": method, "threshold": float(threshold), "complexity": float(threshold)}
        try:
            fit = _fit_baseline_on_indices(system, noisy, train_indices, method, float(threshold))
            active_terms = [name for name, keep in zip(fit["terms"], fit["active"]) if keep]
            candidate["complexity"] = len(active_terms)
            value, fail = validation_error(system, fit["fhat"], noisy, train_indices)
            out.append(CandidateResult(candidate | {"fit": fit}, fit["fhat"], value, fail, {"fits": 1, "integrations": len(train_indices)}))
        except Exception as exc:
            out.append(CandidateResult(candidate, None, math.inf, type(exc).__name__, {"fits": 1, "integrations": 0}))
    return out


def refit_baseline_full(system: ODESystem, noisy: TrajectorySet, train_indices: tuple[int, ...], method: str, selected: CandidateResult):
    trajectories = [noisy.noisy[idx] for idx in train_indices]
    terms = allowed_library_terms(np.concatenate(trajectories))
    return _fit_baseline_arrays([np.asarray(row, dtype=float) for row in trajectories], system.t, method, float(selected.candidate["threshold"]), terms)


def resample_state_derivative(x_values: np.ndarray, f_values: np.ndarray, points: int = ANNIHILATOR_SAMPLE_POINTS) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(x_values, dtype=float).reshape(-1)
    f = np.asarray(f_values, dtype=float).reshape(-1)
    order = np.argsort(x)
    x_sorted = x[order]
    f_sorted = f[order]
    unique, starts = np.unique(x_sorted, return_index=True)
    sums = np.add.reduceat(f_sorted, starts)
    counts = np.diff(np.append(starts, f_sorted.size))
    mean_f = sums / counts
    grid = np.linspace(float(unique[0]), float(unique[-1]), int(points))
    values = CubicSpline(unique, mean_f)(grid)
    z = (grid - 0.5 * (grid[0] + grid[-1])) / (0.5 * (grid[-1] - grid[0]))
    return grid, z, values


def estimate_derivatives(t: np.ndarray, trajectories: list[np.ndarray]) -> list[np.ndarray]:
    differentiation = ps.SmoothedFiniteDifference()
    out = []
    for values in trajectories:
        arr = np.asarray(values, dtype=float).reshape(-1, 1)
        deriv = differentiation._differentiate(arr, np.asarray(t, dtype=float))
        out.append(np.asarray(deriv, dtype=float).reshape(-1))
    return out


def annihilator_grid_from_training(system: ODESystem, noisy: TrajectorySet, train_indices: tuple[int, ...], fit_only: bool, exact_f: bool = False) -> tuple[Domain, np.ndarray, np.ndarray, np.ndarray]:
    fit_mask, _val_mask = split_mask(system.t)
    x_rows = []
    f_rows = []
    for idx in train_indices:
        x = noisy.noisy[idx]
        mask = fit_mask if fit_only else np.ones_like(system.t, dtype=bool)
        x_use = x[mask]
        f_use = system.numeric_rhs(x_use) if exact_f else estimate_derivatives(system.t[mask], [x_use])[0]
        x_rows.append(x_use)
        f_rows.append(f_use)
    x_grid, z_grid, f_grid = resample_state_derivative(np.concatenate(x_rows), np.concatenate(f_rows))
    domain = Domain("learned", float(x_grid[0]), float(x_grid[-1]))
    return domain, x_grid, z_grid, f_grid


def fit_annihilator_candidate(domain: Domain, x_grid: np.ndarray, z_grid: np.ndarray, f_grid: np.ndarray, cls: tuple[int, int]) -> tuple[Callable | None, dict, str | None]:
    r, d = cls
    k_fit, _k_val, a_fit, _a_val = WeightContext(z_grid, f_grid, SEARCH_SETTINGS).split(r, d)
    coeffs, iterations, converged, message, singular_values, _m_matrix = aml_candidate(a_fit, k_fit)
    width = domain.b - domain.a
    fhat, fail = basis_ivp_fhat(coeffs, r, d, domain, x_grid, f_grid, (domain.a - 2.0 * width, domain.b + 10.0 * width))
    info = {
        "operator_r": r,
        "operator_d": d,
        "operator_coefficients_z": np.asarray(coeffs, dtype=float).tolist(),
        "aml_iterations": iterations,
        "aml_converged": converged,
        "aml_message": message,
        "singular_values": np.asarray(singular_values, dtype=float).tolist(),
        "fhat_fit_coefficients": getattr(fhat, "fit_coefficients", None) if fhat is not None else None,
        "fhat_effective_interval": list(fhat.effective_interval) if fhat is not None else None,
    }
    return fhat, info, fail


def annihilator_candidates(system: ODESystem, noisy: TrajectorySet, train_indices: tuple[int, ...]) -> list[CandidateResult]:
    out = []
    try:
        domain, x_grid, z_grid, f_grid = annihilator_grid_from_training(system, noisy, train_indices, fit_only=True)
    except Exception as exc:
        return [CandidateResult({"kind": "annihilator", "class": list(cls), "complexity": (cls[0] + 1) * (cls[1] + 1)}, None, math.inf, type(exc).__name__, {"classes": 0}) for cls in e2e_classes()]
    for cls in e2e_classes():
        candidate = {"kind": "annihilator", "class": list(cls), "complexity": (cls[0] + 1) * (cls[1] + 1)}
        try:
            fhat, info, fail = fit_annihilator_candidate(domain, x_grid, z_grid, f_grid, cls)
            if fhat is None:
                out.append(CandidateResult(candidate | info, None, math.inf, fail, {"classes": 1, "integrations": 0}))
                continue
            value, val_fail = validation_error(system, fhat, noisy, train_indices)
            out.append(CandidateResult(candidate | info, fhat, value, val_fail, {"classes": 1, "integrations": len(train_indices)}))
        except Exception as exc:
            out.append(CandidateResult(candidate, None, math.inf, type(exc).__name__, {"classes": 1, "integrations": 0}))
    return out


def refit_annihilator_full(system: ODESystem, noisy: TrajectorySet, train_indices: tuple[int, ...], selected: CandidateResult):
    cls = tuple(selected.candidate["class"])
    domain, x_grid, z_grid, f_grid = annihilator_grid_from_training(system, noisy, train_indices, fit_only=False)
    return fit_annihilator_candidate(domain, x_grid, z_grid, f_grid, cls) + ((domain, x_grid, f_grid),)


def n_exact_for_class(system: ODESystem, selected: tuple[int, int]) -> int:
    domain = training_domain(system)
    n_exact, _coeffs = nullspace(system.sympy_expr, domain, int(selected[0]), int(selected[1]))
    return int(n_exact)


def baseline_category(system_id: int, selected_terms: set[str]) -> tuple[bool, bool, str]:
    truth = {3: {"x", "x^2"}, 7: {"x", "x log(x)"}, 21: {"1", "x", "exp(-x)"}, 19: None}.get(int(system_id))
    if int(system_id) not in {3, 7, 19, 21}:
        return False, False, "synthetic"
    if truth is None:
        return False, False, "not_representable"
    exact = selected_terms == truth
    superset = bool(truth.issubset(selected_terms))
    return exact, superset and not exact, "exact" if exact else ("true_plus" if superset else "surrogate")


def evaluate_items(system: ODESystem, fhat: Callable, items: list[tuple[str, float, np.ndarray]]) -> list[dict]:
    rows = []
    for name, x0, truth in items:
        pred, fail = integrate_fhat(system.t, fhat, x0)
        if pred is None:
            rows.append({"name": name, "nrmse_x": math.inf, "r2": -math.inf, "fail_reason": fail})
        else:
            rows.append({"name": name, "nrmse_x": nrmse(pred, truth), "r2": r2_score(pred, truth), "fail_reason": None})
    return rows


def nrmse_f_on_domain(system: ODESystem, fhat: Callable) -> float:
    domain = training_domain(system)
    grid = np.linspace(domain.a, domain.b, 2000)
    try:
        return nrmse(fhat(grid), system.numeric_rhs(grid))
    except Exception:
        return math.inf


def fit_record(system: ODESystem, setup_row: dict, reference: dict, eta: float, seed: int, method: str, protocol: str) -> dict:
    noisy = shared_noisy_trajectories(system, eta, seed)
    train_indices = protocol_training_indices(protocol)
    candidates = annihilator_candidates(system, noisy, train_indices) if method == "annihilator" else baseline_candidates(system, noisy, train_indices, method)
    selected = select_candidate(candidates)
    validation_candidates = [
        {"candidate": row.candidate, "validation_nrmse_x": row.validation_error, "fail_reason": row.fail_reason}
        for row in candidates
    ]
    counts = {
        "candidate_count": len(candidates),
        "failed_candidates": sum(not np.isfinite(row.validation_error) for row in candidates),
        "selection_integrations": sum(int(row.counts.get("integrations", 0)) for row in candidates),
    }
    if method == "annihilator":
        fhat, fit_info, fail, full_payload = refit_annihilator_full(system, noisy, train_indices, selected)
        selected_class = tuple(selected.candidate["class"])
        ref_class, _ref_coeffs, ref_n_exact = reference_for_system(system, reference)
        selected_n_exact = n_exact_for_class(system, selected_class)
        struct_exact = selected_class == ref_class
        struct_superset = selected_n_exact > 0 and not struct_exact
        domain, _x_grid, f_grid = full_payload
        selected_model = fit_info | {
            "selected_class": list(selected_class),
            "reference_class": list(ref_class),
            "reference_n_exact": ref_n_exact,
            "selected_n_exact": selected_n_exact,
            "operator_coefficients_z": fit_info.get("operator_coefficients_z"),
            "fit_domain": {"xmin": domain.a, "xmax": domain.b, "mu": domain.mu, "scale": domain.scale},
            "resampled_points": int(f_grid.size),
        }
    else:
        fit = refit_baseline_full(system, noisy, train_indices, method, selected)
        fhat = fit["fhat"]
        fail = None
        selected_terms = {name for name, keep in zip(fit["terms"], fit["active"]) if keep}
        struct_exact, struct_superset, category = baseline_category(system.system_id, selected_terms)
        selected_model = {
            "selected_terms": [{"term": name, "coefficient": float(value)} for name, value, keep in zip(fit["terms"], fit["coefficients"], fit["active"]) if keep],
            "selected_term_names": sorted(selected_terms),
            "threshold": fit["threshold"],
            "category": category,
            "pysindy_parameters": fit["parameters"],
        }
    reconstruction_items = [(f"AB{idx + 1}", float(system.init[idx]), np.asarray(system.x_train[idx], dtype=float)) for idx in train_indices]
    generalization_items = protocol_generalization_items(system, setup_row, protocol)
    if fhat is None:
        reconstruction = [{"name": name, "nrmse_x": math.inf, "r2": -math.inf, "fail_reason": fail} for name, _x0, _truth in reconstruction_items]
        generalization = [{"name": name, "nrmse_x": math.inf, "r2": -math.inf, "fail_reason": fail} for name, _x0, _truth in generalization_items]
        nrmse_f = math.inf
    else:
        reconstruction = evaluate_items(system, fhat, reconstruction_items)
        generalization = evaluate_items(system, fhat, generalization_items)
        nrmse_f = nrmse_f_on_domain(system, fhat)
    record = {
        "spec": SPEC,
        "system_id": int(system.system_id),
        "eta": float(eta),
        "seed": int(seed),
        "method": method,
        "protocol": protocol,
        "training_trajectories": list(train_indices),
        "selection_rule": {"fit": "t <= 8", "validation": "t > 8", "tie_rel": SELECTION_TIE_REL, "metric": "validation_nrmse_x"},
        "selected_validation_nrmse_x": selected.validation_error,
        "selected_validation_fail_reason": selected.fail_reason,
        "candidate_validations": validation_candidates,
        "refit_on_full_time": True,
        "nrmse_f": nrmse_f,
        "reconstruction": reconstruction,
        "generalization": generalization,
        "reconstruction_r2": [row["r2"] for row in reconstruction],
        "generalization_r2": [row["r2"] for row in generalization],
        "reconstruction_nrmse_x": [row["nrmse_x"] for row in reconstruction],
        "generalization_nrmse_x": [row["nrmse_x"] for row in generalization],
        "structure_exact": bool(struct_exact),
        "structure_superset": bool(struct_superset),
        "selected_model": selected_model,
        "counts": counts,
    }
    return _json_safe_record(record)


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _record_key(record: dict) -> tuple:
    return (int(record["system_id"]), float(record["eta"]), int(record["seed"]), str(record["method"]), str(record["protocol"]))


def _compute_record_task(task: tuple[int, float, int, str, str, Path]) -> dict:
    sid, eta, seed, method, protocol, results = task
    if int(sid) == 999:
        system, setup_row, reference = synthetic_system()
        return fit_record(system, setup_row, reference, float(eta), int(seed), method, protocol)
    setup = load_json(results / "setup.json")
    reference = load_json(results / "reference.json")
    system = load_systems()[int(sid)]
    return fit_record(system, setup["systems"][str(sid)], reference, float(eta), int(seed), method, protocol)


def _compute_record_task_with_seconds(task: tuple[int, float, int, str, str, Path]) -> tuple[dict, float]:
    start = time.perf_counter()
    record = _compute_record_task(task)
    return record, time.perf_counter() - start


def _task_log_payload(task: tuple[int, float, int, str, str, Path]) -> dict:
    return {"system_id": task[0], "eta": task[1], "seed": task[2], "method": task[3], "protocol": task[4]}


def _write_task_failure(results: Path, task: tuple[int, float, int, str, str, Path], log, tb: str) -> None:
    payload = _task_log_payload(task) | {"event": "task_failed", "traceback": tb}
    log.write(json.dumps(payload, sort_keys=True) + "\n")
    log.flush()
    with (results / "failed_tasks.jsonl").open("a") as failed:
        failed.write(json.dumps(payload, sort_keys=True) + "\n")


def run_command(results: Path, systems: list[int], etas: list[float], seeds: list[int], methods: list[str], workers: int) -> int:
    global _LAST_RUN_FAILED_TASKS
    _LAST_RUN_FAILED_TASKS = 0
    _copy_setup_reference(results)
    if any(int(sid) not in SYSTEM_IDS for sid in systems):
        raise ValueError(f"only ODEBench smoke system IDs are allowed: {SYSTEM_IDS}")
    if any(method not in METHODS for method in methods):
        raise ValueError(f"unknown method in {methods}; allowed: {METHODS}")
    existing = load_records(results / "records.jsonl")
    seen = {_record_key(record) for record in existing}
    tasks = []
    for sid in systems:
        for eta in etas:
            seed_list = seeds or ([0] if float(eta) == 0.0 else list(NOISY_SEEDS))
            for seed in seed_list:
                for method in methods:
                    for protocol in PROTOCOLS:
                        key = (int(sid), float(eta), int(seed), method, protocol)
                        if key not in seen:
                            tasks.append((int(sid), float(eta), int(seed), method, protocol, results))
    written = 0
    failed = 0
    with (results / "records.jsonl").open("a") as handle, (results / "run.log").open("a") as log:
        if workers <= 1:
            for task in tasks:
                try:
                    record, seconds = _compute_record_task_with_seconds(task)
                    handle.write(json.dumps(record, sort_keys=True, allow_nan=True) + "\n")
                    handle.flush()
                    log.write(json.dumps({"event": "record", **_task_log_payload(task), "seconds": seconds}) + "\n")
                    log.flush()
                    written += 1
                except Exception:
                    failed += 1
                    _write_task_failure(results, task, log, traceback.format_exc())
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=int(workers)) as pool:
                future_to_task = {pool.submit(_compute_record_task_with_seconds, task): task for task in tasks}
                for future in concurrent.futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        record, seconds = future.result()
                        handle.write(json.dumps(record, sort_keys=True, allow_nan=True) + "\n")
                        handle.flush()
                        log.write(json.dumps({"event": "record", **_task_log_payload(task), "seconds": seconds}) + "\n")
                        log.flush()
                        written += 1
                    except Exception:
                        failed += 1
                        _write_task_failure(results, task, log, "".join(traceback.format_exception(future.exception())))
    _LAST_RUN_FAILED_TASKS = failed
    return written


def structure_hit_by_system(records: list[dict], method: str, system_id: int) -> bool:
    subset = [r for r in records if r["method"] == method and int(r["system_id"]) == int(system_id) and float(r["eta"]) == DECISION_ETA]
    if not subset:
        return False
    seed_votes: dict[int, bool] = {}
    for seed in sorted({int(r["seed"]) for r in subset}):
        rows = [r for r in subset if int(r["seed"]) == seed]
        seed_votes[seed] = any(bool(r.get("structure_exact")) for r in rows)
    return sum(seed_votes.values()) > len(seed_votes) / 2


def generalization_success(records: list[dict], method: str, system_id: int) -> float:
    rows = [r for r in records if r["method"] == method and int(r["system_id"]) == int(system_id) and float(r["eta"]) == DECISION_ETA]
    values = [float(r2) for row in rows for r2 in row.get("generalization_r2", [])]
    return float(sum(v >= R2_SUCCESS_THRESHOLD for v in values) / len(values)) if values else 0.0


def evaluate_decision(records: list[dict]) -> dict:
    systems = sorted({int(r["system_id"]) for r in records})
    generalization = {
        str(sid): {method: generalization_success(records, method, sid) for method in METHODS}
        for sid in systems
    }
    structure = {
        method: sum(structure_hit_by_system(records, method, sid) for sid in systems)
        for method in METHODS
    }
    g_count = 0
    for sid in systems:
        ann = generalization[str(sid)]["annihilator"]
        best_baseline = max(generalization[str(sid)]["sindy"], generalization[str(sid)]["wsindy"])
        if ann >= best_baseline:
            g_count += 1
    best_baseline_structure = max(structure["sindy"], structure["wsindy"])
    s_ok = structure["annihilator"] >= best_baseline_structure
    decision = DISCUSS_LABEL if g_count >= DISCUSS_G_SYSTEMS and s_ok else END_LABEL
    return {"decision": decision, "G": g_count, "S": s_ok, "generalization": generalization, "structure_system_counts": structure}


def summarize_command(results: Path) -> dict:
    records = load_records(results / "records.jsonl")
    summary = {"n_records": len(records), "decision": evaluate_decision(records), "thresholds": {"eta": DECISION_ETA, "r2": R2_SUCCESS_THRESHOLD, "G_systems": DISCUSS_G_SYSTEMS}}
    write_json(results / "summary.json", summary)
    return summary


def _copy_setup_reference(results: Path) -> None:
    results.mkdir(parents=True, exist_ok=True)
    source = ROOT / "results"
    for name in ("setup.json", "reference.json"):
        target = results / name
        if not target.exists():
            target.write_text((source / name).read_text())


def synthetic_system() -> tuple[ODESystem, dict, dict]:
    t = np.linspace(0.0, 10.0, 512)

    def rhs(x):
        values = np.asarray(x, dtype=float)
        return 0.5 * values - 0.02 * values**2

    trajectories = []
    for x0 in (1.0, 9.0):
        sol = solve_ivp(lambda _t, y: [float(rhs(float(y[0])))], (0.0, 10.0), [x0], t_eval=t, method="LSODA", rtol=1e-10, atol=1e-12)
        trajectories.append(np.asarray(sol.y[0], dtype=float))
    x_symbol = sp.Symbol("x")
    system = ODESystem(999, "dx/dt = 0.5*x - 0.02*x^2", "0.5*x - 0.02*x**2", (), (1.0, 9.0), "x_0 > 0", t, tuple(trajectories), 0.5 * x_symbol - 0.02 * x_symbol**2, rhs)
    setup_row = {"test_initial_conditions": {"mid": 3.0, "hi": 14.0, "lo": 0.5}, "test_trajectories": {}}
    for name, x0 in setup_row["test_initial_conditions"].items():
        sol = solve_ivp(lambda _t, y: [float(rhs(float(y[0])))], (0.0, 10.0), [x0], t_eval=t, method="LSODA", rtol=1e-10, atol=1e-12)
        setup_row["test_trajectories"][name] = np.asarray(sol.y[0], dtype=float).tolist()
    reference = {"systems": {"999": {"reference_class": [1, 1], "reference_coeffs": [-0.5, 0.02, 1.0, 0.0], "reference_n_exact": 1}}}
    return system, setup_row, reference


def sanity_command(results: Path) -> dict:
    _copy_setup_reference(results)
    start = time.perf_counter()
    system, setup_row, reference = synthetic_system()
    synthetic = {}
    for method in METHODS:
        record = fit_record(system, setup_row, reference, 0.0, 0, method, "P2")
        synthetic[method] = {"validation_nrmse_x": record["selected_validation_nrmse_x"], "passed": record["selected_validation_nrmse_x"] < 1e-3}
    systems = load_systems()
    setup = load_json(results / "setup.json")
    ref = load_json(results / "reference.json")
    exact_chain = {}
    for sid, ode_system in systems.items():
        row_start = time.perf_counter()
        ref_class, _coeffs, _n_exact = reference_for_system(ode_system, ref)
        noisy = shared_noisy_trajectories(ode_system, 0.0, 0)
        domain, x_grid, z_grid, f_grid = annihilator_grid_from_training(ode_system, noisy, (0, 1), fit_only=True, exact_f=True)
        fhat, info, fail = fit_annihilator_candidate(domain, x_grid, z_grid, f_grid, ref_class)
        value, val_fail = validation_error(ode_system, fhat, noisy, (0, 1)) if fhat is not None else (math.inf, fail)
        documented_exception = int(sid) == 7
        exact_chain[str(sid)] = {
            "reference_class": list(ref_class),
            "validation_nrmse_x": value,
            "fail_reason": val_fail,
            "seconds": time.perf_counter() - row_start,
            "counts": {"classes": 1, "sample_points": int(f_grid.size), "aml_iterations": info.get("aml_iterations")},
            "passed": value < 1e-4,
        }
        if documented_exception:
            exact_chain[str(sid)]["documented_exception"] = True
    sanity = {"synthetic_selection": synthetic, "exact_derivative_reference_class": exact_chain, "seconds": time.perf_counter() - start}
    checked_exact_chain = [row for sid, row in exact_chain.items() if int(sid) != 7]
    sanity["passed"] = all(row["passed"] for row in synthetic.values()) and all(row["passed"] for row in checked_exact_chain)
    write_json(results / "sanity.json", sanity)
    return sanity


def _write_done_marker(results: Path, records_written: int, failed_tasks: int = 0) -> None:
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "records_written": int(records_written),
        "failed_tasks": int(failed_tasks),
        "total_records": len(load_records(results / "records.jsonl")),
    }
    (results / "DONE").write_text(json.dumps(payload, sort_keys=True) + "\n")
    failed = results / "FAILED"
    if failed.exists():
        failed.unlink()


def _write_failed_marker(results: Path) -> None:
    payload = {"timestamp": datetime.now().isoformat(timespec="seconds"), "traceback": traceback.format_exc()}
    (results / "FAILED").write_text(json.dumps(payload, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=RESULTS_E2E)
    parser.add_argument("--sanity", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--detach-marker", action="store_true")
    parser.add_argument("--systems", nargs="*", type=int, default=list(SYSTEM_IDS))
    parser.add_argument("--eta", nargs="*", type=float, default=[0.0, 0.01])
    parser.add_argument("--seeds", nargs="*", type=int, default=[])
    parser.add_argument("--methods", nargs="*", default=list(METHODS))
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    args.results.mkdir(parents=True, exist_ok=True)
    try:
        if args.sanity:
            sanity_command(args.results)
        written = 0
        if args.run:
            written = run_command(args.results, args.systems, args.eta, args.seeds, args.methods, args.workers)
            if args.detach_marker:
                _write_done_marker(args.results, written, _LAST_RUN_FAILED_TASKS)
        if args.summarize:
            summarize_command(args.results)
    except Exception:
        if args.run and args.detach_marker:
            _write_failed_marker(args.results)
        raise


if __name__ == "__main__":
    main()
