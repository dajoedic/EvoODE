# WP-T1f-b Report

## Status

Implemented the WP-T1f-b correction in `studies/regression/wp_t1f_warm_neighbourhood.jl`.

Julia was not executed in this Codex environment, per `codex/CODEX_PROTOCOL.md` and the task text.
The package is therefore reported as `blocked` for environment reasons only; Claude must run the
Julia acceptance commands below.

## Changed Files

- `studies/regression/wp_t1f_warm_neighbourhood.jl`
- `test/test_wp_t1f_warm_neighbourhood.jl`
- `SCRIPTS.md`
- `codex/reports/REPORT_WP_T1f_b.md`
- `codex/STATUS.md`

## Implementation Notes

- `wp_t1d_neighbourhood_loss.jl` and `src/` were not edited.
- WP-T1f now computes `log10_loss_ratio` and `beats_floor` from raw neighbour and floor losses when
  both losses are finite and neither is a sentinel, even if either side exhausted the BFGS budget.
- Each warm neighbour row now records `comparison_budget_stratum` with one of:
  `neither_exhausted`, `neighbour_exhausted`, `floor_exhausted`, `both_exhausted`.
- Warm raw CSV columns now include both `budget_exhausted` and `floor_budget_exhausted`.
- Aggregation recomputes comparison fields for both warm rows and old WP-T1d `cold_reference` rows
  from raw losses and budget flags.
- Aggregation writes margin summaries, threshold grids, and quantiles separately for
  `all_comparable` and `neither_exhausted`, and writes budget stratum counts to
  `comparison_budget_strata_by_dimension_class.csv`.
- Added `--control-only`, which evaluates all 36 cells at the true coefficients, writes
  `outputs/wp_t1f_warm_neighbourhood/control_only.csv`, prints every cell above `1e-4`, and exits
  nonzero if any such cell exists.
- `t1f_analysis_dir_for` strips trailing `/` and `\` before deriving the input label.
- `SCRIPTS.md` now lists the `--control-only --fresh` command in the WP-T1f local Julia checks.

## Static Checks Run

```powershell
rg -n "[^\x00-\x7F]" studies/regression/wp_t1f_warm_neighbourhood.jl test/test_wp_t1f_warm_neighbourhood.jl
```

Result: no matches.

```powershell
rg -n "log10_loss_ratio\(" studies/regression/wp_t1f_warm_neighbourhood.jl test/test_wp_t1f_warm_neighbourhood.jl
```

Result: no matches.

## Julia Commands for Claude

Run in this order:

```text
julia --project=. test/test_wp_t1f_warm_neighbourhood.jl
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --self-test --fresh
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --control-only --fresh
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --smoke --fresh
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --aggregate-only --input-dir outputs/wp_t1d_neighbourhood/orion_5a87efb
```

## Not Run

- No Julia test, self-test, control-only, smoke, aggregate-only, local campaign, Docker,
  `oc`/`kubectl`, or Orion command was run by Codex.
- `git status --short` was read at session start to inspect the existing uncommitted WP-T1f tree;
  no Git staging, commit, push, checkout, reset, or other write operation was run.
