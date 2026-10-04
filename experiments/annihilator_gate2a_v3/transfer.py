"""Affine transfer from narrow to wide z-coordinates."""

from __future__ import annotations

import math

import numpy as np

from .config import Domain, class_columns


def transfer_matrix(r: int, d: int, narrow: Domain, wide: Domain) -> np.ndarray:
    cols = class_columns(r, d)
    index = {col: i for i, col in enumerate(cols)}
    alpha = wide.scale / narrow.scale
    beta = (wide.mu - narrow.mu) / narrow.scale
    t = np.zeros((len(cols), len(cols)), dtype=float)
    for in_i, (k, j) in enumerate(cols):
        for p in range(j + 1):
            out_col = (k, p)
            if out_col in index:
                coeff = math.comb(j, p) * (alpha**p) * (beta ** (j - p)) * (alpha ** (-k))
                t[index[out_col], in_i] += coeff
    return t


def transfer_coeffs(coeffs: np.ndarray, r: int, d: int, narrow: Domain, wide: Domain) -> np.ndarray:
    out = transfer_matrix(r, d, narrow, wide) @ coeffs
    out /= np.linalg.norm(out)
    i = int(np.argmax(np.abs(out)))
    if out[i] < 0:
        out *= -1.0
    return out


def transfer_coeffs_and_cov(
    coeffs: np.ndarray,
    coeff_cov: np.ndarray,
    r: int,
    d: int,
    narrow: Domain,
    wide: Domain,
) -> tuple[np.ndarray, np.ndarray]:
    t = transfer_matrix(r, d, narrow, wide)
    raw = t @ coeffs
    norm = np.linalg.norm(raw)
    out = raw / norm
    cov = (t @ coeff_cov @ t.T) / (norm**2)
    i = int(np.argmax(np.abs(out)))
    if out[i] < 0:
        out *= -1.0
    return out, cov


def angle(a: np.ndarray, b: np.ndarray) -> float:
    aa = a / np.linalg.norm(a)
    bb = b / np.linalg.norm(b)
    dot = min(1.0, abs(float(np.dot(aa, bb))))
    return float(math.acos(dot))
