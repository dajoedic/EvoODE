"""Multiscale weak operator matrix construction for Gate 2A v3."""

from __future__ import annotations

from functools import lru_cache
import hashlib
from math import comb, factorial

import numpy as np
from numpy.polynomial import legendre

from .config import D_MAX, R_MAX, Settings, class_columns


def trap_weights(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    if z.size < 2:
        return np.ones_like(z)
    w = np.empty_like(z, dtype=float)
    w[1:-1] = 0.5 * (z[2:] - z[:-2])
    w[0] = 0.5 * (z[1] - z[0])
    w[-1] = 0.5 * (z[-1] - z[-2])
    return w


def sample_split(z: np.ndarray, values: np.ndarray, kind: str) -> tuple[np.ndarray, np.ndarray]:
    offset = {"fit": 0, "val": 1}[kind]
    return z[offset::2], values[offset::2]


def rows(kind: str, settings: Settings) -> list[tuple[int, int, int]]:
    if settings.ell_max is None:
        raise ValueError("ell_max is not available; run stage K or pass it explicitly")
    out = []
    for ell in range(settings.ell_max + 1):
        for block in range(2**ell):
            for mode in range(settings.modes):
                out.append((ell, block, mode))
    return out


def _falling(n: int, p: int) -> float:
    if p < 0 or p > n:
        return 0.0
    return float(factorial(n) // factorial(n - p))


def _pow_linear_derivative(base: np.ndarray, slope: float, power: int, order: int) -> np.ndarray:
    if order > power:
        return np.zeros_like(base, dtype=float)
    return _falling(power, order) * (slope**order) * (base ** (power - order))


@lru_cache(maxsize=None)
def _legendre_derivative_coeffs(mode: int, order: int) -> tuple[float, ...]:
    coef = np.zeros(mode + 1)
    coef[mode] = 1.0
    return tuple(legendre.legder(coef, m=order))


def _legendre_derivative(mode: int, order: int, u: np.ndarray) -> np.ndarray:
    coeffs = _legendre_derivative_coeffs(mode, order)
    if len(coeffs) == 0:
        return np.zeros_like(u, dtype=float)
    return legendre.legval(u, coeffs)


def _factorized_derivative_u(u: np.ndarray, center: float, halfwidth: float, z_power: int, mode: int, order: int, q: int) -> np.ndarray:
    total = np.zeros_like(u, dtype=float)
    z_base = center + halfwidth * u
    left_base = 1.0 - u
    right_base = 1.0 + u
    for a in range(order + 1):
        za = _pow_linear_derivative(z_base, halfwidth, z_power, a)
        for b in range(order - a + 1):
            lb = _pow_linear_derivative(left_base, -1.0, q, b)
            for c in range(order - a - b + 1):
                p_order = order - a - b - c
                rb = _pow_linear_derivative(right_base, 1.0, q, c)
                pd = _legendre_derivative(mode, p_order, u)
                total += comb(order, a) * comb(order - a, b) * comb(order - a - b, c) * za * lb * rb * pd
    return total


_WEIGHT_TENSOR_CACHE: dict[tuple, np.ndarray] = {}


def _z_cache_key(z: np.ndarray) -> tuple:
    z_view = np.ascontiguousarray(np.asarray(z, dtype=float))
    digest = hashlib.sha256(z_view.view(np.uint8)).hexdigest()
    return (z_view.shape, digest)


def _settings_cache_key(settings: Settings) -> tuple:
    return (settings.ell_max, settings.modes, settings.q)


def weight_tensor(z: np.ndarray, r: int, d: int, kind: str, settings: Settings) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    weights = trap_weights(z)
    cols = class_columns(r, d)
    row_defs = rows(kind, settings)
    result = np.zeros((len(row_defs), len(cols), z.size), dtype=float)
    for row_i, (ell, block, mode) in enumerate(row_defs):
        width = 2.0 / (2**ell)
        left = -1.0 + block * width
        center = left + 0.5 * width
        halfwidth = 0.5 * width
        u = (z - center) / halfwidth
        support = np.abs(u) <= 1.0 + 1e-14
        for col_i, (k, j) in enumerate(cols):
            vals = (halfwidth ** (-k)) * _factorized_derivative_u(u, center, halfwidth, j, mode, k, settings.q)
            vals = np.where(support, vals, 0.0)
            result[row_i, col_i, :] = weights * ((-1.0) ** k) * vals
    return result


def cached_weight_tensor(z: np.ndarray, r: int, d: int, kind: str, settings: Settings) -> np.ndarray:
    key = (_z_cache_key(z), r, d, kind, _settings_cache_key(settings))
    cached = _WEIGHT_TENSOR_CACHE.get(key)
    if cached is None:
        cached = weight_tensor(z, r, d, kind, settings)
        _WEIGHT_TENSOR_CACHE[key] = cached
    return cached


MAX_COLUMNS = tuple(class_columns(R_MAX, D_MAX))
MAX_COLUMN_INDEX = {col: i for i, col in enumerate(MAX_COLUMNS)}


def class_column_indices(r: int, d: int) -> list[int]:
    return [MAX_COLUMN_INDEX[col] for col in class_columns(r, d)]


class WeightContext:
    def __init__(
        self,
        z: np.ndarray,
        values: np.ndarray,
        settings: Settings,
        k_fit_full: np.ndarray | None = None,
        k_val_full: np.ndarray | None = None,
    ):
        self.z = np.asarray(z, dtype=float)
        self.values = np.asarray(values, dtype=float)
        self.settings = settings
        self.z_fit, self.values_fit = sample_split(self.z, self.values, "fit")
        self.z_val, self.values_val = sample_split(self.z, self.values, "val")
        self.k_fit_full = k_fit_full if k_fit_full is not None else cached_weight_tensor(self.z_fit, R_MAX, D_MAX, "fit", settings)
        self.k_val_full = k_val_full if k_val_full is not None else cached_weight_tensor(self.z_val, R_MAX, D_MAX, "val", settings)
        self.a_fit_full = matrix_from_tensor(self.k_fit_full, self.values_fit)
        self.a_val_full = matrix_from_tensor(self.k_val_full, self.values_val)
        self._split_cache: dict[tuple[int, int], tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}

    def with_values(self, values: np.ndarray) -> "WeightContext":
        return WeightContext(self.z, values, self.settings, self.k_fit_full, self.k_val_full)

    def split(self, r: int, d: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        cached = self._split_cache.get((r, d))
        if cached is not None:
            return cached
        idx = class_column_indices(r, d)
        cached = (
            self.k_fit_full[:, idx, :],
            self.k_val_full[:, idx, :],
            self.a_fit_full[:, idx],
            self.a_val_full[:, idx],
        )
        self._split_cache[(r, d)] = cached
        return cached


def matrix_from_tensor(tensor: np.ndarray, values: np.ndarray) -> np.ndarray:
    return np.einsum("rci,i->rc", tensor, values, optimize=True)


def residual_weights(tensor: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    return np.einsum("rci,c->ri", tensor, coeffs, optimize=True)


def split_matrices(z: np.ndarray, values: np.ndarray, r: int, d: int, settings: Settings) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    z_fit, values_fit = sample_split(z, values, "fit")
    z_val, values_val = sample_split(z, values, "val")
    k_fit = weight_tensor(z_fit, r, d, "fit", settings)
    k_val = weight_tensor(z_val, r, d, "val", settings)
    return k_fit, k_val, matrix_from_tensor(k_fit, values_fit), matrix_from_tensor(k_val, values_val)
