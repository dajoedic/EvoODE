# WP-N47 — Orion image and indexed Job for the SINDy-family baselines on the full C-6 export (DOP853)
**Language: Python** (plus Dockerfile, CI, k8s YAML)

## Why

WP-N46 (`da83040`) made DOP853 the default and Claude re-ran the clean 378 cells locally
(`outputs/c6_n46_clean_dop853/`, `hierarchy_n46`). The full noisy grid (4,536 cells × 10 configurations × SINDy,
Weak-SINDy, E-SINDy = 136,080 model rows; ~23 h at 10 local processes) must run on Orion: the laptop is needed for
other work. Orion has no Python/pysindy image yet. **Time matters: the user wants to push tonight.** Keep it minimal.

## Deliverables

1. **`baselines/Dockerfile.sindy-baselines`** + `.dockerignore` (allowlist style like `baselines/Dockerfile.dockerignore`).
   Base `python:3.12-slim`. Pin exactly the versions of Claude's laptop, which produced the clean reference:
   Python 3.12, pysindy 2.1.0, scipy 1.13.1, numpy 2.2.6, pandas 2.2.2, scikit-learn 1.5.1, sympy 1.13.1 — plus
   whatever else `run_phasec_noise_sindy_baselines.py` imports, pinned to the laptop's installed versions
   (`pip show` / `importlib.metadata`; list them in the report). Copy only what the runner needs (`analysis/`,
   `benchmarks/data/strogatz_extended.json`, the config). No build-essential unless a wheel is missing.
2. **CI job** `build_sindy_baselines_image` in `.gitlab-ci.yml`, same pattern as `build_odeformer_reference_image`
   (tag `$CI_REGISTRY_IMAGE/sindy-baselines:$CI_COMMIT_SHA`). It must build on the next push (rules: changes on its
   Dockerfile/dockerignore/requirements and on the three runner scripts). Add the matching trivy job like the others.
   Do not change the existing build jobs.
3. **Entry script** (e.g. `analysis/scripts/aggregate/run_k8s_sindy_shard.py`): reads `JOB_COMPLETION_INDEX` and
   env `EVO_SINDY_EXPORT_DIR`, `EVO_SINDY_OUTPUT_DIR`, `EVO_SINDY_N_SHARDS`; builds shard `i` as
   `index.csv.iloc[i::N]` with `cell_dir` resolved absolutely against the export dir (the same split rule as
   `SCRIPTS.md`); calls the noise runner with `--methods sindy,weak_sindy,e_sindy --integrator dop853`, output
   `<OUTPUT>/shard_<i>`. Resume (WP-N46 D) must work so a restarted pod continues.
4. **`k8s/phase_c_c6_sindy_baselines_job.yaml`**: indexed Job, `completions: 80` (80 shards for load balancing),
   **`parallelism: 8`**, 1 CPU / 2Gi request = limit, `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` = 1,
   **no `activeDeadlineSeconds`**, `backoffLimit` like the others, `imagePullSecrets` and NFS volume exactly as
   `k8s/paper2_t2a_s1_job.yaml`. Export: `/outputs/phase_c_c6_data_conditions_5dd1df839f8ece98f2bb3bbff78d15d8c433d9d3`;
   output `/outputs/c6_sindy_baselines_dop853_<COMMIT_SHA>`. Image placeholder `<COMMIT_SHA>` as in the other manifests.
   Header comment: purpose, expected cost (~200–250 core-h, capacity planning only).
5. **Smoke (allowed):** run the entry script locally with `JOB_COMPLETION_INDEX=0`, `EVO_SINDY_N_SHARDS=4536` (one
   cell), against the local export `outputs/phase_c_c6_data_conditions_5dd1df8` — pick N so shard 0 is a clean cell, or
   add an optional filter env for the smoke only; the 30 rows must equal the matching rows of
   `outputs/c6_n46_clean_dop853` (R² columns, statuses, active terms, full coefficients). Do not run docker.
6. `SCRIPTS.md`: the `oc apply` substitution command, the collect/merge command afterwards, and the acceptance
   control: the clean rows from Orion must be identical to `outputs/c6_n46_clean_dop853` (cross-machine; report
   numeric tolerance if not bit-identical).

## Verboten

- Running anything beyond the smoke. Docker builds. Pushing. Committing. Editing this file.
- Changing the runner's science (methods, thresholds, seeds, integrator settings).

## Abnahme

- Report `codex/reports/REPORT_WP_N47.md` (pinned versions, smoke comparison, files). `STATUS.md` `done` / `blocked`.
