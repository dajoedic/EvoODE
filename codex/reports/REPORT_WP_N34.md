# WP-N34 Report - SINDy and Weak-SINDy on exported noisy Phase-C data

## Implementation

Added `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`.

The script reads `outputs/stage1/data_export/index.csv`, validates the quoted export index, reads each
cell through the referenced little-endian float64 binaries, and recomputes the `time_sha256` and
`state_sha256` hashes before fitting. Training uses the exported noisy/subsampled `(t, x)` bytes.
Evaluation uses clean truth from `benchmarks/data/strogatz_extended.json` on the full clean 512-point
grid: reconstruction from the clean training IC and generalization from the other clean IC.

The ordinary SINDy arm reuses the existing ten `library_grid` configurations unchanged from
`analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py`.

Weak-SINDy uses `pysindy.WeakPDELibrary` with the same function library as the corresponding SINDy
configuration and the same STLSQ optimizer threshold. No interpolation is applied. For the two
irregular-grid cells (`subsample_rho=0.5`), the real observed time vector is passed to PySINDy.

Outputs:

- `outputs/wp_n34_noise_sindy_baselines/details.csv`
- `outputs/wp_n34_noise_sindy_baselines/summary.csv`
- `outputs/wp_n34_noise_sindy_baselines/export_checks.csv`
- `outputs/wp_n34_noise_sindy_baselines/comparison_with_robustness_stage_report.csv`

The comparison table was generated next to the gate-report path. The available
`outputs/wp_n33a_stage_report/robustness_stage_report.csv` in this workspace contains only
`noise_sigma=0`, `subsample_rho=0`, `noise_realization=0` rows, so all 80 comparison rows have
`evogrow_comparison_status=missing_in_stage_report`.

## PySINDy / Weak-SINDy source check

Local version: `pysindy 2.1.0`.

Local source file read:
`C:\Users\joedicke\AppData\Local\Programs\Python\Python312\Lib\site-packages\pysindy\feature_library\weak_pde_library.py`.

The `WeakPDELibrary` signature in this environment is:

```text
(function_library=None, derivative_order=0, spatiotemporal_grid=None, include_bias=False,
 include_interaction=True, K=100, H_xt=None, p=4, num_pts_per_domain=None,
 implicit_terms=False, multiindices=None, differentiation_method=FiniteDifference,
 diff_kwargs={}, is_uniform=None, periodic=None)
```

The source requires `spatiotemporal_grid`. Its documented/source defaults include `K=100`,
`H_xt=L_xt/20` when omitted, `p=4`, `derivative_order=0`, `include_interaction=True`, and default
`function_library=PolynomialLibrary(degree=3, include_bias=False)` when no library is passed. Here
the function library is explicitly the same library used by the paired SINDy configuration. The
source computes weak integral features on sampled subdomains and says the integrated function is
assumed linear between the provided grid points. The four-cell run completed for both regular and
subsampled time grids; no Weak-SINDy cell was converted to interpolation.

## Run

Command:

```text
python analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py --export-index outputs/stage1/data_export/index.csv --output-dir outputs/wp_n34_noise_sindy_baselines
```

Result:

- `details.csv`: 80 rows.
- SINDy: 40 rows, 10 configurations, 40 `fit_status=success`.
- Weak-SINDy: 40 rows, 10 configurations, 40 `fit_status=success`.
- Export checks: 4 rows, all `hash_verified=True`.
- Data conditions: `(0.01, 0.0, 1)`, `(0.01, 0.5, 1)`, `(0.05, 0.0, 1)`, `(0.05, 0.5, 1)`.

PySINDy emitted `AxesWarning: 2 axes labeled for array with 1 axes` during weak-library fitting and
two STLSQ sparsity warnings for high-threshold fits. These warnings did not abort fitting; the
corresponding rows remain reported.

## C-1 reproduction control

The requested control for `(noise_sigma=0, subsample_rho=0)` could not be executed from the provided
WP-N34 input because `outputs/stage1/data_export/index.csv` contains only four noisy System-1,
IC1 rows: `noise_sigma in {0.01, 0.05}`, `subsample_rho in {0.0, 0.5}`,
`noise_realization=1`. No zero-noise/zero-subsample export index for Systems 1 and 24 was present or
provided to the script.

The script exposes `--control-export-index` for a separate zero-noise index, but no such index was
available in this session.

## Tests

Command:

```text
python -m pytest analysis/tests/test_phasec_noise_sindy_baselines.py -q
```

Result:

```text
2 passed, 2 warnings in 2.51s
```

The tests derive fixtures from the real export bytes under `outputs/stage1/data_export`: they copy a
real index row and its referenced binary files into `outputs/wp_n34_pytest`, recompute hashes through
the production reader, and run a minimal SINDy/Weak-SINDy baseline pass on that copied real fixture.

## System 1 table

All rows below are from `outputs/wp_n34_noise_sindy_baselines/details.csv`.

| method | library_id | noise_sigma | subsample_rho | fit_status | reconstruction_status | reconstruction_r2 | generalization_status | generalization_r2 |
|---|---:|---:|---:|---|---|---:|---|---:|
| sindy | poly_deg2_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.99971 | success | 0.999648 |
| weak_sindy | poly_deg2_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.999995 | success | 0.999865 |
| sindy | poly_deg2_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.99971 | success | 0.999648 |
| weak_sindy | poly_deg2_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.999781 | success | 0.99985 |
| sindy | poly_deg3_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.99971 | success | 0.999648 |
| weak_sindy | poly_deg3_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.999987 | success | 0.999984 |
| sindy | poly_deg3_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.99971 | success | 0.999648 |
| weak_sindy | poly_deg3_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.99991 | success | 0.999962 |
| sindy | poly_deg4_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.99971 | success | 0.999648 |
| weak_sindy | poly_deg4_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.999957 | success | 0.999802 |
| sindy | poly_deg4_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.99971 | success | 0.999648 |
| weak_sindy | poly_deg4_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.999768 | success | 0.999906 |
| sindy | poly_deg5_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.99971 | success | 0.999648 |
| weak_sindy | poly_deg5_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.999916 | success | 0.999966 |
| sindy | poly_deg5_stlsq_0.1 | 0.01 | 0.0 | success | success | -0.135473 | success | -18.9384 |
| weak_sindy | poly_deg5_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.999996 | success | 0.999903 |
| sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.999688 | success | 0.993447 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.01 | 0.0 | success | success | 0.999897 | success | 0.99994 |
| sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.01 | 0.0 | success | success | -8.0438 | success | -8.0438 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.01 | 0.0 | success | success | 0.999949 | success | 0.999755 |
| sindy | poly_deg2_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.974739 | success | 0.835081 |
| weak_sindy | poly_deg2_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.999958 | success | 0.99981 |
| sindy | poly_deg2_stlsq_0.1 | 0.01 | 0.5 | success | success | -0.0945894 | success | -19.7694 |
| weak_sindy | poly_deg2_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.999644 | success | 0.997585 |
| sindy | poly_deg3_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.974739 | success | 0.835081 |
| weak_sindy | poly_deg3_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.999991 | success | 0.999857 |
| sindy | poly_deg3_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.99526 | success | 0.992517 |
| weak_sindy | poly_deg3_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.99971 | success | 0.999416 |
| sindy | poly_deg4_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.974739 | success | 0.835081 |
| weak_sindy | poly_deg4_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.999993 | success | 0.999826 |
| sindy | poly_deg4_stlsq_0.1 | 0.01 | 0.5 | success | success | -0.0945894 | success | -19.7694 |
| weak_sindy | poly_deg4_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.999766 | success | 0.999124 |
| sindy | poly_deg5_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.974739 | success | 0.835081 |
| weak_sindy | poly_deg5_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.999519 | success | 0.998761 |
| sindy | poly_deg5_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.99526 | success | 0.992517 |
| weak_sindy | poly_deg5_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.999972 | success | 0.999315 |
| sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.975048 | success | 0.968528 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.01 | 0.5 | success | success | 0.997296 | success | 0.995317 |
| sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.99526 | success | 0.992517 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.01 | 0.5 | success | success | 0.999957 | success | 0.99998 |
| sindy | poly_deg2_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.935563 | success | 0.925684 |
| weak_sindy | poly_deg2_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.999275 | success | 0.995299 |
| sindy | poly_deg2_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.947335 | success | 0.769984 |
| weak_sindy | poly_deg2_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.99939 | success | 0.994596 |
| sindy | poly_deg3_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.935563 | success | 0.925684 |
| weak_sindy | poly_deg3_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.998831 | success | 0.999517 |
| sindy | poly_deg3_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.947335 | success | 0.769984 |
| weak_sindy | poly_deg3_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.999668 | success | 0.999868 |
| sindy | poly_deg4_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.732418 | success | -0.0464683 |
| weak_sindy | poly_deg4_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.990468 | success | 0.595028 |
| sindy | poly_deg4_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.947335 | success | 0.769984 |
| weak_sindy | poly_deg4_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.998204 | success | 0.998661 |
| sindy | poly_deg5_stlsq_0.01 | 0.05 | 0.0 | success | success | -7.77134 | success | -0.634312 |
| weak_sindy | poly_deg5_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.999743 | success | 0.999898 |
| sindy | poly_deg5_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.947335 | success | 0.769984 |
| weak_sindy | poly_deg5_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.999627 | success | 0.99903 |
| sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.05 | 0.0 | success | success | -1.0257 | success | 0.870343 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.05 | 0.0 | success | success | 0.998845 | success | 0.999184 |
| sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.900243 | success | 0.221488 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.05 | 0.0 | success | success | 0.999665 | success | 0.993494 |
| sindy | poly_deg2_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.521046 | success | -5.30609 |
| weak_sindy | poly_deg2_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.998712 | success | 0.98874 |
| sindy | poly_deg2_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.521046 | success | -5.30609 |
| weak_sindy | poly_deg2_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.99912 | success | 0.999568 |
| sindy | poly_deg3_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.322181 | success | 0.742726 |
| weak_sindy | poly_deg3_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.997652 | success | 0.997291 |
| sindy | poly_deg3_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.521046 | success | -5.30609 |
| weak_sindy | poly_deg3_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.998951 | success | 0.985422 |
| sindy | poly_deg4_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.836528 | diverged | -9.39719e+46 |
| weak_sindy | poly_deg4_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.993712 | success | 0.811864 |
| sindy | poly_deg4_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.521046 | success | -5.30609 |
| weak_sindy | poly_deg4_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.995892 | success | 0.998262 |
| sindy | poly_deg5_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.836528 | diverged | -9.39719e+46 |
| weak_sindy | poly_deg5_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.999199 | success | 0.995508 |
| sindy | poly_deg5_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.521046 | success | -5.30609 |
| weak_sindy | poly_deg5_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.997898 | success | 0.996414 |
| sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.771371 | success | 0.955265 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.01 | 0.05 | 0.5 | success | success | 0.989138 | success | 0.997013 |
| sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.771371 | success | 0.955265 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.1 | 0.05 | 0.5 | success | success | 0.984797 | success | 0.513657 |
