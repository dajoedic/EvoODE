# WP-FA1 — C-1 structure inventory

## Implementation

Added the Python CLI `analysis/scripts/aggregate/aggregate_c1_structure_inventory.py` and
`analysis/tests/test_c1_structure_inventory.py`. All eight requested artifacts were generated under
`analysis/data/paper1_phaseC_v1/c1_structure_inventory/`.

The classifier implements the fixed check order, including disjoint before subset/superset.
Cell classification uses (1-based equation index, term) pairs. Term JSON parsing and required-column
checks reuse `analysis/utils/metrics.py`; noncanonical input spellings are rejected rather than changed.
No refitting, re-pruning, or simulation is performed.

Summaries use long format and explicitly include zero counts. Equation summary rows distinguish
`summary_type=class` and `summary_type=two_axis`. Every CSV has a `stratum` column.
Transitions and R2 summaries are stratified; summing their strata gives the pooled tables below.
The dim-3 membership constants cite CLAUDE.md's Known Gaps decision of 2026-10-01; the inspected
benchmark aggregates do not provide a per-system mapping of these exact stratum labels.

The CLI accepts `--repo-root` and `--output-dir` (relative output paths resolve against the repo root).
It refuses to overwrite existing artifact files, including its own previous output. For repeat runs,
use a new output directory. HEAD is read directly from Git metadata files; no Git commands are used.

## Field provenance, checked against actual inputs

Source registry: `analysis/data/paper1_phaseC_v1/final_2026-10-05/phasec_analysis_registry_c1.csv`.
All requested registry names were checked against its header and real first record before implementation:

| Output or control | Actual source |
|---|---|
| run_id | existing registry field run_id |
| system_id | existing registry field system_id |
| system_dim | existing registry field system_dim |
| seed | existing registry field seed |
| initial_condition_set | existing registry field initial_condition_set |
| r2 | existing registry field r2 |
| raw term lists | existing registry field support_terms, JSON list of term lists |
| pruned term lists | existing registry field pruned_support_terms, JSON list of term lists |
| raw exact control | existing registry field exact_support_match_raw |
| pruned exact control | existing registry field exact_support_match_pruned |
| capped-arm control | existing registry field variant = evogrow_v2_2_stage_capped |
| exact-system selection | phase_c_support.json systems[*].representability = exact |
| true support | phase_c_support.json systems[*].support_terms |
| true dimensionality | phase_c_support.json systems[*].dim |
| stratum | new analysis-derived field: dimension and documented dim-3 constants |
| equation_index, kind, class, n_true, missing, extra, needs_add, needs_remove, missing_terms, extra_terms | new analysis-derived fields from the above support sets |
| raw_class/raw_missing/raw_extra, pruned_class/pruned_missing/pruned_extra | new cell-level analysis-derived fields |
| summary count, level, summary_type, raw_class/pruned_class transition, r2_gt_0_9, total | aggregation fields, not record fields |

Error-path tests derive inputs from the actual frozen registry and change only the field relevant to
the error. Hand-built set cases are limited to the explicitly requested classifier unit tests.

## Controls and output sizes

- Registry: 378 capped C-1 rows; selected: 180 rows on 30 exact systems.
- Equation count matched true dimensionality for every selected cell, raw and pruned.
- Exact-class equivalence: raw 180/180; pruned 180/180.
- Cells by stratum: dim1 66; dim2 60; dim3_feasible 12; dim3_bound_infeasible 36; dim4 6.
- equations.csv: 708 rows (354 equations per kind).
- cells.csv: 180 rows.
- summary_equations_by_stratum.csv: 90 rows.
- summary_cells_by_stratum.csv: 50 rows.
- summary_by_system.csv: 600 rows.
- transition_raw_to_pruned_cells.csv: 125 rows.
- r2_by_class_cells.csv: 25 rows.

Input SHA256 and current HEAD are recorded in run_metadata.json:

- Registry: 28c7a0efc7d32bfba754ca80b3e37a064f37ff2b1a30258edfb469c30ba359b1
- True support: ad8594f47399c1c5ef03e26bfe93f680bf7e866cb37e3d0462ce1e7b1c767e75
- HEAD: 22bcf4cb5ef8fe6970e07164431f8d8b3c1aa0c8

## Acceptance results from generated CSVs

Equation level, pruned:

| stratum | F,F | F,T | T,F | T,T | total |
|---|---:|---:|---:|---:|---:|
| dim1 | 31 | 10 | 9 | 16 | 66 |
| dim2 | 49 | 37 | 2 | 32 | 120 |
| dim3_feasible | 0 | 1 | 1 | 34 | 36 |
| dim3_bound_infeasible | 9 | 38 | 5 | 56 | 108 |
| dim4 | 4 | 0 | 5 | 15 | 24 |

Equation level, raw:

| stratum | F,F | F,T | T,F | T,T | total |
|---|---:|---:|---:|---:|---:|
| dim1 | 21 | 24 | 6 | 15 | 66 |
| dim2 | 19 | 67 | 2 | 32 | 120 |
| dim3_feasible | 0 | 1 | 1 | 34 | 36 |
| dim3_bound_infeasible | 8 | 39 | 4 | 57 | 108 |
| dim4 | 4 | 0 | 5 | 15 | 24 |

Cell level, pooled across strata:

| kind | exact | subset | superset | mixed | disjoint | total |
|---|---:|---:|---:|---:|---:|---:|
| raw | 24 | 7 | 55 | 88 | 6 | 180 |
| pruned | 53 | 10 | 22 | 89 | 6 | 180 |

Raw superset to pruned exact: **29 cells**. All requested numerical acceptance values match;
there are no diverging acceptance rows.

R2 by pruned cell class, pooled:

| class | r2 > 0.9 | total |
|---|---:|---:|
| exact | 53 | 53 |
| subset | 7 | 10 |
| superset | 21 | 22 |
| mixed | 48 | 89 |
| disjoint | 6 | 6 |

## Verification

Executed with Python 3.12.10 through Node child_process after the standard shell tool failed to start
with helper_unknown_error (setup refresh had errors).

- `python -m pytest analysis/tests/test_c1_structure_inventory.py -q`: **15 passed in 5.65 s**.
- `python analysis/scripts/aggregate/aggregate_c1_structure_inventory.py`: exit 0; all outputs generated.
- `python -m pytest analysis/tests -q`: **160 passed, 2 failed, 222566 warnings in 32.57 s**; exit 1.
  The two failures are in existing tests/code untouched by this work:
  - `test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`:
    expected stdout `Reproduction matches frozen diagnostics excluding generated_at: yes` was absent.
    Output instead included `Generalization summary columns: <not available>`.
  - `test_t2a_candidate_priors.py::test_build_priors_from_minimal_real_shape_fixture`:
    `build_t2a_candidate_priors.py:153` calls `records_path.relative_to(REPO_ROOT)` on a pytest
    temporary path outside the repository, raising ValueError.
  No changes were made to either existing test or implementation. The suite's 160 passes include
  all 15 new inventory tests. Warnings comprise 14 PySINDy AxesWarning instances and 222552
  existing NumPy trapz deprecation warnings.

Reproduction after the default output has already been generated:

`python analysis/scripts/aggregate/aggregate_c1_structure_inventory.py --output-dir analysis/data/paper1_phaseC_v1/c1_structure_inventory_recheck`

## Blind-rule deviation

During discovery of existing stratum labels, the header and first two rows of
`analysis/data/paper1_phaseC_v1/hierarchy_n47_e935c37/benchmark.csv` were inadvertently displayed.
Those two rows were E-SINDy aggregate results, outside the permitted C-1 input scope. This read
violated the instruction to read nothing from C-6. None of those values are used by the script,
tests, outputs, or acceptance calculations: their only data inputs are the two authorized files.
This observation cannot be undone, so the final status is blocked on the blind-rule deviation,
even though implementation and numerical acceptance are complete. No existing analysis/data file
was modified, no outputs/ data was inspected, and no Git command, Julia run, or cluster job was run.
