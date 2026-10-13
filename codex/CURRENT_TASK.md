# WP-N46b — clean-only mode for the §9.3 hierarchy
**Language: Python**

## Why

Claude ran the WP-N46 clean re-run (`outputs/c6_n46_clean_dop853/shard_0..9`, 378 cells, 11,340 model rows, all three
methods, DOP853) and the C-4c re-run (`analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export_n46/`). The
`hierarchy_n46` command from `SCRIPTS.md` then fails:

```
Error: C-6 SINDy merge expected 4,536 distinct cells, found 378
```

The §9.3 hierarchy reads only the clean (σ = 0, ρ = 0) rows, but the merge check demands the full noisy export. The
noisy re-run is a separate decision; the clean table is needed now.

## Deliverables

- A flag on `aggregate_phasec_hierarchy_n43.py` (e.g. `--clean-only`) under which the merge and its checks expect exactly
  the 378 clean cells (σ = 0, ρ = 0) and fail on anything else — no silent acceptance of partial data. Without the flag,
  behaviour unchanged.
- Under `--clean-only`, SINDy, Weak-SINDy and E-SINDy all come from the one shard tree (the N46 shards hold all three
  methods); E-SINDy rows must reach the hierarchy (do not drop them because `--esindy-*` is empty). If your WP-N46
  changes already route E-SINDy from the main shard tree, say so in the report.
- Every control that compares the C-6 clean rows against C-4c must keep working (both DOP853 now). Record the flag in
  `metadata.json`.
- Run it yourself — the aggregation is cheap and reads existing files:
  `--sindy-shards-dir outputs\c6_n46_clean_dop853 --sindy-merged-dir outputs\c6_n46_clean_dop853\merged
  --sindy-c4c-details analysis\data\paper1_phaseC_v1\phasec_sindy_baseline_wp_c4c_export_n46\details.csv
  --output-dir outputs\phase_c_campaign_221a3a7\agg\hierarchy_n46 --clean-only`, and the old-vs-new delta table against
  `analysis/data/paper1_phaseC_v1/hierarchy_n45/`.
- Update the `hierarchy_n46` command in `SCRIPTS.md`. Test for the flag (accepts 378 clean cells, rejects a noisy row
  and a missing cell).

## Verboten

- Changing metrics, thresholds, the variance weighting, strata, or the EvoGrow/ODEFormer inputs. Re-running any fit.
  Committing. Editing this file.

## Abnahme

- `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n46/` written, all controls pass (report the count), delta table
  present; tests pass; report `codex/reports/REPORT_WP_N46B.md` with the control count and the overall rows per method
  and configuration (old → new, both regimes, pruned and raw structure).
- `STATUS.md` `done` or `blocked`.
