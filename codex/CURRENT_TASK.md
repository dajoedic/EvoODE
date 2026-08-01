# CURRENT TASK

**Language: Julia**

## WP-L5 — Cap safety: only positive evidence may set a cap

### 1. The defect

WP-L4 delivered the per-equation stage cap. An independent check of
`estimate_stage_caps` against the five regression systems found:

| System | per-equation true stage | computed cap | |
|---|---|---|---|
| 3 | [2] | [2] | correct |
| 11 | [4] | [4] | correct |
| 26 | [3, 3] | [3, 3] | correct |
| 31 | [3, 3] | [3, 3] | correct |
| 63 | [3, 3, 1, 1] | **[1, 1, 1, 1]** | `du1`/`du2` wrong |

On System 63, equations 1 and 2 receive a cap of 1 although they require the stage-3 cross
term `u1*u3`. Under the capped variant their true structure becomes **structurally
unreachable** — no amount of search could recover it.

The WP-L4 report states that equations which cannot be judged stay uncapped. That property
is not actually implemented: `_cap_for_equation` returns `nothing` only when no split has a
usable stage-1 fit at all. In every other case it returns a number, starting from a default
of 1 and raising it only when a gain is detected. A residual that already lies below the
noise floor at stage 1 is therefore read as "stage 1 is sufficient" rather than "the data
cannot discriminate here".

This is not merely a coding slip. The rule cannot distinguish "genuinely only stage 1 is
needed" from "the signal is too small to judge" — both present as a residual below the
floor at stage 1. It is the same ambiguity the look-ahead was built to resolve, reappearing
one level down inside the look-ahead's own floor test.

### 2. The principle to implement

The costs are asymmetric. A wrong cap makes the truth unreachable; a missing cap merely
costs the status quo, which is exactly the behaviour the project has today.

> **A cap may only be set on positive evidence. Absence of evidence must leave the
> equation uncapped.**

Concretely, three cases must be separated instead of collapsed into a number:

- **Positive evidence to stop.** The residual at stage `s` is *above* the noise floor, the
  next applicable stage is evaluable, and it yields no gain above the floor. This justifies
  a cap at `s`.
- **Cannot discriminate.** The residual is already at or below the noise floor at stage
  `s`. The data cannot tell whether a later stage would help. No cap.
- **Cannot evaluate.** The next applicable stage is rank-deficient, ill-conditioned, or its
  fit is invalid. No cap.

Review the loop that currently `break`s on an unusable stage: an unevaluable later stage
must not freeze the cap at the last decidable stage, it must remove the cap.

### 3. Aggregation across splits

The current implementation takes a median over per-split caps. Under the new principle an
undecidable split is not a number and must not be silently dropped.

Default rule to implement: a cap is set only if a majority of valid splits provide positive
evidence for it **and** no valid split reports the equation as undecidable at or below that
cap. Report how the five verified systems behave under at least one stricter and one looser
aggregation, so the sensitivity of the choice is visible rather than assumed.

### 4. Acceptance criteria

These are concrete and must be checked, not argued:

1. Systems 3, 11, 26 and 31 keep their current caps — `[2]`, `[4]`, `[3,3]`, `[3,3]`.
2. System 63 equations 1 and 2 are **uncapped** (`nothing`). Equations 3 and 4 may be
   capped at 1 only if positive evidence exists under section 2; otherwise uncapped.

Criterion 1 is load-bearing for a different reason: **a decisive run of
`evogrow_v3_stage_capped` on System 26 seed 42 is currently in progress.** If this work
package changes the cap on System 26, that run's comparison basis is invalidated. Verify
the System 26 cap explicitly and report it first. If it changes, stop and report rather
than proceeding.

### 5. The safety invariant, measured suite-wide

Add an offline check over all exact benchmark systems: for every equation, the cap must be
either `nothing` or greater than or equal to that equation's true stage. Report the number
of violations. It is 2 today (System 63, equations 1 and 2) and the target is 0.

Ground truth is used here to *judge* the cap, never to compute it. Keep that separation
explicit in the code and state it in the report.

Report the price of the added safety alongside it: how many equations still receive a cap,
and how many stages are saved in total. A rule that is safe because it never caps anything
is worthless, and that has to be visible in the same table.

### 6. Also report

Whether the offline confusion matrix changes. It currently stands at 12 exact / 0 over /
4 under / 0 rank-deficient, and two of those undershoots are System 63 equations 1 and 2 —
the same defect seen from the offline side. Uncapped equations need their own category
there; they are not undershoots.

### 7. Scope and execution

`EvoGrowV3` and `EvoGrow` must remain bit-identical with the cap disabled. The
`config_fingerprint` will change again; report the new value.

**Do not run the decisive cell — it is already running externally.** Nothing may be written
to `studies/regression/history.jsonl`. Verification is limited to the cap computation
itself, unit tests, the suite-wide safety check, and a cheap smoke run on a small system.
All of that is seconds to minutes; if anything exceeds a few minutes, stop and report.

### 8. Pre-registered expectation

After the fix, System 63 equations 1 and 2 are uncapped, Systems 3/11/26/31 are unchanged,
and the suite-wide violation count is 0. If violations cannot be driven to 0 without also
losing the correct caps on Systems 3, 11, 26 and 31, report that trade-off explicitly with
the numbers — it would mean the noise-floor criterion is not a sufficient basis for a safe
cap, which is a result in its own right and more useful than a tuned compromise.
