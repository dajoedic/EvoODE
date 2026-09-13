# WP-N16 Report

## Result

Implemented the Phase-C configuration package and the executable Python changes. Julia execution remains blocked in this Codex environment per `codex/CODEX_PROTOCOL.md`; Claude must run the Julia commands below.

## Built

- Parameterized `studies/regression/derive_phase_b_support.jl` with `--basis` and `--output`. The default path and basis still target `phase_b_support.json` with `default_staged_polynomial_basis`; generated payloads now declare `basis_name`.
- Added `studies/regression/phase_c_config.jl` with campaign id `paper1_phaseC_v1`, canonical basis `staged_polynomial_basis_with_constant`, `max_fit_attempts = 3`, Phase-C variants with explicit `basis_name`, load-time basis validation, and `phase_c_fingerprint()`.
- Added `studies/regression/generate_phase_c_manifest.jl`. C-1 and C-2 rows are adjacent per `(system, IC set, seed)` so an early abort hits both paired arms evenly. C-3 rows are generated only for exact systems from `phase_c_support.json`.
- Extended `studies/regression/run_batch_cell.jl` to route `paper1_phaseC_v1` manifest rows through Phase-C config lazily.
- Extended `studies/regression/run_regression.jl` with per-variant `max_fit_attempts` and a new `executed_levels` record field derived from `sum(meta.stage_level_counts)`, separate from configured `n_levels`.
- Extended `analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py` to carry `total_parameter_fit_attempts`, `basis_name`, `model_terms`, `max_fit_attempts`, and `executed_levels`.
- Extended `analysis/scripts/aggregate/verify_campaign_registry.py` with `--phase-c-support-table`; Phase-C row counts, per-condition counts, exact rows, and surrogate rows are derived from the support table instead of duplicated constants.

## Column Origins

| Column | Origin |
|---|---|
| `executed_levels` | New Julia record field in `run_regression.jl`; computed from executed `stage_level_counts`, not `n_levels`. |
| `total_parameter_fit_attempts` | Existing Julia record field; now carried through registry conversion. |
| `total_parameter_fits` | Existing Julia record field. |
| `total_loss_evals` | Existing Julia record field. |
| `total_ode_solves` | Existing Julia record field. |
| `final_stage` | Existing Julia record field. |
| `system_expected_stage` | Registry field converted from record `expected_stage`, which Phase C derives from `phase_c_support.json`. |
| `exact_support_match_raw` | Existing Julia record field from WP-N12. |
| `exact_support_match_pruned` | Existing Julia record field from WP-N12. |
| `exact_support_match_definition` | Existing Julia record field from WP-N12. |
| `structural_f1` | Analysis pipeline, from `analysis/utils/metrics.py` and structure-metric aggregation. |
| `term_precision` | Analysis pipeline, from `analysis/utils/metrics.py` and structure-metric aggregation. |
| `term_recall` | Analysis pipeline, from `analysis/utils/metrics.py` and structure-metric aggregation. |
| `coefficient_relative_error_mean` | Analysis pipeline, from `analysis/utils/metrics.py` and structure-metric aggregation. |

No structural metric was reimplemented in Julia.

## Python Verification

- `python -m py_compile analysis/scripts/aggregate/verify_campaign_registry.py analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py` -> exit 0.
- `python -m pytest analysis/tests/test_campaign_identity.py analysis/tests/test_phasec_cap_ablation.py` with workspace-local basetemp -> 13 passed, exit 0.
- `python analysis/scripts/aggregate/verify_campaign_registry.py --input __missing_registry__.csv` -> exit 1 as expected.
- `python analysis/scripts/aggregate/verify_campaign_registry.py --campaign paper1_phaseB_v1 --input experiments/paper1_phaseB_v1/run_registry.csv` -> exit 0, 756 rows verified.

## Claude Commands

Support table:

```bash
julia --project=. studies/regression/derive_phase_b_support.jl --basis staged_polynomial_basis_with_constant --output studies/regression/phase_c_support.json
```

Support-table check:

```bash
julia --project=. studies/regression/derive_phase_b_support.jl --basis staged_polynomial_basis_with_constant --output studies/regression/phase_c_support.json --check
```

Manifest:

```bash
julia --project=. studies/regression/generate_phase_c_manifest.jl --all-dimensions
```

Smoke test, one manifest cell only after the manifest exists:

```bash
julia --project=. studies/regression/run_batch_cell.jl 1 --manifest outputs/studies/regression/phase_c/manifest.csv --output-dir outputs/studies/regression/phase_c/smoke_tasks
```

Registry verification after records are converted:

```bash
python analysis/scripts/aggregate/verify_campaign_registry.py --campaign paper1_phaseC_v1 --input experiments/paper1_phaseC_v1/run_registry.csv --phase-c-support-table studies/regression/phase_c_support.json --expected-git-hash <git> --expected-config-fingerprint <phase_c_fingerprint> --expected-stage-cap-behavior-fingerprint <stage_cap_fingerprint>
```

## Blocked Items

Julia code was not executed by Codex because Julia is blocked in this environment. Open Julia acceptance points for Claude: generate `phase_c_support.json`, print the canonical exact/surrogate counts, generate the manifest and its per-arm row counts, and run the smoke cell.
