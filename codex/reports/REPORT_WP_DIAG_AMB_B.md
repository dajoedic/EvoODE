# WP-DIAG-AMB-b Report

## Changes

- Added `--part i/k`, `--outdir`, `--merge`, and `--records` to `experiments/annihilator_gate2a_v3/diagnostics/ambiguity_diagnostic.py`.
- Partitioning removes completed pilot tasks from the main `records.jsonl` before applying `j % k == i`.
- Part runs write to `parts/part_<i>_of_<k>/` with local `records.jsonl`, `run.log`, `nullspace_cache.json`, and `DONE`.
- Merge reads the main records and all part records, rejects duplicate `(function, seed)`, rejects seeds outside `50000..50000+N-1` when `--reps N` is provided, and writes `records_merged.jsonl`.
- Nullspace cache writes now use a same-directory temporary file plus `os.replace`; unreadable cache input is treated as empty and logged as a warning.
- Progress log lines now include function, seed, tested classes, AML iterations, and seconds only.
- Copied the real F2 seed 50000 pilot record to `experiments/annihilator_gate2a_v3/tests/fixtures/record_f2_seed50000.json`.

## Tests

Command:

```powershell
New-Item -ItemType Directory -Force -Path .codex_tmp | Out-Null
$env:TMP = (Resolve-Path .codex_tmp).Path
$env:TEMP = (Resolve-Path .codex_tmp).Path
python -m pytest experiments/annihilator_gate2a_v3/tests/test_ambiguity_diagnostic.py -q
```

Result:

```text
10 passed in 1.67s
```

The explicit `TMP`/`TEMP` override was needed because the default user temp directory was not readable in this sandbox.

## Pilot Merge And Summary Check

Commands:

```powershell
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --merge --reps 2
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --summarize --records experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/records_merged.jsonl
```

Result:

- records: 12
- verdict: negative
- N1 states: NONE 0, AMBIGUOUS 5, CORRECT 0, TRUE_NOT_REF 0, WRONG 1
- I states: NONE 0, AMBIGUOUS 3, CORRECT 3, TRUE_NOT_REF 0, WRONG 0
- F1 states: NONE 0, AMBIGUOUS 1, CORRECT 1, TRUE_NOT_REF 0, WRONG 0
- F2 states: NONE 0, AMBIGUOUS 1, CORRECT 1, TRUE_NOT_REF 0, WRONG 0
- F4 states: NONE 0, AMBIGUOUS 1, CORRECT 0, TRUE_NOT_REF 0, WRONG 1
- F5 states: NONE 0, AMBIGUOUS 2, CORRECT 0, TRUE_NOT_REF 0, WRONG 0
- F6 states: NONE 0, AMBIGUOUS 1, CORRECT 1, TRUE_NOT_REF 0, WRONG 0
- F8 states: NONE 0, AMBIGUOUS 2, CORRECT 0, TRUE_NOT_REF 0, WRONG 0

## Main-Run Commands

One part on a pod:

```powershell
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --reps 100 --part i/11 --outdir <Pfad> --workers 1
```

Merge after all parts:

```powershell
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --merge --reps 100 --outdir <Pfad>
```

Summarize merged records:

```powershell
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --summarize --records <Pfad>/records_merged.jsonl --outdir <Pfad>
```
