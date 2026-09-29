# REPORT WP-N31

## Change

`analysis/scripts/aggregate/run_phasec_sindy_baseline.py` now has:

- `pair-odeformer`, pairing canonical ODEFormer `reference_orion_55e9c75/records.csv` with C-1 EvoGrow on `(system_id, source_initial_condition_set, target_initial_condition_set, direction, regime)`.
- `--representability-threeway` for SINDy pairing. The old `phasec_representability_threeway` column remains in the paired output; summaries use `phasec_true_threeway_class` from `representability_threeway_by_system.csv`.

Policies in the paired outputs:

- ODEFormer: `mean_rate_over_3_repetitions`; invalid status, missing R2, and `timeout_enforced` count as not `R2 > 0.9`.
- EvoGrow: `mean_rate_over_available_phasec_seeds`, unchanged from WP-N30.
- Canonical R2 is `_arithmetic_mean`; `_variance_weighted` is reported as a sensitivity rate.
- Structure-hit summary rates are reported only for `fully_representable`; other classes are `NaN`.

## Outputs

```text
outputs/phase_c_campaign_221a3a7/agg/odeformer_n31/phasec_odeformer_paired.csv
outputs/phase_c_campaign_221a3a7/agg/odeformer_n31/phasec_odeformer_paired_summary.csv
outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired.csv
outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired_summary.csv
```

Counts:

```text
ODEFormer paired rows: 1008
ODEFormer summary rows: 80
SINDy paired rows: 2520
SINDy summary rows: 400
true classes: fully_representable 30, partially_representable 31, non_representable 2
```

## ODEFormer counterprobe

Rates are `R2 > 0.9`, arithmetic mean over states, averaged over the 3 ODEFormer repetitions per unit and then over units.

| config | reconstruction | generalization |
|---|---:|---:|
| beam10_noopt | 0.576720 | 0.261905 |
| beam10_opt | 0.727513 | 0.309524 |
| beam50_noopt | 0.648148 | 0.277778 |
| beam50_opt | 0.775132 | 0.322751 |

Rounded to three decimals these match Claude's ad-hoc values: 0.577/0.262, 0.728/0.310, 0.648/0.278, 0.775/0.323.

Beam50 opt, generalization, by dimension:

| dim | rate |
|---:|---:|
| 1 | 0.586957 |
| 2 | 0.244048 |
| 3 | 0.000000 |
| 4 | 0.000000 |

Rounded to three decimals these match 0.587, 0.244, 0.000, 0.000.

## SINDy stratification

`outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired_summary.csv` has aggregation scope `dimension_by_phasec_true_threeway_class`. The legacy `phasec_representability_threeway` values from `details.csv` remain in `phasec_sindy_paired.csv`; they are not the true three-way class, only the first non-representable-equation label from the old support table.

## Commands

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py pair-odeformer --odeformer-records analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.csv --evogrow-records-dir outputs/phase_c_campaign_221a3a7/records --evogrow-generalization outputs/wp_n5_ic_generalization_phase_c/cells.csv --representability-threeway analysis/data/paper1_phaseC_v1/representability_threeway/representability_threeway_by_system.csv --output outputs/phase_c_campaign_221a3a7/agg/odeformer_n31/phasec_odeformer_paired.csv --summary-output outputs/phase_c_campaign_221a3a7/agg/odeformer_n31/phasec_odeformer_paired_summary.csv

python analysis/scripts/aggregate/run_phasec_sindy_baseline.py pair --sindy-details analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv --evogrow-records-dir outputs/phase_c_campaign_221a3a7/records --evogrow-generalization outputs/wp_n5_ic_generalization_phase_c/cells.csv --representability-threeway analysis/data/paper1_phaseC_v1/representability_threeway/representability_threeway_by_system.csv --output outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired.csv --summary-output outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired_summary.csv
```

## Tests

```text
python -m py_compile analysis/scripts/aggregate/run_phasec_sindy_baseline.py
```

```text
python -m pytest analysis/tests/test_phasec_sindy_baseline.py --basetemp .pytest_tmp
20 passed in 6.70s
```

```text
python -m pytest analysis/tests --basetemp .pytest_tmp
1 failed, 98 passed, 222552 warnings in 32.77s
```

The failing test is the known pre-existing Phase-A artifact stdout failure:

```text
analysis/tests/test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts
AssertionError: missing stdout line "Reproduction matches frozen diagnostics excluding generated_at: yes"
```
