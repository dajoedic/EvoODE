"""Weak operator matrix construction."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.polynomial import Polynomial, legendre

from .config import D_MAX, R_MAX, Settings, class_columns


def trap_weights(z: np.ndarray) -> np.ndarray:
    w = np.empty_like(z, dtype=float)
    dz = float(z[1] - z[0])
    w[:] = dz
    w[0] = 0.5 * dz
    w[-1] = 0.5 * dz
    return w


def _legendre_as_polynomial(m: int) -> Polynomial:
    coef = np.zeros(m + 1)
    coef[m] = 1.0
    return Polynomial(legendre.leg2poly(coef))


def _compose_u(poly_u: Polynomial, center: float, halfwidth: float) -> Polynomial:
    u_of_z = Polynomial([-center / halfwidth, 1.0 / halfwidth])
    out = Polynomial([0.0])
    for coef in reversed(poly_u.coef):
        out = out * u_of_z + float(coef)
    return out


def test_polynomial(block_index: int, mode: int, settings: Settings) -> tuple[Polynomial, float, float]:
    width = 2.0 / settings.blocks
    left = -1.0 + block_index * width
    center = left + 0.5 * width
    halfwidth = 0.5 * width
    envelope = (Polynomial([1.0]) - Polynomial([0.0, 0.0, 1.0])) ** settings.q
    poly_u = envelope * _legendre_as_polynomial(mode)
    return _compose_u(poly_u, center, halfwidth), center, halfwidth


def _block_poly_u(block_index: int, mode: int, z_power: int, settings: Settings) -> tuple[Polynomial, float, float]:
    width = 2.0 / settings.blocks
    left = -1.0 + block_index * width
    center = left + 0.5 * width
    halfwidth = 0.5 * width
    envelope = (Polynomial([1.0]) - Polynomial([0.0, 0.0, 1.0])) ** settings.q
    z_of_u = Polynomial([center, halfwidth])
    poly_u = (z_of_u**z_power) * envelope * _legendre_as_polynomial(mode)
    return poly_u, center, halfwidth


def block_indices(kind: str, settings: Settings) -> list[int]:
    if kind == "fit":
        return [i for i in range(settings.blocks) if i % 2 == 0]
    if kind == "val":
        return [i for i in range(settings.blocks) if i % 2 == 1]
    raise ValueError(kind)


def rows(kind: str, settings: Settings) -> list[tuple[int, int]]:
    return [(b, m) for b in block_indices(kind, settings) for m in range(settings.modes)]


def weight_tensor(z: np.ndarray, r: int, d: int, kind: str, settings: Settings) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    weights = trap_weights(z)
    cols = class_columns(r, d)
    result = np.zeros((len(rows(kind, settings)), len(cols), z.size), dtype=float)
    for row_i, (b, m) in enumerate(rows(kind, settings)):
        _, center, halfwidth = test_polynomial(b, m, settings)
        u = (z - center) / halfwidth
        support = np.abs((z - center) / halfwidth) <= 1.0 + 1e-14
        for col_i, (k, j) in enumerate(cols):
            poly_u, _, _ = _block_poly_u(b, m, j, settings)
            vals = (halfwidth ** (-k)) * poly_u.deriv(k)(u)
            vals[~support] = 0.0
            result[row_i, col_i, :] = weights * ((-1.0) ** k) * vals
    return result


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
        self.k_fit_full = k_fit_full if k_fit_full is not None else weight_tensor(self.z, R_MAX, D_MAX, "fit", settings)
        self.k_val_full = k_val_full if k_val_full is not None else weight_tensor(self.z, R_MAX, D_MAX, "val", settings)
        self.a_fit_full = matrix_from_tensor(self.k_fit_full, self.values)
        self.a_val_full = matrix_from_tensor(self.k_val_full, self.values)

    def with_values(self, values: np.ndarray) -> "WeightContext":
        return WeightContext(self.z, values, self.settings, self.k_fit_full, self.k_val_full)

    def split(self, r: int, d: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        idx = class_column_indices(r, d)
        return (
            self.k_fit_full[:, idx, :],
            self.k_val_full[:, idx, :],
            self.a_fit_full[:, idx],
            self.a_val_full[:, idx],
        )


def matrix_from_tensor(tensor: np.ndarray, values: np.ndarray) -> np.ndarray:
    return np.einsum("rci,i->rc", tensor, values, optimize=True)


def residual_weights(tensor: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    return np.einsum("rci,c->ri", tensor, coeffs, optimize=True)


def split_matrices(z: np.ndarray, values: np.ndarray, r: int, d: int, settings: Settings) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    k_fit = weight_tensor(z, r, d, "fit", settings)
    k_val = weight_tensor(z, r, d, "val", settings)
    return k_fit, k_val, matrix_from_tensor(k_fit, values), matrix_from_tensor(k_val, values)
