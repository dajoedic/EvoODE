import pytest
import numpy as np

from experiments.annihilator_gate2a_v3.operator_search import _aml_objective, aml_cost, aml_projected_gradient, normalize_coeffs


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


@pytest.mark.parametrize(
    "x_vec",
    [
        np.array([-5.0, 1.25, 0.5, -0.75]),
        np.array([5.0, -1.25, 0.5, -0.75]),
    ],
)
def test_aml_objective_gradient_matches_finite_differences_with_both_signs(x_vec):
    rng = np.random.default_rng(789)
    a_fit = rng.normal(size=(8, 4))
    k_fit = rng.normal(size=(8, 4, 10))
    _, analytic = _aml_objective(a_fit, k_fit, x_vec)
    eps = 1e-6
    numeric = np.empty_like(x_vec)
    for i in range(x_vec.size):
        step = np.zeros_like(x_vec)
        step[i] = eps
        numeric[i] = (_aml_objective(a_fit, k_fit, x_vec + step)[0] - _aml_objective(a_fit, k_fit, x_vec - step)[0]) / (2 * eps)
    assert np.linalg.norm(analytic - numeric) / max(np.linalg.norm(numeric), 1e-12) < 2e-4
