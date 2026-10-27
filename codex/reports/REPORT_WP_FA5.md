# WP-FA5 — scopes 2–7 delivered, Julia acceptance pending

2026-10-27. **Status: blocked — Umgebung, nicht Sache: Julia parse/smoke is reserved for Claude by CURRENT_TASK.**
The shell works: the first command, `Get-Location`, exited 0. Python execution and the final tests below actually ran.
No Julia command, Git operation, cluster command, fit, campaign or EvoGrow C-6 result read was performed.
No Q5 fitted-model result or success rate is claimed. All delivered changes remain uncommitted.

## Delivered files

- `analysis/scripts/aggregate/build_sideproject_q5_paths.py`: original C-6 observations through the existing Python
  loader, unchanged Q4 growth algorithm, actual observation times, per-equation end flags, observed data hashes,
  weak best-subset upper bound on each observed design, clean Q4 candidate/start controls, deterministic cell order,
  probe/control/grid modes and whole-cell shard lists with planning costs.
- `studies/regression/sideproject_q5_noise_fits.jl`: top-level include of the frozen Q4 runner, strict export CSV/binary
  reader, shape/layout/count/hash checks, unchanged optimizer and observed-first-sample fit/selection, clean-export
  reconstruction/generalization, D5 evaluation on observed times from the clean IC, fit loss evaluations/ODE solves
  and separate evaluation solve counts. Candidate resume validates provenance and rejects torn/duplicate history.
  Each candidate is published by writing the previous JSONL plus the complete new row to a same-directory temporary
  file and renaming it over the destination. Each indexed shard has its own output file.
- `analysis/scripts/aggregate/aggregate_sideproject_q5.py`: all three choices and both upper bounds, raw/pruned
  support and both R² definitions, D1–D5 and cost, pooled and rho-specific reports, matching-library references,
  metric-specific threshold selection on pooled stratum × sigma, and Weak-SINDy's median/min/max over ten configs.
  Rates carry numerators/denominators, distinct unit counts and cell counts. All controls precede table writing.
  Multiple paths/globs are accepted; existing Q5 tables are never overwritten.
- `analysis/scripts/aggregate/prepare_sideproject_q5_inputs.py`: clean-target comparison with baseline integration
  and the complete staging inventory. `audit_sideproject_q5_inputs.py`: all 1,632 baseline hash joins, staging hashes,
  clean path identity and ordered 8-pod planning calculation.
- `analysis/tests/test_sideproject_q5.py`: 16 tests; fixtures derive from actual export cells and Q4 records.
- `k8s/sideproject_q5_probe_job.yaml`, `k8s/sideproject_q5_job.yaml`: indexed Jobs, parallelism 8, one CPU/4Gi,
  Julia and OpenBLAS threads 1, original NFS mount/image pattern, no deadline. No Job was submitted.
- Generated inputs, shard lists, cost files, staging inventory, target-comparison audit and logs:
  `outputs/sideproject_q5_inputs/`. Derived synthetic test artifacts: `outputs/sideproject_q5_tests/`.

`sideproject_q4_path_fits.jl` remains byte-identical, SHA256
`2725a2927c9197fe103a4b21d8a9aad0dea111220ace5eaf99bbcd6ac56933e4` (also asserted by a passing test).
No src, Q4 output/table, protocol, C-6 export, CURRENT_TASK or forbidden WP-N48b file was edited.

## Bindings retained from the completed scope-1 audit

The historical audit below is retained for its detailed evidence; its earlier stop/decision request is superseded.

1. Actual-time weak quadrature already exists at
   `analysis/exploratory/term_relevance/term_relevance.py:186`, especially `:198` (`np.trapz`, explicit observed times).
   Q4 imports and calls it through its existing Q3/FA2 chain. No quadrature change was needed.
2. The amendment controls the IC convention. Q4's `fit_parameters` call remains the model at
   `studies/regression/sideproject_q4_path_fits.jl:100`; `q4_evaluate` is reused from `:12`.
   The baseline uses clean ICs for post-fit reconstruction/generalization at
   `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py:373–379`, and constructs clean targets using
   `integrate_truth` at `:628–629`. Q5 fitting receives the observed trajectory unchanged, including its first time.
   D5 creates a separate evaluation grid; its clean IC never enters fitting or selection.
3. Python reader/hash representation are reused from the baseline file `:93`, `:127`, `:174`.
   There was no existing Julia export reader; the new one is `sideproject_q5_noise_fits.jl:31–67`.
   It reads index.csv, checks raw little-endian binaries and records Python's compact sorted JSON `data_sha` string,
   not the differently shaped campaign hash dictionary.

## Clean evaluation targets and field audit

Q5 evaluates against the export's (0,0), realization-1 trajectories for both ICs. The runner checks both exported
clean trajectories against `build_trajectory` from Q4, including exact times and states, before fitting any candidate.
The Python comparison actually ran the baseline's DOP853 `integrate_truth` for all **48** clean trajectories:
maximum absolute state difference **1.1223801889670426e-5**; maximum difference divided by
`max(1, abs(baseline_target))` **5.053667687770887e-6**; **0/48** arrays bit-identical across the two integrators.
These are numerical agreement measurements, not a claim of baseline-target bit identity. Detailed values are in
`outputs/sideproject_q5_inputs/clean_target_agreement.json`. Q4 bit controls concern the same export/Q4 targets.

Real `index.csv` fields used: system_id, initial_condition_set, dimension, noise_sigma, subsample_rho,
noise_realization, n_observed_points, layout/shape fields, cell_dir, time/state paths and SHA256 values.
`observed_data_sha256` is **derived by existing `data_sha`**, not an index column.
Real baseline fields checked: method, method_config_id, polynomial_degree, include_sin_cos, stlsq_threshold,
system_id, source/target_initial_condition_set, noise_sigma, subsample_rho, noise_realization,
observed_data_sha256, sindy_structure_hit_raw/pruned, reconstruction/generalization_r2_arithmetic_mean_gt_0_9
and *_variance_weighted_gt_0_9. All six baseline success columns have **0 missing values** over 136,080 rows.
Candidate/training/generalization/settings/fit_meta fields come from actual Q4 records. New Q5 analysis fields are
cell_id, sigma/rho/realization, path_end/ended_at_cap, reconstruction, clean_ic_observed_mse and evaluation_ode_solves.
No fixture assumes a nonexistent record-level `success` field.

## Measured input construction and controls

Final probe: **9 cells, 130 path candidates + 9 upper subsets**, **0.877621 s** in the builder's measured cell loop.
Full grid was allowed after the first measured probe projected <1h. Final grid: **1,632 cells**, **21,250 path
candidates + 1,632 upper subsets = 22,882 fits planned**, **118.425696 s** measured in the final cell-build loop.
Interpreter/import/Q4-cost-loading overhead is outside those timers. No timer is a stopping rule.

All **48/48** clean controls reproduced the Q4 candidate dictionaries and upper subsets; every start coefficient
matched. All **1,632/1,632** observed-data hashes match the baseline rows. Repeated construction of a real irregular
noisy cell produced identical candidates, coefficients and metadata. The irregular-grid test also checks the
actual-time trapezoid and endpoint increment directly.

Probe units are the **upper middle order statistic by total Q4 unit fit time**, including its upper subset,
with unit ID breaking ties. This convention chooses an actual unit for even-sized strata:

| Stratum | Unit | Total Q4 fit seconds | Candidates clean / (0.05,0) / (0.05,0.5) | Cap-ending probe paths |
|---|---|---:|---|---:|
| dim1 | sys0006_ic1 | 19.971000 | 10 / 6 / 6 | 3/3 |
| dim2 | sys0026_ic1 | 111.650000 | 15 / 13 / 19 | 3/3 |
| dim3_feasible | sys0061_ic2 | 10439.051917 | 20 / 20 / 21 | 3/3 |

Every noisy probe uses realization 1; each unit also has its (0,0) control.
For the grid, **1,615/1,632** paths reach a cap: dim1 737/748; dim2 675/680; dim4 68/68;
dim3_feasible 135/136. `path_end` records the reason per equation; `ended_at_cap` means at least one equation
reached six terms, with cap precedence if both stopping conditions hold at that state.

Fit/selection/loss bit controls have **not** run in Julia. The aggregation will abort if they fail.
The optimizer fingerprint must equal the sole Q4 fingerprint
`608ac81047860684035841955cf944a50f8dad6a5a6d669775d7c9b51b31fa90`.
Duplicate Q5 records must be identical as entire parsed records, including timing fields and signed Float64 zero;
independently rerun overlapping cells will usually fail this deliberately strict control. Merge disjoint shards or
exact copied records. Each result set must use its matching paths artifact; probe and grid artifacts have different hashes.

## Shards, cost and the approximate three-hour target

One complete (unit,data set) per shard: probe **9**, grid **1,632**. Lists are ordered dim1, dim2, dim4,
dim3_feasible, then unit/sigma/rho/realization. No bound-infeasible dim3 unit is included.
Estimator = mean Q4 candidate fit wall seconds for that unit × new count including the upper subset.
It is a planning proxy, not a measured noise cost. Q4 records are read only from the two sideproject_q4 directories.

| Stratum | Units | Grid shards | Core-h at Q4 cost | EUR at 1.50/core-h |
|---|---:|---:|---:|---:|
| dim1 | 22 | 748 | 10.290318 | 15.44 |
| dim2 | 20 | 680 | 29.065031 | 43.60 |
| dim4 | 2 | 68 | 0.240223 | 0.36 |
| dim3_feasible | 4 | 136 | 204.902157 | 307.35 |
| total | 48 | 1632 | 244.497728 | 366.75 |

Ordered greedy scheduling on 8 pods gives **31.953113 h**, versus an ideal load bound of 30.562216 h.
An unmeasured noise factor x1–x3 gives **244.5–733.5 core-h**, **EUR 366.75–1100.24**, about **1.33–3.99 days**,
excluding startup overhead. Probe: **8.946819 core-h**, **3.041350 h** ordered wall, **EUR 13.42**, before that factor.

**Planning limitation:** 25/1,632 indivisible whole-cell shards exceed the nominal 3h target; maximum **3.694508 h**.
The probe has one at **3.037819 h**. The requested whole-cell granularity is preserved, rather than splitting a
data-set group or imposing a runtime cutoff. Thus the approximate 3h sizing goal has this explicitly quantified
overshoot. It cannot be a strict <=3h guarantee with whole cells under this estimator. There are no runtime limits.
The probe must measure the noise factor; the user decides the grid after seeing those numbers.
Memory stays Q4's 4Gi: observed arrays are at most the clean 512 samples and are often halved; larger memory has no
measured justification. Peak Julia RSS remains unmeasured.

## Staging list — nothing uploaded here

The complete per-file local path → NFS path → SHA256 list is
[`outputs/sideproject_q5_inputs/staging.csv`](../../outputs/sideproject_q5_inputs/staging.csv):
**3,269 files, 36,316,418 bytes**, including **3,264 binaries**, the **unchanged full original index**,
two paths files and two shard lists. Every listed file hash was actually checked by the final audit.
Inventory SHA256: `c8b0383800ce02413848785debc8c9945379ecbde4d21782e6be60ebdca42905`.
The index remains whole so its original hash survives; only the selected cells' binary payloads are staged.
All other clean ICs needed for generalization are among the 48 controls and therefore included.

All NFS destinations start `/outputs/sideproject_q5_<COMMIT_SHA>/input/`:

| Local file | NFS suffix | SHA256 |
|---|---|---|
| outputs/sideproject_q5_inputs/q5_probe_paths.json | q5_probe_paths.json | 8c4641a42a006fbc73ce55b8980596f2cf0eb23486bb81d3cd84e9ff7954735d |
| outputs/sideproject_q5_inputs/q5_grid_paths.json | q5_grid_paths.json | 3d178ba883bea713f2cbbdd07103670fde0a3ce0fd567bb8e71195ebd45363c9 |
| outputs/sideproject_q5_inputs/q5_probe_paths.shards.txt | q5_probe_paths.shards.txt | 5467fe886854cdd66e817b83b0e44ccb2e389475d1ab75e35b7a634dc1a37d8e |
| outputs/sideproject_q5_inputs/q5_grid_paths.shards.txt | q5_grid_paths.shards.txt | 4716b46788d9542bcfbb0c6f51d017be80ffcaaacb68ea7452ed613243f2766c |
| outputs/phase_c_c6_data_conditions_5dd1df8/index.csv | export/index.csv | ce20350b895c963659e9a55a11cc4e53be35be3a9b926803e4e78216a9a65d97 |

For each binary the suffix is `export/<original cell_dir>/<original time_path or state_path>`; staging.csv spells out
every one and its original SHA256. The image must carry the new runner and its Q4/Q3/source dependencies.
No Q3 fit outputs, Q4 fit outputs or baseline results need to be staged for the runner.

## Final verification

- `python -m pytest analysis/tests/test_sideproject_q5.py -q -p no:cacheprovider` — **exit 0, 16 passed,
  3,747 existing np.trapz deprecation warnings, 100.98 s**. Final log:
  `outputs/sideproject_q5_inputs/pytest_verified.log`. This run followed final path generation; no input was regenerated
  during it. Earlier pytest attempts hit the managed Windows mode-0700 temp-directory ACL; the local fixture now
  creates ordinary UUID directories in the test script's own output folder and retains them for review.
- Coverage: real irregular-grid quadrature, deterministic paths, all 48 clean path/start bit controls, complete
  synthetic aggregation/no-overwrite, distinct metric/pooled threshold selection, data hash/baseline hash/source/
  fingerprint/settings/missing candidate/duplicate/signed zero/clean loss/candidate failures before output,
  Q4 runner bytes, YAML resources/thread/index settings and exact shard-list coverage/order.
- Python AST parsing: **5/5** new Python files pass.
- `prepare_sideproject_q5_inputs.py` and `audit_sideproject_q5_inputs.py` — exit 0. The latter checks every staged
  SHA256 and all 1,632 baseline hash joins. Raw summary: `outputs/sideproject_q5_inputs/input_audit.json`.
- Static Julia review covered top-level includes, JSON3 arrays via collect, concrete CSV dictionaries, 0-based list
  indices through the existing Q4 selector, actual index fields, endian/C-order conversion, exact byte lengths,
  missing/duplicate history, observed-vs-clean IC separation and same-directory candidate publication.
  This is **not** a Julia parse/runtime result.

## Commands for Claude — not executed here

Use the pinned Julia 1.12.6. Parse:

```powershell
julia --project=. -e 'VERSION == v"1.12.6" || error("Julia 1.12.6 required"); Meta.parseall(read("studies/regression/sideproject_q5_noise_fits.jl", String)); println("parse ok")'
```

Short laptop smoke, one clean probe cell (10 path fits plus upper subset); run it twice with the same output to
exercise candidate resume. `--limit` counts cells, as in Q4:

```powershell
julia --project=. studies/regression/sideproject_q5_noise_fits.jl --paths outputs/sideproject_q5_inputs/q5_probe_paths.json --export-dir outputs/phase_c_c6_data_conditions_5dd1df8 --unit-list outputs/sideproject_q5_inputs/q5_probe_paths.shards.txt --index 0 --limit 1 --output outputs/sideproject_q5_smoke/index_0.jsonl
```

Additional irregular/noisy smoke: the same command with `--index 2` and output `outputs/sideproject_q5_smoke/index_2.jsonl`.
Full local probe without selection (139 fits; separate output):

```powershell
julia --project=. studies/regression/sideproject_q5_noise_fits.jl --paths outputs/sideproject_q5_inputs/q5_probe_paths.json --export-dir outputs/phase_c_c6_data_conditions_5dd1df8 --output outputs/sideproject_q5_probe_local/results.jsonl
```

After image build and staging according to the inventory, replace `<COMMIT_SHA>` in both manifests and input/output
paths. The Job commands below are documentation only; the second still requires the user's post-probe grid decision:

```powershell
kubectl apply -f k8s/sideproject_q5_probe_job.yaml
kubectl apply -f k8s/sideproject_q5_job.yaml
```

After downloading the complete probe outputs, its aggregation (separate tables):

```powershell
python analysis/scripts/aggregate/aggregate_sideproject_q5.py --paths outputs/sideproject_q5_inputs/q5_probe_paths.json --input "outputs/sideproject_q5_<COMMIT_SHA>/out/probe_index_*.jsonl" --output-dir analysis/data/sideproject_residual_growth/q5_probe
```

Full grid aggregation, after all indexed results are available:

```powershell
python analysis/scripts/aggregate/aggregate_sideproject_q5.py --paths outputs/sideproject_q5_inputs/q5_grid_paths.json --input "outputs/sideproject_q5_<COMMIT_SHA>/out/index_*.jsonl"
```

Disjoint laptop files made with that same grid paths artifact can be listed after `--input` alongside the quoted glob.
Incomplete inputs abort before writing tables. Local Q4 files and canonical baseline details.csv must remain available
for these aggregations. The grid aggregate requires every clean Q4 bit control, not only the three probe units.

---

## Historical session logs — superseded

# WP-FA5 — resumed 2026-10-27; shell execution blocked

Status: **blocked — Umgebung, nicht Sache.** The resumed CURRENT_TASK resolves the scope-1 initial-state binding. The binding-decision stop in the historical audit below is superseded.

## Resumption stop

The first shell call in this session failed before any command executed:

```text
exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
```

The resumed task explicitly requires: "The shell helper failed in your last session: if it fails again, report `blocked` with the error instead of working around it — tests must actually run." Accordingly, no alternative process launcher was used, no implementation was attempted, and no Python test, path build, Julia command, Git operation or cluster command ran. The Node filesystem tool was used only to read the task/protocol and existing report and to write the required status/report. No EvoGrow C-6 result or derivative was opened.

Scopes 2–7 remain unimplemented in this session. No test results, candidate counts, shard estimates or staging hashes are claimed. The immediate prerequisite is a working shell helper, after which scopes 2–7 can proceed under the resolved binding. The task also reserves Julia parsing and smoke execution for Claude.

Only codex/STATUS.md and this report were changed in this session. CURRENT_TASK.md was not modified.

---

The following is the preserved historical scope-1 audit; its initial decision request and binding-blocked status no longer apply.

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
