# WP-FA6c — W1-interp on the irregular C-6 cells

Status: done. Infrastructure, bounded technical smoke and focused checks are complete. MATLAB/Octave and the full fitting run were not executed. No scientific rates, structure hits, R² values or scientific comparisons were computed by this WP's smoke or reported here.

## Implementation and input boundary

`run_sideproject_q5w_wsindy.py` accepts `W1-interp:L-C6` and `W1-interp:L-Q5` through `--configurations`. `CONFIGS` remains the original six-element tuple. The named function `interpolate_uniform` validates finite states and strictly increasing times, constructs `linspace(t_first, t_last, M)` with M equal to the observed point count, and applies `numpy.interp` independently to each state. There is no extrapolation. Already-uniform grids pass through unchanged, using the same uniformity tolerance as the existing W1 design (rtol=1e-10, atol=1e-14). On a real rho=0 cell both libraries give bit-identical W1/W1-interp coefficient bytes and identical equation metadata.

The helper runs before the unchanged W1 fit. `wsindy_reference.py` is untouched. The evaluator still receives the original observed t/x and the existing clean trajectories. A focused test intercepts that boundary and verifies the original array objects for both new configurations. The smoke sets `technical_only=True`, so it calls neither evaluator nor truth integration. The CLI now selects requested `--cells` from the export index even without `--all-cells`; previously it intersected them with the default clean smoke subset.

Existing-six preservation is checked against the actual prior `outputs/sideproject_q5w_wsindy/smoke/details.csv`: all six technical rows for its first cell match exactly after excluding only elapsed-time columns. The default tuple itself is asserted explicitly. Existing full outputs and the old smoke artifacts are not rewritten.

## Field provenance (checked against actual records)

The real export `outputs/phase_c_c6_data_conditions_5dd1df8/index.csv` supplies all five keys individually: `system_id`, `initial_condition_set`, `noise_sigma`, `subsample_rho`, `noise_realization`. It also supplies `dimension`, `n_observed_points`, `time_sha256`, `state_sha256`, `time_path` and `state_path`. Actual observed arrays are loaded and hash-verified by the existing `baseline.read_index_cell`. The runner checks `observed_data_sha256` against the WP-N47 details rows before each cell's fits; that field is the existing `baseline.data_sha(row)` serialization. Stored details' `source_initial_condition_set` alias remains handled by `key`.

All W1 row construction and `q5w_equations` metadata remain available for W1-interp, including zero-based `lambda_grid_index`, `support_indices`, `coefficients_original_scale`, loss curves and solve counts. Three new analysis fields are emitted only for W1-interp:

| Field | Source |
|---|---|
| `q5w_interpolation_points` | Length of the arrays passed to W1; equals original observed M |
| `q5w_interpolation_dt` | (last-first)/(M-1) on the interpolation grid |
| `q5w_interpolated_sha256` | SHA-256 of time bytes followed by state bytes, both little-endian float64, C order |

MATLAB manifest entries retain the existing per-array `time_sha256` and `state_sha256`, binary `.mat` file name, cell key, library and ordered column names, and add `arm=W1-interp` and the three interpolation fields. Array hashes describe the actual uniform inputs, while the runner's observed-data hash continues to describe the original observations. Fixtures use real export rows or actual preserved Q5-W equation records as their schema foundation; synthetic MATLAB results are explicitly fabricated from those records for tests only.

## Artifacts and bounded smoke

All new execution artifacts are under `outputs/sideproject_q5w_wsindy/`:

- `w1_interp_acceptance/cells_rho05.csv`: **2,268 unique cells**, exactly the five runner keys.
- `w1_interp_acceptance/smoke_cells.csv`: **20 unique rho=0.5 cells**. Dimension 1: 4 sigma=0 and 4 noisy; dimension 2: 3 and 3; dimension 3: 3 and 3. Noisy observations include sigma=0.01 and sigma=0.02. Systems selected by the deterministic index-order sampling are 1, 24 and 52; this is a smoke sample, not a representative cost survey.
- `w1_interp_acceptance/smoke/details.csv` and `repeat/details.csv`: **40 rows each, 80 total, 0 fit errors**. Complete cell/configuration coverage and all fields other than the two elapsed-time fields agree exactly, including hashes, equation JSON, coefficients, indices and counters.
- `w1_interp_acceptance/summary.json`: technical verdict, counts and timing context.
- `matlab_inputs/w1_interp/manifest.json`: **2,268 interpolated cells, 4,536 library-specific tasks**, with losslessly round-tripped `.mat` arrays and per-task JSON sidecars. The original parent manifest is preserved. A post-export check confirms that its unique cell keys equal the complete five-key CSV and that all 40 smoke rows have exactly the same interpolation point counts, dt values and combined array hashes as their MATLAB manifest entries.

One smoke pass requested **133,632 sample-column library evaluations** and **8,366 least-squares solves**. The full arm comprises **2,268 × 2 = 4,536 fits**. Scaling the 20-cell pass by **113.4** projects **15,153,868.8 sample-column evaluations** and **948,704.4 solve requests**. Fractional values are projections, not measured full-run counts. Both smoke passes together took **23.29466620000312 seconds** including setup/reference loading; scaling only measured fitting time projects **166.10404481567676 seconds**. These timings are context only: the smoke excludes evaluation, and the sample covers only three systems, so this is not an estimate of complete evaluated full-run wall time.

The smoke script refuses to reuse existing details files; a repeat invocation must choose a fresh `--output-dir`. This prevents resumed rows from being reported as a newly executed deterministic run.

## MATLAB infrastructure

`export_sideproject_q5w_matlab.py --interpolated` exports only the addendum inputs into the dedicated subfolder and does not rerun Lorenz or rewrite the original export. Both library tag bindings are unchanged.

The driver required a minimal interface extension: it previously hardcoded the parent input/output directories, so it could not access a separate subfolder. `analysis/matlab/run_wsindy_original_q5w.m` now accepts optional third/fourth arguments for those directories; its first two arguments, original defaults, reference call, settings, column permutation and serialization remain unchanged. No external reference code, comments or text were copied.

`compare_sideproject_q5w_matlab.py --interpolated` selects W1-interp rows and the corresponding manifest/output subfolders. It additionally binds the port's interpolated-array hash to the manifest. The equation criterion is unchanged: identical nonzero support and selected grid index, finite matching coefficient shapes, max absolute difference <= 1e-6 times the reference equation's maximum coefficient magnitude. Synthetic fixtures cover identity, a changed selected index and an incorrect interpolation hash; the existing tests cover coefficient/support perturbations and tolerance. The addendum writes its separate `matlab_interp_identity_passed` field, leaving `matlab_identity_passed` unchanged. No real MATLAB verdict is claimed.

## Commands executed and validation

```text
python -m pytest analysis/tests/test_sideproject_q5w_interp.py analysis/tests/test_sideproject_q5w_wsindy.py analysis/tests/test_sideproject_q5w_matlab.py -q -p no:cacheprovider
python analysis/scripts/aggregate/accept_sideproject_q5w_interp.py
python analysis/scripts/aggregate/export_sideproject_q5w_matlab.py --interpolated
python -m py_compile analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py analysis/scripts/aggregate/export_sideproject_q5w_matlab.py analysis/scripts/aggregate/compare_sideproject_q5w_matlab.py analysis/scripts/aggregate/accept_sideproject_q5w_interp.py analysis/tests/test_sideproject_q5w_interp.py
```

Final focused-test result: **34 passed, 3 existing pysindy AxesWarnings in 13.35 seconds**. Compilation completed with exit code 0. Post-export validation confirmed all 4,536 binary input files exist and every JSON sidecar equals its manifest entry; the CSV contains exactly 2,268 unique keys. Only Q5-W tests were run. Tests additionally cover invalid interpolation inputs, actual binary export round trips, interpolation manifest metadata, original evaluation inputs, CLI selection and preservation of the default six rows.

## Commands for Claude (not executed)

Short evaluated check in a separate folder:

```text
python analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py --all-cells --cells outputs/sideproject_q5w_wsindy/w1_interp_acceptance/cells_rho05.csv --limit 2 --configurations W1-interp:L-C6,W1-interp:L-Q5 --output-dir outputs/sideproject_q5w_wsindy/w1_interp_check
```

Exact full-run command (4,536 fits; existing acceptance gates still apply):

```text
python analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py --all-cells --cells outputs/sideproject_q5w_wsindy/w1_interp_acceptance/cells_rho05.csv --configurations W1-interp:L-C6,W1-interp:L-Q5 --output-dir outputs/sideproject_q5w_wsindy/w1_interp_full
```

MATLAB first two tasks, then all tasks (apply the protocol's runtime rule before the latter):

```text
matlab -batch "addpath('analysis/matlab'); run_wsindy_original_q5w(pwd, 2, fullfile(pwd,'outputs','sideproject_q5w_wsindy','matlab_inputs','w1_interp'), fullfile(pwd,'outputs','sideproject_q5w_wsindy','matlab_outputs','w1_interp'))"
matlab -batch "addpath('analysis/matlab'); run_wsindy_original_q5w(pwd, inf, fullfile(pwd,'outputs','sideproject_q5w_wsindy','matlab_inputs','w1_interp'), fullfile(pwd,'outputs','sideproject_q5w_wsindy','matlab_outputs','w1_interp'))"
python analysis/scripts/aggregate/compare_sideproject_q5w_matlab.py --interpolated --port-rows outputs/sideproject_q5w_wsindy/w1_interp_full/details.csv
```

No Git operations, staging, commits, cluster work, full fitting run, MATLAB/Octave execution, frozen Q5 edits, WP-N47 output edits or WP-N48b file edits were performed. Changes remain uncommitted.



