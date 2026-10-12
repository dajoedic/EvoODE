# WP-N45b Report

## Built

- Added deterministic Weak-SINDy seeding in `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`.
- PySINDy sampling location checked locally: `pysindy/feature_library/weak_pde_library.py`, class `WeakPDELibrary`.
- `WeakPDELibrary.__init__()` calls `_weak_form_setup()`, which calls `_set_up_weights()`. `_set_up_weights()` samples subdomain centers with `np.random.uniform(...)`, including resampling when a domain has fewer than two indices.
- The runner now calls `np.random.seed(seed)` immediately before constructing `ps.WeakPDELibrary(...)`.
- Weak-SINDy seed derivation uses the WP-N45 E-SINDy fields: `system_id`, `initial_condition_set`, `noise_sigma`, `subsample_rho`, `noise_realization`, `data_condition_fingerprint`, and `library_id`; JSON is sorted/compact and SHA-256 first 8 hex digits are converted to an integer.
- E-SINDy keeps the WP-N45 seed derivation unchanged: no method tag is added to `ensemble_seed`.
- Weak-SINDy adds `method: "weak_sindy"` before hashing, so Weak-SINDy and E-SINDy do not share a seed for the same cell/configuration.
- Added `weak_seed` for Weak-SINDy rows. `ensemble_seed` remains readable and unchanged for E-SINDy rows. SINDy-only output does not get a `weak_seed` column.
- No `WeakPDELibrary` argument, `STLSQ` argument, or `EnsembleOptimizer` argument was changed.
- Hierarchy code was not changed; Weak-SINDy clean rows remain realization-level repetitions.
- Updated `SCRIPTS.md` with the 10-shard C-6 command for `--methods weak_sindy,e_sindy` into `outputs\c6_seeded_weak_esindy_baselines_<SHA>\`, plus merge-compatible SINDy/Weak and E-only shard preparation and the hierarchy merge command.

## Tests

Focused runner tests:

```text
python -m pytest analysis/tests/test_phasec_noise_sindy_baselines.py -q --basetemp .pytest_tmp_wp_n45b_focus
```

Result:

- 8 passed
- 14 PySINDy `AxesWarning` warnings

Required acceptance command:

```text
python -m pytest analysis/tests -q -k "sindy or hierarchy" --basetemp .pytest_tmp_wp_n45b
```

Result:

- 36 passed
- 98 deselected
- 14 PySINDy `AxesWarning` warnings

Test coverage added:

- Same Weak-SINDy cell run twice gives identical `weak_seed`.
- Same Weak-SINDy cell run twice gives identical `sindy_coefficients_active`.
- Weak-SINDy `weak_seed` differs from E-SINDy `ensemble_seed` for the same cell/configuration.
- SINDy-only output has no `weak_seed` column and no seed values.

## Smoke

Smoke input:

- 4 exported cells copied from `outputs/stage1/data_export/index.csv`
- Full `analysis/configs/paper1_phaseC_sindy_baseline.json`
- Method: `weak_sindy`
- Output root: `outputs/wp_n45b_weak_smoke_20261013_005147/`

Commands:

```text
python analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py --export-index outputs/wp_n45b_weak_smoke_20261013_005147/input/index.csv --output-dir outputs/wp_n45b_weak_smoke_20261013_005147/run1 --methods weak_sindy
python analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py --export-index outputs/wp_n45b_weak_smoke_20261013_005147/input/index.csv --output-dir outputs/wp_n45b_weak_smoke_20261013_005147/run2 --methods weak_sindy
```

Results:

- Run 1 rows: 40
- Run 2 rows: 40
- Run 1 fit statuses: 40 `success`
- Run 2 fit statuses: 40 `success`
- Run 1 unique `weak_seed` values: 40
- Coefficient-compare CSV columns: `method`, `method_config_id`, `library_id`, `system_id`, `source_initial_condition_set`, `noise_sigma`, `subsample_rho`, `noise_realization`, `data_condition_fingerprint`, `weak_seed`, `sindy_coefficients_active`
- Run 1 coefficient output SHA-256: `31beb0694a07e24bab2ce1435d67aeaec66ac2b41dcf8eed28ca3511c1ca5dd0`
- Run 2 coefficient output SHA-256: `31beb0694a07e24bab2ce1435d67aeaec66ac2b41dcf8eed28ca3511c1ca5dd0`
- Byte-identical coefficient output: `true`

## SINDy/E-SINDy Stability

- SINDy fit path still calls `fit_sindy(...)` directly and never computes a seed.
- A SINDy-only run writes no `weak_seed` column.
- E-SINDy still records `ensemble_seed` and `ensemble_optimizer_metadata`; its seed hashes the same WP-N45 key as before because `esindy_seed(...)` returns `hash_seed(sindy_seed_key(...))` with no method tag.
