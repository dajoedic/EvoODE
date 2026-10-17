# REPORT WP-FA2

Implemented the frozen Q1/Q2 protocol in analysis/scripts/aggregate/run_sideproject_residual_growth.py with --repo-root and --output-dir. Existing result files are refused. No Git commands, staging, commits, campaigns, Julia calls, or changes to existing source files were made. CURRENT_TASK.md was not edited.

Specification: docs/sideproject_residual_growth_protocol.md, protocol commit e61f48f. No conflicting thresholds or algorithm requirements were found between the task and scientific protocol. The standing CODEX_PROTOCOL.md imposes a 15-minute elapsed limit, stricter than the task's 30-minute progress estimate; the script enforces both. The full analysis was run once with defaults, with no adjustment after results.

The script imports phasec_basis, evaluate_basis, build_design, load_exported_trajectories, verify_basis_consistency, and load_exact_supports from the unchanged term_relevance module. build_design evaluates the canonical basis internally. Inventory classification, stratum mapping, and read-only HEAD resolution reuse the existing WP-FA1 helpers; importing them does not load their registry.

Each uncentred design is column-scaled and its augmented matrix [A,b] is compressed by QR. Every subset fit uses numpy.linalg.lstsq (SVD) on this orthogonally transformed design, retaining the transformed target's perpendicular component. No Gram matrix or normal equations are formed. SSE is computed as a residual squared norm. Ties use exact floating-point equality, without a new tolerance: lowest basis index for forward selection/removal and worst rank for truth in Q1. The best competing Q1 subset breaks SSE ties lexicographically by basis indices.

Q2 uses the oracle number of additions, including zero. Backward elimination runs even for initial supersets with no additions. Q2a is vacuously true for m=0; R2 and R3 count only addition-needing units. R3 compares G+B and F0 counts on the same Q2 units: an F0 result is repeated for each distinct S0 of a trajectory equation. This preserves the specified Q2 counting unit instead of comparing a structure-unit count to a deduplicated trajectory count. R4 is the pairwise AUC with half credit for ties. Secondary rho-prime AUC and OMP counts accompany each summary row. R1 is repeated across kinds because Q1 is independent of S0.

## Input fields checked against actual files

The actual first inventory record has run_id=5_evogrow_v2_2_stage_capped_1_1_7, system_id=1, system_dim=1, seed=7, initial_condition_set=1, stratum=dim1, equation_index=1, kind=raw, class=exact, n_true=2, missing=0, extra=0, needs_add=False, needs_remove=False, missing_terms=[], extra_terms=[]. There is no S0 column. Each starting set is reconstructed as (truth minus missing_terms) union extra_terms and checked against the existing class/count fields. Tests derive the inventory error fixture from the actual inventory, modifying one real pruned exact row's missing count.

| Input field | Origin and use |
|---|---|
| run_id | Existing inventory; cell identity and collapse controls |
| system_id | Existing inventory and support JSON; join |
| system_dim | Existing inventory; checked against support dim |
| initial_condition_set | Existing inventory and trajectory manifest; IC identity |
| equation_index | Existing inventory, 1-based; support equation identity |
| kind | Existing inventory; raw or pruned |
| stratum | Existing inventory; checked against existing WP-FA1 stratum helper |
| class | Existing inventory; checked and exported as wp_fa1_class |
| n_true | Existing inventory; checked against true support size |
| missing | Existing inventory; checked against reconstructed start |
| extra | Existing inventory; checked against reconstructed start |
| needs_add | Existing inventory; checked against missing count |
| needs_remove | Existing inventory; checked against extra count |
| missing_terms | Existing inventory JSON list; reconstruction and output |
| extra_terms | Existing inventory JSON list; reconstruction and output |
| representability | Existing support JSON; exact selection |
| status | Existing support JSON; ok selection |
| dim | Existing support JSON; basis dimension |
| support_terms | Existing support JSON; true sets |
| support_idxs | Existing support JSON; basis consistency check (1-based) |
| basis_name | Existing support JSON; loader and canonical basis checks |
| time_path | Existing trajectory manifest; time binary path |
| state_path | Existing trajectory manifest; state binary path |
| time_sha256 | Existing trajectory manifest; verified by loader |
| state_sha256 | Existing trajectory manifest; verified by loader |
| dtype | Existing trajectory manifest; verified by loader |
| byte_order | Existing trajectory manifest; verified by loader |
| time_axis_order | Existing trajectory manifest; verified by loader |
| state_axis_order | Existing trajectory manifest; verified by loader |
| time_shape | Existing trajectory manifest; binary reshape |
| state_shape | Existing trajectory manifest; binary reshape |

All remaining output fields are newly derived analysis fields, not claimed as existing record fields: s0, cells_collapsed, k_star, subset_count, q1_rank, truth_sse, best_other_sse, best_other_terms, q1b, b_norm2, condition_number, m, random_addition_probability, g_added_terms, g_q2a, g_first_missing_ranks, g_final_terms, g_q2b, omp_added_terms, omp_q2a, omp_first_missing_ranks, omp_final_terms, omp_q2b, f0_terms, f0_exact, sse0, best_addition_reduction, rho, rho_prime. Summary numerator/denominator/value/threshold/passed/decision and the named counts, AUC diagnostics, and condition-number extrema are computed from those unit outputs.

## Controls and verification

- 30 exact systems passed basis consistency; trajectory hashes passed for 60 trajectories, using only the permitted export.
- 118 unique Q1 units; 24,306 subsets enumerated, with each unit's count independently checked against its binomial coefficient.
- 508 unique Q2 units: 251 pruned and 257 raw. Each kind collapses 354 equation records; source inventory has 708 equation records from 180 cells.
- Every Q2 trajectory-equation identity exists in Q1. Duplicate Q2 start identities are absent. Inventory classes/counts and pruned exact S0 equality passed.
- rules_by_stratum.csv: 40 rows; by_system.csv: 240 rows. Both nonprimary strata carry decision=reported_only.
- python -m pytest analysis/tests/test_sideproject_residual_growth.py -q: 8 passed, 15,174 warnings, 4.38 s.
- python analysis/scripts/aggregate/run_sideproject_residual_growth.py: exit 0, exactly one default run.
- python -m pytest analysis/tests -q: 168 passed, 2 failed, 237,740 warnings, 55.02 s. The only failures are the two pre-existing failures identified in the task: test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts and test_t2a_candidate_priors.py::test_build_priors_from_minimal_real_shape_fixture. They were not modified.
- Independent artifact audit: exit 0; identity joins, collapse sums, binomial counts, row counts and reported-only decisions passed.

Targeted tests cover exact sparse recovery, full enumeration count, Q1 ties against truth, index tie breaks, correlated-column G/OMP disagreement, AUC ties, backward elimination for m=0 supersets, QR/raw-SSE equivalence on a conditioned synthetic design, six real-data empty-G/F0 consistency checks, and an inventory error derived from a real record.

The shell tool could not start because of helper setup-refresh errors. Python commands ran successfully through Node child_process. Numeric-library thread counts were fixed to one for the executed commands; no scientific settings were changed. Logs: WP_FA2_targeted_tests.log, WP_FA2_full_run.log, WP_FA2_analysis_tests.log, WP_FA2_artifact_audit.log, alongside this report.

## Outputs and provenance

All five requested outputs are in analysis/data/sideproject_residual_growth/. run_metadata.json contains hashes for the support, inventory, scientific protocol, imported term_relevance implementation, trajectory manifest and all selected trajectory binaries. Git HEAD is read directly from ref files without a Git operation.

Recorded HEAD: 3f4c008c7ce6056d899a44baf94766257b90e6fa. Analysis runtime: 5.102783999987878 seconds (through metadata construction, excluding final CSV writes).

## Rules table exactly as produced

```csv
stratum,kind,rule,numerator,denominator,value,threshold,passed,decision,q1_units,q2_units,addition_units,negative_units,f0_exact_count,omp_q2a_count,omp_q2b_count,rho_prime_auc_numerator,rho_prime_auc_denominator,rho_prime_auc,condition_number_min,condition_number_max
dim1,pruned,R1,22.0,22,1.0,0.8,True,pass,22,24,9,15,4,2,2,135.0,135,1.0,53.94678740210828,306746147883886.25
dim1,pruned,R2,9.0,9,1.0,0.7,True,pass,22,24,9,15,4,2,2,135.0,135,1.0,53.94678740210828,306746147883886.25
dim1,pruned,R3,9.0,9,9.0,4.0,True,pass,22,24,9,15,4,2,2,135.0,135,1.0,53.94678740210828,306746147883886.25
dim1,pruned,R4,135.0,135,1.0,0.8,True,pass,22,24,9,15,4,2,2,135.0,135,1.0,53.94678740210828,306746147883886.25
dim1,raw,R1,22.0,22,1.0,0.8,True,pass,22,22,7,15,3,2,2,105.0,105,1.0,53.94678740210828,306746147883886.25
dim1,raw,R2,7.0,7,1.0,0.7,True,pass,22,22,7,15,3,2,2,105.0,105,1.0,53.94678740210828,306746147883886.25
dim1,raw,R3,7.0,7,7.0,3.0,True,pass,22,22,7,15,3,2,2,105.0,105,1.0,53.94678740210828,306746147883886.25
dim1,raw,R4,105.0,105,1.0,0.8,True,pass,22,22,7,15,3,2,2,105.0,105,1.0,53.94678740210828,306746147883886.25
dim2,pruned,R1,40.0,40,1.0,0.8,True,pass,40,72,22,50,14,4,4,972.0,1100,0.8836363636363637,10.605518224957219,26761236370.75118
dim2,pruned,R2,19.0,22,0.8636363636363636,0.7,True,pass,40,72,22,50,14,4,4,972.0,1100,0.8836363636363637,10.605518224957219,26761236370.75118
dim2,pruned,R3,19.0,22,19.0,14.0,True,pass,40,72,22,50,14,4,4,972.0,1100,0.8836363636363637,10.605518224957219,26761236370.75118
dim2,pruned,R4,1100.0,1100,1.0,0.8,True,pass,40,72,22,50,14,4,4,972.0,1100,0.8836363636363637,10.605518224957219,26761236370.75118
dim2,raw,R1,40.0,40,1.0,0.8,True,pass,40,80,22,58,14,4,4,1141.0,1276,0.8942006269592476,10.605518224957219,26761236370.75118
dim2,raw,R2,19.0,22,0.8636363636363636,0.7,True,pass,40,80,22,58,14,4,4,1141.0,1276,0.8942006269592476,10.605518224957219,26761236370.75118
dim2,raw,R3,19.0,22,19.0,14.0,True,pass,40,80,22,58,14,4,4,1141.0,1276,0.8942006269592476,10.605518224957219,26761236370.75118
dim2,raw,R4,1276.0,1276,1.0,0.8,True,pass,40,80,22,58,14,4,4,1141.0,1276,0.8942006269592476,10.605518224957219,26761236370.75118
dim3_feasible,pruned,R1,12.0,12,1.0,0.8,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_feasible,pruned,R2,22.0,30,0.7333333333333333,0.7,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_feasible,pruned,R3,22.0,30,22.0,15.0,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_feasible,pruned,R4,30.0,30,1.0,0.8,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_feasible,raw,R1,12.0,12,1.0,0.8,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_feasible,raw,R2,22.0,30,0.7333333333333333,0.7,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_feasible,raw,R3,22.0,30,22.0,15.0,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_feasible,raw,R4,30.0,30,1.0,0.8,True,pass,12,31,30,1,15,6,6,28.0,30,0.9333333333333333,213.40579187292164,3930758808850061.5
dim3_bound_infeasible,pruned,R1,36.0,36,1.0,0.8,True,reported_only,36,105,60,45,24,8,8,2447.0,2700,0.9062962962962963,148.0889596260537,145350135.412027
dim3_bound_infeasible,pruned,R2,53.0,60,0.8833333333333333,0.7,True,reported_only,36,105,60,45,24,8,8,2447.0,2700,0.9062962962962963,148.0889596260537,145350135.412027
dim3_bound_infeasible,pruned,R3,53.0,60,53.0,24.0,True,reported_only,36,105,60,45,24,8,8,2447.0,2700,0.9062962962962963,148.0889596260537,145350135.412027
dim3_bound_infeasible,pruned,R4,2700.0,2700,1.0,0.8,True,reported_only,36,105,60,45,24,8,8,2447.0,2700,0.9062962962962963,148.0889596260537,145350135.412027
dim3_bound_infeasible,raw,R1,36.0,36,1.0,0.8,True,reported_only,36,105,60,45,24,8,8,2438.0,2700,0.902962962962963,148.0889596260537,145350135.412027
dim3_bound_infeasible,raw,R2,53.0,60,0.8833333333333333,0.7,True,reported_only,36,105,60,45,24,8,8,2438.0,2700,0.902962962962963,148.0889596260537,145350135.412027
dim3_bound_infeasible,raw,R3,53.0,60,53.0,24.0,True,reported_only,36,105,60,45,24,8,8,2438.0,2700,0.902962962962963,148.0889596260537,145350135.412027
dim3_bound_infeasible,raw,R4,2700.0,2700,1.0,0.8,True,reported_only,36,105,60,45,24,8,8,2438.0,2700,0.902962962962963,148.0889596260537,145350135.412027
dim4,pruned,R1,8.0,8,1.0,0.8,True,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
dim4,pruned,R2,11.0,17,0.6470588235294118,0.7,False,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
dim4,pruned,R3,11.0,17,11.0,8.0,True,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
dim4,pruned,R4,34.0,34,1.0,0.8,True,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
dim4,raw,R1,8.0,8,1.0,0.8,True,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
dim4,raw,R2,11.0,17,0.6470588235294118,0.7,False,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
dim4,raw,R3,11.0,17,11.0,8.0,True,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
dim4,raw,R4,34.0,34,1.0,0.8,True,reported_only,8,19,17,2,8,0,0,22.0,34,0.6470588235294118,4.179285326782367e+16,4.268811388142221e+16
```
