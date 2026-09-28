# WP-T1f-c Report

## Status

Implemented WP-T1f-c as an unclamped WP-T1f variant.

Julia was not executed in this Codex environment, per `codex/CODEX_PROTOCOL.md` and the task text.
The package is therefore reported as `blocked` for environment reasons only; Claude must run the
Julia acceptance commands below.

## Changed Files

- `studies/regression/wp_t1d_neighbourhood_loss.jl`
- `studies/regression/wp_t1f_warm_neighbourhood.jl`
- `test/test_wp_t1f_warm_neighbourhood.jl`
- `SCRIPTS.md`
- `k8s/wp_t1f_indexed_smoke_job.yaml`
- `k8s/wp_t1f_indexed_campaign_job.yaml`
- `codex/reports/REPORT_WP_T1f_c.md`
- `codex/STATUS.md`

## Implementation Notes

- `src/`, `studies/regression/run_regression.jl`, `studies/regression/phase_c_config.jl`, and
  `BFGS_CLAMP_VAL` were not edited.
- `fit_fixed_structure_phase_c` received one defaulted optional keyword, `optimizer = nothing`.
  With the default, it still builds `build_reference_optimizer(max_fit_attempts = max_fit_attempts)`.
- `build_t1f_unclamped_optimizer` builds the Phase-C reference optimizer for the requested
  `max_fit_attempts`, copies all optimizer fields from it, and changes only `clamp_val` to `Inf`.
- WP-T1f control, floor, warm-neighbour, truth-cold, and `--control-only` paths now pass an
  unclamped optimizer into fitting or simulation.
- WP-T1f raw rows now write `phase_c_config_fingerprint`, `wp_t1f_config_fingerprint`,
  `optimizer_variant = "phase_c_reference_unclamped"`, and `clamp_val = "Inf"`.
- Aggregation compatibility for old WP-T1d `cold_reference` rows reads `config_fingerprint` into
  `phase_c_config_fingerprint` when the new name is absent.
- `run_t1f_self_test` now asserts optimizer equality except `clamp_val` and writes
  `optimizer_self_test.csv`.
- `SCRIPTS.md` and the WP-T1f indexed manifests now state that WP-T1f disables only the parameter
  clamp so the loss question is not bounded by the optimizer cap.

## Static Checks Run

```powershell
python -c "import yaml; paths=['k8s/wp_t1f_indexed_smoke_job.yaml','k8s/wp_t1f_indexed_campaign_job.yaml']; [yaml.safe_load(open(p, encoding='utf-8')) for p in paths]; print('parsed '+str(len(paths))+' yaml files')"
```

Result: parsed 2 yaml files.

```powershell
rg "[^\x00-\x7F]" studies/regression/wp_t1f_warm_neighbourhood.jl studies/regression/wp_t1d_neighbourhood_loss.jl test/test_wp_t1f_warm_neighbourhood.jl k8s/wp_t1f_indexed_campaign_job.yaml k8s/wp_t1f_indexed_smoke_job.yaml
```

Result: no matches.

```powershell
rg "BFGS_CLAMP_VAL" studies/regression/wp_t1f_warm_neighbourhood.jl test/test_wp_t1f_warm_neighbourhood.jl -n
```

Result: no matches.

## Julia Commands for Claude

Run in this order:

```text
julia --project=. test/test_wp_t1d_neighbourhood.jl
```

```text
julia --project=. test/test_wp_t1f_warm_neighbourhood.jl
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --self-test --fresh
```

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --control-only --fresh
```

Expected: all 36 cells have control loss `<= 1e-4`.

```text
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --smoke --fresh
```

## Not Run

- No Julia test, self-test, control-only, smoke, local campaign, Docker, `oc`/`kubectl`, or Orion
  command was run by Codex.
- No Git staging, commit, push, checkout, reset, or other write operation was run.
