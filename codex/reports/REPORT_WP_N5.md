# WP-N5 Report

## Status

Blocked by environment, not by task logic: Julia was not started in this Codex session as required by the task text. No numerical generalization results are reported here.

## Implemented

Added `studies/regression/wp_n5_ic_generalization.jl`.

The script evaluates the WP-N1 records without search and without parameter refitting:

- reads `outputs/wp_n1_dim1_probe/history.jsonl`
- reconstructs `StructureSpec` and the coefficient vector directly from `model_terms[*].term_index` and `model_terms[*].coefficient`
- rebuilds the basis from `basis_name`
- integrates the record model from its own initial-condition set for the reconstruction probe
- integrates the same fixed model from the other initial-condition set for held-out generalization
- computes `MSELoss` and `r2_summary`, reusing the project R2 definition
- separates IC1 -> IC2 and IC2 -> IC1
- writes outputs only under `outputs/wp_n5_ic_generalization/`

Expected output files:

| file | content |
|---|---|
| `results.jsonl` | full per-cell records, including reconstruction and generalization metrics |
| `cells.csv` | flat per-cell reconstruction/generalization table |
| `reconstruction_probe.csv` | self-integration loss check against the stored record loss |
| `metric_summary.csv` | structure hits and R2 > 0.9 by basis, dimension and direction, for both regimes |
| `loss_quantiles.csv` | 5/10/25/50/75/90/95 loss quantiles by basis, dimension and direction, for both regimes |
| `manifest.json` | run metadata plus the campaign coefficient probe |
| `fingerprint.txt` | WP-N5 config fingerprint |

## Static data checks

PowerShell inventory of `outputs/wp_n1_dim1_probe/history.jsonl`:

| check | value |
|---|---:|
| records | 132 |
| records missing `basis_name`, `model_terms`, `initial_condition_set`, `loss` or `r2` | 0 |
| records with unexpected equation count for dim 1 | 0 |
| missing `term_index` or `coefficient` entries | 0 |

Breakdown:

| basis | initial condition set | records |
|---|---:|---:|
| `default_staged_polynomial_basis` | 1 | 33 |
| `default_staged_polynomial_basis` | 2 | 33 |
| `staged_polynomial_basis_with_constant` | 1 | 33 |
| `staged_polynomial_basis_with_constant` | 2 | 33 |

## Campaign coefficient probe

`experiments/paper1_phaseB_v1/run_registry.csv` has 756 rows and 58 columns.

| required field | present |
|---|---:|
| `model_terms` | false |
| `coefficient` | false |
| `coefficients` | false |

Finding: the campaign registry is not evaluable for WP-N5 generalization because the fitted coefficients are absent. The implemented script records this as `campaign_probe` in its manifest and does not merge campaign data with the WP-N1 probe data.

## Commands for Claude

Limit smoke run:

```text
julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n5_ic_generalization_smoke --limit 6 --fresh
```

Full run:

```text
julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n5_ic_generalization --fresh
```

## Acceptance status

The acceptance criterion is implemented in `reconstruction_probe.csv` via:

```text
abs(reconstruction_loss - stored_reconstruction_loss) <= 1e-8 + 1e-6 * abs(stored_reconstruction_loss)
```

Every failed reconstruction probe is counted and printed at the end of the run. Because Julia cannot be started here, the probe result, the metric tables, the divergence counts and the answer to the WP-N5 question remain open for Claude's execution.
