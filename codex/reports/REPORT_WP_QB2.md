# WP-QB2 — WeakIdent adapter, controls and cost probe

2026-11-08. **Blocked: a reference-algorithm RNG setting is missing from the
frozen settings.** Implementation and independent checks are provided; control
acceptance is incomplete. No seed was selected, no shared packages were changed,
and no further fits were run after the failed determinism control was diagnosed.

## Blocking evidence and required decision

Noise injection is off, but that does not make the authors' algorithm
deterministic. `model.py:401,416` calls `compute_cross_validation_err_v2`, which
repeatedly calls `compute_cross_validation_error`; `utils/calculations.py:290`
uses `np.random.permutation(n)`. No initialization is supplied by the adapter.
This is part of the reference cross-validation, not the example-data corruption.

In the three prescribed dim-1–3 control cells, disabling the B2b extension gave
**0 differing fields out of 198** (66 per cell, timing omitted). A second native
fit differed on **14 fields in the dimension-2 cell**, while the other two cells
had 0 differences. Only field names/counts are retained, not quality values.
Arm labels (`method`, `method_config_id`) are normalized for the disabled-arm
comparison; the actual dictionary id and all remaining fields are compared.
The control artifacts are `outputs/sideproject_qb2_checks/controls.json`.

The task explicitly says to stop for a needed setting outside its fixed list.
A declared RNG initialization policy is needed before deterministic controls can
be accepted. A selected fixed seed, its scope per cell/arm, and its recording in
the environment/rows must be resolved by the protocol owner. The adapter does
not replace random cross-validation with another algorithm. The successful fit
count does not override this failed acceptance criterion.

## Files and implementation

- `baselines/run_weakident_c6.py`: native and trig adapters, unchanged B1 evaluator
  reuse, input validation, bounded probe, resumable indexed shard entry point.
- `baselines/tests/test_run_weakident_c6.py`: 8 tests, using real Q9/export and
  W1-interp records as fixture sources.
- `baselines/requirements-qb2-weakident.txt`: existing baseline pins plus
  `numpy-indexed==0.3.7`.
- `baselines/Dockerfile.qb2-weakident` and its Docker ignore file.
- `k8s/sideproject_qb2_weakident_job.yaml`: prepared indexed Job, 240 completions,
  at most 8 one-core pods, no deadline, image placeholder. Not built or applied.
- `baselines/third_party/weakident/PROVENANCE.md`: new requested extension heading.
  No reference implementation source was edited.

The single marked `build_dictionary` function adds the trig weak columns using
the reference's actual FFT test function, convolution and sample indices. ODE
scales remain a copy of W. The dynamic region uses the native dictionary; native
narrow-fit, trimming, maximum sparsity and cross-validation are called unchanged.
No example-data loading or noise injection is used. The adapter isolates the
authors' absolute `utils` imports from the project's own package without editing
their code, and imports the vendored numpy-indexed package via `sys.path`.

The full row is constructed by
`run_phasec_noise_sindy_baselines.run_one_model`, with only its fit function
replaced for the call. This reuses DOP853, clean training/other ICs on the 512-point
evaluation grid, coefficient serialization, pruning, support and R² scoring.
Methods are `weakident_native` / `weakident_trig`; library ids start with
`qb2_weakident_v1_poly3_` and cannot collide with B1 or WP-N47 ids. STLSQ threshold
is blank; tau is a separate WeakIdent field.

Dimension 4 is never fitted; its 136 rows per arm have the distinct status
`not supported by the reference implementation`, empty structure scores and
empty R² decisions. Dimensions 1–3 contain 4,148 cells. Non-exact systems and
exact native-arm systems with trig true terms also have a distinct
`structure_status` and blank structure metrics, not false misses.

## Field provenance and data checks

Field names were checked against existing files before constructing fixtures:

| Fields | Actual source |
| --- | --- |
| `system_id`, `initial_condition_set`, `dimension`, `noise_sigma`, `subsample_rho`, `noise_realization` | C-6 `index.csv` and real Q9 `cells[].export` |
| `time_sha256`, `state_sha256`, `data_condition_fingerprint`, `n_observed_points` | Same export records; verified by `select_q9` against `q9_paths.json` |
| `observed_data_sha256` | Q9 embedded serialized time/state hashes; the B1 row uses `data_sha(export_row)` |
| `cell_dir`, `time_path`, `state_path`, shapes, dtype, byte order and axis metadata | Existing C-6 index; B1 `read_index_cell` recomputes actual-byte hashes |
| `cell_key`, `input_file`, `time_sha256`, `state_sha256`, `q5w_interpolated_sha256`, `q5w_interpolation_points`, `q5w_interpolation_dt` | Existing W1-interp manifest, selecting `library=L-C6`; states/times loaded from its `.mat` files |
| `phasec_representability` and other support metadata | Existing `load_phase_c_support` analysis output, not new record fields |
| WP-N47 fit, integration, coefficient and score fields | Existing B1 `run_one_model` result |
| `structure_status`, `weakident_tau`, `weakident_max_dt`, `weakident_source_commit` | New adapter metadata |

Every probe cell passed actual observed-byte hash validation and the Q9/export
checks. Every probe cell has rho=0.5 and also passed both per-array interpolation
hashes and the combined little-endian float64 C-order time+state
`q5w_interpolated_sha256`. No interpolation was performed. The stored probe
inputs have 256 points; their exported resolution was preserved. The 512-point
grid applies to clean evaluation, not an additional input re-interpolation.

The exhaustive mapping test checks 4, 10, 20 and 35 polynomial multi-indices for
dimensions 1–4, respectively, plus 2, 4, 6 and 8 trig terms. It verifies numerical
evaluation by the existing B1 feature compiler. For dimensions 1–3, the
multi-indices are also compared with the actual reference dictionary. Dimension
4 mapping is checked mathematically without extending the unsupported builder.
The extension test checks unchanged native columns/region and trig weak values
against direct circular convolution, independently of the FFT implementation.

## Authors' gate (accepted upstream; not rerun)

As recorded in protocol amendment 2: noise-free Lotka–Volterra exact; with the
authors' 10% noise, 16 of 20 draws exact and 4 with one wrong or missing term;
2D linear example exact. These are Claude's recorded gate results, not new
measurements from this session. The gate was not rerun.

## Cost probe — planning context only

The final complete probe command was `python baselines/run_weakident_c6.py probe`.
It exited nonzero because of the determinism control. A preceding `--limit 1`
smoke passed; the table and projection below come only from the final complete
probe's `cost.json` / `projection.json`, not that smoke.

Cells: first exact system per dimension, systems 1, 24, 52; IC 1, sigma=0.05,
rho=0.5, realization 1. One BLAS thread, Python 3.12.10, NumPy 2.2.6,
SciPy 1.13.1, pandas 2.2.2, pySINDy 2.1.0, sklearn 1.5.1, SymPy 1.13.1,
threadpoolctl 3.5.0, vendored numpy-indexed 0.3.7. Per-arm fingerprints are in
`outputs/sideproject_qb2_checks/environment_0.json`.

| Dimension / system | Native fit s | Native fit+eval s | Trig fit s | Trig fit+eval s |
| --- | ---: | ---: | ---: | ---: |
| 1 / 1 | 0.0264704 | 0.0337948 | 0.0523495 | 0.0614324 |
| 2 / 24 | 0.2312296 | 0.2945459 | 0.1460602 | 0.2000769 |
| 3 / 52 | 0.2572889 | 0.2678019 | 0.6135629 | 0.6329394 |

**0 fit failures in 6 timed fits**. Identity/repeat controls require additional
fits on these same three cells and are not included in the cost projection.
No benchmark-cell quality values are printed or reported.

Using the amended mix 1:1,564, 2:1,904, 3:680 and summing
`cell_wall_s × dimension_count / 3600` gives:

- Native: **0.22104882 core-h**.
- Trig: **0.25206263 core-h**.
- Combined: **0.47311145 core-h**, approximately **28.39 minutes** on one core.
- Remaining dimension-4 count: **136 unsupported cells**, not fitted or assigned
  miss scores, not extrapolated as supported jobs.

The measured fit+evaluation projection is below one laptop hour for both arms
together. It excludes startup, shared input loading/hash checks, clean truth
integration, output I/O and unsupported-row overhead. One cell per dimension is
only planning context; RNG policy is unresolved and can affect search cost.
This is not a guarantee of total end-to-end completion within an hour.

## Tests and preparation checks

1. `python -m pytest baselines/tests/test_run_weakident_c6.py -q`: **8 passed**,
   7.99 s. Reference NumPy scalar-conversion deprecations and a pytest-cache
   permission warning; no test failure.
2. `python -m pytest baselines/tests analysis/tests/test_phasec_noise_sindy_baselines.py analysis/tests/test_phasec_sindy_baseline.py analysis/tests/test_qb1_wisp_library.py -q -p no:cacheprovider`:
   **123 passed, 5 skipped, 22 setup errors**, 66.30 s. Every setup error was
   `PermissionError [WinError 5]` accessing pytest temporary directories.
3. A retry of the two affected test files with a fresh `--basetemp` under
   `outputs/sideproject_qb2_checks/` also failed on directory access and pytest
   cleanup. Therefore those existing checks cannot be claimed green here.
4. `python -m pytest baselines/tests analysis/tests/test_phasec_noise_sindy_baselines.py -q -p no:cacheprovider --tb=short`:
   **112 passed, 5 skipped**, 43.90 s, 28 warnings. This includes the eight new
   tests and confirms the existing baseline test directory and noise-evaluator
   tests pass together.
5. Adapter AST and Job YAML parsed successfully; Indexed mode, parallelism <=8
   and absence of a Job deadline were checked. Docker image and cluster execution
   remain untested, as requested. The shard retry path was reviewed statically;
   it skips existing per-method cell keys and writes per-shard CSVs.

Final changes after the probe only improve field comparison for NaN/signed-zero
representations and shard restart handling; fitting, extension and evaluation
behavior were not changed after the recorded probe. No further benchmark fits
were attempted after diagnosing the random cross-validation.

## Handoff

Resolve and declare the RNG policy, then rerun the controls before deployment:

```text
python baselines/run_weakident_c6.py probe --limit 1
python baselines/run_weakident_c6.py probe
```

Also rerun the two existing analysis test files in an environment where pytest
can create and access temporary directories. No full-run command is authorized
by this task. No Git commands, commit, staging, push, cluster action or build
were performed. All deliverable changes remain in the working tree.
