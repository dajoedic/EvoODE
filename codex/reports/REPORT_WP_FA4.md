# WP-FA4 — Q4 implementation

Status: blocked — Julia run pending (Claude). Environment, not subject matter.

## Delivered

- New Python path builder, aggregation script, and seven tests. Existing FA2/FA3 files and src were not edited.
- New Julia runner; Julia was neither executed nor parsed in this session.
- q4_paths.json: 60 units, 769 distinct path candidates, 60 separate weak best-subset upper-bound candidates. In-process repeated path construction matched candidates and full step logs for all 60 units. Every weak design has 2529 rows.
- Full run: 830 fit_parameters calls including the one forced-true-support control. The two-unit smoke command below requires seven calls. No measured Julia runtime is available.
- Final Q4 CSV tables and run metadata are intentionally pending real Julia results. Tests write derived fixtures and aggregation tables only to temporary directories. No fit result or scientific success rate is claimed.

## Verification

- python analysis/scripts/aggregate/build_sideproject_q4_paths.py — exit 0 on final source with defaults; repeated construction checked in-process.
- python -m pytest analysis/tests/test_sideproject_q4.py -q — 7 passed in 17.45 s on final source.
- python -m pytest analysis/tests -q — 190 passed, 2 failed, 240248 warnings in 47.20 s. Complete output: codex/reports/WP_FA4_pytest.log.
- The two known failures are test_phase_a_evaluation_does_not_overwrite_frozen_artifacts (frozen diagnostics reproduction assertion) and test_build_priors_from_minimal_real_shape_fixture (temporary fixture path is outside REPO_ROOT).
- Tests cover correlated-decoy removal, cross-equation normalisation, six-term cap, determinism, all size rules including sentinel/divergence exclusion, real-reference joins, campaign pruning parity, complete aggregation, and missing-candidate abort before output.

## Data semantics and field audit

The real hierarchy per_run.csv header and records were inspected before building the reference fixture. aggregate_phasec_hierarchy_n43.py, build_evogrow_rows, joins source_initial_condition_set to the registry initial_condition_set; target_initial_condition_set is the other IC. direction is IC1_to_IC2 or IC2_to_IC1. The new join validates all three fields and initial_condition_set explicitly.

Reference fields are existing hierarchy columns: method, configuration, system_id, source_initial_condition_set, target_initial_condition_set, direction, initial_condition_set, seed, realization, noise_level, subsampling_ratio, raw_exact_support_match, pruned_exact_support_match, reconstruction/generalization_r2_arithmetic, reconstruction/generalization_r2_variance_weighted, their availability fields and *_gt_0_9 columns. Clean filtering gives 1980 rows: EvoGrow C-1_capped has 180 rows (three seeds per unit); Weak-SINDy has 1800 rows (ten configurations, three realisations per unit). Counts and uniqueness are checked per unit/configuration. Twenty-one EvoGrow generalisation flags are empty; all 21 have availability=False and generalization_diverged_or_nonfinite=True. They count as failures over the full reference denominator.

Existing Q3 fields verified on a real results.jsonl record: W1.loss, W1.r2, W1.fit_meta.loss_evals, trajectory_control.passed and unit_id. The complete aggregation fixture copies that actual fit_meta inventory and loss, then explicitly adds the new Q4 candidate/training/generalization fields; it does not claim those synthetic Q4 metrics are measured fits.

New path fields are derived analysis outputs: candidate_id, step/origin, active_idxs, per-equation basis_indices/term_names, coefficients, weak_sse, n_rows, flattened p0, k and weak_bic. New Julia fields are params, pruned_active_idxs, training/generalization metrics, optimizer settings/fingerprint and provenance. fit_meta is the existing fit_parameters output, and loss_evals is its existing counter. No success record field is assumed.

## Canonical metrics, pruning and controls

Arithmetic and per-dimension R² reuse studies/regression/run_regression.jl:r2_summary/r2_by_dimension. Variance-weighted R² matches analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py:build_evogrow_rows: average per-dimension R² using the target trajectory dimension variances. Variances use corrected=false (population convention, matching numpy.var in aggregate_variance_weighted_r2.py:load_variance_weights). Reconstruction uses the training target; generalisation uses build_trajectory(system, 3-ic). No test metric enters any size choice.

Julia pruning directly calls studies/regression/diagnostic_systems.jl:pruned_support_idxs, which delegates to pruned_support_idxs_for_equation. Python imports phase1_diagnostic.py:prune_terms and requires exact agreement with Julia indices. Both use per-equation max(1e-6,1e-3*max_abs), with >= inclusion.

Julia includes Q3 machinery at top level without invoking q3_main or reading the P-04 directory. Each candidate has one build_reference_optimizer(max_fit_attempts=1) fit from weak p0, seed 7, followed by training/test simulation. Every record carries a settings fingerprint, source hashes and input hashes. Infinite pre-existing settings are serialized as strings; no wall-clock stopping rule was added. Resume checks identities, full provenance, controls, duplicate/torn JSONL records, and skips completed candidates.

The separate sys0001_ic1/control_true record loads the actual Q3 weak vector/support, fits only that support, and requires UInt64 equality of its training loss to Q3 W1. This control is not a selectable path candidate. It remains unexecuted.

Weak BIC implements log(0) as negative infinity (serialized as a string); it adds no SSE floor. Ties in growth/selection use stored equation, term and path order, without tuning.

## Protocol ambiguity / task differences

No conflict between the task and frozen protocol was found. The frozen protocol does not disambiguate repeated true-size path states: 30 of 60 units have multiple such states, and zero units lack one. To avoid inventing a size-selection rule for the reported-only bound, q4_units.csv reports every matching upper_path state individually. Its summary denominators count these states, explicitly recorded in run metadata; those summaries must not be read as a single chosen-model rate over 60 units. Rules a/b/c retain exactly one row per unit and R7–R9 use only those unit rows. Weak best-subset is obtained from the existing Q1 per-equation table (truth when uniquely best, otherwise recorded best_other_terms) and fitted separately, only for reporting.

## Candidate counts for runtime planning

| Stratum | Units | Path candidates | Min/unit | Max/unit |
|---|---:|---:|---:|---:|
| dim1 | 22 | 133 | 1 | 10 |
| dim2 | 20 | 228 | 2 | 18 |
| dim3_feasible | 4 | 93 | 20 | 27 |
| dim3_bound_infeasible | 12 | 273 | 19 | 33 |
| dim4 | 2 | 42 | 18 | 24 |

Add one best-subset fit per unit and one global Q3 control fit.

| Unit | Stratum | Path candidates |
|---|---|---:|
| sys0001_ic1 | dim1 | 2 |
| sys0001_ic2 | dim1 | 5 |
| sys0002_ic1 | dim1 | 1 |
| sys0002_ic2 | dim1 | 1 |
| sys0003_ic1 | dim1 | 8 |
| sys0003_ic2 | dim1 | 8 |
| sys0005_ic1 | dim1 | 3 |
| sys0005_ic2 | dim1 | 3 |
| sys0006_ic1 | dim1 | 10 |
| sys0006_ic2 | dim1 | 10 |
| sys0008_ic1 | dim1 | 6 |
| sys0008_ic2 | dim1 | 6 |
| sys0009_ic1 | dim1 | 4 |
| sys0009_ic2 | dim1 | 5 |
| sys0011_ic1 | dim1 | 7 |
| sys0011_ic2 | dim1 | 7 |
| sys0012_ic1 | dim1 | 7 |
| sys0012_ic2 | dim1 | 9 |
| sys0017_ic1 | dim1 | 8 |
| sys0017_ic2 | dim1 | 8 |
| sys0023_ic1 | dim1 | 7 |
| sys0023_ic2 | dim1 | 8 |
| sys0024_ic1 | dim2 | 2 |
| sys0024_ic2 | dim2 | 2 |
| sys0025_ic1 | dim2 | 5 |
| sys0025_ic2 | dim2 | 4 |
| sys0026_ic1 | dim2 | 15 |
| sys0026_ic2 | dim2 | 16 |
| sys0027_ic1 | dim2 | 12 |
| sys0027_ic2 | dim2 | 18 |
| sys0028_ic1 | dim2 | 8 |
| sys0028_ic2 | dim2 | 5 |
| sys0029_ic1 | dim2 | 13 |
| sys0029_ic2 | dim2 | 15 |
| sys0031_ic1 | dim2 | 12 |
| sys0031_ic2 | dim2 | 14 |
| sys0032_ic1 | dim2 | 12 |
| sys0032_ic2 | dim2 | 12 |
| sys0038_ic1 | dim2 | 17 |
| sys0038_ic2 | dim2 | 18 |
| sys0043_ic1 | dim2 | 14 |
| sys0043_ic2 | dim2 | 14 |
| sys0052_ic1 | dim3_feasible | 26 |
| sys0052_ic2 | dim3_feasible | 27 |
| sys0054_ic1 | dim3_bound_infeasible | 33 |
| sys0054_ic2 | dim3_bound_infeasible | 24 |
| sys0055_ic1 | dim3_bound_infeasible | 25 |
| sys0055_ic2 | dim3_bound_infeasible | 25 |
| sys0056_ic1 | dim3_bound_infeasible | 21 |
| sys0056_ic2 | dim3_bound_infeasible | 21 |
| sys0057_ic1 | dim3_bound_infeasible | 19 |
| sys0057_ic2 | dim3_bound_infeasible | 19 |
| sys0058_ic1 | dim3_bound_infeasible | 24 |
| sys0058_ic2 | dim3_bound_infeasible | 20 |
| sys0059_ic1 | dim3_bound_infeasible | 20 |
| sys0059_ic2 | dim3_bound_infeasible | 22 |
| sys0061_ic1 | dim3_feasible | 20 |
| sys0061_ic2 | dim3_feasible | 20 |
| sys0063_ic1 | dim4 | 24 |
| sys0063_ic2 | dim4 | 18 |

## Exact commands for Claude (repository root, Julia 1.12.6)

Parse first; this command has not been run here:

```powershell
julia --project=. -e 'Meta.parseall(read("studies/regression/sideproject_q4_path_fits.jl", String)); println("parse ok")'
```

Two-unit smoke including the control unit; use the default append-only output so the full run resumes these fits:

```powershell
julia --project=. studies/regression/sideproject_q4_path_fits.jl --units sys0001_ic1,sys0024_ic1
```

An alternative short limit path (first two units, including the control):

```powershell
julia --project=. studies/regression/sideproject_q4_path_fits.jl --limit 2
```

Full candidate fits, followed by final aggregation:

```powershell
julia --project=. studies/regression/sideproject_q4_path_fits.jl
python analysis/scripts/aggregate/aggregate_sideproject_q4.py
```

Open acceptance items: Julia parse, real candidate fits, bit-identical Q3 W1 control, final real-data aggregation and scientific R7–R9 outcomes. All remain pending Claude; there are no invented outputs. No commits, staging, pushes or cluster/campaign runs were performed.


# WP-FA4b — Orion preparation for Q4 dim 3/4 (2026-10-17)

Status: blocked — environment, not subject matter (Umgebung, nicht Sache). Implementation and Python verification are complete; Julia parsing, CLI smoke tests and the real platform duplicate comparison remain for Claude. Julia and cluster commands were not executed.

## Delivered and compatibility

- Modified only the Q4 runner and aggregation/tests; added the indexed Job and the 19-line unit list. Q3 machinery and src are unchanged. No Git operations were performed. The active laptop directory outputs/sideproject_q4_path_fits/ was neither read nor written by this work.
- Runner flags: --paths (Q4 paths JSON), --q3-results, --q3-weak-starts, --export-dir, --output; --unit-list FILE --index I selects one line with a zero-based index, as an alternative to --units. Missing partners, conflicting selectors, empty/duplicate unit-list entries and invalid indices fail. Existing defaults, --units and --limit remain supported.
- --input-root supplies hash-audit dependencies that the image excludes. It mirrors repository-relative paths below the input directory; image-resident sources are still checked in the repository first. No input digest is rewritten. The override branch verifies the original full manifest, every selected export binary and every non-export frozen input. Default invocation retains the original full-input audit.
- Windows export separators are normalized when resolving an override directory. The runner supplies absolute time/state paths to the existing q3_trajectory_control loader; that function and its numerical comparisons remain unchanged. The loader itself does not read trajectory_manifest.csv, but the frozen q4_paths.json hash audit requires its original full bytes, so the full manifest is staged with the binary subset.
- The only new provenance member is input_paths, recording explicitly supplied path overrides. The original input/source digests and settings fingerprint remain. Resume still requires complete provenance equality. Byte comparisons confirmed unchanged q4_settings, q4_evaluate and the fitting body from basis construction through evaluation. No time limit was added.
- Aggregation --input accepts one or more files/quoted globs; Python run also accepts the original scalar Path. All record provenance is checked, including duplicate records. Duplicate keys compare optimizer_loss, training.loss and generalization.loss as packed Float64 bytes (so +0 and -0 differ); a mismatch aborts before table output. Metadata records duplicates_compared, each input file and digest, both allowed runner hashes, observed hashes and the single common settings fingerprint. No settings mismatch is waived across runner versions or duplicates.

Exactly two runner hashes are constants in aggregate_sideproject_q4.py:

| Version | SHA256 |
|---|---|
| Pre-WP-FA4b (bytes read before editing) | dfce09c938459c318250be60f792e9b46264e702628a902cbb0a79d1202cf648 |
| Post-WP-FA4b | 2725a2927c9197fe103a4b21d8a9aad0dea111220ace5eaf99bbcd6ac56933e4 |

Any other runner hash fails, even if it matches a later local edit. Source-file hashes continue to require the local source bytes. The Q3 file was deliberately left unchanged so existing laptop provenance needs no additional source-hash exceptions.

## Field audit, counts and cost order

Existing fields were inspected in actual files: q4_paths.json units[].unit_id, dim, candidates, upper_candidates and export (including its stored Windows paths), plus Q3 results.jsonl unit_id and W1.fit_meta.fit_time_s. Cost is W1.fit_meta.fit_time_s multiplied by len(candidates) + len(upper_candidates); ties use unit_id. The tests derive their base fields/fit_meta from an actual Q3 W1 record and explicitly add Q4 metrics, including the actual W1.optimizer_loss field. They do not represent measured Q4 fits.

The task's 459-fit estimate differs from the frozen JSON: 408 path candidates + 18 upper_subset candidates = **426 dim-3/dim-4 fits**. Adding the three sys0024_ic1 platform candidates gives **429 fits in 19 pods**. No candidates were added or dropped. The separate sys0001_ic1/control_true remains on the laptop and is unchanged.

| Index (0-based) | Unit | Candidates including upper subset | Q3 W1 fit_time_s | Estimated cost (s) |
|---:|---|---:|---:|---:|
| 0 | sys0061_ic2 | 21 | 993.225000 | 20857.725003 |
| 1 | sys0061_ic1 | 21 | 898.746000 | 18873.666001 |
| 2 | sys0055_ic1 | 26 | 662.899000 | 17235.373998 |
| 3 | sys0054_ic1 | 34 | 131.227000 | 4461.718000 |
| 4 | sys0058_ic1 | 25 | 71.535000 | 1788.375002 |
| 5 | sys0059_ic1 | 21 | 78.406000 | 1646.526003 |
| 6 | sys0058_ic2 | 21 | 73.302000 | 1539.342001 |
| 7 | sys0055_ic2 | 26 | 25.964000 | 675.064000 |
| 8 | sys0056_ic1 | 22 | 12.707000 | 279.554000 |
| 9 | sys0052_ic1 | 27 | 9.850000 | 265.949997 |
| 10 | sys0052_ic2 | 28 | 8.592000 | 240.576000 |
| 11 | sys0054_ic2 | 25 | 6.884000 | 172.100002 |
| 12 | sys0059_ic2 | 23 | 4.385000 | 100.855000 |
| 13 | sys0056_ic2 | 22 | 3.256000 | 71.632001 |
| 14 | sys0057_ic1 | 20 | 1.214000 | 24.280000 |
| 15 | sys0057_ic2 | 20 | 1.015000 | 20.300002 |
| 16 | sys0063_ic1 | 25 | 0.049000 | 1.225001 |
| 17 | sys0063_ic2 | 19 | 0.045000 | 0.855001 |
| 18 | sys0024_ic1 | 3 | 0.088000 | 0.264000 |

Total estimate: 68255.381012 core-seconds = 18.959828 core-hours; the longest unit proxy is 5.793813 hours. These are planning proxies from Q3, not measured Q4 runtimes. The manifest retains the requested ~5–8 h wall / longest ~5 h / ~15–20 core-h estimate and uncertainty up to x2; the exact Q3 proxy for the longest unit is ~5.8 h.

The Job has completions=19, parallelism=8, backoffLimit=10, restartPolicy=Never, one CPU and one Julia/OpenBLAS thread per pod, with no activeDeadlineSeconds. Each index appends only to its own out/index_I.jsonl, including on retry. CPU accounting is 32 existing + 8 new = 40. Memory requests and limits were raised from 2 Gi to **4 Gi per pod**: peak RSS including Julia JIT and solver allocations is unmeasured, and this session cannot establish 2 Gi as sufficient. This is a conservative reservation, not a measured memory claim (8 concurrent pods request 32 Gi).

## Exact input staging inventory

Replace <COMMIT_SHA> consistently with the image revision containing the changed runner and unit list. The table uses pod-visible absolute destinations. On the NFS server replace the leading /outputs/ with /bigdata/data-science/joedicke/ (the Job mounts /bigdata with subPath data-science/joedicke).

Copy exactly these 50 local files (8092674 bytes total). All SHA256 values below were computed from their actual bytes; all entries present in q4_paths.json input_sha256 matched their frozen digest. Export binaries cover both ICs of systems 24, 52, 54–59, 61 and 63; system 24 IC2 is included as requested with the system subset although the platform pod uses only IC1. Every selected unit's time/state pair was checked against this inventory. No live Q4 fit output is an input.

| Local file (repository-relative) | NFS destination (pod-visible) | SHA256 |
|---|---|---|
| analysis/data/sideproject_residual_growth/q4_paths.json | /outputs/sideproject_q4_<COMMIT_SHA>/input/q4_paths.json | 7b0b882e3f3cd61287db92289263b1fc927f3b12a05055374a3abe74d6a95e17 |
| outputs/sideproject_q3_weak_start/results.jsonl | /outputs/sideproject_q4_<COMMIT_SHA>/input/q3_results.jsonl | 2dd594d7e62efa9da9ac4dfd67eaa23b34379fff68d876a5b3b449d5a2cfadf0 |
| analysis/data/sideproject_residual_growth/q3_weak_starts.json | /outputs/sideproject_q4_<COMMIT_SHA>/input/q3_weak_starts.json | 6780799a2e453c4558b3a48d0d61fffe034d3bfff8fdc98973d58c1f1219c627 |
| analysis/data/sideproject_residual_growth/q1_units.csv | /outputs/sideproject_q4_<COMMIT_SHA>/input/analysis/data/sideproject_residual_growth/q1_units.csv | 407fbeea1e52f175c6dd4f211de6127ef1dfbd08f66839f1c575541bdb518865 |
| analysis/exploratory/term_relevance/term_relevance.py | /outputs/sideproject_q4_<COMMIT_SHA>/input/analysis/exploratory/term_relevance/term_relevance.py | bc2e99595c262ea590f24baa1d4880ad6d9418cdd2908f0803817a9a53e941cb |
| analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py | /outputs/sideproject_q4_<COMMIT_SHA>/input/analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py | 6c4b636e4dfb283cfee71dc61073b43d31f02f04350c105542887ce2875fbf8d |
| analysis/scripts/aggregate/build_sideproject_q4_paths.py | /outputs/sideproject_q4_<COMMIT_SHA>/input/analysis/scripts/aggregate/build_sideproject_q4_paths.py | 3cc3bcc47ba3161d0239b716d2d16129c09a2dd88b16b2f89ea060a818eb99f4 |
| analysis/scripts/aggregate/run_sideproject_residual_growth.py | /outputs/sideproject_q4_<COMMIT_SHA>/input/analysis/scripts/aggregate/run_sideproject_residual_growth.py | a960f9f4888492e1d7b707fdaba60c39c601dbe2d6ee0a0ba995ca268fb70f41 |
| docs/sideproject_residual_growth_protocol_q4.md | /outputs/sideproject_q4_<COMMIT_SHA>/input/docs/sideproject_residual_growth_protocol_q4.md | 83f88a2826c68f9936d2379e860c140c82920a5bc76deaca39448e5cca813478 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/trajectory_manifest.csv | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/trajectory_manifest.csv | c92ec60a3453c18d123e29b10c63f28a2cc67a67e5ea6021f014d9847ccb63b0 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0024_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0024_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0024_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0024_ic1_state_f64le_c_order.bin | 7a0cb065a725ce6f96bb42f2513fe021f726e088c0090ed0db0b96fbcf902391 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0024_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0024_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0024_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0024_ic2_state_f64le_c_order.bin | 33ed2a81e4f4e66426a0dc51832715f1c58dce189922fbe2014a3b0a2920f08c |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0052_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0052_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0052_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0052_ic1_state_f64le_c_order.bin | 88e74aa50cb078f28d92cfd1f3bd61d684e54c07f13a3c732a1218e39cc74674 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0052_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0052_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0052_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0052_ic2_state_f64le_c_order.bin | e6125403daf636e9b2ddc7ac67ad4a266415d6ee519c277067159218f6e27c69 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0054_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0054_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0054_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0054_ic1_state_f64le_c_order.bin | c3f821ba213a31e637437e1b75bc79ee56d234438524d86cc808c591900550a6 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0054_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0054_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0054_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0054_ic2_state_f64le_c_order.bin | 0e462496560df0f27d7f9b60ee0013a8a875ce2f443905fc16a4a2341a0165c8 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0055_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0055_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0055_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0055_ic1_state_f64le_c_order.bin | d4e1900669ed840e4981c2314e79007159c935999837262341864d32e1fa8089 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0055_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0055_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0055_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0055_ic2_state_f64le_c_order.bin | d38700c068fd7fd4dd042ca8673b1c09f8473cb39873a70acc3df6e08b2e0b97 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0056_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0056_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0056_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0056_ic1_state_f64le_c_order.bin | 10276e28a124639ae6e9f81ddcd1cd8e3921af744c596f98846fb0d1d125cc3b |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0056_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0056_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0056_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0056_ic2_state_f64le_c_order.bin | 959a49cc2561f63ad336254e5b57cdb8365e14e68ee35dca91ef86ec26a37f7d |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0057_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0057_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0057_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0057_ic1_state_f64le_c_order.bin | 9502decd7c0310446897b904a13ef3580064fa4b793d7602319a276cf96a24e9 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0057_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0057_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0057_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0057_ic2_state_f64le_c_order.bin | 9d3cd2297b9d73beffac59869633ae5efa5029f9345ccbe7a8a5cba23ffda309 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0058_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0058_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0058_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0058_ic1_state_f64le_c_order.bin | 7826234290aae87558458194073c3f9665cf80911bd013db3de00487ad06b2c0 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0058_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0058_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0058_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0058_ic2_state_f64le_c_order.bin | f258d81ec92a8f4dc69b21c812cdb2e976a5627e399435d21ff2c349144a4957 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0059_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0059_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0059_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0059_ic1_state_f64le_c_order.bin | c29655fc0d92b2c872776c1db49cb70f7bd4b445cb39a011ad5104c7fede651c |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0059_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0059_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0059_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0059_ic2_state_f64le_c_order.bin | 7b580b1d4821abfa1424f7348d9baa068f2dbe0252ade52e8134d20151707b21 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0061_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0061_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0061_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0061_ic1_state_f64le_c_order.bin | 65c06eabaf8d55ef89e2b4f2b9226ed0f6eec60fec36da597ca514ab25f29081 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0061_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0061_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0061_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0061_ic2_state_f64le_c_order.bin | af35cc8103aee5b295742c25bbf92522fbcc333c33577707f230f3eda826db56 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0063_ic1_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0063_ic1_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0063_ic1_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0063_ic1_state_f64le_c_order.bin | c260eda10dd542ff304045970c8ba0a7865eb34eff31db77f5bdd9f18efa3c32 |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0063_ic2_time_f64le.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0063_ic2_time_f64le.bin | ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f |
| outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/cells/system_0063_ic2_state_f64le_c_order.bin | /outputs/sideproject_q4_<COMMIT_SHA>/input/trajectory_export/cells/system_0063_ic2_state_f64le_c_order.bin | f5f6ee38b7f9b01bd9078cc1597df308e3f62c05d550fac638eec2446c7233a6 |

The six additional analysis/docs files above are needed solely for the frozen input hash audit and are absent from the image. studies/regression/phase_c_support.json, benchmarks/data/strogatz_extended.json and the Q3 source dependencies already come from the image and must match their hashes; do not replace them. The unit list is baked into the image at /opt/EvoODE/studies/regression/sideproject_q4_orion_units.txt, not copied to NFS. No staging, image build or cluster action was performed here.

## Commands for Claude (not executed here)

After the current laptop run finishes, parse the changed Julia source using the pinned Julia 1.12.6:

~~~powershell
julia --project=. -e 'Meta.parseall(read("studies/regression/sideproject_q4_path_fits.jl", String)); println("parse ok")'
~~~

Short local CLI smoke: index 18 is sys0024_ic1 (3 fits); --limit 1 selects one unit, not one candidate. The output is deliberately outside the active laptop directory:

~~~powershell
julia --project=. studies/regression/sideproject_q4_path_fits.jl --paths analysis/data/sideproject_residual_growth/q4_paths.json --q3-results outputs/sideproject_q3_weak_start/results.jsonl --q3-weak-starts analysis/data/sideproject_residual_growth/q3_weak_starts.json --export-dir outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export --input-root . --unit-list studies/regression/sideproject_q4_orion_units.txt --index 18 --limit 1 --output outputs/sideproject_q4_fa4b_smoke/results.jsonl
~~~

Full local invocation for the 18 dim-3/dim-4 units (documentation only; do not launch alongside the laptop run):

~~~powershell
julia --project=. studies/regression/sideproject_q4_path_fits.jl --units sys0061_ic2,sys0061_ic1,sys0055_ic1,sys0054_ic1,sys0058_ic1,sys0059_ic1,sys0058_ic2,sys0055_ic2,sys0056_ic1,sys0052_ic1,sys0052_ic2,sys0054_ic2,sys0059_ic2,sys0056_ic2,sys0057_ic1,sys0057_ic2,sys0063_ic1,sys0063_ic2 --output outputs/sideproject_q4_fa4b_dim34/results.jsonl
~~~

The Job command is the full indexed NFS invocation; it does not use --limit. After Claude obtains/downloads the 19 output files and the laptop file is complete, aggregate them with a quoted glob (or list each downloaded file):

~~~powershell
python analysis/scripts/aggregate/aggregate_sideproject_q4.py --input outputs/sideproject_q4_path_fits/results.jsonl "outputs/sideproject_q4_<COMMIT_SHA>/out/index_*.jsonl"
~~~

An otherwise nonduplicated complete merge must report duplicates_compared=3 for sys0024_ic1. Its measured platform losses must pass the bit comparison; no cross-platform equivalence is claimed before that run. The sys0001_ic1/control_true reference check remains mandatory.

## Verification

- Final targeted command: python -m pytest analysis/tests/test_sideproject_q4.py -q --basetemp tmp/wp_fa4b_q4_final — exit 0, **17 passed in 14.82 s**. Log: codex/reports/WP_FA4b_q4_pytest.log.
- Full command: python -m pytest analysis/tests -q — exit 1, **200 passed, 2 failed, 240248 warnings in 103.84 s**. Log: codex/reports/WP_FA4b_pytest.log. The two failures are exactly the known test_phase_a_evaluation_does_not_overwrite_frozen_artifacts (frozen diagnostics reproduction assertion) and test_build_priors_from_minimal_real_shape_fixture (temporary records.csv outside REPO_ROOT).
- New aggregation coverage: list and glob merge, both frozen runner versions together, three sys0024_ic1 duplicate comparisons, no double counting (829 candidate table rows), bitwise loss mismatch including signed zero in training/generalization/optimizer loss, unknown runner rejection, differing fingerprints in unique and duplicate records, invalid duplicate source hashes, unmatched/empty result inputs and the post-runner constant matching the actual file.
- Python AST parsing passed for both changed Python files. YAML parsing and structural assertions passed for indexed mode, 19 completions, parallelism 8, backoffLimit 10, one CPU / 4 Gi request and limit, no deadline at Job or Pod level and the zero-based index shell argument.
- Static runner review covered all included files and the unchanged Q3 loader, JSON3.Object conversion through pairs, collection types for Set operations, guarded tryparse/zero-based indexing, actual export fields and path normalization. No Julia runtime result is reported.

Open acceptance: Claude must parse/smoke-test the CLI in Julia 1.12.6 after the laptop run; the real NFS invocation, platform bit-identity comparison and completed real-data aggregation remain unexecuted. All changes are left uncommitted.


## WP-FA4c — source hash LF/CRLF variants

Implemented in analysis/scripts/aggregate/aggregate_sideproject_q4.py and analysis/tests/test_sideproject_q4.py. Source checks now accept SHA256(local raw bytes) or SHA256(local bytes with every CRLF replaced by LF), and reject any other digest before writing tables. No decoding, whitespace stripping, lone-CR replacement, or working-tree normalization is performed.

q4_run_metadata.json gains source_sha256, keyed by the original source path. Each entry contains raw_sha256, lf_sha256, raw_matches and lf_matches. Counts cover every input record, including the control and duplicate candidates before deduplication. If the two accepted hashes coincide, a matching record increments both counters; these counters are variant matches, not mutually exclusive categories.

Field audit: the first real outputs/sideproject_q4_path_fits/results.jsonl record has provenance fields q3_weak_sha256, paths_sha256, settings_fingerprint, runner_sha256, protocol_commit, q3_results_sha256 and source_sha256. Its source_sha256 map has 41 entries, including studies/regression/sideproject_q3_weak_start.jl. The Julia source-map builder was inspected: the Q3 runner source is inserted into that map by the Q4 runner, so it receives the same variant check. The runner_sha256 field remains checked against the two frozen constants, rather than local bytes. The metadata variant fields are new aggregation output, not assumed record fields.

Data checks (including the frozen input_sha256 audit and trajectory inputs), paths_sha256, q3_results_sha256, q3_weak_sha256, settings-fingerprint equality and trajectory-control checks are unchanged. No Julia file or file under src/ was edited; no existing file's line-ending convention was changed. The current runner's raw SHA256 remains 2725a2927c9197fe103a4b21d8a9aad0dea111220ace5eaf99bbcd6ac56933e4, so the two-runner-hash table above is unchanged. No Git operations, fits, campaign, cluster action, or manifests were performed.

Verification:

- python -m pytest analysis/tests/test_sideproject_q4.py -q — exit 0, **23 passed in 12.04 s**.
- python -m pytest analysis/tests -q — exit 1, **206 passed, 2 failed, 240248 warnings in 64.06 s**. Full output: codex/reports/WP_FA4c_pytest.log. The failures are exactly the two already documented: test_phase_a_evaluation_does_not_overwrite_frozen_artifacts (frozen diagnostics reproduction assertion) and test_build_priors_from_minimal_real_shape_fixture (temporary records.csv outside REPO_ROOT).
- Both modified Python files passed AST parsing and retain LF endings (0 CRLF sequences before and after).
- Six added test cases cover CRLF and LF hashes in a complete aggregation, serialized metadata counts including a duplicate, changed-content rejection, coincident-hash counters and lone-CR preservation, and exact data-input hashes for each of paths_sha256, q3_results_sha256 and q3_weak_sha256. The CRLF source fixture is derived from the actual Q3 Julia source; existing result fixtures retain their real Q3 W1 basis with explicit Q4 field additions.

All acceptance checks completed with only the two known suite failures. Changes remain uncommitted.
