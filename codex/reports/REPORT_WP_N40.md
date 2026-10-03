# REPORT WP-N40

## Change

Added `baselines/recompute_odeformer_grid_structure.py`.

The script recomputes ODEFormer structure fields from existing grid records without running ODEFormer and without overwriting the raw grid files. It writes sidecar outputs next to each input:

- `records_structure_recomputed.jsonl`
- `records_structure_recomputed.csv`
- `structure_recompute_manifest.json`

`analysis/scripts/aggregate/run_phasec_sindy_baseline.py pair-odeformer` now accepts `records.jsonl` as well as `records.csv`.

## Recomputed Grid Outputs

| grid | records | raw hits | pruned hits | outside-basis records | code hash |
|---|---:|---:|---:|---:|---|
| reference_orion_55e9c75 | 1512 | 126 | 129 | 852 | `9a8420592f03db186a90c8091d364e2122c89b60c7bb4ce4a6f75aa3d7022962` |
| candidate_orion_8e0e699 | 1512 | 132 | 132 | 824 | `9a8420592f03db186a90c8091d364e2122c89b60c7bb4ce4a6f75aa3d7022962` |

Paths:

```text
analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records_structure_recomputed.jsonl
analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records_structure_recomputed.csv
analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/structure_recompute_manifest.json

analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_orion_8e0e699/records_structure_recomputed.jsonl
analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_orion_8e0e699/records_structure_recomputed.csv
analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_orion_8e0e699/structure_recompute_manifest.json
```

## WP-N31 Reaggregation Outputs

Reference grid:

```text
outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired.csv
outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired_summary.csv
outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired_summary_comparison.csv
```

Candidate grid:

```text
outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_candidate/phasec_odeformer_paired.csv
outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_candidate/phasec_odeformer_paired_summary.csv
```

The old-vs-new reference comparison has 80 matched summary rows. `n_units` delta is 0 for all 80 rows.

R2 controls:

```text
max abs delta odeformer_r2_gt_0_9_rate_over_units = 0.0
max abs delta odeformer_r2_variance_weighted_gt_0_9_rate_over_units = 0.0
```

Structure rates changed in 16 rows. Old raw/pruned structure rates were 0.0 in every changed row.

| config | regime | dim | threeway | raw new | pruned new | R2 delta | weighted R2 delta |
|---|---|---:|---|---:|---:|---:|---:|
| beam10_noopt | generalization | 1 | fully_representable | 0.409091 | 0.409091 | 0.0 | 0.0 |
| beam10_noopt | generalization | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |
| beam10_noopt | reconstruction | 1 | fully_representable | 0.409091 | 0.409091 | 0.0 | 0.0 |
| beam10_noopt | reconstruction | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |
| beam10_opt | generalization | 1 | fully_representable | 0.409091 | 0.409091 | 0.0 | 0.0 |
| beam10_opt | generalization | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |
| beam10_opt | reconstruction | 1 | fully_representable | 0.409091 | 0.409091 | 0.0 | 0.0 |
| beam10_opt | reconstruction | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |
| beam50_noopt | generalization | 1 | fully_representable | 0.363636 | 0.363636 | 0.0 | 0.0 |
| beam50_noopt | generalization | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |
| beam50_noopt | reconstruction | 1 | fully_representable | 0.363636 | 0.363636 | 0.0 | 0.0 |
| beam50_noopt | reconstruction | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |
| beam50_opt | generalization | 1 | fully_representable | 0.363636 | 0.409091 | 0.0 | 0.0 |
| beam50_opt | generalization | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |
| beam50_opt | reconstruction | 1 | fully_representable | 0.363636 | 0.409091 | 0.0 | 0.0 |
| beam50_opt | reconstruction | 2 | fully_representable | 0.100000 | 0.100000 | 0.0 | 0.0 |

All other config/dimension/threeway rows have unchanged structure rates under the WP-N31 summary policy.

## Commands

```text
python baselines/recompute_odeformer_grid_structure.py
```

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py pair-odeformer --odeformer-records analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records_structure_recomputed.csv --evogrow-records-dir outputs/phase_c_campaign_221a3a7/records --evogrow-generalization outputs/wp_n5_ic_generalization_phase_c/cells.csv --representability-threeway analysis/data/paper1_phaseC_v1/representability_threeway/representability_threeway_by_system.csv --output outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired.csv --summary-output outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired_summary.csv
```

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py pair-odeformer --odeformer-records analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_orion_8e0e699/records_structure_recomputed.csv --evogrow-records-dir outputs/phase_c_campaign_221a3a7/records --evogrow-generalization outputs/wp_n5_ic_generalization_phase_c/cells.csv --representability-threeway analysis/data/paper1_phaseC_v1/representability_threeway/representability_threeway_by_system.csv --output outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_candidate/phasec_odeformer_paired.csv --summary-output outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_candidate/phasec_odeformer_paired_summary.csv
```

## Tests

```text
python -m py_compile baselines/recompute_odeformer_grid_structure.py baselines/run_odeformer_noise.py analysis/scripts/aggregate/run_phasec_sindy_baseline.py
```

```text
python -m pytest baselines/tests/test_recompute_odeformer_grid_structure.py baselines/tests/test_run_odeformer_noise.py analysis/tests/test_phasec_sindy_baseline.py --basetemp .pytest_tmp
32 passed in 15.87s
```

