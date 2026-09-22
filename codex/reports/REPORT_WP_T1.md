# REPORT WP-T1

## Scope

Implemented the exploratory Python study under `analysis/exploratory/term_relevance/` and the
CLI entry point `analysis/scripts/aggregate/run_wp_t1_term_relevance.py`.

The run used the campaign trajectory export:

`outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/trajectory_manifest.csv`

No fallback integration was used. The loader reads dtype, byte order, axis order, shapes, and
SHA256 values from the manifest and aborts on a mismatch.

## Degenerate Columns and Tie Breaks

Degenerate columns are kept in the candidate set. They are marked in each record, receive score
`null` in the CSV serialization, and are ranked after all non-degenerate columns. In this run the
`fd` signal had exactly 1 degenerate column per record, the constant term; the `weak` signal had 0.

Rank ties are resolved by ascending 1-based basis index. The forward method ranks terms by
residual-error reduction order over the full candidate set; it does not stop early.

## Outputs

Data written to `analysis/data/wp_t1_term_relevance/`:

- `records.csv`: 7,788 rows
- `aggregate_by_configuration_dimension.csv`: 528 rows
- `null_model_by_configuration_dimension.csv`: 528 rows
- `gate_decision.json`
- `run_metadata.json`

Figures written to `analysis/figures/wp_t1_term_relevance/`:

- `distribution_by_dimension_configuration.png`
- `diagnostics_cosine_condition.png`

The 7,788 records equal 59 equations times 132 replicated configuration cells:
11 dim-1 equations, 20 dim-2 equations, 24 dim-3 equations, and 4 dim-4 equations.

## Basis and Inputs

The Python basis clone matches `staged_polynomial_basis_with_constant` for all 30 exact systems.
Library sizes are 6, 12, 19, and 27 for dimensions 1 through 4.

Input hashes are recorded in `run_metadata.json`, together with the configuration hash. The
maximum absolute difference between empirical and analytic random-ordering means was 0.0634666667
over 10,000 random permutations per equation.

## Decision Cell

The pre-declared decision cell was:

- signal: `weak`
- method: `forward`
- `sigma_rel`: 0
- IC strategy: `ic1`
- stratum: dim 2 and dim 3

Effective cluster size: 18 systems. The decision cell contains 44 equations.

Gate values:

- median `n_false_before_last_true`: 0.0, threshold <= 2: pass
- share with `n_false_before_last_true <= 3`: 37 / 44 = 0.8409090909, threshold >= 0.60: pass
- pooled cluster-robust null p-value: 0.00000762936542753, threshold < 0.01: pass
- IC2 replication condition: same direction, p = 0.00000762936542753

Gate judgment: `positive`.

The thresholds 2 and 3 are the pre-declared human design decision levels, not data-derived
thresholds.

## Dimension Separation

Dim 1 is reported only as a sanity check and is not part of the decision. For the decision
configuration with `ic1`, dim 1 had median 0.0 and 10 / 11 equations at value <= 3.

Dim 2 and dim 3 are the decision stratum:

- dim 2: 20 equations, median 0.0, 19 / 20 at value <= 3, analytic null mean 6.104167,
  empirical null mean 6.095675, cluster p = 0.001951
- dim 3: 24 equations, median 0.0, 18 / 24 at value <= 3, analytic null mean 11.527778,
  empirical null mean 11.570925, cluster p = 0.007782

Dim 4 is system 63 only and is reported separately. For the decision configuration with `ic1`,
its four equations had `n_false_before_last_true` values 0, 2, 10, and 0. The condition number was
4.539687e9, and max true-vs-false cosine values were 0.986489, 0.999989, 0.999998, and 0.999998.

## Verification

Commands run:

```text
python -m pytest analysis/tests/test_wp_t1_term_relevance.py -q --basetemp .pytest_tmp_wp_t1
python analysis/scripts/aggregate/run_wp_t1_term_relevance.py
python -m pytest analysis/tests -q --basetemp .pytest_tmp_wp_t1_all
```

Results:

- WP-T1 focused tests: 6 passed
- full analysis tests: 69 passed
- full WP-T1 run completed and produced the outputs listed above
