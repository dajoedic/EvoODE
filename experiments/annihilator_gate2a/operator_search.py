"""Candidate selection, tests, A1 and A2 for Gate 2A."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
from scipy.stats import chi2

from .config import CLASSES, PINV_REL_TOL, Settings, class_columns
from .functions import sigma_eff
from .weak_operator import WeightContext, residual_weights, split_matrices


@dataclass
class TestResult:
    passed: bool
    statistic: float
    dof: int
    critical: float
    rank: int


@dataclass
class Selection:
    selected_class: tuple[int, int] | None
    coeffs: np.ndarray | None
    coeff_cov: np.ndarray | None
    statistic: float | None
    dof: int | None
    critical: float | None
    singular_values: tuple[float | None, float | None]
    a1: bool
    bootstrap_share: float | None
    tested_classes: int


@dataclass
class ClassEvaluation:
    coeffs: np.ndarray
    coeff_cov: np.ndarray
    test: TestResult
    singular_values: np.ndarray


def normalize_coeffs(vec: np.ndarray) -> np.ndarray:
    out = np.asarray(vec, dtype=float).copy()
    out /= np.linalg.norm(out)
    i = int(np.argmax(np.abs(out)))
    if out[i] < 0:
        out *= -1.0
    return out


def _pinv_quadratic(cov: np.ndarray, rho: np.ndarray, alpha: float) -> TestResult:
    vals, vecs = np.linalg.eigh(0.5 * (cov + cov.T))
    vmax = float(np.max(vals)) if vals.size else 0.0
    keep = vals > PINV_REL_TOL * vmax if vmax > 0 else np.zeros_like(vals, dtype=bool)
    dof = int(np.sum(keep))
    if dof == 0:
        stat = float(np.dot(rho, rho) / PINV_REL_TOL)
        critical = 0.0
        return TestResult(False, stat, 0, critical, 0)
    proj = vecs[:, keep].T @ rho
    stat = float(np.sum((proj**2) / vals[keep]))
    critical = float(chi2.ppf(1.0 - alpha, dof))
    return TestResult(stat <= critical, stat, dof, critical, dof)


def coefficient_covariance(a_fit: np.ndarray, k_fit: np.ndarray, coeffs: np.ndarray, sigma: float, singular_index: int = -1) -> np.ndarray:
    u, s, vt = np.linalg.svd(a_fit, full_matrices=False)
    n = vt.shape[1]
    idx = singular_index if singular_index >= 0 else len(s) + singular_index
    vi = vt[idx, :]
    sigma_i = s[idx]
    terms = []
    for j in range(len(s)):
        if j == idx:
            continue
        denom = sigma_i**2 - s[j] ** 2
        if abs(denom) < 1e-30:
            continue
        vj = vt[j, :]
        w_vi = residual_weights(k_fit, vi)
        w_vj = residual_weights(k_fit, vj)
        g_row = (s[j] * (u[:, j] @ w_vi) + sigma_i * (u[:, idx] @ w_vj)) / denom
        terms.append(np.outer(vj, g_row))
    if not terms:
        return np.zeros((n, n))
    g = np.sum(terms, axis=0)
    cov = (sigma**2) * (g @ g.T)
    tangent = np.eye(n) - np.outer(vi, vi)
    return tangent @ cov @ tangent


def test_operator(a_val: np.ndarray, k_val: np.ndarray, coeffs: np.ndarray, coeff_cov: np.ndarray, sigma: float, settings: Settings) -> TestResult:
    rho = a_val @ coeffs
    w = residual_weights(k_val, coeffs)
    cov = (sigma**2) * (w @ w.T) + a_val @ coeff_cov @ a_val.T
    return _pinv_quadratic(cov, rho, settings.alpha)


def evaluate_class(
    a_fit: np.ndarray,
    k_fit: np.ndarray,
    a_val: np.ndarray,
    k_val: np.ndarray,
    sigma: float,
    settings: Settings,
    singular_index: int = -1,
) -> ClassEvaluation:
    _, s, vt = np.linalg.svd(a_fit, full_matrices=False)
    coeffs = normalize_coeffs(vt[singular_index, :])
    coeff_cov = coefficient_covariance(a_fit, k_fit, coeffs, sigma, singular_index)
    test = test_operator(a_val, k_val, coeffs, coeff_cov, sigma, settings)
    return ClassEvaluation(coeffs, coeff_cov, test, s)


def search_once(
    z: np.ndarray,
    values: np.ndarray,
    eta: float,
    settings: Settings,
    forced_class: tuple[int, int] | None = None,
    test_sigma_scale: float = 1.0,
    context: WeightContext | None = None,
) -> Selection:
    sigma = test_sigma_scale * sigma_eff(values, eta, settings.sigma_floor_factor)
    candidates = [forced_class] if forced_class else CLASSES
    context = context or WeightContext(z, values, settings)
    tested = 0
    for r, d in candidates:
        tested += 1
        k_fit, k_val, a_fit, a_val = context.split(r, d)
        evaluation = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, settings, -1)
        coeffs = evaluation.coeffs
        coeff_cov = evaluation.coeff_cov
        test = evaluation.test
        s = evaluation.singular_values
        if test.passed:
            a1 = False
            if a_fit.shape[1] >= 2:
                a1 = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, settings, -2).test.passed
            s2 = float(s[-2]) if len(s) > 1 else None
            s1 = float(s[-1]) if len(s) > 0 else None
            return Selection((r, d), coeffs, coeff_cov, test.statistic, test.dof, test.critical, (s1, s2), a1, None, tested)
    return Selection(None, None, None, None, None, None, (None, None), False, None, tested)


def bootstrap_share(
    z: np.ndarray,
    values: np.ndarray,
    eta: float,
    seed: int,
    selected_class: tuple[int, int] | None,
    settings: Settings,
    context: WeightContext | None = None,
) -> float | None:
    if selected_class is None:
        return None
    sigma = sigma_eff(values, eta, settings.sigma_floor_factor)
    same = 0
    for b in range(settings.boot_reps):
        rng = np.random.default_rng(10000 + 100 * seed + b)
        replicated = values + sigma * rng.standard_normal(values.size)
        replica_context = context.with_values(replicated) if context is not None else None
        sel = search_once(z, replicated, eta, settings, test_sigma_scale=sqrt(2.0), context=replica_context)
        if sel.selected_class == selected_class:
            same += 1
    return same / settings.boot_reps


def full_search(z: np.ndarray, values: np.ndarray, eta: float, seed: int, settings: Settings, with_bootstrap: bool = True) -> Selection:
    context = WeightContext(z, values, settings)
    sel = search_once(z, values, eta, settings, context=context)
    if with_bootstrap and sel.selected_class is not None:
        share = bootstrap_share(z, values, eta, seed, sel.selected_class, settings, context)
        sel.bootstrap_share = share
    return sel
