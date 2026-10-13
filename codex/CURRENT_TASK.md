# WP-T2a-impl-b — two defects found in Claude's controls of WP-T2a-impl
**Language: Julia**

## Why

Claude ran the WP-T2a-impl control plan (`codex/reports/REPORT_WP_T2A_IMPL.md`). Results:

- **Bit-identity without prior: passed, 3 of 3** (C-1 cells 1, 277, 633; `loss`, `support_terms`, `model_terms`,
  `total_loss_evals`, `config_fingerprint = 0c9672de35c75a9d` identical). `test/test_stage_cap.jl` and
  `test/test_evogrow_v3_childgen.jl` pass.
- **Defect 1 — manifest builder.** `julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl
  --paper2-t2a-pilot --output experiments/paper2_t2a_pilot_v1/manifest.csv` fails with
  `LoadError: Phase C manifest identities are not unique` (`generate_phase_c_manifest.jl`, `main`). The identity used
  for the uniqueness check does not include the prior arm, so the `oracle_prior` and `guided_prior` rows of the same
  system / seed / IC collide. Consequently the oracle smoke (T2a manifest index 67) could not run.
- **Defect 2 — test construction.** `test/test_candidate_prior.jl`, testset "Phase C fingerprint remains unchanged
  without prior and prior payload changes identity", `include`s `studies/regression/run_regression.jl` inside the
  `@testset`. That script includes `src/EvoODE.jl` (a `module` definition), which Julia allows only at top level →
  `LoadError` at `run_regression.jl:14`. The other testsets in the file were not reached or not reported.

## Deliverables

1. Fix the T2a manifest identity so that it includes the prior arm (and whatever else distinguishes T2a rows), while
   the **Phase C manifest identity and its uniqueness check stay exactly as they are** for the non-T2a path. The
   regenerated Phase C manifest must be byte-identical to `experiments/paper1_phaseC_v1/manifest.csv` — say in the
   report how Claude verifies that (command).
2. Fix the test: move the script `include`s to top level (or another construct that keeps them at top level), keep the
   assertions unchanged. The file must run start to finish under
   `julia --project=. --startup-file=no test/test_candidate_prior.jl`.
3. Report `codex/reports/REPORT_WP_T2A_IMPL_B.md` with the exact commands Claude must run: the test file, the Phase C
   manifest byte-identity check, the T2a manifest generation with its expected counts (252 rows, 126 per arm, 20 S1
   indices), and the oracle smoke with its pass criteria (unchanged from WP-T2a-impl).

## Verboten

- Any change to search behaviour, the prior sampler, the prior files, the Phase C identity semantics or the C-1
  configuration. Running Julia (not possible here). Committing. Editing this file.

## Abnahme

- Code and test changed as above; report with commands; `STATUS.md` `done` (Julia not executed) or `blocked`.
