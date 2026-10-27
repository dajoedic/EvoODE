# WP-FA5 — binding audit; stopped before implementation

Status: **blocked — initial-state binding requires the user decision explicitly required by CURRENT_TASK scope 1.** This is a substantive binding conflict, not the separate Julia environment limitation.

## Stop condition and decision

The task says: "If the two conventions differ, report it and stop (blocked) before writing the runner — the user decides."

The C-6 SINDy-family harness starts fitted-model reconstruction at the **clean training IC on the clean grid**, even when fitting used noisy, thinned observations. Q4's optimizer and evaluator instead initialize from the **first row of the trajectory supplied to each call**, at that trajectory's first time. In Q4 that trajectory is clean, so the realized initial states coincide with the baseline convention. Passing Q5's observed trajectory to the unchanged Q4 fit/evaluation machinery would change the initial state under noise and can also change the starting time under thinning. This audit identifies that incompatibility; it does not claim Q4 itself fitted noisy data.

A decision is needed on authorizing a Q5 adaptation that decouples the clean simulation initial state/time from the observed loss targets/times while preserving the optimizer and Q4 source. Merely using clean reconstruction after an observed-first-point fit would not meet the requirement that fit, selection and reconstruction all use the baseline convention. Overwriting the first observed row with a clean state would change the loss data and is not a valid resolution. No such adaptation was implemented pending the required decision.

## Binding 1 — quadrature

- analysis/scripts/aggregate/build_sideproject_q4_paths.py:8–12 imports build_design from build_sideproject_q3_weak_starts.py; :87 calls it with trajectory.time and trajectory.state.
- analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py:15–18 reexports it from run_sideproject_residual_growth.py.
- analysis/scripts/aggregate/run_sideproject_residual_growth.py:19–22 imports the actual implementation from analysis/exploratory/term_relevance/term_relevance.py.
- analysis/exploratory/term_relevance/term_relevance.py:186–200 evaluates the basis on observations; uses index-window lengths (1, 2, 4, 8, 16); integrates with np.trapz(..., x=time[start:stop+1], axis=0) at :198 and uses endpoint state differences at :199.

There is **no uniform-spacing assumption in this quadrature**. It already uses actual observation times and constant test functions on those index windows. No quadrature modification is needed for rho=0.5. No path builder was run, so bit identity to q4_paths.json is not claimed.

## Binding 2 — initial states, with source evidence

| Layer | Source | Existing behavior |
|---|---|---|
| N47 entry | analysis/scripts/aggregate/run_k8s_sindy_shard.py:16, :90–103 | Calls the N34 harness with dop853. |
| Baseline fitting | analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py:348–355 | Fits the library to observed_x and observed_t; these sparse-regression fits do not themselves integrate a trajectory. |
| Baseline simulation | same file :373–379 | For reconstruction uses clean_by_ic[source_ic][0, :]; for generalization uses clean_by_ic[target_ic][0, :]; both use clean_t. |
| Baseline clean target construction | same file :626–631 | Calls integrate_truth for both clean ICs. The control-only alternate branch :618–625 loads clean exported trajectories. |
| Q4 train and test | studies/regression/sideproject_q4_path_fits.jl:76–78 | Builds clean training and other-IC trajectories. |
| Q4 fitting | same file :98–106 | Passes train directly to fit_parameters; evaluates the same train and the clean test. |
| Optimizer simulation | src/optimize/bfgs.jl:166–180 | _predict_traj uses u0=collect(traj.x[1, :]), tspan=(traj.t[1],traj.t[end]); :203 saves on traj.t. |
| Q4 post-fit simulation | studies/regression/sideproject_q4_path_fits.jl:12–17; src/simulate/solve.jl:27–39 | simulate likewise uses the supplied trajectory's first data row/time. |
| Clean trajectory construction | studies/regression/run_regression.jl:575–583 | Uses system[:init_sets][ic_set] on the clean grid. |

The clean Q4 case hides the difference between "first supplied observation" and "clean initial state". It is consequential in the requested Q5 application.

### Original export evidence (no fitted results)

Read directly from the existing C-6 export index and binary files for system 1, IC1, realization 1. Both binary SHA256 values matched their index fields for all four cells (8 checks).

| sigma | rho | observed points | first observed time | first observed state |
|---|---|---|---|---|
| 0 | 0 | 512 | 0 | 10 |
| 0.05 | 0 | 512 | 0 | 9.77123693516151 |
| 0 | 0.5 | 256 | 0.019569471624266144 | 9.935560931119724 |
| 0.05 | 0.5 | 256 | 0.05870841487279843 | 9.395677969643407 |

The baseline clean training IC for this unit is the clean cell's state 10 at time 0. Therefore simply supplying the observed trajectory to Q4's optimizer does not preserve that convention, including in the subsampling-only case.

## Binding 3 — existing C-6 data access

**Julia campaign (N32):** there is no export-index loader in the inspected campaign path. studies/regression/run_regression.jl:855–858 builds the clean trajectory, applies apply_phase_c_data_condition, then hashes the resulting observed trajectory. studies/regression/phase_c_data_condition.jl:43–71 applies seeded multiplicative noise and random thinning; :73–79 hashes time/state. It does not read index.csv. The export writer studies/regression/export_phase_c_data_conditions.jl:59–72 uses the same generator then export_trajectory!; :75–91 writes index.csv. Thus "reuse the Julia loader" cannot mean a preexisting N32 CSV reader: this path regenerates data. A future Q5 implementation must make export consumption and hash verification explicit rather than silently regenerate it.

**Python (N34/N47):** reuse analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py:93–124 read_export_index and :127–153 read_index_cell. The latter checks layout, shapes, counts and binary hashes, resolving export_root / cell_dir / time_path or state_path. N47's wrapper normalizes/shards the index at analysis/scripts/aggregate/run_k8s_sindy_shard.py:58–76, then invokes this harness. observed_data_sha256 is not an index column: data_sha at run_phasec_noise_sindy_baselines.py:174–179 derives the canonical JSON string from the index's time_sha256 and state_sha256. The Julia campaign's same-named record field is a dictionary including hash_format (phase_c_data_condition.jl:73–79), so those representations must not be confused.

## Changes, verification and pending work

Only codex/STATUS.md and this new report were written. CURRENT_TASK.md, Q4 source/outputs/tables, src/, protocols, the export and the listed WP-N48b files were not modified. No Git operation, Julia command, cluster command, fit, campaign or path build was run. No EvoGrow C-6 result or derivative was opened.

The shell helper failed before executing the initial read command (setup refresh/helper_unknown_error). File reading and the four-cell binary/hash audit used the available Node filesystem tool. This did not run Python tests or scientific computation. No test pass count or Julia acceptance is claimed.

Source/data identity observed during this audit:

- studies/regression/sideproject_q4_path_fits.jl SHA256: 2725a2927c9197fe103a4b21d8a9aad0dea111220ace5eaf99bbcd6ac56933e4 (matches the FA4 report).
- outputs/phase_c_c6_data_conditions_5dd1df8/index.csv SHA256: ce20350b895c963659e9a55a11cc4e53be35be3a9b926803e4e78216a9a65d97.

Scopes 2–7 remain pending the scope-1 decision: no Q5 builder, runner, shard lists, manifests, aggregation or staging files exist from this session. Candidate/cap counts, median-cost probe units, shard/cost estimates and tests are therefore not reported. Julia parse/smoke, probe/grid Job and aggregation commands cannot yet target delivered Q5 artifacts; providing executable commands for nonexistent artifacts would be misleading. After the binding is resolved and implementation completed, Claude must perform the pinned Julia 1.12.6 parse/smoke and probe; the grid still requires the user's post-probe decision.
