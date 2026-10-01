# WP-N32 Report

## Summary

Implemented the Phase-C data-condition path and selectable `clamp_val` plumbing without changing the method code. The working tree contains:

- `studies/regression/phase_c_data_condition.jl`: seeded multiplicative noise, post-noise random thinning, data-condition fingerprint, observed-data hash.
- `studies/regression/run_regression.jl`: optional data-condition and clamp arguments in `run_one`, new record fields, JSON-safe `Inf` encoding as `"Inf"`.
- `studies/regression/run_batch_cell.jl`: optional manifest columns `noise_sigma`, `subsample_rho`, `noise_realization`, `clamp_val`, defaults `0/0/0/10`.
- `studies/regression/phase_c_config.jl`: `phase_c_fingerprint(; clamp_val=...)`; default `10` is intended to preserve `0c9672de35c75a9d`.
- `studies/regression/generate_phase_c_manifest.jl`: writes the new optional columns; explicit data-condition options use `paper1_phaseC_robustness_v1`, including explicit `(0,0,10)` controls.
- `studies/regression/export_phase_c_data_conditions.jl`: exports corrupted trajectories with the existing raw little-endian Float64 hash format.
- `studies/regression/wp_n3_oracle_refit.jl`: `--clamp-val 10|1000|Inf`; the Phase-C oracle fingerprint path keeps the old payload for `10`.
- `analysis/scripts/aggregate/compare_phasec_controls.py` and `analysis/tests/test_compare_phasec_controls.py`: field-by-field control comparison.
- `test/test_wp_n32_data_condition.jl`: Julia acceptance tests for data conditions, fingerprints, `Inf`, and real-record-derived field fixture.

Status is `blocked` only because Julia cannot be executed in this Codex environment. Python tests ran green.

## Specification Notes

Section 9.4 says `(0,0)` is C-1 and reused for the main robustness grid. The task additionally says newly generated `(0,0,10)` records must not keep the C-1 experiment ID. I implemented compatibility as follows: old manifests with missing columns still run as `paper1_phaseC_v1`; explicit WP-N32 manifest generation with data-condition options uses `paper1_phaseC_robustness_v1`, even when values are `0,0,10`.

The RNG is Julia stdlib `Random.Xoshiro`. Its output is declared stable only within Julia 1.12.6. Seed schema version: `phase_c_data_condition_seed_v1`. The two streams are labelled `noise` and `subsample`, each seeded from `(system_id, ic_set, sigma, rho, realization, stream, schema_version)`, not from the method seed.

## Record Field Origins

| Field | Origin |
|---|---|
| `noise_sigma` | new record field from manifest/default |
| `subsample_rho` | new record field from manifest/default |
| `noise_realization` | new record field from manifest/default |
| `noise_model` | new record field, constant `multiplicative_gaussian_iid` |
| `data_condition_fingerprint` | analysis/data-condition layer |
| `observed_data_sha256` | analysis/data-condition layer, existing trajectory hash format |
| `n_observed_points` | analysis/data-condition layer |
| `clamp_val` | new record field from manifest/default; JSON `Inf` encoded as string `"Inf"` |

## Irregular Grid Audit

No method code was changed.

- `src/structure/stage_cap.jl:36` `_cap_uniform_step` computes `mean(diff(t))`. This assumes only ordered numeric times; it is defined on irregular grids but would summarize them as one mean step. It is currently not used by the Stage-Capped path.
- `src/structure/stage_cap.jl:41` `_cap_local_poly_derivatives` fits local polynomials on actual `t[lo:hi] .- t[i]`. Defined for irregular ordered grids; can fail numerically if duplicate times create rank problems, but thinning keeps unique original times.
- `src/structure/stage_cap.jl:63` `_cap_estimate_derivatives`: default `:local_poly` uses actual times. `:central` delegates to `estimate_derivatives`.
- `src/structure/stage_cap.jl:69` `_cap_coarsened_trajectory` takes every second observed point. Defined on irregular grids; it coarsens by observation index, not time spacing.
- `src/structure/stage_cap.jl:74` `_cap_interpolate_to_full` linearly interpolates by actual times. Defined for sorted unique times; thinning preserves this.
- `src/structure/stage_cap.jl:97` `_cap_richardson_error_estimate` compares full derivatives to coarsened/interpolated derivatives. Defined, but the interpretation is index-coarsening, not uniform-grid Richardson.
- `src/structure/stage_cap.jl:347` builds design matrices using the observed `traj.t`; defined on irregular grids.
- `src/optimize/pretune.jl:3`, `:14`, `:16`, `:20` finite differences divide by actual time gaps. Defined for sorted unique irregular grids; no uniform step assumption, but derivative accuracy changes.
- `src/optimize/pretune.jl:25` `build_design_matrix` passes each actual time to basis terms. Defined.
- `src/simulate/solve.jl:17`, `:29`, `:30`, `:39`, `:57` uses first observed point as IC, `tspan=(t[1],t[end])`, `saveat=t`, and checks returned length. Defined for sorted irregular grids.
- `src/loss/mse.jl:15` compares arrays elementwise. Defined for observed-grid arrays of equal shape.
- `studies/regression/run_regression.jl:662` and `:683` R2 compares arrays on the observed grid. Defined for equal shape; returns `nothing` on nonfinite predictions or zero variance.

No audited path was found that must throw solely because the grid is irregular, provided thinning leaves at least two sorted unique points. The stage-cap Richardson interpretation changes under irregular subsampling; per task, this is reported and not repaired.

## Verification

Ran:

```bash
python -m pytest analysis/tests/test_compare_phasec_controls.py -q --basetemp .pytest_tmp
```

Result: `2 passed in 0.32s`.

Also ran:

```bash
python -m py_compile analysis/scripts/aggregate/compare_phasec_controls.py analysis/tests/test_compare_phasec_controls.py
```

Result: no output, exit code 0.

Julia was not run because this environment cannot execute it. The `.pytest_tmp` directory was left behind because the sandbox blocked recursive removal.

## Commands for Claude

1. Julia tests, expected under 2 minutes after compilation:

```bash
julia --project=. --startup-file=no test/test_wp_n32_data_condition.jl
```

2. Four `(0,0,10)` control cells through the new path, systems 1 and 24, seed 42, both IC sets. Expected duration is the normal C-1 duration for those four cells; expected comparison result is bit-identical on `loss`, `support_terms`, `model_terms` coefficients, `total_loss_evals`, and `stage_caps`.

```bash
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl \
  --output outputs/wp_n32_controls/manifest.csv --limit 3 \
  --noise-sigma 0 --subsample-rho 0 --noise-realization 0 --clamp-val 10
# Then select/run the four rows for systems 1 and 24, IC sets 1 and 2, seed 42 via run_batch_cell.jl.
python analysis/scripts/aggregate/compare_phasec_controls.py \
  --candidate outputs/wp_n32_controls/tasks \
  --reference-c1 outputs/phase_c_campaign_221a3a7
```

3. Noisy/thinned through-check for system 1 at `(0.05,0.5)`, realization 1. Expected duration is one normal system-1 cell; the record `observed_data_sha256` must match the export index row.

```bash
julia --project=. --startup-file=no studies/regression/export_phase_c_data_conditions.jl \
  --systems 1 --ic-sets 1 --sigmas 0.05 --rhos 0.5 --realizations 1 \
  --output-dir outputs/phase_c_data_conditions/wp_n32_system1
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl \
  --output outputs/wp_n32_noisy_system1/manifest.csv --limit 3 \
  --noise-sigma 0.05 --subsample-rho 0.5 --noise-realization 1 --clamp-val 10
# Run the selected system-1 row via run_batch_cell.jl, then compare observed_data_sha256 with the export index.
```

4. Oracle refits: three cells at `10` compared to C-5, then the same three at `1000` and `Inf` as pass-through diagnostics. Expected duration is bounded by three C-5 refit cells per arm.

```bash
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl \
  --campaign paper1_phaseC_v1 --input outputs/phase_c_campaign_221a3a7/history.jsonl \
  --output-dir outputs/wp_n32_oracle_bound10 --limit 3 --clamp-val 10 --fresh
python analysis/scripts/aggregate/compare_phasec_controls.py \
  --candidate outputs/phase_c_campaign_221a3a7/tasks \
  --reference-c1 outputs/phase_c_campaign_221a3a7 \
  --candidate-oracle outputs/wp_n32_oracle_bound10/results.jsonl \
  --reference-oracle outputs/wp_n3_oracle_refit_phase_c
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl \
  --campaign paper1_phaseC_v1 --input outputs/phase_c_campaign_221a3a7/history.jsonl \
  --output-dir outputs/wp_n32_oracle_bound1000 --limit 3 --clamp-val 1000 --fresh
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl \
  --campaign paper1_phaseC_v1 --input outputs/phase_c_campaign_221a3a7/history.jsonl \
  --output-dir outputs/wp_n32_oracle_unbounded --limit 3 --clamp-val Inf --fresh
```

