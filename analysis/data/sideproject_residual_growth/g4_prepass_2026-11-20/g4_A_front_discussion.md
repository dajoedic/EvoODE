# G4 pre-pass A — paper/wisp/wisp.tex lines 1–641 and 984–end (hand-typed numbers only)

Evidence state: Q9 interim + Q-B, build 2026-11-19 (`outputs/qb_paper_2026-11-19/`). "noisy" = sigma > 0. Read-only audit, 2026-11-20.

| line | number as printed | short context | source (file + filter/computation) | recomputed value | verdict |
|---|---|---|---|---|---|
| 113 | 63 systems; 1–5 % noise; half the samples | abstract, population | q9_cells/cells.csv: system_id nunique; sigma values; rho | 63; sigma ∈ {0.01..0.05}; rho ∈ {0, 0.5} | MATCH |
| 123 | median 2–10 trajectory fits per data set, dims 1–2 | abstract, cost | claims/cost.csv, n_candidates, noisy, dim1/2 exact/surrogate medians | 2, 3, 6, 10 | MATCH |
| 165 | path typically 2–10 models | intro | same as line 123 | 2, 3, 6, 10 | MATCH |
| 169 | 63-system benchmark, dims 1–4 | intro | cells.csv dim | 63 systems, dim 1–4 | MATCH |
| 272 | candidates median 2–19 | Fig. 1 box | claims/cost.csv, n_candidates, noisy, all strata | medians 2, 3, 6, 10, 12, 18.5, 18, 8, 18.5 → 2–18.5 | ROUNDING |
| 293 | p = 6, 12, 19, 27 for d = 1..4 | Fig. 1 caption | counted from Θ: 1 + d + d + C(d,2) + d + d + d | 6, 12, 19, 27 | MATCH |
| 313–314 | 30 of 63 exact; 33 surrogate | library | cells.csv drop_duplicates(system_id), representability | 30 exact, 33 surrogate | MATCH |
| 330 | 2,529 rows for n = 512 | weak design | Σ_L (512 − L), L ∈ {1,2,4,8,16} | 2,529 | MATCH |
| 384 | 509 of 936 equations end at the stop on noise-free cells | noise estimate | q9_paths.json, cells sigma == 0 (clean + sub), equation_paths.end_reason == 'floor' | 509 / 936 (full 333, no_gain 45, sse 44, cycle 5) | MATCH |
| 510 | LV coefficients 1.84, 1.45, 3.0, 1.62; 256 of 512; 5 % | worked example | paper/wisp/data/example.json truth, observed_t, sigma, rho | identical; 256 observed; σ 0.05, ρ 0.5 | MATCH |
| 511 | cubic terms x1^3, x0^3 and a constant first | worked example | example.json steps 1–3: u2^3, u1^3, 1 | identical | MATCH |
| 513 | x0x1 enters prey eq at state 6, predator at state 10 | worked example | example.json steps: term 6 (u1*u2) in eq0 at step 6, eq1 at step 10 | 6 and 10 | MATCH |
| 515–516 | state 11 = truth; stop statistic 3.4 and 1.2 | worked example | example.json step 11 support [[u1,u1*u2],[u2,u1*u2]], max_ratio 3.39 / 1.15 | 3.39, 1.15 | MATCH |
| 516 | eleven candidates; BIC margin > 1,600 | worked example | example.json candidates (11), traj_bic q7_011 −2251.9 vs next best q7_008 −549.7 | 11; margin 1,702 | MATCH |
| 517 | coefficients deviate ≤ 1.3 % | worked example | q7_011 params vs truth: 1.8481/1.84, 1.4684/1.45, 2.9834/3.0, 1.6246/1.62 | max 1.27 % | MATCH |
| 518 | R² = 0.989 unseen IC | worked example | q7_011 gen_r2 | 0.98902 | MATCH |
| 519 | WSINDy 14 terms, R² = −5.0 | worked example | example.json ws_coef (14 entries), ws_rec | 14; −5.005 | MATCH |
| 530/535 | 256 of 512, 5 %, eleven candidates | Fig. 2 caption | example.json | as above | MATCH |
| 546 | 63 systems, two ICs each | data | cells.csv initial_condition_set | 63 × 2 | MATCH |
| 551–552 | 51 of dim 1–2 (21 exact, 30 surrogate); twelve of dim 3–4 | data | cells.csv per system: dim1 11/12, dim2 10/18, dim3 8/2, dim4 1/1 | 51 (21/30); 12 | MATCH |
| 553–556 | 10 noisy conditions; 60 data sets per system (10×3×2) | data | cells.csv sigma>0 groupby system_id size | 60 for every system | MATCH |
| 557 | 4,284 data sets | data | cells.csv rows; build_metadata.json cells | 4,284 | MATCH |
| 572–573 | 13 thresholds; 2 thresholds for first library | references | build_metadata reference_rows: B1 55,692 = 4,284 × 13; WP-N47 8,568 = 4,284 × 2 | 13; 2 | MATCH |
| 576–577 | 7 τ values; no dim 4 | WeakIdent | reference_rows weakident 29,036 = 7 × (4,284 − 136 dim-4 cells) | 7 τ, dim 4 absent | MATCH |
| 580–581 | four configurations, three repetitions | ODEFormer | reference_cells.csv B3 configs (beam10/50 × opt/noopt); 17,136 = 4 × 4,284; repetitions already averaged in the file; 3 reps only in CLAUDE.md (B3 merge 54,432) | 4 configs; reps not re-checked in data | MATCH (configs) / DOC-ONLY (reps) |
| 582 | ODEFormer trained up to 10 % noise, half samples removed | references | literature statement | — | DOC-ONLY |
| 592 | 10,000 resamples | statistics | claims/metadata.json bootstrap | 10,000 | MATCH |
| 594 | four primary tests | statistics | claims/primary.csv P1–P4 | 4 | MATCH |
| 605 | margin 5 pp | pre-registration | q7_decision_inputs.csv, q8_decision_inputs.csv margin_pp | 5 | MATCH |
| 606 | cap of six terms per equation | pre-registration | q9_paths.json key states_beyond_6; CLAUDE.md | 6 | DOC-ONLY |
| 607 | better by 14–17 points on structure | Q7 vs Q5 | q7_grid/q7_decision_inputs.csv pruned_exact difference_pp dim1/dim2 | +14.24 / +16.83 (dim3 feasible −1.67, not "better") | MATCH |
| 612 | dim-1 generalization 5.7 points lower under wider bound | declared deviation | q8_decision_inputs.csv R2 dim1_exact gen C1000 57 vs C10 62 of 88 | 5.68 pp | MATCH |
| 612 | one cell beyond the margin | declared deviation | 5 pp × 88 = 4.4 cells allowed, difference 5 | 5 vs ≤ 4 | MATCH |
| 613 | three systems, wrong under both bounds | declared deviation | q8_units.csv dim1_exact noisy, C10 vs C1000 discordant gen cells: systems 3, 12, 17; pruned_exact False in both arms | 3 systems | MATCH |
| 614 | structure identical in every decided stratum | declared deviation | q8_decision_inputs R2 pruned_exact 40/40, 36/36 | identical | MATCH |
| 614–615 | six of eight 3-D systems infeasible under [−10,10] | declared deviation | strogatz_extended.json: 54 (12), 55 (99.96), 56 (28), 57–59 (5·5.7 = 28.5) > 10; 52, 61 ≤ 10 | 6 of 8 | MATCH |
| 621 | nine claims | pre-registration | claims/claims.csv C1–C9; Q9-A protocol table | 9 | MATCH |
| 621 | two further protocols | pre-registration | docs Q9 + Q9-A | 2 | DOC-ONLY |
| 632–633 | 4,280 of 4,284; four missing are σ = 0, ρ = 0.5 | preliminary box | build_metadata complete_cells; claims/missing.csv | 4,280; 4 missing, all σ 0 / ρ 0.5 | MATCH |
| 1005 | ODEFormer 41 % of 1-D structures on clean data, no more under noise | discussion | reference_cells.csv B3, dim1 exact, clean (σ 0, ρ 0) cluster mean, best config; claims/rates.csv | clean 40.9 %; noisy 41.7 % | MATCH |
| 1016–1017 | in about half of the data sets the truth never on the path | discussion C7 | wisp_choices.csv size_rule c, noisy, exact, dim ≤ 2: truth_on_path False | 670 / 1,260 = 53.2 % | MATCH |
| 1025 | replacing the cap shortened the paths by half | discussion | Q7 vs Q5 noisy candidates: q7_grid/q7_cost.csv vs q5_grid/q5_candidates.csv medians; q7_diagnostics vs q7_q5_diagnostics sums | medians 8→2 (dim1), 16→6 (dim2), 24→12 (dim3 feas.), 41→8 (dim4); sums to 35 % (dim1), 42 % (dim2), 60 % (dim3), 20 % (dim4), pooled 40 % of Q5 | MISMATCH (understated: shortened by 58–75 % on dim 1/2) |
| 1026 | 14–17 points | discussion | as line 607 | +14.2 / +16.8 | MATCH |
| 1040 | 33 of 63 without exact representation | limitations | cells.csv | 33 | MATCH |
| 1044 | liberal by a factor of 5–30 | limitations | stop_calibration/rates.csv N1_hat_6.635, subset all, vs nominal 1 % | dim1 5.2 %, dim2 13.1 %, dim3 feas. 23.4 %, dim3 infeas. 29.4 % → ×5–29; dim4 2.6 % (×2.6) not covered | ROUNDING |
| 1048 | 18 % of missing true terms stay below threshold, dim 1 | limitations | stop_calibration/rates.csv dim1 all P1_hat_6.635 = 0.825 | 17.5 % | MATCH |
| 1050 | 47.3 % vs 44.7 % (abs-penalty rule vs BIC, dim-2 structure) | limitations | paper/wisp/data/size_rules_exact_C1000.csv noisy dim2_exact, rule b vs rule c (c = BIC, matches \WispDimOneExactStructNoisy 40.6) | 47.33 / 44.67 | MATCH |
| 1052 | ablations: two noise levels, one realization | limitations | q8_units.csv no_foba/random_start/no_refit: sigma {0.01, 0.05} (+ clean), realization {1} | 2 levels, 1 realization | MATCH |
| 1052–1053 | dims 3 and 4 on twelve systems | limitations | cells.csv | 12 | MATCH |
| 1063 | 1–5 % noise | conclusions | cells.csv sigma | 0.01–0.05 | MATCH |
| 1100 | about 2,530 rows | appendix | as line 330 | 2,529 | MATCH |
| 1137–1138 | 30 exactly representable systems; σ 0.01–0.05, ρ {0, 0.5}, three realizations | calibration appendix | stop_calibration/rates.csv: n_true_pairs/strata; 30 exact systems in cells.csv | consistent (dim1–4 exact) | MATCH |
| 229 | EvoGrow: hundreds of nonlinear fits per data set | related work | CLAUDE.md (median 410 fits per cell, Phase B) | — | DOC-ONLY |
