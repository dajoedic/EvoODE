"""Acceptance 2: weak validation rows versus strong-form integrals."""

from __future__ import annotations

import numpy as np
import sympy as sp

from experiments.annihilator_gate2a.acceptance.common import Timer, parser, write_result
from experiments.annihilator_gate2a.config import FUNCTIONS, Settings, class_columns, domain_for
from experiments.annihilator_gate2a.functions import grid, numeric_values, symbolic_z
from experiments.annihilator_gate2a.operator_search import normalize_coeffs
from experiments.annihilator_gate2a.oracle import reference_for
from experiments.annihilator_gate2a.weak_operator import _block_poly_u, matrix_from_tensor, rows, trap_weights, weight_tensor


def _strong_validation_rows(function_key: str, domain_name: str, z_grid: np.ndarray, coeffs: np.ndarray, r: int, d: int, settings: Settings) -> np.ndarray:
    domain = domain_for(FUNCTIONS[function_key], domain_name)
    z, expr = symbolic_z(function_key, domain)
    derivative_values = [sp.lambdify(z, sp.diff(expr, z, k), "numpy")(z_grid) for k in range(r + 1)]
    operator_values = np.zeros_like(z_grid, dtype=float)
    for coeff, (k, j) in zip(coeffs, class_columns(r, d)):
        operator_values += coeff * (z_grid**j) * np.asarray(derivative_values[k], dtype=float)
    weights = trap_weights(z_grid)
    out = []
    for block, mode in rows("val", settings):
        poly_u, center, halfwidth = _block_poly_u(block, mode, 0, settings)
        u = (z_grid - center) / halfwidth
        support = np.abs(u) <= 1.0 + 1e-14
        phi = poly_u(u)
        phi[~support] = 0.0
        out.append(float(np.sum(weights * phi * operator_values)))
    return np.asarray(out, dtype=float)


def _operator_record(function_key: str, coeffs: np.ndarray, r: int, d: int, settings: Settings) -> dict:
    domain = domain_for(FUNCTIONS[function_key], "wide")
    x, z = grid(domain, settings.n)
    values = numeric_values(function_key, x)
    k_val = weight_tensor(z, r, d, "val", settings)
    a_val = matrix_from_tensor(k_val, values)
    weak = a_val @ coeffs
    strong = _strong_validation_rows(function_key, "wide", z, coeffs, r, d, settings)
    diff_norm = float(np.linalg.norm(weak - strong))
    strong_norm = float(np.linalg.norm(strong))
    weak_relative = float(np.linalg.norm(weak) / max(np.linalg.norm(a_val) * np.linalg.norm(coeffs), 1e-300))
    strong_relative_error = diff_norm / max(strong_norm, 1e-300)
    return {
        "weak_norm": float(np.linalg.norm(weak)),
        "strong_norm": strong_norm,
        "difference_norm": diff_norm,
        "strong_relative_error": strong_relative_error,
        "weak_annihilation_relative": weak_relative,
    }


def main() -> None:
    args = parser().parse_args()
    n = 20_000 if args.limit else 200_000
    settings = Settings(n=n, boot_reps=1)
    functions = ("F2",) if args.limit else ("F2", "F4", "F9")
    records = {}
    with Timer() as timer:
        for key in functions:
            (r, d), oracle_coeffs = reference_for(key, "wide")
            rng = np.random.default_rng(0)
            random_coeffs = normalize_coeffs(rng.standard_normal(oracle_coeffs.size))
            oracle_record = _operator_record(key, oracle_coeffs, r, d, settings)
            random_record = _operator_record(key, random_coeffs, r, d, settings)
            oracle_record["passed"] = oracle_record["weak_annihilation_relative"] < 1e-8
            random_record["passed"] = random_record["strong_relative_error"] < 1e-6
            records[key] = {
                "class": [r, d],
                "oracle": oracle_record,
                "random_seed_0": random_record,
                "passed": oracle_record["passed"] and random_record["passed"],
            }
    write_result(
        "accept_02_weak_strong",
        {
            "limit": args.limit,
            "n": n,
            "records": records,
            "passed": all(record["passed"] for record in records.values()),
            "runtime_seconds": timer.seconds,
        },
    )


if __name__ == "__main__":
    main()
