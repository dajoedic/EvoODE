"""Direct sparse-regression reality check for Gate 2A v3 samples."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
import json
import math
import time
from pathlib import Path
from typing import Callable, Iterable, Sequence

import numpy as np
from scipy.stats import chi2

from experiments.annihilator_gate2a_v3.config import FUNCTIONS, RESULTS, Settings, domain_for
from experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic import diagnostic_settings
from experiments.annihilator_gate2a_v3.functions import noisy_sample, numeric_values, rms, sigma_eff


DOMAIN_NAME = "wide"
ETA = 0.01
SEED_BASE = 50000
SEED_END = 50019
ALPHA = 0.01
K_MAX = 4
STLSQ_THRESHOLD = 0.1
STLSQ_MAX_ITER = 20
FUNCTION_KEYS = tuple(FUNCTIONS)
PRIMARY_FUNCTIONS = ("F4", "F5", "F8")
CONTROL_FUNCTIONS = ("F1", "F2", "F6")
SECONDARY_FUNCTIONS = ("F3", "F7", "F9", "F10")
COMPARISON_GROUPS = {"N1": PRIMARY_FUNCTIONS, "I": CONTROL_FUNCTIONS}
OUTDIR = RESULTS / "reality_check_direct"
ANNIHILATOR_RECORDS = RESULTS / "diagnostic_ambiguity" / "orion" / "results" / "records_merged.jsonl"


@dataclass(frozen=True)
class Term:
    name: str
    evaluate: Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True)
class FitResult:
    selected: tuple[str, ...] | None
    coefficients: dict[str, float]
    rss: float | None
    statistic: float | None
    critical: float | None
    fits: int
    accepted_at_k: int | None
    fail_reason: str | None = None


def _as_float_array(values: np.ndarray | float) -> np.ndarray:
    return np.asarray(values, dtype=float)


def library() -> list[Term]:
    return [
        Term("1", lambda x: np.ones_like(_as_float_array(x))),
        Term("x", lambda x: _as_float_array(x)),
        Term("x^2", lambda x: _as_float_array(x) ** 2),
        Term("x^3", lambda x: _as_float_array(x) ** 3),
        Term("x^4", lambda x: _as_float_array(x) ** 4),
        Term("sqrt(x)", lambda x: np.sqrt(_as_float_array(x))),
        Term("x^1.5", lambda x: _as_float_array(x) ** 1.5),
        Term("log(x)", lambda x: np.log(_as_float_array(x))),
        Term("x log(x)", lambda x: _as_float_array(x) * np.log(_as_float_array(x))),
        Term("exp(x)", lambda x: np.exp(_as_float_array(x))),
        Term("exp(-x)", lambda x: np.exp(-_as_float_array(x))),
        Term("exp(1.5x)", lambda x: np.exp(1.5 * _as_float_array(x))),
        Term("exp(-1.5x)", lambda x: np.exp(-1.5 * _as_float_array(x))),
        Term("exp(2x)", lambda x: np.exp(2.0 * _as_float_array(x))),
        Term("exp(-2x)", lambda x: np.exp(-2.0 * _as_float_array(x))),
        Term("exp(-x^2)", lambda x: np.exp(-(_as_float_array(x) ** 2))),
        Term("x exp(-x^2)", lambda x: _as_float_array(x) * np.exp(-(_as_float_array(x) ** 2))),
        Term("sin(x)", lambda x: np.sin(_as_float_array(x))),
        Term("cos(x)", lambda x: np.cos(_as_float_array(x))),
        Term("sin(2x)", lambda x: np.sin(2.0 * _as_float_array(x))),
        Term("cos(2x)", lambda x: np.cos(2.0 * _as_float_array(x))),
        Term("1/(1+x)", lambda x: 1.0 / (1.0 + _as_float_array(x))),
        Term("1/(2+x)", lambda x: 1.0 / (2.0 + _as_float_array(x))),
    ]


LIBRARY = library()
TERM_BY_NAME = {term.name: term for term in LIBRARY}

TRUE_COEFFICIENTS: dict[str, dict[str, float]] = {
    "F1": {"x^2": 1.0},
    "F2": {"exp(1.5x)": 1.0},
    "F3": {"x^1.5": 1.0},
    "F4": {"log(x)": 1.0},
    "F5": {"x log(x)": 1.0},
    "F6": {"exp(-x^2)": 1.0},
    "F7": {"sin(2x)": math.cos(0.5), "cos(2x)": math.sin(0.5)},
    "F8": {"1": 1.0, "1/(2+x)": -2.0},
    "F9": {"x^2": 1.0, "exp(x)": 1.0},
    "F10": {"sin(x)": 1.0, "exp(-x^2)": 1.0},
}


def output_paths(outdir: Path = OUTDIR) -> dict[str, Path]:
    return {
        "outdir": outdir,
        "records": outdir / "records.jsonl",
        "exact": outdir / "exact_check.json",
        "summary_json": outdir / "summary.json",
        "summary_md": outdir / "summary.md",
        "log": outdir / "run.log",
    }


def tau_from_diagnostic_settings() -> float:
    return float(diagnostic_settings().sigma_floor_factor)


def is_finite_real(values: np.ndarray) -> bool:
    arr = np.asarray(values)
    return not np.iscomplexobj(arr) and bool(np.all(np.isfinite(arr.astype(float))))


def admissible_terms(function_key: str, *, grid_size: int | None = None) -> list[Term]:
    spec = FUNCTIONS[function_key]
    domain = domain_for(spec, DOMAIN_NAME)
    n = Settings().n if grid_size is None else grid_size
    singular_points = [point for point in (-2.0, -1.0, 0.0) if domain.a <= point <= domain.b]
    points = np.concatenate(([domain.a, domain.b], singular_points, np.linspace(domain.a, domain.b, n)))
    out: list[Term] = []
    for term in LIBRARY:
        with np.errstate(all="ignore"):
            try:
                values = term.evaluate(points)
            except (FloatingPointError, ValueError, ZeroDivisionError, OverflowError):
                continue
        if is_finite_real(values):
            out.append(term)
    return out


def design_matrix(x: np.ndarray, terms: Sequence[Term]) -> np.ndarray:
    columns = []
    for term in terms:
        with np.errstate(all="ignore"):
            column = np.asarray(term.evaluate(x), dtype=float)
        columns.append(column)
    return np.column_stack(columns) if columns else np.empty((len(x), 0), dtype=float)


def fit_subset(x: np.ndarray, y: np.ndarray, terms: Sequence[Term]) -> tuple[dict[str, float] | None, float | None]:
    matrix = design_matrix(x, terms)
    if not is_finite_real(matrix):
        return None, None
    try:
        coeffs, *_ = np.linalg.lstsq(matrix, y, rcond=None)
    except np.linalg.LinAlgError:
        return None, None
    if not np.all(np.isfinite(coeffs)):
        return None, None
    residual = y - matrix @ coeffs
    rss = float(np.dot(residual, residual))
    return {term.name: float(coeff) for term, coeff in zip(terms, coeffs)}, rss


def chi2_critical(n: int, k: int) -> float:
    return float(chi2.ppf(0.99, n - k))


def best_subset_fit(x: np.ndarray, y: np.ndarray, sigma: float, terms: Sequence[Term]) -> FitResult:
    fits = 0
    if sigma <= 0.0 or not math.isfinite(sigma):
        return FitResult(None, {}, None, None, None, fits, None, "nonpositive sigma")
    for k in range(1, K_MAX + 1):
        accepted: list[tuple[float, dict[str, float], tuple[Term, ...], float, float]] = []
        for subset in combinations(terms, k):
            fits += 1
            coeffs, rss = fit_subset(x, y, subset)
            if coeffs is None or rss is None:
                continue
            statistic = rss / (sigma**2)
            critical = chi2_critical(len(y), k)
            if statistic <= critical:
                accepted.append((rss, coeffs, tuple(subset), statistic, critical))
        if accepted:
            rss, coeffs, subset, statistic, critical = min(accepted, key=lambda item: item[0])
            return FitResult(
                tuple(term.name for term in subset),
                coeffs,
                rss,
                statistic,
                critical,
                fits,
                len(accepted),
            )
    return FitResult(None, {}, None, None, None, fits, None, "no accepted subset through k=4")


def stlsq_fit(x: np.ndarray, y: np.ndarray, sigma: float, terms: Sequence[Term]) -> FitResult:
    matrix = design_matrix(x, terms)
    if not is_finite_real(matrix):
        return FitResult(None, {}, None, None, None, 0, None, "nonfinite design matrix")
    col_rms = np.sqrt(np.mean(matrix**2, axis=0))
    if np.any(~np.isfinite(col_rms)) or np.any(col_rms <= 0.0):
        return FitResult(None, {}, None, None, None, 0, None, "nonpositive column rms")
    normalized = matrix / col_rms
    active = np.ones(len(terms), dtype=bool)
    coeffs_norm = np.zeros(len(terms), dtype=float)
    fits = 0
    for _ in range(STLSQ_MAX_ITER):
        fits += 1
        try:
            active_coeffs, *_ = np.linalg.lstsq(normalized[:, active], y, rcond=None)
        except np.linalg.LinAlgError:
            return FitResult(None, {}, None, None, None, fits, None, "least-squares failure")
        next_coeffs = np.zeros(len(terms), dtype=float)
        next_coeffs[active] = active_coeffs
        next_active = np.abs(next_coeffs) >= STLSQ_THRESHOLD
        if not np.any(next_active):
            return FitResult(None, {}, None, None, None, fits, None, "all coefficients thresholded")
        if np.array_equal(next_active, active):
            coeffs_norm = next_coeffs
            break
        active = next_active
        coeffs_norm = next_coeffs
    coeffs_original = coeffs_norm / col_rms
    selected_indices = tuple(int(idx) for idx in np.flatnonzero(np.abs(coeffs_norm) >= STLSQ_THRESHOLD))
    selected_terms = tuple(terms[idx].name for idx in selected_indices)
    coeffs = {terms[idx].name: float(coeffs_original[idx]) for idx in selected_indices}
    residual = y - matrix[:, selected_indices] @ np.asarray([coeffs[name] for name in selected_terms])
    rss = float(np.dot(residual, residual))
    k = len(selected_terms)
    statistic = None if sigma <= 0.0 else rss / (sigma**2)
    critical = chi2_critical(len(y), k)
    return FitResult(selected_terms, coeffs, rss, statistic, critical, fits, None)


def category_for(function_key: str, selected: tuple[str, ...] | None, fail_reason: str | None = None) -> tuple[str, str | None]:
    if selected is None:
        return "FAIL", fail_reason
    true_set = set(TRUE_COEFFICIENTS[function_key])
    selected_set = set(selected)
    if selected_set == true_set:
        return "TRUE_STRUCTURE", None
    if selected_set > true_set:
        return "TRUE_PLUS", None
    return "SURROGATE", None


def coefficient_error(function_key: str, coeffs: dict[str, float], selected: tuple[str, ...] | None) -> float | None:
    true_coeffs = TRUE_COEFFICIENTS[function_key]
    if selected is None or not set(true_coeffs).issubset(set(selected)):
        return None
    expected = np.asarray([true_coeffs[name] for name in true_coeffs], dtype=float)
    actual = np.asarray([coeffs[name] for name in true_coeffs], dtype=float)
    return float(np.linalg.norm(actual - expected) / np.linalg.norm(expected))


def prediction_error(
    function_key: str,
    coeffs: dict[str, float],
    selected: tuple[str, ...] | None,
    x: np.ndarray,
) -> tuple[float | None, str | None]:
    if selected is None:
        return None, "no selected model"
    try:
        matrix = design_matrix(x, [TERM_BY_NAME[name] for name in selected])
    except (ValueError, FloatingPointError, ZeroDivisionError, OverflowError) as exc:
        return None, str(exc)
    if not is_finite_real(matrix):
        return math.nan, "selected term is not finite on evaluation interval"
    coef = np.asarray([coeffs[name] for name in selected], dtype=float)
    true = numeric_values(function_key, x)
    return float(rms(matrix @ coef - true) / rms(true)), None


def build_record(function_key: str, seed: int, method: str, fit: FitResult, x: np.ndarray, y: np.ndarray, sigma: float) -> dict:
    spec = FUNCTIONS[function_key]
    domain = domain_for(spec, DOMAIN_NAME)
    category, reason = category_for(function_key, fit.selected, fit.fail_reason)
    dense_x = np.linspace(domain.a, domain.b, 10000)
    ext_x = np.linspace(domain.b, domain.b + (domain.b - domain.a) / 2.0, 10000)
    grid_error, grid_reason = prediction_error(function_key, fit.coefficients, fit.selected, dense_x)
    extension_error, extension_reason = prediction_error(function_key, fit.coefficients, fit.selected, ext_x)
    train_residual = None if fit.rss is None else float(math.sqrt(fit.rss / len(y)) / rms(y))
    return {
        "function": function_key,
        "seed": int(seed),
        "method": method,
        "category": category,
        "fail_reason": reason,
        "selected_terms": [] if fit.selected is None else list(fit.selected),
        "coefficients": fit.coefficients,
        "k": 0 if fit.selected is None else len(fit.selected),
        "rss": fit.rss,
        "T": fit.statistic,
        "critical": fit.critical,
        "accepted_at_k": fit.accepted_at_k,
        "fits": fit.fits,
        "sigma": float(sigma),
        "coefficient_relative_error": coefficient_error(function_key, fit.coefficients, fit.selected),
        "training_residual_relative": train_residual,
        "grid_error_relative": grid_error,
        "grid_error_reason": grid_reason,
        "extension_error_relative": extension_error,
        "extension_error_reason": extension_reason,
    }


def run_one(function_key: str, seed: int, method: str, *, eta: float = ETA) -> dict:
    settings = diagnostic_settings()
    spec = FUNCTIONS[function_key]
    domain = domain_for(spec, DOMAIN_NAME)
    x, _, values, _ = noisy_sample(function_key, domain, settings.n, eta, seed)
    sigma = sigma_eff(values, eta, settings.sigma_floor_factor)
    terms = admissible_terms(function_key)
    start = time.perf_counter()
    if method == "BS":
        fit = best_subset_fit(x, values, sigma, terms)
    elif method == "STLSQ":
        fit = stlsq_fit(x, values, sigma, terms)
    else:
        raise ValueError(f"unknown method {method!r}")
    record = build_record(function_key, seed, method, fit, x, values, sigma)
    record["wall_clock_seconds"] = time.perf_counter() - start
    return record


def iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if line.strip():
            yield json.loads(line)


def completed_keys(path: Path) -> set[tuple[str, int, str]]:
    return {(record["function"], int(record["seed"]), record["method"]) for record in iter_jsonl(path)}


def append_record(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def log_progress(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"{record['function']} seed={record['seed']} method={record['method']} "
        f"fits={record['fits']} seconds={record['wall_clock_seconds']:.3f}"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def parse_seeds(value: str) -> list[int]:
    if "-" in value:
        left, right = value.split("-", 1)
        start = int(left)
        end = int(right)
        if end < start:
            raise SystemExit("--seeds range end must be >= start")
        return list(range(start, end + 1))
    return [int(item) for item in value.split(",") if item]


def parse_functions(values: Sequence[str] | None) -> list[str]:
    if not values:
        return list(FUNCTION_KEYS)
    out: list[str] = []
    for value in values:
        out.extend(item for item in value.split(",") if item)
    unknown = sorted(set(out) - set(FUNCTION_KEYS))
    if unknown:
        raise SystemExit(f"unknown functions: {', '.join(unknown)}")
    return out


def run_records(seeds: Sequence[int], functions: Sequence[str], outdir: Path = OUTDIR) -> None:
    paths = output_paths(outdir)
    done = completed_keys(paths["records"])
    for seed in seeds:
        for function_key in functions:
            for method in ("BS", "STLSQ"):
                key = (function_key, int(seed), method)
                if key in done:
                    continue
                record = run_one(function_key, int(seed), method)
                append_record(record, paths["records"])
                log_progress(record, paths["log"])
                done.add(key)


def run_exact(outdir: Path = OUTDIR) -> dict:
    paths = output_paths(outdir)
    paths["outdir"].mkdir(parents=True, exist_ok=True)
    records = [run_one(function_key, 0, "BS", eta=0.0) for function_key in FUNCTION_KEYS]
    payload = {
        "tau": tau_from_diagnostic_settings(),
        "records": records,
        "all_true_structure": all(record["category"] == "TRUE_STRUCTURE" for record in records),
    }
    paths["exact"].write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def count_categories(records: list[dict]) -> dict[str, int]:
    counts = Counter(record["category"] for record in records)
    return {key: counts[key] for key in ("TRUE_STRUCTURE", "TRUE_PLUS", "SURROGATE", "FAIL")}


def rate(records: list[dict], category: str) -> float | None:
    if not records:
        return None
    return sum(record["category"] == category for record in records) / len(records)


def baseline_false_unique(records: list[dict]) -> float | None:
    denom = sum(record["category"] in {"TRUE_STRUCTURE", "TRUE_PLUS", "SURROGATE"} for record in records)
    if denom == 0:
        return None
    return sum(record["category"] == "SURROGATE" for record in records) / denom


def annihilator_state_summary(records: list[dict]) -> dict:
    counts = Counter(record["state"] for record in records)
    denom = counts["CORRECT"] + counts["TRUE_NOT_REF"] + counts["WRONG"]
    return {
        "total": len(records),
        "states": {state: counts[state] for state in ("NONE", "AMBIGUOUS", "CORRECT", "TRUE_NOT_REF", "WRONG")},
        "wrong_given_unambiguous": None if denom == 0 else counts["WRONG"] / denom,
        "wrong_over_unambiguous": f"{counts['WRONG']}/{denom}",
    }


def load_annihilator_records(path: Path = ANNIHILATOR_RECORDS) -> list[dict]:
    return list(iter_jsonl(path))


def records_for_group(records: list[dict], group: str) -> list[dict]:
    return [record for record in records if record["function"] in COMPARISON_GROUPS[group]]


def baseline_false_unique_by_group_and_method(records: list[dict]) -> dict[str, dict[str, float | None]]:
    return {
        group: {
            method: baseline_false_unique(
                [
                    record
                    for record in records_for_group(records, group)
                    if record["method"] == method
                ]
            )
            for method in ("BS", "STLSQ")
        }
        for group in COMPARISON_GROUPS
    }


def annihilator_summary_by_scope(annihilator_records: list[dict], *, paired: bool) -> dict[str, dict]:
    def in_scope(record: dict) -> bool:
        return not paired or SEED_BASE <= int(record["seed"]) <= SEED_END

    return {
        group: annihilator_state_summary([record for record in records_for_group(annihilator_records, group) if in_scope(record)])
        for group in COMPARISON_GROUPS
    }


def summarize_records(records: list[dict], annihilator_records: list[dict]) -> dict:
    bs = [record for record in records if record["method"] == "BS"]
    stlsq = [record for record in records if record["method"] == "STLSQ"]
    primary = [record for record in bs if record["function"] in PRIMARY_FUNCTIONS]
    controls = [record for record in bs if record["function"] in CONTROL_FUNCTIONS]
    required_primary = {(function_key, seed) for function_key in PRIMARY_FUNCTIONS for seed in range(SEED_BASE, SEED_END + 1)}
    actual_primary = {(record["function"], int(record["seed"])) for record in primary}
    if actual_primary != required_primary:
        missing = sorted(required_primary - actual_primary)
        extra = sorted(actual_primary - required_primary)
        raise SystemExit(f"primary BS records must be exactly F4/F5/F8 seeds 50000-50019; missing={missing} extra={extra}")
    p_control_true = rate(controls, "TRUE_STRUCTURE")
    p_true = rate(primary, "TRUE_STRUCTURE")
    p_surr = rate(primary, "SURROGATE")
    if p_control_true is None or p_control_true < 0.70:
        verdict = "INVALID"
    elif p_true is not None and p_true >= 0.70 and p_surr is not None and p_surr <= 0.20:
        verdict = "STRONG_NEGATIVE"
    else:
        verdict = "OPEN"
    by_function = {}
    for function_key in FUNCTION_KEYS:
        subset = [record for record in records if record["function"] == function_key]
        by_function[function_key] = {
            "BS": count_categories([record for record in subset if record["method"] == "BS"]),
            "STLSQ": count_categories([record for record in subset if record["method"] == "STLSQ"]),
        }
    return {
        "records": len(records),
        "primary_count": len(primary),
        "control_count": len(controls),
        "p_control_true": p_control_true,
        "p_true": p_true,
        "p_surr": p_surr,
        "verdict": verdict,
        "baseline_false_unique": baseline_false_unique_by_group_and_method(records),
        "by_function": by_function,
        "annihilator": {
            "paired": annihilator_summary_by_scope(annihilator_records, paired=True),
            "reference": annihilator_summary_by_scope(annihilator_records, paired=False),
        },
        "secondary_functions": {function_key: by_function[function_key] for function_key in SECONDARY_FUNCTIONS},
    }


def write_summary(summary: dict, outdir: Path = OUTDIR) -> None:
    paths = output_paths(outdir)
    paths["outdir"].mkdir(parents=True, exist_ok=True)
    paths["summary_json"].write_text(json.dumps(summary, indent=2, sort_keys=True))
    lines = [
        "# Direct Regression Reality Check",
        "",
        f"- records: {summary['records']}",
        f"- verdict: {summary['verdict']}",
        f"- primary_count: {summary['primary_count']}",
        f"- control_count: {summary['control_count']}",
        f"- P_true_primary_BS: {summary['p_true']}",
        f"- P_surr_primary_BS: {summary['p_surr']}",
        f"- P_true_control_BS: {summary['p_control_true']}",
        "",
        "## Annihilator Comparison",
        "",
        "| Group | Annihilator paired | Annihilator reference | BS | STLSQ |",
        "|---|---:|---:|---:|---:|",
    ]
    for group in COMPARISON_GROUPS:
        paired = summary["annihilator"]["paired"][group]["wrong_over_unambiguous"]
        reference = summary["annihilator"]["reference"][group]["wrong_over_unambiguous"]
        bs_rate = summary["baseline_false_unique"][group]["BS"]
        stlsq_rate = summary["baseline_false_unique"][group]["STLSQ"]
        bs_text = "-" if bs_rate is None else f"{bs_rate:.6g}"
        stlsq_text = "-" if stlsq_rate is None else f"{stlsq_rate:.6g}"
        lines.append(f"| {group} | {paired} | {reference} | {bs_text} | {stlsq_text} |")
    lines.extend(
        [
        "",
        "## By Function",
        "",
        "| Function | Method | TRUE_STRUCTURE | TRUE_PLUS | SURROGATE | FAIL |",
        "|---|---|---:|---:|---:|---:|",
        ]
    )
    for function_key, methods in summary["by_function"].items():
        for method, counts in methods.items():
            lines.append(
                f"| {function_key} | {method} | {counts['TRUE_STRUCTURE']} | {counts['TRUE_PLUS']} | "
                f"{counts['SURROGATE']} | {counts['FAIL']} |"
            )
    paths["summary_md"].write_text("\n".join(lines) + "\n")


def summarize(outdir: Path = OUTDIR, annihilator_path: Path = ANNIHILATOR_RECORDS) -> dict:
    records = list(iter_jsonl(output_paths(outdir)["records"]))
    summary = summarize_records(records, load_annihilator_records(annihilator_path))
    write_summary(summary, outdir)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--seeds", type=str, default=None)
    parser.add_argument("--functions", nargs="*", default=None)
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    args = parser.parse_args()
    if args.exact:
        run_exact(args.outdir)
        return
    if args.summarize:
        summarize(args.outdir)
        return
    if args.seeds is None:
        raise SystemExit("use --exact, --seeds, or --summarize")
    run_records(parse_seeds(args.seeds), parse_functions(args.functions), args.outdir)


if __name__ == "__main__":
    main()
