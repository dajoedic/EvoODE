# WP-C1 Report

## What Changed

- Added regression variant `evogrow_v2_2_stage_capped`.
- The variant uses the existing v2.2 `:stage_local` promotion and `:hard` usage path.
- The look-ahead cap is applied only as a per-equation term restriction: equation `k` sees terms with stage `<= min(global_stage, cap[k])`; `nothing` means the basis maximum.
- The effective global promotion maximum is the maximum cap, with `nothing` counted as the basis maximum.
- `estimate_stage_caps`, `EvoGrowV3`, and `EvoGrowStageCapped` were not changed.

## Fingerprint

- `config_fingerprint()` = `df5db7763bcd2449`.
- `FINGERPRINT_VARIANT_LABELS` and the `lookahead_stage_cap` payload were left unchanged. The payload still names only `evogrow_v3_stage_capped`, which is now incomplete but intentionally frozen.

## Cap-Disabled Equivalence

System 11, seed 42, comparing `evogrow_v2_2_stage_local` against the same v2.2 substrate with `stage_caps = [nothing]`.

| metric | v2.2 stage-local | v2.2 cap-disabled |
| --- | --- | --- |
| loss | 4.402192340718147e-15 | 4.402192340718147e-15 |
| final_stage | 4 | 4 |
| pruned_match | true | true |
| support_terms | [["u1", "u1^2", "u1^3"]] | [["u1", "u1^2", "u1^3"]] |

Bit-identical comparison on reported values: `true`.

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

## Confirmed Cap Values

| system | caps |
| --- | --- |
| 3 | Union{Nothing, Int64}[2] |
| 11 | Union{Nothing, Int64}[4] |
| 26 | Union{Nothing, Int64}[3, 3] |
| 31 | Union{Nothing, Int64}[3, 3] |
| 63 | Union{Nothing, Int64}[nothing, nothing, nothing, nothing] |

## Surprises

- No parser or cap-estimator disagreement surfaced.
- The fingerprint payload's cap variant label is now incomplete by design; changing it would change the frozen hash.

