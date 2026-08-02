# CURRENT TASK

**Language: Julia**

## WP-C1b — Resolve the duplicated child-generation path and decide the coupling-term rule

WP-C1 is verified and committed (`d3fce98`): fingerprint unchanged, cap-disabled run
bit-identical to `evogrow_v2_2_stage_local`, capped smoke run on System 3 recovers the true
support. This work package cleans up three findings from the review of that delivery. It must not
change any verified behaviour except where explicitly stated below.

### Finding 1 — A load-bearing function was duplicated

`_expand_with_stage_caps` in `src/structure/evogrow.jl` is a near-verbatim copy of the existing
`_expand_equation_aware_with_usage_policy` in `src/structure/evogrow_v3_childgen.jl`, and
`_equation_capped_terms` is a near-verbatim copy of `_evogrow_v3_equation_terms`.

Two copies of the child-generation dispatch now exist, and they are used by the two variants we
are about to compare against each other. If one is ever changed and the other is not, the two
arms diverge for a reason that will not be visible in any result file.

There must be **one** implementation, shared by both variants.

### Finding 2 — The copy silently dropped the coupling-term coherence rule

The original path filters terms through `_evogrow_v3_term_available`, which contains an extra
rule beyond the stage check: a term referencing two or more variables is available to equation
`k` only if **every** referenced variable has itself reached that stage
(`minimum(eq_stages[v] for v in vars) >= stage`). The new copy checks only the stage of the
target equation and drops that clause.

So the two capped variants currently use different availability semantics for coupling terms —
the terms this project is fundamentally about — whenever stages are non-uniform.

**Decision, which you implement rather than re-derive: the coherence rule is removed for
cap-derived stage limits, in both capped variants.**

The reason it must go: the rule was written for v3, where `eq_stages` reflects *promotion
progress* and a low stage is temporary. A cap is a *permanent ceiling derived from the data*. If
equation 2 is permanently capped at stage 2, the coherence rule makes `u1*u2` unavailable to
equation 1 forever, even when equation 1's own cap is 3 — the cap silently becomes a global
ceiling for every coupling term and the true structure becomes unreachable. That is the same
failure mode WP-L4 hit on System 63, and the same principle applies: a restriction must rest on
positive evidence about the equation it restricts.

Important scoping question you must answer rather than assume: v3's promotion-driven stage
limits and the cap-derived limits can coexist in `EvoGrowStageCapped`. Determine whether the
coherence rule can be removed for cap-derived limits **without** changing v3's behaviour where
stages differ because of promotion rather than because of a cap. If the two cannot be separated
cleanly, stop and report the conflict instead of choosing one.

### Finding 3 — The report asserts results as hardcoded prose

`studies/regression/verify_wp_c1.jl` writes the line "No parser or cap-estimator disagreement
surfaced." as a string literal, independently of what the runs produced. The table values come
from real data; that sentence does not. A verification report must not contain claims that
cannot fail.

Derive every factual statement in the report from the measured records, or remove it. In
particular, the confirmed-cap section should compare against the expected caps and state the
comparison outcome as data.

### Also in scope, low risk

`stage_cap_policy::Any` in the `EvoGrow` struct is untyped because `src/structure/stage_cap.jl`
is included after `src/structure/evogrow.jl` in `src/EvoODE.jl`. If the include order can be
adjusted so the policy type is available at struct-definition time, do so and give the field its
proper type. If that reordering causes any other load problem, leave it as is and say so — this
is cosmetic and must not put the working state at risk.

### Verification

Re-run `studies/regression/verify_wp_c1.jl` and confirm all three results still hold:

- `config_fingerprint()` is still `df5db7763bcd2449`
- cap-disabled on System 11 seed 42 is still bit-identical to `evogrow_v2_2_stage_local`,
  loss `4.402192340718147e-15`, support `[["u1", "u1^2", "u1^3"]]`
- capped smoke on System 3 seed 42 still gives cap `[2]`, final stage 2, overshoot 0,
  loss `1.3476451847014113e-08`, support `[["u1", "u1^2"]]`, `pruned_match = true`

Any deviation from these numbers is a regression and must be reported, not explained away.

Additionally, demonstrate that the coupling-term change is inert on the five regression systems.
Their caps are `3 → [2]`, `11 → [4]`, `26 → [3,3]`, `31 → [3,3]`, `63 → all nothing`, all
uniform, and the coherence rule has no effect when stages are uniform. Show this rather than
assert it, so the four already-completed capped cells are provably unaffected.

Update `codex/REPORT_WP_C1.md` or add `codex/REPORT_WP_C1b.md` with the outcome.

### Hard constraints

- **Do not run the regression matrix.** The decisive cells are multi-hour and are started by the
  user. Only the verification script above may be executed.
- Do not write to `studies/regression/history.jsonl`.
- Do not change `FINGERPRINT_VARIANT_LABELS` or the `lookahead_stage_cap` fingerprint payload.
- Do not change `estimate_stage_caps`.
- Generated output goes to its own subfolder under `outputs/`.
- If any decision above turns out to be unimplementable as stated, stop and report the conflict
  rather than choosing different semantics silently. The comparability of the two capped arms is
  the whole point of this work package.
