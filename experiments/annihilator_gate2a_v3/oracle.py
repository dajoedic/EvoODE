"""High-precision oracle for Gate 2A v3."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import mpmath as mp
import numpy as np
import sympy as sp
from scipy import special

from .config import ALL_FUNCTIONS, CLASSES, ORACLE_DIGITS, ORACLE_POINTS, ORACLE_REL_TOL, RESULTS, class_columns, domain_for
from .functions import symbolic_z
from .transfer import transfer_matrix


@dataclass(frozen=True)
class OracleClass:
    n_exact: int
    coeffs: list[float] | None


ORACLE_METADATA = {
    "method": "sympy_derivatives_mpmath_svd_gate2a_v3",
    "precision_digits": ORACLE_DIGITS,
    "points": ORACLE_POINTS,
    "relative_threshold": ORACLE_REL_TOL,
    "n_exact_policy": "wide_table_used_for_both_domains; narrow_table_retained_as_diagnostic",
}

V2_CACHE = Path("experiments/annihilator_gate2a_v2/results/oracle_reference_v2.json")


def _cache_is_valid(data: dict) -> bool:
    metadata = dict(data.get("metadata", {}))
    metadata.pop("source_cache", None)
    return metadata == ORACLE_METADATA


def _v3_cache_path() -> Path:
    return RESULTS / "oracle_reference_v3.json"


def _mp_airyaiprime(x):
    return mp.airyai(x, derivative=1)


def _scipy_airyai(x):
    return special.airy(x)[0]


def _scipy_airyaiprime(x):
    return special.airy(x)[1]


MPMATH_MODULES = [{"airyai": mp.airyai, "airyaiprime": _mp_airyaiprime, "besselj": mp.besselj}, "mpmath"]
SCIPY_MODULES = [{"airyai": _scipy_airyai, "airyaiprime": _scipy_airyaiprime, "besselj": special.jv}, "scipy", "numpy"]


def lambdify_mpmath_derivative(symbol: sp.Symbol, expr: sp.Expr, order: int):
    return sp.lambdify(symbol, sp.diff(expr, symbol, order), MPMATH_MODULES)


def lambdify_scipy_derivative(symbol: sp.Symbol, expr: sp.Expr, order: int):
    return sp.lambdify(symbol, sp.diff(expr, symbol, order), SCIPY_MODULES)


@lru_cache(maxsize=None)
def _mp_derivatives(function_key: str, domain_name: str):
    spec = ALL_FUNCTIONS[function_key]
    domain = domain_for(spec, domain_name)
    z, expr = symbolic_z(function_key, domain)
    return tuple(lambdify_mpmath_derivative(z, expr, k) for k in range(max(r for r, _ in CLASSES) + 1))


@lru_cache(maxsize=None)
def _mp_sample() -> tuple[mp.mpf, ...]:
    return tuple(mp.mpf("-0.97") + mp.mpf("1.94") * i / (ORACLE_POINTS - 1) for i in range(ORACLE_POINTS))


def _mp_collocation_matrix(function_key: str, domain_name: str, r: int, d: int) -> mp.matrix:
    derivs = _mp_derivatives(function_key, domain_name)
    sample = _mp_sample()
    mat = mp.matrix(ORACLE_POINTS, (r + 1) * (d + 1))
    for col, (k, j) in enumerate(class_columns(r, d)):
        for row, zi in enumerate(sample):
            mat[row, col] = (zi**j) * derivs[k](zi)
    return mat


def _nullspace(function_key: str, domain_name: str, r: int, d: int) -> tuple[int, list[float] | None]:
    mp.mp.dps = ORACLE_DIGITS
    mat = _mp_collocation_matrix(function_key, domain_name, r, d)
    _, singular_values, vh = mp.svd_r(mat, full_matrices=False)
    s = [mp.mpf(value) for value in singular_values]
    threshold = mp.mpf(str(ORACLE_REL_TOL)) * max(s)
    n_exact = sum(value < threshold for value in s)
    coeffs = None
    if n_exact > 0:
        row = vh[mat.cols - 1, :]
        vec = np.array([float(row[i]) for i in range(mat.cols)], dtype=float)
        vec /= np.linalg.norm(vec)
        max_i = int(np.argmax(np.abs(vec)))
        if vec[max_i] < 0:
            vec *= -1.0
        coeffs = vec.tolist()
    return n_exact, coeffs


def _definition_residual(function_key: str, domain_name: str) -> sp.Expr:
    domain = domain_for(ALL_FUNCTIONS[function_key], domain_name)
    z, expr = symbolic_z(function_key, domain)
    mu = sp.nsimplify(domain.mu, rational=True)
    scale = sp.nsimplify(domain.scale, rational=True)
    if function_key == "K3":
        coeffs = [-(scale**2) * mu, -(scale**3), 0, 0, 1, 0]
    elif function_key == "K4":
        coeffs = [(scale**2) * mu, scale**3, scale, 0, mu, scale]
    else:
        raise KeyError(function_key)
    total = 0
    for c, (k, j) in zip(coeffs, class_columns(2, 1)):
        total += c * z**j * sp.diff(expr, z, k)
    return sp.simplify(total)


def _verify_reference(function_key: str, domain_name: str, r: int, d: int, coeffs: list[float]) -> dict:
    if function_key in {"K3", "K4"}:
        residual = _definition_residual(function_key, domain_name)
        mode = "definition_ode_symbolic"
        passed = residual == 0
        return {"mode": mode, "symbolic_zero": bool(passed), "passed": bool(passed)}
    elif function_key == "F10":
        residual = symbolic_residual(function_key, domain_name, r, d, np.asarray(coeffs, dtype=float))
        mode = "numeric"
    else:
        residual = symbolic_residual(function_key, domain_name, r, d, np.asarray(coeffs, dtype=float))
        exact = sp.simplify(residual)
        if exact == 0:
            return {"mode": "symbolic_nsimplify", "symbolic_zero": True, "passed": True}
        mode = "symbolic_nsimplify"
    sample = np.linspace(-0.9, 0.9, 19)
    values = [float(abs(sp.N(residual.subs({"z": z}), 80))) for z in sample]
    max_abs = max(values)
    return {"mode": mode, "max_abs_on_sample": max_abs, "passed": max_abs < 1e-45}


def _apply_v3_oracle_rules(data: dict, source: str) -> dict:
    data = json.loads(json.dumps(data))
    data["metadata"] = dict(ORACLE_METADATA, source_cache=source)
    for function_key, function_data in data["functions"].items():
        wide = function_data["wide"]
        narrow = function_data["narrow"]
        narrow["diagnostic_direct_reference_class"] = list(narrow["reference_class"])
        narrow["diagnostic_direct_reference_coeffs"] = narrow["reference_coeffs"]
        narrow["diagnostic_direct_classes"] = json.loads(json.dumps(narrow["classes"]))
        narrow["diagnostic_direct_reference_matches_wide"] = tuple(narrow["reference_class"]) == tuple(wide["reference_class"])
        for class_key, class_data in narrow["classes"].items():
            direct = int(class_data["n_exact"])
            wide_n = int(wide["classes"][class_key]["n_exact"])
            class_data["diagnostic_direct_n_exact"] = direct
            class_data["n_exact"] = wide_n
        r, d = tuple(wide["reference_class"])
        spec = ALL_FUNCTIONS[function_key]
        narrow["reference_class"] = list(wide["reference_class"])
        transform = transfer_matrix(r, d, spec.narrow, spec.wide)
        narrow_coeffs = np.linalg.solve(transform, np.asarray(wide["reference_coeffs"], dtype=float))
        narrow_coeffs /= np.linalg.norm(narrow_coeffs)
        if narrow_coeffs[int(np.argmax(np.abs(narrow_coeffs)))] < 0:
            narrow_coeffs *= -1.0
        narrow["reference_coeffs"] = narrow_coeffs.tolist()
        narrow["reference_n_exact"] = narrow["classes"][f"{r},{d}"]["n_exact"]
        narrow["verification"] = _verify_reference(function_key, "narrow", r, d, narrow["reference_coeffs"])
        wide["verification"] = _verify_reference(function_key, "wide", *tuple(wide["reference_class"]), wide["reference_coeffs"])
    return data


def promote_v2_cache(cache_path: Path | None = None) -> dict:
    cache_path = cache_path or _v3_cache_path()
    if not V2_CACHE.exists():
        raise FileNotFoundError(f"v2 oracle cache not found: {V2_CACHE}")
    data = _apply_v3_oracle_rules(json.loads(V2_CACHE.read_text()), str(V2_CACHE))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, indent=2, sort_keys=True))
    return data


def build_reference(cache_path: Path | None = None, force: bool = False, function_keys: list[str] | None = None) -> dict:
    cache_path = cache_path or _v3_cache_path()
    if function_keys is None and cache_path.exists() and not force:
        data = json.loads(cache_path.read_text())
        if _cache_is_valid(data):
            return data
    if function_keys is None and not force and V2_CACHE.exists():
        return promote_v2_cache(cache_path)
    start = time.perf_counter()
    data: dict[str, dict] = {"metadata": ORACLE_METADATA, "classes": [list(c) for c in CLASSES], "functions": {}}
    selected = function_keys if function_keys is not None else list(ALL_FUNCTIONS)
    for fkey in selected:
        spec = ALL_FUNCTIONS[fkey]
        data["functions"][fkey] = {}
        for domain_name in ("wide", "narrow"):
            classes = {}
            reference_class = None
            reference_coeffs = None
            for r, d in CLASSES:
                n_exact_value, coeffs = _nullspace(fkey, domain_name, r, d)
                classes[f"{r},{d}"] = {"n_exact": int(n_exact_value)}
                if reference_class is None and n_exact_value > 0:
                    reference_class = (r, d)
                    reference_coeffs = coeffs
                    classes[f"{r},{d}"]["coeffs"] = coeffs
            if reference_class is None or reference_coeffs is None:
                raise RuntimeError(f"oracle found no reference class for {fkey}/{domain_name}")
            verification = _verify_reference(fkey, domain_name, *reference_class, reference_coeffs)
            data["functions"][fkey][domain_name] = {
                "expected_class": list(spec.reference_class),
                "reference_class": list(reference_class),
                "class_matches_expected": reference_class == spec.reference_class,
                "reference_coeffs": reference_coeffs,
                "reference_n_exact": classes[f"{reference_class[0]},{reference_class[1]}"]["n_exact"],
                "verification": verification,
                "classes": classes,
            }
    data["runtime_seconds"] = time.perf_counter() - start
    data = _apply_v3_oracle_rules(data, "fresh_v3_nullspace")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, indent=2, sort_keys=True))
    return data


def reference_for(function_key: str, domain_name: str) -> tuple[tuple[int, int], np.ndarray]:
    ref = build_reference()["functions"][function_key][domain_name]
    return tuple(ref["reference_class"]), np.asarray(ref["reference_coeffs"], dtype=float)


def n_exact(function_key: str, domain_name: str, r: int, d: int) -> int:
    return int(build_reference()["functions"][function_key][domain_name]["classes"][f"{r},{d}"]["n_exact"])


def symbolic_residual(function_key: str, domain_name: str, r: int, d: int, coeffs: np.ndarray) -> sp.Expr:
    domain = domain_for(ALL_FUNCTIONS[function_key], domain_name)
    z, expr = symbolic_z(function_key, domain)
    coeffs = np.asarray(coeffs, dtype=float)
    pivot = coeffs[int(np.argmax(np.abs(coeffs)))]
    if pivot == 0:
        raise ValueError("zero reference coefficient pivot")
    total = 0
    for c, (k, j) in zip(coeffs, class_columns(r, d)):
        ratio = float(c / pivot)
        coeff = sp.Integer(0) if abs(ratio) < 1e-12 else sp.nsimplify(ratio, tolerance=1e-9, rational=True)
        total += coeff * z**j * sp.diff(expr, z, k)
    return sp.simplify(total)
