# REPORT WP-B3

## Merge Semantics

Decision: failed task records are kept as per-task JSONL artifacts, but `merge_batch_records.jl`
refuses to merge them into history.

Reasoning: the task file is valuable failure evidence on a cluster, especially for long 4D cells,
but `history.jsonl` represents completed campaign cells. Merging failed records would poison the
uniqueness key and block a later successful retry.

Verification used a scratch copy only:

- Synthetic failed task record with the same key as cell `61`: `considered=1`, `added=0`, `skipped_duplicates=0`, `skipped_failed=1`
- Corresponding successful cell `61` merged afterwards: `considered=1`, `added=1`, `skipped_duplicates=0`, `skipped_failed=0`
- Scratch history final line count: `43` from an original `42`
- `studies/regression/history.jsonl` was not modified.

## Deterministic Budget

- New `config_fingerprint`: `db8ec4003aa99a0e`
- Previous WP-B2 fingerprint: `256014cf6f0295e1`
- Replaced regression-path `BFGS_TIME_LIMIT_S = 1800.0` with `BFGS_MAX_LOSS_EVALS = 100000` per parameter fit.
- `BFGSOptimizer` now has a deterministic `max_loss_evals` budget and records `optimizer_eval_budget_limit_hits`.
- Regression records now include `total_loss_evals` and `total_optimizer_eval_budget_limit_hits`.

Calibration evidence:

- Read `19` successful existing regression records carrying `total_ode_solves` and `total_parameter_fits`.
- Existing regression history did not yet carry `total_loss_evals`; in the fit code one loss evaluation performs one ODE solve, so `total_ode_solves / total_parameter_fits` is the available historical estimate of loss-evaluations per fit.
- Maximum historical aggregate mean: `7576.788888888889` ODE solves per fit (`evogrow_v3_stage_capped`, system `26`, seed `123`, fingerprint `df5db7763bcd2449`).
- Historical optimizer safety-limit hits: `0`.
- Chosen per-fit budget `100000` leaves about `13.2x` margin over the largest historical aggregate mean and did not bind in the six WP-B3 batch cells.

WP-B1 confirmation under the new fingerprint:

- Cell `61`, system `3`, IC set `1`, seed `42`, variant `evogrow_v2_2_stage_capped`
- Loss: `5.18873247985214e-9`
- Cap: `[2]`
- Support: `[["u1","u1^2"]]`
- `total_optimizer_eval_budget_limit_hits`: `0`

This matches WP-B1 exactly.

## 1D Batch Counts

All six cells were run through `studies/regression/run_batch_cell.jl`, not the suite loop. Only
variant `evogrow_v2_2_stage_capped`, systems `3` and `11`, IC set `1`, and seeds `42`, `123`, `7`
were run.

| index | system | seed | total_parameter_fits | total_ode_solves | total_loss_evals | n_levels | loss |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 61 | 3 | 42 | 110 | 228683 | 228683 | 30 | 5.18873247985214e-9 |
| 62 | 3 | 123 | 110 | 282224 | 282224 | 30 | 5.7203406754820479e-10 |
| 63 | 3 | 7 | 150 | 569374 | 569374 | 30 | 1.919779439191307e-9 |
| 67 | 11 | 42 | 290 | 11006 | 11006 | 30 | 4.6699654872889309e-15 |
| 68 | 11 | 123 | 270 | 11892 | 11892 | 30 | 4.652019557907288e-15 |
| 69 | 11 | 7 | 270 | 11444 | 11444 | 30 | 4.5938956573965318e-15 |

Summary:

- Parameter fits range: `110 - 290`
- ODE solves / loss evals range: `11006 - 569374`
- Sum parameter fits: `1200`
- Sum ODE solves: `1114623`
- Sum loss evals: `1114623`
- Budget hits: `0`
- Wall-clock timings from this laptop were not used as evidence.

## Resource Request Update

`docs/hpc_requirements.md` §5 now uses the measured 1D batch-path count range:

- 1D parameter fits per job: `110 - 290`
- 1D ODE integrations per job: `1.1e4 - 5.7e5`

The core-hour total was not changed, because this task produced count evidence, not trustworthy
cluster timing evidence. The document now labels the core-hour table as a planning assumption and
keeps the pilot allocation request as the step that must convert counts into real runtimes.
