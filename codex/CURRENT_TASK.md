# CURRENT TASK

**Language: Julia**

## WP-L5b — Repair the stage cap rule: correct floor semantics and a look-ahead horizon

### 0. Read this first — the acceptance table comes before any other work

Produce the acceptance table of section 4 **first**, before tests, before the report,
before the fingerprint change, before anything else. Print it and stop if it does not
pass. The previous attempt did all its work and only then discovered the rule was broken;
this ordering makes the outcome visible in the first minutes.

### 1. What happened in WP-L5

WP-L5 correctly followed its stop rule and halted at the System 26 check, which is why it
delivered only the code change. That was right. But the rule it implemented fails badly,
and it fails in a way WP-L5 misdiagnosed as the trade-off pre-registered in its section 8.
It is not a trade-off. Independent verification:

| System | per-equation truth | WP-L4 | WP-L5 |
|---|---|---|---|
| 3 | [2] | [2] correct | `nothing` |
| 11 | [4] | [4] correct | `nothing` |
| 26 | [3, 3] | [3, 3] correct | `nothing, nothing` |
| 31 | [3, 3] | [3, 3] correct | **[1, 1] — new violation** |
| 63 | [3, 3, 1, 1] | [1, 1, 1, 1] wrong | [1, 1, `nothing`, `nothing`] |

Safety violations rose from 2 to 4 while no system kept a useful cap. A genuine trade-off
would have improved safety at the cost of utility; both axes got worse, which means a
defect, not a compromise.

### 2. The two causes — both concrete, both fixable

**Cause 1: the floor rule in the WP-L5 spec was wrong, and that was my error, not yours.**
It said a residual at or below the noise floor means "cannot judge, no cap". But reaching
the noise floor is *exactly what a correct model does*. Under that rule no solvable system
can ever receive a cap, which is why Systems 3, 11 and 26 lost theirs.

The distinction that actually matters:

- the residual **fell** to the floor at this stage, after an observed gain → the model has
  become adequate here → positive evidence, cap at this stage;
- the residual was **already** at or below the floor at the first evaluable stage, before
  any stage produced a gain → the signal carries no information → no cap.

**Cause 2: the look-ahead horizon collapsed to one stage.** WP-L4 scanned all stages and
took the maximum, so it could see past a useless intermediate stage. The WP-L5 walk stops
at the first stage without a gain. System 31 fails exactly there: its truth needs the
stage-3 cross term `u1*u2` while the stage-2 self-quadratics contribute nothing, so the
walk halts at stage 1.

This is the dead-intermediate-stage case that motivated a horizon of two applicable stages
in the original design discussion. Restore a horizon of at least two **applicable** stages
— applicable meaning the stage contributes new terms for this equation, so genuinely empty
stages are skipped rather than counted against the horizon.

### 3. What to keep from WP-L5

The three-way split of the per-split verdict into positive / undecidable / invalid is
right and should stay, as should the explicit aggregation modes and the rule that a cap is
only set on positive evidence. Only the floor semantics and the horizon change.

Also keep: a cap may only be set at stage `s` if the successor stage was actually
**evaluable**. If the next applicable stage is rank-deficient or ill-conditioned, there is
no evidence that it would not have helped, so the equation stays uncapped. This is what
should keep System 63 equations 1 and 2 uncapped, since their stage-3 library is
rank-deficient along the trajectory.

### 4. Acceptance table — produce this first

Compute `estimate_stage_caps` for the five regression systems and print, per equation, the
true stage, the cap, and whether the safety invariant `cap === nothing || cap >= true
stage` holds. Required outcome:

| System | required cap |
|---|---|
| 3 | [2] |
| 11 | [4] |
| 26 | [3, 3] |
| 31 | [3, 3] |
| 63 | `nothing` for equations 1 and 2; equations 3 and 4 either `nothing` or 1 |

Safety violations must be **0**.

The System 26 cap is load-bearing for a second reason: a decisive run of
`evogrow_v3_stage_capped` on System 26 seed 42 is in flight under the WP-L4 semantics with
cap [3, 3]. Restoring [3, 3] keeps that run interpretable. If it cannot be restored, stop
and report before doing anything else — exactly as WP-L5 did.

Ground truth is used here only to *judge* the caps. It must not enter their computation;
`estimate_stage_caps` keeps its current signature with no channel for it.

### 5. After the table passes

- **Suite-wide safety check** over all exact benchmark systems: count equations where the
  cap is below the equation's true stage. Report the count, and alongside it the utility
  side — how many equations receive a cap at all and how many stages are saved in total.
  A rule that is safe because it never caps is worthless and that must be visible in the
  same table.
- **Aggregation sensitivity:** report the five systems under the stricter and looser
  aggregation modes, so the choice of default is visible rather than assumed.
- **Fingerprint:** the cap policy in `run_regression.jl` is a hardcoded tuple that does not
  contain `aggregation`, so the WP-L5 semantics change did not move
  `3f9be6d36c4043de`. Add the missing field and any new policy parameter introduced here,
  and report the new fingerprint. Records produced before and after this repair must not
  be pooled as one configuration.
- **Tests:** the floor semantics in both directions (fell to the floor versus already at
  it), the horizon crossing a useless intermediate stage, an empty stage not consuming
  horizon, no cap when the successor stage is not evaluable, and the existing WP-L4
  invariants — cap never forces a promotion, uncapped equations unaffected, cap below the
  current stage handled conservatively, `EvoGrowV3` bit-identical with the cap disabled.
- **Report** under `docs/`, stating the acceptance table, the safety and utility counts,
  the sensitivity, and the new fingerprint.

### 6. Scope and execution

**Do not run the decisive cell — it is running externally.** Nothing may be written to
`studies/regression/history.jsonl`. Verification is limited to cap computation, unit tests,
the suite-wide check and a cheap smoke run on a small system; all of that is seconds to
minutes. If anything exceeds a few minutes, stop and report.

### 7. Pre-registered expectation

The corrected floor semantics restore the caps on Systems 3, 11 and 26; the restored
horizon restores System 31; the evaluability requirement leaves System 63 equations 1 and 2
uncapped. Expected: 0 safety violations with the useful caps intact.

If that cannot be achieved — in particular if restoring System 31 also re-introduces a
violation somewhere — report it with the numbers rather than tuning thresholds until the
table passes. It would mean the noise floor plus a fixed horizon is not a sufficient basis
for a safe cap, which is a genuine result and more valuable than a fitted compromise.
