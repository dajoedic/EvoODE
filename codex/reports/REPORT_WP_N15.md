# WP-N15 Report

## Built

- Added `analysis/scripts/aggregate/aggregate_wp_n1_dim2_probe.py`.
- Added shared `equationwise_support_match()` to `analysis/utils/metrics.py`.
- Added `analysis/tests/test_wp_n1_dim2_probe_aggregation.py`.
- Added the `.gitignore` exception for `analysis/data/wp_n1_dim2_probe/`.

## Outputs Produced By The Script

Default output directory:

```text
analysis/data/wp_n1_dim2_probe/
```

Files:

```text
wp_n1_dim2_probe_cells.csv
wp_n1_dim2_probe_decision_table.csv
```

The cell table contains separate `raw_support_match` and `pruned_support_match` columns, the
`support_equality_definition` field, manifest completeness fields, the decision layer, effort
counts, and `elapsed_s_evidence_role = non_evidence`.

The decision table keeps row types separate:

```text
layer_summary
literature_r2_summary
layer_a_raw_contingency
layer_a_by_system
```

It includes denominators, missing-manifest fields, raw/pruned rates, `r2 > 0.9` rates, Layer A
effective sample size by systems, effort quantiles for `total_parameter_fits` and
`total_loss_evals`, and `elapsed_s` quantiles marked as non-evidence.

## Checks Implemented

- Single `git_hash`, `config_fingerprint`, and `stage_cap_behavior_fingerprint`.
- Reject `git_hash = not_collected`.
- Reject non-empty `error`.
- Reject duplicate cells by `(system_id, seed, initial_condition_set, variant)`.
- Reject missing records unless `--allow-incomplete` is passed.
- Report missing manifest indices in every output when incomplete runs are allowed.
- Exclude `*.heartbeat.jsonl` from directory input.
- Verify derived exact-system sets against the WP-N15 check values:
  - both bases exact: `24,25,26,27,28,29,31,32,38`
  - constant-only exact: `43`
  - old-only exact: none
- Count raw-implies-pruned violations without changing either value.

## Test Results

Command:

```powershell
$env:TMP = (Resolve-Path .).Path + '\.pytest_tmp'; $env:TEMP = $env:TMP; New-Item -ItemType Directory -Force $env:TMP | Out-Null; python -m pytest analysis/tests/test_wp_n1_dim2_probe_aggregation.py
```

Result:

```text
6 passed in 7.00s
```

Command:

```powershell
$env:TMP = (Resolve-Path .).Path + '\.pytest_tmp'; $env:TEMP = $env:TMP; New-Item -ItemType Directory -Force $env:TMP | Out-Null; python -m pytest analysis/tests
```

Result:

```text
33 passed in 6.15s
```

The first pytest attempt without setting `TMP`/`TEMP` failed before tests ran because pytest could
not scan `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke`.

## Real Data Run

Share visibility check:

```powershell
Test-Path "S:\BigDataOrion\data-science\joedicke\wp_n1_dim2_probe_ec3b6bd5b43f06539d38b633257ca51115bfa47f\tasks"
```

Result:

```text
False
```

The real 335-record run could not be executed in this Codex session because the `S:\` share is not
visible. The command for Claude to run is:

```powershell
python analysis/scripts/aggregate/aggregate_wp_n1_dim2_probe.py --allow-incomplete
```

Expected acceptance checks from that run:

```text
Missing manifest indices: [293]
Layer A systems: [24, 25, 26, 27, 28, 29, 31, 32, 38]
Layer A counts by variant: {'wp_n1_constant_basis': 54, 'wp_n1_old_basis': 54}
```

No recommendation or basis decision is made by the script or this report.
