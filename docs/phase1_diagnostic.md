# Phase 1 Diagnostic: Metric Artifact vs. Structural Failure
Generated: 2026-05-17T19:02:20.419070+00:00
Source: `experiments/paper1_phaseA_v1/runs/` (frozen Phase A; not used for final claims)

## Summary

| system | variant | n_runs | raw_match | pruned_match | metric_artifacts | genuine_failures | mean_loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | evogrow_v1 | 5 | 5 | 5 | 0 | 0 | 6.323e-12 |
| 2 | evogrow_v2_1 | 5 | 5 | 5 | 0 | 0 | 6.323e-12 |
| 2 | evogrow_v2_2_passive | 5 | 5 | 5 | 0 | 0 | 6.323e-12 |
| 2 | evogrow_v2_2_soft | 5 | 5 | 5 | 0 | 0 | 6.323e-12 |
| 2 | evogrow_v2_2_stage_local | 5 | 5 | 5 | 0 | 0 | 6.323e-12 |
| 3 | evogrow_v1 | 5 | 5 | 5 | 0 | 0 | 3.236e-08 |
| 3 | evogrow_v2_1 | 5 | 5 | 5 | 0 | 0 | 3.236e-08 |
| 3 | evogrow_v2_2_passive | 5 | 5 | 5 | 0 | 0 | 3.236e-08 |
| 3 | evogrow_v2_2_soft | 5 | 5 | 5 | 0 | 0 | 3.236e-08 |
| 3 | evogrow_v2_2_stage_local | 5 | 5 | 5 | 0 | 0 | 3.236e-08 |
| 11 | evogrow_v1 | 5 | 0 | 5 | 5 | 0 | 4.345e-15 |
| 11 | evogrow_v2_1 | 5 | 0 | 5 | 5 | 0 | 4.345e-15 |
| 11 | evogrow_v2_2_passive | 5 | 0 | 5 | 5 | 0 | 4.345e-15 |
| 11 | evogrow_v2_2_soft | 5 | 0 | 5 | 5 | 0 | 4.345e-15 |
| 11 | evogrow_v2_2_stage_local | 5 | 0 | 5 | 5 | 0 | 4.345e-15 |
| 24 | evogrow_v1 | 5 | 5 | 5 | 0 | 0 | 5.354e-14 |
| 24 | evogrow_v2_1 | 5 | 5 | 5 | 0 | 0 | 5.354e-14 |
| 24 | evogrow_v2_2_passive | 5 | 5 | 5 | 0 | 0 | 5.354e-14 |
| 24 | evogrow_v2_2_soft | 5 | 5 | 5 | 0 | 0 | 5.354e-14 |
| 24 | evogrow_v2_2_stage_local | 5 | 5 | 5 | 0 | 0 | 5.354e-14 |
| 26 | evogrow_v1 | 5 | 0 | 0 | 0 | 5 | 3.658e-04 |
| 26 | evogrow_v2_1 | 5 | 0 | 0 | 0 | 5 | 3.658e-04 |
| 26 | evogrow_v2_2_passive | 5 | 0 | 0 | 0 | 5 | 3.787e-04 |
| 26 | evogrow_v2_2_soft | 5 | 0 | 0 | 0 | 5 | 2.494e-04 |
| 26 | evogrow_v2_2_stage_local | 5 | 0 | 0 | 0 | 5 | 3.658e-04 |
| 31 | evogrow_v1 | 5 | 0 | 0 | 0 | 5 | 6.975e-05 |
| 31 | evogrow_v2_1 | 5 | 0 | 0 | 0 | 5 | 6.975e-05 |
| 31 | evogrow_v2_2_passive | 5 | 0 | 0 | 0 | 5 | 6.975e-05 |
| 31 | evogrow_v2_2_soft | 5 | 0 | 0 | 0 | 5 | 6.975e-05 |
| 31 | evogrow_v2_2_stage_local | 5 | 0 | 0 | 0 | 5 | 6.975e-05 |
| 54 | evogrow_v1 | 5 | 0 | 0 | 0 | 5 | 0.00135884 |
| 54 | evogrow_v2_1 | 5 | 0 | 0 | 0 | 5 | 0.00159398 |
| 54 | evogrow_v2_2_passive | 5 | 0 | 0 | 0 | 5 | 0.00118531 |
| 54 | evogrow_v2_2_soft | 5 | 0 | 0 | 0 | 5 | 9.425e-04 |
| 54 | evogrow_v2_2_stage_local | 5 | 0 | 0 | 0 | 5 | 7.419e-04 |
| 63 | evogrow_v1 | 5 | 0 | 0 | 0 | 5 | 0.00116653 |
| 63 | evogrow_v2_1 | 5 | 0 | 0 | 0 | 5 | 0.00116653 |
| 63 | evogrow_v2_2_passive | 5 | 0 | 0 | 0 | 5 | 0.00116446 |
| 63 | evogrow_v2_2_soft | 5 | 0 | 0 | 0 | 5 | 9.611e-04 |
| 63 | evogrow_v2_2_stage_local | 5 | 0 | 0 | 0 | 5 | 0.00116653 |

## Per-System Findings

### System 2 (Exponential growth)
Across 25 EvoGrow Phase A runs, raw support matched in 25 runs and pruned support matched in 25 runs. The diagnosis counts are 0 metric artifacts, 0 genuine structural failures, and 25 runs already correct under the raw metric.

### System 3 (Logistic growth)
Across 25 EvoGrow Phase A runs, raw support matched in 25 runs and pruned support matched in 25 runs. The diagnosis counts are 0 metric artifacts, 0 genuine structural failures, and 25 runs already correct under the raw metric.

### System 11 (Critical slowing down - du=-u1^3)
Across 25 EvoGrow Phase A runs, raw support matched in 0 runs and pruned support matched in 25 runs. The diagnosis counts are 25 metric artifacts, 0 genuine structural failures, and 0 runs already correct under the raw metric.

### System 24 (Simple harmonic oscillator)
Across 25 EvoGrow Phase A runs, raw support matched in 25 runs and pruned support matched in 25 runs. The diagnosis counts are 0 metric artifacts, 0 genuine structural failures, and 25 runs already correct under the raw metric.

### System 26 (Lotka-Volterra competition)
Across 25 EvoGrow Phase A runs, raw support matched in 0 runs and pruned support matched in 0 runs. The diagnosis counts are 0 metric artifacts, 25 genuine structural failures, and 0 runs already correct under the raw metric.

### System 31 (SIR infection model)
Across 25 EvoGrow Phase A runs, raw support matched in 0 runs and pruned support matched in 0 runs. The diagnosis counts are 0 metric artifacts, 25 genuine structural failures, and 0 runs already correct under the raw metric.

### System 54 (Lorenz system)
Across 25 EvoGrow Phase A runs, raw support matched in 0 runs and pruned support matched in 0 runs. The diagnosis counts are 0 metric artifacts, 25 genuine structural failures, and 0 runs already correct under the raw metric.

### System 63 (SEIR-style epidemic system)
Across 25 EvoGrow Phase A runs, raw support matched in 0 runs and pruned support matched in 0 runs. The diagnosis counts are 0 metric artifacts, 25 genuine structural failures, and 0 runs already correct under the raw metric.

## Gate 1 Input

- Systems where pruning fixes the metric: 11
- Systems with genuine structural failure: 26, 31, 54, 63
- Diagnosis: Pruning resolves near-zero-term artifacts where the expected support is otherwise present, but systems with missing or wrong terms remain genuine structural failures.
