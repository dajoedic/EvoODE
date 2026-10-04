"""Acceptance 3: covariance Monte Carlo for estimated reference-class coefficients."""

from __future__ import annotations

import numpy as np

from experiments.annihilator_gate2a.acceptance.common import Timer, parser, write_result
from experiments.annihilator_gate2a.config import FUNCTIONS, Settings, domain_for
from experiments.annihilator_gate2a.functions import grid, noisy_sample, numeric_values, sigma_eff
from experiments.annihilator_gate2a.operator_search import evaluate_class, test_operator
from experiments.annihilator_gate2a.oracle import reference_for
from experiments.annihilator_gate2a.weak_operator import WeightContext


def _summarize_tests(t_over_dof: list[float], rejected: int, reps: int) -> dict:
    return {
        "rejection_rate": rejected / reps,
        "mean_T_over_dof": float(np.nanmean(t_over_dof)),
    }


def _run_function(function_key: str, reps: int, settings: Settings) -> dict:
    spec = FUNCTIONS[function_key]
    domain = domain_for(spec, "wide")
    (r, d), reference_coeffs = reference_for(function_key, "wide")
    x, z = grid(domain, settings.n)
    base_context = WeightContext(z, numeric_values(function_key, x), settings)
    coeffs = []
    analytic_traces = []
    full_rejected = 0
    no_coeff_cov_rejected = 0
    full_t_over_dof = []
    no_coeff_cov_t_over_dof = []

    for seed in range(reps):
        _, _, values, _ = noisy_sample(function_key, domain, settings.n, 0.01, seed)
        sigma = sigma_eff(values, 0.01, settings.sigma_floor_factor)
        context = base_context.with_values(values)
        k_fit, k_val, a_fit, a_val = context.split(r, d)
        evaluation = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, settings, -1)
        coeff = evaluation.coeffs
        if float(np.dot(coeff, reference_coeffs)) < 0.0:
            coeff = -coeff
        coeffs.append(coeff)
        analytic_traces.append(float(np.trace(evaluation.coeff_cov)))
        full_rejected += int(not evaluation.test.passed)
        full_t_over_dof.append(evaluation.test.statistic / evaluation.test.dof if evaluation.test.dof else np.nan)

        no_cov = np.zeros_like(evaluation.coeff_cov)
        no_cov_test = test_operator(a_val, k_val, evaluation.coeffs, no_cov, sigma, settings)
        no_coeff_cov_rejected += int(not no_cov_test.passed)
        no_coeff_cov_t_over_dof.append(no_cov_test.statistic / no_cov_test.dof if no_cov_test.dof else np.nan)

    coeff_matrix = np.vstack(coeffs)
    empirical_cov = np.cov(coeff_matrix, rowvar=False, ddof=1)
    empirical_trace = float(np.trace(empirical_cov))
    analytic_trace_mean = float(np.mean(analytic_traces))
    trace_ratio = empirical_trace / analytic_trace_mean if analytic_trace_mean > 0.0 else float("nan")
    full = _summarize_tests(full_t_over_dof, full_rejected, reps)
    full["trace_ratio"] = trace_ratio
    full["passed"] = (
        0.0 <= full["rejection_rate"] <= 0.03
        and 0.85 <= full["mean_T_over_dof"] <= 1.15
        and 0.8 <= trace_ratio <= 1.25
    )
    without = _summarize_tests(no_coeff_cov_t_over_dof, no_coeff_cov_rejected, reps)
    without["trace_ratio"] = trace_ratio
    return {
        "class": [r, d],
        "reps": reps,
        "with_coeff_cov": full,
        "without_coeff_cov_in_test": without,
        "empirical_trace": empirical_trace,
        "mean_analytic_trace": analytic_trace_mean,
    }


def main() -> None:
    arg_parser = parser()
    arg_parser.add_argument("--part", choices=["F2", "F4", "F9"], help="Run only one full Monte Carlo part.")
    args = arg_parser.parse_args()
    reps = 20 if args.limit else 1000
    settings = Settings(boot_reps=1)
    functions = (args.part,) if args.part else (("F2",) if args.limit else ("F2", "F4", "F9"))
    records = {}
    with Timer() as timer:
        for key in functions:
            records[key] = _run_function(key, reps, settings)
    write_result(
        "accept_03_covariance_mc",
        {
            "limit": args.limit,
            "part": args.part,
            "records": records,
            "passed": all(record["with_coeff_cov"]["passed"] for record in records.values()),
            "runtime_seconds": timer.seconds,
        },
    )


if __name__ == "__main__":
    main()
