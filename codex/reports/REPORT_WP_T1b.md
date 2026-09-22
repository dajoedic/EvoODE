# WP-T1b Report

## Scope

Implemented the standalone trajectory-ranking discovery procedure:
selection path -> least-squares coefficients in the selected signal space -> ODE integration -> SINDy-compatible metrics.

No EvoGrow comparison was performed. Phase B uses the old basis without the constant term, and the canonical Phase-C EvoGrow number is a separate campaign result.

## Outputs

Data:

- `analysis/data/wp_t1b_standalone_ranking/details.csv`
- `analysis/data/wp_t1b_standalone_ranking/summary.csv`
- `analysis/data/wp_t1b_standalone_ranking/selection_path.csv`
- `analysis/data/wp_t1b_standalone_ranking/cost.csv`
- `analysis/data/wp_t1b_standalone_ranking/run_metadata.json`

Figures:

- `analysis/figures/wp_t1b_standalone_ranking/structure_hit_path_by_dimension.png`
- `analysis/figures/wp_t1b_standalone_ranking/structure_vs_r2_rate_against_sindy.png`

Full run size:

- `details.csv`: 16,832 rows
- systems: 63
- signals: `fd`, `weak`
- directions: `IC1_to_IC2`, `IC2_to_IC1`
- sigma values: 0.0, 0.01, 0.05
- operating points: `full_path`, `bic`, `oracle_size`
- `selection_path.csv`: 2,872 rows

## Intercept Treatment

The repaired `fd` arm keeps the constant column uncentered, assigns it scale 1, and passes it to forward selection as a regular candidate. This fixes the WP-T1 defect where centering made the constant column degenerate and structurally unfindable. The default WP-T1 path remains unchanged; the repair is only enabled via `explicit_intercept=True`.

This is a correction, not tuning. It was selected before reading WP-T1b results.

## Selection Rules

BIC uses:

`n * log(SSE / n) + k * log(n)`

where `n` is the number of design rows for the current signal problem. For the weak signal this is a known weakness because overlapping windows are not independent; the criterion is still reported as the single predeclared automatic stopping rule.

`oracle_size` is an upper bound, not a procedure. It uses the true support size per equation to separate rank quality from stopping-rule quality.

Full paths were integrated only at sigma 0. For sigma 0.01 and 0.05 only `bic` and `oracle_size` were integrated.

## Main Sigma 0 Results

Exact systems only, dimensions 2 and 3:

| signal | operating point | dim | regime | n | structure hit | R2 > 0.9 |
|---|---|---:|---|---:|---:|---:|
| fd | bic | 2 | reconstruction | 20 | 0.2000 | 0.7000 |
| fd | bic | 2 | generalization | 20 | 0.2000 | 0.5500 |
| fd | bic | 3 | reconstruction | 16 | 0.0000 | 0.0000 |
| fd | bic | 3 | generalization | 16 | 0.0000 | 0.0000 |
| fd | oracle_size | 2 | reconstruction | 20 | 0.5000 | 0.5500 |
| fd | oracle_size | 2 | generalization | 20 | 0.5000 | 0.4000 |
| fd | oracle_size | 3 | reconstruction | 16 | 0.2500 | 0.0625 |
| fd | oracle_size | 3 | generalization | 16 | 0.2500 | 0.0000 |
| weak | bic | 2 | reconstruction | 20 | 0.3000 | 0.7500 |
| weak | bic | 2 | generalization | 20 | 0.3000 | 0.7500 |
| weak | bic | 3 | reconstruction | 16 | 0.0000 | 0.1250 |
| weak | bic | 3 | generalization | 16 | 0.0000 | 0.1250 |
| weak | oracle_size | 2 | reconstruction | 20 | 0.4500 | 0.6500 |
| weak | oracle_size | 2 | generalization | 20 | 0.4500 | 0.4000 |
| weak | oracle_size | 3 | reconstruction | 16 | 0.0625 | 0.1250 |
| weak | oracle_size | 3 | generalization | 16 | 0.0625 | 0.0000 |

Against the predeclared SINDy reference, standalone ranking does not reach the dim 2 structure target and does not rescue dim 3. Oracle-|S| also remains poor on dim 3. This is interpretation C: rank quality is necessary but not sufficient for a standalone discovery procedure.

## Cost

The smoke projection was 16,832 integrations, below the 40,000 cutoff. The full run executed 16,832 evaluation integrations.

During selection itself the number of ODE integrations was 0. Selection used design-space least squares only.

Cost totals:

- `n_target_regressions`: 5,148
- `n_path_least_squares`: 70,224
- `n_evaluation_integrations`: 16,832
- `n_selection_integrations`: 0

## WP-T1 Relation

WP-T1's statement "weak beats fd" is not durable as stated. WP-T1's `fd` arm structurally could not find constants, and the fair no-constant subset in WP-T1 had already shown matching sigma 0 medians. WP-T1b therefore treats the FD intercept defect as corrected for this standalone procedure while preserving the old WP-T1 path.

The WP-T1 regression control was run after the change. `gate_decision.json` and `aggregate_by_configuration_dimension.csv` were byte-identical to the saved references.

## Verification

Commands run:

- `python -m py_compile analysis/scripts/aggregate/run_wp_t1b_standalone_ranking.py analysis/exploratory/term_relevance/term_relevance.py`
- `python analysis/scripts/aggregate/run_wp_t1b_standalone_ranking.py --limit-systems 1,24,52 --smoke-only`
- `python analysis/scripts/aggregate/run_wp_t1b_standalone_ranking.py --smoke-only`
- `python analysis/scripts/aggregate/run_wp_t1b_standalone_ranking.py --limit-systems 1,24,52`
- `pytest -q analysis/tests/test_wp_t1_term_relevance.py analysis/tests/test_wp_t1b_standalone_ranking.py`
- `python analysis/scripts/aggregate/run_wp_t1b_standalone_ranking.py`
- `python analysis/scripts/aggregate/run_wp_t1_term_relevance.py` followed by byte-hash comparison of `gate_decision.json` and `aggregate_by_configuration_dimension.csv`

Test result:

- 10 passed
- WP-T1 regression outputs byte-identical

