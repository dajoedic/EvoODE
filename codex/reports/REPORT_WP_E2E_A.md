# WP-E2E-A Report

## Status

Blocked by the required sanity check. The implementation and tests were completed, but `--sanity` produced a failing plausibility result for the exact-derivative reference-class Annihilator chain on systems 7 and 19. Per task instruction, no method or rule was changed after this finding.

## Files

- `experiments/annihilator_odebench_smoke/end2end.py`
- `experiments/annihilator_odebench_smoke/tests/test_end2end.py`
- `experiments/annihilator_odebench_smoke/results_e2e/setup.json`
- `experiments/annihilator_odebench_smoke/results_e2e/reference.json`
- `experiments/annihilator_odebench_smoke/results_e2e/sanity.json`

## Commands And Output

```text
python -m pytest experiments/annihilator_odebench_smoke/tests/test_end2end.py -q
9 passed in 1.41s
```

```text
python -m pytest experiments/annihilator_odebench_smoke/tests -q --basetemp=.pytest_tmp/e2e_smoke_final
23 passed in 7.23s
```

```text
python -m pytest experiments/annihilator_gate2a_v3/tests -q --basetemp=.pytest_tmp/e2e_v3_final
54 passed in 70.01s (0:01:10)
```

```text
python -m experiments.annihilator_odebench_smoke.end2end --sanity
exit code: 0
results: experiments/annihilator_odebench_smoke/results_e2e/sanity.json
```

No `--run` command on systems 3, 7, 19, 21 was executed.

## Sanity Results

Synthetic 1D ODE, eta 0:

| method | validation NRMSE_x | passed |
|---|---:|---|
| annihilator | 1.1209905410459518e-06 | true |
| sindy | 1.960490741024021e-07 | true |
| wsindy | 7.059147062524494e-09 | true |

Exact derivative, fixed reference class:

| system | reference class | validation NRMSE_x | fail reason | seconds | AML iterations | passed |
|---:|---|---:|---|---:|---:|---|
| 3 | [3, 0] | 4.807801567753964e-07 | null | 30.435145600000396 | 23 | true |
| 7 | [3, 1] | Infinity | LEADING_ZERO_IN_TRAINING_DOMAIN | 41.208182600006694 | 90 | false |
| 19 | [2, 2] | Infinity | LEADING_ZERO_IN_TRAINING_DOMAIN | 30.546467000007397 | 22 | false |
| 21 | [3, 0] | 2.4125315867010034e-06 | null | 28.949313899996923 | 12 | true |

`sanity.json` top-level `passed` is `false`; total sanity time was 250.7361372000014 seconds.

## Record Field List From Synthetic Run

Top-level fields from a synthetic SINDy `P2` record:

`spec`, `system_id`, `eta`, `seed`, `method`, `protocol`, `training_trajectories`, `selection_rule`, `selected_validation_nrmse_x`, `selected_validation_fail_reason`, `candidate_validations`, `refit_on_full_time`, `nrmse_f`, `reconstruction`, `generalization`, `reconstruction_r2`, `generalization_r2`, `reconstruction_nrmse_x`, `generalization_nrmse_x`, `structure_exact`, `structure_superset`, `selected_model`, `counts`.

Origins:

- Existing ODEBench/synthetic system fields: `system_id`, `eta`, `seed`, `method`, `protocol`, `training_trajectories`.
- New end-to-end selection fields: `spec`, `selection_rule`, `selected_validation_nrmse_x`, `selected_validation_fail_reason`, `candidate_validations`, `refit_on_full_time`, `counts`.
- Analysis pipeline fields: `nrmse_f`, `reconstruction`, `generalization`, `reconstruction_r2`, `generalization_r2`, `reconstruction_nrmse_x`, `generalization_nrmse_x`, `structure_exact`, `structure_superset`, `selected_model`.

Nested fields:

- `candidate_validations`: `candidate`, `validation_nrmse_x`, `fail_reason`.
- `reconstruction` / `generalization`: `name`, `nrmse_x`, `r2`, `fail_reason`.
- `counts`: `candidate_count`, `failed_candidates`, `selection_integrations`.
- Baseline `selected_model`: `selected_terms`, `selected_term_names`, `threshold`, `category`, `pysindy_parameters`.
- Baseline `pysindy_parameters`: `pysindy_version`, `method`, `library_terms`, `threshold`, `model`, `optimizer`, `differentiation_method`, `feature_library`, `function_library`.

## Instantiated PySINDy Parameters

SINDy:

- `pysindy_version`: 2.1.0 observed through the runtime object.
- Library terms: `1`, `x`, `x^2`, `x^3`, `log(x)`, `x log(x)`, `exp(-x)`, `sin(x)`, `cos(x)`, filtered to finite values on the noisy learning states.
- Optimizer: `STLSQ`, `normalize_columns=True`, threshold from the 20-value grid `1e-3` to `1`.
- Differentiation: `SmoothedFiniteDifference()` defaults. Runtime parameters included `save_smooth=True`, Savitzky-Golay smoother with `window_length=11`, `polyorder=3`, `axis=0`.

W-SINDy:

- Same custom function library and STLSQ settings.
- Feature library: `WeakPDELibrary(function_library=..., spatiotemporal_grid=t, K=200)`.
- Differentiation object in the model: `FiniteDifference()` defaults.

## Annihilator Fit Cost From Sanity Check 2

One fixed-class Annihilator fit in check (2) used 2000 resampled points and one class. Observed wall times were 28.949313899996923 to 41.208182600006694 seconds per fit, median 30.490806300003896 seconds. AML iterations were 12, 23, 90, and 22 for systems 21, 3, 7, and 19 respectively.

For a discovery fit over the 18 end-to-end classes, a direct linear extrapolation from check (2) gives about 521.0876501999446 to 741.7472868001205 seconds per Annihilator fit before extra validation integrations.
