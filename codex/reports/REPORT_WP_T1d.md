# WP-T1d Report

## Status

Implemented `studies/regression/wp_t1d_neighbourhood_loss.jl` and the neighbourhood-generation guard
`test/test_wp_t1d_neighbourhood.jl`.

Julia was not executed in this Codex environment. Per protocol this package is reported as
`blocked`: implementation is complete, but the self-test and smoke-test must be run by Claude.

## Implemented Commands

Neighbourhood self-test:

```text
julia --project=. test/test_wp_t1d_neighbourhood.jl
```

Smoke path on one dim-2 system and one dim-3 system, first IC set:

```text
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --self-test --fresh
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --smoke --fresh
```

Full path for the user after smoke projection is accepted:

```text
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --fresh
```

The full path writes raw neighbour rows under `outputs/wp_t1d_neighbourhood/` and aggregate CSVs
under `analysis/data/wp_t1d_neighbourhood/`.

## Design

The script selects exact Phase-C systems in dimensions 2 and 3 and excludes system 63. For each
selected `(system, initial_condition_set)` cell, it fits the true support once and reuses that loss
for every neighbour comparison in the cell.

The fixed-structure fit follows the WP-N3 primitive shape: `StructureSpec`, `build_rhs`, reference
BFGS, trajectory simulation, and `MSELoss`. The necessary difference is explicit:
`build_reference_optimizer(max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS)`, i.e. 3 attempts, because
WP-N3's `_fit_fixed_structure` hard-codes the default single-attempt optimizer path.

Trajectory hashes are checked against
`outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/trajectory_manifest.csv` before fitting.
The script recomputes the same little-endian raw-float SHA-256 hashes used by the Phase-C export and
aborts on mismatch.

## Neighbourhood Sizes

Current basis sizes from `staged_polynomial_basis_with_constant`:

- dim 2: `p = 12`
- dim 3: `p = 19`

For each equation with support size `s`, the test enforces:

- `add_one = p - s`
- `remove_one = s`
- `swap_one = s * (p - s)`

It also checks that there are no duplicate neighbour supports and that the true support is not
included as a neighbour.

Static structure-fit projection from the current support file and basis:

| dimension | cells | structure fits incl. truth | neighbour fits |
|---:|---:|---:|---:|
| 2 | 20 | 1190 | 1170 |
| 3 | 16 | 2756 | 2740 |
| total | 36 | 3946 | 3910 |

Using the Phase-B reference value `9.48 s` per structure fit, the full-run projection is
`3946 * 9.48 / 3600 = 10.3911 h`, below the predeclared 25 h cutoff. The smoke path rewrites
`projection.json` using measured smoke seconds per structure fit; if that projection exceeds 25 h,
the full run must not be started.

The task text says "around 2,900 fits" and also gives `20 * 64` plus `16 * 201`, which is `4496`,
not `2900`. The implemented projection is therefore computed from the repository's current
`phase_c_support.json` and `staged_polynomial_basis_with_constant` rather than from either text
approximation.

## Output Fields

Raw rows, one per neighbour, include the required fields:

`system_id`, `dimension`, `initial_condition_set`, `equation_idx`, `neighbor_class`,
`neighbor_terms`, `true_terms`, `support_size_true`, `support_size_neighbor`, `loss_true`,
`loss_neighbor`, `log10_loss_ratio`, `beats_true`, `sentinel_true`, `sentinel_neighbor`,
`extra_term_survives_pruning`, `total_parameter_fits`, `elapsed_s_non_evidence`, `git_hash`,
`config_fingerprint`, `trajectory_sha256`.

Aggregates are written separately by dimension and neighbour class:

- `aggregate_by_dimension_class.csv`
- `margin_quantiles_by_dimension_class.csv`
- `margin_threshold_grid_by_dimension_class.csv`
- `add_one_pruning_survival_by_dimension.csv`
- `swap_one_beating_neighbours.csv`

The three neighbour classes are never collapsed into one metric.

## Interpretation Boundary

`swap_one` is the decisive class because it keeps parameter count fixed while replacing terms. If a
same-size false support beats the true support, the trajectory loss does not locally identify the
truth under the proposed operator set.

`add_one` is nested: a strict superset can fit at least as well as the true support, so a smaller
loss is not a structural counterexample by itself. The script therefore reports the margin and
whether the added coefficient survives the existing pruning rule
`max(1e-6, 1e-3 * max_abs_coefficient)`.

`remove_one` beating the truth is reported as a separate problem class. It may indicate
identifiability or optimizer effects, but the script does not collapse it into the guidance
question.

## Sentinel Handling

Loss values that are non-finite or `>= 1e6` are marked as sentinel losses. A sentinel on either side
sets `log10_loss_ratio = nothing`; the row is not counted as "neighbour beats truth" in either
direction and is excluded from margin quantiles and threshold-grid denominators. Sentinel counts
remain visible in the aggregate summary.

## Not Run

No Julia command was run by Codex. Commands left for Claude:

```text
julia --project=. test/test_wp_t1d_neighbourhood.jl
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --self-test --fresh
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --smoke --fresh
```
