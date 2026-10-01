# WP-S04 Report

Status: blocked (Umgebung, nicht Sache). Julia cannot be started in this Codex sandbox; even
`julia --version` failed with `Program 'julia.exe' failed to run: The file cannot be accessed by the system`.

## Implemented Files

- `studies/lookahead/wp_s04_stage_cap_noise_thinning.jl`
- `analysis/scripts/aggregate/summarize_wp_s04_stage_cap_noise.py`
- `analysis/tests/test_wp_s04_stage_cap_noise_summary.py`

## Julia Diagnostic Script

The Julia script is standalone and writes to its own output directory under
`outputs/studies/lookahead/wp_s04_stage_cap_noise_thinning`.

It includes:

- Phase-C exact-system selection with `dim <= 2`.
- Grid: `sigma in [0.0, 0.01, 0.02, 0.03, 0.04, 0.05]`, `rho in [0.0, 0.5]`.
- Realizations: `(sigma=0, rho=0)` uses realization `0`; the other 11 conditions use realizations `1,2,3`.
- Data construction through `apply_phase_c_data_condition`.
- Standard frozen policy through `LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...)`.
- Stage-cap reconstruction with `_cap_estimate_derivatives`, `_cap_splits`, `_cap_fit_eval`,
  `_cap_split_decision`, and `_cap_aggregate_split_decisions`.
- Loud mismatch control: reconstructed caps must match `estimate_stage_caps` for every row.
- Clean-data C-1 control: `(0,0)` caps must match `outputs/phase_c_campaign_221a3a7/history.jsonl`
  capped seed-42 records for every selected system and IC.
- F1 truncation flag: finite cap below the required true-support stage.
- F2 clean-vs-observed change class.
- F3 median residual and floor per stage over splits, plus usable split counts.
- F4 local cubic derivative-filter variance prediction using true `sigma^2 * x_clean^2`, estimated
  local residual variance, measured derivative error against `f(x_clean)`, and measured true-stage
  residual.

Expected full scope from `phase_c_support.json`: 21 systems, 31 equations per IC, 2 ICs, 34
conditions per cell, 2108 detail rows. The first two selected systems produce 136 detail rows.

## Commands for Claude

Short limit run:

```bash
julia --project=. studies/lookahead/wp_s04_stage_cap_noise_thinning.jl --limit 2
python analysis/scripts/aggregate/summarize_wp_s04_stage_cap_noise.py --input outputs/studies/lookahead/wp_s04_stage_cap_noise_thinning/stage_cap_noise_thinning_detail.csv --output-dir outputs/studies/lookahead/wp_s04_stage_cap_noise_thinning/summary
```

Full run:

```bash
julia --project=. studies/lookahead/wp_s04_stage_cap_noise_thinning.jl
python analysis/scripts/aggregate/summarize_wp_s04_stage_cap_noise.py --input outputs/studies/lookahead/wp_s04_stage_cap_noise_thinning/stage_cap_noise_thinning_detail.csv --output-dir outputs/studies/lookahead/wp_s04_stage_cap_noise_thinning/summary
```

Expected duration: the script performs no search and no optimization. The `--limit 2` run should be
well below 1 minute in a working Julia environment; the full 2108-row diagnostic is expected to be
seconds to a few minutes, depending on package load time and local BLAS.

## Python Summary

The Python script writes:

- `f1_safety.csv`
- `f2_behavior.csv`
- `f3_residual_quantiles.csv`
- `f3_floor_quantiles.csv`
- `f3_usable_split_means.csv`
- `f4_ratio_quantiles.csv`
- `f4_level_quantiles.csv`
- `summary.md`

It aborts if either loud control column is false:

- `rebuild_cap_matches_estimate`
- `clean_reference_matches_c1`

## Verification in Codex

Passed:

```bash
python -m pytest analysis/tests/test_wp_s04_stage_cap_noise_summary.py -q --basetemp .pytest_tmp_wp_s04
```

Result: `3 passed`.

Passed:

```bash
python -m py_compile analysis/scripts/aggregate/summarize_wp_s04_stage_cap_noise.py analysis/tests/test_wp_s04_stage_cap_noise_summary.py
```

Julia was not run because the sandbox cannot start `julia.exe`. Static checks covered includes,
internal Stage-Cap function names, Phase-C data-condition entry points, JSON serialization of split
decisions, and the clean/observed trajectory alignment needed for the subsampling path.

## 2026-10-02 Runtime-Fix Continuation

Claude's first `--limit 2` run stopped at line 447 with unqualified access to the non-exported
Stage-Cap internals. I corrected `studies/lookahead/wp_s04_stage_cap_noise_thinning.jl` so that
the script now uses the same module-qualified form as the neighboring `studies/lookahead/`
diagnostics:

- `EvoODE._cap_weights_from_richardson`
- `EvoODE._max_stage`
- `EvoODE._cap_splits`
- `EvoODE._cap_cumulative_stage_idxs`
- `EvoODE.build_design_matrix`
- `EvoODE._cap_stage_condition`
- `EvoODE._cap_fit_eval`
- `EvoODE._cap_split_decision`
- `EvoODE._cap_aggregate_split_decisions`
- `EvoODE._cap_estimate_derivatives`
- `EvoODE._cap_richardson_error_estimate`

Additional static hardening:

- Added `finite_median_or_inf` and used it for residual/floor medians so an all-nonfinite stage
  remains `Inf` instead of calling `median` on an empty vector.
- Rechecked the script for `using DifferentialEquations`; it does not contain it. `run_regression.jl`
  brings in `OrdinaryDiffEq`.
- Rechecked includes: `run_regression.jl` includes `src/EvoODE.jl` and
  `phase_c_data_condition.jl`; `phase_c_config.jl` provides the Phase-C helpers used by the script.
- Rechecked field access paths used in the diagnostic loop: `stage_caps` is skipped when absent,
  C-1 clean caps are length-checked against `dim`, and `expected_support` is only taken from exact
  Phase-C systems selected by `phase_c_exact_systems()`.

Continuation verification in Codex:

```bash
rg "(?<!EvoODE\\.)(?:_cap_weights_from_richardson|_max_stage|_cap_splits|_cap_cumulative_stage_idxs|build_design_matrix|_cap_stage_condition|_cap_fit_eval|_cap_split_decision|_cap_aggregate_split_decisions|_cap_estimate_derivatives|_cap_richardson_error_estimate)|DifferentialEquations" --pcre2 studies/lookahead/wp_s04_stage_cap_noise_thinning.jl
```

Result: no matches.

```bash
python -m pytest analysis/tests/test_wp_s04_stage_cap_noise_summary.py -q --basetemp .pytest_tmp_wp_s04
```

Result: `3 passed in 5.01s`.

## Open Acceptance Items

Open only because of environment:

- Execute the Julia `--limit 2` run.
- Execute the full Julia run.
- Run the Python summary on the produced full detail CSV.

## 2026-10-02 Clean-Trajectory Source Continuation

Claude's full run correctly stopped on the hard C-1 control:

```text
Clean cap mismatch against C-1 record for system 5, IC1: computed=[4], reference=[2]
```

Root cause fixed in `studies/lookahead/wp_s04_stage_cap_noise_thinning.jl`: `diagnostic_rows()`
no longer builds the clean trajectory from `_phase_c_solution_trajectory(...)`, i.e. the ODEBench
shipped solution. It now uses the same campaign path as `studies/regression/run_regression.jl` and
`apply_phase_c_data_condition`:

```julia
clean_traj = build_trajectory(phase_c_system(system_id), ic_set)
```

This means the clean caps, observed noisy/thinned trajectories, F4 clean-on-observed alignment, and
true RHS comparison are all derived from the self-integrated `Tsit5` trajectory on
`system[:t_grid]` with `abstol = reltol = 1e-9`. The hard C-1 reference check remains unchanged and
still aborts on any mismatch.

Static checks in Codex:

```bash
rg -n "_phase_c_solution_trajectory|_phase_c_dataset_rows|dataset_rows|solutions\\]" studies/lookahead/wp_s04_stage_cap_noise_thinning.jl
```

Result: no matches.

```bash
rg -n "(?<!EvoODE\\.)(?:_cap_weights_from_richardson|_max_stage|_cap_splits|_cap_cumulative_stage_idxs|build_design_matrix|_cap_stage_condition|_cap_fit_eval|_cap_split_decision|_cap_aggregate_split_decisions|_cap_estimate_derivatives|_cap_richardson_error_estimate)|DifferentialEquations" --pcre2 studies/lookahead/wp_s04_stage_cap_noise_thinning.jl
```

Result: no matches.

Python verification in Codex:

```bash
python -m pytest analysis/tests/test_wp_s04_stage_cap_noise_summary.py -q --basetemp .pytest_tmp_wp_s04
```

Result: `3 passed in 0.96s`.

```bash
python -m py_compile analysis/scripts/aggregate/summarize_wp_s04_stage_cap_noise.py analysis/tests/test_wp_s04_stage_cap_noise_summary.py
```

Result: passed.
