# WP-T1c Report

## Scope

Implemented `stlsq_path` as a third ranking method in `analysis/exploratory/term_relevance/term_relevance.py` and added the WP-T1c runner `analysis/scripts/aggregate/run_wp_t1c_prior_generator.py`.

No files under `src/`, `experiments/`, `studies/`, `k8s/`, `containers/`, or `benchmarks/` were modified. WP-T1c outputs were written only under:

- `analysis/data/wp_t1c_prior_generator/`
- `analysis/figures/wp_t1c_prior_generator/`

## STLSQ Path

The fixed threshold grid used in the final run was:

`[0.0, 1e-12, 1e-11, 1e-10, 1e-09, 1e-08, 1e-07, 1e-06, 1e-05, 0.0001, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0, 100000000.0]`

The initial upper end `1e4` did not remove all terms in the full run, so the declared grid was extended upward to `1e8` before accepting outputs. This was an abdeckung fix, not a performance-tuning step.

Coverage check: `stlsq_threshold_coverage.csv` has 2458 unique STLSQ coverage rows. All 2458 rows start with the full active library at threshold `0.0`, and all 2458 rows end with active count `0` at `1e8`.

Tie-break rule: terms with the same dropout threshold are ordered by the absolute standardized coefficient at the last threshold where both were active, then by ascending basis index.

## Outputs

Final full run:

- `records.csv`: 5192 rows
- `aggregate_by_configuration_dimension.csv`: 352 rows
- `paired_method_comparison_by_dimension.csv`: 176 rows
- `stlsq_threshold_coverage.csv`: 2458 rows
- `generator_decision.json`: written
- `run_metadata.json`: written
- `paired_difference_by_dimension.png`: written

## Decision Cell

Decision cell: `signal=weak`, `sigma_rel=0.0`, `noise_replicate=0`, `ic_strategy=ic1`, dimensions 2 and 3. Denominator: 18 systems, 44 equations.

Candidate values:

| method | median n_false_before_last_true | count <= 3 | rate <= 3 |
|---|---:|---:|---:|
| forward | 0.0 | 37 / 44 | 0.840909 |
| stlsq_path | 0.0 | 40 / 44 | 0.909091 |

Primary direction by the predeclared tie-break is `stlsq_path` because medians tie and its `<= 3` rate is higher.

Replication condition on `ic2`, same denominator of 44 equations:

| method | median n_false_before_last_true | count <= 3 | rate <= 3 |
|---|---:|---:|---:|
| forward | 0.0 | 39 / 44 | 0.886364 |
| stlsq_path | 0.0 | 38 / 44 | 0.863636 |

The direction flips on `ic2`, so the final result is `no_winner`. Per the predeclared rule, `forward` remains the WP-T2a prioritizer.

## Paired Differences

Differences are `stlsq_path - forward`; negative values favor `stlsq_path`.

Decision-cell paired distributions:

| signal | ic | dim | n_pairs | q0 | q10 | q25 | q50 | q75 | q90 | q100 | diff <= 0 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| weak | ic1 | 2 | 20 | -5.0 | -1.2 | -1.0 | 0.0 | 0.0 | 3.0 | 3.0 | 16 / 20 |
| weak | ic1 | 3 | 24 | -14.0 | -6.4 | -2.0 | 0.0 | 0.0 | 2.7 | 9.0 | 20 / 24 |
| weak | ic2 | 2 | 20 | -8.0 | -2.1 | -1.25 | 0.0 | 0.0 | 3.2 | 5.0 | 16 / 20 |
| weak | ic2 | 3 | 24 | -6.0 | -2.7 | -2.0 | 0.0 | 0.0 | 1.4 | 8.0 | 21 / 24 |

Although many paired differences are non-positive, the predeclared decision is based on median, then `<= 3` rate, and then replication direction. The `<= 3` direction does not replicate.

## fd Arm

The `fd` arm used `explicit_intercept=True` for both methods. At `sigma_rel=0.0`, `fd` does not show a stable advantage for `stlsq_path` on the canonical basis:

| ic | dim | n_pairs | forward median | stlsq median | forward <= 3 | stlsq <= 3 |
|---|---:|---:|---:|---:|---:|---:|
| ic1 | 1 | 11 | 1.0 | 0.0 | 10 / 11 | 11 / 11 |
| ic1 | 2 | 20 | 0.0 | 0.5 | 16 / 20 | 17 / 20 |
| ic1 | 3 | 24 | 0.0 | 0.5 | 20 / 24 | 14 / 24 |
| ic1 | 4 | 4 | 7.5 | 11.5 | 2 / 4 | 0 / 4 |
| ic2 | 1 | 11 | 1.0 | 0.0 | 10 / 11 | 9 / 11 |
| ic2 | 2 | 20 | 0.0 | 0.5 | 18 / 20 | 15 / 20 |
| ic2 | 3 | 24 | 0.0 | 0.0 | 23 / 24 | 17 / 24 |
| ic2 | 4 | 4 | 10.0 | 18.5 | 2 / 4 | 0 / 4 |

This answers the library-versus-selection-rule question for this work package: putting STLSQ on the canonical basis does not produce a replicated ranking winner over forward. Therefore the SINDy gap from WP-T1b is not resolved by simply swapping the ranking rule to STLSQ on our basis.

## Tests

Commands run:

```text
$env:TMP=(Resolve-Path .tmp_pytest); $env:TEMP=$env:TMP; python -m pytest analysis/tests/test_wp_t1_term_relevance.py analysis/tests/test_wp_t1b_standalone_ranking.py analysis/tests/test_wp_t1c_prior_generator.py
python analysis/scripts/aggregate/run_wp_t1c_prior_generator.py
```

Test result: 15 passed. The pytest run emitted only `np.trapz` deprecation warnings from the existing weak-design builder.

The regression guard checks the existing WP-T1 and WP-T1b reference artifacts by SHA-256:

- `analysis/data/wp_t1_term_relevance/gate_decision.json`
- `analysis/data/wp_t1_term_relevance/aggregate_by_configuration_dimension.csv`
- `analysis/data/wp_t1b_standalone_ranking/summary.csv`
- `analysis/data/wp_t1b_standalone_ranking/cost.csv`

## Decision Boundary

The prioritizer choice is made here from rank quality, not later from EvoGrow outcomes. Final WP-T1c result: `no_winner`; `forward` remains the prioritizer for WP-T2a by the incumbent rule.
