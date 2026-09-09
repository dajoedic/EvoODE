# WP-H6 Report

## Changes

- Progress display gating is centralized in `studies/regression/run_regression.jl` at `progress_display_enabled()`, which returns `stderr isa Base.TTY`.
- The per-level `Progress("Levels", ...)` in `run_one` and the outer `Progress("Regression", ...)` in `main` are now created only when that check is true.
- Heartbeat writes remain outside the progress-display guard. The `level` and `complete` heartbeat events are still emitted regardless of terminal availability.

Covered entry points:

- `studies/regression/run_batch_cell.jl`, because it includes `run_regression.jl` and calls `run_one`.
- `studies/regression/run_k8s_indexed_cell.jl`, because it follows the same batch-cell path through `run_one`.
- `studies/regression/run_regression.jl`, because the suite-level progress in `main` uses the same terminal check.

## Kubernetes Values

Before values from `HEAD`:

| Manifest | restartPolicy | memory request | memory limit |
| --- | --- | --- | --- |
| `k8s/phase_b_bootstrap_smoke_job.yaml` | `OnFailure` | `2Gi` | `2Gi` |
| `k8s/phase_b_indexed_smoke_job.yaml` | `OnFailure` | `2Gi` | `2Gi` |

After values in the working tree:

| Manifest | restartPolicy | memory request | memory limit |
| --- | --- | --- | --- |
| `k8s/phase_b_bootstrap_smoke_job.yaml` | `Never` | `8Gi` | `8Gi` |
| `k8s/phase_b_indexed_smoke_job.yaml` | `Never` | `2Gi` | `2Gi` |

The bootstrap workload now requests the known-working 8 GiB. The cell workload memory stays unchanged at 2 GiB.

Structural inspection:

```text
k8s\phase_b_bootstrap_smoke_job.yaml:24:      restartPolicy: Never
k8s\phase_b_bootstrap_smoke_job.yaml:47:              memory: 8Gi
k8s\phase_b_bootstrap_smoke_job.yaml:50:              memory: 8Gi
k8s\phase_b_indexed_smoke_job.yaml:27:      restartPolicy: Never
k8s\phase_b_indexed_smoke_job.yaml:52:              memory: 2Gi
k8s\phase_b_indexed_smoke_job.yaml:55:              memory: 2Gi
```

YAML parse check:

```text
python -c "import yaml,sys; [yaml.safe_load(open(p, encoding='utf-8')) for p in sys.argv[1:]]; print('k8s_yaml_ok')" ...
k8s_yaml_ok
```

## Behavioral Progress Test

Same entry point in both runs:

```text
/workspace/studies/regression/run_batch_cell.jl --manifest /workspace/outputs/wp_h4_mapping/manifest.csv --output-dir <mode>/tasks 61
```

TTY-attached run:

```text
docker run --rm -t ... /workspace/studies/regression/run_batch_cell.jl ...
log: outputs/wp_h6_tty_final/combined.log
exit: 0
progress markers: Lines=211, Levels=11, ETA=10, best_loss=10, ESC=418
sample: Levels   7%|...|  ETA: 0:02:19 ( 4.96  s/it)
```

Redirected/non-TTY run:

```text
docker run --rm ... /workspace/studies/regression/run_batch_cell.jl ... > outputs/wp_h6_notty_cmd/stdout.log 2> outputs/wp_h6_notty_cmd/stderr.log
logs: outputs/wp_h6_notty_cmd/stdout.log, outputs/wp_h6_notty_cmd/stderr.log
exit: 0
progress markers: nonempty_lines=4, Levels=0, ETA=0, best_loss=0, ESC=0
stdout: variant=evogrow_v2_2_stage_capped_pretune_on sys=11 ic=1 seed=42 loss=4.636e-15 stage=4/nothing pruned=true elapsed=13.4s
```

The TTY run still displays ProgressMeter output. The redirected run emits no ProgressMeter progress output.

## Heartbeat

Both behavioral runs wrote the expected heartbeat file:

```text
outputs/wp_h6_tty_final/tasks/cell_000061.heartbeat.jsonl    total=15 start=1 level=13 complete=1
outputs/wp_h6_notty_cmd/tasks/cell_000061.heartbeat.jsonl    total=15 start=1 level=13 complete=1
```

This confirms the batch heartbeat mechanism is unchanged in both modes.

## Cluster Scope

No Kubernetes manifest was applied to the cluster, and no campaign was run.
