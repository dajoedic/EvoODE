# WP-N45 Report

## Built

- Added `e_sindy` to `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`.
- Added `--methods`, defaulting to `sindy,weak_sindy`; existing commands keep their old method set.
- E-SINDy uses the same `build_library(cfg)`, finite-difference derivative, STLSQ threshold, `alpha=1e-6`, and `normalize_columns=False` as SINDy.
- E-SINDy wraps that STLSQ in `pysindy.EnsembleOptimizer(..., bagging=True)`.
- Added deterministic E-SINDy seeding: SHA-256 over system id, IC set, noise sigma, subsample rho, realization, data-condition fingerprint, and `library_id`; first 8 hex digits are converted to an integer and passed to NumPy's global RNG immediately before the fit.
- Added per-row `ensemble_seed` and JSON `ensemble_optimizer_metadata`.
- Extended `analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py` with Weak-SINDy rows and optional E-SINDy input through `--esindy-details`, `--esindy-shards-dir`, and `--esindy-merged-dir`.
- Added `esindy_status` to hierarchy `metadata.json`; the no-input run records `absent` and does not fabricate rows.
- Added the N43b reference benchmark control row for existing EvoGrow/SINDy/ODEFormer rows.
- Updated `SCRIPTS.md` with the 10-shard E-SINDy command and the hierarchy command including E-SINDy arguments.

## Recorded EnsembleOptimizer Arguments

The runner records these explicit values in `ensemble_optimizer_metadata`:

- `optimizer`: `pysindy.EnsembleOptimizer`
- `bagging`: `true`
- `library_ensemble`: `false`
- `n_models`: `20`
- `n_subset`: `null`
- `n_candidates_to_drop`: `1`
- `replace`: `true`
- `ensemble_aggregator`: `null`
- `ensemble_aggregator_effective`: `median`
- Base optimizer: `pysindy.STLSQ`, `threshold=<configuration threshold>`, `alpha=1e-6`, `normalize_columns=false`
- `seed`: per-row deterministic integer

Only `bagging=True` is passed away from the library default; the other EnsembleOptimizer defaults are recorded, not tuned.

## Smoke

Smoke input: 4 exported cells, all 10 configurations each, 40 E-SINDy rows total.

| system | dim | sigma | rho | realization | rows | success | total fit seconds | mean fit seconds/config |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0.00 | 0.0 | 1 | 10 | 10 | 0.260713 | 0.026071 |
| 1 | 1 | 0.01 | 0.0 | 1 | 10 | 10 | 0.297266 | 0.029727 |
| 24 | 2 | 0.00 | 0.0 | 1 | 10 | 10 | 0.512153 | 0.051215 |
| 24 | 2 | 0.01 | 0.0 | 1 | 10 | 10 | 0.992863 | 0.099286 |

Fit statuses: 40 `success`, 0 failures.

Projection from this smoke: `2.0629953000025107 s / 4 cells * 4536 cells = 2339.4366702028474 s`, i.e. `38.99061117004746 min`. This is capacity context only.

## Hierarchy Check

Command run without E-SINDy input:

```text
python analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py --output-dir outputs/wp_n45_hierarchy_no_esindy --sindy-merged-dir outputs/wp_n45_hierarchy_no_esindy/merged_sindy
```

Resulting `benchmark.csv` method rows:

- Weak-SINDy: 100
- SINDy: 100
- ODEFormer: 80
- EvoGrow: 10

`metadata.json` has `esindy_status: absent`.

Existing-method control:

- `n43b_existing_methods_benchmark_byte_identity`
- `n_checked`: 190
- `expected`: `byte_identical`
- `actual`: `byte_identical`
- `passed`: `true`

## Tests

Command:

```text
python -m pytest analysis/tests -q -k "sindy or hierarchy" --basetemp .pytest_tmp_wp_n45
```

Result: 34 passed, 98 deselected, 10 PySINDy axis warnings.

## Ambiguity

WP-N45 says Weak-SINDy should be processed by the SINDy hierarchy rules including the clean realization-identity check. The real WP-N34 Weak-SINDy clean rows are not realization-identical; the hierarchy therefore keeps Weak-SINDy clean realizations as repetitions rather than collapsing them. Deterministic SINDy still gets the identity check and collapse. E-SINDy is also kept by realization when present because the required seed includes the cell key, including realization.
