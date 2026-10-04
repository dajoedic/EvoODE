import numpy as np

from experiments.annihilator_gate2a_v3.config import FUNCTIONS, Settings, domain_for
from experiments.annihilator_gate2a_v3.functions import grid, numeric_values
from experiments.annihilator_gate2a_v3.transfer import angle, transfer_coeffs
from experiments.annihilator_gate2a_v3.weak_operator import split_matrices


def test_weak_oracle_residual_is_small_on_exact_data():
    settings = Settings(n=600, modes=8, ell_max=3, sigma_floor_factor=1e-8, boot_reps=3)
    domain = domain_for(FUNCTIONS["F2"], "wide")
    x, z = grid(domain, settings.n)
    values = numeric_values("F2", x)
    coeffs = np.asarray([-3.0, 1.0], dtype=float)
    coeffs /= np.linalg.norm(coeffs)
    _, _, a_fit, a_val = split_matrices(z, values, 1, 0, settings)
    rel = np.linalg.norm(a_val @ coeffs) / (np.linalg.norm(a_val) * np.linalg.norm(coeffs))
    assert rel < 5e-2


def test_transfer_exact_f2_operator_is_parallel():
    spec = FUNCTIONS["F2"]
    narrow = np.asarray([-0.3, 1.0], dtype=float)
    narrow /= np.linalg.norm(narrow)
    wide = np.asarray([-3.0, 1.0], dtype=float)
    wide /= np.linalg.norm(wide)
    moved = transfer_coeffs(narrow, 1, 0, spec.narrow, spec.wide)
    assert angle(moved, wide) < 1e-10
