import numpy as np
from functools import lru_cache

from experiments.annihilator_gate2a_v3.config import CALIBRATION_FUNCTIONS, Settings, calibration_reference_coeffs, domain_for
from experiments.annihilator_gate2a_v3.functions import noisy_sample
from experiments.annihilator_gate2a_v3.operator_search import aml_candidate, aml_cost, aml_projected_gradient, normalize_coeffs
from experiments.annihilator_gate2a_v3.transfer import angle
from experiments.annihilator_gate2a_v3.weak_operator import WeightContext


@lru_cache(maxsize=1)
def _k1_wide_fit_matrices():
    settings = Settings(n=2000, ell_max=3, sigma_floor_factor=1e-8, boot_reps=1)
    spec = CALIBRATION_FUNCTIONS["K1"]
    _, z, values, _ = noisy_sample("K1", domain_for(spec, "wide"), settings.n, 0.01, 0)
    context = WeightContext(z, values, settings)
    k_fit, _, a_fit, _ = context.split(2, 0)
    return k_fit, a_fit


def test_aml_lbfgs_improves_svd_start_and_has_small_projected_gradient():
    k_fit, a_fit = _k1_wide_fit_matrices()
    _, _, vt = np.linalg.svd(a_fit, full_matrices=False)
    start = normalize_coeffs(vt[-1, :])
    coeffs, _, _, _, _, _ = aml_candidate(a_fit, k_fit, start=start)
    assert aml_cost(a_fit, k_fit, coeffs) <= aml_cost(a_fit, k_fit, start) + 1e-10
    assert np.linalg.norm(aml_projected_gradient(a_fit, k_fit, coeffs)) < 1e-5


def test_aml_lbfgs_k1_wide_one_percent_seed0_angle_under_one_degree():
    k_fit, a_fit = _k1_wide_fit_matrices()
    coeffs, _, _, _, _, _ = aml_candidate(a_fit, k_fit)
    _, true_coeffs = calibration_reference_coeffs("K1", "wide")
    true_coeffs = normalize_coeffs(np.asarray(true_coeffs, dtype=float))
    assert angle(coeffs, true_coeffs) < np.deg2rad(1.0)
