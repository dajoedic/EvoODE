# REPORT WP-N14b

## Result

Fixed the Phase-C cap-ablation pair equality allowlist in
`analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py` and added the missing positive
fixture in `analysis/tests/test_phasec_cap_ablation.py`.

Newly allowed pair differences:

- `campaign_manifest_index`: added because each paired arm has its own campaign manifest row; it is
  bookkeeping for the campaign cell, not an experimental condition.
- `stage_cap_policy_active`: added because the capped arm must have the stage-cap policy active and
  the uncapped arm must not; this is the intended intervention being compared.

Already present and rechecked:

- `stage_caps`: already allowed; capped and uncapped arms intentionally differ in cap values.

Checked and not added:

- `stage_cap_behavior_fingerprint`: not added; it fingerprints cap behavior and must match across
  paired arms.
- `config_fingerprint`: not added; it fingerprints run configuration and must match across paired
  arms.
- `use_pretuning`: not added; pretuning is a real condition, not cap bookkeeping.
- `screening_budgets_active`: not added; screening-budget enablement is a real condition.
- `derivative_screening_active`: not added; derivative-screening enablement is a real condition.
- `LOOKAHEAD_CAP_POLICY` fields from `phase_b_config.jl` and `run_regression.jl`
  (`estimator`, `weighting`, `aggregation`, `lookahead_horizon`, `tau_rel`, `tau_abs`, `cond_cap`,
  `excitation_floor`, `post_floor_significant_drop_ratio`, `post_floor_min_floor_ratio`): not added;
  these are cap-policy settings and must remain equality-checked through fingerprints/configuration,
  not treated as arm bookkeeping.

The added positive fixture constructs one capped/uncapped pair whose non-allowed condition fields
match and whose allowed arm/bookkeeping/cap fields differ (`variant_slug`, computed `condition`,
`campaign_manifest_index`, `stage_caps`, and `stage_cap_policy_active`). `build_pairs` accepts it.

## Acceptance

### Python tests

Command:

```text
python -m pytest analysis/tests/ -q
```

Output:

```text
...........................                                              [100%]
27 passed in 2.00s
```

Targeted fixture command:

```text
python -m pytest analysis/tests/test_phasec_cap_ablation.py -q
```

Output:

```text
........                                                                 [100%]
8 passed in 0.76s
```

### Phase-B byte comparison

Regeneration command:

```text
python analysis/scripts/aggregate/analyze_pretuning_contrast.py --config analysis/configs/paper1_phaseB_v1.json --output outputs/wp_n14b_phaseb_bytecheck/pretuning_contrast.json
```

Output:

```text
Pretuning contrast analysis completed
  Pairs: total=378, exact=120, surrogate=258
  Output: C:\Users\joedicke\Documents\reps\EvoODE\outputs\wp_n14b_phaseb_bytecheck\pretuning_contrast.json
  exact_support_match (exact): n=120, effect=-0.0833333, naive_p=0.0212708, cluster_p=0.217718
  r2 (surrogate): n=258, effect=-8.187340e-13, naive_p=0.00723412, cluster_p=0.0269697
  log10_loss (exact): n=120, effect=4.666489e-12, naive_p=0.294846, cluster_p=0.590064
  log10_loss (surrogate): n=258, effect=3.487521e-11, naive_p=0.00595798, cluster_p=0.0105799
```

Byte comparison:

```text
IDENTICAL bytes=4258
```

### Syntax check

Command:

```text
python -m py_compile analysis/utils/paired_stats.py analysis/scripts/aggregate/analyze_pretuning_contrast.py analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py analysis/tests/test_phasec_cap_ablation.py
```

Output: no output, exit code 0.

## Files Changed

```text
analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py
analysis/tests/test_phasec_cap_ablation.py
codex/reports/REPORT_WP_N14b.md
codex/STATUS.md
```
