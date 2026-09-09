# WP-N4 Report - Multi-start reference refit

## Status

Blocked by environment, not by the WP-N4 implementation. The task explicitly states that Julia
cannot start in this Codex environment (`A specified logon session does not exist`), so no Julia
execution was attempted, no refit results were produced, and no numerical conclusions are invented.

## Implemented Artifact

`studies/regression/wp_n4_multistart_refit.jl`

The script is separate from WP-N3 and writes only to its own default output directory:

`outputs/wp_n4_multistart_refit/`

It accepts:

```text
--input <history.jsonl>
--output-dir <directory under outputs/>
--limit <n>
--starts <n>
--fresh
```

`--starts` defaults to `10` and must be at least `10`, because the WP-N4 curve is fixed at
`k = 1, 2, 3, 5, 10`.

## Commands For Claude

Short smoke test over a few cells:

```powershell
julia --project=. --startup-file=no studies/regression/wp_n4_multistart_refit.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n4_multistart_refit_smoke --limit 3 --starts 10 --fresh
```

Full WP-N4 run:

```powershell
julia --project=. --startup-file=no studies/regression/wp_n4_multistart_refit.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n4_multistart_refit --starts 10 --fresh
```

## Start Derivation

For each fitted cell and each fixed structure, start `1` uses the cell seed exactly:

```text
start_seed(cell_seed, 1) = cell_seed
```

This preserves WP-N3's initialization path: `Random.seed!(seed)` immediately before
`fit_parameters(...; p0 = nothing)`, so `fit_parameters` draws `0.1 .* randn(n_params)` from the same
global RNG state as WP-N3.

Starts `2..n` are deterministic SHA-derived seeds:

```text
digest = bytes2hex(sha256(codeunits("WP-N4:start:<cell_seed>:<start_index>")))
start_seed = parse(Int, digest[1:15]; base = 16)
```

Each start sets both `Random.seed!(start_seed)` and `build_options(start_seed)`. No pretuning or OLS
warm start is used.

## Method Encoded

For each input cell with available true support, the script refits both WP-N3 structures:

| structure | terms |
|---|---|
| oracle | raw original term set intersected with `wp_n1_expected_support_terms` |
| reference | exactly `wp_n1_expected_support_terms` |

For each structure it runs the requested `--starts` sequence once. The reported `k` values are then
computed cumulatively from those same starts:

| k | data used |
|---:|---|
| 1 | best of start 1 |
| 2 | best of starts 1..2 |
| 3 | best of starts 1..3 |
| 5 | best of starts 1..5 |
| 10 | best of starts 1..10 |

The k-values are therefore nested and not independent.

The fixed-structure refit reuses the existing WP-N3/project helpers:

| item | implementation |
|---|---|
| trajectory | `build_trajectory(system, ic_set)` |
| optimizer | `build_reference_optimizer()` |
| options | `build_options(start_seed)` |
| RHS construction | `build_rhs(StructureSpec(...), basis)` |
| parameter fit | `fit_parameters(optimizer, f!, traj, n_params, MSELoss(), options)` |
| validation simulation | `simulate(...)` with optimizer tolerances, clamp and divergence settings |
| validation loss | `evaluate_loss(MSELoss(), yhat, traj.x)` |
| R2 | `r2_summary(yhat, traj.x, loss)` |

## Output Files

When Julia is available, the script writes:

| file | content |
|---|---|
| `starts.jsonl` | one JSON record per input cell, including all oracle/reference start results |
| `cells_by_k.csv` | per-cell best result for each `k` and structure |
| `curve_summary.csv` | by `k`, basis and structure: sentinel count, structure hits, R2 > 0.9 count, reaches/beats-original count |
| `curve_loss_quantiles.csv` | by `k`, basis and structure: loss quantiles 5/10/25/50/75/90/95 |
| `nonadaptable_cells_at_k10.csv` | cells still at sentinel loss for oracle/reference at `k = 10` |
| `manifest.json` | run metadata and seed derivation |
| `fingerprint.txt` | WP-N4 configuration fingerprint |

## Static Input Inventory

PowerShell inventory of `outputs/wp_n1_dim1_probe/history.jsonl`:

| metric | count |
|---|---:|
| total rows | 132 |
| rows with available true support | 102 |
| rows without available true support | 30 |
| `default_staged_polynomial_basis` rows | 66 |
| `staged_polynomial_basis_with_constant` rows | 66 |
| supported `default_staged_polynomial_basis` rows | 36 |
| supported `staged_polynomial_basis_with_constant` rows | 66 |

The 30 rows without available true support are kept in `starts.jsonl` and `cells_by_k.csv` with
`error = "true support is unavailable for this basis"` and are excluded from basis summaries.

## Static Checks Performed

No Julia process was started. Static checks against `studies/regression/wp_n4_multistart_refit.jl`
found:

| check | result |
|---|---|
| direct write target | default output is `outputs/wp_n4_multistart_refit` |
| WP-N3 output modification | no `outputs/wp_n3_oracle_refit` reference |
| forbidden `elapsed_s` cost metric | no `elapsed_s` reference |
| pretuning warm start | no pretuning reference and no `p0` argument |
| curve k values | `WP_N4_CURVE_K = [1, 2, 3, 5, 10]` |
| start 1 compatibility | `_start_seed(cell_seed, 1) = cell_seed` |
| WP-N3b `sort(::Set)` class | no `sort(intersect(...))` pattern |
| guarded JSON access | record access uses `_json_get` / `_json_require`; the only raw `getproperty` is inside `_json_get` |

## Open Acceptance Points

The implementation is ready for Claude to run, but these points remain open only because Julia is
blocked in this Codex session:

| acceptance point | status |
|---|---|
| execute short `--limit` smoke test | blocked by Julia startup environment |
| execute full 102 supported-cell refit | blocked by Julia startup environment |
| verify k=1 reproduces WP-N3 sentinel counts: oracle 11 / 102, reference 15 / 102 | blocked by Julia startup environment |
| fill WP-N4 curve tables with measured numbers | blocked by Julia startup environment |
| answer whether the reference sentinel quote falls to zero by k=10 | blocked by Julia startup environment |
| list non-adaptable plateau cells, if any remain | blocked by Julia startup environment |
