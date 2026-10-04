"""Independent symbolic/numeric reference side for Gate 2A."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import mpmath as mp
import numpy as np
import sympy as sp

from .config import CLASSES, FUNCTIONS, ORACLE_DIGITS, ORACLE_POINTS, ORACLE_REL_TOL, RESULTS, class_columns, domain_for
from .functions import symbolic_z


@dataclass(frozen=True)
class OracleClass:
    n_exact: int
    coeffs: list[float] | None


ORACLE_METADATA = {
    "method": "sympy_derivatives_mpmath_svd",
    "precision_digits": ORACLE_DIGITS,
    "points": ORACLE_POINTS,
    "relative_threshold": ORACLE_REL_TOL,
}


def _cache_is_valid(data: dict) -> bool:
    return data.get("metadata") == ORACLE_METADATA


@lru_cache(maxsize=None)
def _mp_derivatives(function_key: str, domain_name: str):
    spec = FUNCTIONS[function_key]
    domain = domain_for(spec, domain_name)
    z, expr = symbolic_z(function_key, domain)
    return tuple(sp.lambdify(z, sp.diff(expr, z, k), "mpmath") for k in range(max(r for r, _ in CLASSES) + 1))


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


def _verify_reference(function_key: str, domain_name: str, r: int, d: int, coeffs: list[float]) -> None:
    if function_key == "F10":
        return
    residual = symbolic_residual(function_key, domain_name, r, d, np.asarray(coeffs, dtype=float))
    sample = np.linspace(-0.9, 0.9, 19)
    values = [float(abs(residual.subs({"z": z}))) for z in sample]
    if max(values) > 1e-8:
        raise RuntimeError(f"oracle symbolic verification failed for {function_key}/{domain_name}: {max(values)}")


def build_reference(cache_path: Path | None = None, force: bool = False) -> dict:
    cache_path = cache_path or RESULTS / "oracle_reference.json"
    if cache_path.exists() and not force:
        data = json.loads(cache_path.read_text())
        if _cache_is_valid(data):
            return data
        raise RuntimeError(f"refusing stale oracle cache without required metadata: {cache_path}")
    start = time.perf_counter()
    data: dict[str, dict] = {"metadata": ORACLE_METADATA, "classes": [list(c) for c in CLASSES], "functions": {}}
    for fkey in FUNCTIONS:
        data["functions"][fkey] = {}
        for domain_name in ("wide", "narrow"):
            classes = {}
            reference_class = None
            reference_coeffs = None
            for r, d in CLASSES:
                n_exact, coeffs = _nullspace(fkey, domain_name, r, d)
                classes[f"{r},{d}"] = {"n_exact": n_exact}
                if reference_class is None and n_exact > 0:
                    reference_class = (r, d)
                    reference_coeffs = coeffs
                    classes[f"{r},{d}"]["coeffs"] = coeffs
            if reference_class is None or reference_coeffs is None:
                raise RuntimeError(f"oracle found no reference class for {fkey}/{domain_name}")
            if reference_class != FUNCTIONS[fkey].reference_class:
                raise RuntimeError(f"oracle reference mismatch for {fkey}/{domain_name}: {reference_class}")
            if classes[f"{reference_class[0]},{reference_class[1]}"]["n_exact"] != 1:
                raise RuntimeError(f"oracle reference nullspace is not one-dimensional for {fkey}/{domain_name}")
            _verify_reference(fkey, domain_name, *reference_class, reference_coeffs)
            data["functions"][fkey][domain_name] = {
                "reference_class": list(reference_class) if reference_class else None,
                "reference_coeffs": reference_coeffs,
                "classes": classes,
            }
    data["runtime_seconds"] = time.perf_counter() - start
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, indent=2, sort_keys=True))
    return data


def reference_for(function_key: str, domain_name: str) -> tuple[tuple[int, int], np.ndarray]:
    ref = build_reference()["functions"][function_key][domain_name]
    return tuple(ref["reference_class"]), np.asarray(ref["reference_coeffs"], dtype=float)


def n_exact(function_key: str, domain_name: str, r: int, d: int) -> int:
    return int(build_reference()["functions"][function_key][domain_name]["classes"][f"{r},{d}"]["n_exact"])


def symbolic_residual(function_key: str, domain_name: str, r: int, d: int, coeffs: np.ndarray) -> sp.Expr:
    domain = domain_for(FUNCTIONS[function_key], domain_name)
    z, expr = symbolic_z(function_key, domain)
    total = 0
    for c, (k, j) in zip(coeffs, class_columns(r, d)):
        total += sp.N(str(c), 40) * z**j * sp.diff(expr, z, k)
    return sp.simplify(total)
