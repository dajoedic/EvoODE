# CURRENT TASK

**Language: Julia**

## WP-L4 — Stage cap from the look-ahead: first test as a discovery mechanism

Two parts, in order. Part A is a small correctness fix that Part B depends on. Part B is
the first time the look-ahead touches the search at all.

**Execution rule for this work package: do not run the decisive experiment.** Part B
produces a run of several hours on System 26. Implement it, verify it with the cheap smoke
tests described in section B.7, and stop. The real run is started externally.

---

## Part A — Disambiguate "non-identifiable"

WP-L3 reports "non-identifiable" with two different meanings that happen to yield the same
count of 4, which makes the report easy to misread:

- `identifiability.csv` flags `{54 du2, 54 du3, 63 du1, 63 du2}` — equations where a
  lower-stage library already reaches the noise floor, so the true stage cannot be
  distinguished from a lower one along this trajectory.
- The confusion category `not_identifiable` covers all four equations of System 63 —
  equations whose *higher-stage* library is rank-deficient.

These are different properties and must carry different names and different columns.
Choose two explicit names (for example a lower-stage-indistinguishable property and a
rank-deficient property), report them separately everywhere, and state in the report how
many equations carry each and how many carry both.

The second classification is also too aggressive. System 63 equations 3 and 4 have expected
stage 1 and their stage-1 design matrices are well conditioned (condition number 234).
Marking them undecidable because a stage they never need is rank-deficient understates the
method. Rank deficiency must be recorded **per tested stage**, not as a blanket property of
the equation, and an equation must remain decidable up to the highest stage that is
actually well conditioned.

Regenerate the WP-L3 outputs with the corrected classification and report the confusion
matrix again. Say explicitly whether the headline numbers (10 exact / 0 over / 2 under)
change.

---

## Part B — Per-equation stage cap in the search

### B.1 What is being tested

Every look-ahead result so far is offline: known ground truth, full term library as the
checkpoint, no interaction with the search. Part B tests the mechanism for the first time.

The gate depends only on trajectory, basis, equation and stage — never on the population or
the current structure. It therefore needs no speculative unlock, no checkpoint and no
rollback. A per-equation `max_useful_stage_k` is computed once, before the search, and acts
as a cap: equation `k` may never promote beyond it. Everything else in the search stays as
it is.

### B.2 Absolutely no ground truth may enter the cap

This is the single most important constraint in this work package. The probe used ground
truth only for *evaluation* — confusion matrices and the analytic noise-floor reference
rows. The cap must be computed from the observed trajectory and the basis alone.

Nothing derived from `expected_terms`, `expected_stage`, `true_rhs!`, or any per-system
table may reach `max_useful_stage_k`. The Richardson noise floor is data-only and is
allowed; the firing thresholds are ordinary hyperparameters and are allowed.

Add a test that fails if the cap computation can see ground truth — for example by
computing the cap for a system whose true structure is withheld and asserting the same
result. State in the report how this was enforced.

### B.3 Variant, not a modification

Introduce the capped search as a **new variant** with its own slug. `EvoGrow` v2.2 and
`EvoGrowV3` must remain bit-identical when the cap is disabled; verify this the same way
WP-v3.2 and WP-v3.3 verified their equivalence. The new variant changes search behaviour
and therefore the `config_fingerprint`; that is expected and must be reported, not avoided.

### B.4 Behaviour to define explicitly

- **Equations the probe cannot judge.** If an equation is undecidable under the corrected
  Part-A classification, it gets **no cap** and falls back to current behaviour. The gate
  must never block an equation it cannot assess. State this in the docstring.
- **Cap below the current stage.** Define what happens if a cap is computed that lies below
  a stage the equation has already reached. It must not retroactively remove terms; specify
  and implement the conservative reading.
- **Interaction with existing promotion.** The cap is an upper bound only. All existing
  promotion conditions still have to be met; the cap can only ever prevent a promotion,
  never cause one.

### B.5 The decisive cell

The experiment is the frozen do-or-die cell: System 26, seed 42, 30 levels, otherwise the
WP-G2.1 configuration. Comparison targets are the frozen v2.2 anchor
(loss `0.001391623174905009`, `final_stage 5`, overshoot 2, wasted 8) and the v3 Gate-2
result (loss `2.5195575964774715e-4`, `eq_final_stages [5,5]`, `eq_overshoot [2,2]`).

Reuse the existing readout in `studies/gate2_do_or_die/` rather than writing a new one;
extend it if it cannot represent the capped variant.

### B.6 What counts as a result — read this before writing the readout

On System 26 the probe's cap is `[3, 3]`. **The cap therefore forces
`eq_final_stages = [3,3]` by construction.** Reporting that as a success would be
circular, and the readout must not do it. Treat it as a construction check: if it does not
hold, the implementation is wrong.

The actual questions are:

1. **Structure.** Does `du2` improve? Under v2.2 it ended as `{u1, u1^2}` while the truth is
   `2·u2 − u1·u2 − u2²`, all available at stage 3. Confining the search to stage 3 gives it
   nowhere else to go — does it now find the right support, or does it still fail? This is
   the question that decides whether stage escalation was the problem or merely a symptom.
2. **Loss.** Better, equal, or worse than the v2.2 anchor and the v3 result?
3. **Cost.** Integrations and levels saved relative to both. Report counts, not wall-clock —
   the wall-clock axis has been unreliable in this project.

A plausible and fully reportable outcome is: overshoot gone, cost down, `du2` still wrong.
That would mean the look-ahead solves complexity allocation and not structural recovery,
which is a real and publishable result. Do not present it as a shortfall.

### B.7 Verification without the long run

Permitted: the bit-identity check from B.3, the ground-truth-leak test from B.2, unit tests
for the cap logic (cap respected, cap never forces a promotion, uncapped equations
unaffected, cap below current stage handled as specified), and a cheap end-to-end smoke run
on a small system with a low level count — System 3 or System 11, few levels — purely to
show the path executes.

Not permitted: running System 26, or any configuration expected to exceed a few minutes.

### B.8 Outputs

The new variant, its registration, the readout extension, tests, and a short report on the
verification performed. Nothing may be written to `studies/regression/history.jsonl` by
this work package.

State clearly in the delivery that the decisive run has not been executed and give the
exact command to start it.
