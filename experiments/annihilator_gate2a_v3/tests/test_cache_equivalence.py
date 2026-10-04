import dataclasses

import numpy as np

from experiments.annihilator_gate2a_v3.config import Settings, domain_for, CALIBRATION_FUNCTIONS
from experiments.annihilator_gate2a_v3.functions import noisy_sample, sigma_eff
from experiments.annihilator_gate2a_v3.operator_search import evaluate_class
from experiments.annihilator_gate2a_v3.weak_operator import class_column_indices, matrix_from_tensor, sample_split, weight_tensor, WeightContext


class UncachedWeightContext:
    def __init__(self, z, values, settings):
        self.z = np.asarray(z, dtype=float)
        self.values = np.asarray(values, dtype=float)
        self.settings = settings
        self.z_fit, self.values_fit = sample_split(self.z, self.values, "fit")
        self.z_val, self.values_val = sample_split(self.z, self.values, "val")
        self.k_fit_full = weight_tensor(self.z_fit, 6, 6, "fit", settings)
        self.k_val_full = weight_tensor(self.z_val, 6, 6, "val", settings)
        self.a_fit_full = matrix_from_tensor(self.k_fit_full, self.values_fit)
        self.a_val_full = matrix_from_tensor(self.k_val_full, self.values_val)

    def with_values(self, values):
        return UncachedWeightContext(self.z, values, self.settings)

    def split(self, r, d):
        idx = class_column_indices(r, d)
        return (
            self.k_fit_full[:, idx, :],
            self.k_val_full[:, idx, :],
            self.a_fit_full[:, idx],
            self.a_val_full[:, idx],
        )


def _evaluation_record(evaluation):
    record = dataclasses.asdict(evaluation)
    record["coeffs"] = evaluation.coeffs.tolist()
    record["coeff_cov"] = evaluation.coeff_cov.tolist()
    record["singular_values"] = evaluation.singular_values.tolist()
    record["m_matrix"] = evaluation.m_matrix.tolist()
    return record


def test_cached_and_uncached_k_cell_evaluation_are_bitwise_equal():
    settings = Settings(n=100, ell_max=3, sigma_floor_factor=1e-8, boot_reps=1)
    _, z, values, _ = noisy_sample("K1", domain_for(CALIBRATION_FUNCTIONS["K1"], "wide"), settings.n, 0.01, 0)
    uncached = UncachedWeightContext(z, values, settings)
    cached = WeightContext(z, values, settings)
    uk_fit, uk_val, ua_fit, ua_val = uncached.split(2, 0)
    ck_fit, ck_val, ca_fit, ca_val = cached.split(2, 0)
    sigma = sigma_eff(values, 0.01, settings.sigma_floor_factor)
    uncached_eval = evaluate_class(ua_fit, uk_fit, ua_val, uk_val, sigma, settings)
    cached_eval = evaluate_class(ca_fit, ck_fit, ca_val, ck_val, sigma, settings)
    assert _evaluation_record(cached_eval) == _evaluation_record(uncached_eval)
