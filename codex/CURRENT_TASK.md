# CURRENT TASK

**Language: Julia**

## WP-M1 — The two metrics the campaign is currently missing

### Why this exists

The campaign would today produce 756 records that cannot answer the questions the paper asks.

`PAPER_1.md` lists `r2` in its core metric table; the code contains no implementation. For the 43
surrogate systems — two thirds of the campaign — that leaves raw loss as the only quality measure,
with no bridge to the ODEBench literature, which argues in terms of R².

Separately, `expected_stage` is hard-coded to `nothing` for every Phase B system. The metric table
defines `stage_overshoot` and `wasted_levels` relative to it, so both are null throughout — including
on the 20 exact systems. `wasted_levels` is the quantity the central claim rests on: that stage
escalation is pure waste on systems where the structure is already reachable. As things stand the
campaign would not measure it.

Both changes must land **before the first campaign record**, because both are expected to move the
Phase B fingerprint.

### 1. R², for all 63 systems

Implement the coefficient of determination between the discovered model's simulated trajectory and
the reference trajectory, per dimension and averaged, and record it alongside `loss`.

Do not invent the convention. `docs/paper1_odebench_protocol_alignment.md` exists precisely to keep
this comparable with the published numbers — follow what the protocol audit establishes, and where
it is silent, say so in the report rather than choosing silently.

Two cases need explicit handling, and both occur in real records: a solve that produces non-finite
values, and a run that terminated on the optimizer's sentinel loss. Neither may yield a plausible
looking R². Decide what is recorded in those cases and justify it; a missing value is an acceptable
answer, a misleading number is not.

This metric applies to **all** systems. It is the only quality statement the surrogate systems can
carry, and it is the reason they are in the campaign at all.

### 2. `expected_stage`, derived rather than maintained

`studies/regression/phase_b_support.json` already carries, per exact system, the basis indices of the
true support (`support_idxs`, one list per equation). The staged basis groups its terms into five
stages. The expected stage of a system is therefore the highest stage still containing one of its
support terms — a mechanical consequence of data the project already derives.

Derive it. Do not add a hand-maintained table: this project has been bitten by exactly that before,
when `expected_terms_for` covered five systems and silently yielded nothing for the rest.

**Acceptance test, and it is a strong one:** the derivation must reproduce **all five** hand-maintained
values in `studies/regression/diagnostic_systems.jl`. If it disagrees on any of them, either the
derivation or the hand-maintained value is wrong — stop and report, do not adjust one to match the
other.

**Surrogate systems keep `expected_stage = nothing`.** They have no true support, so no expected
stage exists. Report their reached stage as an observation, never as a deviation from a target. Do
not invent a value to fill the column.

Once this is in place, verify that `stage_overshoot` and `wasted_levels` become non-null on the exact
systems and remain null on the surrogate ones.

### 3. Retire "target term-class usage"

`CLAUDE.md` design principle 8 currently promises that surrogate systems are scored on "stage
reached, target term-class usage, fit quality and stability". Three of those four are covered by this
work package and by what records already carry. The second has no definition anywhere in the
repository, no implementation, and no entry in the metric table — it exists only as that phrase.

Remove it from the principle and state what surrogate systems are actually scored on. An unfulfilled
promise in the orientation document is worse than an honest, narrower one.

### 4. The fingerprint will move, and that is intended

Deriving `expected_stage` changes the Phase B system definitions, and the support table is already
part of the campaign identity — WP-E2 moved the fingerprint for exactly this reason.

Report the old and the new `phase_b_fingerprint` explicitly, and state which of the two changes
caused the move. Do not attempt to preserve the old value.

The regression fingerprint must be checked too: if it moves, say why, since the regression systems
already had expected stages.

### 5. Verification

- The five hand-maintained expected stages are reproduced exactly (§2)
- A reference cell on an **exact** system now reports non-null `stage_overshoot` and `wasted_levels`
- A reference cell on a **surrogate** system still reports null for both, and a non-null `r2`
- `loss` and `pruned_match` are **unchanged** on a reference cell against a known previous record —
  this work package adds measurements, it must not alter what the search does
- Both fingerprints reported, old and new

The last point matters most. If a previously recorded loss changes, something was altered that
should not have been.

Do not run a campaign and do not apply anything to the cluster.

### 6. Out of scope

What claim the surrogate systems support is settled: fit quality via R², plus reached stage and
stability as observations. Do not design a structural metric for them — there is no true support to
compare against, so no such metric can exist.

Also out of scope: the analysis pipeline (WP-A1 runs separately), the Kubernetes manifests, the
image, and any change to hyperparameters, variants, seeds or the system list.

### Report

Write `codex/REPORT_WP_M1.md`: the R² definition used and which protocol source it follows, the
handling of non-finite and sentinel cases, the derivation rule for `expected_stage` and the
comparison against all five hand-maintained values, the before/after fingerprints with the cause of
the move, and the reference-cell comparison showing `loss` and `pruned_match` unchanged.
