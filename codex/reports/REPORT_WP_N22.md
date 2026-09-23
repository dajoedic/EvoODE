# REPORT WP-N22

Status: blocked, environment not subject. The Python code, four configs, runner, summary script, and local tests are in place. The remaining acceptance requires building and running the ODEFormer Docker images; WP-N22 assigns that execution to Claude.

## Changed files

- `baselines/harness.py`: added a reusable `ODEFormerAdapter`, optional constant optimization through ODEFormer's unchanged `ConstantOptimizer`, before/after record fields, optimizer diagnostics, config/environment IDs, and explicit non-silent optimization failure status.
- `baselines/configs/odeformer_beam10_noopt.json`
- `baselines/configs/odeformer_beam10_opt.json`
- `baselines/configs/odeformer_beam50_noopt.json`
- `baselines/configs/odeformer_beam50_opt.json`
- `baselines/configs/odeformer_grid.json`
- `baselines/run_odeformer_grid.py`: four-configuration runner with atomic per-cell JSON writes, resumability, subset filters, per-cell time budget marking, one model adapter per config per process, and index sharding.
- `baselines/summarize_odeformer_grid.py`: summary tables under `analysis/data/paper1_phaseC_v1/odeformer_baseline/`.
- `baselines/tests/test_harness.py`: added local tests for resumability, atomic write behavior, timeout marking, and summary counts/expression identity using real trajectory export inputs.

## ODEFormer source evidence

- `ConstantOptimizer` is ODEFormer's own class: `outputs/third_party/odeformer/param_optimizer.py:21`.
- Constructor settings used by the adapter:
  - `init_random`: `outputs/third_party/odeformer/param_optimizer.py:29`, documented at `outputs/third_party/odeformer/param_optimizer.py:45-46`.
  - `optimization_objective="r2"` default: `outputs/third_party/odeformer/param_optimizer.py:30`.
  - `eval_objective="r2"` default: `outputs/third_party/odeformer/param_optimizer.py:31`.
  - `track_eval_history=True` default: `outputs/third_party/odeformer/param_optimizer.py:32`, behavior at `outputs/third_party/odeformer/param_optimizer.py:130-135`.
  - constants are read from the expression by `get_params`: `outputs/third_party/odeformer/param_optimizer.py:69-82`.
  - `init_random=False` starts from expression constants; random start uses `np.random.randn`: `outputs/third_party/odeformer/param_optimizer.py:124-129`.
  - objective uses variance-weighted R2 for `"r2"`: `outputs/third_party/odeformer/param_optimizer.py:111-117`.
  - SciPy `minimize` is called without custom method/options/tolerances, so SciPy defaults apply: `outputs/third_party/odeformer/param_optimizer.py:124-129`.
- Conscious adapter choice: optimized configs set `init_random=false` so optimization starts from ODEFormer's own fitted constants rather than random values. This is the non-structure-changing choice requested by WP-N22.
- Optimizer data separation: the adapter passes only the fit trajectory as `observed_trajectory` in `baselines/harness.py:425-433`; the generalization trajectory is integrated only after fitting in `baselines/harness.py:491-494`.
- ODEFormer is loaded once per config adapter in `baselines/harness.py:360-385`; the grid runner caches adapters in `baselines/run_odeformer_grid.py:160-172`.

## Record fields

The ODEFormer records now include:

- stable grid identity: `odeformer_config_id`, `odeformer_environment_id`
- before/after expressions: `odeformer_expression_before_optimization`, `odeformer_expression_after_optimization`
- before/after constants: `odeformer_constants_before_optimization`, `odeformer_constants_after_optimization`
- before/after R2 aggregations for reconstruction and generalization:
  - `reconstruction_before_optimization_r2_arithmetic_mean`
  - `reconstruction_before_optimization_r2_variance_weighted`
  - `generalization_before_optimization_r2_arithmetic_mean`
  - `generalization_before_optimization_r2_variance_weighted`
  - `reconstruction_after_optimization_r2_arithmetic_mean`
  - `reconstruction_after_optimization_r2_variance_weighted`
  - `generalization_after_optimization_r2_arithmetic_mean`
  - `generalization_after_optimization_r2_variance_weighted`
- optimizer diagnostics: `odeformer_optimization_status`, `odeformer_optimization_nit`, `odeformer_optimization_nfev`, `odeformer_optimization_stop_reason`, `odeformer_optimization_error_type`, `odeformer_optimization_error_message`

If optimization fails, the record keeps the unoptimized expression and sets `odeformer_optimization_status="error_unoptimized_expression_retained"`.

## Local verification

Commands run locally:

```text
python -m compileall -q baselines
python -m pytest baselines/tests -q
```

Observed result:

```text
12 passed in 10.26s
```

## Commands for Claude

All run commands use `--entrypoint python` and mount `baselines/`.

### A. Build images

```text
docker build -f baselines/Dockerfile.odeformer-reference -t evocode/odeformer-reference:wp-n22 .
docker build -f baselines/Dockerfile.odeformer-candidate -t evocode/odeformer-candidate:wp-n22 .
```

Expected output: both builds finish successfully and include the same ODEFormer weights hash `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`.

Pass criterion: both images build without hash mismatch.

### B. Timing run on systems 1, 2, 24, and one dim-3 system

Use system 52 as the dim-3 timing representative.

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_grid --config baselines/configs/odeformer_grid.json --environment-id reference --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_timing --system-ids 1,2,24,52
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_grid --config baselines/configs/odeformer_grid.json --environment-id candidate --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_timing --system-ids 1,2,24,52
```

Expected output: each command prints its `records.jsonl` path.

Pass criterion: each JSONL has 32 records: 4 systems x 2 fit/generalization directions x 4 configs, with no partial files in `records/`.

Suggested timeout: keep `timeout_seconds_per_cell=900` for the full run until the timing records show a smaller safe cap. This keeps each ODEFormer cell below the protocol's 15-minute ceiling while still allowing beam 50 plus constant optimization.

### C. Full run per environment

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_grid --config baselines/configs/odeformer_grid.json --environment-id reference --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/reference
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_grid --config baselines/configs/odeformer_grid.json --environment-id candidate --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate
```

Expected output: each command prints its `records.jsonl` path.

Pass criterion: each JSONL has 504 records: 63 systems x 2 fit/generalization directions x 4 configs. Records with completed status are skipped on rerun; timeout cells are marked `status=timeout` and the run continues.

Optional shard example, no manifest creation:

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_grid --config baselines/configs/odeformer_grid.json --environment-id candidate --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate --shard-index 0 --shard-count 8
```

Expected output: the shard prints the shared `records.jsonl` path after writing its subset.

Pass criterion: shard arguments partition by cell index; rerunning all shards leaves complete records in place and only fills missing records.

### D. Summary

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.summarize_odeformer_grid --reference-records analysis/data/paper1_phaseC_v1/odeformer_baseline/reference/records.jsonl --candidate-records analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate/records.jsonl --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline
```

Expected output:

```text
analysis/data/paper1_phaseC_v1/odeformer_baseline/summary.csv
analysis/data/paper1_phaseC_v1/odeformer_baseline/expression_identity.csv
```

Pass criterion: `summary.csv` has environment x config x dimension rows with counts and shares for reconstruction/generalization and arithmetic/variance-weighted R2 > 0.9, plus error/timeout counts. `expression_identity.csv` has identical-expression counts between reference and candidate by config and dimension.

## Blocked items

Codex did not build or run Docker images in this session. The remaining ODEFormer execution acceptance is blocked by environment, not subject.
