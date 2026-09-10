# REPORT WP-N14

## Result

Implemented `analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py` for the paired Phase-C
cap ablation and moved the reusable paired-statistics helpers to `analysis/utils/paired_stats.py`.
`analysis/scripts/aggregate/analyze_pretuning_contrast.py` now imports those helpers instead of
carrying its own copies.

The new cap-ablation script:

- accepts only `evogrow_v2_2_stage_capped` and `evogrow_v2_2_stage_local`;
- requires `--expected-total-pairs`;
- pairs by `system_id`, `seed`, and `initial_condition_set`;
- checks pair condition equality by allowlist: unknown columns must match;
- requires `executed_levels` and refuses to substitute `n_levels`;
- writes `analysis/data/<campaign>/phasec_cap_ablation_paired.csv`;
- writes `analysis/data/<campaign>/phasec_cap_ablation_summary.json`.

## Required Phase-C Record Columns

The script requires these registry columns:

```text
experiment_id
variant_slug
system_id
system_name
system_dim
system_representability
system_expected_stage
seed
initial_condition_set
loss
r2
exact_support_match_raw
exact_support_match_pruned
structural_f1
term_precision
term_recall
coefficient_relative_error_mean
total_parameter_fits
total_parameter_fit_attempts
total_loss_evals
total_ode_solves
final_stage
executed_levels
```

Optional generalization columns are included when present:

```text
generalization_r2
generalization_loss
generalization_mse
test_r2
test_loss
test_mse
```

`executed_levels` is the expected executed-level count column. `n_levels` is not accepted as a
replacement because it is the configured level budget.

## Acceptance

### 1. Python tests

Command:

```text
python -m pytest analysis/tests/ -q
```

Output:

```text
..........................                                               [100%]
26 passed in 2.52s
```

New fixture tests cover:

- complete pairing over all fixture cells -> success;
- missing countercell -> abort;
- unexpected mismatching allowlist-excluded column -> abort, message includes column and both values;
- newly added unknown mismatching column -> abort;
- wrong arm label -> abort;
- missing `executed_levels` -> abort with explicit no-`n_levels` substitution message;
- CLI output of paired CSV and summary JSON.

### 2. Phase-B byte comparison after statistics extraction

Regeneration command:

```text
python analysis/scripts/aggregate/analyze_pretuning_contrast.py --config analysis/configs/paper1_phaseB_v1.json --output outputs/wp_n14_phaseb_bytecheck/pretuning_contrast.json
```

Output:

```text
Pretuning contrast analysis completed
  Pairs: total=378, exact=120, surrogate=258
  Output: C:\Users\joedicke\Documents\reps\EvoODE\outputs\wp_n14_phaseb_bytecheck\pretuning_contrast.json
  exact_support_match (exact): n=120, effect=-0.0833333, naive_p=0.0212708, cluster_p=0.217718
  r2 (surrogate): n=258, effect=-8.187340e-13, naive_p=0.00723412, cluster_p=0.0269697
  log10_loss (exact): n=120, effect=4.666489e-12, naive_p=0.294846, cluster_p=0.590064
  log10_loss (surrogate): n=258, effect=3.487521e-11, naive_p=0.00595798, cluster_p=0.0105799
```

Byte comparison output:

```text
IDENTICAL bytes=4258
```

### 3. Syntax check

Command:

```text
python -m py_compile analysis/utils/paired_stats.py analysis/scripts/aggregate/analyze_pretuning_contrast.py analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py analysis/tests/test_phasec_cap_ablation.py
```

Output: no output, exit code 0.

## Files Changed

```text
analysis/utils/paired_stats.py
analysis/scripts/aggregate/analyze_pretuning_contrast.py
analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py
analysis/tests/test_phasec_cap_ablation.py
codex/reports/REPORT_WP_N14.md
```
