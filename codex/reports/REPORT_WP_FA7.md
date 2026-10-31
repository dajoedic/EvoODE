# WP-FA7 — Q6 stage 1 implementation; acceptance blocked

Implemented the estimator, sparse primary/secondary floors, pluggable growth path,
runner and focused tests. Acceptance is **blocked** by a historical Q5 hash mismatch
and an actual failure of the frozen reference-prefix control. Neither input nor
control was changed. No full grid, trajectory fit, simulation, Julia or Git operation
was run. No scientific classification totals, end-reason totals, recall, structure,
trajectory-quality or observed-data estimator-quality values were evaluated or reported.

## Deliverables

- `analysis/scripts/aggregate/build_sideproject_q6_paths.py`
- `analysis/tests/test_sideproject_q6.py`
- `codex/reports/WP_FA7_pytest.log`
- Smoke failure logs: `outputs/sideproject_q6_paths/validation/smoke_a.log` and
  `smoke_b.log` (gitignored).

The original growth function, Q4/Q5 builders, weak design, Q5 inputs, records,
frozen protocols and listed WP-N48b files were not edited. All deliverables remain
uncommitted.

## Blocking controls

### Historical hash

Both real-manifest smoke attempts exit with code 1 before processing any cells:

```text
ValueError: Q5 input hash mismatch: docs/sideproject_residual_growth_protocol_q5.md
```

The expected digest comes directly from `q5_grid_paths.json.input_sha256`:

```text
expected: 14d52ea7deace7000e167618e95976a534ed4c7e5877c99cc50fbf259815f46a
actual:   fedef6787d0490f1be1739c83e93596fe90bf67e8981b26e381d0ff90f6384fe
```

Normalizing CRLF to LF does not change the actual digest of this file. The other
three historical Q5 input digests match: Q4 paths, C-6 index and Q5 builder.
There is no override flag or relaxed hash comparison.

### Uncapped joint path versus capped joint prefix

A focused cell-level technical check, independently of the historical-manifest
preflight, rejects `sys0024_ic1_s0.01_r0_n1`. Its first differing joint state is
step 14: the uncapped reference selects equation sizes `[7, 5]`; Q5 selects
`[6, 6]`. This is a support-list difference before coefficient comparison.
The capped new implementation reproduces the original path and its log exactly.

The mechanical cause is visible in the frozen algorithm: an equation at six
terms remains eligible in the uncapped reference and competes for the next
joint forward step. Q5 excludes it at that point. Removing the cap therefore
does not in general preserve the capped *joint* candidate prefix.

The same strict cell-level reference control also rejects
`sys0063_ic1_s0.01_r0_n1` and `sys0052_ic1_s0.01_r0_n1`;
it passes for `sys0001_ic1_s0.01_r0_n1`. These are control outcomes, not
scientific classifications. The test suite explicitly verifies that the actual
2D divergence raises. A change to the frozen requirement or algorithm needs
resolution outside this implementation; no prefix was filtered or reconstructed
to make the control pass.

### Process environment

`ProcessPoolExecutor` creation fails in this managed Windows session at
`multiprocessing.Pipe`, with `PermissionError: [WinError 5] Access is denied`.
The process test is skipped only for that exact environment error. Production
does not suppress the exception. The default serial runner does not use pipes.

## Implementation details

`estimate_noise_variance` uses the actual increasing times, centered/scaled cubic
coordinates and an SVD least-squares projection on nine points. The endpoint
windows are the first/last nine observations. Each component's squared residual
is divided by its own `1-h_ii`; a prefix sum forms the truncated centered
21-point mean. No observation-noise model is assumed.

`weak_noise_operators` follows the unchanged weak design's row order for windows
1, 2, 4, 8 and 16. `D` is the sparse endpoint-incidence matrix and `W` contains
the actual-time trapezoid weights. For the primary floor,
`L = D diag(sqrt(variance_j))`. For the secondary floor the component blocks are
`L_j = (delta_j,e D - W diag(df/dx_j)) diag(sqrt(variance_j))`.
Both floors evaluate `||L||_F^2 - ||L' U_S||_F^2`, where `U_S` spans the selected
normalized design columns. Shared endpoints and endpoint/integral cross terms
are therefore retained. No dense row covariance or dense row projector is built
in production. Dense matrices are used only for the small independent floor test.

`basis_jacobian` differentiates every Phase-C basis term analytically:

- Constant: zero.
- Monomial: `power_j * product(x_k ** (power_k - delta_k,j))` for positive
  `power_j`, otherwise zero; there is no division by a state value.
- `sin(x_j)`: `cos(x_j)` in component j.
- `cos(x_j)`: `-sin(x_j)` in component j.

Every term in dimensions 1 through 4 is checked against centered finite
differences, including a state equal to zero. Secondary derivatives are weighted
by the current support's coefficients from the existing `weak_coefficients`.

`growth_path_with_end` retains the frozen forward gains, global equation tie
rules, backward cost calculations and FoBa threshold. Only stopping and repeated
state handling change. `cap=6` is a test hook; the runner never supplies a cap.
Numerical zero retains the strict normalized `< 1e-14` comparison. An attempted
repeat is discarded; the preceding joint state is retained. Stops are reevaluated
after cross-equation removals, as with the original cap logic. An equation still
eligible when the joint path cycles receives `cycle`; equations already satisfying
their own stop retain that reason. Per-equation `path_length` counts stored joint
states, including states with an unchanged support for that equation;
`states_beyond_6` uses that same stored-state convention.

The runner writes one Q5-schema `cells` payload for each end condition, with the
existing `candidate` function generating candidate IDs, equation data, weak
coefficients, `p0`, sizes and weak BIC. Q6 adds `end_condition` and
`equation_paths`; Q5-only upper candidates are empty because they are outside Q6.
Outputs are written incrementally, with a bounded batch of process results and
deterministic input order. `technical.json` is written only after successful
completion; interrupted output directories are incomplete and cannot be reused.
Elapsed time is excluded from deterministic artifacts.

Scientific tables are enabled only for the full run. Smoke mode neither loads
truth nor constructs classification/recall/estimator-quality fields. Full-run
quantile output uses every empirical order statistic per condition, without
selecting additional probability constants. Ratios at zero true noise are
undefined and omitted from the empirical distribution, with an empty marker
when the group has no defined ratios. This scientific branch has been statically
reviewed, but not executed in this task.

## Field audit against actual files

The fixture foundation is the real `q5_grid_paths.json` cell/manifest and its
embedded C-6 export row; no hypothetical result-record schema is used.

| Fields | Origin |
|---|---|
| `cell_id`, `unit_id`, `system_id`, `initial_condition_set`, `dim`, `stratum`, `sigma`, `rho`, `realization`, `n_observed_points` | Existing Q5 cell fields |
| `observed_data_sha256`, `export`, `candidates`, `upper_candidates`, `path_end`, `ended_at_cap` | Existing Q5 cell fields; Q6 replaces the candidate/end values |
| Candidate `candidate_id`, `active_idxs`, `equations`, `p0`, `k`, `weak_bic`, `step`, `origin` | Existing Q5 candidate schema/function |
| Export `noise_sigma`, `subsample_rho`, `noise_realization`, `dimension`, shapes, layout, paths and SHA-256 fields | Existing actual C-6 export row; existing reader validates raw bytes |
| Truth support | Existing `studies/regression/phase_c_support.json`, exact systems' `support_idxs`, 1-based |
| `end_condition`, `equation_paths`, `rule`, `equation_index`, `end_reason`, `path_length`, `states_beyond_6` | New Q6 analysis fields |
| `classification`, `extra_terms_at_end`, `extra_terms_first_truth`, `first_truth_step`, `true_term_recall_at_end` | New full-run analysis fields, not evaluated in smoke |
| `hash_control`, `reference_prefix_control`, `primary_clean_identity` | New per-cell control fields; clean identity deviation is recorded, not raised |
| `point_index`, `time`, `estimated_sigma` | New full-run estimator analysis fields from observed times and estimated variance |
| `true_sigma` | Full-run analysis: Q5 `sigma` times absolute clean exported state at exactly matched observed times; no simulation/interpolation |
| Quantile `metric`, `quantile`, `value`, `n_points` | Full-run empirical distributions of estimated/true standard deviations, difference and defined ratio |

The orchestration test uses a separately written, visibly modified fixture under
`outputs/sideproject_q6_paths/tests/`: its historical Q5 protocol digest is replaced
with the current digest *only in that fixture*, and selection is limited to two
actual 1D noisy cells. This exercises JSON/CSV writing and serial determinism.
It is not a valid real-manifest smoke, and is not presented as one. Actual Q5
inputs are untouched.

## Validation

Final focused command (PowerShell, repository root):

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python -m pytest analysis/tests/test_sideproject_q6.py analysis/tests/test_sideproject_q4.py::test_correlated_decoy_added_then_removed analysis/tests/test_sideproject_q4.py::test_cross_equation_normalisation analysis/tests/test_sideproject_q4.py::test_cap_and_determinism analysis/tests/test_sideproject_q5.py::test_irregular_grid_and_determinism analysis/tests/test_sideproject_q5.py::test_all_clean_paths_are_q4_bit_identical -q --tb=short -rs -p no:cacheprovider --disable-warnings
```

Final result: **23 passed, 1 skipped**, 25.03 seconds. The skip is the process-pipe
environment failure described above. The deprecation warnings originate from
the unchanged weak design's `np.trapz`. Both new Python files also pass AST parsing.

Coverage includes synthetic heteroscedastic estimator calibration and cubic/edge
behavior; both floors against Monte Carlo and explicit covariance/projector
calculations; shared endpoints; rank-deficient/zero columns; every basis
derivative; zero/full/floor stops; a deliberately nonstationary fit inducing a
cycle; exact path/log/candidate reproduction on eight actual Q5 cells spanning
all four strata and zero/noisy sigma; real cell determinism; raw observation
identity rejection; historical hash rejection; actual reference-prefix rejection;
streamed output determinism and the existing Q4/Q5 path controls.

An earlier command selected the complete Q4/Q5 test modules too broadly, including
out-of-scope aggregation and manifest tests. Those exposed existing historical
hash differences, a manifest parallelism assertion and sandbox temp-directory
errors. They were not repaired or used as the focused acceptance result.

## Smoke and count projection

Selection is deterministic: five real cells per stratum (dimensions 1, 2,
3_feasible, 4), including sigma zero/noisy and both rho conditions. The intended
smoke is 20 cells, 60 paths and 150 equation rows per run; repeating it would
build 120 paths. The full projection is **1,632 cells, 4,896 paths and 8,364
equation rows**. Candidate-state/fit costs are not projected from a failed smoke.

Two real-manifest attempts, with output names `smoke_a` and `smoke_b`, both failed
at the same preflight hash. Wall-clock context: 4.51 and 4.01 seconds respectively.
No successful 20-cell output exists and bit-identical successful smoke artifacts
cannot be claimed. Independent cell-level and modified-fixture determinism tests
do not satisfy that missing acceptance point.

Reproduction commands for Claude (no bypass; expected to remain blocked until
the provenance and reference-prefix requirements are resolved):

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
# Short technical test, without truth or estimator-quality evaluation:
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --limit 1 --workers 1 --output outputs/sideproject_q6_paths/short_check
# Required smoke, then repeat to a separate output directory:
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --workers 1 --output outputs/sideproject_q6_paths/smoke_a
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --workers 1 --output outputs/sideproject_q6_paths/smoke_b
# Exact full-run command; not executed by Codex:
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --workers 1 --output outputs/sideproject_q6_paths/grid
```

The full run emits `q6_primary_paths.json`, `q6_secondary_paths.json`,
`q6_reference_paths.json`, `equations.csv`, `controls.csv`,
`estimator_points.csv`, `estimator_quantiles.csv` and `technical.json`.
Smoke omits both estimator tables and the scientific equation fields.
There is no built-in timeout and no parameter that relaxes a control.

Remaining acceptance: resolve the two substantive control conflicts, then run
the unchanged real-manifest smoke twice and verify identical output bytes.
Process validation additionally requires an environment permitting Windows pipes.

## WP-FA7b

The two amended controls are implemented. Acceptance remains **blocked** by a
different real-data growth-path exception and one recorded clean-identity
deviation. The original WP-FA7 findings above describe the superseded controls;
this section records the current implementation and validation.

### Changes

- Every cell first builds a fourth path with `growth_path_with_end(..., cap=6)`.
  Its complete candidate objects, including weak coefficients and signed zeros,
  must match the actual Q5 candidates through exact canonical JSON bytes.
  Mismatch raises `Q5 identity control failed` with the cell ID. The control
  path is discarded; only its per-cell Boolean `q5_identity_control` is emitted
  in `controls.csv`. It has no path file, equation rows or classification.
- The invalid reference-prefix check is removed. The real
  `sys0024_ic1_s0.01_r0_n1` test now verifies that the uncapped reference differs
  from Q5 without raising, while the capped identity control passes.
- The Q5 protocol digest is computed from the raw stdout bytes of exactly
  `git show f454a32:docs/sideproject_residual_growth_protocol_q5.md`.
  Its SHA-256 is
  `14d52ea7deace7000e167618e95976a534ed4c7e5877c99cc50fbf259815f46a`,
  matching the unchanged real manifest. All three other input digests match
  using the existing file-hashing function. No normalization, fallback or
  comparison relaxation was added. The working protocol file is untouched.
- The writer tests now use the unchanged real manifest; they no longer replace
  its historical protocol digest in a fixture. New rejection tests cover a
  modified real candidate coefficient and a corrupted historical digest.
- `technical.json`, when a run completes, includes technical candidate-state
  and control-path counts. Existing growth exceptions now identify the cell
  and rule without changing the algorithm or its stop conditions.

Field provenance: `q5_identity_control` replaces the superseded
`reference_prefix_control` analysis field. Its reference is the existing
`q5_grid_paths.json.cells[].candidates`, not an invented fixture schema.
`candidate_states` and `control_paths` are new technical runner counts. No new
fields are required from Q5 records.

### Focused tests

Final command, from the repository root:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python -m pytest analysis/tests/test_sideproject_q6.py analysis/tests/test_sideproject_q4.py::test_correlated_decoy_added_then_removed analysis/tests/test_sideproject_q4.py::test_cross_equation_normalisation analysis/tests/test_sideproject_q4.py::test_cap_and_determinism analysis/tests/test_sideproject_q5.py::test_irregular_grid_and_determinism analysis/tests/test_sideproject_q5.py::test_all_clean_paths_are_q4_bit_identical -q --tb=short -rs -p no:cacheprovider --disable-warnings
```

Result: **25 passed, 1 skipped**, 21.59 seconds; log:
`codex/reports/WP_FA7b_pytest.log`. The cap identity test now checks **all 20
actual smoke cells**, comparing paths, logs and candidate objects with the
unchanged original algorithm/Q5 records. All 20 capped controls pass. The skip
remains the exact Windows `multiprocessing.Pipe` access-denied error for the
two-worker writer test; serial writer determinism passes. Both changed Python
files also pass AST parsing.

### Real-manifest smoke results

The real-manifest `smoke_a` and `smoke_b` runs used `--workers 1` and were run
serially. Both exit with code 1 at the same cell and rule:

```text
ValueError: sys0063_ic1_s0_r0.5_n1 (primary): No positive gain before protocol stop
```

This is the existing `gain <= 0` rejection in the Q6 growth implementation,
after the digest and capped controls pass for that cell. No extra stop, gain
clamp, changed tolerance, skipped cell or alternate algorithm was introduced.
The three protocol end conditions do not authorize treating this exception as
a successful path end. Resolving it is outside this controls-only amendment.

Each run persists **11 completed cells, 33 scientific paths, 57 equation rows
and 473 candidate states** before the failure. Candidate-state counts across
these completed paths are 133 primary, 122 secondary and 218 reference. All
11 persisted observation-hash and Q5 identity controls pass. The separate
20-cell identity unit test covers the capped controls for the entire smoke
selection, including cells not reached by the failed runner.

The existing clean control also records
`sys0063_ic1_s0_r0_n1: primary_clean_identity=False`; the other two persisted
applicable clean controls are `True`. This deviation is reported as required
by the protocol, without classification or a scientific interpretation.
Consequently, "all controls pass" is not satisfied even apart from the
runtime exception.

All **five partial artifacts** compare byte-identically between the runs:
the three path JSON files, `equations.csv` and `controls.csv`. The partial
JSON files lack their closing document delimiters and both directories lack
`technical.json`; they are incomplete outputs, not successful smoke results.
No successful 20-cell determinism claim is made.

Evidence:

- `outputs/sideproject_q6_paths/validation/smoke_a_FA7b.log`
- `outputs/sideproject_q6_paths/validation/smoke_b_FA7b.log`
- `outputs/sideproject_q6_paths/validation/WP_FA7b_validation.json`
- `outputs/sideproject_q6_paths/smoke_a/` and `smoke_b/` (incomplete)

The validation JSON records file byte lengths, SHA-256 digests and exact byte
comparisons, plus the metadata-derived counts. An initial smoke attempt before
adding cell/rule exception context failed at the same underlying assertion;
its partial outputs were preserved under
`outputs/sideproject_q6_paths/validation/smoke_a_FA7b_initial_failure/`.

### Count projection and commands

The planned smoke remains **20 cells × (3 scientific paths + 1 control)**:
60 scientific paths, 20 control paths and 150 scientific equation rows per
run. The exact full-grid projection from the unchanged manifest is **1,632
cells, 4,896 scientific paths, 1,632 control paths and 8,364 scientific equation
rows**. The Q5 identity control would rebuild exactly **21,250 candidate
states**, counted from the existing manifest. These control states are never
written as paths. The scientific candidate-state projection remains open:
the smoke terminates after only 11 cells, so a complete smoke-based projection
is unavailable. No per-stratum totals of states beyond six terms were computed
or reported.

Commands (failed output directories must be preserved/moved before reuse):

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
# Short technical check:
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --limit 1 --workers 1 --output outputs/sideproject_q6_paths/short_check
# Required serial smoke pair, executed with the unchanged real manifest:
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --workers 1 --output outputs/sideproject_q6_paths/smoke_a
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --workers 1 --output outputs/sideproject_q6_paths/smoke_b
# Exact full-run command; NOT executed:
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --workers 1 --output outputs/sideproject_q6_paths/grid
```

No full run, trajectory fitting, simulation, scientific classification,
end-reason aggregation, recall or estimator-quality evaluation was performed.
Frozen code, inputs, protocols, WP-N48b files and `CURRENT_TASK.md` were not
edited. The only Git command used was the explicitly authorized read-only
historical `git show`; no staging, commit or push occurred. There is no built-in
timeout, and all executions lasted less than 15 minutes. Changes remain
uncommitted. Open acceptance: the runtime failure, clean identity deviation,
successful complete smoke pair and scientific candidate-state projection.

## WP-FA7c

Acceptance is **complete** under Amendment 2. The focused tests pass and both
fresh, serial real-manifest smoke runs complete with identical output bytes.
This section supersedes the open acceptance points in WP-FA7b.

### Implementation and tests

Only `growth_path_with_end` changes: when the best available gain is <= 0,
an uncapped scientific path stops at its current state. Every equation still
eligible receives `no_gain`; equations already satisfying an existing stop
retain that reason. No candidate or forward-step log is appended for the
unsuccessful addition. All three scientific rules share this handling.
When a cap is supplied, the existing exception is retained. The frozen
`growth_path` and the runner's non-raising `primary_clean_identity` recording
are unchanged. The new reason uses the existing Q6 `end_reason` field; no
input-record field or output schema column was added.

Three parametrized synthetic cases (primary, secondary, reference) use actual
`WeakFit` with a zero design column and an unexplained target component.
They check stopping after successful additions, `no_gain` for every remaining
eligible equation, preservation of `sse` and applicable `floor` reasons,
unchanged path/log lengths, and exceptions in both the capped control and
frozen algorithm. The existing real-record test still checks exact paths,
logs and complete Q5 candidate bytes on all 20 smoke cells.

Executed focused command:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python -m pytest analysis/tests/test_sideproject_q6.py analysis/tests/test_sideproject_q4.py::test_correlated_decoy_added_then_removed analysis/tests/test_sideproject_q4.py::test_cross_equation_normalisation analysis/tests/test_sideproject_q4.py::test_cap_and_determinism analysis/tests/test_sideproject_q5.py::test_irregular_grid_and_determinism analysis/tests/test_sideproject_q5.py::test_all_clean_paths_are_q4_bit_identical -q --tb=short -rs -p no:cacheprovider --disable-warnings
```

Result: **28 passed, 1 skipped**, 51.53 seconds, 123,511 warnings; log:
`codex/reports/WP_FA7c_pytest.log`. The skip is the existing managed-Windows
`multiprocessing.Pipe` access-denied condition; serial determinism passes.
Warnings are the unchanged weak design's `np.trapz` deprecation warnings.
Both changed Python files also pass AST parsing.

### Complete smoke pair and controls

Executed in this order, with fresh output directories and the unchanged real
manifest, using the same thread environment as above:

```powershell
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --workers 1 --output outputs/sideproject_q6_paths/smoke_a_FA7c
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --smoke --workers 1 --output outputs/sideproject_q6_paths/smoke_b_FA7c
python outputs/sideproject_q6_paths/validation/validate_FA7c.py
```

Each smoke exits successfully with **20 cells, 60 scientific paths, 20 capped
control paths, 150 equation rows and 4,157 scientific candidate states**.
All 20 observation-hash and Q5 candidate-identity controls pass in each run.
Historical input digests pass the runner's unchanged preflight. All three
path JSON documents parse completely. All **six artifacts** compare byte for
byte: the three path files, `equations.csv`, `controls.csv`, `technical.json`.
Scientific tables remain disabled.

Clean-identity deviations (cell IDs only):

- `sys0063_ic1_s0_r0_n1`
- `sys0052_ic1_s0_r0_n1`

Evidence, under `outputs/sideproject_q6_paths/validation/`:

- `smoke_a_FA7c.log` and `smoke_b_FA7c.log`
- `WP_FA7c_validation.json`: byte lengths, SHA-256 digests, exact comparisons,
  control checks and technical candidate counts
- `validate_FA7c.py`: reproducible technical-only validation

The validation helper's initial invocation used an incorrect Q5 manifest path
and failed with `FileNotFoundError`; after correcting it to the existing
`outputs/sideproject_q5_inputs/q5_grid_paths.json`, it completed successfully.
Neither smoke was rerun or altered for this helper correction.

### Candidate-state projection in counts

Each stratum contributes five smoke cells. Candidate states below count stored
joint scientific states, with no evaluation of truth or end-reason totals.

| Stratum | Full cells | Smoke primary | Smoke secondary | Smoke reference |
|---|---:|---:|---:|---:|
| dim1 | 748 | 24 | 24 | 29 |
| dim2 | 680 | 79 | 68 | 151 |
| dim3_feasible | 136 | 510 | 419 | 674 |
| dim4 | 68 | 341 | 203 | 1,635 |
| Total | 1,632 | 954 | 714 | 2,489 |

Projection: for each rule, sum `(smoke states / 5) * full cells` over strata.
This gives **32,844 primary**, **26,996 secondary**, and **65,443.2 reference**
states: **125,283.2**, or approximately **125,284 scientific candidate states**
rounded upward. The capped controls rebuild exactly **21,250 Q5 candidate
states**, counted from the manifest: approximately **146,534 total candidate
states** including controls. The full grid has **4,896 scientific paths,
1,632 control paths and 8,364 scientific equation rows**. The scientific-state
counts are arithmetic extrapolations from one selected unit per stratum and
five selected conditions, not measured full-grid totals or runtime estimates.

Full-run command, provided for subsequent authorization and **not executed**:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python analysis/scripts/aggregate/build_sideproject_q6_paths.py --workers 1 --output outputs/sideproject_q6_paths/grid
```

No full run, fits, Julia, cluster jobs, scientific classifications, end-reason
counts, recall, R-squared or observed-data estimator-quality evaluation was
performed. No built-in timeout was added; all executions finished within
15 minutes. Frozen code, inputs, protocols, WP-N48b files and `CURRENT_TASK.md`
were untouched. Changes remain uncommitted. At startup, `git status --short`
was inadvertently read before the task's Git restriction had been processed;
subsequent Git calls were only the authorized historical `git show`. No Git
mutation was performed.
