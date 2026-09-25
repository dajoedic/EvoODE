# REPORT WP-N27

## Changed files

- `.gitlab-ci.yml`
  - Added `build_odeformer_reference_image` for
    `$CI_REGISTRY_IMAGE/odeformer-reference:$CI_COMMIT_SHA` and
    `$CI_REGISTRY_IMAGE/odeformer-reference:$CI_COMMIT_REF_SLUG`.
  - Added `trivy-odeformer-reference-image` with `allow-failure: true`.
- `CHANGELOG.md`
  - Added the 2026-09-25 CI note for the ODEFormer reference image, Claim D on Orion, E7 scan
    risk, and the Google Drive `gdown` build-time dependency.
- `baselines/run_odeformer_grid.py`
  - Added `--repetition`, `--trajectory-export-dir`, and `--collect`.
  - Repetition output roots are `rep_{N:03d}/`.
  - The runner rejects non-faithful configurations where `timeout_seconds_per_cell` or an
    ODEFormer config `integration_timeout_seconds` is non-null.
  - Records written by the updated path include the resolved trajectory export path, faithful-mode
    marker, repetition marker, and observed/requested Torch thread information.
  - Collection now merges `rep_*/records`, requires every repetition to have the expected record
    count, and writes `records.jsonl`, `records.csv`, `repetition_counts.csv`, and
    `cell_repetition_summary.csv`.
- `baselines/run_odeformer_grid_k8s.py`
  - Added the Kubernetes indexed-Job entry point. `JOB_COMPLETION_INDEX=i` maps to
    `repetition = i // 42 + 1` and `shard_index = i % 42`.
- `baselines/run_odeformer_repeatability.py`
  - Reuses the grid repetition-summary helper for bitwise identity, handler timeout min/max, and
    R2-threshold flips.
- `baselines/tests/test_harness.py`
  - Added/updated tests for repetition output, non-faithful abort, completion-index mapping,
    shard coverage, and incomplete repetition collection.
- `k8s/odeformer_reference_grid_job.yaml`
  - Added the 126-completion indexed Orion Job.
- `k8s/odeformer_reference_grid_smoke_job.yaml`
  - Added the one-pod, `--limit 2` smoke Job.
- `SCRIPTS.md`
  - Added the "ODEFormer-Referenzraster auf Orion" runbook.

`baselines/Dockerfile.odeformer-reference` was not changed.

## Deadline derivation

- Work: `63 systems * 2 directions * 4 configs * 3 repetitions = 1,512 cell-repetitions`.
- WP-N23 maximum per cell: `940 s`.
- Orion parallelism: `16`.
- Safety factor: `2`.
- Formula: `1,512 * 940 / 16 * 2 = 177,660 s`.
- Manifest value: `activeDeadlineSeconds: 180000`.

This is an upper bound, not a point estimate.

## Commands run

```bash
python -m pytest baselines/tests/test_harness.py -q
```

Result: `29 passed, 2 skipped in 34.04s`.

```bash
python -m pytest baselines/tests -q
```

Result: `29 passed, 2 skipped in 14.61s`.

```bash
python -m py_compile baselines/run_odeformer_grid.py baselines/run_odeformer_grid_k8s.py baselines/run_odeformer_repeatability.py
```

Result: success.

```bash
python -c "import yaml; from pathlib import Path; paths=[Path('.gitlab-ci.yml'),Path('k8s/odeformer_reference_grid_job.yaml'),Path('k8s/odeformer_reference_grid_smoke_job.yaml')]; [yaml.safe_load(p.read_text(encoding='utf-8')) for p in paths]; print('\n'.join(str(p) for p in paths))"
```

Result: parsed `.gitlab-ci.yml`, `k8s/odeformer_reference_grid_job.yaml`, and
`k8s/odeformer_reference_grid_smoke_job.yaml`.

## Commands for Claude

Local Docker smoke of the Kubernetes entry point with the existing image:

```bash
docker run --rm \
  -e JOB_COMPLETION_INDEX=0 \
  -e OMP_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -e ODEFORMER_TORCH_THREADS=1 \
  -v /path/to/trajectory_export:/trajectory_export:ro \
  -v /path/to/output:/outputs \
  evoode/odeformer-reference:wp-n21 \
  python -m baselines.run_odeformer_grid_k8s \
    --trajectory-export-dir /trajectory_export \
    --output-dir /outputs/reference \
    --limit 2
```

Final collection after the Orion Job:

```bash
python -m baselines.run_odeformer_grid \
  --config baselines/configs/odeformer_grid.json \
  --output-dir /outputs/odeformer_grid_<COMMIT_SHA>/reference \
  --collect --repetitions 3
```

## Not verified locally

- Docker build and push of `baselines/Dockerfile.odeformer-reference`.
- Google Drive reachability from the GitLab runner during `gdown`.
- Trivy registry scan execution for the new image.
- Kubernetes image pull, NFS mount, ODEFormer weight load, and full 126-completion Orion run.
