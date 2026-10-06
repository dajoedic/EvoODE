"""Build a fitted right-hand side from an annihilator operator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from experiments.annihilator_gate2a_v3.config import class_columns

from .catalog import Domain


@dataclass
class FHat:
    domain: tuple[float, float]
    effective_interval: tuple[float, float]
    coefficients: list[float]
    fit_coefficients: list[float]
    n_basis: int
    basis_type: str = "polynomial"

    def __call__(self, x: np.ndarray | float) -> np.ndarray:
        values = np.asarray(x, dtype=float)
        if np.any((values < self.effective_interval[0]) | (values > self.effective_interval[1])):
            raise ValueError("outside fhat domain")
        powers = np.vstack([values**i for i in range(len(self.fit_coefficients))])
        return np.tensordot(np.asarray(self.fit_coefficients), powers, axes=(0, 0))


def leading_coefficients(coeffs: np.ndarray, r: int, d: int) -> np.ndarray:
    lead = np.zeros(d + 1, dtype=float)
    for c, (k, j) in zip(np.asarray(coeffs, dtype=float), class_columns(r, d)):
        if k == r:
            lead[j] = c
    return lead


def leading_has_zero_in_domain(coeffs: np.ndarray, r: int, d: int, domain: Domain) -> bool:
    return first_real_leading_zero_in_training_domain(coeffs, r, d, domain) is not None


def real_leading_zeroes_x(coeffs: np.ndarray, r: int, d: int, domain: Domain) -> list[float]:
    lead = leading_coefficients(coeffs, r, d)
    if np.allclose(lead, 0.0):
        return [domain.a]
    roots = np.roots(lead[::-1])
    real_roots = sorted(float(domain.mu + domain.scale * root.real) for root in roots if abs(root.imag) < 1e-10)
    return real_roots


def first_real_leading_zero_in_training_domain(coeffs: np.ndarray, r: int, d: int, domain: Domain) -> float | None:
    for root in real_leading_zeroes_x(coeffs, r, d, domain):
        if domain.a <= root <= domain.b:
            return root
    return None


def effective_eval_interval(coeffs: np.ndarray, r: int, d: int, domain: Domain, eval_domain: tuple[float, float]) -> tuple[tuple[float, float] | None, str | None]:
    zero_in_training = first_real_leading_zero_in_training_domain(coeffs, r, d, domain)
    if zero_in_training is not None:
        return None, "LEADING_ZERO_IN_TRAINING_DOMAIN"
    width = domain.b - domain.a
    margin = 1e-3 * width
    left, right = map(float, eval_domain)
    for root in real_leading_zeroes_x(coeffs, r, d, domain):
        if left < root < domain.a:
            left = max(left, root + margin)
        elif domain.b < root < right:
            right = min(right, root - margin)
    if not left < right:
        return None, "EMPTY_EFFECTIVE_INTERVAL"
    return (left, right), None


def basis_ivp_fhat(coeffs: np.ndarray, r: int, d: int, domain: Domain, x_train: np.ndarray, f_train: np.ndarray, eval_domain: tuple[float, float]) -> tuple[FHat | None, str | None]:
    coeffs = np.asarray(coeffs, dtype=float)
    effective, fail = effective_eval_interval(coeffs, r, d, domain, eval_domain)
    if effective is None:
        return None, fail
    cols = class_columns(r, d)
    lead = leading_coefficients(coeffs, r, d)
    z0 = float(np.linspace(-1.0, 1.0, 200)[np.argmax(np.abs(np.polyval(lead[::-1], np.linspace(-1.0, 1.0, 200))))])

    def coeff_for(k: int, z: float) -> float:
        return float(sum(c * (z**j) for c, (kk, j) in zip(coeffs, cols) if kk == k))

    def ode(z: float, y: np.ndarray) -> np.ndarray:
        out = np.empty(r, dtype=float)
        out[:-1] = y[1:]
        denom = coeff_for(r, z)
        if abs(denom) < 1e-14:
            raise ZeroDivisionError("leading coefficient vanished")
        out[-1] = -sum(coeff_for(k, z) * y[k] for k in range(r)) / denom
        return out

    z_min = (effective[0] - domain.mu) / domain.scale
    z_max = (effective[1] - domain.mu) / domain.scale
    dense = []
    for basis_i in range(r):
        y0 = np.zeros(r)
        y0[basis_i] = 1.0
        left = solve_ivp(ode, (z0, z_min), y0, method="DOP853", dense_output=True, rtol=1e-10, atol=1e-12)
        right = solve_ivp(ode, (z0, z_max), y0, method="DOP853", dense_output=True, rtol=1e-10, atol=1e-12)
        if not left.success or not right.success:
            return None, "BASIS_INTEGRATION_FAILED"
        dense.append((left.sol, right.sol))

    z_train = (np.asarray(x_train, dtype=float) - domain.mu) / domain.scale
    basis_values = []
    for left, right in dense:
        vals = np.where(z_train <= z0, left(z_train)[0], right(z_train)[0])
        basis_values.append(vals)
    design = np.vstack(basis_values).T
    fit, *_ = np.linalg.lstsq(design, np.asarray(f_train, dtype=float), rcond=None)

    class BasisIVPFHat(FHat):
        def __call__(self, x: np.ndarray | float) -> np.ndarray:
            values = np.asarray(x, dtype=float)
            if np.any((values < self.effective_interval[0]) | (values > self.effective_interval[1])):
                raise ValueError("outside fhat domain")
            z_values = (values - domain.mu) / domain.scale
            out = np.zeros_like(z_values, dtype=float)
            for a, (left, right) in zip(fit, dense):
                out += a * np.where(z_values <= z0, left(z_values)[0], right(z_values)[0])
            return out

    return BasisIVPFHat(
        (domain.a, domain.b),
        effective,
        coeffs.tolist(),
        fit.tolist(),
        r,
        "basis_ivp",
    ), None
