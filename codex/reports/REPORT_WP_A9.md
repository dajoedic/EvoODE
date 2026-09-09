# WP-A9 Report

## Commands

- `python -m py_compile analysis/scripts/aggregate/aggregate_phaseb_heartbeat_waste_systems.py analysis/scripts/plot/table_phaseb_heartbeat_waste_systems.py`
- `python analysis/scripts/aggregate/aggregate_phaseb_heartbeat_waste_systems.py --config analysis/configs/paper1_phaseB_v1.json`
- `python analysis/scripts/plot/table_phaseb_heartbeat_waste_systems.py --config analysis/configs/paper1_phaseB_v1.json`
- `python analysis/scripts/aggregate/aggregate_phaseb_heartbeat_waste_systems.py --config analysis/configs/paper1_phaseB_v1.json --input analysis/fixtures/wp_a9_missing_complete_registry.csv --heartbeat-dir analysis/fixtures/wp_a9_missing_complete_heartbeats --expected-row-count 1`
- `python -c <acceptance row-count and file-existence check>`

## Aggregation Output

```text
Aggregated Phase-B heartbeat waste and system tables
  Heartbeat streams: 756
  Level-event count values: [{'level_event_count': 1, 'n_cells': 35}, {'level_event_count': 2, 'n_cells': 1}, {'level_event_count': 4, 'n_cells': 6}, {'level_event_count': 5, 'n_cells': 30}, {'level_event_count': 6, 'n_cells': 2}, {'level_event_count': 8, 'n_cells': 10}, {'level_event_count': 11, 'n_cells': 3}, {'level_event_count': 12, 'n_cells': 2}, {'level_event_count': 13, 'n_cells': 13}, {'level_event_count': 14, 'n_cells': 17}, {'level_event_count': 15, 'n_cells': 3}, {'level_event_count': 16, 'n_cells': 67}, {'level_event_count': 17, 'n_cells': 17}, {'level_event_count': 18, 'n_cells': 1}, {'level_event_count': 19, 'n_cells': 1}, {'level_event_count': 20, 'n_cells': 220}, {'level_event_count': 21, 'n_cells': 60}, {'level_event_count': 22, 'n_cells': 32}, {'level_event_count': 23, 'n_cells': 27}, {'level_event_count': 24, 'n_cells': 38}, {'level_event_count': 25, 'n_cells': 29}, {'level_event_count': 26, 'n_cells': 30}, {'level_event_count': 27, 'n_cells': 15}, {'level_event_count': 28, 'n_cells': 21}, {'level_event_count': 29, 'n_cells': 10}, {'level_event_count': 30, 'n_cells': 66}]
  Cells where level_event_count != n_levels: 690
  System table rows: 252
  Equal best_loss transitions: 10794; nonmonotone best_loss transitions: 24
```

The registry reports `n_levels = 30` for all 756 cells. The heartbeat streams show 26 distinct observed level-event counts, from 1 to 30. Only 66 cells have 30 level events; 690 cells differ from the registry value. Cell 1 has 20 observed level events, confirming the known discrepancy. The silent-level measurement is therefore restricted to observed heartbeat `level` events and is not extrapolated to 30 levels.

## Generated Artifacts

Intermediate data under `analysis/data/paper1_phaseB_v1/`:

- `heartbeat_waste_cells.csv`
- `heartbeat_waste_summary.csv`
- `heartbeat_waste_threshold_grid.csv`
- `heartbeat_level_event_counts.csv`
- `heartbeat_last_improvement_level1_by_dim.csv`
- `phaseb_system_table.csv`
- `phaseb_system_waste_top10_by_class.csv`
- `phaseb_system_worst_target_top10_by_class.csv`

Tables under `analysis/tables/paper1_phaseB_v1/`:

- `heartbeat_waste_summary.csv` / `.tex`
- `heartbeat_waste_threshold_grid.csv` / `.tex`
- `phaseb_system_table.csv` / `.tex`
- `phaseb_system_waste_top10_by_class.csv` / `.tex`
- `phaseb_system_worst_target_top10_by_class.csv` / `.tex`

## Improvement Definition

Default improvement threshold: `0.0`. A level counts as an improvement if its `best_loss` is strictly below the best value seen so far. Equal `best_loss` values are not counted as improvements; they are silent unless a later strict decrease occurs. If a `best_loss` value increases relative to the previous heartbeat value, the code records it as a non-monotone transition and still compares the value against the best value seen so far. Across the campaign, there are 10794 equal transitions and 24 non-monotone transitions.

Additional substantive threshold: `0.01`. The aggregation reports `substantial_silent_levels` and `substantial_silent_fraction` in `heartbeat_waste_cells.csv` using a required relative best-loss decrease of at least 1 percent.

## Level-Event Count Distribution

```csv
level_event_count,n_cells
1,35
2,1
4,6
5,30
6,2
8,10
11,3
12,2
13,13
14,17
15,3
16,67
17,17
18,1
19,1
20,220
21,60
22,32
23,27
24,38
25,29
26,30
27,15
28,21
29,10
30,66
```

## Last Improvement on Level 1

```csv
system_dim,n_cells,last_improvement_level1_cells,share
1,276,42,0.152173913043
2,336,68,0.202380952381
3,120,4,0.0333333333333
4,24,12,0.5
```

## Waste by Dimension

Overall silent-fraction quantiles by dimension:

```csv
system_dim,q05,q10,q25,q50,q75,q90,q95
1,0,0,0.142857142857,0.35,0.6875,0.8375,0.95
2,0,0,0.115384615385,0.269230769231,0.5,0.95,0.95
3,0.0333333333333,0.1,0.133333333333,0.3,0.545138888889,0.863636363636,0.904761904762
4,0.579273504274,0.614814814815,0.715925925926,0.888043478261,0.95,0.95,0.95
```

Dimension-level level counts:

```csv
system_dim,n_cells,mean_silent_fraction,silent_levels_sum,level_events_sum
1,276,0.384610613604,1904,4378
2,336,0.346155127529,2401,6804
3,120,0.380526055055,1115,3143
4,24,0.811086786938,436,550
```

The full grouped quantile table by representability, condition, initial-condition set, and dimension is `analysis/tables/paper1_phaseB_v1/heartbeat_waste_summary.csv`. The full threshold grid for silent_fraction > 0.25 / 0.5 / 0.75 / 0.9 is `analysis/tables/paper1_phaseB_v1/heartbeat_waste_threshold_grid.csv`.

## Notable Waste Extract

Systems with the largest silent-level totals, ten per representability class:

```csv
system_id,system_name,system_dim,system_representability,n_cells,silent_levels_sum,silent_fraction_q50,exact_support_match_rate,r2_median,class_target
63,SEIR infection model (proportions),4,exact,12,228,0.95,0,,0
28,Pendulum without friction,2,exact,12,155,0.65,0,,0
8,Logistic equation with Allee effect,1,exact,12,135,0.90625,0.25,,0.25
55,Lorenz equations in complex periodic regime,3,exact,12,99,0.266666666667,0,,0
54,Lorenz equations in well-behaved periodic regime,3,exact,12,93,0.333333333333,0,,0
56,Lorenz equations standard parameters (chaotic),3,exact,12,76,0.216666666667,0,,0
31,SIR infection model only for healthy and sick,2,exact,12,69,0.46875,0.25,,0.25
32,Damped double well oscillator,2,exact,12,64,0.0166666666667,0.583333333333,,0.583333333333
11,Naive critical slowing down (statistical mechanics),1,exact,12,55,0.125,0.5,,0.5
26,Lotka-Volterra competition model (Strogatz version with sheeps and rabbits),2,exact,12,53,0.232142857143,0,,0
30,RNA molecules catalyzing each others replication,2,surrogate,12,228,0.95,,0.988019248179,0.988019248179
39,"Glycolytic oscillator, e.g., ADP and F6P in yeast (dimensionless)",2,surrogate,12,218,0.95,,0.966267040798,0.966267040798
36,"Pendulum with non-linear damping, no driving (dimensionless)",2,surrogate,12,217,0.925,,0.999435117568,0.999435117568
53,Model for apoptosis (cell death),3,surrogate,12,210,0.844861660079,,0.628914662045,0.628914662045
62,Binocular rivalry model with adaptation (oscillations),4,surrogate,12,208,0.711851851852,,0.999457624591,0.999457624591
46,Interacting bar magnets,2,surrogate,12,201,0.94375,,0.902630359773,0.902630359773
47,Binocular rivalry model (no oscillations),2,surrogate,12,186,0.738095238095,,0.875515966553,0.875515966553
9,Language death model for two languages,1,surrogate,12,185,0.85,,0.290633124854,0.290633124854
10,Refined language death model for two languages,1,surrogate,12,174,0.74375,,0.996500373643,0.996500373643
57,Rossler attractor (stable fixed point),3,surrogate,12,163,0.667832167832,,0.796171500126,0.796171500126
```

## Worst Target Extract

Lowest class-specific target systems, ten per representability class:

```csv
system_id,system_name,system_dim,system_representability,n_cells,silent_levels_sum,silent_fraction_q50,exact_support_match_rate,r2_median,class_target
26,Lotka-Volterra competition model (Strogatz version with sheeps and rabbits),2,exact,12,53,0.232142857143,0,,0
28,Pendulum without friction,2,exact,12,155,0.65,0,,0
54,Lorenz equations in well-behaved periodic regime,3,exact,12,93,0.333333333333,0,,0
55,Lorenz equations in complex periodic regime,3,exact,12,99,0.266666666667,0,,0
56,Lorenz equations standard parameters (chaotic),3,exact,12,76,0.216666666667,0,,0
61,Chen-Lee attractor; system for gyro motion with feedback control of rigid body (chaotic),3,exact,12,44,0.136645962733,0,,0
63,SEIR infection model (proportions),4,exact,12,228,0.95,0,,0
8,Logistic equation with Allee effect,1,exact,12,135,0.90625,0.25,,0.25
29,Dipole fixed point,2,exact,12,47,0.240384615385,0.25,,0.25
31,SIR infection model only for healthy and sick,2,exact,12,69,0.46875,0.25,,0.25
9,Language death model for two languages,1,surrogate,12,185,0.85,,0.290633124854,0.290633124854
60,Aizawa attractor (chaotic),3,surrogate,12,127,0.386083743842,,0.49215611823,0.49215611823
53,Model for apoptosis (cell death),3,surrogate,12,210,0.844861660079,,0.628914662045,0.628914662045
52,Maxwell-Bloch equations (laser dynamics),3,surrogate,12,148,0.642857142857,,0.668585368777,0.668585368777
59,Rossler attractor (chaotic),3,surrogate,12,71,0.116666666667,,0.742733836367,0.742733836367
57,Rossler attractor (stable fixed point),3,surrogate,12,163,0.667832167832,,0.796171500126,0.796171500126
47,Binocular rivalry model (no oscillations),2,surrogate,12,186,0.738095238095,,0.875515966553,0.875515966553
46,Interacting bar magnets,2,surrogate,12,201,0.94375,,0.902630359773,0.902630359773
50,Chemical oscillator model by Schnackenberg 1979 (dimensionless),2,surrogate,12,128,0.568681318681,,0.913735525161,0.913735525161
58,Rossler attractor (periodic),3,surrogate,12,84,0.225,,0.9277456279,0.9277456279
```

## Fixture Error Path

Exit code: 1

```text
Error: C:\Users\joedicke\Documents\reps\EvoODE\analysis\fixtures\wp_a9_missing_complete_heartbeats\cell_000001.heartbeat.jsonl has no complete event
```

## Acceptance Check

```text
missing []
system_table_rows 252
heartbeat_streams 756
```

## Pilot Comparison

WP-B1 pilot values were time fractions: dim 1 about 10 percent, dim 2 50 percent, dim 3 44 percent, dim 4 96 percent. The campaign metric here is a level fraction, not a time fraction. By mean silent level fraction, dim 4 remains the highest at 0.811, so the campaign level-count evidence is directionally consistent with the pilot's strong dim-4 waste signal but lower in magnitude. Dim 3 is 0.381, close to the pilot's 0.44. Dim 2 is 0.346, below the pilot's 0.50. Dim 1 is 0.385, above the pilot's 0.10. Because the pilot used elapsed time and this report uses level counts, these are not direct cost-ratio confirmations.
