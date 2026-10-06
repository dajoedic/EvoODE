"""CLI for the ODEBench smoke test."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import shutil
import time
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np

from experiments.annihilator_gate2a_v3.functions import sigma_eff
from experiments.annihilator_gate2a_v3.operator_search import evaluate_class, full_search
from experiments.annihilator_gate2a_v3.weak_operator import WeightContext

from .baselines import PYSINDY_PARAMETERS, fit_pysindy_baseline, library_matrix
from .catalog import build_setup, load_systems, training_domain
from .categories import baseline_category, baseline_struct_ok, evaluate_decision, grouped_table, require_spec_version_2
from .config import ANNIHILATOR_SAMPLE_POINTS, CLEAN_SEEDS, METHODS, NOISY_SEEDS, RESULTS_V1, RESULTS_V2, SEARCH_SETTINGS, SPEC_VERSION, SYSTEM_IDS
from .fhat import basis_ivp_fhat
from .metrics import nrmse, trajectory_metrics
from .oracle import build_reference, nullspace, reference_for_system


_N_EXACT_CACHE: dict[tuple[int, int, int], int] = {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=True))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_setup_reference_from_v1(source: Path = RESULTS_V1) -> tuple[dict, dict, dict]:
    setup_path = source / "setup.json"
    reference_path = source / "reference.json"
    if not setup_path.exists() or not reference_path.exists():
        raise FileNotFoundError(f"missing frozen v1 setup/reference under {source}")
    hashes = {"setup.json": _sha256(setup_path), "reference.json": _sha256(reference_path)}
    return json.loads(setup_path.read_text()), json.loads(reference_path.read_text()), hashes


def _uniform_training_sample(setup_row: dict, system) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    domain_row = setup_row["training_domain"]
    x_values = np.linspace(float(domain_row["xmin"]), float(domain_row["xmax"]), ANNIHILATOR_SAMPLE_POINTS)
    z_values = (x_values - float(domain_row["mu"])) / float(domain_row["scale"])
    exact_f = system.numeric_rhs(x_values)
    return x_values, z_values, exact_f


def setup_command(results: Path) -> dict:
    start = time.perf_counter()
    source_setup = RESULTS_V1 / "setup.json"
    source_reference = RESULTS_V1 / "reference.json"
    setup, reference, source_hashes = _load_setup_reference_from_v1()
    results.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_setup, results / "setup.json")
    shutil.copy2(source_reference, results / "reference.json")
    copied_hashes = {"setup.json": _sha256(results / "setup.json"), "reference.json": _sha256(results / "reference.json")}
    if copied_hashes != source_hashes:
        raise RuntimeError(f"copied setup/reference hashes differ: {copied_hashes} != {source_hashes}")
    sanity = run_sanity(setup, reference)
    write_json(results / "sanity.json", sanity)
    with (results / "run.log").open("a") as handle:
        handle.write(json.dumps({"event": "setup", "systems": len(setup["systems"]), "seconds": time.perf_counter() - start, "copied_hashes": copied_hashes}) + "\n")
    return {"setup": setup, "reference": reference, "sanity": sanity}


def run_sanity(setup: dict, reference: dict) -> dict:
    systems = load_systems()
    integration = {}
    exact_chain = {}
    for sid, system in systems.items():
        rows = []
        for x0, truth in zip(system.init, system.x_train):
            pred = __import__("experiments.annihilator_odebench_smoke.catalog", fromlist=["integrate_trajectory"]).integrate_trajectory(system, x0)
            rows.append(nrmse(pred, truth))
        integration[str(sid)] = {"max_nrmse_x": max(rows), "passed": max(rows) < 1e-4}
        domain = training_domain(system)
        ref_class, coeffs, n_exact = reference_for_system(system, reference)
        x_train, z_train, f_train = _uniform_training_sample(setup["systems"][str(sid)], system)
        width = domain.b - domain.a
        fhat, fail = basis_ivp_fhat(coeffs, ref_class[0], ref_class[1], domain, x_train, f_train, (domain.a - 2.0 * width, domain.b + 10.0 * width))
        if fhat is None:
            value = math.inf
            train_metrics = []
            v3_test = None
        else:
            grid = np.linspace(domain.a, domain.b, ANNIHILATOR_SAMPLE_POINTS)
            value = nrmse(fhat(grid), system.numeric_rhs(grid))
            train_metrics = [trajectory_metrics(system, fhat, float(x0), truth) for x0, truth in zip(system.init, system.x_train)]
            context = WeightContext(z_train, f_train, SEARCH_SETTINGS)
            k_fit, k_val, a_fit, a_val = context.split(ref_class[0], ref_class[1])
            sigma = sigma_eff(f_train, 0.0, SEARCH_SETTINGS.sigma_floor_factor)
            evaluation = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, SEARCH_SETTINGS, start=np.asarray(coeffs, dtype=float))
            v3_test = {
                "passed": bool(evaluation.test.passed),
                "T": evaluation.test.statistic,
                "critical": evaluation.test.critical,
                "dof": evaluation.test.dof,
                "rank": evaluation.test.rank,
            }
        exact_chain[str(sid)] = {
            "reference_class": list(ref_class),
            "reference_n_exact": n_exact,
            "sample_points": ANNIHILATOR_SAMPLE_POINTS,
            "nrmse_f": value,
            "effective_interval": list(fhat.effective_interval) if fhat is not None else None,
            "train_nrmse_x": [row["nrmse_x"] for row in train_metrics],
            "train_r2": [row["r2"] for row in train_metrics],
            "v3_test": v3_test,
            "fail_reason": fail,
            "passed": value < 1e-6 and all(np.isfinite(row["nrmse_x"]) for row in train_metrics) and bool(v3_test and v3_test["passed"]),
        }
    return {
        "training_reintegration": integration,
        "exact_reference_operator_to_fhat": exact_chain,
        "passed": all(row["passed"] for row in integration.values()) and all(row["passed"] for row in exact_chain.values()),
    }


def n_exact_for_class(system, selected: tuple[int, int]) -> int:
    key = (int(system.system_id), int(selected[0]), int(selected[1]))
    if key not in _N_EXACT_CACHE:
        domain = training_domain(system)
        n_exact, _coeffs = nullspace(system.sympy_expr, domain, int(selected[0]), int(selected[1]))
        _N_EXACT_CACHE[key] = int(n_exact)
    return _N_EXACT_CACHE[key]


def annihilator_state_for_system(system, selected: tuple[int, int] | None, reference_class: tuple[int, int], ambiguous: bool) -> tuple[str, int | None]:
    if selected is None:
        return "NONE", None
    selected_n_exact = n_exact_for_class(system, selected)
    if ambiguous:
        return "AMBIGUOUS", selected_n_exact
    if selected == reference_class:
        return "CORRECT", selected_n_exact
    if selected_n_exact > 0:
        return "TRUE_NOT_REF", selected_n_exact
    return "WRONG", selected_n_exact


def _seed_list(eta: float, requested: list[int]) -> list[int]:
    if requested:
        return requested
    return list(CLEAN_SEEDS if eta == 0.0 else NOISY_SEEDS)


def _rng(seed: int, system_id: int, kind: str) -> np.random.Generator:
    return np.random.default_rng([int(seed), int(system_id), {"annihilator": 101, "sindy": 202, "wsindy": 303}[kind]])


def _trajectory_summary(system, fhat, setup_row: dict) -> dict:
    train_rows = [trajectory_metrics(system, fhat, float(x0), truth) for x0, truth in zip(system.init, system.x_train)]
    test_rows = []
    for name in ("mid", "hi", "lo"):
        truth = np.asarray(setup_row["test_trajectories"][name], dtype=float)
        test_rows.append(trajectory_metrics(system, fhat, float(setup_row["test_initial_conditions"][name]), truth))
    return {
        "train_nrmse_x": [row["nrmse_x"] for row in train_rows],
        "train_r2": [row["r2"] for row in train_rows],
        "train_fail_reason": [row.get("fail_reason") for row in train_rows],
        "train_nrmse_x_median": float(np.median([row["nrmse_x"] for row in train_rows])),
        "train_r2_ge_0_9": int(sum(row["r2"] >= 0.9 for row in train_rows)),
        "test_nrmse_x": [row["nrmse_x"] for row in test_rows],
        "test_r2": [row["r2"] for row in test_rows],
        "test_fail_reason": [row.get("fail_reason") for row in test_rows],
        "test_nrmse_x_median": float(np.median([row["nrmse_x"] for row in test_rows])),
        "test_r2_ge_0_9": int(sum(row["r2"] >= 0.9 for row in test_rows)),
    }


def _annihilator_record(system, setup_row: dict, reference: dict, eta: float, seed: int) -> dict:
    domain = training_domain(system)
    x_sorted, z_sorted, exact_f = _uniform_training_sample(setup_row, system)
    sigma = eta * float(np.sqrt(np.mean(exact_f**2)))
    observed_f = exact_f if eta == 0.0 else exact_f + sigma * _rng(seed, system.system_id, "annihilator").standard_normal(exact_f.size)
    selection = full_search(z_sorted, observed_f, eta, seed, SEARCH_SETTINGS, with_bootstrap=True)
    ref_class, _ref_coeffs, n_exact = reference_for_system(system, reference)
    selected_class = tuple(selection.selected_class) if selection.selected_class else None
    state, selected_n_exact = annihilator_state_for_system(system, selected_class, ref_class, bool(selection.a1 or selection.a2 or selection.a3))
    record = {
        "system_id": system.system_id,
        "eta": eta,
        "seed": seed,
        "method": "annihilator",
        "spec_version": SPEC_VERSION,
        "annihilator_sample_points": ANNIHILATOR_SAMPLE_POINTS,
        "sample_grid": "uniform_training_domain",
        "reference_class": list(ref_class),
        "reference_n_exact": n_exact,
        "selected_n_exact": selected_n_exact,
        "selected_class": list(selection.selected_class) if selection.selected_class else None,
        "state": state,
        "tested_classes": selection.tested_classes,
        "aml_iterations": selection.aml_iterations,
        "bootstrap_share": selection.bootstrap_share,
        "A1": selection.a1,
        "A2": selection.a2,
        "A3": selection.a3,
    }
    if selection.selected_class is None or selection.coeffs is None:
        record.update({"fhat_fail": "NONE", "nrmse_f": math.inf, "struct_ok": False})
        return record
    width = domain.b - domain.a
    fhat, fail = basis_ivp_fhat(selection.coeffs, selection.selected_class[0], selection.selected_class[1], domain, x_sorted, observed_f, (domain.a - 2.0 * width, domain.b + 10.0 * width))
    record.update({
        "operator_coefficients_z": np.asarray(selection.coeffs, dtype=float).tolist(),
        "operator_r": int(selection.selected_class[0]),
        "operator_d": int(selection.selected_class[1]),
    })
    if fhat is None:
        record.update({"fhat_fail": fail, "nrmse_f": math.inf, "struct_ok": False, "fhat_effective_interval": None})
        return record
    grid = np.linspace(domain.a, domain.b, 2000)
    nrmse_f = nrmse(fhat(grid), system.numeric_rhs(grid))
    record.update({
        "fhat_fail": None,
        "nrmse_f": nrmse_f,
        "struct_ok": state == "CORRECT" and nrmse_f <= 0.05,
        "fhat_effective_interval": list(fhat.effective_interval),
        "fhat_fit_coefficients": fhat.fit_coefficients,
    })
    record.update(_trajectory_summary(system, fhat, setup_row))
    return record


def _baseline_record(system, setup_row: dict, eta: float, seed: int, method: str) -> dict:
    noisy = []
    rng = _rng(seed, system.system_id, method)
    for values in system.x_train:
        multiplier = 1.0 if eta == 0.0 else 1.0 + eta * rng.standard_normal(values.size)
        noisy.append(np.asarray(values, dtype=float) * multiplier)
    fit = fit_pysindy_baseline(noisy, system.t, method)
    coef = fit["coefficients"]
    names = fit["terms"]
    active = fit["active"]
    selected_terms = {name for name, keep in zip(names, active) if keep}
    category = baseline_category(system.system_id, selected_terms)

    def fhat(x):
        mat, _ = library_matrix(np.asarray(x, dtype=float), tuple(names))
        return mat @ coef

    domain = training_domain(system)
    grid = np.linspace(domain.a, domain.b, 2000)
    nrmse_f = nrmse(fhat(grid), system.numeric_rhs(grid))
    record = {
        "system_id": system.system_id,
        "eta": eta,
        "seed": seed,
        "method": method,
        "spec_version": SPEC_VERSION,
        "category": category,
        "selected_terms": [{"term": name, "coefficient": float(value)} for name, value, keep in zip(names, coef, active) if keep],
        "selected_term_names": sorted(selected_terms),
        "threshold": fit["threshold"],
        "aicc": fit["aicc"],
        "rss": fit["rss"],
        "n_regression_rows": fit["n_regression_rows"],
        "aicc_residual_source": fit["residual_source"],
        "nrmse_f": nrmse_f,
        "struct_ok": baseline_struct_ok(category, nrmse_f),
        "pysindy_parameters": fit["parameters"],
    }
    record.update(_trajectory_summary(system, fhat, setup_row))
    return record


def _compute_record_task(task: tuple[int, float, int, str, Path]) -> dict:
    sid, eta, seed, method, results = task
    if not (results / "setup.json").exists() or not (results / "reference.json").exists():
        setup_command(results)
    setup = json.loads((results / "setup.json").read_text())
    reference = json.loads((results / "reference.json").read_text())
    system = load_systems()[sid]
    if method == "annihilator":
        return _annihilator_record(system, setup["systems"][str(sid)], reference, float(eta), int(seed))
    return _baseline_record(system, setup["systems"][str(sid)], float(eta), int(seed), method)


def _compute_record_task_with_seconds(task: tuple[int, float, int, str, Path]) -> tuple[dict, float]:
    start = time.perf_counter()
    record = _compute_record_task(task)
    return record, time.perf_counter() - start


def run_command(results: Path, system_ids: list[int], etas: list[float], seeds: list[int], methods: list[str], workers: int = 1) -> int:
    if any(sid not in SYSTEM_IDS for sid in system_ids):
        raise ValueError(f"only smoke-test system IDs are allowed: {SYSTEM_IDS}")
    if any(method not in METHODS for method in methods):
        raise ValueError(f"unknown method in {methods}; allowed: {METHODS}")
    setup_path = results / "setup.json"
    reference_path = results / "reference.json"
    if not setup_path.exists() or not reference_path.exists():
        setup_command(results)
    setup = json.loads(setup_path.read_text())
    reference = json.loads(reference_path.read_text())
    systems = load_systems()
    records_path = results / "records.jsonl"
    existing = load_records(records_path)
    seen = {(int(r["system_id"]), float(r["eta"]), int(r["seed"]), r["method"]) for r in existing}
    tasks = []
    for sid in system_ids:
        for eta in etas:
            for seed in _seed_list(float(eta), seeds):
                for method in methods:
                    key = (sid, float(eta), int(seed), method)
                    if key not in seen:
                        tasks.append((sid, float(eta), int(seed), method, results))
    written = 0
    with records_path.open("a") as handle, (results / "run.log").open("a") as log:
        if workers <= 1:
            for task in tasks:
                record, seconds = _compute_record_task_with_seconds(task)
                handle.write(json.dumps(record, sort_keys=True, allow_nan=True) + "\n")
                handle.flush()
                log.write(json.dumps({"event": "record", "system_id": task[0], "eta": task[1], "seed": task[2], "method": task[3], "seconds": seconds}) + "\n")
                log.flush()
                written += 1
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=int(workers)) as pool:
                future_to_task = {pool.submit(_compute_record_task_with_seconds, task): task for task in tasks}
                for future in concurrent.futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    record, seconds = future.result()
                    handle.write(json.dumps(record, sort_keys=True, allow_nan=True) + "\n")
                    handle.flush()
                    log.write(json.dumps({"event": "record", "system_id": task[0], "eta": task[1], "seed": task[2], "method": task[3], "seconds": seconds}) + "\n")
                    log.flush()
                    written += 1
    return written


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def summarize_command(results: Path) -> dict:
    records = load_records(results / "records.jsonl")
    require_spec_version_2(records)
    summary = {"decision": evaluate_decision(records), "table": grouped_table(records), "n_records": len(records), "pysindy_parameters": PYSINDY_PARAMETERS}
    write_json(results / "summary.json", summary)
    lines = ["# ODEBench smoke summary", "", f"Records: {len(records)}", "", "| method | eta | system | n | struct_ok | median NRMSE_f | median test NRMSE_x |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in summary["table"]:
        lines.append(f"| {row['method']} | {row['eta']} | {row['system_id']} | {row['n']} | {row['struct_ok']} | {row['median_nrmse_f']:.6g} | {row['median_test_nrmse_x']:.6g} |")
    (results / "summary.md").write_text("\n".join(lines) + "\n")
    return summary


def _write_done_marker(results: Path, records_written: int) -> None:
    payload = {"timestamp": datetime.now().isoformat(timespec="seconds"), "records_written": int(records_written), "total_records": len(load_records(results / "records.jsonl"))}
    (results / "DONE").write_text(json.dumps(payload, sort_keys=True) + "\n")
    failed = results / "FAILED"
    if failed.exists():
        failed.unlink()


def _write_failed_marker(results: Path) -> None:
    payload = {"timestamp": datetime.now().isoformat(timespec="seconds"), "traceback": traceback.format_exc()}
    (results / "FAILED").write_text(json.dumps(payload, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=RESULTS_V2)
    parser.add_argument("--setup", action="store_true")
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
        if args.setup:
            setup_command(args.results)
        written = 0
        if args.run:
            written = run_command(args.results, args.systems, args.eta, args.seeds, args.methods, args.workers)
            if args.detach_marker:
                _write_done_marker(args.results, written)
        if args.summarize:
            summarize_command(args.results)
    except Exception:
        if args.run and args.detach_marker:
            _write_failed_marker(args.results)
        raise


if __name__ == "__main__":
    main()
