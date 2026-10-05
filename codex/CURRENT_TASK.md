# WP-N43 — §9.3 aggregation hierarchy for EvoGrow, SINDy and ODEFormer (Phase C, clean data)
**Language: Python**

## Why

`docs/paper1_phaseC_benchmark_plan.md` §9.3 fixes one aggregation hierarchy for every method:

```text
equation -> run -> seeds (or noise realizations) within a direction -> both directions -> system -> benchmark
```

Every system carries equal weight. The final Phase C evaluation must be **recomputed** under this
hierarchy for EvoGrow and every baseline identically. Today's figures are in units of
(system, direction) — 82.3 % / 37.3 % and the WP-N30 / WP-N31 / WP-N40 tables — and §9.3 says they
are **not** carried in parallel. This is the open rest of backlog item P-02 in `CLAUDE.md`.

Read §9.2, §9.3 and §6b of the plan before starting. Claim D context: `CLAUDE.md`, Known Gaps,
"Generalization is the weak axis".

## Inputs (verify each path; report any that differs)

- **EvoGrow C-1, reconstruction:** the final strict registry
  `analysis/data/paper1_phaseC_v1/final_2026-10-05/phasec_analysis_registry_c1.csv` and/or the
  records under `outputs/phase_c_campaign_221a3a7/records`. Only the canonical C-1 arm enters the
  headline; C-2 (uncapped) and C-3 (pretuning) may be produced as additional rows, labelled.
- **EvoGrow C-1, generalization:** `outputs/wp_n5_ic_generalization_phase_c/cells.csv`.
- **SINDy (C-4):** `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv`, ten
  configurations, reconstruction and generalization rows.
- **ODEFormer:** reference grid
  `analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records_structure_recomputed.csv`
  (canonical) and candidate grid `.../candidate_orion_8e0e699/records_structure_recomputed.csv`
  (sensitivity arm only). Structure fields come from these WP-N40 sidecars, never from the raw
  grid records (their structure fields are empty — `CLAUDE.md`, Known Gaps).
- **Classes:** `analysis/data/paper1_phaseC_v1/representability_threeway/representability_threeway_by_system.csv`
  (three-way class) and the feasible-under-bound-10 label of plan §9.2 (24 feasible, 54–59
  infeasible, derived from true coefficients — reuse the existing extraction, do not re-derive by
  hand).

Reuse the existing pairing / loading code in `analysis/scripts/aggregate/run_phasec_sindy_baseline.py`
and `analysis/utils/metrics.py` where it fits; do not duplicate it.

## What to build

A new aggregation script under `analysis/scripts/aggregate/` (name it after its purpose) that
produces, for each method and each method configuration separately (SINDy: all ten configurations;
ODEFormer: every configuration of each grid; **no maximum over configurations is taken anywhere**):

1. **Per-run table** — one row per (method, configuration, system, direction, seed or repetition):
   reconstruction R² and generalization R² under **both** aggregations of §6b (arithmetic per-dim
   mean and variance-weighted), raw and pruned exact support match, structural F1 / precision /
   recall on the pruned support (exact systems only), divergence flag, IC, seed, noise level, subsampling ratio, realization (zero
   for this clean data).
2. **Per-system table** — aggregated through the hierarchy: within a direction over seeds or
   repetitions (share of runs for the rates, plus the median of continuous R²), then over both
   directions, giving one value per system.
3. **Benchmark table** — equal weight per system, reported overall and stratified by dimension,
   by three-way class, and (dim 3 only) feasible vs infeasible under bound 10. Rates: R² > 0.9
   reconstruction and generalization (both aggregations), raw and pruned exact recovery and mean
   structural F1 (exact systems only). Always both metric families together (Design Principle 9).
   Report the number of systems in every cell.
4. **Sensitivity table** — the number of runs that cross the 0.9 threshold between the arithmetic
   and variance-weighted aggregation, per method and dimension (§6b says this is published).

The script must take the inputs as arguments so that the same code later runs on the C-6 grid,
where the "seeds" level becomes seeds × noise realizations within one data condition and the
benchmark table gains (noise sigma, subsampling rho) as stratifying keys. Do not implement the C-6
loading now; make the hierarchy generic over these keys and state in the report what C-6 will need.

## Hard rules

- Exact and surrogate systems are never mixed in a structure metric (Design Principle 8).
- Divergent integrations count as R² ≤ 0.9, never as missing. Report how many there are.
- The pruning threshold is the frozen rule `tau = max(1e-6, 1e-3 * max_i |c_i|)`. Do not change it.
- If a method's input lacks per-dimension R² (needed for the variance-weighted figure), **do not
  approximate it**. Report the gap in the report with the exact missing field, and fill that column
  with NaN plus an explicit `*_available = False` flag. Claude decides whether to extend the
  producer.
- No new experiments, no re-running of SINDy, ODEFormer or Julia. Python only.

## Controls (must pass; report each)

1. **EvoGrow back-compatibility:** collapsing the per-run table to (system, direction) units with
   the arithmetic aggregation reproduces the published C-1 rates 82.3 % reconstruction and 37.3 %
   generalization over 126 units, and the per-dimension figures in `CLAUDE.md`
   (dim 1 97.8 / 70.3, dim 2 91.7 / 25.6, dim 3 28.3 / 1.7).
2. **SINDy and ODEFormer back-compatibility:** the same collapse reproduces the per-configuration
   rates in `outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired_summary.csv` and
   `outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired_summary.csv`.
3. **Variance weighting on dim 1** equals the arithmetic figure exactly for every method.
4. **Equal system weight:** the benchmark rate equals the unweighted mean of the per-system values.

A failed control is a stop: report `blocked` with the numbers, do not adjust the aggregation.

## Outputs

`outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43/` — per-run, per-system, benchmark and
sensitivity CSVs, plus a `metadata.json` listing input paths and their SHA-256.

## Tests

`analysis/tests/test_<script name>.py`: hierarchy order on a synthetic fixture (a system with two
directions and three seeds where the naive pooled rate and the hierarchical rate differ), equal
system weight, divergent run counted as failure, NaN flag when per-dim R² is missing.

## Report

`codex/reports/REPORT_WP_N43.md`: commands, control results with numbers, the benchmark table for
the canonical configurations, the list of missing fields, and what C-6 will need. Do not commit;
leave the files uncommitted and write the status into `codex/STATUS.md`.
