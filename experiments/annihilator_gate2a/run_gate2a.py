"""CLI for Gate 2A runs."""

from __future__ import annotations

import argparse
import csv
import os
import time
from multiprocessing import Pool
from pathlib import Path

from .config import FUNCTIONS, RESULTS, Settings, domain_for, settings_for_variant
from .functions import noisy_sample, sigma_eff
from .operator_search import full_search, test_operator
from .oracle import build_reference, n_exact, reference_for
from .transfer import angle, transfer_coeffs_and_cov
from .weak_operator import WeightContext


RUN_FIELDS = [
    "variant", "function", "domain", "eta", "seed", "selected_r", "selected_d", "C", "T", "dof",
    "critical", "sigma_min", "sigma_second_min", "A1", "bootstrap_share", "state",
    "coeff_angle", "transfer_passed", "tested_classes", "N", "B", "M", "q", "alpha",
    "sigma_floor_factor", "B_boot", "bootstrap_threshold", "git_hash", "runtime_seconds",
]


def git_hash() -> str:
    return os.environ.get("GIT_COMMIT", "unavailable")


def state_for(function_key: str, domain_name: str, selected: tuple[int, int] | None, ambiguous: bool) -> str:
    if selected is None:
        return "NONE"
    if ambiguous:
        return "AMBIGUOUS"
    ref_class, _ = reference_for(function_key, domain_name)
    if selected == ref_class:
        return "CORRECT"
    return "TRUE_NOT_REF" if n_exact(function_key, domain_name, *selected) > 0 else "WRONG"


def one_run(args: tuple[str, str, float, int, str]) -> dict:
    function_key, domain_name, eta, seed, variant = args
    settings = settings_for_variant(variant)
    spec = FUNCTIONS[function_key]
    domain = domain_for(spec, domain_name)
    start = time.perf_counter()
    _, z, values, _ = noisy_sample(function_key, domain, settings.n, eta, seed)
    selection = full_search(z, values, eta, seed, settings, with_bootstrap=True)
    ambiguous = selection.a1 or (selection.bootstrap_share is not None and selection.bootstrap_share < settings.boot_threshold)
    state = state_for(function_key, domain_name, selection.selected_class, ambiguous)
    coeff_angle = ""
    if selection.selected_class is not None and state == "CORRECT":
        _, ref = reference_for(function_key, domain_name)
        coeff_angle = angle(selection.coeffs, ref)
    transfer_passed = ""
    if domain_name == "narrow" and selection.selected_class is not None and selection.coeffs is not None and selection.coeff_cov is not None:
        selected_r, selected_d = selection.selected_class
        moved, moved_cov = transfer_coeffs_and_cov(selection.coeffs, selection.coeff_cov, selected_r, selected_d, spec.narrow, spec.wide)
        _, z_wide, values_wide, _ = noisy_sample(function_key, spec.wide, settings.n, eta, seed + 1000)
        wide_context = WeightContext(z_wide, values_wide, settings)
        _, k_val_wide, _, a_val_wide = wide_context.split(selected_r, selected_d)
        sigma_wide = sigma_eff(values_wide, eta, settings.sigma_floor_factor)
        transfer_test = test_operator(
            a_val_wide,
            k_val_wide,
            moved,
            coeff_cov=moved_cov,
            sigma=sigma_wide,
            settings=settings,
        )
        transfer_passed = transfer_test.passed
    selected_r = selected_d = c_complexity = ""
    if selection.selected_class:
        selected_r, selected_d = selection.selected_class
        c_complexity = (selected_r + 1) * (selected_d + 1)
    return {
        "variant": variant,
        "function": function_key,
        "domain": domain_name,
        "eta": eta,
        "seed": seed,
        "selected_r": selected_r,
        "selected_d": selected_d,
        "C": c_complexity,
        "T": "" if selection.statistic is None else selection.statistic,
        "dof": "" if selection.dof is None else selection.dof,
        "critical": "" if selection.critical is None else selection.critical,
        "sigma_min": "" if selection.singular_values[0] is None else selection.singular_values[0],
        "sigma_second_min": "" if selection.singular_values[1] is None else selection.singular_values[1],
        "A1": selection.a1,
        "bootstrap_share": "" if selection.bootstrap_share is None else selection.bootstrap_share,
        "state": state,
        "coeff_angle": coeff_angle,
        "transfer_passed": transfer_passed,
        "tested_classes": selection.tested_classes,
        "N": settings.n,
        "B": settings.blocks,
        "M": settings.modes,
        "q": settings.q,
        "alpha": settings.alpha,
        "sigma_floor_factor": settings.sigma_floor_factor,
        "B_boot": settings.boot_reps,
        "bootstrap_threshold": settings.boot_threshold,
        "git_hash": git_hash(),
        "runtime_seconds": time.perf_counter() - start,
    }


def run_tasks(tasks: list[tuple[str, str, float, int, str]], workers: int) -> list[dict]:
    if workers == 1:
        return [one_run(t) for t in tasks]
    with Pool(workers) as pool:
        return pool.map(one_run, tasks)


def tasks_from_args(args: argparse.Namespace) -> list[tuple[str, str, float, int, str]]:
    if args.smoke:
        return [("F2", "wide", 0.0, 0, args.variant), ("F2", "wide", 0.01, 0, args.variant), ("F2", "wide", 0.01, 1, args.variant), ("F10", "wide", 0.0, 0, args.variant)]
    functions = args.function or list(FUNCTIONS)
    domains = args.domain or ["wide", "narrow"]
    etas = args.eta if args.eta is not None else list(settings_for_variant(args.variant).noise_levels)
    tasks = []
    for f in functions:
        for d in domains:
            for eta in etas:
                seeds = [0] if eta == 0 else (args.seed if args.seed is not None else list(settings_for_variant(args.variant).noisy_seeds))
                for seed in seeds:
                    tasks.append((f, d, eta, seed, args.variant))
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="standard")
    parser.add_argument("--function", action="append", choices=list(FUNCTIONS))
    parser.add_argument("--domain", action="append", choices=["wide", "narrow"])
    parser.add_argument("--eta", action="append", type=float)
    parser.add_argument("--seed", action="append", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if not args.smoke and git_hash() == "unavailable":
        raise SystemExit("GIT_COMMIT must be set for non-smoke Gate 2A runs")
    build_reference(force=not (RESULTS / "oracle_reference.json").exists())
    tasks = tasks_from_args(args)
    outdir = RESULTS / args.variant
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / "runs.csv"
    rows = run_tasks(tasks, args.workers)
    with outfile.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {outfile}")


if __name__ == "__main__":
    main()
