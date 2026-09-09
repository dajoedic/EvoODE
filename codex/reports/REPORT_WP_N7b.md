# WP-N7b Report

## Implemented

Added:

- `analysis/utils/support_match_definition.py`
- `analysis/scripts/aggregate/aggregate_phaseb_raw_pruned_support_comparison.py`
- `analysis/tests/test_phaseb_support_acceptance.py`
- `analysis/data/paper1_phaseB_v1/phaseb_raw_pruned_support_comparison.csv`

Existing WP-N7 files were not removed or overwritten by the new raw/pruned comparison script.

## Phase-B Recall Acceptance Test

The test `test_phaseb_pruned_match_implies_no_missing_true_terms` recomputes Phase-B structure
metrics into a temporary workspace directory and validates the directed relationship:

```text
pruned_match == True implies n_missing_true_terms == 0
```

Observed counts:

| quantity | cells |
|---|---:|
| exact Phase-B cells | 240 |
| pruned matches | 110 |
| pruned matches with missing true terms | 0 |
| exact cells with missing true terms equal to 0 | 119 |

Negative control:

```powershell
python -c "... monkeypatch aggregate_phaseb_structure_metrics.term_set_metrics to add one missing true term ..."
```

Result:

```text
negative control failed as expected
```

## Raw Versus Pruned Support

Generated:

```text
analysis/data/paper1_phaseB_v1/phaseb_raw_pruned_support_comparison.csv
```

Full table:

| aggregation_level | system_dim | condition | initial_condition_set | n_exact_cells | raw_exact_support_match_count | pruned_exact_support_match_count | pruning_rescued_support_match_count |
|---|---:|---|---:|---:|---:|---:|---:|
| overall |  |  |  | 240 | 70 | 110 | 40 |
| by_dimension | 1 |  |  | 72 | 51 | 57 | 6 |
| by_dimension | 2 |  |  | 108 | 19 | 53 | 34 |
| by_dimension | 3 |  |  | 48 | 0 | 0 | 0 |
| by_dimension | 4 |  |  | 12 | 0 | 0 | 0 |
| by_condition |  | pretune_off |  | 120 | 34 | 60 | 26 |
| by_condition |  | pretune_on |  | 120 | 36 | 50 | 14 |
| by_initial_condition_set |  |  | 1 | 120 | 37 | 62 | 25 |
| by_initial_condition_set |  |  | 2 | 120 | 33 | 48 | 15 |
| by_dimension_condition_initial_condition_set | 1 | pretune_off | 1 | 18 | 15 | 18 | 3 |
| by_dimension_condition_initial_condition_set | 1 | pretune_off | 2 | 18 | 12 | 12 | 0 |
| by_dimension_condition_initial_condition_set | 1 | pretune_on | 1 | 18 | 12 | 15 | 3 |
| by_dimension_condition_initial_condition_set | 1 | pretune_on | 2 | 18 | 12 | 12 | 0 |
| by_dimension_condition_initial_condition_set | 2 | pretune_off | 1 | 27 | 4 | 15 | 11 |
| by_dimension_condition_initial_condition_set | 2 | pretune_off | 2 | 27 | 3 | 15 | 12 |
| by_dimension_condition_initial_condition_set | 2 | pretune_on | 1 | 27 | 6 | 14 | 8 |
| by_dimension_condition_initial_condition_set | 2 | pretune_on | 2 | 27 | 6 | 9 | 3 |
| by_dimension_condition_initial_condition_set | 3 | pretune_off | 1 | 12 | 0 | 0 | 0 |
| by_dimension_condition_initial_condition_set | 3 | pretune_off | 2 | 12 | 0 | 0 | 0 |
| by_dimension_condition_initial_condition_set | 3 | pretune_on | 1 | 12 | 0 | 0 | 0 |
| by_dimension_condition_initial_condition_set | 3 | pretune_on | 2 | 12 | 0 | 0 | 0 |
| by_dimension_condition_initial_condition_set | 4 | pretune_off | 1 | 3 | 0 | 0 | 0 |
| by_dimension_condition_initial_condition_set | 4 | pretune_off | 2 | 3 | 0 | 0 | 0 |
| by_dimension_condition_initial_condition_set | 4 | pretune_on | 1 | 3 | 0 | 0 | 0 |
| by_dimension_condition_initial_condition_set | 4 | pretune_on | 2 | 3 | 0 | 0 | 0 |

Control totals:

```text
exact=240, pruned=110, raw=70, rescued=40
```

## exact_support_match Definition Guard

`infer_exact_support_match_definition` maps Phase-A registry metadata to
`raw_support_terms_exact_match` and Phase-B registry metadata to
`pruned_support_terms_exact_match`.

`require_compatible_exact_support_match_definitions` raises `ValueError` when registries with
different definitions are passed to one analysis path.

Tested cases:

| case | behavior |
|---|---|
| two Phase-B registries | accepted as `pruned_support_terms_exact_match` |
| Phase-A plus Phase-B registry | fails with both definitions named in the error |
| explicit metadata column | accepted and normalized |

Phase A was not re-evaluated or migrated.

## Commands

Generate raw/pruned comparison:

```powershell
python analysis/scripts/aggregate/aggregate_phaseb_raw_pruned_support_comparison.py
```

Result:

```text
Wrote analysis\data\paper1_phaseB_v1\phaseb_raw_pruned_support_comparison.csv
Rows: 25
Totals: exact=240, pruned=110, raw=70, rescued=40
```

Run new tests:

```powershell
python -m pytest analysis/tests/test_phaseb_support_acceptance.py
```

Result:

```text
5 passed in 0.98s
```

Run all analysis tests:

```powershell
python -m pytest analysis/tests --basetemp .pytest_tmp_wp_n7b_all
```

Result:

```text
15 passed in 2.47s
```

The `--basetemp` argument keeps pytest temporary files inside the workspace.

## Acceptance Status

Done.
