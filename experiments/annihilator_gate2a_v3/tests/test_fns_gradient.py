import numpy as np

from experiments.annihilator_gate2a_v3.operator_search import aml_cost, aml_projected_gradient, normalize_coeffs


def test_aml_gradient_matches_finite_differences_on_small_random_instance():
    rng = np.random.default_rng(123)
    a_fit = rng.normal(size=(7, 4))
    k_fit = rng.normal(size=(7, 4, 9))
    coeffs = normalize_coeffs(rng.normal(size=4))
    analytic = aml_projected_gradient(a_fit, k_fit, coeffs)
    eps = 1e-6
    numeric = np.empty_like(coeffs)
    for i in range(coeffs.size):
        step = np.zeros_like(coeffs)
        step[i] = eps
        numeric[i] = (aml_cost(a_fit, k_fit, coeffs + step) - aml_cost(a_fit, k_fit, coeffs - step)) / (2 * eps)
    assert np.linalg.norm(analytic - numeric) / max(np.linalg.norm(numeric), 1e-12) < 2e-4


def test_aml_projected_gradient_is_tangent():
    rng = np.random.default_rng(456)
    a_fit = rng.normal(size=(9, 5))
    k_fit = rng.normal(size=(9, 5, 11))
    coeffs = normalize_coeffs(rng.normal(size=5))
    projected = aml_projected_gradient(a_fit, k_fit, coeffs)
    assert abs(float(np.dot(projected, coeffs))) < 1e-10
