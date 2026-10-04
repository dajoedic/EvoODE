"""Acceptance 1: cached oracle classes and exact reference verification."""

from __future__ import annotations

import mpmath as mp
import numpy as np
import sympy as sp

from experiments.annihilator_gate2a.acceptance.common import Timer, parser, write_result
from experiments.annihilator_gate2a.config import CLASSES, F10_REL_TOL, FUNCTIONS, ORACLE_DIGITS, ORACLE_REL_TOL, class_columns
from experiments.annihilator_gate2a.functions import symbolic_x
from experiments.annihilator_gate2a.oracle import ORACLE_METADATA, _mp_collocation_matrix, _mp_derivatives, build_reference


def _class_key(r: int, d: int) -> str:
    return f"{r},{d}"


def _rationalized_coeffs(coeffs: list[float]) -> list[sp.Expr]:
    values = np.asarray(coeffs, dtype=float)
    pivot = float(np.max(np.abs(values)))
    if pivot <= 0.0:
        raise ValueError("zero coefficient vector cannot be rationalized")
    out = []
    for value in values:
        ratio = float(value / pivot)
        if abs(ratio) < 1e-40:
            out.append(sp.Integer(0))
        else:
            out.append(sp.nsimplify(ratio, tolerance=1e-8, rational=True))
    return out


def _symbolic_residual_exact(function_key: str, domain_name: str, r: int, d: int, coeffs: list[float]) -> tuple[bool, str]:
    domain = getattr(FUNCTIONS[function_key], domain_name)
    z = sp.Symbol("z")
    x, expr_x = symbolic_x(function_key)
    mu = sp.nsimplify(domain.mu, tolerance=1e-12, rational=True)
    scale = sp.nsimplify(domain.scale, tolerance=1e-12, rational=True)
    expr = expr_x.subs(x, mu + scale * z)
    try:
        rational = _rationalized_coeffs(coeffs)
        residual = sp.simplify(sum(c * z**j * sp.diff(expr, z, k) for c, (k, j) in zip(rational, class_columns(r, d))))
        return residual == 0, str(residual)
    except Exception as exc:  # pragma: no cover - exercised by malformed cache data.
        return False, f"rationalization_failed: {exc}"


def _f10_coeffs(function_key: str, domain_name: str, r: int, d: int) -> list[mp.mpf]:
    mp.mp.dps = ORACLE_DIGITS
    mat = _mp_collocation_matrix(function_key, domain_name, r, d)
    _, singular_values, vh = mp.svd_r(mat, full_matrices=False)
    threshold = mp.mpf(str(ORACLE_REL_TOL)) * max(mp.mpf(value) for value in singular_values)
    if sum(mp.mpf(value) < threshold for value in singular_values) != 1:
        raise RuntimeError(f"F10 reference class is not one-dimensional for {domain_name}")
    row = [mp.mpf(vh[mat.cols - 1, i]) for i in range(mat.cols)]
    norm = mp.sqrt(mp.fsum(value * value for value in row))
    coeffs = [value / norm for value in row]
    max_i = max(range(len(coeffs)), key=lambda i: abs(coeffs[i]))
    if coeffs[max_i] < 0:
        coeffs = [-value for value in coeffs]
    return coeffs


def _f10_residual_check(domain_name: str, r: int, d: int) -> dict:
    coeffs = _f10_coeffs("F10", domain_name, r, d)
    derivs = _mp_derivatives("F10", domain_name)
    max_rel = mp.mpf("0")
    worst_z = None
    for i in range(200):
        z = mp.mpf("-1") + mp.mpf("2") * i / mp.mpf(199)
        terms = [coeff * (z**j) * derivs[k](z) for coeff, (k, j) in zip(coeffs, class_columns(r, d))]
        denom = max(abs(term) for term in terms)
        rel = abs(mp.fsum(terms)) / denom if denom != 0 else abs(mp.fsum(terms))
        if rel > max_rel:
            max_rel = rel
            worst_z = z
    return {
        "max_relative_residual": mp.nstr(max_rel, 20),
        "threshold": F10_REL_TOL,
        "worst_z": None if worst_z is None else mp.nstr(worst_z, 20),
        "coeffs_30_digits": [mp.nstr(coeff, 32) for coeff in coeffs],
        "passed": bool(max_rel < mp.mpf(str(F10_REL_TOL))),
    }


def main() -> None:
    args = parser().parse_args()
    with Timer() as timer:
        data = build_reference(force=False)
        keys = list(FUNCTIONS)[:3] if args.limit else list(FUNCTIONS)

        reference_records = {}
        symbolic_records = {}
        f10_records = {}
        n_exact_differences = {}
        f10_presence_differences = {}

        for key in keys:
            reference_records[key] = {}
            wide_classes = data["functions"][key]["wide"]["classes"]
            narrow_classes = data["functions"][key]["narrow"]["classes"]
            diffs = []
            presence_diffs = []
            for r, d in CLASSES:
                class_key = _class_key(r, d)
                wide_n = int(wide_classes[class_key]["n_exact"])
                narrow_n = int(narrow_classes[class_key]["n_exact"])
                if wide_n != narrow_n:
                    diffs.append({"class": [r, d], "wide": wide_n, "narrow": narrow_n})
                if (wide_n > 0) != (narrow_n > 0):
                    presence_diffs.append({"class": [r, d], "wide": wide_n, "narrow": narrow_n})
            n_exact_differences[key] = diffs
            if key == "F10":
                f10_presence_differences[key] = presence_diffs

            for domain in ("wide", "narrow"):
                record = data["functions"][key][domain]
                r, d = record["reference_class"]
                ref_class_ok = tuple(record["reference_class"]) == FUNCTIONS[key].reference_class
                ref_dim = int(record["classes"][_class_key(r, d)]["n_exact"])
                reference_records[key][domain] = {
                    "reference_class": record["reference_class"],
                    "expected_reference_class": list(FUNCTIONS[key].reference_class),
                    "reference_class_ok": ref_class_ok,
                    "reference_n_exact": ref_dim,
                    "reference_n_exact_one": ref_dim == 1,
                }
                if key == "F10":
                    f10_records[domain] = _f10_residual_check(domain, r, d)
                else:
                    ok, residual = _symbolic_residual_exact(key, domain, r, d, record["reference_coeffs"])
                    symbolic_records.setdefault(key, {})[domain] = {"passed": ok, "residual": residual}

    table_passed = all(not diffs for diffs in n_exact_differences.values())
    f10_presence_passed = all(not diffs for diffs in f10_presence_differences.values())
    reference_passed = all(record["reference_class_ok"] and record["reference_n_exact_one"] for per_fn in reference_records.values() for record in per_fn.values())
    symbolic_passed = all(record["passed"] for per_fn in symbolic_records.values() for record in per_fn.values())
    f10_passed = all(record["passed"] for record in f10_records.values())
    metadata_ok = data.get("metadata") == ORACLE_METADATA
    write_result(
        "accept_01_oracle",
        {
            "limit": args.limit,
            "metadata": data.get("metadata"),
            "expected_metadata": ORACLE_METADATA,
            "metadata_ok": metadata_ok,
            "reference_records": reference_records,
            "n_exact_table_differences": n_exact_differences,
            "n_exact_table_passed": table_passed,
            "f10_presence_differences": f10_presence_differences,
            "symbolic_verification": symbolic_records,
            "symbolic_verification_passed": symbolic_passed,
            "f10_high_precision": f10_records,
            "f10_high_precision_passed": f10_passed,
            "passed": metadata_ok and reference_passed and table_passed and f10_presence_passed and symbolic_passed and f10_passed,
            "runtime_seconds": timer.seconds,
        },
    )


if __name__ == "__main__":
    main()
