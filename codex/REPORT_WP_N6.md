# WP-N6 Report - SINDy baseline on Phase-B data

## Commands

```text
python -m py_compile analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py
python analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py --config analysis/configs/wp_n6_sindy_error_fixture.json
python analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py --config analysis/configs/wp_n6_sindy_baseline.json
```

The fixture command exits with:

```text
ValueError: benchmark_path does not exist: ...analysis\fixtures\wp_n6_sindy_baseline\missing_strogatz_extended.json
```

## Outputs

- `analysis/data/wp_n6_sindy_baseline/trajectory_check.csv`
- `analysis/data/wp_n6_sindy_baseline/details.csv`
- `analysis/data/wp_n6_sindy_baseline/summary.csv`
- `analysis/data/wp_n6_sindy_baseline/costs.csv`
- `analysis/data/wp_n6_sindy_baseline/evoode_wp_n5_comparison.csv`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_summary.csv`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_summary.tex`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_costs.csv`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_costs.tex`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_trajectory_check.csv`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_trajectory_check.tex`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_evoode_wp_n5_comparison.csv`
- `analysis/tables/wp_n6_sindy_baseline/wp_n6_evoode_wp_n5_comparison.tex`

## Trajectory Check

The script loads all 63 systems from `benchmarks/data/strogatz_extended.json`, both initial
conditions per system, and evaluates 512 points on `t in [0, 10]` including both endpoints. This
matches the Phase-B source protocol in `studies/regression/phase_b_config.jl` and
`studies/regression/run_regression.jl`: same system list, same IC sets, same grid, same substituted
RHS definitions, and self-integration instead of shipped `solutions` values.

No stored EvoODE trajectory arrays were found in `outputs/wp_n5_ic_generalization/`; that directory
contains metrics and model terms, not the raw simulated training trajectories. Therefore the direct
check is against the Phase-B generator inputs and source protocol, not against saved Julia arrays.

The shipped JSON grid matches the Phase-B grid in all 126 system/IC cells:

```text
trajectory rows: 126
grid_matches_phase_b: 126 / 126
self integration status: success in 126 / 126
self_vs_shipped_max_abs: min 1.0e-6, median 8.9e-5, max 72.2879758378
self_vs_shipped_mse: min 4.58e-14, median 7.50e-10, max 467.805940604
```

The large shipped/self differences occur in chaotic systems and are a property of the shipped
low-tolerance trajectories; shipped trajectories were not used for fitting or scoring.

## SINDy Setup

Version: `pysindy 2.1.0`.

Differentiation method: `pysindy.FiniteDifference(order=2)`. This is a protocol difference from
EvoODE: SINDy fits derivatives, while EvoODE does not require derivative observations. The data are
noise-free, which favours SINDy relative to a noisy derivative-estimation setting.

Optimizer: `pysindy.STLSQ(alpha=1e-6, normalize_columns=False)` with thresholds `0.01` and `0.1`.
Support is evaluated with the EvoODE pruning rule from `experiments/run_experiment.jl`: a SINDy
coefficient is active if `abs(coef) > max(1e-6, 1e-3 * max_abs)` within the same equation.

Model simulation for scoring uses explicit Euler steps on the 512-point Phase-B grid. This avoids
adaptive solver hangs on divergent SINDy RHS functions and records those cells as divergent when
state magnitude exceeds `1e9` or non-finite values appear.

## Grid and Cell Counts

The complete 120-row grid is in `analysis/data/wp_n6_sindy_baseline/summary.csv`: 10 configurations
times 2 directions times 2 regimes times 3 subsets.

Run counts:

```text
fit cells: 126 per configuration
detail rows: 2520
fit_status: success in 2520 / 2520 rows
integration_status: success 2047, diverged 473
R2 valid: 2520 / 2520
R2 > 0.9: 1178 / 2520
```

Cost counts, summed across dimensions per configuration:

```text
poly degree 2:              34 library terms over dimensions, 234 target regressions
poly degree 3:              69 library terms over dimensions, 234 target regressions
poly degree 3 + sin/cos:    89 library terms over dimensions, 234 target regressions
poly degree 4:             125 library terms over dimensions, 234 target regressions
poly degree 5:             209 library terms over dimensions, 234 target regressions
```

Across the 10 configurations this is 1,170 fitted model cells and 2,340 target regressions. The
wall-clock field is written as `elapsed_s_non_evidence_total` in `costs.csv` and is not used as
method evidence.

## Result Ranges

Across all 63 systems:

```text
structure_hit_count range: 7 to 19 of 63
R2 > 0.9 count range:      15 to 43 of 63
divergent count range:     4 to 25 of 63
```

On the 20 EvoODE-staged-representable systems:

```text
structure_hit_count range: 4 to 11 of 20
R2 > 0.9 count range:      5 to 12 of 20
divergent count range:     1 to 9 of 20
```

On the 40 SINDy-polynomial-representable systems:

```text
structure_hit_count range: 7 to 17 of 40
R2 > 0.9 count range:      10 to 25 of 40
divergent count range:     2 to 18 of 40
```

These are ranges over the configured grid, not a selection of a best configuration.

## Comparison to WP-N5 EvoODE Numbers

The descriptive comparison table is `analysis/data/wp_n6_sindy_baseline/evoode_wp_n5_comparison.csv`.
The denominators differ: WP-N5 reports the dimension-1 EvoODE generalization probe with `n=33`,
while WP-N6 SINDy reports all 63 ODEBench systems and also the 20/40 representability subsets.

WP-N5 EvoODE default staged basis:

```text
IC1->IC2 reconstruction: structure 18/33, R2>0.9 33/33, divergent 0/33
IC1->IC2 generalization: structure 18/33, R2>0.9 24/33, divergent 3/33
IC2->IC1 reconstruction: structure 12/33, R2>0.9 30/33, divergent 0/33
IC2->IC1 generalization: structure 12/33, R2>0.9 15/33, divergent 6/33
```

WP-N5 EvoODE staged basis with constant:

```text
IC1->IC2 reconstruction: structure 17/33, R2>0.9 33/33, divergent 0/33
IC1->IC2 generalization: structure 17/33, R2>0.9 29/33, divergent 0/33
IC2->IC1 reconstruction: structure 12/33, R2>0.9 30/33, divergent 0/33
IC2->IC1 generalization: structure 12/33, R2>0.9 22/33, divergent 0/33
```

WP-N6 SINDy over all 63 systems:

```text
reconstruction R2>0.9 range: 32/63 to 43/63
generalization R2>0.9 range: 15/63 to 30/63
reconstruction divergent range: 4/63 to 19/63
generalization divergent range: 8/63 to 25/63
structure-hit range: 7/63 to 19/63
```

Descriptively, SINDy is worse than the WP-N5 EvoODE rows on the reported R2>0.9 rates in both
reconstruction and generalization, and it has more divergent integrations in every corresponding
regime. SINDy is better only on representational coverage before fitting: `sindy_poly=Y` for 40
systems against `evoode_staged=Y` for 20 systems in
`analysis/data/paper1_phaseB_v1/representational_adequacy.csv`. That wider library coverage does
not translate into higher measured structure-hit counts on this grid.

