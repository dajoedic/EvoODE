# WP-N47 Report

## Files

- `baselines/Dockerfile.sindy-baselines`
- `baselines/Dockerfile.sindy-baselines.dockerignore`
- `baselines/requirements-sindy-baselines.txt`
- `analysis/scripts/aggregate/run_k8s_sindy_shard.py`
- `k8s/phase_c_c6_sindy_baselines_job.yaml`
- `.gitlab-ci.yml`
- `SCRIPTS.md`

## Pinned Python Packages

Versions were read from the local Python 3.12 environment with `importlib.metadata`.

| Package | Version |
|---|---:|
| pysindy | 2.1.0 |
| scipy | 1.13.1 |
| numpy | 2.2.6 |
| pandas | 2.2.2 |
| scikit-learn | 1.5.1 |
| sympy | 1.13.1 |
| derivative | 0.6.3 |
| joblib | 1.4.2 |
| threadpoolctl | 3.5.0 |
| typing_extensions | 4.12.2 |

The runner imports only stdlib modules plus `numpy`, `pandas`, `sympy`, `scipy`, `pysindy`, and
scikit-learn through PySINDy. The extra non-stdlib pins are PySINDy runtime dependencies present on
the laptop.

## Smoke

Command shape:

```powershell
$env:PYTHONPATH='analysis'
$env:JOB_COMPLETION_INDEX='0'
$env:EVO_SINDY_EXPORT_DIR='outputs/phase_c_c6_data_conditions_5dd1df8'
$env:EVO_SINDY_OUTPUT_DIR='outputs/c6_n47_smoke'
$env:EVO_SINDY_N_SHARDS='4536'
$env:EVO_SINDY_CONFIG='analysis/configs/paper1_phaseC_sindy_baseline.json'
python -m scripts.aggregate.run_k8s_sindy_shard
```

Results:

| Measure | Value |
|---|---:|
| `details.csv` rows | 30 |
| `export_checks.csv` rows | 1 |
| resume rerun exit code | 0 |
| rows after resume rerun | 30 |

The first local invocation without `PYTHONPATH=analysis` failed before running the smoke because the
local shell did not mirror the container `PYTHONPATH`; the image sets it in the Dockerfile.

## N46 Clean Comparison

Candidate: `outputs/c6_n47_smoke/shard_0/details.csv`

Reference: `outputs/c6_n46_clean_dop853/merged/details.csv`

Join keys:
`method`, `library_id`, `system_id`, `source_initial_condition_set`, `noise_sigma`, `subsample_rho`,
`noise_realization`.

| Check | Result |
|---|---:|
| candidate rows | 30 |
| paired rows | 30 |
| candidate-only rows | 0 |
| status mismatches | 0 |
| active term mismatches | 0 |
| full coefficient mismatches | 0 |
| reconstruction R2 arithmetic max abs delta | 0.0 |
| reconstruction R2 variance-weighted max abs delta | 0.0 |
| generalization R2 arithmetic max abs delta | 0.0 |
| generalization R2 variance-weighted max abs delta | 0.0 |

## Checks

- `python -m py_compile analysis/scripts/aggregate/run_k8s_sindy_shard.py` passed.
- `.gitlab-ci.yml` parsed with PyYAML and contains `build_sindy_baselines_image` plus
  `trivy-sindy-baselines-image`.
- Docker build was not run, per Verboten.
- No cluster job, campaign, or full run was started.
