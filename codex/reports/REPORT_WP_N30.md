# REPORT WP-N30

## Defect

The old Claim-D pairing kept only SINDy generalization rows and joined them to EvoGrow record `r2`, which is the reconstruction score. Because it joined on `initial_condition_set`, SINDy models trained on one IC and evaluated on the other were compared with EvoGrow models trained and evaluated on the target IC.

## Change

`run_phasec_sindy_baseline.py pair` now requires:

```text
--evogrow-generalization <WP-N5 cells.csv>
```

The pairing key is `(system_id, source_initial_condition_set, target_initial_condition_set, direction, regime)`. EvoGrow R2 comes from WP-N5 `reconstruction_r2` / `generalization_r2`; records remain the source for identity, fingerprints, raw/pruned structure hits, `total_parameter_fits`, and `total_loss_evals`.

The implementation aborts if records and WP-N5 `cells.csv` do not cover the same C-1 cells, or if `cells.csv:reconstruction_r2` differs from record `r2` by more than `1.0e-12`.

## Outputs

```text
outputs/phase_c_campaign_221a3a7/agg/sindy_n30/phasec_sindy_paired.csv
outputs/phase_c_campaign_221a3a7/agg/sindy_n30/phasec_sindy_paired_summary.csv
```

Generated rows:

```text
paired rows: 2520
summary rows: 400
libraries: 10
regimes: reconstruction 1260, generalization 1260
generalization structure non-null counts: SINDy 0, EvoGrow 0
```

## Counterprobe

Rates are over all units. EvoGrow is the mean over available seeds per unit, then averaged over units. SINDy min/max is over the ten libraries with both directions pooled.

| dim | units | EvoGrow reconstruction | EvoGrow generalization | SINDy reconstruction min-max | SINDy generalization min-max |
|---:|---:|---:|---:|---:|---:|
| 1 | 46 | 0.978261 | 0.702899 | 0.673913-0.956522 | 0.456522-0.608696 |
| 2 | 56 | 0.916667 | 0.255952 | 0.553571-0.732143 | 0.214286-0.464286 |
| 3 | 20 | 0.283333 | 0.016667 | 0.000000-0.150000 | 0.000000-0.100000 |
| 4 | 4 | 0.416667 | 0.000000 | 0.000000-0.500000 | 0.000000-0.000000 |

This matches the task reference table after rounding to three decimals.

## Tests

```text
python -m pytest analysis/tests/test_phasec_sindy_baseline.py --basetemp .pytest_tmp
15 passed in 8.20s
```

```text
python -m pytest analysis/tests --basetemp .pytest_tmp
1 failed, 93 passed, 222552 warnings in 30.83s
```

The failing test is outside WP-N30:

```text
analysis/tests/test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts
AssertionError: missing stdout line "Reproduction matches frozen diagnostics excluding generated_at: yes"
```

The same failure appeared before the final WP-N30 patch; `analysis/tests/test_phasec_sindy_baseline.py` is green.
