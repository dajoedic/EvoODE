# WP-L5d Stage Cap Closeout

Generated: 2026-08-01.

## Acceptance

Ground truth is used only to judge these caps. `estimate_stage_caps(traj, basis; policy)`
still has no argument for system id, expected stage, expected terms, or true RHS.

| System | Eq | True stage | Cap | Safe |
|---:|---:|---:|---:|---|
| 3 | 1 | 2 | 2 | true |
| 11 | 1 | 4 | 4 | true |
| 26 | 1 | 3 | 3 | true |
| 26 | 2 | 3 | 3 | true |
| 31 | 1 | 3 | 3 | true |
| 31 | 2 | 3 | 3 | true |
| 63 | 1 | 3 | nothing | true |
| 63 | 2 | 3 | nothing | true |
| 63 | 3 | 1 | nothing | true |
| 63 | 4 | 1 | nothing | true |

Acceptance pass: true.

## Suite Safety And Utility

Exact benchmark systems: 2, 3, 11, 24, 26, 31, 54, 63.

| Suite | Violations | Capped equations | Stages saved | Total equations |
|---|---:|---:|---:|---:|
| exact benchmark | 2 | 8 | 18 | 16 |

Violations:

| System | Eq | True stage | Cap |
|---:|---:|---:|---:|
| 54 | 2 | 3 | 2 |
| 54 | 3 | 3 | 2 |

System 63 is entirely uncapped and contributes no utility. This is intentional under the
current safety rule because equations 1 and 2 cannot be safely capped along the benchmark
trajectory.

The two System 54 violations are a known resolution limit, not an open implementation bug.
They are the same equations WP-L3 identified as undershoots: at benchmark sampling the
residual drops below the derivative-estimator noise floor already at stage 2, so the stage-3
cliff is below the resolution of the derivative estimate. The WP-L3 density sweep showed the
stage-3 cliff becoming visible from twice the sampling density. The current characterisation
is therefore closed: the cap rule is safe where the derivative estimate resolves the
structure, and unsafe where it does not.

## Sensitivity

Six-system set: 3, 11, 26, 31, 54, 63.

| Aggregation | Horizon | Violations | Capped equations | Stages saved |
|---|---:|---:|---:|---:|
| unanimous | 1 | 4 | 8 | 22 |
| unanimous | 2 | 2 | 8 | 18 |
| unanimous | 3 | 2 | 8 | 18 |
| majority_no_undecided_at_or_below | 1 | 4 | 8 | 22 |
| majority_no_undecided_at_or_below | 2 | 2 | 8 | 18 |
| majority_no_undecided_at_or_below | 3 | 2 | 8 | 18 |
| any_positive | 1 | 5 | 8 | 26 |
| any_positive | 2 | 2 | 8 | 18 |
| any_positive | 3 | 2 | 8 | 18 |

Default remains `aggregation=:majority_no_undecided_at_or_below` and
`lookahead_horizon=2`. Horizon 1 fails the System 31 dead-intermediate-stage case.
`any_positive` at horizon 1 is visibly unsafe.

## Fingerprint

`studies/regression/run_regression.jl` now records all behavioural cap-policy fields in the
fingerprint payload:

- estimator
- weighting
- aggregation
- lookahead_horizon
- tau_rel
- tau_abs
- cond_cap
- excitation_floor

New config fingerprint:

```text
df5db7763bcd2449
```

Pre-repair records with `3f9be6d36c4043de` and post-repair records with
`df5db7763bcd2449` must not be pooled.

The Gate-2 readout does not recompute the current fingerprint when selecting the capped
record. It matches `variant=evogrow_v3_stage_capped`, `system_id=26`, `seed=42`,
`error=nothing`, and presence of `support_terms`, so the in-flight record written with the
old process-start fingerprint can still be found after this code change.

History check on the existing file:

```text
existing_capped_gate2_matches=0
existing_evogrow_v3_system26_records_checked=2
existing_evogrow_v3_correctly_not_matched=2
```

## System 31 Caveat

The System 31 repair has been verified by the acceptance table and sensitivity table, but
the original diagnosis path timed out. The fix was made by inference from the intended
floor-crossing semantics and acts in the safe direction: System 31 changed from `[1, 3]` to
`[3, 3]` while Systems 3, 11, 26, and 63 kept their required outcomes. If the rule surprises
later, System 31 equation 1 is the first place to inspect.

## Verification

Commands run:

```powershell
julia --project=. test/test_stage_cap.jl
julia --project=. test/test_gate2_do_or_die.jl
julia --project=. test/test_regression_runner_gate2.jl
```

All passed. No decisive cell was run, and `studies/regression/history.jsonl` was not
modified.

