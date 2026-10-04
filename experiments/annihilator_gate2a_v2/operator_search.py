"""FNS candidate selection, validation tests, and ambiguity checks."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
from scipy.stats import chi2

from .config import CLASSES, FNS_ANGLE_TOL, FNS_MAX_ITER, PINV_REL_TOL, Settings
from .functions import sigma_eff
from .weak_operator import WeightContext, residual_weights


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
    a2: bool
    a3: bool
    bootstrap_share: float | None
    tested_classes: int
    fns_iterations: int
    fns_converged: bool
    sqrt_trace_cov: float | None


@dataclass
class ClassEvaluation:
    coeffs: np.ndarray
    coeff_cov: np.ndarray
    test: TestResult
    singular_values: np.ndarray
    fns_iterations: int
    fns_converged: bool
    m_matrix: np.ndarray


def normalize_coeffs(vec: np.ndarray, align_to: np.ndarray | None = None) -> np.ndarray:
    out = np.asarray(vec, dtype=float).copy()
    norm = np.linalg.norm(out)
    if norm == 0:
        raise ValueError("zero coefficient vector")
    out /= norm
    if align_to is not None:
        if float(np.dot(out, align_to)) < 0:
            out *= -1.0
        return out
    i = int(np.argmax(np.abs(out)))
    if out[i] < 0:
        out *= -1.0
    return out


def _pinv(cov: np.ndarray) -> tuple[np.ndarray, int]:
    vals, vecs = np.linalg.eigh(0.5 * (cov + cov.T))
    vmax = float(np.max(vals)) if vals.size else 0.0
    keep = vals > PINV_REL_TOL * vmax if vmax > 0 else np.zeros_like(vals, dtype=bool)
    if not np.any(keep):
        return np.zeros_like(cov), 0
    inv = (vecs[:, keep] / vals[keep]) @ vecs[:, keep].T
    return inv, int(np.sum(keep))


def _pinv_quadratic(cov: np.ndarray, rho: np.ndarray, alpha: float) -> TestResult:
    pinv, dof = _pinv(cov)
    if dof == 0:
        stat = float(np.dot(rho, rho) / PINV_REL_TOL)
        return TestResult(False, stat, 0, 0.0, 0)
    stat = float(rho @ pinv @ rho)
    critical = float(chi2.ppf(1.0 - alpha, dof))
    return TestResult(stat <= critical, stat, dof, critical, dof)


def fns_matrices(a_fit: np.ndarray, k_fit: np.ndarray, coeffs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    w = residual_weights(k_fit, coeffs)
    s_mat = w @ w.T
    s_pinv, _ = _pinv(s_mat)
    eta = s_pinv @ (a_fit @ coeffs)
    q_cols = []
    for col in range(k_fit.shape[1]):
        q_cols.append(k_fit[:, col, :].T @ eta)
    q_mat = np.column_stack(q_cols)
    m_mat = a_fit.T @ s_pinv @ a_fit
    x_mat = m_mat - q_mat.T @ q_mat
    return m_mat, 0.5 * (x_mat + x_mat.T)


def fns_cost(a_fit: np.ndarray, k_fit: np.ndarray, coeffs: np.ndarray) -> float:
    w = residual_weights(k_fit, coeffs)
    s_mat = w @ w.T
    s_pinv, _ = _pinv(s_mat)
    residual = a_fit @ coeffs
    return float(residual @ s_pinv @ residual)


def fns_gradient(a_fit: np.ndarray, k_fit: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    _, x_mat = fns_matrices(a_fit, k_fit, coeffs)
    return 2.0 * x_mat @ coeffs


def fns_candidate(a_fit: np.ndarray, k_fit: np.ndarray, start: np.ndarray | None = None) -> tuple[np.ndarray, int, bool, np.ndarray, np.ndarray]:
    _, singular_values, vt = np.linalg.svd(a_fit, full_matrices=False)
    coeffs = normalize_coeffs(vt[-1, :] if start is None else start)
    m_mat, x_mat = fns_matrices(a_fit, k_fit, coeffs)
    converged = False
    for iteration in range(1, FNS_MAX_ITER + 1):
        vals, vecs = np.linalg.eigh(x_mat)
        idx = int(np.argmin(np.abs(vals)))
        nxt = normalize_coeffs(vecs[:, idx], align_to=coeffs)
        angle_sin = float(np.sqrt(max(0.0, 1.0 - min(1.0, abs(float(np.dot(coeffs, nxt)))) ** 2)))
        coeffs = normalize_coeffs(nxt)
        m_mat, x_mat = fns_matrices(a_fit, k_fit, coeffs)
        if angle_sin < FNS_ANGLE_TOL:
            converged = True
            break
    return coeffs, iteration, converged, singular_values, m_mat


def coefficient_covariance(m_mat: np.ndarray, coeffs: np.ndarray, sigma: float) -> np.ndarray:
    p_mat = np.eye(coeffs.size) - np.outer(coeffs, coeffs)
    middle = p_mat @ m_mat @ p_mat
    middle_pinv, _ = _pinv(middle)
    cov = (sigma**2) * middle_pinv
    return p_mat @ cov @ p_mat


def test_operator(a_val: np.ndarray, k_val: np.ndarray, coeffs: np.ndarray, coeff_cov: np.ndarray, sigma: float, settings: Settings) -> TestResult:
    rho = a_val @ coeffs
    w = residual_weights(k_val, coeffs)
    cov = (sigma**2) * (w @ w.T) + a_val @ coeff_cov @ a_val.T
    return _pinv_quadratic(cov, rho, settings.alpha)


def evaluate_class(a_fit: np.ndarray, k_fit: np.ndarray, a_val: np.ndarray, k_val: np.ndarray, sigma: float, settings: Settings, start: np.ndarray | None = None) -> ClassEvaluation:
    coeffs, iterations, converged, singular_values, m_mat = fns_candidate(a_fit, k_fit, start=start)
    coeff_cov = coefficient_covariance(m_mat, coeffs, sigma)
    test = test_operator(a_val, k_val, coeffs, coeff_cov, sigma, settings)
    return ClassEvaluation(coeffs, coeff_cov, test, singular_values, iterations, converged, m_mat)


def _a1_passes(a_fit: np.ndarray, k_fit: np.ndarray, a_val: np.ndarray, k_val: np.ndarray, evaluation: ClassEvaluation, sigma: float, settings: Settings) -> bool:
    vals, vecs = np.linalg.eigh(0.5 * (evaluation.m_matrix + evaluation.m_matrix.T))
    order = np.argsort(vals)
    for idx in order:
        c2 = vecs[:, idx]
        c2 = c2 - evaluation.coeffs * float(np.dot(c2, evaluation.coeffs))
        if np.linalg.norm(c2) > 1e-12:
            c2 = normalize_coeffs(c2)
            cov2 = coefficient_covariance(evaluation.m_matrix, c2, sigma)
            return test_operator(a_val, k_val, c2, cov2, sigma, settings).passed
    return False


def search_once(z: np.ndarray, values: np.ndarray, eta: float, settings: Settings, forced_class: tuple[int, int] | None = None, test_sigma_scale: float = 1.0, context: WeightContext | None = None) -> Selection:
    sigma = test_sigma_scale * sigma_eff(values, eta, settings.sigma_floor_factor)
    candidates = [forced_class] if forced_class else CLASSES
    context = context or WeightContext(z, values, settings)
    tested = 0
    last_iterations = 0
    last_converged = True
    for r, d in candidates:
        tested += 1
        k_fit, k_val, a_fit, a_val = context.split(r, d)
        evaluation = evaluate_class(a_fit, k_fit, a_val, k_val, sigma, settings)
        last_iterations = evaluation.fns_iterations
        last_converged = evaluation.fns_converged
        if evaluation.test.passed:
            a1 = _a1_passes(a_fit, k_fit, a_val, k_val, evaluation, sigma, settings)
            sqrt_trace = float(np.sqrt(max(0.0, np.trace(evaluation.coeff_cov))))
            a3 = sqrt_trace > settings.a3_trace_threshold
            s2 = float(evaluation.singular_values[-2]) if len(evaluation.singular_values) > 1 else None
            s1 = float(evaluation.singular_values[-1]) if len(evaluation.singular_values) > 0 else None
            return Selection((r, d), evaluation.coeffs, evaluation.coeff_cov, evaluation.test.statistic, evaluation.test.dof, evaluation.test.critical, (s1, s2), a1, False, a3, None, tested, evaluation.fns_iterations, evaluation.fns_converged, sqrt_trace)
    return Selection(None, None, None, None, None, None, (None, None), False, False, False, None, tested, last_iterations, last_converged, None)


def bootstrap_share(z: np.ndarray, values: np.ndarray, eta: float, seed: int, selected_class: tuple[int, int] | None, settings: Settings, context: WeightContext | None = None) -> float | None:
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
        sel.a2 = share < settings.boot_threshold
    return sel
