# CURRENT TASK

**Language: Julia**

## WP-C1 — Look-ahead stage cap on the v2.2 substrate

### Why this exists

The look-ahead stage cap currently only exists as `EvoGrowStageCapped`, which is `EvoGrowV3`
*plus* cap. Three regression cells on System 31 (run 2026-08-02) separated the two effects and
found that the v3 substrate, not the cap, carries the dominant share of the loss regression:
on seed 42, v2.2 reaches 6.808e-11, v3 reaches 1.285e-4 (about six orders worse), and the cap
adds two more orders on top (1.678e-2).

The reason is known and measured: v3's per-equation promotion signal `r_k` is the derivative
residual, and WP-L2 showed it to be contaminated by derivative-estimation error, biasing it
toward "more terms help".

But the cap does not need v3. `estimate_stage_caps` reads only the trajectory and the basis; the
caps are a vector precomputed before the search starts. The cap is coupled to v3 today only
because it was wired into v3's promotion path.

This work package puts the cap on the v2.2 substrate, so the good mechanism runs on the
uncontaminated promotion rule. If the resulting variant keeps v2.2's fit quality while removing
the stage overshoot, it is the final Paper 1 variant.

### Deliverable

A new structure-search variant, label **`evogrow_v2_2_stage_capped`**, registered in the
regression runner and runnable there.

### Fixed design decisions

These are decided. Do not renegotiate them; implement them.

#### 1. Promotion rule is v2.2's, unchanged

Stage progression uses the existing v2.2 mechanism (`:stage_local` progression, `:hard` usage,
stage-local plateau with minimum stage budget). **The per-equation derivative residual `r_k` must
not appear anywhere in this variant.** That signal is the thing being removed.

#### 2. The cap restricts terms per equation

The cap vector is per equation. v2.2 carries a single global stage counter. The cap must
therefore act as a **per-equation term restriction**: equation `k` may only use basis terms from
stages at or below `cap[k]`. A cap entry of `nothing` means no restriction for that equation.

Do not collapse the cap to a single global value by taking the maximum. That would let an
equation with a low cap still receive higher-stage terms whenever some other equation needs
them, which reintroduces exactly the per-equation overshoot the cap removes.

Equation-aware child generation already exists from WP-v3.3. Reusing it is acceptable and
expected — it is the child-generation path, not the contaminated promotion signal. Reuse or a
separate path is your call; the observable behaviour above is what matters.

#### 3. Promotion stops when no equation can still gain

With per-equation caps, raising the global stage counter past every equation's cap unlocks
nothing and only burns levels. Promotion must be blocked once every equation has reached its cap
— that is, the effective maximum stage for the global counter is the maximum over the cap
entries, with `nothing` counting as the basis maximum.

#### 4. Metrics stay comparable to the existing cells

Record `eq_final_stages`, `eq_overshoot` and `eq_wasted_levels` with the same meaning as in the
v3 variants, so the new cells sit in the same table as the existing ones. For a globally staged
algorithm the effective stage of equation `k` is the global stage limited by that equation's cap.

#### 5. The config fingerprint must not change

`FINGERPRINT_VARIANT_LABELS` in `studies/regression/run_regression.jl` is a frozen list that
feeds the fingerprint hash. **Do not add the new variant to it, and do not touch the
`lookahead_stage_cap` payload.** The current fingerprint is `df5db7763bcd2449` and must stay
byte-identical, otherwise all 32 existing history records become incomparable and the entire
point of these runs is lost.

Each run is independent, so an additional runnable variant cannot affect any other variant's
result. Keeping it out of the fingerprint is correct, not a workaround.

Consequence to accept without repairing: the `lookahead_stage_cap.variant` field in the
fingerprint payload names only `evogrow_v3_stage_capped`, which becomes an incomplete
description once a second variant uses the cap. Leave it. Note it in your report; changing it
changes the hash.

#### 6. `estimate_stage_caps` must not be modified

The cap computation is verified (WP-L4 through WP-L5d) and its caps are known: System 3 → `[2]`,
11 → `[4]`, 26 → `[3,3]`, 31 → `[3,3]`, 63 → all `nothing`. It is consumed here, not changed.

Likewise `EvoGrowV3` and `EvoGrowStageCapped` must keep their current behaviour exactly. This is
an addition, not a refactor.

### Verification

#### Mandatory: cap-disabled equivalence

With the cap disabled (or all cap entries `nothing`), the new variant must be **bit-identical to
the existing `evogrow_v2_2_stage_local`** — same loss, same support, same final stage. This is
the same discipline the v3.2 lockstep bridge was held to, and it is what proves the cap is the
only thing that changed.

Verify this deterministically on a cheap system and report the compared values, not a verdict.

#### Mandatory: cap-enabled smoke test

One run on **System 3, seed 42** (1D, minutes). Expected: cap `[2]`, final stage 2, no overshoot,
and a loss in the same range as v2.2 on that system. Report the actual numbers.

#### Report

Write findings to `codex/REPORT_WP_C1.md`: what changed, the equivalence comparison, the smoke
test numbers, the confirmed cap values, and anything that surprised you.

### Hard constraints

- **Do not run the regression matrix.** The decisive cells (System 26 seed 42; System 31 seeds
  42, 123, 7) are multi-hour runs and are started by the user, not by you. Only the two cheap
  verifications above may be executed.
- If a verification exceeds a few minutes, stop and report rather than letting it run.
- Do not write to `studies/regression/history.jsonl`.
- Any generated output goes to its own subfolder under `outputs/`, never directly into a shared
  output directory.
- If a fixed decision above turns out to be unimplementable as stated, stop and report the
  conflict. Do not silently choose a different semantics — the comparability of these cells is
  the entire deliverable.
