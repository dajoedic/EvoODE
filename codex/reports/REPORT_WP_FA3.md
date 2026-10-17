# WP-FA3 — Q3 weak-form warm starts

Status: **blocked — Umgebung, nicht Sache: Julia run pending (Claude)**.
Python implementation, weak-start generation and Python verification are complete.
Julia was not executed, as explicitly required by CURRENT_TASK.md and CODEX_PROTOCOL.md.
There are no measured W0/W1 losses, reconstruction rates, R5/R6 decisions or Julia control results yet.

## Files delivered

- analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py
- analysis/data/sideproject_residual_growth/q3_weak_starts.json
- studies/regression/sideproject_q3_weak_start.jl
- analysis/scripts/aggregate/aggregate_sideproject_q3.py
- analysis/tests/test_sideproject_q3.py
- This report and codex/STATUS.md.
- Python verification logs and exit records: outputs/sideproject_q3_weak_start/python_verification/.

No Git commands, staging, commits or pushes were performed. CURRENT_TASK.md, the frozen protocols,
existing Python/Julia helpers and src/ were not edited. No campaign, cluster or regression run was
started. The only scientific output generated here is the requested weak-start JSON; the aggregation
CSVs/metadata await actual Julia results.

## Protocol precedence: required correction to the task

The task says to read P-04's oracle_starts. The frozen protocol c81e7c6 §§1/3 requires a comparison
on the **true structure**. The existing runner defines oracle_terms as the intersection of the
original discovered terms and true_terms, then fits oracle_starts on that intersection.
reference_starts are fitted on true_terms (wp_n4_multistart_refit.jl, _run_record_phase_c).

All 180 P-04 records from the 36 allowed shard files were inspected. In **101/180** cells,
oracle_structure differs from true_structure and oracle_is_true_subset is true. Therefore both the
new aggregation and the three start-1 controls use **reference_starts**, following the task's explicit
protocol-precedence instruction. No oracle records are silently substituted or mixed into the
reference. The aggregation metadata records this deviation. The aggregation reuses best_start and
checked_starts from aggregate_phasec_restart_curve.py: minimum loss in the first k starts, with
exact equal-loss ties resolved by the first entry in stored order (not by R²).

## Weak starts and parameter ordering

The builder reuses imports from run_sideproject_residual_growth.py / term_relevance.py. It uses
build_design(..., "weak", ...), the FA2 WeakFit augmented QR compression, and the same NumPy SVD
lstsq on the true-support columns. It divides the fitted normalized-column coefficients by the
original column norms. There is no centering, intercept special case or Gram-matrix solve. SSE is
WeakFit.sse on the same support.

The order is defined in src/basis/interface.jl:24 (build_rhs), specifically the outer equation loop
and inner loop over structure.active_idxs[k]. StructureSpec in src/structure/interface.jl:12 stores
the supplied vectors and does not sort them. The Q3 structures use sorted unique basis indices, as
P-04's _fit_fixed_structure_once does; the Python flattening routine follows the stored order and is
also tested on an intentionally unsorted two-equation structure.

The successful default builder invocation exited **0** and wrote:

- **30 systems, 60 unique (system, IC) units, 118 equations, 236 coefficients**.
- Strata: dim1 **22**, dim2 **20**, dim3_feasible **4**, dim3_bound_infeasible **12**, dim4 **2** units.
- **22 coefficient entries** have |c_w| > 10. These are reported, not used to alter settings.
- q3_weak_starts.json SHA256: 6780799a2e453c4558b3a48d0d61fffe034d3bfff8fdc98973d58c1f1219c627.
- Rechecking all input_sha256 entries after the tests found **0 mismatches**.

Per equation the JSON contains term names, 1-based basis indices, coefficients and weak SSE. Each
unit carries active_idxs, p0 in build_rhs order, the export trajectory SHA256, and the manifest row
needed to validate the binary export in Julia. All inputs to the builder are hashed.

## Field audit against real records

The fixture starts from the actual first line of
outputs/phase_c_c5_restart_curve_5dd1df8/out/shard_001_of_036/starts.jsonl
(cell sys0001_seed123_ic1). Tests copy that record and visibly edit only the controlled cases.
A second completeness test uses all real P-04 records and the generated weak-unit identities;
its W-arm values are explicitly copied fixture values, never scientific Q3 results.

| Field | Origin |
|---|---|
| system_id, initial_condition_set, seed, cell_key, system_name | Existing P-04 record fields |
| true_structure, oracle_structure, oracle_is_true_subset | Existing P-04 record fields |
| trajectory_hash.state_sha256, trajectory_hash.time_sha256 | Existing P-04 record fields |
| reference_starts / oracle_starts | Existing lists of start records |
| start_index, start_seed, loss, r2, r2_by_dim, coefficients, optimizer_loss | Existing fields inside each start |
| fit_meta.loss_evals, solver_retcodes, optimizer_retcodes, retcode | Existing fields inside each start's fit_meta |
| term, term_index, coefficient | Existing fields inside nested per-equation coefficient lists |
| support_idxs, support_terms, dim | phase_c_support.json; verified by existing basis-consistency helper |
| stratum | Existing stratum_for analysis helper, not a P-04 record field |
| unit_id, p0, equations, weak_sse, export | New weak-start artifact fields |
| W0, W1, trajectory_control, random_start_control, source_sha256, p04_sha256 | New Julia record fields |
| *_success, evaluation sums/medians, relative loss comparisons, R5/R6 | New aggregation calculations |

There is no assumed top-level success field or top-level loss_evals field in a real P-04 start.
Success is calculated strictly as finite R² > 0.9, including strict failure at exactly 0.9.

## Julia implementation and static review

The new runner includes wp_n4_multistart_refit.jl at top level, which already includes
run_regression.jl and wp_n25_phase_c_c5_common.jl. It does not include them again or include code
inside a function. Training trajectories use build_trajectory(system, ic) exactly as P-04.
W0 uses simulate with every simulation setting taken from build_reference_optimizer(max_fit_attempts = 1),
including clamp_val, tolerances, solver iteration limit and divergence settings. Its original and
effective clamped parameters are both retained. W1 passes the original p0 directly to one
fit_parameters call using that same single-attempt optimizer. A fixed seed **7** supplies options and
RNG state for reproducibility; no starts or settings are selected from W results.

The runner records losses, R² and per-dimension R², model coefficients, optimizer loss, complete
fit_meta, sentinel status and the number of weak entries beyond 10. The sentinel convention is the
existing P-04 >= 1e6 convention. JSONL writes are append-only; completed unit IDs are skipped only
after source, weak-start, P-04 input hashes and stored control results are checked. Duplicate IDs,
changed provenance and a torn final JSON line abort; the runner never truncates the file. A
15-minute session timer terminates the process, preserving completed lines for an unchanged resume.

For each unit, the export binary hashes are checked, time arrays must match exactly, and the state
hash must match or the reported maximum elementwise relative difference must be < 1e-8. Relative
error uses max(abs(export state), eps(Float64)) as denominator to handle zero values. State bytes
are read as little-endian Float64 and reshaped from time-by-dimension C order explicitly.

The three preselected p0=nothing start-1 controls are:

| Unit | Dimension | System | P-04 seed |
|---|---:|---|---:|
| sys0001_ic1 | 1 | RC-circuit (charging capacitor) | 7 |
| sys0024_ic1 | 2 | Harmonic oscillator without damping | 7 |
| sys0052_ic1 | 3 | Maxwell-Bloch equations (laser dynamics) | 7 |

These call the existing _fit_fixed_structure_once with start index 1 and compare Float64 loss bits
against reference_starts[1]. Failure aborts before the unit is appended. Julia VERSION must be
1.12.6. Static review covered transitive includes, actual helper signatures, JSON3.Object access and
conversion, Set operations, optional random-start controls, missing indices, coefficient ordering,
binary shapes/endianness and append/resume handling. This is not a substitute for Julia execution.

## Aggregation

The production aggregation requires all **60 unique units** and all **180 P-04 cells** with seeds
7/42/123, plus the trajectory controls on every unit and all three start-1 controls. It validates
weak-input hashes, Julia runner/source hashes and P-04 input hashes. It writes one CSV row per unit;
P-04 best-of-1/3/10 losses, R², success flags, selected start index and loss-evaluation sums each get
per-seed columns. Reference evaluation sums are also reduced to their median across the three
cells for each unit. W0/W1 coefficients and W1 fit_meta remain available in the unit CSV.

R5 compares W1 unit success rate to true-structure P-04 best-of-10 cell success rate; R6 uses
best-of-3. Numerators and denominators are explicit and the comparison uses integer cross products.
Non-primary strata have decision=reported_only and no pass/fail verdict. W0 rates, evaluation
medians, coefficient-bound counts and sentinel counts are reported alongside the rules. Loss
comparisons are per seed: exact equality or abs(W1 - P04) <= 1e-12 * abs(P04) is equal, including
exact equality at zero; otherwise better/worse follows loss order.

## Verification actually executed

- python -m pytest analysis/tests/test_sideproject_q3.py -q
  - Final result: **15 passed**, **2508 warnings**, **5.08 s**, exit **0**.
  - Log: outputs/sideproject_q3_weak_start/python_verification/q3_tests_final.log.
  - Covers parameter order, exact affine-linear weak recovery, real-record field shape, best-of-k
    tie behavior, strict R² threshold, unit/cell denominators, R5/R6, reported-only strata, relative
    loss comparisons, evaluation sums, all-60 completeness and failed control paths.
- python analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py
  - Successful default run: exit **0**, **60 units / 118 equations**.
  - Log: outputs/sideproject_q3_weak_start/python_verification/builder.log.
- python -m pytest analysis/tests -q
  - Final result: **183 passed, 2 failed**, **240248 warnings**, **53.22 s**, exit **1**.
  - Log: outputs/sideproject_q3_weak_start/python_verification/analysis_tests_final.log.
  - Existing failures, left unchanged as instructed:
    1. test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts
       — frozen diagnostics reproduction assertion.
    2. test_t2a_candidate_priors.py::test_build_priors_from_minimal_real_shape_fixture
       — temporary records.csv is outside REPO_ROOT for Path.relative_to.

The normal terminal tool failed before process creation (setup refresh had errors); Python was run
through the available Node child_process API instead. An initial combined invocation hit the
Node tool timeout and reset its kernel before producing a weak-start artifact. The unchanged
commands were then run with durable logs; no settings were changed and the default builder output
was successfully written once. The suite was repeated after adding the complete-data fixture test;
the final numbers above come from that final invocation.

## Pending commands for Claude

Run from the repository root, with the project's Julia 1.12.6 environment. The smoke and full run
share the same append-only output so the three completed smoke units are reused.

~~~powershell
julia +1.12.6 --project=. studies/regression/sideproject_q3_weak_start.jl --units "sys0001_ic1,sys0024_ic1,sys0052_ic1" --limit 3 --output outputs/sideproject_q3_weak_start/results.jsonl
julia +1.12.6 --project=. studies/regression/sideproject_q3_weak_start.jl --output outputs/sideproject_q3_weak_start/results.jsonl
python analysis/scripts/aggregate/aggregate_sideproject_q3.py --input outputs/sideproject_q3_weak_start/results.jsonl
~~~

If the 15-minute timer stops a run, repeat the identical full command to resume; do not change
settings. Do not rerun the weak builder: the verified weak-start artifact already exists and the
builder intentionally refuses overwrite. The aggregation also refuses to overwrite existing Q3
CSV/metadata outputs.

Open acceptance items: executing Julia smoke and full runs, achieving all trajectory and bit-identical
start-1 controls, and generating q3_units.csv, q3_rules_by_stratum.csv and q3_run_metadata.json from
those actual results. **Umgebung, nicht Sache — Julia run pending (Claude).**

## WP-FA3b

Removed both 900-second checks, the session Timer and its close/try/finally wrapper,
and the unused started variable. The earlier timer description above is superseded.
No replacement limit or option was added.

Changed runner ranges (new line numbers): 149–150 (removed timer origin),
191–197 (unit loop without the two time checks), and 201–203 (direct q3_main call).
Runner diff-stat equivalent: 1 insertion, 12 deletions (214 lines → 203 lines);
all other runner content is unchanged. Fit settings, controls, resume logic and
output format remain unchanged. This report section is append-only.

Verification: exact in-memory comparison against the original runner with only
the specified removals and entry-point simplification; no remaining 900, Timer,
session_timer, started, session-limit or 15-minute references in the runner.
Julia was not executed, as required. No Git commands or runs were started.

## WP-FA3c

Renamed the reserved Julia keyword used as a local variable to `export_info`
in `studies/regression/sideproject_q3_weak_start.jl` (203 lines, unchanged line count):

- Line 57: renamed the local binding; the JSON key `unit["export"]` is unchanged.
- Lines 58, 59: updated the time/state path lookups.
- Lines 60, 61: updated the time/state SHA256 lookups.
- Line 63: updated the state-shape lookup.
- Line 71: updated the state-hash comparison.
- Line 75: updated the exported state SHA256 lookup in the returned dictionary.
- Line 76: updated the hash-identity comparison in the returned dictionary.

Verification: compared the complete before/after text in memory; exactly 9 lines
changed, comprising 1 binding and 8 references. The full file was manually reviewed
for the listed reserved identifiers, block/end balance, delimiter balance, Python-style
syntax, and unintended string interpolation. No additional issues in those classes
were found. All dollar signs occur in intended `$(...)` interpolations. No further
runner changes were necessary. Fit settings, controls, resume logic and output format
are unchanged. The previous report text is preserved and this section is appended.

Julia was not executed, as explicitly forbidden for WP-FA3c; this is a static syntax
correction, not a Julia parser or runtime validation. No Git operations or scientific
runs were performed. Optional validation commands for Claude (not executed here):

~~~powershell
julia +1.12.6 --project=. studies/regression/sideproject_q3_weak_start.jl --units "sys0001_ic1,sys0024_ic1,sys0052_ic1" --limit 3 --output outputs/sideproject_q3_weak_start/results.jsonl
julia +1.12.6 --project=. studies/regression/sideproject_q3_weak_start.jl --output outputs/sideproject_q3_weak_start/results.jsonl
~~~
