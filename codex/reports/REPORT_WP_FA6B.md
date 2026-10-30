# WP-FA6b ? revised Q5-W acceptance and MATLAB identity infrastructure

Status: **done** (infrastructure scope). Frozen protocol section 5 points 1(i), 2, 3 and 4 pass; point 1(ii) is reported only. `matlab_identity_passed` is **null**: MATLAB is not installed and was not run. This does not establish identity with the original or unseal the results.

## Acceptance and preserved evidence

`outputs/sideproject_q5w_wsindy/acceptance/summary.json` contains explicit `acceptance_points`: 1(i)=true, 1(ii)=reported_only, 2=true, 3=true, 4=true; `pre_smoke_passed=true`. The gate no longer uses a noisy Lorenz threshold; the full-run entry point additionally requires the complete, error-free deterministic smoke verdict. MATLAB identity is separate and does not gate execution.

`--stage complete-pre` reads the preserved 21 Lorenz records and the prior evaluation-identity evidence; no Lorenz fit or evaluation was rerun. It recomputes the library mapping checks. The preserved Lorenz file SHA-256 is `05edb1a9b263e420fc252990c4bfca4a41be70316b663e6d024d5261d4d6c45c`. No write path to that file was used in this WP. The clean Lorenz relative E_inf is 5.105757086961863e-13, below 1e-4.

Point 3 uses the protocol's explicit ?or names the exception? branch: 100 previously checked cells, 36 fully bit-identical, 64 with named exceptions (228 differing fields). The preserved `acceptance/evaluation_identity.json` identifies every cell, field, actual and stored value; the previous report `codex/reports/REPORT_WP_FA6.md` documents these exceptions. Acceptance here is not a claim of bit identity on all 100 cells. No evaluation metrics were recomputed or printed in this WP. The evidence-file records must have cell keys and difference lists for this exception branch to pass.

Point 1(ii), preserved evidence in full (no gate; coefficients and loss grids remain in `acceptance/lorenz.jsonl`):

| Seed | Exact support | E_inf | E2 | Selected lambda by equation |
|---|---|---|---|---|
| clean | True | 5.1057570869618631e-13 | 5.2813171085455123e-13 | 0.0001, 0.0001, 0.0001 |
| 0 | True | 0.027735209139470536 | 0.027363887375741934 | 0.02009233002565048, 0.012618568830660211, 0.024201282647943835 |
| 1 | False | 0.023583062790270986 | 0.02253274438590681 | 0.013848863713938732, 0.024201282647943835, 0.0045348785081285817 |
| 2 | False | 0.0069594128759388673 | 0.0096132929984171899 | 0.012618568830660211, 0.0079248289835391773, 0.010476157527896652 |
| 3 | False | 0.030967813723542674 | 0.028018793524845629 | 0.013848863713938732, 0.011497569953977368, 0.011497569953977368 |
| 4 | False | 0.2165757213322467 | 0.19537016723535475 | 0.015199110829529346, 0.0059948425031894088, 0.012618568830660211 |
| 5 | True | 0.0356487489711661 | 0.032659361262727275 | 0.011497569953977368, 0.012618568830660211, 0.022051307399030457 |
| 6 | False | 0.090850049308798767 | 0.085836428789132849 | 0.0054622772176843425, 0.0095454845666183476, 0.029150530628251788 |
| 7 | True | 0.0336891612415769 | 0.031227134435080493 | 0.016681005372000592, 0.010476157527896652, 0.0086974900261778346 |
| 8 | True | 0.014607880520495569 | 0.013777620664399184 | 0.015199110829529346, 0.0054622772176843425, 0.046415888336127822 |
| 9 | True | 0.019555929280286044 | 0.018030482456220565 | 0.011497569953977368, 0.018307382802953697, 0.026560877829466867 |
| 10 | False | 0.031983811164756633 | 0.03126102109327808 | 0.0079248289835391773, 0.007220809018385471, 0.015199110829529346 |
| 11 | False | 0.021688396764033842 | 0.020536474673643459 | 0.015199110829529346, 0.006579332246575682, 0.024201282647943835 |
| 12 | True | 0.031998202249655501 | 0.029735585530562936 | 0.029150530628251788, 0.015199110829529346, 0.013848863713938732 |
| 13 | False | 0.067432169879854661 | 0.07523324011906192 | 0.007220809018385471, 0.007220809018385471, 0.0079248289835391773 |
| 14 | False | 0.03572757161970945 | 0.033634901221765004 | 0.010476157527896652, 0.0049770235643321137, 0.022051307399030457 |
| 15 | False | 0.045583721258725063 | 0.042956482048921829 | 0.016681005372000592, 0.011497569953977368, 0.029150530628251788 |
| 16 | False | 0.010837548265819714 | 0.01371815088674602 | 0.012618568830660211, 0.007220809018385471, 0.016681005372000592 |
| 17 | False | 0.033389516672006687 | 0.036053753734721639 | 0.0079248289835391773, 0.018307382802953697, 0.0028480358684358021 |
| 18 | False | 0.040724488836920002 | 0.038141809344337661 | 0.0095454845666183476, 0.010476157527896652, 0.0095454845666183476 |
| 19 | False | 0.030920330186222363 | 0.041496825573892726 | 0.006579332246575682, 0.0054622772176843425, 0.0095454845666183476 |

## Authorized smoke and cost

Two separate runs completed on the same 20 clean surrogate cells, six configurations each: **120 rows per run, 240 persisted rows total, 0 fit errors, deterministic=true**. Equality excludes only elapsed-time fields and includes coefficients, loss grids, selected indices, counters and hashes. Coverage checks require all 120 cell/configuration pairs. Per-row observed-data hashes were checked against WP-N47 before fitting. The smoke uses `technical_only=True`: no evaluator, clean-trajectory integration or structure/R2 computation. These smoke CSVs contain technical metadata and coefficients only.

One run requested **368,640 sample-column library evaluations** and **9,084 least-squares solves**. Full-run work is **4,536 x 6 = 27,216 fits**; multiplying smoke counts by **226.8** projects **83,607,552 library evaluations** and **2,060,251.2 solve requests** (an estimate, hence fractional). Measured fit/row durations project **2,528.8079114468296 seconds = 42.1468 minutes**. Both smoke runs together took **53.49225830001524 seconds** including setup and reference loading; naive extrapolation of half this entire wall time is **6,066.022091221728 seconds = 101.1004 minutes**, which repeatedly charges setup. Timing is context, not an acceptance criterion or a guaranteed <1h full run. The 20-cell surrogate subset does not represent all dimensions/conditions. No full run was started; Claude must apply section 7's cost rule.

Artifacts: `smoke/details.csv`, `determinism_repeat/details.csv`, `acceptance/smoke_cells.csv`, all beneath `outputs/sideproject_q5w_wsindy/`.

## Exact library binding

Both libraries are expressible **yes**. Pass `polys=[]`, `trigs=[]`, `custom_fcns={}` and all desired columns as `custom_tags`. Real exponent rows specify monomials; a single -i entry specifies sine, +i cosine. This uses the original tag inputs without custom numerical functions and preserves the original monomial scaling. L-Q5 includes only its specified cubes and pair products, without unwanted mixed cubics. The original sorts/deduplicates tags; the driver establishes a unique fixed permutation from returned tags back to exported port order, and also writes the original order.

Reading `get_tags.m`, `build_theta.m` and `build_poly_lib.m` established these input semantics. In the actual `wsindy_ode_fun` path, `get_tags` plus `custom_tags` and row uniqueness determines columns; `build_poly_lib` is not called. No reference implementation text was copied.

The extended point-2 mapping test checks names/order against existing canonical builders and independently evaluates explicit tags numerically. It passes for dimensions 1?4, including randomized signed probes in focused tests. Counts (L-C6/L-Q5) are 6/6, 14/12, 26/19, 43/27. Numerical tolerance is 1e-14 relative and absolute. This proves the tag representation numerically in Python under the inspected original semantics; actual execution of the original remains part of pending MATLAB identity.

## MATLAB inputs and driver

`analysis/scripts/aggregate/export_sideproject_q5w_matlab.py` exported **21 Lorenz data sets + 2,268 distinct C-6 rho=0 cells**. The C-6 cells each have both L-C6 and L-Q5 inputs: **4,557 task MAT files and 4,557 per-task JSON manifests**, plus `manifest.json`, under `outputs/sideproject_q5w_wsindy/matlab_inputs/`. The libraries reuse identical observed arrays per physical cell. C-6 arrays come directly through the existing lossless export reader/hash validator. Lorenz arrays are regenerated with the exact existing solve_ivp call and NumPy PCG64 noise construction, without running WSINDy or overwriting its preserved records. MATLAB receives these same binary doubles, rather than independently solving Lorenz or generating noise. Every MAT file was read back and checked with exact array equality during export.

Each manifest records the existing five-part cell key (or Lorenz seed), library, column names, time/state SHA-256 and binary filename. Hashes are SHA-256 over little-endian float64 in C order, matching existing export hashes. The MAT file carries observed `tobs`, `xobs` and the explicit complex `requested_tags`. No fit was performed on a noisy C-6 cell.

`analysis/matlab/run_wsindy_original_q5w.m` adds the unmodified reference folder to the path and calls its entry point. All active settings were checked against frozen section 3, not inherited on trust from the Octave example: phi_class=1, max_d=1, tau=1e-16, tauhat=-1, K_frac=1, overlap_frac=1, relax_AG=0, scale_Theta=2, useGLS=0, 100 lambdas from 1e-4 to 1, gamma=0, alpha_loss=.8, smoothing_window=ceil(M/100). run_sindy=0 disables the separate SINDy path. Adaptive-placement arguments (.8, [1;0], [1;0]) and useFD=2 are inactive under relax_AG=0/run_sindy=0. Empty truth weights avoid injecting truth. The driver uses base MATLAB functions only; original dependencies are called unchanged.

The original loss output's first row is the loss curve and second row its lambda grid. MATLAB `min` selects the first minimizer, as the original does; the driver derives its **zero-based** selected grid index as MATLAB index minus one, verifies the returned grid value, and serializes lambda and original-scale coefficients with `%.17g`. Original returned coefficients already have the correct physical scale; no second rescaling is applied. Returned original tags (real/imaginary parts), permutation, support indices and column names are written per cell. Temporary files are moved into place on successful completion. Resume skips completed JSON files only after checking manifest hashes/library, and a limit supports a short first check.

Commands for Claude, from the repository root, once MATLAB is installed (NOT executed here):

```powershell
matlab -batch "addpath('analysis/matlab'); run_wsindy_original_q5w(pwd, 2)"
matlab -batch "addpath('analysis/matlab'); run_wsindy_original_q5w(pwd)"
```

The second command resumes completed cells. Use the short MATLAB check to assess runtime before applying section 7's <1h/discussion rule; Python timing is not a MATLAB runtime estimate.

## Port fields and sealed identity comparison

`wsindy_reference.py` changes output fields only: each equation now includes `lambda_grid_index` (zero-based), `lambda_grid_index_base=0`, `support_indices` (zero-based column positions) and `coefficients_original_scale`. Existing fields and algorithm are retained. WP-FA6 rows had lambda values/grid and full coefficients at row level, but no explicit selected index or equation-level coefficient/support payload. Legacy Lorenz records are adapted only in memory: their lambda value must match exactly one entry of their stored grid. They remain untouched.

`analysis/scripts/aggregate/compare_sideproject_q5w_matlab.py` reads the 4,557-task manifest, MATLAB JSON outputs, preserved Lorenz rows and W1 rows from the future full CSV. It checks manifest hashes/library/column order; per equation it requires equal nonzero support and grid index, finite coefficient vectors of identical shape, and max|port-original| <= 1e-6 max|original|. A zero reference vector therefore has zero coefficient tolerance. It writes `matlab_identity/verdicts.json` and `matlab_identity/summary.json` with cells, passed count and failing cells/first differing equation. Missing inputs cannot pass. It prints identity verdicts only. `acceptance/summary.json` receives the separate MATLAB verdict: null with no MATLAB output, false for incomplete/failing comparisons, true only if every expected task passes. No unsealing mechanism or scientific aggregation was run.

After MATLAB and the authorized port full run, Claude runs:

```powershell
python analysis/scripts/aggregate/compare_sideproject_q5w_matlab.py --port-rows outputs/sideproject_q5w_wsindy/full/details.csv
```

## Validation and file boundary

Executed:

```text
python analysis/scripts/aggregate/accept_sideproject_q5w_wsindy.py --stage complete-pre
python analysis/scripts/aggregate/accept_sideproject_q5w_wsindy.py --stage smoke
python analysis/scripts/aggregate/export_sideproject_q5w_matlab.py
python -m pytest analysis/tests/test_sideproject_q5w_wsindy.py analysis/tests/test_sideproject_q5w_matlab.py -q -p no:cacheprovider
python -m py_compile analysis/scripts/aggregate/wsindy_reference.py analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py analysis/scripts/aggregate/accept_sideproject_q5w_wsindy.py analysis/scripts/aggregate/export_sideproject_q5w_matlab.py analysis/scripts/aggregate/compare_sideproject_q5w_matlab.py analysis/tests/test_sideproject_q5w_matlab.py
```

Final focused tests: **22 passed, 2 existing pysindy AxesWarnings, 4.61 seconds**. Tests include identical and deliberately perturbed real-record-derived fixtures, tolerance/zero coefficients, original-scale output fields, binary hash/roundtrip identity, both libraries/dimensions, revised gate independence, and complete comparison CLI execution on an identical fixture followed by a changed index. Synthetic MATLAB fixtures derive their equation schema from the actual preserved clean Lorenz row; the deliberately altered index/coefficient/support is explicit. They are test fixtures, not claimed MATLAB output. An initial pytest tmp_path setup failed on Windows sandbox permissions (including a workspace basetemp attempt); the binary export fixture now uses its own output subfolder, and the final command above passed.

`complete-pre` was repeated after final gate changes, preserving the completed smoke and nullable MATLAB verdict. The actual MATLAB driver was statically checked against all input/output shapes and the reference entry point; it is unexecuted as required. MATLAB runtime validation remains Claude's next step, not an unmet infrastructure acceptance requirement.

New repository files: export script, comparison script, `analysis/matlab/run_wsindy_original_q5w.m`, `analysis/tests/test_sideproject_q5w_matlab.py`, this report. Modified: acceptance script, runner (technical-only smoke option), reference output metadata, STATUS. No Git operations, staging, commits, cluster work, Octave/MATLAB execution, noisy C-6 fitting, full run, scientific C-6 aggregation, frozen-file edits or WP-N48b edits. All work remains uncommitted.
