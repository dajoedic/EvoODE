# WP-T2a-impl — candidate prior for EvoGrow (oracle and guided), behaviour-neutral by default, S1 manifest
**Language: Julia** (plus a small Python generator)

## Why

Paper 2, step 4 (`docs/phd_thesis_arc.md` §5, "Step 4 — frozen 2026-10-13") — **read that section in full; it is the
specification**. EvoGrow draws every new basis term uniformly (`rand(candidates)`). The pilot asks whether an
equation-specific prior over candidate terms improves support recovery. Three arms: control = C-1 itself (no new run),
**oracle prior**, **guided prior**. Frozen: `P(φ_j) = (1−ε)·P_rank(φ_j) + ε·P_uniform(φ_j)`, **ε = 0.2**,
**P_rank ∝ 1/rank**. The first run (S1) is the oracle arm only, dim 2, seed 42, both IC sets: 20 cells.

P-04 (2026-10-13, `DIARY.md`) is the reason the stop rule is evaluated only on fittable cells; that is evaluation, not
part of this package.

## Deliverables

### 1. Prior hook in the search (Julia, `src/`)

- A new optional configuration on `EvoGrow` (e.g. a `candidate_prior` field, default `nothing`) carrying, **per
  equation**, a full ranking of the basis term indices (rank 1 = most preferred), plus ε. Validate on construction:
  every equation has a ranking that is a permutation of the full basis term set of that dimension.
- **Every** draw of a basis term for an equation on the **C-1 code path** uses the prior when it is set: population
  initialisation and all child-generation draws that pick a term out of a candidate set. Find them yourself — they
  include `_init_population` and `_expand*` in `src/structure/evogrow.jl` and the child generation in
  `src/structure/evogrow_v3_childgen.jl` that `evogrow.jl` calls (`_expand_equation_aware_with_usage_policy`). List
  every site you changed in the report, and every `rand` call you deliberately left uniform (the equation choice
  `rand(1:dim)`, the usage-policy coin flips) with the reason.
- The draw probability over the **current** candidate set `C` (which changes with stage, existing terms and caps):
  `w_j = 1/rank_j` from the full-basis ranking of that equation, `P_rank(j) = w_j / Σ_{i∈C} w_i`,
  `P(j) = (1−ε)·P_rank(j) + ε/|C|`. One draw from that categorical distribution with the same RNG stream the search
  already uses.
- **Behaviour-neutral default (hard requirement):** with `candidate_prior = nothing` the code path must call exactly the
  same `rand` functions on exactly the same arguments in the same order as today, so that C-1 is reproduced
  bit-identically. Do not route the uniform case through the weighted sampler.
- When the prior is active, its content enters the configuration fingerprint (the ranking per equation, ε, the
  mapping name `harmonic`, the prior source tag and the source file hash); when it is `nothing`, the fingerprint must be
  unchanged (`0c9672de35c75a9d` for the Phase C configuration). Records carry the prior fields
  (`candidate_prior_arm`, ε, mapping, per-equation ranking, source hash) or explicit nulls.
- Tests (`test/test_candidate_prior.jl`): validation errors; the weighted sampler's empirical frequencies over many
  draws match the formula within a tolerance for a fixed seed; a term not in `C` is never drawn; ε = 1 gives the uniform
  frequencies; fingerprint unchanged without a prior; fingerprint changes with it.

### 2. Prior files (Python, `analysis/scripts/aggregate/build_t2a_candidate_priors.py`)

- Source: `analysis/data/wp_t1_term_relevance/records.csv`, rows with `signal == "weak"`,
  `ranking_method == "forward"`, `sigma_rel == 0`, `basis_name == "staged_polynomial_basis_with_constant"`, and
  `ic_strategy` `ic1` or `ic2` (one ranking per system × IC × equation; the training trajectory of a cell is its own IC).
  Do **not** use `ic1_ic2` rows. Check that `trajectory_sha256` equals the C-1 training-trajectory hash of that system
  and IC (state hash from the Phase C export used by WP-C4c / the campaign; find the source and name it); refuse on
  mismatch.
- **guided** ranking = `candidate_ranks` as recorded (map `candidate_names` to the Julia basis term indices by name;
  refuse if any name does not map).
- **oracle** ranking = the true support terms of that equation first, ordered among themselves by their guided rank,
  then all other terms in guided order. True support from `studies/regression/phase_c_support.json`.
- Output: one JSON per arm × system × IC under `experiments/paper2_t2a_pilot_v1/priors/` with the per-equation
  rankings, source file SHA-256, row identifiers, and the arm tag. Tests for the oracle construction and the
  name-mapping refusal.

### 3. Campaign path (Julia, `studies/regression/`)

- A new experiment `paper2_t2a_pilot_v1`: manifest builder and runner entry reusing the Phase C C-1 configuration
  **unchanged** (variant `evogrow_v2_2_stage_capped`, `pretuning = false`, `max_fit_attempts = 3`, bound 10, stage cap
  policy, canonical basis, clean data, same trajectories), adding only the prior loaded from the JSON of the cell's arm,
  system and IC. Arms: `oracle_prior`, `guided_prior`. Cells: the 21 exact systems of dim 1 and 2, seeds 42/123/7, both
  IC sets (126 per arm), with an index list **for S1 only**: arm `oracle_prior`, dim 2, seed 42, both IC sets
  (20 cells). Records written like Phase C records, including all duplicate/confounder counters that C-1 records
  already carry.
- `k8s/paper2_t2a_s1_job.yaml`: indexed Job over the S1 index list, **`parallelism: 8`** (Orion limit: 40 cores in
  total for EvoODE, 32 are taken by C-6), 1 CPU / 2 Gi per pod like C-1, **no `activeDeadlineSeconds`**, image
  placeholder `<COMMIT_SHA>`, header comment with the expected cost (~200 core hours, ~9.8 h per dim-2 cell from C-1;
  capacity planning, not evidence).

### 4. Control plan for Claude (Codex cannot run Julia)

Write into the report the exact commands Claude must run, and the pass criteria:

- the new tests and the existing `test/test_stage_cap.jl` (and any other test file touching the changed code);
- **bit-identity without prior** (hard stop): re-run through the **new** code path with `candidate_prior = nothing`
  the C-1 cells system 1 seed 42 IC 1, system 24 seed 42 IC 1, and the cheapest dim-3 C-1 cell (pick it from
  `experiments/paper1_phaseC_v1/run_registry.csv` by `total_loss_evals`; name it) and compare `loss`, `support_terms`,
  `model_terms`, `total_loss_evals`, `config_fingerprint` against the C-1 records;
- a laptop smoke of the oracle arm on system 24 seed 42 IC 1 (one cell, dim 2's cheapest), showing that the prior is
  loaded, recorded and changes the draws.

### 5. Docs

`SCRIPTS.md` entries for the prior generator, the manifest builder, the controls and the S1 Job; report
`codex/reports/REPORT_WP_T2A_IMPL.md`.

## Verboten

- Changing anything on the uniform path that alters C-1 behaviour; changing ε, the mapping, the arms, the cells or any
  C-1 configuration value.
- Pruning candidates (soft guidance only; every term must stay reachable).
- Any other search change (stage policy, usage policy, population carry-over, stage cap, optimizer, restarts).
- Touching `evogrow_v3.jl` behaviour beyond what a shared helper change forces; if a shared helper changes, say so.
- Running Julia (you cannot here) — write the code, the tests and the control commands; report `blocked` only if
  something in §5 Step 4 is contradictory, otherwise `done` with "Julia not executed".
- Looking at C-6 EvoGrow results. Committing. Editing this file.

## Abnahme

- Python tests for the generator pass; the generator has produced the prior JSONs for all 21 systems × 2 ICs × 2 arms.
- Julia code, tests, manifest builder, runner entry and the S1 Job manifest exist; the report lists every changed draw
  site and the control commands with pass criteria.
- `STATUS.md` set to `done` (Julia not executed) or `blocked` with the reason.
