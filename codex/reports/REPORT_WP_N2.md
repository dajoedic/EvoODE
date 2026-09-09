# WP-N2 Report - Pruning rule as a measurement instrument

## Commands

```powershell
python analysis/scripts/aggregate/aggregate_wp_n2_pruning_sensitivity.py --config analysis/configs/wp_n2_pruning_sensitivity.json
python analysis/scripts/aggregate/aggregate_wp_n2_pruning_sensitivity.py --input outputs/wp_n1_dim1_probe/history.jsonl
python analysis/scripts/aggregate/aggregate_wp_n2_pruning_sensitivity.py --config analysis/configs/wp_n2_pruning_sensitivity.json --input analysis/fixtures/wp_n2_missing_model_terms.jsonl
python -m py_compile analysis/scripts/aggregate/aggregate_wp_n2_pruning_sensitivity.py
```

The fixture command exits with:

```text
Error: record line 1 is missing model_terms
```

## Artifacts

- Script: `analysis/scripts/aggregate/aggregate_wp_n2_pruning_sensitivity.py`
- Config: `analysis/configs/wp_n2_pruning_sensitivity.json`
- Fixture: `analysis/fixtures/wp_n2_missing_model_terms.jsonl`
- Data CSV:
  - `analysis/data/wp_n2_pruning_sensitivity/wp_n2_pruning_evaluations.csv`
  - `analysis/data/wp_n2_pruning_sensitivity/wp_n2_pruning_switching_cells.csv`
- Table CSV/TEX:
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_current_decomposition.csv`
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_current_decomposition.tex`
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_rule_grid.csv`
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_rule_grid.tex`
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_raw_counterprobe.csv`
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_raw_counterprobe.tex`
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_switching_summary.csv`
  - `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_switching_summary.tex`

## Current-rule failure decomposition

The current rule is `max(1e-6, 1e-3 * max_abs)`. The input contains 102 exact cell-equations:
36 for the old basis and 66 for the constant basis. All are equation 1.

| basis | equation | n_cells | structure_hits | r2_gt_0_9_count | r2_gt_0_9_rate | extra_term_survives_cells | true_term_deleted_cells | true_term_never_found_cells | both_pruning_error_cells |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| constant_basis | 1 | 66 | 29 | 63 | 0.954545 | 12 | 4 | 21 | 1 |
| old_basis | 1 | 36 | 30 | 36 | 1.000000 | 0 | 0 | 6 | 0 |

This reproduces the stated acceptance numbers: old basis 30/36; constant basis 29/66 with 12
surviving extra terms and 4 deleted true terms. The old-basis remainder is 6 cells where a true term
was never found.

## Rule grid

The complete grid is written to `analysis/tables/wp_n2_pruning_sensitivity/wp_n2_rule_grid.csv`
and `.tex`. Each row carries the structure-hit count and the R2 > 0.9 count/rate.

Unique aggregate outcomes over the 24 rules:

| basis | structure_hits | extra_term_survives_cells | true_term_deleted_cells | true_term_never_found_cells | both_pruning_error_cells | n_rules |
|---|---:|---:|---:|---:|---:|---:|
| constant_basis | 18 | 0 | 27 | 21 | 5 | 4 |
| constant_basis | 18 | 0 | 30 | 18 | 5 | 1 |
| constant_basis | 21 | 24 | 0 | 21 | 0 | 1 |
| constant_basis | 25 | 20 | 0 | 21 | 0 | 1 |
| constant_basis | 27 | 3 | 18 | 18 | 5 | 1 |
| constant_basis | 27 | 3 | 18 | 18 | 6 | 3 |
| constant_basis | 29 | 3 | 13 | 21 | 5 | 4 |
| constant_basis | 29 | 12 | 4 | 21 | 1 | 4 |
| constant_basis | 30 | 15 | 0 | 21 | 0 | 5 |
| old_basis | 15 | 0 | 15 | 6 | 0 | 5 |
| old_basis | 27 | 0 | 3 | 6 | 0 | 8 |
| old_basis | 27 | 3 | 0 | 6 | 0 | 1 |
| old_basis | 30 | 0 | 0 | 6 | 0 | 10 |

The R2 > 0.9 metric is invariant over the pruning grid because pruning only changes the structural
classification: old basis 36/36, constant basis 63/66.

## Threshold-free counterprobe

| basis | equation | n_cells | raw_match_count | raw_match_rate | truth_subset_count | truth_subset_rate | r2_gt_0_9_count | r2_gt_0_9_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| constant_basis | 1 | 66 | 21 | 0.318182 | 45 | 0.681818 | 63 | 0.954545 |
| old_basis | 1 | 36 | 27 | 0.750000 | 30 | 0.833333 | 36 | 1.000000 |

The subset count is the upper bound for any pruning rule that only deletes already found terms:
45/66 for the constant basis and 30/36 for the old basis.

## Switching and stability

| basis | equation | n_cells | category_switch_cells | hit_status_switch_cells | category_stable_cells | hit_status_stable_cells |
|---|---:|---:|---:|---:|---:|---:|
| constant_basis | 1 | 66 | 33 | 21 | 33 | 45 |
| old_basis | 1 | 36 | 18 | 18 | 18 | 18 |

Across the full grid, 33/66 constant-basis cells and 18/36 old-basis cells change failure category.
The structure-hit status changes in 21/66 constant-basis cells and 18/36 old-basis cells. Aggregate
classification is stable over some local blocks of the grid, not over the full grid: for example,
the current mixed form at `rel = 1e-3` is unchanged for `abs` in `1e-8, 1e-6, 1e-4`, while `abs =
1e-2` changes both bases. Likewise, the mixed rules at `rel = 1e-1` are stable for the old basis
over all four absolute floors, while the constant basis changes at `abs = 1e-2`.

No threshold is recommended or selected here; the output records the dependence of the measurement
on the rule.
