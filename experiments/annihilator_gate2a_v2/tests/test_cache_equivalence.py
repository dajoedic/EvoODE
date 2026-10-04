import dataclasses

import numpy as np

from experiments.annihilator_gate2a_v2.config import Settings, domain_for, CALIBRATION_FUNCTIONS
from experiments.annihilator_gate2a_v2.functions import noisy_sample
from experiments.annihilator_gate2a_v2.operator_search import bootstrap_share, search_once
from experiments.annihilator_gate2a_v2.weak_operator import class_column_indices, matrix_from_tensor, sample_split, weight_tensor, WeightContext


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


def _selection_record(selection):
    record = dataclasses.asdict(selection)
    record["coeffs"] = None if selection.coeffs is None else selection.coeffs.tolist()
    record["coeff_cov"] = None if selection.coeff_cov is None else selection.coeff_cov.tolist()
    return record


def test_cached_and_uncached_k_cell_search_are_bitwise_equal():
    settings = Settings(n=160, ell_max=3, sigma_floor_factor=1e-8, boot_reps=5)
    _, z, values, _ = noisy_sample("K1", domain_for(CALIBRATION_FUNCTIONS["K1"], "wide"), settings.n, 0.01, 0)
    uncached = UncachedWeightContext(z, values, settings)
    cached = WeightContext(z, values, settings)
    uncached_selection = search_once(z, values, 0.01, settings, context=uncached)
    cached_selection = search_once(z, values, 0.01, settings, context=cached)
    uncached_share = bootstrap_share(z, values, 0.01, 0, uncached_selection.selected_class, settings, uncached)
    cached_share = bootstrap_share(z, values, 0.01, 0, cached_selection.selected_class, settings, cached)
    uncached_selection.bootstrap_share = uncached_share
    cached_selection.bootstrap_share = cached_share
    uncached_selection.a2 = uncached_share is not None and uncached_share < settings.boot_threshold
    cached_selection.a2 = cached_share is not None and cached_share < settings.boot_threshold
    assert _selection_record(cached_selection) == _selection_record(uncached_selection)
