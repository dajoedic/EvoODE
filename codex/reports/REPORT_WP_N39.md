# REPORT WP-N39 - PySR GP Baseline

## Implemented

- Added the PySR adapter path to `baselines/harness.py`, including method dispatch for `"pysr"` and package-version capture.
- Added `baselines/run_pysr_noise.py` for the noisy Phase-C exports. It reuses the WP-N34 export index/hash validator, fits on observed data, evaluates clean reconstruction/generalization on the 512-point truth grid, writes `details.csv`, `records.jsonl`, `summary.csv`, `export_checks.csv`, and a comparison join.
- Added `baselines/configs/pysr_faithful.json`, `baselines/requirements-pysr.txt`, and `baselines/Dockerfile.pysr`.
- Added fake-adapter tests for PySR structure expansion, exact-system R2=1, output files, and comparison-join behavior.
- Added frozen decisions and cost formula in `docs/WP-N39.md`.

## Local Verification

Command:

```text
python -m pytest baselines/tests/test_run_pysr_noise.py baselines/tests/test_run_odeformer_noise.py baselines/tests/test_harness.py -q
```

Result:

```text
58 passed, 5 skipped in 27.09s
```

No PySR run was started.

## Commands for Claude

### 1. Build the PySR image

Purpose: build the isolated PySR environment without modifying the existing baseline image.

Command:

```text
docker build -f baselines/Dockerfile.pysr -t evocode-pysr:wp-n39 .
```

Expected duration: image build; depends on PySR/Julia artifact download and package compilation.

Pass criterion: image builds successfully and contains the pinned packages from `baselines/requirements-pysr.txt`.

### 2. Smoke on one exported cell

Purpose: run the allowed one-cell PySR smoke on system 1, sigma 0.01, rho 0, from `outputs/stage1/data_export/index.csv`.

Command:

```text
docker run --rm -v "%cd%:/workspace/EvoODE" evocode-pysr:wp-n39 --export-index outputs/stage1/data_export/index.csv --output-dir outputs/wp_n39_pysr_smoke_system1_sigma001_rho0 --seeds 1 --limit 1
```

Expected duration: one PySR cell; this is the measurement that fills `T_cell` in `docs/WP-N39.md`.

Pass criterion: command exits 0 and writes `details.csv`, `records.jsonl`, `summary.csv`, `export_checks.csv`, and `comparison_with_external_baselines.csv`; `export_checks.csv` has `hash_verified=True`; `details.csv` contains one `method=pysr` row for system 1 with either `status=success` or a recorded error row.

### 3. Full run after smoke approval

Purpose: run the declared full PySR grid only after Claude accepts the smoke.

Command:

```text
docker run --rm -v "%cd%:/workspace/EvoODE" evocode-pysr:wp-n39 --export-index outputs/stage1/data_export/index.csv --export-index outputs/stage2/data_export/index.csv --export-index outputs/stage3/data_export/index.csv --output-dir outputs/wp_n39_noise_pysr --seeds 1,2,3
```

Expected duration: `4,536 * T_cell / parallel_cell_count` wall-clock seconds, with `4,536 * T_cell / 3,600` core-hours at one core per cell.

Pass criterion: command exits 0 and writes all five output files; `export_checks.csv` has all hashes verified; `records.jsonl` has one record per exported cell and seed.

## Notes

The smoke command uses `--limit 1`; if Claude needs to guarantee the exact condition before running, filter `outputs/stage1/data_export/index.csv` to system 1, `noise_sigma=0.01`, `subsample_rho=0`, and pass the filtered index instead.
