# REPORT WP-N26

## Changed files

- `analysis/scripts/aggregate/build_phasec_system_classification.py`
- `analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py`
- `analysis/tests/test_phasec_structure_metrics_n26.py`
- `analysis/data/paper1_phaseC_v1/system_classification.csv`
- `outputs/phase_c_dryrun_2026-09-25/agg/structure_n26/phasec_structure_metrics_by_equation.csv`
- `outputs/phase_c_dryrun_2026-09-25/agg/structure_n26/phasec_structure_metrics_by_cell.csv`
- `outputs/phase_c_dryrun_2026-09-25/agg/structure_n26/phasec_support_match_registry_discrepancies.csv`
- `studies/regression/merge_batch_records.jl`
- `SCRIPTS.md`

WP-N25 files already present in the working tree were not reverted. `SCRIPTS.md` was extended on top of the existing Phase-C chain.

## Coefficient error definition

For Phase-C exact systems, coefficient errors are computed per true term only:

`abs(found_coefficient - true_coefficient) / abs(true_coefficient)`

The found coefficients come from the registry `model_terms` JSON. The true coefficients are extracted from the classification `equation` expression using the Phase-C `variable_mapping` convention `x_i -> u{i+1}`. If a true term is missing from `model_terms`, its found coefficient is treated as `0.0`. Extra found terms are not included in the coefficient error; they are counted by the structural support metrics. Surrogate systems keep coefficient fields empty.

## Commands run

```powershell
python -m pytest analysis/tests/test_phasec_structure_metrics_n26.py -q --basetemp .pytest_tmp_n26
```

Result: 5 passed in 1.46 s on the final run.

```powershell
python analysis/scripts/aggregate/build_phasec_system_classification.py
```

Result: wrote `analysis/data/paper1_phaseC_v1/system_classification.csv`; 117 rows; 30 exact systems.

```powershell
python analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py --campaign paper1_phaseC_v1 --registry outputs/phase_c_dryrun_2026-09-25/run_registry.csv --classification analysis/data/paper1_phaseC_v1/system_classification.csv --output-dir outputs/phase_c_dryrun_2026-09-25/agg/structure_n26
```

Result: 885 cells; legacy `exact_support_match` agreement 805/885; raw agreement 885/885; pruned agreement 885/885.

Dry-run output checks:

- `phasec_support_match_registry_discrepancies.csv`: 0 rows.
- Exact cells identified by `n_true_terms_micro > 0`: 520.
- Exact cells with missing `coefficient_relative_error_mean`: 0.
- Exact cells with missing `coefficient_relative_error_max`: 0.
- Minimum exact-cell `n_coefficient_terms`: 1.

```powershell
python -m pytest analysis/tests/test_campaign_identity.py::test_structure_metric_paths_derive_from_campaign_and_allow_overrides analysis/tests/test_structure_metrics.py -q --basetemp .pytest_tmp_n26_more
```

Result: 7 passed in 1.36 s.

Phase-B bit-identity command:

```powershell
python analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py --output-dir outputs/wp_n26_phaseb_bitcheck
```

Result: 756 cells; registry agreement 716/756. Hash comparison against `analysis/data/paper1_phaseB_v1/`:

- `phaseb_structure_metrics_by_equation.csv`: match, SHA256 `65470B5549F318342AB573C8764B38C738D9469C7DE17AD580332473893E9C23`
- `phaseb_structure_metrics_by_cell.csv`: match, SHA256 `772D35C89DE2A21010B950B8B2ED14C3B7ECFD0B892BBF1283811277A29B0632`
- `phaseb_support_match_registry_discrepancies.csv`: match, SHA256 `E8D80DB35B08E38052A554157B270D703E548C5782CAC57464B989F46D42B423`

## Not verified

- Julia was not executed. The heartbeat protection in `studies/regression/merge_batch_records.jl` was written only, per protocol/environment constraints.
- Permutation tests, bootstraps, full test suite, cluster jobs, campaign runs, and regression runs were not started.
- Cleanup of local scratch output `outputs/wp_n26_phaseb_bitcheck/` was attempted but blocked by the command policy, so those three temporary Phase-B bitcheck CSVs may remain in the working tree.
