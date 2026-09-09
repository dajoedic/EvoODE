# WP-N3 Report - Oracle pruning and search-free refit

## Status

Blocked by environment, not by the WP-N3 implementation: `julia.exe` does not start in this
Codex session, so no refit results were produced and no numerical conclusions are reported.

## Commands

Julia start check:

```powershell
julia --project=. -e 'import Pkg; Pkg.activate("."); println(VERSION)'
```

Result:

```text
Program 'julia.exe' failed to run: A specified logon session does not exist. It may already have been terminated
CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
FullyQualifiedErrorId : NativeCommandFailed
```

WP-N3 run command attempted:

```powershell
julia --project=. studies\regression\wp_n3_oracle_refit.jl --input outputs\wp_n1_dim1_probe\history.jsonl --output-dir outputs\wp_n3_oracle_refit --fresh
```

Result:

```text
Program 'julia.exe' failed to run: A specified logon session does not exist. It may already have been terminated
CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
FullyQualifiedErrorId : NativeCommandFailed
```

Input inventory command:

```powershell
$rows = Get-Content outputs\wp_n1_dim1_probe\history.jsonl | ForEach-Object { $_ | ConvertFrom-Json }; $rows | Group-Object basis_name,wp_n1_support_status
```

Static input counts:

| basis / support status | cells |
|---|---:|
| default_staged_polynomial_basis / ok | 36 |
| default_staged_polynomial_basis / eq1_not_representable | 30 |
| staged_polynomial_basis_with_constant / ok | 66 |
| total | 132 |

## Implemented Artifact

Script:

```text
studies/regression/wp_n3_oracle_refit.jl
```

The script is parameterized with:

```text
--input <history.jsonl>
--output-dir <directory under outputs/>
--limit <n>
--fresh
```

Default input is `outputs/wp_n1_dim1_probe/history.jsonl`. Default output directory is
`outputs/wp_n3_oracle_refit/`.

When Julia is available, the script writes:

| artifact | content |
|---|---|
| `results.jsonl` | one record per input cell |
| `cells.csv` | flat per-cell metrics and loss ratios |
| `metric_summary.csv` | structure-hit and R2 > 0.9 counts by all/basis/category/basis-category |
| `loss_quantiles.csv` | 5/10/25/50/75/90/95 loss quantiles for original/oracle/reference |
| `loss_ratios.csv` | 5/10/25/50/75/90/95 quantiles for per-cell loss ratios |
| `exact_structure_deviations.csv` | cells where exact original structures do not produce identical oracle/reference structures |
| `fingerprint.txt` | WP-N3 configuration fingerprint |

## Method Encoded In The Script

For each N1 cell, the script reconstructs:

| structure | source |
|---|---|
| original | `model_terms[*].term_index` from the N1 record |
| original pruned | current `support_match_pruned` threshold, `max(1e-6, 1e-3 * max_abs)` |
| oracle | raw original term set intersected with `wp_n1_expected_support_terms` |
| reference | exactly `wp_n1_expected_support_terms` |

For cells with unavailable true support (`wp_n1_expected_support_terms === nothing`), the script
keeps a per-cell output record with `error = "true support is unavailable for this basis"` and does
not invent oracle/reference metrics.

The fixed-structure refit uses the existing project helpers:

| item | implementation |
|---|---|
| trajectory | `build_trajectory(system, ic_set)` |
| optimizer | `build_reference_optimizer()` |
| options | `build_options(seed)` |
| RHS construction | `build_rhs(StructureSpec(...), basis)` |
| parameter fit | `fit_parameters(..., MSELoss(), options)` |
| validation simulation | `simulate(...)` with the fitted optimizer tolerances and clamp |
| validation loss | `evaluate_loss(MSELoss(), yhat, traj.x)` |
| R2 | `r2_summary(yhat, traj.x, loss)` |

## Random Start Handling

`fit_parameters` draws `p0` from the global RNG when no warm start is supplied. The WP-N3 script
therefore calls `Random.seed!(seed)` immediately before each oracle fit and immediately before each
reference fit. This preserves the N1 cell seed as the stochastic initial-value source while keeping
oracle and reference refits reproducible.

No pretuning warm start is used, matching WP-N1 (`use_pretuning = false` in both N1 basis modes).

## Aggregates

No aggregate refit tables are available from this Codex session because `julia.exe` failed before
the script could start. The script is prepared to produce the required aggregate tables with both
metrics:

| required table | output CSV |
|---|---|
| structure hits and R2 > 0.9, all/basis/category/basis-category | `metric_summary.csv` |
| loss quantiles for original/oracle/reference | `loss_quantiles.csv` |
| loss-ratio quantiles per cell | `loss_ratios.csv` |
| WP-N2 category breakdown | `metric_summary.csv`, `loss_quantiles.csv`, `loss_ratios.csv` |

## Core Questions

Does oracle pruning make the loss worse?

No numerical answer is reported. The run did not execute because Julia failed to start. The script
computes this as `oracle_loss / original_loss` per cell and summarizes the ratio by quantiles.

How far is the search-free reference refit above the original run?

No numerical answer is reported. The script computes this as `reference_loss / original_loss` per
cell and summarizes the ratio by quantiles. This is the intended search-attributable gap once the
script is run in a working Julia environment.

## Open Acceptance Points

The implementation file exists under `studies/regression/` and is parameterized. The following
acceptance points remain open only because the Julia process cannot start here:

| acceptance point | status |
|---|---|
| execute 132 cells | blocked by `julia.exe` startup failure |
| write per-cell result file | blocked by `julia.exe` startup failure |
| compute oracle/reference coefficients | blocked by `julia.exe` startup failure |
| compute aggregate tables from refit results | blocked by `julia.exe` startup failure |
| verify exact-original oracle/reference structure deviations at runtime | implemented in script, not executed |
