"""Stage K calibration for Gate 2A v2."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.stats import ncx2

from experiments.annihilator_gate2a_v2.config import (
    APPENDIX_A_JSON,
    CALIBRATION_FUNCTIONS,
    K_MATRIX_THRESHOLD,
    RESULTS,
    TAU_MAX,
    Settings,
    calibration_reference_coeffs,
    domain_for,
)
from experiments.annihilator_gate2a_v2.functions import grid, noisy_sample, numeric_values, rms, sigma_eff
from experiments.annihilator_gate2a_v2.operator_search import evaluate_class, full_search, normalize_coeffs, test_operator
from experiments.annihilator_gate2a_v2.oracle import ORACLE_METADATA, build_reference
from experiments.annihilator_gate2a_v2.weak_operator import WeightContext, residual_weights


MC_FUNCTIONS = ("K1", "K2", "K3", "K4", "K5", "K6")
CLEAN_FUNCTIONS = tuple(CALIBRATION_FUNCTIONS)


def _settings(ell_max: int, tau: float = 1e-12, *, n: int = 2000, boot_reps: int = 50) -> Settings:
    return Settings(n=n, ell_max=ell_max, sigma_floor_factor=tau, boot_reps=boot_reps)


def _reference(function_key: str, domain_name: str) -> tuple[tuple[int, int], np.ndarray]:
    cls, coeffs = calibration_reference_coeffs(function_key, domain_name)
    return cls, normalize_coeffs(np.asarray(coeffs, dtype=float))


def _oracle_cache(required: bool) -> dict | None:
    cache_path = RESULTS / "oracle_reference_v2.json"
    if not cache_path.exists():
        if required:
            raise RuntimeError(f"v2 oracle cache missing for TRUE_NOT_REF classification: {cache_path}")
        return None
    data = json.loads(cache_path.read_text())
    if data.get("metadata") != ORACLE_METADATA:
        if required:
            raise RuntimeError(f"v2 oracle cache metadata mismatch: {cache_path}")
        return None
    return data


def _oracle_n_exact(cache: dict, function_key: str, domain_name: str, cls: tuple[int, int]) -> int:
    r, d = cls
    return int(cache["functions"][function_key][domain_name]["classes"][f"{r},{d}"]["n_exact"])


def _state_for_clean(cache: dict | None, function_key: str, domain_name: str, selection, expected: tuple[int, int], limit: bool) -> tuple[str, list[str]]:
    sources = []
    if selection.a1:
        sources.append("A1")
    if selection.a2:
        sources.append("A2")
    if selection.a3:
        sources.append("A3")
    if selection.selected_class is None:
        return "NONE", sources
    if sources:
        return "AMBIGUOUS", sources
    selected = tuple(selection.selected_class)
    if selected == expected:
        return "CORRECT", sources
    if cache is None and not limit:
        raise RuntimeError("v2 oracle cache is required to distinguish TRUE_NOT_REF from WRONG")
    if cache is not None and _oracle_n_exact(cache, function_key, domain_name, selected) > 0:
        return "TRUE_NOT_REF", sources
    return "WRONG", sources


def _cell_matrix_error(function_key: str, domain_name: str, split: str, ell_max: int, n: int) -> dict:
    spec = CALIBRATION_FUNCTIONS[function_key]
    domain = domain_for(spec, domain_name)
    x, z = grid(domain, n)
    values = numeric_values(function_key, x)
    (r, d), coeffs = _reference(function_key, domain_name)
    context = WeightContext(z, values, _settings(ell_max, n=n, boot_reps=1))
    k_fit, k_val, a_fit, a_val = context.split(r, d)
    tensor = k_fit if split == "fit" else k_val
    matrix = a_fit if split == "fit" else a_val
    residual = matrix @ coeffs
    row_noise = np.linalg.norm(residual_weights(tensor, coeffs), axis=1) * rms(values)
    scaled = np.abs(residual) / np.maximum(row_noise, 1e-300)
    return {
        "function": function_key,
        "domain": domain_name,
        "split": split,
        "class": [r, d],
        "max_scaled_error": float(np.max(scaled)),
        "passed": bool(np.max(scaled) <= K_MATRIX_THRESHOLD),
        "accepted_deviation": "compared against Ac*=0; equivalent because L*f is identically zero and boundary terms vanish",
    }


def stage_k_a(n: int, limit: bool = False) -> dict:
    by_ell = {}
    ell_values = (3,) if limit else (3, 4, 5)
    function_keys = ("K1", "K2") if limit else CLEAN_FUNCTIONS
    for ell_max in ell_values:
        records = [
            _cell_matrix_error(function_key, domain_name, split, ell_max, n)
            for function_key in function_keys
            for domain_name in ("wide", "narrow")
            for split in ("fit", "val")
        ]
        by_ell[str(ell_max)] = {
            "records": records,
            "max_error": max(record["max_scaled_error"] for record in records),
            "passed": all(record["passed"] for record in records),
        }
    eligible = [ell for ell in ell_values if by_ell[str(ell)]["passed"]]
    return {"ell_max": max(eligible) if eligible else None, "by_ell": by_ell, "passed": bool(eligible)}


def _tau_cell(function_key: str, domain_name: str, ell_max: int, n: int) -> dict:
    spec = CALIBRATION_FUNCTIONS[function_key]
    domain = domain_for(spec, domain_name)
    x, z = grid(domain, n)
    values = numeric_values(function_key, x)
    (r, d), coeffs = _reference(function_key, domain_name)
    context = WeightContext(z, values, _settings(ell_max, n=n, boot_reps=1))
    _, k_val, _, a_val = context.split(r, d)
    coeff_cov = np.zeros((coeffs.size, coeffs.size), dtype=float)
    test = test_operator(a_val, k_val, coeffs, coeff_cov, rms(values), _settings(ell_max, n=n, boot_reps=1))
    tau_cell = float(np.sqrt(test.statistic / test.critical)) if test.critical > 0 else float("inf")
    return {"function": function_key, "domain": domain_name, "T1": test.statistic, "dof": test.dof, "critical": test.critical, "tau_cell": tau_cell}


def stage_k_b(ell_max: int, n: int, limit: bool = False) -> dict:
    function_keys = ("K1", "K2") if limit else CLEAN_FUNCTIONS
    records = [_tau_cell(function_key, domain_name, ell_max, n) for function_key in function_keys for domain_name in ("wide", "narrow")]
    tau = max(10.0 * max(record["tau_cell"] for record in records), 1e-12)
    return {"tau": tau, "records": records, "passed": tau <= TAU_MAX}


def ex_ante_k_classes(ell_max: int, tau: float, n: int) -> dict:
    from experiments.annihilator_gate2a_v2.config import CLASSES

    records = {}
    for function_key, spec in CALIBRATION_FUNCTIONS.items():
        records[function_key] = {}
        for domain_name in ("wide", "narrow"):
            domain = domain_for(spec, domain_name)
            x, z = grid(domain, n)
            values = numeric_values(function_key, x)
            sigma = sigma_eff(values, 0.01, tau)
            ref_class, _ = _reference(function_key, domain_name)
            context = WeightContext(z, values, _settings(ell_max, tau, n=n, boot_reps=1))
            earlier = []
            identifiable = True
            for cls in CLASSES:
                if cls == ref_class:
                    break
                r, d = cls
                k_fit, k_val, a_fit, a_val = context.split(r, d)
                evaluation = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, _settings(ell_max, tau, n=n, boot_reps=1))
                beta = float(ncx2.sf(evaluation.test.critical, evaluation.test.dof, evaluation.test.statistic)) if evaluation.test.dof > 0 else 0.0
                earlier.append({"class": [r, d], "beta": beta})
                if beta < 0.9:
                    identifiable = False
            r, d = ref_class
            k_fit, k_val, a_fit, a_val = context.split(r, d)
            ref_eval = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, _settings(ell_max, tau, n=n, boot_reps=1))
            theta = float(np.sqrt(max(0.0, np.trace(ref_eval.coeff_cov))))
            cls_name = "I" if identifiable and theta <= 0.1 else ("N1" if not identifiable else "N2")
            records[function_key][domain_name] = {"class": cls_name, "theta_hat_c": theta, "earlier": earlier}
    return records


def _selected_seeds(reps: int, part: str | None) -> list[int]:
    seeds = list(range(reps))
    if not part:
        return seeds
    index_text, count_text = part.split("/")
    index = int(index_text)
    count = int(count_text)
    if index < 0 or index >= count:
        raise ValueError(f"invalid part {part!r}")
    return [seed for seed in seeds if seed % count == index]


def _empty_mc_accumulator(function_key: str, class_name: str) -> dict:
    return {
        "function": function_key,
        "domain": "wide",
        "ex_ante_class": class_name,
        "checked": class_name == "I",
        "seeds": [],
        "rejects": 0,
        "stats": [],
        "coeff_sum": None,
        "coeff_cross": None,
        "propagated_trace_sum": 0.0,
    }


def _finish_mc_record(acc: dict, true_coeffs: np.ndarray) -> dict:
    if not acc["checked"]:
        return {
            "function": acc["function"],
            "domain": "wide",
            "ex_ante_class": acc["ex_ante_class"],
            "checked": False,
            "not_checked_reason": f"ex-ante class {acc['ex_ante_class']}",
            "passed": None,
        }
    n = len(acc["seeds"])
    coeff_sum = np.asarray(acc["coeff_sum"], dtype=float)
    coeff_cross = np.asarray(acc["coeff_cross"], dtype=float)
    mean_coeff = coeff_sum / n
    empirical_cov = coeff_cross / max(n - 1, 1) - np.outer(coeff_sum, coeff_sum) / (n * max(n - 1, 1)) if n > 1 else np.zeros_like(coeff_cross)
    rejection_rate = acc["rejects"] / n if n else None
    median_t = float(np.nanmedian(acc["stats"])) if acc["stats"] else None
    bias = float(np.linalg.norm(mean_coeff - true_coeffs)) if n else None
    empirical_trace = float(np.trace(empirical_cov)) if n else None
    propagated_trace = acc["propagated_trace_sum"] / n if n else None
    bias_threshold = 0.5 * np.sqrt(max(empirical_trace or 0.0, 0.0))
    trace_ratio = empirical_trace / propagated_trace if propagated_trace and propagated_trace > 0 else None
    points = {
        "1": {
            "rejection_rate": rejection_rate,
            "median_T_over_dof": median_t,
            "threshold": "rejection_rate <= 0.03 and median_T_over_dof in [0.8, 1.25]",
            "passed": rejection_rate is not None and rejection_rate <= 0.03 and median_t is not None and 0.8 <= median_t <= 1.25,
        },
        "2": {
            "bias_norm": bias,
            "threshold": bias_threshold,
            "passed": bias is not None and bias <= bias_threshold,
        },
        "3": {
            "empirical_trace": empirical_trace,
            "mean_propagated_trace": propagated_trace,
            "ratio": trace_ratio,
            "threshold": "0.5 <= ratio <= 2",
            "passed": trace_ratio is not None and 0.5 <= trace_ratio <= 2.0,
        },
    }
    return {
        "function": acc["function"],
        "domain": "wide",
        "ex_ante_class": acc["ex_ante_class"],
        "checked": True,
        "seeds": acc["seeds"],
        "n": n,
        "points": points,
        "passed": all(point["passed"] for point in points.values()),
    }


def _mc_accumulators(ell_max: int, tau: float, n: int, reps: int, part: str | None, ex_ante: dict, limit: bool) -> dict:
    seeds = _selected_seeds(reps, part)
    settings = _settings(ell_max, tau, n=n, boot_reps=1)
    function_keys = ("K1",) if limit else MC_FUNCTIONS
    accumulators = {}
    for function_key in function_keys:
        class_name = ex_ante.get(function_key, {}).get("wide", {}).get("class", "I" if limit else "missing")
        acc = _empty_mc_accumulator(function_key, class_name)
        if acc["checked"]:
            spec = CALIBRATION_FUNCTIONS[function_key]
            (r, d), true_coeffs = _reference(function_key, "wide")
            for seed in seeds:
                _, z, values, _ = noisy_sample(function_key, spec.wide, n, 0.01, seed)
                context = WeightContext(z, values, settings)
                k_fit, k_val, a_fit, a_val = context.split(r, d)
                sigma = sigma_eff(values, 0.01, tau)
                evaluation = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, settings)
                aligned = normalize_coeffs(evaluation.coeffs, align_to=true_coeffs)
                acc["seeds"].append(seed)
                acc["rejects"] += int(not evaluation.test.passed)
                acc["stats"].append(evaluation.test.statistic / evaluation.test.dof if evaluation.test.dof else np.nan)
                acc["coeff_sum"] = aligned if acc["coeff_sum"] is None else np.asarray(acc["coeff_sum"]) + aligned
                outer = np.outer(aligned, aligned)
                acc["coeff_cross"] = outer if acc["coeff_cross"] is None else np.asarray(acc["coeff_cross"]) + outer
                acc["propagated_trace_sum"] += float(np.trace(evaluation.coeff_cov))
        accumulators[function_key] = acc
    return accumulators


def _clean_records(ell_max: int, tau: float, n: int, limit: bool) -> dict:
    settings = _settings(ell_max, tau, n=n, boot_reps=1 if limit else 50)
    cache = _oracle_cache(required=not limit)
    records = {}
    function_keys = ("K1",) if limit else CLEAN_FUNCTIONS
    for function_key in function_keys:
        spec = CALIBRATION_FUNCTIONS[function_key]
        for domain_name in ("wide", "narrow"):
            _, z, values, _ = noisy_sample(function_key, domain_for(spec, domain_name), n, 0.0, 0)
            selection = full_search(z, values, 0.0, 0, settings, with_bootstrap=not limit)
            expected, _ = _reference(function_key, domain_name)
            state, sources = _state_for_clean(cache, function_key, domain_name, selection, expected, limit)
            passed = state == "CORRECT" if domain_name == "wide" else state != "WRONG"
            records[f"{function_key}_{domain_name}"] = {
                "function": function_key,
                "domain": domain_name,
                "selected_class": None if selection.selected_class is None else list(selection.selected_class),
                "expected_class": list(expected),
                "state": state,
                "ambiguity_sources": sources,
                "threshold": "wide CORRECT; narrow not WRONG",
                "passed": passed,
            }
    return records


def stage_k_c(ell_max: int, tau: float, n: int, reps: int, part: str | None, ex_ante: dict, limit: bool) -> dict:
    accumulators = _mc_accumulators(ell_max, tau, n, reps, part, ex_ante, limit)
    mc_records = {}
    for function_key, acc in accumulators.items():
        _, true_coeffs = _reference(function_key, "wide")
        mc_records[function_key] = _finish_mc_record(acc, true_coeffs)
    clean = _clean_records(ell_max, tau, n, limit)
    clean_passed = all(record["passed"] for record in clean.values())
    mc_passed = all(record["passed"] is not False for record in mc_records.values())
    return {
        "part": part,
        "mc_accumulators": accumulators,
        "mc": mc_records,
        "clean": clean,
        "points_passed": {"1_3": mc_passed, "4": clean_passed},
        "passed": mc_passed and clean_passed,
    }


def _part_path(part: str, limit: bool) -> Path:
    safe = part.replace("/", "_of_")
    name = f"appendix_A_limit_part_{safe}.json" if limit else f"appendix_A_part_{safe}.json"
    return RESULTS / "calibration" / name


def _combine_accumulators(parts: list[dict]) -> dict:
    combined = {}
    for payload in parts:
        for function_key, acc in payload["K_c"]["mc_accumulators"].items():
            target = combined.get(function_key)
            if target is None:
                target = dict(acc)
                target["seeds"] = list(acc["seeds"])
                target["stats"] = list(acc["stats"])
                target["coeff_sum"] = None if acc["coeff_sum"] is None else np.asarray(acc["coeff_sum"], dtype=float)
                target["coeff_cross"] = None if acc["coeff_cross"] is None else np.asarray(acc["coeff_cross"], dtype=float)
                combined[function_key] = target
                continue
            target["seeds"].extend(acc["seeds"])
            target["rejects"] += acc["rejects"]
            target["stats"].extend(acc["stats"])
            target["propagated_trace_sum"] += acc["propagated_trace_sum"]
            if acc["coeff_sum"] is not None:
                target["coeff_sum"] = np.asarray(target["coeff_sum"]) + np.asarray(acc["coeff_sum"], dtype=float)
                target["coeff_cross"] = np.asarray(target["coeff_cross"]) + np.asarray(acc["coeff_cross"], dtype=float)
    for target in combined.values():
        if target["coeff_sum"] is not None:
            target["coeff_sum"] = np.asarray(target["coeff_sum"]).tolist()
            target["coeff_cross"] = np.asarray(target["coeff_cross"]).tolist()
    return combined


def merge_parts(reps: int, count: int, limit: bool) -> dict:
    part_payloads = []
    missing = []
    for index in range(count):
        path = _part_path(f"{index}/{count}", limit)
        if not path.exists():
            missing.append(str(path))
        else:
            part_payloads.append(json.loads(path.read_text()))
    if missing:
        raise RuntimeError(f"incomplete Stage K part set; missing {missing}")
    base = dict(part_payloads[0])
    combined_acc = _combine_accumulators(part_payloads)
    mc_records = {}
    for function_key, acc in combined_acc.items():
        _, true_coeffs = _reference(function_key, "wide")
        mc_records[function_key] = _finish_mc_record(acc, true_coeffs)
    all_seeds = sorted({seed for acc in combined_acc.values() for seed in acc["seeds"]})
    if all_seeds != list(range(reps)):
        raise RuntimeError(f"incomplete Stage K seed set; got {len(all_seeds)} of {reps} seeds")
    base["settings"] = dict(base["settings"], part=None, merged_parts=count)
    base["K_c"] = {
        "part": None,
        "mc_accumulators": combined_acc,
        "mc": mc_records,
        "clean": base["K_c"]["clean"],
        "points_passed": {
            "1_3": all(record["passed"] is not False for record in mc_records.values()),
            "4": all(record["passed"] for record in base["K_c"]["clean"].values()),
        },
    }
    base["K_c"]["passed"] = base["K_c"]["points_passed"]["1_3"] and base["K_c"]["points_passed"]["4"]
    base["passed"] = bool(base["K_a"]["passed"] and base["K_b"]["passed"] and base["K_c"]["passed"])
    return base


def _json_safe(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"cannot serialize {type(value).__name__}")


def write_markdown(path: Path, payload: dict) -> None:
    lines = [
        "# Appendix A - Gate 2A v2 Stage K",
        "",
        f"- ell_max: {payload.get('ell_max')}",
        f"- tau: {payload.get('tau')}",
        f"- overall_passed: {payload.get('passed')}",
        f"- runtime_seconds: {payload.get('runtime_seconds')}",
        "",
        "## K-c Monte Carlo",
        "",
        "| Function | Ex-ante | Checked | Point 1 | Point 2 | Point 3 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for record in payload.get("K_c", {}).get("mc", {}).values():
        points = record.get("points", {})
        lines.append(
            f"| {record['function']} | {record.get('ex_ante_class')} | {record.get('checked')} | "
            f"{points.get('1', {}).get('passed')} | {points.get('2', {}).get('passed')} | {points.get('3', {}).get('passed')} |"
        )
    lines.extend(["", "## K-c Clean", "", "| Cell | State | Passed |", "|---|---:|---:|"])
    for cell, record in payload.get("K_c", {}).get("clean", {}).items():
        lines.append(f"| {cell} | {record.get('state')} | {record.get('passed')} |")
    path.write_text("\n".join(lines) + "\n")


def build_payload(n: int, reps: int, part: str | None, limit: bool) -> dict:
    start = time.perf_counter()
    k_a = stage_k_a(n, limit=limit)
    payload = {"settings": {"n": n, "reps": reps, "part": part, "limit": limit}, "K_a": k_a}
    if not k_a["passed"]:
        payload.update({"passed": False, "stop_reason": "K-a failed at ell=3", "runtime_seconds": time.perf_counter() - start})
        return payload
    ell_max = int(k_a["ell_max"])
    k_b = stage_k_b(ell_max, n, limit=limit)
    payload.update({"ell_max": ell_max, "K_b": k_b, "tau": k_b["tau"]})
    if not k_b["passed"]:
        payload.update({"passed": False, "stop_reason": "K-b tau exceeds 1e-4", "runtime_seconds": time.perf_counter() - start})
        return payload
    ex_ante = {"K1": {"wide": {"class": "I"}}} if limit else ex_ante_k_classes(ell_max, k_b["tau"], n)
    k_c = stage_k_c(ell_max, k_b["tau"], n, reps, part, ex_ante, limit)
    payload.update({"ex_ante_classes": ex_ante, "K_c": k_c, "passed": bool(k_a["passed"] and k_b["passed"] and k_c["passed"]), "runtime_seconds": time.perf_counter() - start})
    return payload


def main() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--limit", action="store_true")
    arg_parser.add_argument("--n", type=int, default=400)
    arg_parser.add_argument("--reps", type=int, default=1000)
    arg_parser.add_argument("--part", help="Run only seeds where seed %% count == index, formatted index/count.")
    arg_parser.add_argument("--merge-parts", type=int, help="Merge a complete set of part files with this part count.")
    args = arg_parser.parse_args()
    n = min(args.n, 120) if args.limit else args.n
    reps = min(args.reps, 2) if args.limit else args.reps
    outdir = RESULTS / "calibration"
    outdir.mkdir(parents=True, exist_ok=True)
    if args.merge_parts:
        payload = merge_parts(reps, args.merge_parts, args.limit)
        json_path = outdir / "appendix_A_limit.json" if args.limit else APPENDIX_A_JSON
        md_path = outdir / "appendix_A_limit.md" if args.limit else outdir / "appendix_A.md"
    else:
        payload = build_payload(n, reps, args.part, args.limit)
        if args.part:
            json_path = _part_path(args.part, args.limit)
            md_path = json_path.with_suffix(".md")
        else:
            json_path = outdir / "appendix_A_limit.json" if args.limit else APPENDIX_A_JSON
            md_path = outdir / "appendix_A_limit.md" if args.limit else outdir / "appendix_A.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_safe))
    write_markdown(md_path, payload)
    print(f"wrote {json_path}")


if __name__ == "__main__":
    main()
