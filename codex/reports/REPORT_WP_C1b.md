# WP-C1b Report

## What Changed

- Replaced the duplicated v2.2 stage-cap child-generation copy with the shared `_expand_equation_aware_with_usage_policy` implementation.
- Added explicit child-generation semantics for cap-derived limits: cap-limited referenced variables do not block coupling terms in another equation.
- Kept v3's default promotion-driven coupling coherence for uncapped/non-cap-derived stage differences.
- `estimate_stage_caps`, `FINGERPRINT_VARIANT_LABELS`, and the `lookahead_stage_cap` fingerprint payload were not changed.

## Fingerprint

- `config_fingerprint()` = `df5db7763bcd2449`.
- Expected fingerprint = `df5db7763bcd2449`.
- Match: `true`.

## Cap-Disabled Equivalence

System 11, seed 42, comparing `evogrow_v2_2_stage_local` against the same v2.2 substrate with `stage_caps = [nothing]`.

| metric | v2.2 stage-local | v2.2 cap-disabled |
| --- | --- | --- |
| loss | 4.402192340718147e-15 | 4.402192340718147e-15 |
| final_stage | 4 | 4 |
| pruned_match | true | true |
| support_terms | [["u1", "u1^2", "u1^3"]] | [["u1", "u1^2", "u1^3"]] |

Bit-identical comparison on reported values: `true`.
Expected-value check: `true`.

## Cap-Enabled Smoke Test

System 3, seed 42, variant `evogrow_v2_2_stage_capped`.

| metric | value |
| --- | --- |
| stage_caps | Union{Nothing, Int64}[2] |
| loss | 1.3476451847014113e-8 |
| final_stage | 2 |
| stage_overshoot | 0 |
| eq_final_stages | [2] |
| eq_overshoot | [0] |
| eq_wasted_levels | [0] |
| pruned_match | true |
| support_terms | [["u1", "u1^2"]] |

Expected-value check: `true`.

## Confirmed Cap Values

| system | expected | observed | match |
| --- | --- | --- | --- |
| 3 | Union{Nothing, Int64}[2] | Union{Nothing, Int64}[2] | true |
| 11 | Union{Nothing, Int64}[4] | Union{Nothing, Int64}[4] | true |
| 26 | Union{Nothing, Int64}[3, 3] | Union{Nothing, Int64}[3, 3] | true |
| 31 | Union{Nothing, Int64}[3, 3] | Union{Nothing, Int64}[3, 3] | true |
| 63 | Union{Nothing, Int64}[nothing, nothing, nothing, nothing] | Union{Nothing, Int64}[nothing, nothing, nothing, nothing] | true |

Cap comparison check: `true`.

## Coupling-Term Rule Inertness

| system | caps | coherent vs cap-derived availability identical |
| --- | --- | --- |
| 3 | Union{Nothing, Int64}[2] | true |
| 11 | Union{Nothing, Int64}[4] | true |
| 26 | Union{Nothing, Int64}[3, 3] | true |
| 31 | Union{Nothing, Int64}[3, 3] | true |
| 63 | Union{Nothing, Int64}[nothing, nothing, nothing, nothing] | true |

Coupling-inertness check: `true`.

### Coupling Details

System 3:
- stage 1: eq_stages=[1], same=true, allowed=[["u1"]]
- stage 2: eq_stages=[2], same=true, allowed=[["u1", "u1^2"]]

System 11:
- stage 1: eq_stages=[1], same=true, allowed=[["u1"]]
- stage 2: eq_stages=[2], same=true, allowed=[["u1", "u1^2"]]
- stage 3: eq_stages=[3], same=true, allowed=[["u1", "u1^2"]]
- stage 4: eq_stages=[4], same=true, allowed=[["u1", "u1^2", "u1^3"]]

System 26:
- stage 1: eq_stages=[1, 1], same=true, allowed=[["u1", "u2"], ["u1", "u2"]]
- stage 2: eq_stages=[2, 2], same=true, allowed=[["u1", "u2", "u1^2", "u2^2"], ["u1", "u2", "u1^2", "u2^2"]]
- stage 3: eq_stages=[3, 3], same=true, allowed=[["u1", "u2", "u1^2", "u2^2", "u1*u2"], ["u1", "u2", "u1^2", "u2^2", "u1*u2"]]

System 31:
- stage 1: eq_stages=[1, 1], same=true, allowed=[["u1", "u2"], ["u1", "u2"]]
- stage 2: eq_stages=[2, 2], same=true, allowed=[["u1", "u2", "u1^2", "u2^2"], ["u1", "u2", "u1^2", "u2^2"]]
- stage 3: eq_stages=[3, 3], same=true, allowed=[["u1", "u2", "u1^2", "u2^2", "u1*u2"], ["u1", "u2", "u1^2", "u2^2", "u1*u2"]]

System 63:
- stage 1: eq_stages=[1, 1, 1, 1], same=true, allowed=[["u1", "u2", "u3", "u4"], ["u1", "u2", "u3", "u4"], ["u1", "u2", "u3", "u4"], ["u1", "u2", "u3", "u4"]]
- stage 2: eq_stages=[2, 2, 2, 2], same=true, allowed=[["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2"]]
- stage 3: eq_stages=[3, 3, 3, 3], same=true, allowed=[["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4"]]
- stage 4: eq_stages=[4, 4, 4, 4], same=true, allowed=[["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3"]]
- stage 5: eq_stages=[5, 5, 5, 5], same=true, allowed=[["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3", "sin(u1)", "cos(u1)", "sin(u2)", "cos(u2)", "sin(u3)", "cos(u3)", "sin(u4)", "cos(u4)"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3", "sin(u1)", "cos(u1)", "sin(u2)", "cos(u2)", "sin(u3)", "cos(u3)", "sin(u4)", "cos(u4)"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3", "sin(u1)", "cos(u1)", "sin(u2)", "cos(u2)", "sin(u3)", "cos(u3)", "sin(u4)", "cos(u4)"], ["u1", "u2", "u3", "u4", "u1^2", "u2^2", "u3^2", "u4^2", "u1*u2", "u1*u3", "u1*u4", "u2*u3", "u2*u4", "u3*u4", "u1^3", "u2^3", "u3^3", "u4^3", "sin(u1)", "cos(u1)", "sin(u2)", "cos(u2)", "sin(u3)", "cos(u3)", "sin(u4)", "cos(u4)"]]

## Overall

- All checks passed: `true`.

