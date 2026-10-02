# WP-N39 - PySR as GP Baseline

Status: frozen pre-run decisions for C-7. No PySR result from this work package is used as evidence.

## Sources

ODEFormer's local checkout is `outputs/third_party/odeformer` at commit `c9193012ad07a97186290b98d8290d1a177f4609`.

The direct model source is `outputs/third_party/odeformer/odeformer/baselines/pysr_wrapper.py`.
Its wrapper constructs `PySRRegressor` with `finite_difference_order=2`, `smoother_window_length=None`, `niterations=50`, default binary operators `plus, sub, mult, pow, div`, default unary operators `cos, exp, sin, neg, log, sqrt`, squared loss, `procs=1`, and `equation_file=pysr_hof.csv` (`pysr_wrapper.py:23-55`). It fits ODE derivatives: for one trajectory it calls `super().fit(X=trajectories, y=self.approximate_derivative(...).squeeze(), variable_names=x_i)` (`pysr_wrapper.py:90-115`). It selects equations by reading the hall of fame, sorting by `score` descending, and taking the first candidate per dimension/product combination (`pysr_wrapper.py:117-140`).

ODEFormer's script enables `pysr` and `pysr_poly` as baseline models (`scripts/run_baselines.py:101-115`, `scripts/run_baselines.py:198-205`). It passes `optimize_hyperparams=True`, `hyper_opt_eval_fraction`, and `sorting_metric` to the PySR wrapper (`scripts/run_baselines.py:101-115`), with defaults `hyper_opt_eval_fraction=0.3` and `sorting_metric=r2` (`scripts/run_baselines.py:213-223`). Its shell grid runs `pysr` and `pysr_poly` over subsample ratios `0.0, 0.25, 0.5` and additive noise gammas `0.0, 0.001, 0.01, 0.02, 0.03, 0.04, 0.05` (`scripts/run_baselines.sh:7-43`). It evaluates through ODEFormer's evaluator (`scripts/run_baselines.py:172-176`) and records standard validation metrics including R2 (`scripts/run_baselines.py:245-290`).

PySR documents its Julia backend as `SymbolicRegression.jl`, accessed through `juliacall`, and states that the backend version associated with a PySR checkout is in `pysr/juliapkg.json`: https://pysr.ai/v2.4.0/backend.

## Two PySR APIs

WP-N39 now has two pinned Docker variants:

| Variant | Image tag in report commands | Python package | PySR API | Backend source |
|---|---:|---:|---|---|
| current | `evoode-pysr:wp-n39` | `pysr==1.5.9`, `juliacall==0.9.24` | `v1` | PySR `v1.5.9` `pysr/juliapkg.json`: Julia `=1.10.0, 1.10.3`, SymbolicRegression.jl `~1.11.0` |
| legacy | `evoode-pysr-legacy:wp-n39` | `pysr==0.19.4`, `juliacall==0.9.24` | `legacy_0x` | PySR `v0.19.4` `pysr/juliapkg.json`: Julia `~1.6.7, ~1.7, ~1.8, ~1.9, =1.10.0, ~1.10.3`, SymbolicRegression.jl `=0.24.5` |

Version basis:

- PyPI lists `0.19.4` as the last 0.x release before `1.0.0` and gives its release date as 2024-08-23: https://pypi.org/project/pysr/0.19.4/
- PySR `v0.19.4` `PySRRegressor.__init__` accepts `equation_file` (`pysr/sr.py:699-788`): https://raw.githubusercontent.com/MilesCranmer/PySR/v0.19.4/pysr/sr.py
- PySR `v1.0.0` release notes list the breaking rename `equation_file -> output_directory + run_id`: https://github.com/astroautomata/PySR/discussions/755
- PySR `v1.5.9` API documents `output_directory` and `run_id` as the result-export controls: https://pysr.ai/v1.5.9/api/

The adapter detects the installed PySR version. For `legacy_0x`, it passes the ODEFormer wrapper arguments unchanged, including `equation_file`. For `v1`, it renames only the non-algorithmic result-location argument: `equation_file` becomes `output_directory` plus `run_id`. Every record carries `pysr_api` and `pysr_api_renamed_arguments`.

The Docker images set `EVOODE_PYSR_API_LABEL`, so a default run writes to separate output roots:

- v1: `outputs/wp_n39_noise_pysr_pysr_v1`
- legacy: `outputs/wp_n39_noise_pysr_pysr_legacy_0x`

Explicit `--output-dir` values override this default separation.

## Default Differences

The table below lists `PySRRegressor` parameters not explicitly set by ODEFormer's wrapper and whose defaults differ between PySR 0.19.4 and 1.5.9. Source: `PySRRegressor.__init__` defaults in PySR `v0.19.4` (`pysr/sr.py:699-788`) and `v1.5.9` (`pysr/sr.py:796-897`). These defaults are not aligned; each image runs with its own package defaults unless ODEFormer's wrapper already sets the parameter.

| Parameter | PySR 0.19.4 default | PySR 1.5.9 default |
|---|---:|---:|
| `populations` | `15` | `31` |
| `population_size` | `33` | `27` |
| `maxsize` | `20` | `30` |
| `complexity_of_constants` | `1` | `None` |
| `parsimony` | `0.0032` | `0.0` |
| `adaptive_parsimony_scaling` | `20.0` | `1040.0` |
| `alpha` | `0.1` | `3.17` |
| `ncycles_per_iteration` | `550` | `380` |
| `fraction_replaced` | `0.000364` | `0.00036` |
| `fraction_replaced_hof` | `0.035` | `0.0614` |
| `weight_add_node` | `0.79` | `2.47` |
| `weight_insert_node` | `5.1` | `0.0112` |
| `weight_delete_node` | `1.7` | `0.870` |
| `weight_do_nothing` | `0.21` | `0.273` |
| `weight_mutate_constant` | `0.048` | `0.0346` |
| `weight_mutate_operator` | `0.47` | `0.293` |
| `weight_swap_operands` | `0.1` | `0.198` |
| `weight_rotate_tree` | absent | `4.26` |
| `weight_randomize` | `0.00023` | `0.000502` |
| `weight_simplify` | `0.0020` | `0.00209` |
| `crossover_probability` | `0.066` | `0.0259` |
| `should_simplify` | `None` | `True` |
| `optimizer_f_calls_limit` | absent | `None` |
| `perturbation_factor` | `0.076` | `0.129` |
| `probability_negate_constant` | absent | `0.00743` |
| `tournament_selection_n` | `10` | `15` |
| `tournament_selection_p` | `0.86` | `0.982` |
| `parallelism` | absent | `None` |
| `autodiff_backend` | absent | `None` |
| `logger_spec` | absent | `None` |
| `input_stream` | absent | `"stdin"` |
| `run_id` | absent | `None` |
| `output_directory` | absent | `None` |
| `loss_function_expression` | absent | `None` |
| `loss_scale` | absent | `"log"` |
| `complexity_mapping` | absent | `None` |
| `expression_spec` | absent | `None` |

## Frozen Decisions

### A.1 Target and Derivatives

PySR fits derivative targets estimated from the observed trajectory, not the trajectory directly. This follows ODEFormer's wrapper (`pysr_wrapper.py:107-112`). In this repository the helper is `pysr_finite_difference_targets`, which validates at least three strictly increasing time points and computes second-order `np.gradient` targets (`baselines/harness.py:648-658`).

Irregular grids are accepted without interpolation if the time vector is strictly increasing, because `np.gradient(y, time_values, edge_order=2)` handles nonuniform spacing. A non-increasing grid is a cell error, not repaired.

### A.2 Operators

The frozen operator set is ODEFormer's set:

- binary: `plus, sub, mult, pow, div`
- unary: `cos, exp, sin, neg, log, sqrt`

This is implemented in `pysr_default_config` (`baselines/harness.py`) and traces to ODEFormer's wrapper defaults (`pysr_wrapper.py:38-48`). The set is larger than the canonical EvoODE basis. The canonical basis requires `1, u_i, u_i^2, u_i*u_j, u_i^3, sin(u_i), cos(u_i)`, all expressible by constants, variables, multiplication, powers, sine, and cosine. Extra operators (`div`, `exp`, `log`, `sqrt`, `neg`) stay because the source harness uses them; expressions using them are counted as outside-basis terms during structure scoring rather than treated as harness failures.

ODEFormer also runs `pysr_poly`, which uses the same binary operators and an empty unary set (`scripts/run_baselines.py:101-115`). The EvoODE runner therefore writes both `method=pysr` and `method=pysr_poly` rows for every cell and seed. They are reported side by side; neither variant is selected based on outcomes.

### A.3 Budget

The per-trajectory search budget is ODEFormer's `niterations=50` with no `maxsize` limit and no fixed wall-clock timeout (`pysr_wrapper.py:23-48`). The harness records `pysr_niterations`, operator sets, `pysr_maxsize`, `pysr_candidates_evaluated`, derivative target shape, selected hyperparameters, and elapsed seconds as context, not evidence.

ODEFormer enables hyperparameter optimization by default for its PySR baseline (`scripts/run_baselines.py:101-115`). The faithful EvoODE run therefore uses `optimize_hyperparams=true`, `hyper_opt_eval_fraction=0.3`, and `sorting_metric=r2`, matching `scripts/run_baselines.py:213-223`. The hyperparameter grid is the wrapper grid from `pysr_wrapper.py:64-68`: `finite_difference_order in {2,3,4}` crossed with `smoother_window_length in {None,15}`. Selection is performed only on the held-out fraction of the observed training trajectory; clean reconstruction and clean generalization targets are evaluated after fitting and are not visible to the hyperparameter choice. The selected pair per equation is serialized in `pysr_selected_hyperparams`.

Discarded 2026-10-02: the previous WP-N39 freeze set `optimize_hyperparams=false`, `finite_difference_order=2`, and `smoother_window_length=null` to avoid choosing after seeing outcomes. This was rejected because ODEFormer's own harness makes the hyperparameter search part of the method and scores it on held-out training data, not on this paper's clean targets or reported outcomes.

### A.4 Seeds

PySR runs with ODEFormer's wrapper arguments, including `procs=1`, and does not receive PySR-specific `random_state`, `deterministic`, `parallelism`, `warm_start`, or `precision` arguments. This is deliberate: the two PySR versions are compared through the ODEFormer wrapper surface, with only the non-algorithmic output-location rename applied for PySR 1.x. The runner still records `pysr_seed` and `pysr_realization` as grid/repetition labels and uses the seed in output paths, but PySR's own RNG default is the package default in each image.

### A.5 Versions and Environment

PySR is isolated in two Dockerfiles; it is not installed into the existing baseline image. The current-API pinned requirements are in `baselines/requirements-pysr.txt`:

- `pysr==1.5.9`
- `juliacall==0.9.24`
- Python numerical stack pinned with NumPy, pandas, SciPy, SymPy, scikit-learn, and PySINDy

The legacy pinned requirements are in `baselines/requirements-pysr-legacy.txt`:

- `pysr==0.19.4`
- `juliacall==0.9.24`
- the same Python numerical stack pins as the current image

The Julia search backend is pinned transitively by each PySR package: PySR's `juliapkg.json` declares the compatible `SymbolicRegression.jl` backend. The images must not update PySR independently of their requirements files.

Both Dockerfiles set `JULIA_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, and `OMP_NUM_THREADS=1` to keep the cell budget single-core. The images are built by Claude or the user, not by this package.

### A.6 Canonical Expansion

The found SymPy expression is expanded by the shared external-baseline path in `baselines/harness.py`: `canonicalize_pysr_expression` expands each equation, and `symbolic_active_terms_by_equation` maps terms onto the canonical basis while returning outside-basis terms (`baselines/harness.py:697-787`). This is the same canonical expansion used for ODEFormer after WP-N38; PySR does not get a second expansion.

Outside-basis terms are serialized as `pysr_outside_basis_terms` and counted in `pysr_outside_basis_term_count`. A structure hit requires zero outside-basis terms and exact support equality.

## Harness

The runner is `baselines/run_pysr_noise.py`. It reuses `read_export_index`, `read_index_cell`, and `data_sha` from the WP-N34 noise export path, so exported byte hashes, shape checks, axis-order checks, and duplicate-key validation are shared rather than copied.

Outputs are written under the selected output directory:

- `details.csv`
- `records.jsonl`
- `summary.csv`
- `export_checks.csv`
- `comparison_with_external_baselines.csv`

The fit uses the observed noisy/subsampled trajectory. Reconstruction and generalization metrics are then computed on clean 512-point trajectories: reconstruction from the clean training IC, generalization from the other clean IC. Divergence or nonfinite integration is recorded as status fields and NaN R2, not repaired.

The generic `baselines/harness.py` runner now recognizes method `"pysr"` and delegates to the real adapter if PySR is importable.

## Cost Estimate

Cell definition for the full grid: `63 systems x 12 conditions x 3 noise realizations x 2 IC sets = 4,536 cells`.

Dim 1/2 subset from `benchmarks/data/strogatz_extended.json`: `23 dim-1 systems + 28 dim-2 systems = 51 systems`, so `51 x 12 x 3 x 2 = 3,672 cells`.

PySR is fit once per equation. The equation-fit count is:

`(23*1 + 28*2 + 10*3 + 2*4) systems/equations x 12 x 3 x 2 = 8,424 equation fits`.

Each reported row now runs ODEFormer's 6-point hyperparameter grid. ODEFormer has two PySR variants, `pysr` and `pysr_poly`, so the budget factor is `6 hyper-fits x 2 configurations = 12` per equation.

With budget `50 iterations/equation/hyper-fit`, the full grid has `8,424 x 6 x 2 x 50 = 5,054,400 PySR equation-iterations`. The dim 1/2 subset has `(23*1 + 28*2) x 12 x 3 x 2 x 6 x 2 x 50 = 3,412,800 equation-iterations`.

Let `T_cell` be the smoke-measured seconds per full cell at one core. Then:

- full grid core-hours: `4,536 * T_cell / 3,600 = 1.26 * T_cell`
- full grid cost at 1.50 EUR/core-hour: `1.89 * T_cell` EUR
- dim 1/2 core-hours: `3,672 * T_cell / 3,600 = 1.02 * T_cell`
- dim 1/2 cost at 1.50 EUR/core-hour: `1.53 * T_cell` EUR

Here `T_cell` is the smoke-measured seconds for one complete cell including both variants and all hyper-fits. Equivalently, with `T_eq` as seconds per single equation hyper-fit, full-grid core-hours are `8,424 * 6 * 2 * T_eq / 3,600 = 28.08 * T_eq`, cost `42.12 * T_eq` EUR. The uncertainty is entirely the unmeasured PySR runtime per cell/equation; Claude fills `T_cell` from the smoke. This is not a time-limit upper bound because the frozen budget is iteration-count based, not wall-clock based.
