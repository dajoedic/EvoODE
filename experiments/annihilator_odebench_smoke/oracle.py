"""Generalized high-precision oracle copied from Gate 2A v3."""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp
import numpy as np
import sympy as sp

from experiments.annihilator_gate2a_v3.config import CLASSES, class_columns

from .catalog import Domain, ODESystem, load_systems, training_domain
from .config import ORACLE_DIGITS, ORACLE_POINTS, ORACLE_REL_TOL


@dataclass(frozen=True)
class OracleResult:
    reference_class: tuple[int, int]
    reference_coeffs: list[float]
    reference_n_exact: int
    classes: dict[str, dict]
    verification: dict
    tested_classes_to_reference: int


def symbolic_z_expr(expr_x: sp.Expr, domain: Domain) -> tuple[sp.Symbol, sp.Expr]:
    x = sp.Symbol("x")
    z = sp.Symbol("z")
    mu = sp.nsimplify(domain.mu, rational=True)
    scale = sp.nsimplify(domain.scale, rational=True)
    return z, sp.simplify(expr_x.subs(x, mu + scale * z))


def _mp_derivatives(expr_x: sp.Expr, domain: Domain, max_order: int):
    z, expr_z = symbolic_z_expr(expr_x, domain)
    modules = [{"log": mp.log, "exp": mp.exp, "sin": mp.sin, "cos": mp.cos}, "mpmath"]
    return tuple(sp.lambdify(z, sp.diff(expr_z, z, order), modules) for order in range(max_order + 1))


def _mp_sample() -> tuple[mp.mpf, ...]:
    return tuple(mp.mpf("-0.97") + mp.mpf("1.94") * i / (ORACLE_POINTS - 1) for i in range(ORACLE_POINTS))


def collocation_matrix(expr_x: sp.Expr, domain: Domain, r: int, d: int) -> mp.matrix:
    derivs = _mp_derivatives(expr_x, domain, max(rr for rr, _ in CLASSES))
    sample = _mp_sample()
    mat = mp.matrix(ORACLE_POINTS, (r + 1) * (d + 1))
    for col, (k, j) in enumerate(class_columns(r, d)):
        derivative = derivs[k]
        for row, zi in enumerate(sample):
            mat[row, col] = (zi**j) * derivative(zi)
    return mat


def nullspace(expr_x: sp.Expr, domain: Domain, r: int, d: int) -> tuple[int, list[float] | None]:
    mp.mp.dps = ORACLE_DIGITS
    mat = collocation_matrix(expr_x, domain, r, d)
    _, singular_values, vh = mp.svd_r(mat, full_matrices=False)
    values = [mp.mpf(value) for value in singular_values]
    threshold = mp.mpf(str(ORACLE_REL_TOL)) * max(values)
    n_exact = int(sum(value < threshold for value in values))
    coeffs = None
    if n_exact > 0:
        row = vh[mat.cols - 1, :]
        vec = np.array([float(row[i]) for i in range(mat.cols)], dtype=float)
        vec /= np.linalg.norm(vec)
        pivot = int(np.argmax(np.abs(vec)))
        if vec[pivot] < 0:
            vec *= -1.0
        coeffs = vec.tolist()
    return n_exact, coeffs


def symbolic_residual(expr_x: sp.Expr, domain: Domain, r: int, d: int, coeffs: np.ndarray) -> sp.Expr:
    z, expr_z = symbolic_z_expr(expr_x, domain)
    coeffs = np.asarray(coeffs, dtype=float)
    pivot = coeffs[int(np.argmax(np.abs(coeffs)))]
    if pivot == 0:
        raise ValueError("zero reference coefficient pivot")
    total = 0
    for c, (k, j) in zip(coeffs, class_columns(r, d)):
        ratio = float(c / pivot)
        coeff = sp.Integer(0) if abs(ratio) < 1e-12 else sp.nsimplify(ratio, tolerance=1e-9, rational=True)
        total += coeff * z**j * sp.diff(expr_z, z, k)
    return sp.simplify(total)


def verify_reference(expr_x: sp.Expr, domain: Domain, r: int, d: int, coeffs: list[float]) -> dict:
    residual = symbolic_residual(expr_x, domain, r, d, np.asarray(coeffs, dtype=float))
    exact = sp.simplify(residual)
    if exact == 0:
        return {"mode": "symbolic_nsimplify", "symbolic_zero": True, "passed": True}
    values = [float(abs(sp.N(residual.subs({"z": z}), 80))) for z in np.linspace(-0.9, 0.9, 19)]
    max_abs = max(values)
    return {"mode": "symbolic_nsimplify", "symbolic_zero": False, "max_abs_on_sample": max_abs, "passed": max_abs < 1e-12}


def oracle_for_expr(expr_x: sp.Expr, domain: Domain) -> OracleResult:
    classes: dict[str, dict] = {}
    reference_class = None
    reference_coeffs = None
    tested = 0
    for r, d in CLASSES:
        tested += 1
        n_exact, coeffs = nullspace(expr_x, domain, r, d)
        classes[f"{r},{d}"] = {"n_exact": n_exact}
        if coeffs is not None:
            classes[f"{r},{d}"]["coeffs"] = coeffs
        if reference_class is None and n_exact > 0:
            reference_class = (r, d)
            reference_coeffs = coeffs
            break
    if reference_class is None or reference_coeffs is None:
        raise RuntimeError("oracle found no reference class")
    verification = verify_reference(expr_x, domain, *reference_class, reference_coeffs)
    return OracleResult(reference_class, reference_coeffs, classes[f"{reference_class[0]},{reference_class[1]}"]["n_exact"], classes, verification, tested)


def build_reference() -> dict:
    systems = load_systems()
    out = {
        "metadata": {
            "method": "generalized_sympy_derivatives_mpmath_svd_gate2a_v3_copy",
            "precision_digits": ORACLE_DIGITS,
            "points": ORACLE_POINTS,
            "relative_threshold": ORACLE_REL_TOL,
        },
        "classes": [list(cls) for cls in CLASSES],
        "systems": {},
    }
    for sid, system in systems.items():
        domain = training_domain(system)
        result = oracle_for_expr(system.sympy_expr, domain)
        out["systems"][str(sid)] = {
            "reference_class": list(result.reference_class),
            "reference_coeffs": result.reference_coeffs,
            "reference_n_exact": result.reference_n_exact,
            "verification": result.verification,
            "classes": result.classes,
            "tested_classes_to_reference": result.tested_classes_to_reference,
        }
    return out


def reference_for_system(system: ODESystem, reference: dict | None = None) -> tuple[tuple[int, int], np.ndarray, int]:
    reference = reference or build_reference()
    row = reference["systems"][str(system.system_id)]
    return tuple(row["reference_class"]), np.asarray(row["reference_coeffs"], dtype=float), int(row["reference_n_exact"])
