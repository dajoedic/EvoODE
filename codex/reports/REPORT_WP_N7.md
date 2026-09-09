# WP-N7 Report

## Implemented

Added reusable structural metrics to `analysis/utils/metrics.py`:

- `normalize_term_name`
- `term_set_metrics`
- `aggregate_equation_metrics`
- `coefficient_metrics`

Added scripts:

- `analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py`
- `analysis/scripts/aggregate/aggregate_representability_threeway.py`
- `analysis/scripts/aggregate/aggregate_wp_n1_coefficient_metrics.py`

Added tests:

- `analysis/tests/test_structure_metrics.py`

## Generated Files

Phase B:

- `analysis/data/paper1_phaseB_v1/phaseb_structure_metrics_by_equation.csv`
- `analysis/data/paper1_phaseB_v1/phaseb_structure_metrics_by_cell.csv`
- `analysis/data/paper1_phaseB_v1/phaseb_support_match_registry_discrepancies.csv`

Representability:

- `analysis/data/paper1_phaseB_v1/representability_threeway_by_equation.csv`
- `analysis/data/paper1_phaseB_v1/representability_threeway_by_system.csv`
- `analysis/data/paper1_phaseB_v1/representability_threeway_summary.csv`

WP-N1 coefficient metrics:

- `analysis/data/wp_n1_dim1_probe/wp_n1_structure_coefficient_metrics_by_equation.csv`
- `analysis/data/wp_n1_dim1_probe/wp_n1_structure_coefficient_metrics_by_cell.csv`

## Term Spelling Normalization

The normalizer strips whitespace, maps `**` to `^`, canonicalizes two-factor cross terms such as
`u2*u1` to `u1*u2`, and canonicalizes `sin(uN)` / `cos(uN)` spacing.

Audit on the real Phase-B sources found no spelling changes:

| source | normalization changes |
|---|---:|
| `run_registry.support_terms` | 0 |
| `system_classification.matched_basis_terms` | 0 |

The overlapping term spellings are therefore already identical. No source-specific mapping was
introduced.

## Phase-B Structural Metrics

Rows written:

| file | rows |
|---|---:|
| `phaseb_structure_metrics_by_equation.csv` | 1404 |
| `phaseb_structure_metrics_by_cell.csv` | 756 |

Strict structural exact support match from the stored `support_terms`:

| strict match | cells |
|---|---:|
| `True` | 142 |
| `False` | 614 |

Coefficient fields for Phase B are null, as required:

| field | all null |
|---|---:|
| equation-level `coefficient_relative_error_mean` | true |
| cell-level `coefficient_relative_error_mean` | true |

## Registry Support-Match Reproduction

Agreement between the new strict structural exact match, with legacy null handling, and
`run_registry.exact_support_match`:

```text
716 / 756
```

The 40 disagreements are all `registry=True`, strict structural match `False`, `missing=0`, and
`extra>0`. The stored `support_terms` therefore contain all true terms plus extras, while the legacy
registry column still marks the cell as an exact support match.

| run_id | system_id | comparison | counts |
|---|---:|---|---|
| `61_evogrow_v2_2_stage_capped_pretune_on_11_1_42` | 11 | registry=True strict=False | missing=0, extra=2 |
| `62_evogrow_v2_2_stage_capped_pretune_on_11_1_123` | 11 | registry=True strict=False | missing=0, extra=2 |
| `63_evogrow_v2_2_stage_capped_pretune_on_11_1_7` | 11 | registry=True strict=False | missing=0, extra=2 |
| `157_evogrow_v2_2_stage_capped_pretune_on_27_1_42` | 27 | registry=True strict=False | missing=0, extra=3 |
| `158_evogrow_v2_2_stage_capped_pretune_on_27_1_123` | 27 | registry=True strict=False | missing=0, extra=4 |
| `160_evogrow_v2_2_stage_capped_pretune_on_27_2_42` | 27 | registry=True strict=False | missing=0, extra=6 |
| `161_evogrow_v2_2_stage_capped_pretune_on_27_2_123` | 27 | registry=True strict=False | missing=0, extra=6 |
| `162_evogrow_v2_2_stage_capped_pretune_on_27_2_7` | 27 | registry=True strict=False | missing=0, extra=6 |
| `187_evogrow_v2_2_stage_capped_pretune_on_32_1_42` | 32 | registry=True strict=False | missing=0, extra=5 |
| `188_evogrow_v2_2_stage_capped_pretune_on_32_1_123` | 32 | registry=True strict=False | missing=0, extra=5 |
| `189_evogrow_v2_2_stage_capped_pretune_on_32_1_7` | 32 | registry=True strict=False | missing=0, extra=5 |
| `223_evogrow_v2_2_stage_capped_pretune_on_38_1_42` | 38 | registry=True strict=False | missing=0, extra=7 |
| `224_evogrow_v2_2_stage_capped_pretune_on_38_1_123` | 38 | registry=True strict=False | missing=0, extra=7 |
| `225_evogrow_v2_2_stage_capped_pretune_on_38_1_7` | 38 | registry=True strict=False | missing=0, extra=7 |
| `439_evogrow_v2_2_stage_capped_pretune_off_11_1_42` | 11 | registry=True strict=False | missing=0, extra=2 |
| `440_evogrow_v2_2_stage_capped_pretune_off_11_1_123` | 11 | registry=True strict=False | missing=0, extra=2 |
| `441_evogrow_v2_2_stage_capped_pretune_off_11_1_7` | 11 | registry=True strict=False | missing=0, extra=2 |
| `518_evogrow_v2_2_stage_capped_pretune_off_24_1_123` | 24 | registry=True strict=False | missing=0, extra=1 |
| `519_evogrow_v2_2_stage_capped_pretune_off_24_1_7` | 24 | registry=True strict=False | missing=0, extra=1 |
| `520_evogrow_v2_2_stage_capped_pretune_off_24_2_42` | 24 | registry=True strict=False | missing=0, extra=1 |
| `521_evogrow_v2_2_stage_capped_pretune_off_24_2_123` | 24 | registry=True strict=False | missing=0, extra=1 |
| `522_evogrow_v2_2_stage_capped_pretune_off_24_2_7` | 24 | registry=True strict=False | missing=0, extra=1 |
| `539_evogrow_v2_2_stage_capped_pretune_off_27_2_123` | 27 | registry=True strict=False | missing=0, extra=4 |
| `540_evogrow_v2_2_stage_capped_pretune_off_27_2_7` | 27 | registry=True strict=False | missing=0, extra=6 |
| `547_evogrow_v2_2_stage_capped_pretune_off_29_1_42` | 29 | registry=True strict=False | missing=0, extra=5 |
| `548_evogrow_v2_2_stage_capped_pretune_off_29_1_123` | 29 | registry=True strict=False | missing=0, extra=5 |
| `549_evogrow_v2_2_stage_capped_pretune_off_29_1_7` | 29 | registry=True strict=False | missing=0, extra=4 |
| `562_evogrow_v2_2_stage_capped_pretune_off_31_2_42` | 31 | registry=True strict=False | missing=0, extra=2 |
| `563_evogrow_v2_2_stage_capped_pretune_off_31_2_123` | 31 | registry=True strict=False | missing=0, extra=3 |
| `564_evogrow_v2_2_stage_capped_pretune_off_31_2_7` | 31 | registry=True strict=False | missing=0, extra=2 |
| `565_evogrow_v2_2_stage_capped_pretune_off_32_1_42` | 32 | registry=True strict=False | missing=0, extra=5 |
| `566_evogrow_v2_2_stage_capped_pretune_off_32_1_123` | 32 | registry=True strict=False | missing=0, extra=5 |
| `567_evogrow_v2_2_stage_capped_pretune_off_32_1_7` | 32 | registry=True strict=False | missing=0, extra=8 |
| `570_evogrow_v2_2_stage_capped_pretune_off_32_2_7` | 32 | registry=True strict=False | missing=0, extra=2 |
| `601_evogrow_v2_2_stage_capped_pretune_off_38_1_42` | 38 | registry=True strict=False | missing=0, extra=7 |
| `602_evogrow_v2_2_stage_capped_pretune_off_38_1_123` | 38 | registry=True strict=False | missing=0, extra=7 |
| `603_evogrow_v2_2_stage_capped_pretune_off_38_1_7` | 38 | registry=True strict=False | missing=0, extra=7 |
| `604_evogrow_v2_2_stage_capped_pretune_off_38_2_42` | 38 | registry=True strict=False | missing=0, extra=2 |
| `605_evogrow_v2_2_stage_capped_pretune_off_38_2_123` | 38 | registry=True strict=False | missing=0, extra=1 |
| `606_evogrow_v2_2_stage_capped_pretune_off_38_2_7` | 38 | registry=True strict=False | missing=0, extra=1 |

## Three-Way Representability

Rows written:

| file | rows |
|---|---:|
| `representability_threeway_by_equation.csv` | 234 |
| `representability_threeway_by_system.csv` | 126 |
| `representability_threeway_summary.csv` | 6 |

System counts:

| basis | fully | partially | non |
|---|---:|---:|---:|
| `default_staged_polynomial_basis` | 20 | 39 | 4 |
| `staged_polynomial_basis_with_constant` | 30 | 31 | 2 |

## WP-N1 Coefficient Metrics

Rows written:

| file | rows |
|---|---:|
| `wp_n1_structure_coefficient_metrics_by_equation.csv` | 102 |
| `wp_n1_structure_coefficient_metrics_by_cell.csv` | 102 |

Coefficient coverage:

| quantity | value |
|---|---:|
| records read from `outputs/wp_n1_dim1_probe/history.jsonl` | 132 |
| metric cells written | 102 |
| cells with non-null coefficient mean | 93 |
| shared correctly found coefficient terms | 165 |

The skipped 30 WP-N1 records have no `wp_n1_expected_support_terms`. The 9 cells with null
coefficient error have no correctly found term shared with the true support.

## Commands

Recompute Phase-B structural metrics:

```powershell
python analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py
```

Recompute three-way representability:

```powershell
python analysis/scripts/aggregate/aggregate_representability_threeway.py
```

Recompute WP-N1 coefficient metrics:

```powershell
python analysis/scripts/aggregate/aggregate_wp_n1_coefficient_metrics.py
```

Run the new tests only:

```powershell
python -m pytest analysis/tests/test_structure_metrics.py
```

Run all analysis tests used in this session:

```powershell
python -m pytest analysis/tests/test_structure_metrics.py analysis/tests/test_analysis_variant_visibility.py analysis/tests/test_evaluate_hypotheses_dataset_classification.py
```

Result:

```text
10 passed in 1.95s
```

## Acceptance Status

Blocked on acceptance point 1 as written: strict exact support match from the stored
`run_registry.support_terms` agrees with legacy `run_registry.exact_support_match` in 716/756 cells,
not 756/756. The discrepancies are fully materialized in
`phaseb_support_match_registry_discrepancies.csv` and listed above.
