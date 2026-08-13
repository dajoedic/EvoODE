# WP-M1 Report

## R2 Definition

Implemented fields:

- `r2`: arithmetic mean of per-dimension coefficient of determination.
- `r2_by_dim`: one R2 value per state dimension.

Definition for each dimension `k`:

```text
R2_k = 1 - sum_t((yhat[t,k] - y[t,k])^2) / sum_t((y[t,k] - mean(y[:,k]))^2)
r2 = mean_k(R2_k)
```

The predicted trajectory is `result.meta.prediction.Yhat`, the final simulated model trajectory used by the existing validated `loss`. The reference trajectory is `traj.x`.

Protocol source followed:

- `docs/paper1_odebench_protocol_alignment.md`, section 3, fixes the Phase B trajectory protocol to our own integration on the dataset grid: `t in [0, 10]`, `512` uniform points, both initial-condition sets, `Tsit5`, `abstol = reltol = 1e-9`.
- The same document states that published-source R2 thresholds and exact published metric conventions are not yet verified. Therefore no threshold field was added and no comparison threshold was invented.

Undefined cases are recorded as `null`, not as plausible numbers:

- non-finite prediction values: `r2 = null`, `r2_by_dim = null`
- `MSELoss` sentinel loss, `loss >= 1e6`: `r2 = null`, `r2_by_dim = null`
- zero reference variance in any dimension: that dimension is `null`, and the averaged `r2` is `null`

Direct function check:

```text
r2_perfect=(r2 = 1.0, r2_by_dim = [1.0, 1.0])
r2_nonfinite=(r2 = nothing, r2_by_dim = nothing)
r2_sentinel=(r2 = nothing, r2_by_dim = nothing)
```

## Expected Stage Derivation

Rule:

1. Load `support_idxs` from `studies/regression/phase_b_support.json`.
2. Build `default_staged_polynomial_basis(dim)`.
3. Use `basis.term_groups` to map each support term index to its staged-basis group.
4. For exact systems, `expected_stage = maximum(stage(term_idx) for all support terms in all equations)`.
5. For surrogate systems, `expected_stage = nothing`.

No hand-maintained Phase B table was added.

Acceptance check against all hand-maintained diagnostic systems:

```text
diagnostic_expected_stage system=3 hand=2 derived=2 PASS
diagnostic_expected_stage system=11 hand=4 derived=4 PASS
diagnostic_expected_stage system=26 hand=3 derived=3 PASS
diagnostic_expected_stage system=31 hand=3 derived=3 PASS
diagnostic_expected_stage system=63 hand=3 derived=3 PASS
phase_b_expected_stage exact_missing=0 surrogate_nonnull=0
```

Generated manifest sanity:

```text
rows=756
representability_exact=20
representability_surrogate=43
expected_stage_missing=43
```

The 43 missing expected stages are exactly the 43 surrogate systems.

## Fingerprints

Old fingerprints:

| Fingerprint | Value |
| --- | --- |
| Phase B | `c71c85ac2ec580ff` |
| Regression | `45cb2c4507007366` |

New fingerprints:

| Fingerprint | Value |
| --- | --- |
| Phase B | `ca02ea284d621f6d` |
| Regression | `0825cdc88d9264a0` |

Causes:

- Phase B moved because exact systems now carry derived `expected_stage`, and because the fingerprint payload now includes the new R2 metric schema.
- Regression moved only because the fingerprint payload now includes the new R2 metric schema. The regression systems already had hand-maintained expected stages, and those values were reproduced exactly.

The old value was not preserved.

## Reference Cells

Local WP-M1 manifest:

```text
manifest=/workspace/outputs/wp_m1/manifest.csv
phase_b_fingerprint=ca02ea284d621f6d
regression_fingerprint=0825cdc88d9264a0
rows=756
```

### Bit-exact anchor

Reference: `outputs/wp_h6_tty_final/tasks/cell_000061.jsonl`

New: `outputs/wp_m1/tasks/cell_000061.jsonl`

| Field | Before | After |
| --- | --- | --- |
| system | 11 exact | 11 exact |
| fingerprint | `c71c85ac2ec580ff` | `ca02ea284d621f6d` |
| expected_stage | `null` | `4` |
| loss | `4.635914151853964e-15` | `4.635914151853964e-15` |
| pruned_match | `true` | `true` |
| final_stage | `4` | `4` |
| stage_overshoot | `null` | `0` |
| wasted_levels | `null` | `0` |
| r2 | `null` | `0.9999999999999564` |
| r2_by_dim | `null` | `[0.9999999999999564]` |
| total_loss_evals | `30550` | `30550` |

Result: `loss_equal_exact=True`, `pruned_equal=True`.

### Exact system check

New exact reference: `outputs/wp_m1/tasks/cell_000139.jsonl`

```text
system_id=24
representability=exact
expected_stage=1
final_stage=1
stage_overshoot=0
wasted_levels=0
eq_overshoot=[0, 0]
eq_wasted_levels=[0, 0]
r2=0.999999999999885
r2_by_dim=[0.999999999999937, 0.999999999999833]
pruned_match=true
```

An older pilot record for this same identity had `pruned_match=true` and a numerically indistinguishable loss at the displayed precision, but not bit-identical optimizer counters/provenance. It is not used as the bit-exact anchor.

### Surrogate system check

New surrogate reference: `outputs/wp_m1/tasks/cell_000109.jsonl`

```text
system_id=19
representability=surrogate
expected_stage=null
final_stage=5
stage_overshoot=null
wasted_levels=null
eq_overshoot=null
eq_wasted_levels=null
r2=0.9999929254364572
r2_by_dim=[0.9999929254364572]
pruned_match=null
```

This confirms surrogate systems still report reached stage as an observation, not as a deviation from a target, while carrying non-null fit quality via R2.

## Orientation Document

`CLAUDE.md` design principle 8 was updated. It no longer promises undefined "target term-class usage".

Current wording:

```text
Exact systems are scored on support recovery; surrogate systems on fit quality via R2, reached stage and stability observations.
```

## Scope

No campaign was run and nothing was applied to the cluster. Only local single-cell verification runs were executed.
