# WP-FA5 — Side project Q5: the Q4 pipeline on the C-6 noise export (build, probe, Orion grid)
**Language: Julia** (plus Python and k8s YAML)

Stand 2026-10-27. Authority: the frozen protocol `docs/sideproject_residual_growth_protocol_q5.md` (`f737939`). Read it
first, then the Q4 protocol `_q4.md` and `codex/reports/REPORT_WP_FA4.md` (how Q4 was built and run: path builder,
Julia runner, Orion job, aggregation). Q5 = the Q4 pipeline **unchanged**, applied to the C-6 export instead of the clean
WP-C4c trajectories.

## Resumed 2026-10-27 after the scope-1 stop — the binding is decided

Read the amendment at the top of the protocol. Scope 1 is done (`codex/reports/REPORT_WP_FA5.md`); do not repeat it.
- **Fit and selection use the Q4 machinery unchanged**: the observed trajectory is passed as is, so the simulation
  starts from the first observed sample at the first observed time. Do not overwrite or prepend any state.
- **Reconstruction and generalization** are evaluated from the clean IC on the clean grid, as the baselines
  (`run_phasec_noise_sindy_baselines.py:373–379`); the clean trajectories come from the export's (0, 0) cells or the
  same integration the baselines use — state which, and check they agree.
- **D5**: per chosen (c) model also the training-data MSE simulated from the clean training IC with the same
  coefficients (evaluation only).
- **Julia export reader**: there is none (report binding 3); write one for the runner that reads `index.csv` and the
  binaries and verifies the per-cell hashes exactly as `read_index_cell` does, and records `observed_data_sha256` in the
  Python representation (`data_sha`) so the aggregation can join on it.
- The shell helper failed in your last session: if it fails again, report `blocked` with the error instead of working
  around it — tests must actually run.

Continue with scopes 2–7.

## Why

Q4 (clean data) put the pipeline on par with / ahead of Weak-SINDy. Q5 measures it on the same noisy and subsampled
data the C-6 baselines consumed. It reports; there are no pass/fail rules (protocol §6). The full grid runs on Orion on
8 pods; a probe Job runs first and the user decides the grid after it.

## Scope

1. **Bindings from existing code, not new choices (protocol §3).** Before changing anything, find out and state in the
   report, with file and line:
   - whether the Q4 weak quadrature (`build_sideproject_q4_paths.py` and what it reuses) assumes a uniform time grid;
     if so, make it evaluate on the actual observation times for ρ = 0.5 with the same test functions. At ρ = 0 the
     result must stay bit-identical to Q4.
   - the initial-state convention of the C-6 baseline harness (WP-N34/N47: from which state are fitted models
     simulated on the training side?) and the convention of the Q4 Julia runner; Q5 uses the baseline convention for
     fit, selection and reconstruction. Generalization starts from the clean test IC. If the two conventions differ,
     report it and stop (`blocked`) before writing the runner — the user decides.
   - how the C-6 export (`outputs/phase_c_c6_data_conditions_5dd1df8/`, `index.csv`) is read on the Julia side today
     (the C-6 EvoGrow campaign path, WP-N32) and on the Python side (WP-N47 baselines); reuse those loaders.
2. **Path builder for Q5.** New entry point (or options on the Q4 builder with Q4 defaults unchanged) that builds the
   Q4 growth path for every (unit, σ, ρ, realization) of the protocol's strata — `dim1`, `dim2`, `dim3_feasible`,
   `dim4`; **not** `dim3_bound_infeasible` — from the observed export data. Same path rules, cap and SSE stop as Q4. Each
   path record carries the cell's `observed_data_sha256` from the export, and whether the path ended at the cap or at the
   SSE stop (needed for diagnostic D1). Output: one paths file for the grid, deterministic order.
3. **Julia runner** `studies/regression/sideproject_q5_noise_fits.jl`: a new file that reuses the Q4 runner's machinery
   (include or shared helpers) so that **`sideproject_q4_path_fits.jl` stays byte-identical**. Per candidate: weak-start
   fit exactly as Q4 (`max_fit_attempts = 1`, bound 10, same optimizer settings fingerprint), trajectory loss on the
   observed noisy data at the observed times; then post-hoc evaluation against clean targets as the C-6 baselines do
   (reconstruction against the clean training trajectory, generalization from the clean test IC). Record format as Q4
   plus σ, ρ, realization, `observed_data_sha256`, and loss evals / ODE solves. CLI as WP-FA4b: input path overrides,
   `--unit-list <file> --index <i>`, one output file per index. **Resume per candidate**: a restarted pod skips
   candidates already in its output file (records are appended atomically per candidate). No time limits of any kind.
4. **Shard lists.** One shard = one (unit, data set) group or a small bundle of them, sized so that a shard takes
   ≲ 3 h by the planning estimate (Q4 per-unit fit times in the Q4 records × candidate counts from the new paths). Order:
   all `dim1`/`dim2` shards first, then `dim4`, then `dim3_feasible`. Put the estimate per stratum in the report.
   - **Probe list:** protocol §9 — one unit each of `dim1`, `dim2`, `dim3_feasible` (choose units of median Q4 cost in
     their stratum, name them) at (0.05, 0) and (0.05, 0.5), realization 1, plus the (0, 0) data set of the same units.
   - **Grid list:** everything, including the (0, 0) control of every unit.
5. **Manifests**, modelled on `k8s/sideproject_q4_job.yaml`: `k8s/sideproject_q5_probe_job.yaml` and
   `k8s/sideproject_q5_job.yaml`; indexed Jobs, `parallelism: 8` (project limit 40 cores, 32 in use), 1 CPU per pod,
   memory as Q4 unless the noisy data need more (state why), `JULIA_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, **no
   `activeDeadlineSeconds`**, image `registry.gitlab.scch.at:443/joedicke/evoode:<COMMIT_SHA>`, inputs under
   `/outputs/sideproject_q5_<COMMIT_SHA>/input/`, outputs under `.../out/`. Header comment with expected runtime, core
   hours and € at 1.50 €/core-h (grid planning estimate in the protocol: ~230–700 core-h, ~1.5–4 days on 8 pods —
   replace with your shard-based estimate, uncertainty stated).
6. **Aggregation** `analysis/scripts/aggregate/aggregate_sideproject_q5.py`: protocol §6 (what is reported) and §7
   (diagnostics D1–D4), with unit counts beside every rate; references from
   `outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv` exactly as protocol §5 (Weak-SINDy `poly_deg3_sin_cos`
   better threshold per stratum × σ × metric; SINDy and E-SINDy same library; Weak-SINDy median and range over all ten);
   controls §8 — the (0, 0) records must reproduce Q4 (candidate lists, chosen models, losses) bit-identically, per-cell
   data hashes equal to the baseline rows, one optimizer settings fingerprint equal to Q4, duplicate records
   bit-identical. A failed control aborts. Accept multiple result files (laptop + Orion), refuse to overwrite existing
   tables (as Q4). Output under `analysis/data/sideproject_residual_growth/q5_*`.
7. **Input staging list** in the report: which local files go to which NFS path, with SHA256 (paths file, shard lists,
   the needed export subset and its index).

## What you may run

- Python unit tests (path builder on an irregular grid, determinism, ρ = 0 bit-identity to `q4_paths.json`, aggregation
  on synthetic records, control failures abort).
- The path builder for the **probe** cells and for the (0, 0) controls of all units, and the ρ = 0 comparison against
  `q4_paths.json`. The full grid paths only if the probe path build projects < 1 h on the laptop; otherwise report the
  projection and leave it to Claude.
- **No Julia** (you cannot run it): Claude parses (`Meta.parseall`), smoke-tests the runner on the laptop and runs the
  probe. Report `blocked` only for that Julia step, with exact commands for Claude.

## Forbidden

- No change to `src/`, to `sideproject_q4_path_fits.jl`, to Q4 outputs or tables, to the Q4 protocol, to the C-6 export.
- **Do not open or read any EvoGrow C-6 result** (`outputs/phase_c_c6_grid_5dd1df8/`,
  `outputs/phase_c_c6_grid_uncapped_5dd1df8/`, anything derived from them) — blind rule.
- Do not touch the uncommitted WP-N48b files (`analysis/scripts/aggregate/aggregate_c6_symbolic_baselines.py`,
  `analysis/scripts/aggregate/run_k8s_symbolic_shard.py`, `baselines/c6_shards.py`,
  `baselines/tests/test_c6_symbolic_execution.py`, `k8s/phase_c_c6_pysr_job.yaml`,
  `k8s/phase_c_c6_pysr_smoke_job.yaml`, `codex/reports/REPORT_WP_N48.md`).
- No time limits or timeouts anywhere, also not in tests or helper scripts. No commit, no push, no cluster command.

## Report

`codex/reports/REPORT_WP_FA5.md`: the three bindings (step 1) with file:line, changed/new files, test results, probe path
build numbers (candidates per cell vs Q4, how many paths end at the cap), shard and cost estimate, staging list, exact
commands for Claude (Julia parse, laptop smoke, probe Job, grid Job, aggregation). Status in `codex/STATUS.md`.
