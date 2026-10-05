# REPORT WP-DIAG-AMB-a

## Status

Blocked. The diagnostic script and focused tests were implemented, but the required single real fixture run
`F2/wide/eta=0.01/seed=50000` with bootstrap did not finish before the protocol limit. I aborted it after more than
13 minutes to stay below the 15 minute hard cap. No `records.jsonl` record was written.

## Files

- Added `experiments/annihilator_gate2a_v3/diagnostics/__init__.py`.
- Added `experiments/annihilator_gate2a_v3/diagnostics/ambiguity_diagnostic.py`.
- Added `experiments/annihilator_gate2a_v3/tests/test_ambiguity_diagnostic.py`.
- Added diagnostic result files under `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/`:
  `reference_check.json`, `nullspace_cache.json`, `summary.json`, `summary.md`.

No existing file under `experiments/` was modified.

## Implemented behavior

- Fixed cells in code: F1, F2, F4, F5, F6, F8; domain `wide`; eta `0.01`; groups N1 = F4/F5/F8 and I = F1/F2/F6.
- Settings are loaded via `settings_for_variant("standard", require_appendix=True)` and checked against
  `results/calibration/appendix_A.json`.
- `ell_max` check: expected 4, loaded 4.
- `tau` check: loaded from Appendix A as `3.386508022297224e-07`.
- Per-record state and ambiguity sources use `_state_for_clean` from `acceptance/stage_k_calibration.py`.
- Reference classes and `n_exact` are read from `results/oracle_reference_v3.json`.
- Angle computation uses mpmath SVD over the same collocation matrix path as `oracle._nullspace`, retaining all exact
  nullspace basis vectors.
- `--reps`, `--pilot`, `--workers`, resume from `records.jsonl`, `run.log`, `DONE`, and `--summarize` are implemented.

## Coefficient order and scale check

Command:

```text
python -c "import json; from experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic import OUTDIR, load_oracle_cache, validate_references; OUTDIR.mkdir(parents=True, exist_ok=True); check=validate_references(load_oracle_cache()); (OUTDIR/'reference_check.json').write_text(json.dumps(check, indent=2, sort_keys=True)); print(json.dumps(check, sort_keys=True))"
```

Results:

| Function | Reference class | Nullspace dimension | Dot | Max abs diff |
|---|---:|---:|---:|---:|
| F1 | [1, 1] | 1 | 1.0000000000000002 | 0.0 |
| F2 | [1, 0] | 1 | 1.0000000000000002 | 0.0 |
| F4 | [2, 1] | 1 | 0.9999999999999999 | 0.0 |
| F5 | [3, 1] | 1 | 0.9999999999999999 | 0.0 |
| F6 | [1, 1] | 1 | 1.0 | 0.0 |
| F8 | [1, 2] | 1 | 1.0 | 0.0 |

Appendix B reference classes checked: F4 = [2, 1], F5 = [3, 1], F8 = [1, 2].

## Field provenance

| Output field | Origin |
|---|---|
| function, group, domain, eta, seed | Diagnostic cell definition |
| selected_class | `Selection.selected_class` |
| state, ambiguity_sources | `_state_for_clean(...)` |
| bootstrap_share | `Selection.bootstrap_share` |
| selected_is_reference, reference_class | Oracle reference |
| n_exact | Oracle class table |
| T | `Selection.statistic` |
| dof | `Selection.dof` |
| critical | `Selection.critical` |
| tested_classes | `Selection.tested_classes` |
| aml_iterations | `Selection.aml_iterations` |
| aml_converged | `Selection.aml_converged` |
| aml_message | `Selection.aml_message` |
| boot_reps | `Settings.boot_reps` |
| angle_degrees | Newly computed diagnostic angle |
| wall_clock_seconds | Newly computed logistics timing |
| settings | `Settings` dataclass fields used for the run |

## Real fixture attempt

Attempted command:

```text
python -c "import json; from experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic import OUTDIR, diagnostic_settings, load_oracle_cache, validate_references, run_one, load_nullspace_cache; OUTDIR.mkdir(parents=True, exist_ok=True); settings=diagnostic_settings(); cache=load_oracle_cache(); check=validate_references(cache); null_cache=load_nullspace_cache(); rec=run_one('F2', 50000, settings=settings, cache=cache, null_cache=null_cache); (OUTDIR/'fixture_f2_seed50000.json').write_text(json.dumps(rec, indent=2, sort_keys=True)); (OUTDIR/'reference_check.json').write_text(json.dumps(check, indent=2, sort_keys=True)); print(json.dumps({'state': rec['state'], 'tested_classes': rec['tested_classes'], 'aml_iterations': rec['aml_iterations'], 'wall_clock_seconds': rec['wall_clock_seconds'], 'angle_degrees': rec['angle_degrees']}))"
```

Result: aborted after more than 13 minutes. No state, count fields, duration, or fixture record are available from a
completed run.

## Tests and checks

- Syntax check:
  `python -m py_compile experiments/annihilator_gate2a_v3/diagnostics/ambiguity_diagnostic.py experiments/annihilator_gate2a_v3/tests/test_ambiguity_diagnostic.py`
  passed.
- Focused pytest:
  `python -m pytest experiments/annihilator_gate2a_v3/tests/test_ambiguity_diagnostic.py -q --basetemp experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/pytest_tmp`
  returned `2 passed, 4 skipped in 2.14s`.
- Skipped tests are the tests that require the real F2/50000 fixture; they skip rather than invent fixture records.
- `--summarize` on empty records completed and wrote `summary.json`/`summary.md` with `records = 0` and
  `verdict = incomplete`.

## Required commands

Pilot:

```text
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --pilot --workers 1
```

Main run, example for N = 100:

```text
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --reps 100 --workers 6
```

Summarize:

```text
python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --summarize
```
