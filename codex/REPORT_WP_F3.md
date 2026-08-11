# WP-F3 Report - Campaign evaluation budget set to 20,000

The campaign-path evaluation budget was changed from `100_000` to `20_000` in
`studies/regression/run_regression.jl`. Phase B reads the same constant through
`phase_b_config.jl`, and `SCREENING_BFGS_MAX_LOSS_EVALS` still aliases the reference budget. No
`src/`, line-search, optimizer-default, or record-schema changes were made.

Important verification finding: the reference healthy cell did not remain identical. The 20,000
budget bound on 9 parameter fits, changing loss and aggregate cost counters while preserving support,
stage, and `pruned_match`. This is reported below as a finding, not hidden by retuning the budget.

## Budget And Fingerprints

| item | before | after |
| --- | ---: | ---: |
| `BFGS_MAX_LOSS_EVALS` | 100,000 | 20,000 |
| regression fingerprint | `7acd3ebf3f60b974` | `45cb2c4507007366` |
| Phase B fingerprint | `e577d9d692f3125b` | `c0a236edf030e03a` |

Measured with:

```powershell
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); include(\"studies/regression/phase_b_config.jl\"); println(config_fingerprint()); println(phase_b_fingerprint())"
```

## WP-F1/F2 Replay At 20,000

Replay command:

```powershell
julia --project=. --startup-file=no studies/linesearch/replay_budget_20000.jl
```

Output:

```text
records=36
would_stop_at_20000=4
differences=2
```

The two differences are both improvements relative to the stored optimizer-return `final_loss`, not
degradations:

| source | system | condition | structure | n_params | total evals | replay loss @20k | final loss | factor |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| WP-F1 | 2 | pretune_on | `u1` | 1 | 28,618 | 1.8637666178045605e-12 | 1.8640674002408976e-12 | 0.999838641866545 |
| WP-F1 | 2 | pretune_off | `u1 + u1^2` | 2 | 51,385 | 1.87982316536569e-10 | 8.900238884964752e-10 | 0.21121041689580838 |

Full replay table:

| source | system | dim | condition | structure | line search | n_params | evals | stop @20k | final loss | replay loss | factor | identical |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| WP-F1 | 2 |  | pretune_on | `u1` | default | 1 | 28,618 | true | 1.864067e-12 | 1.863767e-12 | 0.999839 | false |
| WP-F1 | 2 |  | pretune_on | `u1` | backtracking | 1 | 24 | false | 9.559071e-13 | 9.559071e-13 | 1.000000 | true |
| WP-F1 | 2 |  | pretune_off | `u1` | default | 1 | 97 | false | 1.955816e-12 | 1.955816e-12 | 1.000000 | true |
| WP-F1 | 2 |  | pretune_off | `u1` | backtracking | 1 | 38 | false | 1.955814e-12 | 1.955814e-12 | 1.000000 | true |
| WP-F1 | 2 |  | pretune_on | `u1 + u1^2` | default | 2 | 289 | false | 1.518493e-08 | 1.518493e-08 | 1.000000 | true |
| WP-F1 | 2 |  | pretune_on | `u1 + u1^2` | backtracking | 2 | 99 | false | 1.510212e-08 | 1.510212e-08 | 1.000000 | true |
| WP-F1 | 2 |  | pretune_off | `u1 + u1^2` | default | 2 | 51,385 | true | 8.900239e-10 | 1.879823e-10 | 0.211210 | false |
| WP-F1 | 2 |  | pretune_off | `u1 + u1^2` | backtracking | 2 | 231 | false | 1.375132e-08 | 1.375132e-08 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_on | `u1` | default | 1 | 4,105 | false | 9.586518e+01 | 9.586518e+01 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_on | `u1` | backtracking | 1 | 45 | false | 9.586518e+01 | 9.586518e+01 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_off | `u1` | default | 1 | 145 | false | 9.586518e+01 | 9.586518e+01 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_off | `u1` | backtracking | 1 | 62 | false | 9.586518e+01 | 9.586518e+01 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_on | `u1 + u1^2` | default | 2 | 1,749 | false | 7.966898e-03 | 7.966898e-03 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_on | `u1 + u1^2` | backtracking | 2 | 74 | false | 7.966898e-03 | 7.966898e-03 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_off | `u1 + u1^2` | default | 2 | 1,937 | false | 7.966898e-03 | 7.966898e-03 | 1.000000 | true |
| WP-F1 | 17 |  | pretune_off | `u1 + u1^2` | backtracking | 2 | 203 | false | 7.966791e-03 | 7.966791e-03 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_on | `u1` | default | 1 | 31 | false | 1.159602e-01 | 1.159602e-01 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_on | `u1` | backtracking | 1 | 25 | false | 1.159602e-01 | 1.159602e-01 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_off | `u1` | default | 1 | 7 | false | 1.835299e-01 | 1.835299e-01 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_off | `u1` | backtracking | 1 | 7 | false | 1.835299e-01 | 1.835299e-01 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_on | `u1 + u1^2` | default | 2 | 105 | false | 3.847572e-03 | 3.847572e-03 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_on | `u1 + u1^2` | backtracking | 2 | 82 | false | 3.847572e-03 | 3.847572e-03 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_off | `u1 + u1^2` | default | 2 | 9 | false | 2.195661e-01 | 2.195661e-01 | 1.000000 | true |
| WP-F1 | 11 |  | pretune_off | `u1 + u1^2` | backtracking | 2 | 9 | false | 2.195661e-01 | 2.195661e-01 | 1.000000 | true |
| WP-F2 | 26 | 2 | pretune_on | true | default | 6 | 673 | false | 8.140442e-14 | 8.140442e-14 | 1.000000 | true |
| WP-F2 | 26 | 2 | pretune_off | true | default | 6 | 1,329 | false | 8.067786e-14 | 8.067786e-14 | 1.000000 | true |
| WP-F2 | 26 | 2 | pretune_on | oversized | default | 12 | 15 | false | 1.000000e+06 | 1.000000e+06 | 1.000000 | true |
| WP-F2 | 26 | 2 | pretune_off | oversized | default | 12 | 15 | false | 1.000000e+06 | 1.000000e+06 | 1.000000 | true |
| WP-F2 | 31 | 2 | pretune_on | true | default | 3 | 46 | false | 1.490096e-13 | 1.490096e-13 | 1.000000 | true |
| WP-F2 | 31 | 2 | pretune_off | true | default | 3 | 41 | false | 2.044387e+01 | 2.044387e+01 | 1.000000 | true |
| WP-F2 | 31 | 2 | pretune_on | oversized | default | 12 | 100,000 | true | 1.015431e-08 | 1.015431e-08 | 1.000000 | true |
| WP-F2 | 31 | 2 | pretune_off | oversized | default | 12 | 15 | false | 1.000000e+06 | 1.000000e+06 | 1.000000 | true |
| WP-F2 | 54 | 3 | pretune_on | true | default | 7 | 2,575 | false | 1.298355e-02 | 1.298355e-02 | 1.000000 | true |
| WP-F2 | 54 | 3 | pretune_off | true | default | 7 | 100,000 | true | 1.471354e+00 | 1.471354e+00 | 1.000000 | true |
| WP-F2 | 54 | 3 | pretune_on | oversized | default | 18 | 12,521 | false | 7.568700e-04 | 7.568700e-04 | 1.000000 | true |
| WP-F2 | 54 | 3 | pretune_off | oversized | default | 18 | 21 | false | 1.000000e+06 | 1.000000e+06 | 1.000000 | true |

Replay artifact: `outputs/studies/linesearch/wp_f3/budget_20000_replay.csv`.

## Reference Cell

Reference command into scratch history:

```powershell
$env:EVO_REGRESSION_HISTORY_PATH='outputs/studies/linesearch/wp_f3/reference_history.jsonl'
$env:FRESH='1'
$env:EVO_REGRESSION_VARIANT='evogrow_v2_2_stage_capped'
$env:EVO_REGRESSION_SYSTEM_ID='3'
$env:EVO_REGRESSION_IC_SET='1'
$env:EVO_REGRESSION_SEED='7'
julia --project=. --startup-file=no studies/regression/run_regression.jl
```

Observed runtime: 96.2 s wall time; record elapsed `53.1898799` s.

Comparison anchor: `outputs/studies/regression/wp_b3/tasks/cell_000063.jsonl`, matching the WP-D5
DIARY loss `1.920e-09` and carrying the full optimizer telemetry. The newer
`studies/regression/history.jsonl` also has a same-identity row under fingerprint
`df5db7763bcd2449`, but that record lacks `total_loss_evals` and budget-stop fields; it is not the
best field-by-field anchor.

| field | WP-D5/WP-B3 anchor | WP-F3 scratch run | same? |
| --- | --- | --- | --- |
| `loss` | `1.919779439191307e-09` | `1.0641805457760865e-09` | no |
| `objective` | absent | absent | yes, absent in both |
| `support_terms` | `[["u1","u1^2"]]` | `[["u1","u1^2"]]` | yes |
| `final_stage` | `2` | `2` | yes |
| `pruned_match` | `true` | `true` | yes |
| `total_parameter_fits` | `150` | `130` | no |
| `total_loss_evals` | `569374` | `220157` | no |
| `total_ode_solves` | `569374` | `220157` | no |
| `total_optimizer_eval_budget_limit_hits` | `0` | `9` | no |
| `total_optimizer_budget_stop_fits` | absent | `9` | no |
| `optimizer_retcodes` | `["Success","Failure"]` | `["Success","Failure","MaxLossEvals"]` | no |
| `config_fingerprint` | `db8ec4003aa99a0e` | `45cb2c4507007366` | expected no |

Conclusion: the reference-cell check contradicts the expected "identical except fingerprint" result.
The budget did bind on a nominally healthy 1D regression cell. It did not damage the reported
scientific structure metrics in this cell and even lowered the final loss, but it changed the search
path and cost telemetry materially.

## Documentation Updated

- `DIARY.md`: added WP-F3 decision, measured 5,760 basis, 3.5x margin, reproducible safety-limit
  rationale, reference-cell finding, and WP-E2 requirement.
- `docs/hpc_requirements.md`: replaced the old wall-clock-limit wording with the deterministic
  `20,000` evaluation budget; noted that the budget rests on WP-F1/F2 measurements rather than
  extrapolation; updated remaining-work wording.

## Verification Commands

Fingerprint check:

```powershell
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); include(\"studies/regression/phase_b_config.jl\"); println(config_fingerprint()); println(phase_b_fingerprint())"
```

Expected runtime: under 1 minute after compilation. Pass criterion: prints
`45cb2c4507007366` and `c0a236edf030e03a`.

Replay check:

```powershell
julia --project=. --startup-file=no studies/linesearch/replay_budget_20000.jl
```

Expected runtime: under 15 seconds. Pass criterion: `records=36`, `would_stop_at_20000=4`,
`differences=2`, with the two differences listed above and both factors `<= 1`.

Reference-cell check:

```powershell
$env:EVO_REGRESSION_HISTORY_PATH='outputs/studies/linesearch/wp_f3/reference_history.jsonl'
$env:FRESH='1'
$env:EVO_REGRESSION_VARIANT='evogrow_v2_2_stage_capped'
$env:EVO_REGRESSION_SYSTEM_ID='3'
$env:EVO_REGRESSION_IC_SET='1'
$env:EVO_REGRESSION_SEED='7'
julia --project=. --startup-file=no studies/regression/run_regression.jl
```

Expected runtime: about 1-2 minutes. Pass criterion for reproducing the observed WP-F3 state:
single successful record, fingerprint `45cb2c4507007366`, support `[["u1","u1^2"]]`, final stage
`2`, `pruned_match=true`, and `total_optimizer_eval_budget_limit_hits=9`. This is not the originally
expected pass criterion; the non-identical result is the finding.
