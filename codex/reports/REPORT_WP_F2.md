# WP-F2 Report - Coupled-system optimum arrival

WP-F1's "optimum arrives early" finding does not transfer as a fixed 1D-sized budget. On coupled
fits the worst measured first-best index was 5,760 evaluations for system 54 with an oversized
18-parameter structure. A 5,000-evaluation budget would have changed that fit; 10,000 would not.

## Scope

Added a sibling study that reuses the WP-F1 recording-loss pattern:

- `studies/linesearch/diagnose_coupled_budget.jl`
- outputs under `outputs/studies/linesearch/wp_f2/`

No `src/` files were modified. The production optimizer, line search, campaign configuration, and
fingerprints were left unchanged.

## Per-Fit Results

Budget columns are factors against the fit's returned final loss, using WP-D2 semantics: the budget
stop returns the best finite loss seen up to that evaluation.

| system | dim | condition | structure | n_params | total evals | first best | frac | final loss | 500 | 1k | 2k | 5k | 10k | 20k | retcode |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 26 | 2 | pretune_on | true | 6 | 673 | 661 | 0.982 | 8.140442e-14 | 7.23e8 | 0.997 | 0.997 | 0.997 | 0.997 | 0.997 | Success |
| 26 | 2 | pretune_off | true | 6 | 1329 | 1317 | 0.991 | 8.067786e-14 | 1.30e11 | 6.95e9 | 0.829 | 0.829 | 0.829 | 0.829 | Success |
| 26 | 2 | pretune_on | oversized | 12 | 15 | 1 | 0.067 | 1.000000e+06 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Success |
| 26 | 2 | pretune_off | oversized | 12 | 15 | 1 | 0.067 | 1.000000e+06 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Success |
| 31 | 2 | pretune_on | true | 3 | 46 | 37 | 0.804 | 1.490096e-13 | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 | Success |
| 31 | 2 | pretune_off | true | 3 | 41 | 37 | 0.902 | 2.044387e+01 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Success |
| 31 | 2 | pretune_on | oversized | 12 | 100000 | 420 | 0.004 | 1.015431e-08 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | MaxLossEvals |
| 31 | 2 | pretune_off | oversized | 12 | 15 | 1 | 0.067 | 1.000000e+06 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Success |
| 54 | 3 | pretune_on | true | 7 | 2575 | 449 | 0.174 | 1.298355e-02 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Failure |
| 54 | 3 | pretune_on | oversized | 18 | 12521 | 5760 | 0.460 | 7.568700e-04 | 4.595 | 1.568 | 1.258 | 1.004 | 1.000 | 1.000 | Failure |
| 54 | 3 | pretune_off | oversized | 18 | 21 | 1 | 0.048 | 1.000000e+06 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Success |

Maximum first-best index across completed fits: **5,760 evaluations**.

The 100,000-evaluation budget did bind once: system 31, `pretune_on`, oversized, `n_params=12`.
That fit had already reached its best finite loss by evaluation 420, so the budget stop returned the
same best loss seen in the sequence.

## Scaling

The informative non-sentinel fits show an upper envelope that grows with parameter count, but not a
clean linear law:

| n_params | largest first-best index measured |
| ---: | ---: |
| 3 | 37 |
| 6 | 1317 |
| 7 | 449 |
| 12 | 420 |
| 18 | 5760 |

This is not roughly constant. The safest reading is that the needed budget scales at least with
`n_params + 1`, because finite-difference BFGS spends that many objective calls per gradient-scale
step, but the measured sample is too small and irregular to claim a precise slope.

## Proposed Budget Rule

Do not implement this in WP-F2, but the measured rule I would carry forward for a follow-up test is:

```text
max_loss_evals = max(2_000, 2 * maxiters * (n_params + 1))
```

With `maxiters = 200`, this gives:

- `n_params=3`: 2,000 budget, versus measured worst 37
- `n_params=6`: 2,800 budget, versus measured worst 1,317
- `n_params=7`: 3,200 budget, versus measured worst 449
- `n_params=12`: 5,200 budget, versus measured worst 420
- `n_params=18`: 7,600 budget, versus measured worst 5,760

Safety margin against the worst measured fit: `7,600 - 5,760 = 1,840` evaluations, or about 32% over
the observed need. A fixed 5,000 budget is not safe on this sample; a fixed 10,000 budget is safe on
this sample but ignores the scaling axis.

## Honest Limits

The conclusion rests on 11 completed fits:

- systems covered: 26 and 31 in 2D; 54 in 3D
- conditions covered: both Phase B conditions for systems 26 and 31; `pretune_on` true and both
  oversized conditions for system 54
- parameter counts covered: 3, 6, 7, 12, 18

Not covered:

- system 54 `true/pretune_off`; it did not complete within a 15-minute per-invocation window after
  `true/pretune_on` had completed
- any 4D system
- a campaign sweep or multiple seeds/initial-condition sets

Several oversized `pretune_off` fits immediately returned the sentinel `1e6`; they are useful as
budget-semantics checks, but not evidence about successful high-dimensional optimization.

## Fingerprints

Measured in the study output:

```text
regression_fingerprint=7acd3ebf3f60b974
phase_b_fingerprint=e577d9d692f3125b
```

## Artifacts

- `outputs/studies/linesearch/wp_f2/fit_summary.csv`
- `outputs/studies/linesearch/wp_f2/fit_records.jsonl`

The JSONL contains the full evaluation sequence for every completed fit.

## Commands

The full default command is available, but may exceed a cheap-run budget because system 54
`true/pretune_off` was not affordable here:

```powershell
julia --project=. --startup-file=no studies/linesearch/diagnose_coupled_budget.jl
```

Measured commands used for the report:

```powershell
julia --project=. --startup-file=no studies/linesearch/diagnose_coupled_budget.jl --systems 26 --structures true,oversized --conditions pretune_on,pretune_off
julia --project=. --startup-file=no studies/linesearch/diagnose_coupled_budget.jl --append --systems 31 --structures true,oversized --conditions pretune_on,pretune_off
julia --project=. --startup-file=no studies/linesearch/diagnose_coupled_budget.jl --append --systems 54 --structures true --conditions pretune_on
julia --project=. --startup-file=no studies/linesearch/diagnose_coupled_budget.jl --append --systems 54 --structures oversized --conditions pretune_on,pretune_off
```

Observed runtimes here:

- system 26 command: 243.6 s
- system 31 command: 201.0 s
- system 54 true/pretune_on command: 82.3 s
- system 54 oversized command: 128.2 s

Expected runtime for the measured subset on this machine: about 11-15 minutes after compilation.

Pass criterion:

- all measured commands exit with status 0
- summary CSV contains 11 completed fit rows
- `max(first_best_index) == 5760`
- fingerprints match `7acd3ebf3f60b974` and `e577d9d692f3125b`
