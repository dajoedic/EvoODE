# WP-E1 Evidence Output Guard

## Affected Scripts

The scan covered `studies/**/*.jl` for Markdown reports and CSV outputs under `docs/` or `outputs/`.

| script | writes | previous overwrite risk |
|---|---|---|
| `studies/lookahead/audit_exact_stage_cap_horizons.jl` | `docs/wp_c1_stage_cap_horizon_audit.md`, CSV under `outputs/studies/lookahead/audit_exact_stage_cap_horizons` | known: later WP-C2/WP-C4 acceptance runs could overwrite the WP-C1 evidence document |
| `studies/lookahead/diagnose_stage_cap_failures.jl` | `docs/wp_c2_stage_cap_failure_diagnosis.md`, 3 CSVs under `outputs/studies/lookahead/diagnose_stage_cap_failures` | possible: fixed WP-C2 report path |
| `studies/lookahead/measure_dataset_grid_caps.jl` | `docs/wp_g1_dataset_grid_caps.md`, CSV under `outputs/studies/lookahead/wp_g1` | possible: fixed WP-G1 report path |
| `studies/lookahead/wp_c4_stage_cap_doubt_band_report.jl` | `docs/wp_c4_stage_cap_doubt_band.md`, 2 CSVs under `outputs/studies/lookahead/wp_c4_stage_cap_doubt_band` | possible: fixed WP-C4 report path |
| `studies/lookahead/stage_potential_probe.jl` | 2 CSVs and `report.md` under `outputs/studies/lookahead/stage_potential_probe` | possible only if the closed probe is reused for a later WP without an explicit output dir |
| `studies/lookahead/derivative_estimator_probe.jl` | 2 CSVs and `report.md` under `outputs/studies/lookahead/derivative_estimator_probe` | possible only if reused for a later WP without an explicit output dir |
| `studies/lookahead/floor_gated_probe.jl` | 3 CSVs and `report.md` under `outputs/studies/lookahead/floor_gated_probe` | possible only if reused for a later WP without an explicit output dir |
| `studies/linesearch/diagnose_linesearch.jl` | CSV under `outputs/studies/linesearch/wp_f1` | possible: fixed WP-F1 output dir |
| `studies/linesearch/diagnose_coupled_budget.jl` | CSV under `outputs/studies/linesearch/wp_f2` | possible: fixed WP-F2 output dir |
| `studies/linesearch/replay_budget_20000.jl` | CSV under `outputs/studies/linesearch/wp_f3` | possible: fixed WP-F3 output dir |
| `studies/debug/compare_screening_variant.jl` | 2 CSVs under `outputs/studies/debug/compare_screening_variant` | possible only on repeated debug runs |
| `studies/generalization/generalization_study.jl` | 2 CSVs under `outputs/studies/generalization` | possible only on repeated closed-study runs |
| `studies/numerics/solver_tolerance_noise_floor.jl` | 2 CSVs under `outputs/studies/numerics/solver_tolerance_noise_floor` | possible only on repeated closed-study runs |
| `studies/numerics/system26_tolerance_screening.jl` | 3 CSVs under `outputs/studies/numerics/system26_tolerance_screening` | possible only on repeated closed-study runs |
| `studies/profiling/profile_eval_cost.jl` | CSV under `outputs/studies/profiling/profile_eval_cost` | possible only on repeated profiling runs |
| `studies/profiling/profile_init.jl` | 2 CSVs under `outputs/studies/profiling` | possible only on repeated profiling runs |
| `studies/regression/generate_manifest.jl` | `manifest.csv` and optional dimension index under `outputs/studies/regression/wp_b2` | possible: default manifest path |
| `studies/regression/generate_phase_b_manifest.jl` | Phase-B `manifest.csv` and index CSV-adjacent lists under `outputs/studies/regression/phase_b` | possible: default manifest path |

`studies/gate2_do_or_die/readout.jl` and `studies/phase1_diag/run_phase1_diag.jl` also write report-like artifacts under `outputs/`; their output directories now use the same guard even though they are not CSV/report-to-`docs` cases.

## Implementation

Added `studies/output_path_guard.jl`.

Default behavior:

- If `--output-dir <dir>` or `--report <path>` / `--output <path>` is passed, the caller has supplied the target.
- If no target is passed and the old default directory is empty or absent, the old default path is used.
- If no target is passed and the old default file exists or output directory already contains files, a timestamp-suffixed sibling is used.

This keeps existing direct invocations working and avoids silent destruction on second runs. `SCRIPTS.md` documents the new optional target flags and the default fallback.

## Second-Run Proof

Protected document:

`docs/wp_c1_stage_cap_horizon_audit.md`

SHA256 before rerun:

`9DEC5BCA52B3D0792DF4DF0D49D30F020B1962E86FA805BDC2843416014D916B`

Command:

```text
julia --project=. --startup-file=no studies/lookahead/audit_exact_stage_cap_horizons.jl
```

Script output targets:

- Report: `docs/wp_c1_stage_cap_horizon_audit_20260819_195440.md`
- CSV: `outputs/studies/lookahead/audit_exact_stage_cap_horizons_20260819_195440/exact_stage_cap_horizon_audit.csv`

Run facts:

- Rows: `320`
- Truncated systems at horizon 2: `2`
- Selected horizon: `3`
- Runtime: `46 s`

SHA256 after rerun:

`9DEC5BCA52B3D0792DF4DF0D49D30F020B1962E86FA805BDC2843416014D916B`

New report SHA256:

`C0B2D6D0E7F88170B3502860B1D8C413E56838B259CF575059D69B0FF905D00A`

New CSV SHA256:

`4F84952453560443A21EFB8CFA85D551ECA7DEA612B9521537911FF11C416A28`

`docs/wp_c4_stage_cap_horizon_audit.md` SHA256 after the work:

`9FA83A86F8993813D1BB8E6AFDA23C9F169AB40037FAC72ADE1E95EBD5FFD850`

## Fingerprints

Local check command:

```text
julia --project=. --startup-file=no -e "include(\"studies/regression/run_regression.jl\"); include(\"studies/regression/phase_b_config.jl\"); println(config_fingerprint()); println(phase_b_fingerprint()); println(EvoODE.stage_cap_behavior_fingerprint())"
```

Observed values:

| function | value |
|---|---|
| `config_fingerprint()` | `1d0ccf8d53c6576d` |
| `phase_b_fingerprint()` | `e361a2af49366670` |
| `stage_cap_behavior_fingerprint()` | `61b6548ef0014593` |

The acceptance-critical fingerprints `config_fingerprint()` and `stage_cap_behavior_fingerprint()` match the required values `1d0ccf8d53c6576d` and `61b6548ef0014593`.

## Not Changed

- No cluster jobs, campaign runs, regression runs, or probing runs were started.
- No manifest generation was run.
- No cap logic, policy constants, or fingerprint-relevant code was changed.
- `docs/wp_c1_stage_cap_horizon_audit.md` was not modified.
- `docs/wp_c4_stage_cap_horizon_audit.md` was not modified.
- Nothing was staged, committed, or pushed.
