# WP-A8 Report

## Commands

- `python analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py --input experiments/paper1_phaseB_v1/history.jsonl --output experiments/paper1_phaseB_v1/run_registry.csv --experiment-id paper1_phaseB_v1`
- `python analysis/scripts/aggregate/verify_campaign_registry.py --input experiments/paper1_phaseB_v1/run_registry.csv`
- `python analysis/scripts/aggregate/aggregate_phaseb_descriptive_tables.py --config analysis/configs/paper1_phaseB_v1.json`
- `python analysis/scripts/plot/table_phaseb_descriptive_results.py --config analysis/configs/paper1_phaseB_v1.json`
- `python -m py_compile analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py analysis/scripts/aggregate/aggregate_phaseb_descriptive_tables.py analysis/scripts/plot/table_phaseb_descriptive_results.py`
- `python -c <registry column check>`
- `python analysis/scripts/aggregate/aggregate_phaseb_descriptive_tables.py --config analysis/configs/paper1_phaseB_v1.json --input analysis/fixtures/wp_a8_bad_retcode_json.csv`

## Registry verification output

```text
Verified campaign registry: 756 rows
  Unique identities: 756
  Condition column: condition
  Rows per condition: {'pretune_off': 378, 'pretune_on': 378}
  Representability: exact=240, surrogate=516
  git_hash: 91f88c4
  config_fingerprint: 604e79733b22d64d
  stage_cap_behavior_fingerprint: ffb0266c7913352c
  Numeric surrogate r2 rows: 516
```

## Aggregation output

```text
Aggregated Phase-B descriptive tables
  Input: C:\Users\joedicke\Documents\reps\EvoODE\experiments\paper1_phaseB_v1\run_registry.csv
  Output: C:\Users\joedicke\Documents\reps\EvoODE\analysis\data\paper1_phaseB_v1
  Rows: total=756, exact=240, surrogate=516
  Success true cells: 756
  Failure reason cells: 0
  descriptive_t1_surrogate_r2.csv: 16 rows
  descriptive_t2_exact_fit_quality.csv: 32 rows
  descriptive_t3_exact_support.csv: 96 rows
  descriptive_t4_stage_economy.csv: 208 rows
  descriptive_t5_robustness.csv: 4 rows
```

## Fixture error-path output

Exit code: 1

```text
Error: solver_retcodes is not valid JSON at row 2: Expecting value: line 1 column 1 (char 0)
```

## Success and failure check

T5 reports 756 cells with `success == True` and 0 cells with a set `failure_reason`. The generated registry has all nine WP-A8 robustness columns: `solver_retcodes`, `optimizer_retcodes`, `total_diverged_solves`, `total_invalid_solves`, `total_nonfinite_solves`, `total_solver_unstable_solves`, `total_step_limit_solves`, `total_optimizer_limit_hits`, and `total_optimizer_budget_stop_fits`.

The robustness counters are not all zero: diverged, invalid, solver-unstable, step-limit, optimizer-limit, and optimizer-budget counters contain nonzero totals. This does not contradict the narrow assumption of 756 successful cells and no `failure_reason`, but it does show that successful cells can still contain recorded robustness events inside their internal solve/optimizer attempts. `total_nonfinite_solves` is 0 in every T5 group.

## Tables

### T1 -- Fit quality, surrogate systems

```csv
condition,initial_condition_set,system_dim,n_cells,r2_q05,r2_q10,r2_q25,r2_q50,r2_q75,r2_q90,r2_q95,share_r2_gt_0_5,share_r2_gt_0_9,share_r2_gt_0_99,share_r2_gt_0_999
pretune_off,1,1,51,0.979371362693,0.980392655315,0.999425239077,0.999926152064,0.999992825259,0.999996027118,0.999999146629,1,1,0.882352941176,0.764705882353
pretune_off,1,2,57,0.797411608899,0.870146109349,0.955979077571,0.983686305772,0.997458850583,0.999574907861,0.999718891344,1,0.894736842105,0.456140350877,0.245614035088
pretune_off,1,3,18,0.397596861563,0.43350864627,0.527860075676,0.656539951775,0.796550095346,0.959601085319,0.967662850556,0.777777777778,0.166666666667,0,0
pretune_off,1,4,3,0.999845709394,0.999860532539,0.999905001975,0.999979117701,0.999982084842,0.999983865127,0.999984458555,1,1,1,1
pretune_off,2,1,51,0.290152286142,0.977554127018,0.996738274784,0.999575381604,0.99999419479,0.999999084187,0.999999657913,0.941176470588,0.941176470588,0.823529411765,0.647058823529
pretune_off,2,2,57,0.908521118104,0.920939579656,0.975457880662,0.986117315064,0.996405508096,0.999430864842,0.999940506906,1,0.947368421053,0.473684210526,0.210526315789
pretune_off,2,3,18,0.500390176469,0.545342940339,0.609720527115,0.688393524148,0.900549940182,0.961934040776,0.971039471891,0.944444444444,0.277777777778,0.0555555555556,0
pretune_off,2,4,3,0.881436529744,0.885790823891,0.898853706333,0.920625177069,0.954146582629,0.974259425964,0.980963707076,1,0.666666666667,0,0
pretune_on,1,1,51,0.978581652342,0.978647500242,0.999449646876,0.999926152058,0.999992925436,0.999999880083,0.999999913298,1,1,0.882352941176,0.764705882353
pretune_on,1,2,57,0.715226319294,0.757178206398,0.892741830823,0.981396424245,0.997478499641,0.999569326254,0.999673467605,1,0.701754385965,0.368421052632,0.228070175439
pretune_on,1,3,18,0.329891585704,0.331148730626,0.528381923631,0.787326053275,0.899410335046,0.945468896564,0.986823190114,0.833333333333,0.277777777778,0,0
pretune_on,1,4,3,0.999471982168,0.999484678577,0.999522767802,0.999586249845,0.99970346193,0.999773789181,0.999797231599,1,1,1,1
pretune_on,2,1,51,0.290152286142,0.977554127018,0.996738274783,0.999575381424,0.999994519791,0.999999356656,0.999999668733,0.941176470588,0.941176470588,0.823529411765,0.647058823529
pretune_on,2,2,57,0.886248059319,0.920939586324,0.965675449778,0.982457916303,0.998380932186,0.999716745442,0.999953159945,1,0.947368421053,0.473684210526,0.210526315789
pretune_on,2,3,18,0.546031678504,0.549079648028,0.599389150242,0.906384006614,0.939437494965,0.966371772724,0.967062005151,1,0.5,0,0
pretune_on,2,4,3,0.930307006915,0.932179104065,0.937795395512,0.947155881258,0.97330592234,0.988995946989,0.994225955206,1,1,0.333333333333,0.333333333333
```

### T2 -- Fit quality, exact systems

```csv
metric,condition,initial_condition_set,system_dim,n_cells,value_q05,value_q10,value_q25,value_q50,value_q75,value_q90,value_q95
log10_loss,pretune_off,1,1,18,-14.3331775289,-14.3311879707,-13.6331264537,-11.1469119376,-9.03233626454,-4.97816290545,-4.72768807745
log10_loss,pretune_off,1,2,27,-14.1200652431,-13.902707156,-13.3725451823,-10.8571642722,-3.87534087205,-2.26505200816,-0.253757319327
log10_loss,pretune_off,1,3,12,-2.38048725398,-2.2794102113,0.814403884613,1.82163576531,2.1342850851,2.55273120516,2.57278977681
log10_loss,pretune_off,1,4,3,-3.20856039321,-3.19683898052,-3.16167474245,-3.10306767899,-2.96804417398,-2.88703007097,-2.86002536997
log10_loss,pretune_off,2,1,18,-13.3940401981,-13.2160913631,-13.1730140774,-9.60647725683,-3.24203910746,-3.02361578913,-3.02361578913
log10_loss,pretune_off,2,2,27,-14.2240387478,-14.1017975721,-11.0214419108,-7.42816986044,-3.47438413321,-2.7511370844,-0.644967174334
log10_loss,pretune_off,2,3,12,0.21063005856,0.264980766367,1.41043499899,1.85637465916,2.10102204704,2.59637204763,2.600555868
log10_loss,pretune_off,2,4,3,-3.33075813712,-3.33001336252,-3.32777903871,-3.3240551657,-3.27295333621,-3.24229223852,-3.23207187262
log10_loss,pretune_on,1,1,18,-14.3303005224,-14.3303005224,-13.5479384816,-10.5404934689,-7.87237057429,2.75965627074,2.75965627074
log10_loss,pretune_on,1,2,27,-14.1286801558,-13.9188669395,-11.7083887672,-6.18414661357,-3.871949414,-3.42247828811,-3.19175900098
log10_loss,pretune_on,1,3,12,-3.63203232036,-3.18073685786,0.477008116992,1.70237924124,1.97356596636,2.52520872126,2.53593243061
log10_loss,pretune_on,1,4,3,-3.20856039321,-3.19683898052,-3.16167474245,-3.10306767899,-2.96804417398,-2.88703007097,-2.86002536997
log10_loss,pretune_on,2,1,18,-13.1830661127,-13.1830661127,-12.6770680413,-9.6228503446,-3.24203910746,-3.02361578911,-3.02361578911
log10_loss,pretune_on,2,2,27,-14.1870660995,-14.0835587325,-8.50327412888,-7.56009814995,-3.29334863154,-1.22025922852,1.59327231518
log10_loss,pretune_on,2,3,12,-0.393826786186,-0.393826786186,1.1964355473,1.75417057449,1.98648255839,2.44496081125,2.48877911755
log10_loss,pretune_on,2,4,3,-3.33075813712,-3.33001336252,-3.32777903871,-3.3240551657,-3.27295333621,-3.24229223852,-3.23207187262
r2,pretune_off,1,1,18,0.999999934749,0.999999961948,0.999999999953,1,1,1,1
r2,pretune_off,1,2,27,0.905596449837,0.973590483783,0.999947379775,0.999999999989,0.999999999999,1,1
r2,pretune_off,1,3,12,0.0149303169186,0.0571172785728,0.0914007808601,0.218521806236,0.466809954991,0.993154418266,0.995171992337
r2,pretune_off,1,4,3,0.169511951795,0.202775797668,0.302567335289,0.468886564656,0.480501781874,0.487470912206,0.48979395565
r2,pretune_off,2,1,18,0.988014375392,0.988014375392,0.993263221204,0.999999999986,1,1,1
r2,pretune_off,2,2,27,0.987889868564,0.988858476711,0.99612278679,0.999999983159,0.999999999997,0.999999999999,0.999999999999
r2,pretune_off,2,3,12,0.0303823091059,0.0602466134006,0.0958871499023,0.18292021006,0.336137892654,0.756097998193,0.797649212566
r2,pretune_off,2,4,3,0.876718363339,0.879005106049,0.885865334176,0.897299047723,0.897720025591,0.897972612313,0.898056807886
r2,pretune_on,1,1,18,-0.964635760317,-0.964635760317,0.999999999498,0.999999999987,1,1,1
r2,pretune_on,1,2,27,0.997502423889,0.997929041309,0.999947244227,0.999999892914,0.999999999998,0.999999999999,1
r2,pretune_on,1,3,12,0.045300411888,0.0631248035246,0.234234443499,0.328925489022,0.562510845887,0.999357115404,0.999642614805
r2,pretune_on,1,4,3,0.169511951891,0.202775797646,0.302567334911,0.468886563686,0.480501785469,0.487470918538,0.489793962895
r2,pretune_on,2,1,18,0.988014375392,0.988014375392,0.993263221204,0.999999999989,0.999999999999,1,1
r2,pretune_on,2,2,27,0.44502852121,0.771017623082,0.990502405708,0.999999991259,0.999999995767,0.999999999999,0.999999999999
r2,pretune_on,2,3,12,0.171923469972,0.196567476306,0.242672424168,0.325486028206,0.588449892411,0.95418398716,0.95418398716
r2,pretune_on,2,4,3,0.876718358157,0.87900510142,0.885865331211,0.897299047529,0.897720024765,0.897972611106,0.898056806553
```

### T3 -- Support recovery, exact systems

```csv
aggregation_level,condition,initial_condition_set,system_dim,system_id,system_name,n_cells,support_match_count,support_match_rate,share_system_rate_ge_0_0,share_system_rate_ge_0_333333,share_system_rate_ge_0_666667,share_system_rate_ge_1_0
system,pretune_off,1,1,2,Population growth (naive),3,3,1,,,,
system,pretune_off,1,1,3,Population growth with carrying capacity,3,3,1,,,,
system,pretune_off,1,1,6,Autocatalysis with one fixed abundant chemical,3,3,1,,,,
system,pretune_off,1,1,8,Logistic equation with Allee effect,3,3,1,,,,
system,pretune_off,1,1,11,Naive critical slowing down (statistical mechanics),3,3,1,,,,
system,pretune_off,1,1,12,Photons in a laser (simple),3,3,1,,,,
system,pretune_off,1,2,24,Harmonic oscillator without damping,3,3,1,,,,
system,pretune_off,1,2,25,Harmonic oscillator with damping,3,3,1,,,,
system,pretune_off,1,2,26,Lotka-Volterra competition model (Strogatz version with sheeps and rabbits),3,0,0,,,,
system,pretune_off,1,2,27,Lotka-Volterra simple (as on Wikipedia),3,0,0,,,,
system,pretune_off,1,2,28,Pendulum without friction,3,0,0,,,,
system,pretune_off,1,2,29,Dipole fixed point,3,3,1,,,,
system,pretune_off,1,2,31,SIR infection model only for healthy and sick,3,0,0,,,,
system,pretune_off,1,2,32,Damped double well oscillator,3,3,1,,,,
system,pretune_off,1,2,38,Van der Pol oscillator (simplified form from Strogatz),3,3,1,,,,
system,pretune_off,1,3,54,Lorenz equations in well-behaved periodic regime,3,0,0,,,,
system,pretune_off,1,3,55,Lorenz equations in complex periodic regime,3,0,0,,,,
system,pretune_off,1,3,56,Lorenz equations standard parameters (chaotic),3,0,0,,,,
system,pretune_off,1,3,61,Chen-Lee attractor; system for gyro motion with feedback control of rigid body (chaotic),3,0,0,,,,
system,pretune_off,1,4,63,SEIR infection model (proportions),3,0,0,,,,
system,pretune_off,2,1,2,Population growth (naive),3,3,1,,,,
system,pretune_off,2,1,3,Population growth with carrying capacity,3,3,1,,,,
system,pretune_off,2,1,6,Autocatalysis with one fixed abundant chemical,3,3,1,,,,
system,pretune_off,2,1,8,Logistic equation with Allee effect,3,0,0,,,,
system,pretune_off,2,1,11,Naive critical slowing down (statistical mechanics),3,0,0,,,,
system,pretune_off,2,1,12,Photons in a laser (simple),3,3,1,,,,
system,pretune_off,2,2,24,Harmonic oscillator without damping,3,3,1,,,,
system,pretune_off,2,2,25,Harmonic oscillator with damping,3,3,1,,,,
system,pretune_off,2,2,26,Lotka-Volterra competition model (Strogatz version with sheeps and rabbits),3,0,0,,,,
system,pretune_off,2,2,27,Lotka-Volterra simple (as on Wikipedia),3,2,0.666666666667,,,,
system,pretune_off,2,2,28,Pendulum without friction,3,0,0,,,,
system,pretune_off,2,2,29,Dipole fixed point,3,0,0,,,,
system,pretune_off,2,2,31,SIR infection model only for healthy and sick,3,3,1,,,,
system,pretune_off,2,2,32,Damped double well oscillator,3,1,0.333333333333,,,,
system,pretune_off,2,2,38,Van der Pol oscillator (simplified form from Strogatz),3,3,1,,,,
system,pretune_off,2,3,54,Lorenz equations in well-behaved periodic regime,3,0,0,,,,
system,pretune_off,2,3,55,Lorenz equations in complex periodic regime,3,0,0,,,,
system,pretune_off,2,3,56,Lorenz equations standard parameters (chaotic),3,0,0,,,,
system,pretune_off,2,3,61,Chen-Lee attractor; system for gyro motion with feedback control of rigid body (chaotic),3,0,0,,,,
system,pretune_off,2,4,63,SEIR infection model (proportions),3,0,0,,,,
system,pretune_on,1,1,2,Population growth (naive),3,3,1,,,,
system,pretune_on,1,1,3,Population growth with carrying capacity,3,3,1,,,,
system,pretune_on,1,1,6,Autocatalysis with one fixed abundant chemical,3,3,1,,,,
system,pretune_on,1,1,8,Logistic equation with Allee effect,3,0,0,,,,
system,pretune_on,1,1,11,Naive critical slowing down (statistical mechanics),3,3,1,,,,
system,pretune_on,1,1,12,Photons in a laser (simple),3,3,1,,,,
system,pretune_on,1,2,24,Harmonic oscillator without damping,3,3,1,,,,
system,pretune_on,1,2,25,Harmonic oscillator with damping,3,3,1,,,,
system,pretune_on,1,2,26,Lotka-Volterra competition model (Strogatz version with sheeps and rabbits),3,0,0,,,,
system,pretune_on,1,2,27,Lotka-Volterra simple (as on Wikipedia),3,2,0.666666666667,,,,
system,pretune_on,1,2,28,Pendulum without friction,3,0,0,,,,
system,pretune_on,1,2,29,Dipole fixed point,3,0,0,,,,
system,pretune_on,1,2,31,SIR infection model only for healthy and sick,3,0,0,,,,
system,pretune_on,1,2,32,Damped double well oscillator,3,3,1,,,,
system,pretune_on,1,2,38,Van der Pol oscillator (simplified form from Strogatz),3,3,1,,,,
system,pretune_on,1,3,54,Lorenz equations in well-behaved periodic regime,3,0,0,,,,
system,pretune_on,1,3,55,Lorenz equations in complex periodic regime,3,0,0,,,,
system,pretune_on,1,3,56,Lorenz equations standard parameters (chaotic),3,0,0,,,,
system,pretune_on,1,3,61,Chen-Lee attractor; system for gyro motion with feedback control of rigid body (chaotic),3,0,0,,,,
system,pretune_on,1,4,63,SEIR infection model (proportions),3,0,0,,,,
system,pretune_on,2,1,2,Population growth (naive),3,3,1,,,,
system,pretune_on,2,1,3,Population growth with carrying capacity,3,3,1,,,,
system,pretune_on,2,1,6,Autocatalysis with one fixed abundant chemical,3,3,1,,,,
system,pretune_on,2,1,8,Logistic equation with Allee effect,3,0,0,,,,
system,pretune_on,2,1,11,Naive critical slowing down (statistical mechanics),3,0,0,,,,
system,pretune_on,2,1,12,Photons in a laser (simple),3,3,1,,,,
system,pretune_on,2,2,24,Harmonic oscillator without damping,3,3,1,,,,
system,pretune_on,2,2,25,Harmonic oscillator with damping,3,3,1,,,,
system,pretune_on,2,2,26,Lotka-Volterra competition model (Strogatz version with sheeps and rabbits),3,0,0,,,,
system,pretune_on,2,2,27,Lotka-Volterra simple (as on Wikipedia),3,3,1,,,,
system,pretune_on,2,2,28,Pendulum without friction,3,0,0,,,,
system,pretune_on,2,2,29,Dipole fixed point,3,0,0,,,,
system,pretune_on,2,2,31,SIR infection model only for healthy and sick,3,0,0,,,,
system,pretune_on,2,2,32,Damped double well oscillator,3,0,0,,,,
system,pretune_on,2,2,38,Van der Pol oscillator (simplified form from Strogatz),3,0,0,,,,
system,pretune_on,2,3,54,Lorenz equations in well-behaved periodic regime,3,0,0,,,,
system,pretune_on,2,3,55,Lorenz equations in complex periodic regime,3,0,0,,,,
system,pretune_on,2,3,56,Lorenz equations standard parameters (chaotic),3,0,0,,,,
system,pretune_on,2,3,61,Chen-Lee attractor; system for gyro motion with feedback control of rigid body (chaotic),3,0,0,,,,
system,pretune_on,2,4,63,SEIR infection model (proportions),3,0,0,,,,
dimension,pretune_off,1,1,,,18,18,1,1,1,1,1
dimension,pretune_off,1,2,,,27,15,0.555555555556,1,0.555555555556,0.555555555556,0.555555555556
dimension,pretune_off,1,3,,,12,0,0,1,0,0,0
dimension,pretune_off,1,4,,,3,0,0,1,0,0,0
dimension,pretune_off,2,1,,,18,12,0.666666666667,1,0.666666666667,0.666666666667,0.666666666667
dimension,pretune_off,2,2,,,27,15,0.555555555556,1,0.666666666667,0.555555555556,0.444444444444
dimension,pretune_off,2,3,,,12,0,0,1,0,0,0
dimension,pretune_off,2,4,,,3,0,0,1,0,0,0
dimension,pretune_on,1,1,,,18,15,0.833333333333,1,0.833333333333,0.833333333333,0.833333333333
dimension,pretune_on,1,2,,,27,14,0.518518518519,1,0.555555555556,0.555555555556,0.444444444444
dimension,pretune_on,1,3,,,12,0,0,1,0,0,0
dimension,pretune_on,1,4,,,3,0,0,1,0,0,0
dimension,pretune_on,2,1,,,18,12,0.666666666667,1,0.666666666667,0.666666666667,0.666666666667
dimension,pretune_on,2,2,,,27,9,0.333333333333,1,0.333333333333,0.333333333333,0.333333333333
dimension,pretune_on,2,3,,,12,0,0,1,0,0,0
dimension,pretune_on,2,4,,,3,0,0,1,0,0,0
```

### T4 -- Stage economy

```csv
system_representability,metric,condition,initial_condition_set,system_dim,n_cells,value_q05,value_q10,value_q25,value_q50,value_q75,value_q90,value_q95,stage_caps,eq_final_stages
exact,final_stage,pretune_off,1,1,18,1,1,2,2,4,4,4,[null],[1]
exact,final_stage,pretune_off,1,2,27,1,1,3,3,4,5,5,"[null,null]","[1,1]"
exact,final_stage,pretune_off,1,3,12,3,3,3,4,5,5,5,"[null,3,3]","[5,3,3]"
exact,final_stage,pretune_off,1,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
exact,final_stage,pretune_off,2,1,18,1,1,2,2,4,4,4,[null],[1]
exact,final_stage,pretune_off,2,2,27,1,1,3,3,4,5,5,"[null,null]","[1,1]"
exact,final_stage,pretune_off,2,3,12,3,3,3.75,4,5,5,5,"[null,3,3]","[5,3,3]"
exact,final_stage,pretune_off,2,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
exact,final_stage,pretune_on,1,1,18,1,1,2,2,4,4,4,[null],[1]
exact,final_stage,pretune_on,1,2,27,1,1,3,3,4,4.4,5,"[null,null]","[1,1]"
exact,final_stage,pretune_on,1,3,12,3,3,3.75,4.5,5,5,5,"[null,3,3]","[5,3,3]"
exact,final_stage,pretune_on,1,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
exact,final_stage,pretune_on,2,1,18,1,1,2,2,4,4,4,[null],[1]
exact,final_stage,pretune_on,2,2,27,1,1,3,3,5,5,5,"[null,null]","[1,1]"
exact,final_stage,pretune_on,2,3,12,3,3,3.75,5,5,5,5,"[null,3,3]","[5,3,3]"
exact,final_stage,pretune_on,2,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
exact,n_levels,pretune_off,1,1,18,30,30,30,30,30,30,30,,
exact,n_levels,pretune_off,1,2,27,30,30,30,30,30,30,30,,
exact,n_levels,pretune_off,1,3,12,30,30,30,30,30,30,30,,
exact,n_levels,pretune_off,1,4,3,30,30,30,30,30,30,30,,
exact,n_levels,pretune_off,2,1,18,30,30,30,30,30,30,30,,
exact,n_levels,pretune_off,2,2,27,30,30,30,30,30,30,30,,
exact,n_levels,pretune_off,2,3,12,30,30,30,30,30,30,30,,
exact,n_levels,pretune_off,2,4,3,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,1,1,18,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,1,2,27,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,1,3,12,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,1,4,3,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,2,1,18,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,2,2,27,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,2,3,12,30,30,30,30,30,30,30,,
exact,n_levels,pretune_on,2,4,3,30,30,30,30,30,30,30,,
exact,total_loss_evals,pretune_off,1,1,18,2869.65,2950.8,11556,102996,146484.5,1086183.9,1104371.6,,
exact,total_loss_evals,pretune_off,1,2,27,59631.3,130188.6,612060,844994,1411893,2963240.6,4274678.6,,
exact,total_loss_evals,pretune_off,1,3,12,1811018.45,2159981.8,2582417.5,3679930.5,3768681.75,3810844.5,3993840,,
exact,total_loss_evals,pretune_off,1,4,3,336551.9,355851.8,413751.5,510251,629877.5,701653.4,725578.7,,
exact,total_loss_evals,pretune_off,2,1,18,2431.5,2457,78586.5,146984.5,176887.25,221755.9,262371.1,,
exact,total_loss_evals,pretune_off,2,2,27,9878.8,10643.4,312990.5,608554,1718468.5,2394508,2727126.5,,
exact,total_loss_evals,pretune_off,2,3,12,2151986.9,2214764.4,2417008.5,2983327,3242065.5,3418735.5,3455157.9,,
exact,total_loss_evals,pretune_off,2,4,3,447772.5,467996,528666.5,629784,721580.5,776658.4,795017.7,,
exact,total_loss_evals,pretune_on,1,1,18,1830,1830,9470,22950,58050,600000,600000,,
exact,total_loss_evals,pretune_on,1,2,27,4085.9,6037.2,109670.5,982202,1379455.5,2237747.8,2971587.6,,
exact,total_loss_evals,pretune_on,1,3,12,2979047.95,3159029.3,4480700.75,5414782,7069804.25,7632320.3,7953953.5,,
exact,total_loss_evals,pretune_on,1,4,3,213421.3,219898.6,239330.5,271717,400816.5,478276.2,504096.1,,
exact,total_loss_evals,pretune_on,2,1,18,480,480,9930,35480,198290,391820,391820,,
exact,total_loss_evals,pretune_on,2,2,27,3773,4973.6,109735.5,505259,1810609.5,4091282,4783903.8,,
exact,total_loss_evals,pretune_on,2,3,12,4858647.45,5052953.2,5363425,6022795.5,7334266,7757578,7979835.9,,
exact,total_loss_evals,pretune_on,2,4,3,379089.5,386035,406871.5,441599,610632.5,712052.6,745859.3,,
exact,total_ode_solves,pretune_off,1,1,18,2869.65,2950.8,11556,102996,146484.5,1086183.9,1104371.6,,
exact,total_ode_solves,pretune_off,1,2,27,59631.3,130188.6,612060,844994,1411893,2963240.6,4274678.6,,
exact,total_ode_solves,pretune_off,1,3,12,1811018.45,2159981.8,2582417.5,3679930.5,3768681.75,3810844.5,3993840,,
exact,total_ode_solves,pretune_off,1,4,3,336551.9,355851.8,413751.5,510251,629877.5,701653.4,725578.7,,
exact,total_ode_solves,pretune_off,2,1,18,2431.5,2457,78586.5,146984.5,176887.25,221755.9,262371.1,,
exact,total_ode_solves,pretune_off,2,2,27,9878.8,10643.4,312990.5,608554,1718468.5,2394508,2727126.5,,
exact,total_ode_solves,pretune_off,2,3,12,2151986.9,2214764.4,2417008.5,2983327,3242065.5,3418735.5,3455157.9,,
exact,total_ode_solves,pretune_off,2,4,3,447772.5,467996,528666.5,629784,721580.5,776658.4,795017.7,,
exact,total_ode_solves,pretune_on,1,1,18,1830,1830,9470,22950,58050,600000,600000,,
exact,total_ode_solves,pretune_on,1,2,27,4085.9,6037.2,109670.5,982202,1379455.5,2237747.8,2971587.6,,
exact,total_ode_solves,pretune_on,1,3,12,2979047.95,3159029.3,4480700.75,5414782,7069804.25,7632320.3,7953953.5,,
exact,total_ode_solves,pretune_on,1,4,3,213421.3,219898.6,239330.5,271717,400816.5,478276.2,504096.1,,
exact,total_ode_solves,pretune_on,2,1,18,480,480,9930,35480,198290,391820,391820,,
exact,total_ode_solves,pretune_on,2,2,27,3773,4973.6,109735.5,505259,1810609.5,4091282,4783903.8,,
exact,total_ode_solves,pretune_on,2,3,12,4858647.45,5052953.2,5363425,6022795.5,7334266,7757578,7979835.9,,
exact,total_ode_solves,pretune_on,2,4,3,379089.5,386035,406871.5,441599,610632.5,712052.6,745859.3,,
exact,total_parameter_fits,pretune_off,1,1,18,30,30,110,110,270,330,330,,
exact,total_parameter_fits,pretune_off,1,2,27,30,30,260,350,440,490,532,,
exact,total_parameter_fits,pretune_off,1,3,12,385,436,505,610,610,610,610,,
exact,total_parameter_fits,pretune_off,1,4,3,410,410,410,410,410,410,410,,
exact,total_parameter_fits,pretune_off,2,1,18,30,30,110,110,330,330,330,,
exact,total_parameter_fits,pretune_off,2,2,27,30,30,230,290,390,430,486,,
exact,total_parameter_fits,pretune_off,2,3,12,385,442,550,600,610,610,610,,
exact,total_parameter_fits,pretune_off,2,4,3,410,410,410,410,410,410,410,,
exact,total_parameter_fits,pretune_on,1,1,18,30,30,110,140,270,330,330,,
exact,total_parameter_fits,pretune_on,1,2,27,30,30,270,290,350,374,410,,
exact,total_parameter_fits,pretune_on,1,3,12,350,366,555,580,610,610,610,,
exact,total_parameter_fits,pretune_on,1,4,3,410,410,410,410,410,410,410,,
exact,total_parameter_fits,pretune_on,2,1,18,30,30,110,110,330,330,330,,
exact,total_parameter_fits,pretune_on,2,2,27,30,30,270,350,410,426,450,,
exact,total_parameter_fits,pretune_on,2,3,12,481,490,505,610,610,610,610,,
exact,total_parameter_fits,pretune_on,2,4,3,410,410,410,410,410,410,410,,
exact,stage_overshoot,pretune_off,1,1,18,0,0,0,0,0,0,0,,
exact,stage_overshoot,pretune_off,1,2,27,0,0,0,0,0,0,0,,
exact,stage_overshoot,pretune_off,1,3,12,0,0,0,1,2,2,2,,
exact,stage_overshoot,pretune_off,1,4,3,2,2,2,2,2,2,2,,
exact,stage_overshoot,pretune_off,2,1,18,0,0,0,0,0,0,0,,
exact,stage_overshoot,pretune_off,2,2,27,0,0,0,0,0,0.4,1,,
exact,stage_overshoot,pretune_off,2,3,12,0,0,0.75,1,2,2,2,,
exact,stage_overshoot,pretune_off,2,4,3,2,2,2,2,2,2,2,,
exact,stage_overshoot,pretune_on,1,1,18,0,0,0,0,0,0,0,,
exact,stage_overshoot,pretune_on,1,2,27,0,0,0,0,0,0,0,,
exact,stage_overshoot,pretune_on,1,3,12,0,0,0.75,1.5,2,2,2,,
exact,stage_overshoot,pretune_on,1,4,3,2,2,2,2,2,2,2,,
exact,stage_overshoot,pretune_on,2,1,18,0,0,0,0,0,0,0,,
exact,stage_overshoot,pretune_on,2,2,27,0,0,0,0,0,1.4,2,,
exact,stage_overshoot,pretune_on,2,3,12,0,0,0.75,2,2,2,2,,
exact,stage_overshoot,pretune_on,2,4,3,2,2,2,2,2,2,2,,
exact,wasted_levels,pretune_off,1,1,18,0,0,0,0,0,0,0,,
exact,wasted_levels,pretune_off,1,2,27,0,0,0,0,0,0,0,,
exact,wasted_levels,pretune_off,1,3,12,0,0,0,5.5,8,8,8,,
exact,wasted_levels,pretune_off,1,4,3,8,8,8,8,8,8,8,,
exact,wasted_levels,pretune_off,2,1,18,0,0,0,0,0,0,0,,
exact,wasted_levels,pretune_off,2,2,27,0,0,0,0,0,1.2,3.7,,
exact,wasted_levels,pretune_off,2,3,12,0,0,0.75,4.5,8,8,9.35,,
exact,wasted_levels,pretune_off,2,4,3,8,8,8,8,8,8,8,,
exact,wasted_levels,pretune_on,1,1,18,0,0,0,0,0,0,0,,
exact,wasted_levels,pretune_on,1,2,27,0,0,0,0,0,0,0,,
exact,wasted_levels,pretune_on,1,3,12,0,0,2.25,5,8,8,8,,
exact,wasted_levels,pretune_on,1,4,3,8,8,8,8,8,8,8,,
exact,wasted_levels,pretune_on,2,1,18,0,0,0,0,0,0,0,,
exact,wasted_levels,pretune_on,2,2,27,0,0,0,0,0,5.6,8,,
exact,wasted_levels,pretune_on,2,3,12,0,0,1.5,5.5,8,8,8,,
exact,wasted_levels,pretune_on,2,4,3,8,8,8,8,8,8,8,,
exact,eq_overshoot_sum,pretune_off,1,1,18,0,0,0,0,0,0,0,,
exact,eq_overshoot_sum,pretune_off,1,2,27,0,0,0,0,0,0,0,,
exact,eq_overshoot_sum,pretune_off,1,3,12,0,0,0,1,2,2,2,,
exact,eq_overshoot_sum,pretune_off,1,4,3,8,8,8,8,8,8,8,,
exact,eq_overshoot_sum,pretune_off,2,1,18,0,0,0,0,0,0,0,,
exact,eq_overshoot_sum,pretune_off,2,2,27,0,0,0,0,0,0.4,1,,
exact,eq_overshoot_sum,pretune_off,2,3,12,0,0,0.75,1.5,2,2.9,3,,
exact,eq_overshoot_sum,pretune_off,2,4,3,8,8,8,8,8,8,8,,
exact,eq_overshoot_sum,pretune_on,1,1,18,0,0,0,0,0,0,0,,
exact,eq_overshoot_sum,pretune_on,1,2,27,0,0,0,0,0,0,0,,
exact,eq_overshoot_sum,pretune_on,1,3,12,0,0,0.75,1.5,2,2,2,,
exact,eq_overshoot_sum,pretune_on,1,4,3,8,8,8,8,8,8,8,,
exact,eq_overshoot_sum,pretune_on,2,1,18,0,0,0,0,0,0,0,,
exact,eq_overshoot_sum,pretune_on,2,2,27,0,0,0,0,0,2.2,4,,
exact,eq_overshoot_sum,pretune_on,2,3,12,0,0,0.75,2,2.25,3,3,,
exact,eq_overshoot_sum,pretune_on,2,4,3,8,8,8,8,8,8,8,,
surrogate,final_stage,pretune_off,1,1,51,3,4,5,5,5,5,5,[5],[5]
surrogate,final_stage,pretune_off,1,2,57,5,5,5,5,5,5,5,"[null,null]","[5,5]"
surrogate,final_stage,pretune_off,1,3,18,5,5,5,5,5,5,5,"[null,null,null]","[5,5,5]"
surrogate,final_stage,pretune_off,1,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
surrogate,final_stage,pretune_off,2,1,51,2.5,4,5,5,5,5,5,[5],[5]
surrogate,final_stage,pretune_off,2,2,57,4.8,5,5,5,5,5,5,"[null,null]","[5,5]"
surrogate,final_stage,pretune_off,2,3,18,4.85,5,5,5,5,5,5,"[null,null,null]","[5,5,5]"
surrogate,final_stage,pretune_off,2,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
surrogate,final_stage,pretune_on,1,1,51,3,4,5,5,5,5,5,[5],[5]
surrogate,final_stage,pretune_on,1,2,57,5,5,5,5,5,5,5,"[null,null]","[5,5]"
surrogate,final_stage,pretune_on,1,3,18,4.7,5,5,5,5,5,5,"[null,null,null]","[5,5,5]"
surrogate,final_stage,pretune_on,1,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
surrogate,final_stage,pretune_on,2,1,51,2.5,4,5,5,5,5,5,[5],[5]
surrogate,final_stage,pretune_on,2,2,57,4.8,5,5,5,5,5,5,"[null,null]","[5,5]"
surrogate,final_stage,pretune_on,2,3,18,4,4.7,5,5,5,5,5,"[null,null,null]","[5,5,5]"
surrogate,final_stage,pretune_on,2,4,3,5,5,5,5,5,5,5,"[null,null,null,null]","[5,5,5,5]"
surrogate,n_levels,pretune_off,1,1,51,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_off,1,2,57,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_off,1,3,18,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_off,1,4,3,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_off,2,1,51,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_off,2,2,57,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_off,2,3,18,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_off,2,4,3,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,1,1,51,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,1,2,57,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,1,3,18,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,1,4,3,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,2,1,51,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,2,2,57,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,2,3,18,30,30,30,30,30,30,30,,
surrogate,n_levels,pretune_on,2,4,3,30,30,30,30,30,30,30,,
surrogate,total_loss_evals,pretune_off,1,1,51,93873.5,107303,154852.5,572604,1170969,1442336,2027831.5,,
surrogate,total_loss_evals,pretune_off,1,2,57,485915,552340,2068738,2638515,3260164,5245459.2,6004575.8,,
surrogate,total_loss_evals,pretune_off,1,3,18,2124021.55,2265125.7,2469183.75,3495154.5,5897571.25,6082300.3,6201221.15,,
surrogate,total_loss_evals,pretune_off,1,4,3,3832879.6,3852078.2,3909674,4005667,4044092,4067147,4074832,,
surrogate,total_loss_evals,pretune_off,2,1,51,52879.5,61580,103192.5,329613,1164600,1496203,1968278.5,,
surrogate,total_loss_evals,pretune_off,2,2,57,353263.6,456122.2,948768,1804049,2470835,5152457.8,6297893.8,,
surrogate,total_loss_evals,pretune_off,2,3,18,933260.25,1086978.1,1516820,3386797.5,4600808.5,6779155.5,7187386.95,,
surrogate,total_loss_evals,pretune_off,2,4,3,4258395.4,4334916.8,4564481,4947088,5192323,5339464,5388511,,
surrogate,total_loss_evals,pretune_on,1,1,51,34035,36186,127480,451546,1715955,2462060,2747751.5,,
surrogate,total_loss_evals,pretune_on,1,2,57,96769.8,117913.6,564293,2683316,4237850,5818139.8,5961232.2,,
surrogate,total_loss_evals,pretune_on,1,3,18,310270.8,530729.4,1220948.25,1915678,5116013.5,5564620.4,6067645.1,,
surrogate,total_loss_evals,pretune_on,1,4,3,1049007,1058577,1087287,1135137,2825439.5,3839621,4177681.5,,
surrogate,total_loss_evals,pretune_on,2,1,51,21640,24510,44640,728806,1899280,4842210,5644505,,
surrogate,total_loss_evals,pretune_on,2,2,57,80753.2,90066,362836,2029054,3756628,5635989.4,6377627.6,,
surrogate,total_loss_evals,pretune_on,2,3,18,330645.25,384014.6,680691.5,3218535.5,5599445.5,6703608.3,7449749.75,,
surrogate,total_loss_evals,pretune_on,2,4,3,1634215.5,1660601,1739757.5,1871685,2159753.5,2332594.6,2390208.3,,
surrogate,total_ode_solves,pretune_off,1,1,51,93873.5,107303,154852.5,572604,1170969,1442336,2027831.5,,
surrogate,total_ode_solves,pretune_off,1,2,57,485915,552340,2068738,2638515,3260164,5245459.2,6004575.8,,
surrogate,total_ode_solves,pretune_off,1,3,18,2124021.55,2265125.7,2469183.75,3495154.5,5897571.25,6082300.3,6201221.15,,
surrogate,total_ode_solves,pretune_off,1,4,3,3832879.6,3852078.2,3909674,4005667,4044092,4067147,4074832,,
surrogate,total_ode_solves,pretune_off,2,1,51,52879.5,61580,103192.5,329613,1164600,1496203,1968278.5,,
surrogate,total_ode_solves,pretune_off,2,2,57,353263.6,456122.2,948768,1804049,2470835,5152457.8,6297893.8,,
surrogate,total_ode_solves,pretune_off,2,3,18,933260.25,1086978.1,1516820,3386797.5,4600808.5,6779155.5,7187386.95,,
surrogate,total_ode_solves,pretune_off,2,4,3,4258395.4,4334916.8,4564481,4947088,5192323,5339464,5388511,,
surrogate,total_ode_solves,pretune_on,1,1,51,34035,36186,127480,451546,1715955,2462060,2747751.5,,
surrogate,total_ode_solves,pretune_on,1,2,57,96769.8,117913.6,564293,2683316,4237850,5818139.8,5961232.2,,
surrogate,total_ode_solves,pretune_on,1,3,18,310270.8,530729.4,1220948.25,1915678,5116013.5,5564620.4,6067645.1,,
surrogate,total_ode_solves,pretune_on,1,4,3,1049007,1058577,1087287,1135137,2825439.5,3839621,4177681.5,,
surrogate,total_ode_solves,pretune_on,2,1,51,21640,24510,44640,728806,1899280,4842210,5644505,,
surrogate,total_ode_solves,pretune_on,2,2,57,80753.2,90066,362836,2029054,3756628,5635989.4,6377627.6,,
surrogate,total_ode_solves,pretune_on,2,3,18,330645.25,384014.6,680691.5,3218535.5,5599445.5,6703608.3,7449749.75,,
surrogate,total_ode_solves,pretune_on,2,4,3,1634215.5,1660601,1739757.5,1871685,2159753.5,2332594.6,2390208.3,,
surrogate,total_parameter_fits,pretune_off,1,1,51,250,330,410,410,410,450,460,,
surrogate,total_parameter_fits,pretune_off,1,2,57,410,410,430,490,570,610,610,,
surrogate,total_parameter_fits,pretune_off,1,3,18,447,450,490,540,590,610,610,,
surrogate,total_parameter_fits,pretune_off,1,4,3,530,530,530,530,550,562,566,,
surrogate,total_parameter_fits,pretune_off,2,1,51,210,330,410,410,410,410,410,,
surrogate,total_parameter_fits,pretune_off,2,2,57,394,410,410,510,570,610,610,,
surrogate,total_parameter_fits,pretune_off,2,3,18,427,430,430,540,605,610,610,,
surrogate,total_parameter_fits,pretune_off,2,4,3,532,534,540,550,550,550,550,,
surrogate,total_parameter_fits,pretune_on,1,1,51,250,330,410,410,410,430,440,,
surrogate,total_parameter_fits,pretune_on,1,2,57,410,410,410,470,510,518,530,,
surrogate,total_parameter_fits,pretune_on,1,3,18,427,430,435,470,610,610,610,,
surrogate,total_parameter_fits,pretune_on,1,4,3,510,510,510,510,530,542,546,,
surrogate,total_parameter_fits,pretune_on,2,1,51,210,330,410,410,410,410,410,,
surrogate,total_parameter_fits,pretune_on,2,2,57,394,410,410,430,490,530,530,,
surrogate,total_parameter_fits,pretune_on,2,3,18,410,424,430,550,610,610,610,,
surrogate,total_parameter_fits,pretune_on,2,4,3,474,478,490,510,510,510,510,,
```

### T5 -- Robustness and failure modes

```csv
condition,system_representability,n_cells,success_true_cells,failure_reason_set_cells,total_diverged_solves_sum,total_diverged_solves_nonzero_cells,total_invalid_solves_sum,total_invalid_solves_nonzero_cells,total_nonfinite_solves_sum,total_nonfinite_solves_nonzero_cells,total_solver_unstable_solves_sum,total_solver_unstable_solves_nonzero_cells,total_step_limit_solves_sum,total_step_limit_solves_nonzero_cells,total_optimizer_limit_hits_sum,total_optimizer_limit_hits_nonzero_cells,total_optimizer_budget_stop_fits_sum,total_optimizer_budget_stop_fits_nonzero_cells,solver_retcodes_MaxIters_count,solver_retcodes_Success_count,solver_retcodes_Unstable_count,optimizer_retcodes_Failure_count,optimizer_retcodes_MaxLossEvals_count,optimizer_retcodes_Success_count
pretune_off,exact,120,120,0,7034272,102,7893964,102,0,0,7034272,102,859652,72,12579,112,4265,99,72,120,102,107,99,120
pretune_off,surrogate,258,258,0,20336833,255,21639859,255,0,0,20336833,255,1301902,159,47480,246,15772,212,159,258,255,241,212,258
pretune_on,exact,120,120,0,15553750,74,16212146,74,0,0,15553750,74,658396,44,18146,81,5087,66,44,120,74,75,66,117
pretune_on,surrogate,258,258,0,17434386,176,17771637,176,0,0,17434386,176,337251,109,58013,225,13558,144,109,258,176,225,144,243
```
