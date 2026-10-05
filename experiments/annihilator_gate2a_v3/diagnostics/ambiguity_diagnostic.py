"""AMBIGUOUS vs WRONG diagnostic for Gate 2A v3."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
import json
import math
import time
from pathlib import Path
from typing import Iterable

import mpmath as mp
import numpy as np

from experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration import _state_for_clean
from experiments.annihilator_gate2a_v3.config import (
    APPENDIX_A_JSON,
    FUNCTIONS,
    ORACLE_DIGITS,
    ORACLE_REL_TOL,
    RESULTS,
    Settings,
    class_columns,
    domain_for,
    settings_for_variant,
)
from experiments.annihilator_gate2a_v3.functions import noisy_sample
from experiments.annihilator_gate2a_v3.operator_search import Selection, full_search, normalize_coeffs
from experiments.annihilator_gate2a_v3.oracle import _mp_collocation_matrix, reference_for


FUNCTION_KEYS = ("F1", "F2", "F4", "F5", "F6", "F8")
GROUPS = {"N1": ("F4", "F5", "F8"), "I": ("F1", "F2", "F6")}
FUNCTION_GROUP = {function_key: group for group, keys in GROUPS.items() for function_key in keys}
DOMAIN_NAME = "wide"
ETA = 0.01
SEED_BASE = 50000
EXPECTED_APPENDIX_B = {"F4": (2, 1), "F5": (3, 1), "F8": (1, 2)}
OUTDIR = RESULTS / "diagnostic_ambiguity"
RECORDS_PATH = OUTDIR / "records.jsonl"
SUMMARY_JSON = OUTDIR / "summary.json"
SUMMARY_MD = OUTDIR / "summary.md"
DONE_PATH = OUTDIR / "DONE"
LOG_PATH = OUTDIR / "run.log"
NULLSPACE_CACHE_PATH = OUTDIR / "nullspace_cache.json"


def load_oracle_cache() -> dict:
    path = RESULTS / "oracle_reference_v3.json"
    return json.loads(path.read_text())


def diagnostic_settings() -> Settings:
    settings = settings_for_variant("standard", require_appendix=True)
    appendix = json.loads(APPENDIX_A_JSON.read_text())
    tau = float(appendix["tau"])
    if settings.ell_max != 4:
        raise RuntimeError(f"expected ell_max=4 from Appendix A, got {settings.ell_max}")
    if not math.isclose(float(settings.sigma_floor_factor), tau, rel_tol=0.0, abs_tol=0.0):
        raise RuntimeError(f"settings tau {settings.sigma_floor_factor} differs from Appendix A tau {tau}")
    return settings


def settings_payload(settings: Settings) -> dict:
    return asdict(settings)


def _oracle_class(cache: dict, function_key: str, cls: tuple[int, int]) -> dict:
    r, d = cls
    return cache["functions"][function_key][DOMAIN_NAME]["classes"][f"{r},{d}"]


def _n_exact(cache: dict, function_key: str, cls: tuple[int, int] | None) -> int | None:
    if cls is None:
        return None
    return int(_oracle_class(cache, function_key, cls)["n_exact"])


def _reference_class(cache: dict, function_key: str) -> tuple[int, int]:
    return tuple(cache["functions"][function_key][DOMAIN_NAME]["reference_class"])


def validate_references(cache: dict) -> dict:
    checked = {}
    for function_key in FUNCTION_KEYS:
        ref_class = _reference_class(cache, function_key)
        expected, ref_coeffs = reference_for(function_key, DOMAIN_NAME)
        if tuple(expected) != ref_class:
            raise RuntimeError(f"{function_key} reference_for returned {expected}, oracle has {ref_class}")
        basis = nullspace_basis(function_key, ref_class)
        if basis.shape[0] != 1:
            raise RuntimeError(f"{function_key}/{ref_class} reference nullspace dimension is {basis.shape[0]}, expected 1")
        ref_unit = normalize_coeffs(np.asarray(ref_coeffs, dtype=float))
        oracle_unit = normalize_coeffs(basis[0], align_to=ref_unit)
        max_abs_diff = float(np.max(np.abs(oracle_unit - ref_unit)))
        dot = float(np.dot(oracle_unit, ref_unit))
        if max_abs_diff > 1e-10 or dot < 1.0 - 1e-10:
            raise RuntimeError(f"{function_key}/{ref_class} coefficient order/scale check failed")
        checked[function_key] = {
            "reference_class": list(ref_class),
            "dot": dot,
            "max_abs_diff": max_abs_diff,
            "dimension": int(basis.shape[0]),
        }
    for function_key, expected in EXPECTED_APPENDIX_B.items():
        actual = _reference_class(cache, function_key)
        if actual != expected:
            raise RuntimeError(f"{function_key} Appendix B class expected {expected}, got {actual}")
    return checked


def nullspace_basis(function_key: str, cls: tuple[int, int]) -> np.ndarray:
    r, d = cls
    mp.mp.dps = ORACLE_DIGITS
    mat = _mp_collocation_matrix(function_key, DOMAIN_NAME, r, d)
    _, singular_values, vh = mp.svd_r(mat, full_matrices=False)
    svals = [mp.mpf(value) for value in singular_values]
    threshold = mp.mpf(str(ORACLE_REL_TOL)) * max(svals)
    exact_indices = [idx for idx, value in enumerate(svals) if value < threshold]
    rows = []
    for idx in exact_indices:
        row = vh[idx, :]
        vec = np.array([float(row[col]) for col in range(mat.cols)], dtype=float)
        rows.append(normalize_coeffs(vec))
    return np.vstack(rows) if rows else np.empty((0, (r + 1) * (d + 1)), dtype=float)


def load_nullspace_cache() -> dict:
    if not NULLSPACE_CACHE_PATH.exists():
        return {}
    return json.loads(NULLSPACE_CACHE_PATH.read_text())


def save_nullspace_cache(cache: dict) -> None:
    NULLSPACE_CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True))


def cached_nullspace(function_key: str, cls: tuple[int, int], cache: dict) -> np.ndarray:
    key = f"{function_key}:{cls[0]},{cls[1]}"
    if key not in cache:
        basis = nullspace_basis(function_key, cls)
        cache[key] = {"basis": basis.tolist(), "n_exact": int(basis.shape[0])}
        save_nullspace_cache(cache)
    return np.asarray(cache[key]["basis"], dtype=float)


def principal_angle_degrees(coeffs: np.ndarray | None, function_key: str, cls: tuple[int, int] | None, n_exact_value: int | None, cache: dict) -> float | None:
    if coeffs is None or cls is None or not n_exact_value:
        return None
    basis = cached_nullspace(function_key, cls, cache)
    if basis.shape[0] != n_exact_value:
        raise RuntimeError(f"cached basis dimension mismatch for {function_key}/{cls}: {basis.shape[0]} != {n_exact_value}")
    q_mat, _ = np.linalg.qr(basis.T)
    c_hat = np.asarray(coeffs, dtype=float)
    norm = float(np.linalg.norm(c_hat))
    if norm == 0.0:
        raise RuntimeError("zero selected coefficient vector")
    projected_norm = float(np.linalg.norm(q_mat @ (q_mat.T @ c_hat)))
    cosine = min(1.0, max(0.0, projected_norm / norm))
    return float(math.degrees(math.acos(cosine)))


def selection_payload(selection: Selection) -> dict:
    return {
        "selected_class": None if selection.selected_class is None else list(selection.selected_class),
        "T": selection.statistic,
        "dof": selection.dof,
        "critical": selection.critical,
        "singular_values": list(selection.singular_values),
        "A1": selection.a1,
        "A2": selection.a2,
        "A3": selection.a3,
        "bootstrap_share": selection.bootstrap_share,
        "tested_classes": selection.tested_classes,
        "aml_iterations": selection.aml_iterations,
        "aml_converged": selection.aml_converged,
        "aml_message": selection.aml_message,
        "theta_hat_c": selection.sqrt_trace_cov,
    }


def run_one(function_key: str, seed: int, *, settings: Settings | None = None, cache: dict | None = None, null_cache: dict | None = None) -> dict:
    settings = settings or diagnostic_settings()
    cache = cache or load_oracle_cache()
    null_cache = null_cache if null_cache is not None else load_nullspace_cache()
    spec = FUNCTIONS[function_key]
    start = time.perf_counter()
    _, z, values, _ = noisy_sample(function_key, domain_for(spec, DOMAIN_NAME), settings.n, ETA, seed)
    selection = full_search(z, values, ETA, seed, settings, with_bootstrap=True)
    expected = _reference_class(cache, function_key)
    state, sources = _state_for_clean(cache, function_key, DOMAIN_NAME, selection, expected, False)
    selected = None if selection.selected_class is None else tuple(selection.selected_class)
    n_exact_value = _n_exact(cache, function_key, selected)
    angle = principal_angle_degrees(selection.coeffs, function_key, selected, n_exact_value, null_cache)
    record = {
        "function": function_key,
        "group": FUNCTION_GROUP[function_key],
        "domain": DOMAIN_NAME,
        "eta": ETA,
        "seed": seed,
        "selected_class": None if selected is None else list(selected),
        "state": state,
        "ambiguity_sources": sources,
        "bootstrap_share": selection.bootstrap_share,
        "selected_is_reference": None if selected is None else selected == expected,
        "reference_class": list(expected),
        "n_exact": n_exact_value,
        "T": selection.statistic,
        "dof": selection.dof,
        "critical": selection.critical,
        "tested_classes": selection.tested_classes,
        "aml_iterations": selection.aml_iterations,
        "aml_converged": selection.aml_converged,
        "aml_message": selection.aml_message,
        "boot_reps": settings.boot_reps,
        "angle_degrees": angle,
        "wall_clock_seconds": time.perf_counter() - start,
        "selection": selection_payload(selection),
        "settings": settings_payload(settings),
    }
    return record


def iter_records(path: Path = RECORDS_PATH) -> Iterable[dict]:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if line.strip():
            yield json.loads(line)


def completed_keys(path: Path = RECORDS_PATH) -> set[tuple[str, int]]:
    return {(record["function"], int(record["seed"])) for record in iter_records(path)}


def append_record(record: dict) -> None:
    with RECORDS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()


def log_progress(record: dict) -> None:
    line = (
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"{record['function']} seed={record['seed']} state={record['state']} "
        f"tested={record['tested_classes']} aml={record['aml_iterations']} "
        f"seconds={record['wall_clock_seconds']:.3f}"
    )
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def tasks_for_reps(reps: int) -> list[tuple[str, int]]:
    return [(function_key, SEED_BASE + k) for k in range(reps) for function_key in FUNCTION_KEYS]


def run_reps(reps: int, workers: int) -> None:
    if workers < 1 or workers > 6:
        raise SystemExit("--workers must be between 1 and 6")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    cache = load_oracle_cache()
    validate_references(cache)
    settings = diagnostic_settings()
    done = completed_keys()
    tasks = [task for task in tasks_for_reps(reps) if task not in done]
    if workers == 1:
        null_cache = load_nullspace_cache()
        for function_key, seed in tasks:
            record = run_one(function_key, seed, settings=settings, cache=cache, null_cache=null_cache)
            append_record(record)
            log_progress(record)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run_one, function_key, seed): (function_key, seed) for function_key, seed in tasks}
            for future in as_completed(futures):
                record = future.result()
                append_record(record)
                log_progress(record)
    DONE_PATH.write_text(datetime.now().isoformat(timespec="seconds") + "\n")


def _rate(count: int, total: int) -> float | None:
    return None if total == 0 else count / total


def state_table(records: list[dict]) -> dict:
    counts = Counter(record["state"] for record in records)
    total = len(records)
    return {state: {"count": counts[state], "share": _rate(counts[state], total)} for state in ("NONE", "AMBIGUOUS", "CORRECT", "TRUE_NOT_REF", "WRONG")}


def source_table(records: list[dict]) -> dict:
    counts: Counter[str] = Counter()
    for record in records:
        if record["state"] != "AMBIGUOUS":
            continue
        sources = tuple(sorted(record.get("ambiguity_sources") or []))
        if len(sources) > 1:
            counts["multiple"] += 1
        elif len(sources) == 1:
            counts[sources[0]] += 1
    return {key: counts[key] for key in ("A1", "A2", "A3", "multiple")}


def wrong_given_unambiguous(records: list[dict]) -> float | None:
    unambiguous = [record for record in records if record["state"] in {"CORRECT", "TRUE_NOT_REF", "WRONG"}]
    if not unambiguous:
        return None
    return sum(record["state"] == "WRONG" for record in unambiguous) / len(unambiguous)


def median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(np.median(np.asarray(values, dtype=float)))


def angle_summary(records: list[dict]) -> dict:
    out = {}
    for function_key in FUNCTION_KEYS:
        out[function_key] = {}
        for state in ("NONE", "AMBIGUOUS", "CORRECT", "TRUE_NOT_REF", "WRONG"):
            vals = [float(record["angle_degrees"]) for record in records if record["function"] == function_key and record["state"] == state and record.get("angle_degrees") is not None]
            out[function_key][state] = {"median": median(vals), "max": max(vals) if vals else None}
    return out


def cost_summary(records: list[dict]) -> dict:
    out = {}
    for function_key in FUNCTION_KEYS:
        subset = [record for record in records if record["function"] == function_key]
        out[function_key] = {}
        for field in ("tested_classes", "aml_iterations", "wall_clock_seconds"):
            vals = [float(record[field]) for record in subset if record.get(field) is not None]
            out[function_key][field] = {"mean": (sum(vals) / len(vals)) if vals else None, "max": max(vals) if vals else None}
    return out


def b_criteria(records: list[dict]) -> dict:
    by_group = {group: [record for record in records if record["group"] == group] for group in GROUPS}
    n1 = by_group["N1"]
    ident = by_group["I"]
    n1_unambiguous = [record for record in n1 if record["state"] in {"CORRECT", "TRUE_NOT_REF", "WRONG"}]
    n1_wrong_cond = 0.0 if not n1_unambiguous else sum(record["state"] == "WRONG" for record in n1_unambiguous) / len(n1_unambiguous)
    n1_amb = sum(record["state"] == "AMBIGUOUS" for record in n1) / len(n1) if n1 else None
    i_correct = sum(record["state"] == "CORRECT" for record in ident) / len(ident) if ident else None
    i_amb = sum(record["state"] == "AMBIGUOUS" for record in ident) / len(ident) if ident else None
    delta = None if n1_amb is None or i_amb is None else n1_amb - i_amb
    return {
        "B1": {"value": n1_wrong_cond, "threshold": "< 0.20", "passed": n1_wrong_cond < 0.20},
        "B2": {"value": n1_amb, "threshold": ">= 0.50", "passed": n1_amb is not None and n1_amb >= 0.50},
        "B3": {"value": i_correct, "threshold": ">= 0.70", "passed": i_correct is not None and i_correct >= 0.70},
        "B4": {"value": delta, "threshold": ">= 0.25", "passed": delta is not None and delta >= 0.25},
    }


def same_n_per_function(records: list[dict]) -> tuple[bool, dict[str, int]]:
    counts = {function_key: sum(record["function"] == function_key for record in records) for function_key in FUNCTION_KEYS}
    return len(set(counts.values())) == 1 and next(iter(counts.values()), 0) > 0, counts


def summarize_records(records: list[dict]) -> dict:
    by_function = {function_key: [record for record in records if record["function"] == function_key] for function_key in FUNCTION_KEYS}
    by_group = {group: [record for record in records if record["group"] == group] for group in GROUPS}
    complete, counts = same_n_per_function(records)
    criteria = b_criteria(records) if complete else None
    verdict = "incomplete"
    if criteria is not None:
        verdict = "interesting" if all(item["passed"] for item in criteria.values()) else "negative"
    return {
        "records": len(records),
        "records_per_function": counts,
        "complete_equal_n": complete,
        "by_function": {
            function_key: {
                "states": state_table(subset),
                "ambiguous_sources": source_table(subset),
                "wrong_given_unambiguous": wrong_given_unambiguous(subset),
            }
            for function_key, subset in by_function.items()
        },
        "by_group": {
            group: {
                "states": state_table(subset),
                "ambiguous_sources": source_table(subset),
                "wrong_given_unambiguous": wrong_given_unambiguous(subset),
            }
            for group, subset in by_group.items()
        },
        "criteria": criteria,
        "verdict": verdict,
        "angles": angle_summary(records),
        "costs": cost_summary(records),
    }


def write_summary(summary: dict) -> None:
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True))
    lines = [
        "# Diagnostic Ambiguity Summary",
        "",
        "This is a diagnostic with Gate 2A v3, not a Gate run.",
        "",
        f"- records: {summary['records']}",
        f"- complete_equal_n: {summary['complete_equal_n']}",
        f"- verdict: {summary['verdict']}",
        "",
        "## Criteria",
        "",
        "| Criterion | Value | Threshold | Passed |",
        "|---|---:|---|---:|",
    ]
    criteria = summary.get("criteria")
    if criteria is None:
        lines.append("| B1-B4 | null | equal N per function required | null |")
    else:
        for key, item in criteria.items():
            lines.append(f"| {key} | {item['value']} | {item['threshold']} | {item['passed']} |")
    lines.extend(["", "## Groups", "", "| Group | NONE | AMBIGUOUS | CORRECT | TRUE_NOT_REF | WRONG | Wrong given unambiguous |", "|---|---:|---:|---:|---:|---:|---:|"])
    for group, payload in summary["by_group"].items():
        states = payload["states"]
        lines.append(
            f"| {group} | {states['NONE']['count']} | {states['AMBIGUOUS']['count']} | "
            f"{states['CORRECT']['count']} | {states['TRUE_NOT_REF']['count']} | {states['WRONG']['count']} | "
            f"{payload['wrong_given_unambiguous']} |"
        )
    SUMMARY_MD.write_text("\n".join(lines) + "\n")


def summarize() -> dict:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    records = list(iter_records())
    summary = summarize_records(records)
    write_summary(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reps", type=int, default=None)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    if args.summarize:
        summarize()
        return
    reps = 2 if args.pilot else args.reps
    if reps is None:
        raise SystemExit("use --reps N, --pilot, or --summarize")
    if reps < 0:
        raise SystemExit("--reps must be non-negative")
    run_reps(reps, args.workers)


if __name__ == "__main__":
    main()
