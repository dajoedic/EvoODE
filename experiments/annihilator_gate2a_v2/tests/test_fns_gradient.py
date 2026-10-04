import numpy as np

from experiments.annihilator_gate2a_v2.operator_search import fns_cost, fns_gradient, normalize_coeffs


def test_fns_gradient_matches_finite_differences_on_small_random_instance():
    rng = np.random.default_rng(123)
    a_fit = rng.normal(size=(7, 4))
    k_fit = rng.normal(size=(7, 4, 9))
    coeffs = normalize_coeffs(rng.normal(size=4))
    analytic = fns_gradient(a_fit, k_fit, coeffs)
    eps = 1e-6
    numeric = np.empty_like(coeffs)
    for i in range(coeffs.size):
        step = np.zeros_like(coeffs)
        step[i] = eps
        numeric[i] = (fns_cost(a_fit, k_fit, coeffs + step) - fns_cost(a_fit, k_fit, coeffs - step)) / (2 * eps)
    assert np.linalg.norm(analytic - numeric) / max(np.linalg.norm(numeric), 1e-12) < 2e-4
