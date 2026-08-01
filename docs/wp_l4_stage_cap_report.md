# WP-L4 Stage Cap Report

Generated: 2026-07-31.

## Part A: Identifiability Disambiguation

`studies/lookahead/floor_gated_probe.jl` now separates two properties that were both
previously described as non-identifiable:

- `lower_stage_indistinguishable`: a lower-stage library already reaches the Richardson
  noise floor along the observed trajectory.
- `rank_deficient_at_expected_stage` / `rank_deficient_at_tested_stage`: a design matrix
  is rank-deficient or too ill-conditioned at the stage being assessed.

Rank deficiency is recorded per tested stage. A later rank-deficient stage no longer makes
an equation undecidable if the equation is still decidable up to the highest well-conditioned
stage it actually needs.

Regenerated WP-L3 outputs:

- `outputs/studies/lookahead/floor_gated_probe/stage_profiles_by_rule.csv`
- `outputs/studies/lookahead/floor_gated_probe/identifiability.csv`
- `outputs/studies/lookahead/floor_gated_probe/density_sweep.csv`
- `outputs/studies/lookahead/floor_gated_probe/summary.json`
- `outputs/studies/lookahead/floor_gated_probe/report.md`

Corrected main floor-gated confusion, local_poly + richardson_wls + ols:

- exact: 12
- over: 0
- under: 4
- rank_deficient: 0
- invalid_or_inconclusive: 0

The previous headline `10 exact / 0 over / 2 under / 4 not-identifiable` changes to
`12 exact / 0 over / 4 under / 0 rank_deficient`.

Identifiability counts over the 16 exact equations:

- lower-stage indistinguishable: 3
- rank-deficient at expected stage: 2
- both properties: 1

## Part B: Capped Variant

Implemented new variant slug:

- `evogrow_v3_stage_capped`

The variant uses `EvoGrowStageCapped`, which computes `max_useful_stage_k` once before
search from only:

- observed trajectory
- staged basis
- equation index
- tested stage
- ordinary threshold hyperparameters

Ground truth does not enter the cap API. The cap computation has no arguments for
`expected_terms`, `expected_stage`, `true_rhs!`, system id, or benchmark tables.

Behavior:

- undecidable equations receive `nothing` and remain uncapped;
- a cap below the current equation stage does not remove terms or lower the stage;
- the cap is only an upper bound on future promotion;
- all existing promotion criteria must still fire before an uncapped or under-cap equation
  can promote.

System 26 cap-only check:

- `estimate_stage_caps(...) == [3, 3]`

This was a construction check only. The decisive System 26 search was not run.

The new regression config fingerprint is:

- `3f9be6d36c4043de`

`studies/regression/history.jsonl` was not modified by this work package.

## Verification

Commands run:

```powershell
julia --project=. --% -e "using EvoODE; println(\"load ok\")"
julia --project=. test/test_stage_cap.jl
julia --project=. test/test_evogrow_v3_childgen.jl
julia --project=. test/test_gate2_do_or_die.jl
julia --project=. test/test_regression_runner_gate2.jl
julia --project=. studies/lookahead/floor_gated_probe.jl
```

Additional targeted checks:

- `test/test_stage_cap.jl` verifies data-only cap API equivalence with withheld truth,
  promotion blocking, no forced promotion, uncapped equations, conservative cap-below-current
  behavior, a cheap capped smoke path, and bit-identity for `EvoGrowV3` with cap disabled.
- `test/test_evogrow_v3_promote.jl` passed when run before the isolated test rerun; the
  combined multi-include command later hit a test-module ambiguity unrelated to this change,
  so the affected tests were rerun separately.
- `studies/regression/history.jsonl` diff was empty.

## Decisive Run Command

Run this externally to start the pre-registered decisive cell:

```powershell
$env:EVO_REGRESSION_VARIANT = "evogrow_v3_stage_capped"
$env:EVO_REGRESSION_SYSTEM_ID = "26"
$env:EVO_REGRESSION_SEED = "42"
julia --project=. studies/regression/run_regression.jl
```

After completion, run:

```powershell
julia --project=. studies/gate2_do_or_die/readout.jl
```

