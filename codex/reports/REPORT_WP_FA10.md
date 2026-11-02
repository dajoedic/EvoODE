# WP-FA10 — MATLAB-sourced Q5-W rows and solver diagnosis

Status: **blocked**. Implementation and focused tests are complete, but the required two complete row files are not. Each production evaluation process reached its built-in **840-second** boundary and terminated its local workers. In accordance with CODEX_PROTOCOL.md, evaluation was stopped rather than continued in further batches. The preserved files contain **1,980/4,536 W1 rows** and **1,920/4,536 W1-interp rows**. Actual MATLAB G/b matrices were not present in the supplied artifacts; the numerical diagnosis below uses explicitly labelled reconstructions. Five solver identity cases remain unresolved. These are open acceptance items, not waived criteria.

No scientific WSINDy rate, structure rate, or Q5/Q7 comparison was calculated or reported. No production aggregator was executed. Original MATLAB inputs/outputs, identity verdicts, existing port row files, the external reference, wsindy_reference.py, the production MATLAB driver, frozen protocols, Q5/Q7 output tables and WP-N48b files were not edited. No MATLAB, Julia, cluster, Git, staging, commit or push operation was performed.

## Row production and provenance

`analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py` reads the preserved original coefficients and calls **the same `runner.evaluate(StoredModel(...))` function as the port runner**. That function delegates to the existing WP-N47 `baseline.run_one_model` with DOP853. Truth integration, reconstruction/generalization, pruning, support fields, coefficient serialization and all other evaluator fields are reused. The existing evaluator's raw/pruned naming behavior is preserved, as already documented in FA6. The original observations, rather than interpolated evaluation data, reach this evaluator for W1-interp as well.

New artifacts are under `outputs/sideproject_q5w_wsindy/`:

- `full_matlab/details.csv` and `full_matlab/controls.json`;
- `w1_interp_full_matlab/details.csv` and `w1_interp_full_matlab/controls.json`;
- `solver_diagnosis/diagnosis.json` and `solver_diagnosis/summary.json`;
- bounded check/test folders and local `evaluation_workers/` files inside the respective output folder.

Both row files retain all top-level columns of their corresponding port CSV and add provenance. They remain **untrusted/incomplete**, with `complete: false` in both controls. Each successful row is flushed independently. A subsequent invocation validates persisted equation coefficients and input/observed hashes before resuming. `--controls-only` validates saved rows without simulating missing tasks. Workers use local JSON files because `ProcessPoolExecutor` failed with `PermissionError: [WinError 5] Access is denied` while creating a Windows named pipe. The file-worker implementation was exercised against serial evaluation on a small real-record fixture.

Field provenance was checked against a real C-6 manifest entry, its actual MATLAB JSON, the actual export index, and the actual port CSV header/record before constructing fixtures:

| Fields | Origin |
|---|---|
| Five cell keys, observed point count, fingerprint, original time/state hashes | Existing C-6 export record through the existing reader/hash validator |
| `observed_data_sha256` | Existing `baseline.data_sha`, checked against WP-N47 and the port row |
| `q5w_input_time_sha256`, `q5w_input_state_sha256` | New row fields carrying the manifest hashes of the arrays actually supplied to MATLAB |
| `q5w_coefficient_source` | New field: `matlab_original_72d8d6e`; port runner/newly loaded legacy port rows use `port` |
| `q5w_matlab_cell_id` | New field carrying the manifest's existing `cell_id` |
| `q5w_equations` | Existing JSON column; actual MATLAB coefficients, support indices, selected lambda/index and index base |
| `q5w_interpolation_points`, `q5w_interpolation_dt`, `q5w_interpolated_sha256` | Existing interpolation-manifest fields, preserved for W1-interp |
| R2, integration status, raw/pruned support and structure fields, truth, serialized coefficients | Existing shared evaluator, with only the coefficient source changed |
| `source_shard`, source note, configuration labels | Existing columns with explicit original-source values |
| `q5w_cost_note` | New declaration of unavailable original cost counts/timing |

Original-observation hashes remain in the existing `time_sha256`/`state_sha256` columns. On W1-interp they deliberately differ from the newly named MATLAB input hashes. The distinction is explicit.

`q5w_library_evaluations`, `q5w_least_squares_solves`, `fit_elapsed_s_context` and `q5w_elapsed_s_context` are empty for MATLAB rows. No port cost was borrowed or estimated. The original JSONs do not export per-lambda losses, full grid term counts, smoothing/support parameters or solve counts: these are not fabricated inside `q5w_equations`. All available original equation fields are retained. The port runner now writes its own coefficient source and actual fit-input hashes for new rows; appending new provenance columns to a legacy CSV is explicitly refused before fitting, requiring a fresh output directory.

## Controls and remaining coverage

Both **complete manifests** passed the bijection and hash check: **4,557 tasks** for W1 including 21 Lorenz tasks, and **4,536 tasks** for W1-interp. Every manifest task has exactly one JSON output in the corresponding directory. Output identity, library, column order, cell key, binary filename, hashes, interpolation metadata, coefficient dimensions/finiteness, support indices, zero-based lambda index and lambda value were checked. Every binary MAT input was independently hashed and matched its manifest. Lorenz has no C-6 evaluator row; its 21 input/output provenance checks are included in the first count.

The final controls-only commands were run after both production evaluations had stopped:

| Technical control | W1 | W1-interp |
|---|---:|---:|
| Expected C-6 rows | 4,536 | 4,536 |
| Persisted unique C-6 rows | 1,980 | 1,920 |
| Persisted rows with passing coefficient-identity verdict, rechecked | 1,974 | 1,920 |
| Such rows with named evaluation exceptions | 1,689 | 1,766 |
| Maximum absolute R2 delta, including per-dimension R2 | 0.0392407919280231 | 0.00007417549591082206 |

These are **partial coverage controls**, not acceptance on the missing tasks. All exceptions are named by task and field in the respective `controls.json`, including actual/stored values, deltas, coefficient delta and an explanation. The saved identity verdict is independently recomputed before evaluation-field comparison.

Within the checked passing-identity rows there are no support-list, structure-boolean, integration-status or R2-threshold-boolean exceptions. Numeric precision/recall/F1 exceptions have maximum absolute delta **8.326672684688674e-17**. The corresponding support sets are identical, so these are floating-point metric representation/arithmetic discrepancies rather than changed support.

The nonidentical coefficients permitted by the identity criterion are one possible source of R2 changes through integration; a causal explanation for each amplified discrepancy has not been established. There are also **78 W1** and **65 W1-interp** exception tasks whose coefficients are bit-identical: their maximum absolute R2 delta is **1.7763568394002505e-15** in each arm. Their residual execution/serialization discrepancy is explicitly marked as unlocalized. No claim of universal bit identity is made.

## Downstream selection

The consumer search found `aggregate_sideproject_q7.py` and `aggregate_sideproject_q8.py`; Q8 delegates the WSINDy table path to Q7. Both now use the shared `q5w_row_sources.py` and expose:

- `--wsindy-source matlab` (default): substitute original-backed W1/rho=0 and W1-interp/rho=.5 rows;
- `--wsindy-source port`: reproduce the previous coefficient source;
- `--wsindy-matlab-input PATH ...`: override the default `full_matlab/details.csv` and `w1_interp_full_matlab/details.csv` paths.

The supplied port files remain the source for W1 on the native irregular grid, W1-cap and W2. Replacement rows must be unique, use the original coefficient-source label, have matching observed-data hashes and have complete row controls. **The current partial production files are refused.** Source checking occurs before scientific table calculations. Missing MATLAB costs propagate as unavailable instead of becoming zero; source provenance is recorded in comparison rows and run metadata. Legacy mode retains its original numeric costs and scientific inputs.

## Offline diagnosis

`analysis/scripts/aggregate/diagnose_sideproject_q5w_lstsq.py` ran on **all 198 failing W1 tasks**, **all 141 failing W1-interp tasks**, and **28 deterministic passing tasks per arm**, spread over manifest order. No scientific evaluator or truth integration is called by this experiment.

The preserved original JSONs contain coefficients and tags, not G/b. Two matrix constructions were therefore compared: the production port's design and an independently reconstructed original-order design using normalize-before-powers and the original's factorized test polynomial arithmetic. Corner/smoothing helpers are reused. Full-design and original-selected-support condition numbers and numerical ranks are saved per equation, with the selected original lambda index. The design exists before lambda selection; the selected-support submatrix is the lambda-dependent diagnostic.

Four solver/construction choices were fixed for this experiment. The QR candidate uses a pivoted-QR basic solution with `tol=max(m,n)*eps*abs(R11)`. This is **not certified as MATLAB's internal tolerance or a bit-equivalent MATLAB emulator**. The experiment temporarily replaces the imported least-squares callable only inside its standalone process; wsindy_reference.py is unchanged.

| Identity group | Tasks | Rank-deficient reconstructed full design in at least one equation | Port + gelsy identity | Port + QR basic identity | Reconstructed original order + gelsy identity | Reconstructed original order + QR basic identity |
|---|---:|---:|---:|---:|---:|---:|
| W1 failing | 198 | 197 | 0 | 193 | 1 | 194 |
| W1 passing sample | 28 | 1 | 28 | 28 | 28 | 28 |
| W1-interp failing | 141 | 140 | 0 | 139 | 1 | 140 |
| W1-interp passing sample | 28 | 0 | 28 | 28 | 28 | 28 |

These are **coefficient/support/lambda identity counts**, not scientific structure outcomes. For failing tasks, full-design condition numbers range from **3.248536798173466e11 to 4.425412742465927e18** for W1, and **1.2226394225778787e12 to 8.362095657800548e18** for W1-interp. Passing samples span **895.7222853928828 to 3.636989450485738e14** and **89.27628332836878 to 1.976993301442043e13**, respectively. Maximum port/reconstruction matrix and target absolute differences are **8.881784197001252e-16** and **9.592326932761353e-14**. Such small arithmetic differences cannot be assumed harmless at these condition numbers.

Inference: the principal observed mechanism is the choice of least-squares representative/rank handling on near-dependent libraries. Replacing only the port solver reproduces **193/198** and **139/141** failed identity cases; changing construction/order alone with gelsy reproduces only one failed case per arm. LAPACK documents DGELSY as returning a minimum-norm solution through complete orthogonal factorization; MATLAB documents QR/basic-solution behavior for deficient rectangular least-squares problems. [LAPACK DGELSY](https://www.netlib.org/lapack/explore-html/d6/d4b/dgelsy_8f_source.html), [MathWorks least-squares chapter](https://www.mathworks.com/content/dam/mathworks/mathworks-dot-com/moler/leastsquares.pdf). MATLAB's documented QR rank test uses diagonal magnitudes of R; that documentation does not establish the candidate's tolerance as the original backslash tolerance. [MathWorks decomposition](https://www.mathworks.com/help/matlab/ref/decomposition.html).

Five cases still fail under reconstructed-original-order QR:

- `c6_62_1_0_0_1_L-Q5`, `c6_62_1_0_0_2_L-Q5`, `c6_62_1_0_0_3_L-Q5`: equation 3, zero-based, selected lambda index differs; that full design has SVD rank **20/27**, condition **6.177522591798169e16**; the original-selected-support submatrix condition is **8.239637926793234**.
- `c6_63_2_0.02_0_2_L-C6`: equation 2, support differs; full rank **43/43**, full-design condition **3.0589816726438384e12** at that equation; the original selected support is empty.
- `c6_interp_52_2_0.04_0.5_2_L-Q5`: equation 2, selected lambda index differs; full rank **19/19**, condition **2.1214020875436057e12**, selected-support condition **35.77649511223073**.

Their remaining causes have not been established. Raw experimental coefficients and lambda indices for every scenario, the identity verdicts and every equation's matrix diagnostics are saved in `diagnosis.json` for audit.

`analysis/matlab/export_wsindy_q5w_designs.m` is a separate, **unexecuted** exporter for these 395 diagnostic tasks. It calls the unchanged original with the same argument values as the existing driver and saves actual G/b, scaling, mapping, coefficients, input hashes and lambda indices under `matlab_designs/`. It does not edit the production driver. The Python experiment accepts `--original-design-dir`, verifies hashes and coefficient identity against preserved MATLAB outputs, then records diagnostics and solver experiments on those actual matrices. Static inspection checked all 16 requested original return positions, MAT field shapes, column mapping and zero-based equation/index handling. Runtime validation of this MATLAB exporter is still open.

## Reproduction and tests

Commands are from the repository root. Short evaluated checks (fresh folders), followed by the production commands that were attempted; the latter resume the persisted rows but still enforce the 840-second boundary:

```powershell
python analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py --limit 2 --workers 2 --output-dir outputs/sideproject_q5w_wsindy/matlab_row_check_claude
python analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py --interpolated --limit 2 --workers 2 --output-dir outputs/sideproject_q5w_wsindy/matlab_interp_row_check_claude
python analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py --workers 4
python analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py --interpolated --workers 4
python analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py --controls-only
python analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py --interpolated --controls-only
python analysis/scripts/aggregate/diagnose_sideproject_q5w_lstsq.py
```

The full attempted evaluations were stopped at their boundary; only controls-only commands followed. The initial serial check was interrupted during validation to inspect and improve filesystem concurrency. A short process-pool check failed on Windows named pipes. Neither check was reported as a completed production run.

For Claude to obtain actual original matrices (not executed here):

```powershell
matlab -batch "addpath('analysis/matlab'); export_wsindy_q5w_designs(pwd,2)"
matlab -batch "addpath('analysis/matlab'); export_wsindy_q5w_designs(pwd)"
python analysis/scripts/aggregate/diagnose_sideproject_q5w_lstsq.py --original-design-dir outputs/sideproject_q5w_wsindy/matlab_designs --output-dir outputs/sideproject_q5w_wsindy/solver_diagnosis_actual_matlab
```

Consumer CLI inspection was executed with `--help` for both Q7 and Q8. A future Q7 aggregation command, **only after complete row controls and the separate opening decision**, is:

```powershell
python analysis/scripts/aggregate/aggregate_sideproject_q7.py --q5-input 'outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/index_*.jsonl' --q7-input 'outputs/sideproject_q7_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/index_*.jsonl' --wsindy-input outputs/sideproject_q5w_wsindy/full/details.csv outputs/sideproject_q5w_wsindy/w1_interp_full/details.csv --wsindy-source matlab --output-dir outputs/sideproject_q5w_wsindy/consumer_review/q7_matlab
```

For the old source, change `--wsindy-source matlab` to `--wsindy-source port` and select a separate fresh output folder. Q8 exposes the same source options. Neither aggregation was executed in this WP.

Executed focused validation:

```powershell
python -m pytest analysis/tests/test_sideproject_q5w_original_rows.py analysis/tests/test_sideproject_q5w_wsindy.py analysis/tests/test_sideproject_q5w_matlab.py analysis/tests/test_sideproject_q5w_interp.py analysis/tests/test_sideproject_q7.py::test_wsindy_complete_cells_and_both_libraries analysis/tests/test_sideproject_q8.py::test_wsindy_primary_rho_and_missing_coverage -q -p no:cacheprovider
python -m pytest analysis/tests/test_sideproject_q5w_original_rows.py::test_legacy_port_resume_refuses_schema_mixing_before_fitting -q -p no:cacheprovider
python -m py_compile analysis/scripts/aggregate/evaluate_sideproject_q5w_matlab.py analysis/scripts/aggregate/diagnose_sideproject_q5w_lstsq.py analysis/scripts/aggregate/q5w_row_sources.py analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py analysis/scripts/aggregate/aggregate_sideproject_q7.py analysis/scripts/aggregate/aggregate_sideproject_q8.py analysis/tests/test_sideproject_q5w_original_rows.py analysis/tests/test_sideproject_q5w_interp.py
```

The broad focused invocation completed **43 tests in 81.69 seconds**, with 3 existing pysindy AxesWarnings and 4,996 existing trapz deprecation warnings. Afterward the new legacy-schema guard test completed **1 test in 2.94 seconds**; the 43-test result is not represented as a new 44-test run. Compilation exited 0. Tests derive fixtures from actual original/port/export records; corruptions are explicit. They cover bijection/hash failures, unchanged evaluator inputs, missing-cost behavior, source replacement and legacy mode, missing replacements/incomplete controls, exact preserved old fields plus new port provenance, file-worker/serial agreement, a complete one-task production pipeline, controls-only resume and corrupted resume provenance. No full production run is included in tests.

Acceptance remains open for **2,556 W1 rows**, **2,616 W1-interp rows**, their passing-identity evaluation controls, and diagnosis on actual original G/b with the remaining five cases. All implementation files and partial artifacts remain in the working tree for Claude's review.
