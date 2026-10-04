import numpy as np

from experiments.annihilator_gate2a.config import FUNCTIONS, Settings, domain_for
from experiments.annihilator_gate2a.functions import grid, numeric_values
from experiments.annihilator_gate2a.oracle import reference_for
from experiments.annihilator_gate2a.transfer import angle, transfer_coeffs
from experiments.annihilator_gate2a.weak_operator import split_matrices


def test_weak_oracle_residual_is_small_on_exact_data():
    settings = Settings(n=600, modes=8, boot_reps=3)
    for key in ("F2", "F4", "F9"):
        domain = domain_for(FUNCTIONS[key], "wide")
        x, z = grid(domain, settings.n)
        values = numeric_values(key, x)
        (r, d), coeffs = reference_for(key, "wide")
        _, _, a_fit, a_val = split_matrices(z, values, r, d, settings)
        rel = np.linalg.norm(a_val @ coeffs) / (np.linalg.norm(a_val) * np.linalg.norm(coeffs))
        assert rel < 5e-2


def test_transfer_exact_reference_parallel_for_all_functions():
    for key, spec in FUNCTIONS.items():
        (r, d), narrow = reference_for(key, "narrow")
        wide_class, wide = reference_for(key, "wide")
        assert (r, d) == wide_class
        moved = transfer_coeffs(narrow, r, d, spec.narrow, spec.wide)
        assert angle(moved, wide) < 1e-3
