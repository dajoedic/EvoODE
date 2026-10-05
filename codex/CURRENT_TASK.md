# WP-N43b — close the variance-weighted gaps in the §9.3 hierarchy, and switch SINDy to the canonical source
**Language: Python**

## Why

WP-N43 (`60a4393`, `codex/reports/REPORT_WP_N43.md`) built the plan §9.3 hierarchy and passed its
controls, but the §9.3 headline — **variance-weighted generalization R²** — is `NaN` for EvoGrow
and SINDy, and SINDy has no pruned structural F1. All three are recoverable without new runs.

A second defect was found by Claude on 2026-10-05: WP-N43 (default `--sindy-details`) and the
WP-N30 / WP-N31 pairing commands in `SCRIPTS.md` read
`analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv`. That file is the **old,
self-integrated** SINDy run (DOP853). The canonical C-4 run consumes the campaign's exported bytes
(WP-C4c, `DIARY.md`): `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export/details.csv`.
Against the canonical file the old one differs in 66 of 2,520 raw/pruned supports and 4 of 2,520
R² > 0.9 verdicts.

## Inputs

1. **SINDy, C-6 run, done 2026-10-05 by Claude** — ten shard outputs
   `outputs/c6_sindy_baselines_5dd1df8/shard_{0..9}/details.csv` over all 4,536 exported cells of
   `outputs/phase_c_c6_data_conditions_5dd1df8/index.csv` (63 systems × 2 IC sets × 12 conditions ×
   3 realizations), ten configurations each. They carry per-dimension R², variance-weighted R² and
   pruned structural F1 / precision / recall. Shard 9 additionally holds
   `control_c4_reproduction/`: on the (0,0) data it reproduces the canonical WP-C4c file in
   2,520 / 2,520 rows on status, raw and pruned support and the R² > 0.9 verdict, with R² identical
   to 1e-12 except 40 diverged rows. Its scripted control status says "failed" only because the
   script's reference has 80 rows; ignore that status, verify the above yourself and report it.
2. **EvoGrow generalization per dimension** —
   `outputs/wp_n5_ic_generalization_phase_c/shard_001_of_001/results.jsonl` carries
   `generalization_r2_by_dim` (non-null in 337 of 378; check that the rest are exactly the diverged
   / non-finite cells). The variance weights are the per-dimension variances of the **clean target
   trajectory** (the second IC's reference trajectory), as defined in plan §6b and implemented in
   `analysis/scripts/aggregate/aggregate_variance_weighted_r2.py` — reuse that code and its weight
   source rather than writing a second one.

## What to do

1. **Merge the SINDy shards** into one table under `outputs/c6_sindy_baselines_5dd1df8/merged/`
   (`details.csv`, plus a summary built with the harness's own `build_summary` from
   `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`). Check: 4,536 distinct cells,
   no duplicate keys, every configuration present for every cell, the export hash check passed for
   every row. This merged table is the C-6 SINDy/Weak-SINDy deliverable.
2. **SINDy source in the hierarchy.** Give `aggregate_phasec_hierarchy_n43.py` the ability to read
   the clean SINDy rows from the merged C-6 table, condition (σ, ρ) = (0, 0). The three realizations
   of (0,0) are the same data; assert that the results are identical across them and then use one,
   so a deterministic method is not counted three times. Make this the default SINDy source.
   Keep the WP-C4c file loadable as a cross-check.
3. **EvoGrow variance-weighted generalization** from input 2. Control: the arithmetic mean of
   `generalization_r2_by_dim` reproduces the stored `generalization_r2` in every non-diverged cell
   (same tolerance as WP-N20); on dim 1 variance-weighted equals arithmetic exactly.
4. **SINDy pruned structural F1 / precision / recall** from the merged table (exact systems only).
5. Re-run the hierarchy into `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43b/` (do not
   overwrite `hierarchy_n43/`).

## Controls (report each with numbers)

- EvoGrow back-compatibility from WP-N43 still passes unchanged.
- ODEFormer back-compatibility still passes unchanged.
- SINDy: the old back-compatibility target (`sindy_n31`) was built on the old source. **Do not force
  it to pass.** Report, per configuration and regime, the old unit-level rate, the new one, and the
  difference, and list every row whose R² > 0.9 verdict or structure hit changed. This is a finding
  for Claude, not a failure.
- SINDy new source vs WP-C4c: identical R² > 0.9 verdicts and supports on all 2,520 rows.
- Equal system weight and dim-1 equality hold for all three methods, now including variance-weighted
  generalization.

A failed control other than the SINDy back-compatibility one is a stop: `blocked`, with numbers.

## Rules

No SINDy, ODEFormer or Julia runs. Python only. Pruning rule and §6b definitions unchanged. Do not
edit `SCRIPTS.md` command blocks beyond adding the new command; Claude updates the WP-N30/N31
references after reviewing the deltas. Tests for the new loader paths (realization-identity assert,
variance-weight control) in the existing WP-N43 test file.

## Report

`codex/reports/REPORT_WP_N43B.md`: merge checks, all controls, the SINDy old-vs-new delta table,
and the updated overall benchmark table (all methods, all configurations, both aggregations,
structure). Leave everything uncommitted; status into `codex/STATUS.md`.
