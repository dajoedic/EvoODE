# WP-N33a2 Report

## Changes

- `studies/regression/export_phase_c_data_conditions.jl` now quotes CSV fields containing comma, quote, LF, or CR when writing `index.csv`.
- `analysis/scripts/aggregate/robustness_stage_report.py` now validates `--export-index` before building hash checks:
  - every data row must have exactly the header field count;
  - `time_sha256` and `state_sha256` must be 64-character hexadecimal SHA-256 values;
  - invalid input exits non-zero with one clear stderr line and no `check_observed_data_hash = not_passed` fallback.
- `analysis/tests/test_robustness_stage_report.py` now derives a fixture from the real broken `outputs/stage1/data_export/index.csv` first row and checks both failure on the unquoted row and `passed` on the correctly quoted equivalent.
- `test/test_export_phase_c_data_conditions.jl` covers `_csv_field` and `_write_index` quoting for `[512,1]`.

## Field Check

The Python fixture uses:

- real export index source: `outputs/stage1/data_export/index.csv`, header has 25 columns, first unquoted data line has 26 CSV fields because `state_shape = [512,1]`;
- real stage record source: `outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl`;
- record hash fields:
  - `observed_data_sha256.time_sha256 = ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f`;
  - `observed_data_sha256.state_sha256 = e7e535a1b26c412cd6b62aaca038e2591610e84bbe23c2213afd0b9cd8ea23d3`.

## Checks Run

```text
python -m pytest analysis/tests/test_robustness_stage_report.py --basetemp outputs/wp_n33a2_pytest_tmp
```

Result: 4 passed in 0.94 s.

```text
python -m py_compile analysis/scripts/aggregate/robustness_stage_report.py
```

Result: passed.

```text
python analysis/scripts/aggregate/robustness_stage_report.py --stage-records outputs/stage1/s0.01_r0/tasks --clean-eval outputs/stage1/s0.01_r0/clean_eval/results.jsonl --reference-c1 outputs/phase_c_campaign_221a3a7 --export-index outputs/stage1/data_export/index.csv --output-dir outputs/wp_n33a2_check
```

Result: non-zero, with stderr:

```text
Invalid export index outputs\stage1\data_export\index.csv: line 2 has 26 fields, expected 25 from the header. Regenerate the index with quoted CSV fields.
```

## Julia Check For Claude

Julia was not run in this Codex session because the protocol documents that Julia is not executable in this sandbox. Command for Claude:

```text
julia --project=. test/test_export_phase_c_data_conditions.jl
```

## Rebuild And Recompute Commands For Claude

Rebuild the Stage-1 export index with the repaired quoting:

```text
julia --project=. studies/regression/export_phase_c_data_conditions.jl --output-dir outputs/stage1/data_export --systems 1 --ic-sets 1 --sigmas 0.01,0.05 --rhos 0,0.5 --realizations 1
```

Recompute the two Stage-1 Tor reports:

```text
python analysis/scripts/aggregate/robustness_stage_report.py --stage-records outputs/stage1/s0.01_r0/tasks --clean-eval outputs/stage1/s0.01_r0/clean_eval/results.jsonl --reference-c1 outputs/phase_c_campaign_221a3a7 --export-index outputs/stage1/data_export/index.csv --output-dir outputs/stage1/s0.01_r0/robustness_stage_report
```

```text
python analysis/scripts/aggregate/robustness_stage_report.py --stage-records outputs/stage1/s0.05_r0.5/tasks --clean-eval outputs/stage1/s0.05_r0.5/clean_eval/results.jsonl --reference-c1 outputs/phase_c_campaign_221a3a7 --export-index outputs/stage1/data_export/index.csv --output-dir outputs/stage1/s0.05_r0.5/robustness_stage_report
```

Expected after export rebuild: `check_observed_data_hash = passed` for both Stage-1 conditions.
