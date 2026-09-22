# WP-T1e Report

## Status

Implemented WP-T1e changes in `studies/regression/wp_t1d_neighbourhood_loss.jl`,
`test/test_wp_t1d_neighbourhood.jl`, and three new Kubernetes manifests under `k8s/`.

Julia was not executed in this Codex environment. Per `codex/CODEX_PROTOCOL.md`, this is reported
as `blocked`: implementation is complete, but Claude must run the Julia acceptance checks.

## Defect Fixes

Defect 1 was `true = Float64(true_loss)` inside `log10_loss_ratio`. `true` is a Julia keyword, so
the file could not parse.

Defect 2 was `return log10(neighbor / true)`. If the parse error had not stopped loading, Julia
would have treated `true` as the boolean value and effectively computed `log10(neighbor / 1)`.
That would have silently corrupted the main metric with plausible-looking values.

The function now uses `true_loss_value` for both the positivity check and the quotient. A regression
test checks `log10_loss_ratio(1e-4, 1e-2) == -2.0`, which catches the silent defect.

Static keyword-assignment search run:

```text
rg -n "\b(true|false|nothing)\s*=" studies/regression/wp_t1d_neighbourhood_loss.jl test/test_wp_t1d_neighbourhood.jl
```

Result: no matches.

## Budget

The fit uses the existing campaign mechanism:
`build_reference_optimizer(max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS)`, which sets
`max_loss_evals = BFGS_MAX_LOSS_EVALS`.

Field name: `max_loss_evals`.

Value: `BFGS_MAX_LOSS_EVALS = 20_000`, from `studies/regression/run_regression.jl`.

Rows now carry `budget_exhausted_true`, `budget_exhausted_neighbor`, and `bfgs_max_loss_evals`.
Budget exhaustion is detected from the accepted fit's
`fit_meta.stop_reason == "loss_eval_budget"`; only metadata without `stop_reason` falls back to
`fit_meta.optimizer_eval_budget_limit_hits > 0`. If either side exhausts the budget,
`log10_loss_ratio = nothing` and `beats_true = false`, matching sentinel handling.

## Index Order

The K8s cell universe is the 36 exact Phase-C systems in dimensions 2 and 3, excluding system 63,
with both Phase-C IC sets.

Index order is deterministic:

```text
cell_index 0..35 = system_id ascending, and within each system IC 1 before IC 2
```

The bootstrap path writes:

- `cell_index_map.csv`
- `indices_all.txt`
- `indices_smoke_sys24_sys25_ic1.txt`

The smoke list contains exactly system 24 IC 1 and system 25 IC 1.

## Trajectories

Local behavior: if `trajectory_manifest.csv` and its exported binary files exist under the
trajectory export directory, the cell reads the export and verifies the SHA-256 hashes.

Cluster behavior: if the export is absent, the cell integrates the trajectory with the campaign
path, `build_trajectory(system, ic_set)`, which uses `Tsit5`, `abstol = reltol = 1e-9`, and the
Phase-C grid of 512 points over `t in [0,10]`.

Each row carries `trajectory_sha256` and `trajectory_source`, where source is `export` or
`generated`. One cell uses exactly one source.

## Kubernetes

New files:

- `k8s/wp_t1e_bootstrap_index_job.yaml`
- `k8s/wp_t1e_indexed_smoke_job.yaml`
- `k8s/wp_t1e_indexed_campaign_job.yaml`

All use image `registry.gitlab.scch.at:443/joedicke/evoode:<COMMIT_SHA>`,
`imagePullSecrets: evoode-gitlab-pull`, `JULIA_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`,
`cpu: "1"`, and `memory: 2Gi`.

The campaign manifest uses `completions: 36`, `parallelism: 2`, and
`activeDeadlineSeconds: 86400`.

`parallelism: 2` is intentionally small because the Phase-C campaign can occupy 64 of Orion's 96
cores. `activeDeadlineSeconds: 86400` is a ceiling, not an expectation; expected runtime with two
pods is about five to six hours.

## Commands for Claude

Regression and self-test:

```text
julia --project=. test/test_wp_t1d_neighbourhood.jl
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --self-test --fresh
```

Index-list smoke without fitting:

```text
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --write-index-lists --fresh
```

Short local fit check:

```text
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --limit-cells 1 --fresh
```

Full local run, only after smoke is accepted:

```text
julia --project=. studies/regression/wp_t1d_neighbourhood_loss.jl --fresh
```

## Not Run

No Julia command, full run, GitLab push, or `oc apply` was run by Codex.
