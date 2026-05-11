# PAPER_1.md — EvoODE Paper 1: Execution Roadmap and Working Plan

This document is the authoritative execution plan for EvoODE Paper 1.
It defines all phases, work packages, go/no-go criteria, risks, and design decisions.

For architecture and algorithm design, see `CLAUDE.md`.
For frozen Phase A results (historical only), see `docs/paper1_freeze_memo_phaseA.md`.

---

## Critical Scope Decision (2026-05-11)

**The final Paper 1 experiment evaluates exactly two conditions:**

1. The best final EvoODE variant — with pretuning enabled
2. The same final EvoODE variant — with pretuning disabled

No GP baseline. No EvoGrow v1. No EvoGrow v2.1. No legacy variant comparison as a main experiment.
All paper-relevant results must come from new runs. Phase A results are archived as historical exploratory evidence only.

**The final benchmark covers all ODEBench systems** — all 63 systems from `benchmarks/data/strogatz_extended.json`.
No subset selection, no curated shortlist, no overlap-only restriction.
Systems not exactly representable in the current basis are included and classified as surrogate systems.
They are analyzed separately and not scored on exact structural recovery.

---

## Current Status (as of 2026-05-11)

| Item | Status |
|------|--------|
| paper1_phaseA_v1 | Archived — 300/300 runs, all success=true, evidence frozen |
| Freeze Memo | Written: H1 PARTIAL, H2 SUPPORTED, H3 PARTIAL, H4 vacuous |
| Phase A diagnostic corrections | WP-0.1, WP-0.2 pending (see Phase 0) |
| Final EvoODE variant | Not yet defined — Phase 1 pending |
| ODEBench protocol | Not yet implemented — Phase 2 pending |
| Cluster runner | Not yet implemented — Phase 4 |
| EvoGrow v3 | Optional — see Phase 1 decision |

**Active phase: Phase 0 (Archive and correct Phase A)**

---

## Phase Overview

| Phase | Goal | Precondition | Output |
|-------|------|-------------|--------|
| **Phase 0** | Archive Phase A, correct diagnostics | paper1_phaseA_v1 complete | Corrected freeze memo, no new experiments |
| **Phase 1** | Define final EvoODE variant | Phase 0 complete | Written variant spec, all hyperparameters fixed |
| **Phase 2** | ODEBench protocol implementation | Phase 1 complete | Run schema, system classification, metric definitions |
| **Phase 3** | Small validation run | Phase 2 complete | Correctness/schema verified, no paper claims |
| **Phase 4** | Full ODEBench cluster run | Phase 3 complete | All 63 systems, final results |
| **Phase 5** | Analysis and paper | Phase 4 complete | Paper draft |

---

## Phase 0 — Archive Previous Results

### Goal

Correct two known errors in the Phase A diagnostics. No new experiments. No algorithm changes.
After this phase, Phase A evidence is permanently frozen and archived.

Phase A results are not used for final Paper 1 claims. They may appear in the paper as exploratory context
(e.g., "preliminary experiments suggested...") but are not the evidential basis for any hypothesis.

### Go Criteria

- `docs/paper1_freeze_memo_phaseA.md` contains the corrected H4 claim
- `h1_h4_diagnostics.json` is consistent with the corrected memo
- `evaluate_hypotheses.py` generalization path points to the actual data location
- No new runs added to `paper1_phaseA_v1`

### Work Packages

#### WP-0.1 — Correct H4 claim in freeze memo

**Language:** Python

**What:** Change the H4 "Allowed paper claim" in `evaluate_hypotheses.py` from a positive claim
to: "C3 cannot be evaluated — all usage-policy variants achieve exact_match_rate = 0 on all
high-stage systems. The expected ordering holds vacuously through ties only."
Regenerate `docs/paper1_freeze_memo_phaseA.md` and `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`.

**Scope:** 1 edit in `evaluate_hypotheses.py`, regenerate two output files.

#### WP-0.2 — Fix generalization data path

**Language:** Python / config

**What:** Update `analysis/configs/paper1_phaseA_v1.json` to point at the actual
generalization data location. Verify the OMIT verdict is reproduced correctly after the fix.

**Scope:** Config path edit, one verification run.

---

## Phase 1 — Define Final EvoODE Variant

### Goal

Define exactly what "best EvoODE" means for Paper 1.
This phase produces a written specification — not code.
No runs, no implementation. Only decisions, documented here.

The variant defined in this phase is the only EvoODE variant in the final experiment.
It must be fully specified before Phase 2 begins.

### Decisions Required

The following must be decided and written into this document before Phase 1 is closed:

**1. Structure search algorithm:**
Choose one: EvoGrow v2.2 (stage_local, hard usage) or EvoGrow v3 (equation-wise staged, if implemented).
If v3 is chosen, it must already be implemented and validated before Phase 2 begins.
If v2.2 is chosen, it is taken as-is from the current codebase.

**2. Stage progression policy:**
`:stage_local` or `:global_plateau`. Carried over from chosen algorithm.

**3. Stage usage policy:**
`:hard`, `:soft`, or `:passive`. Carried over from chosen algorithm.

**4. Basis configuration:**
`StagedPolynomialBasis` with standard 5 stages — unchanged.
All 63 systems will use the same basis. Basis must cover polynomial and trigonometric terms.

**5. Optimizer configuration:**
`BFGSOptimizer(maxiters, time_limit_s)`. Values must be set explicitly.
A time limit per run is required for cluster robustness.

**6. Pretuning switch:**
The only variation between the two experimental conditions is `use_pretuning = true` vs. `use_pretuning = false`.
All other settings are identical between conditions.

**7. Fixed hyperparameters:**
All hyperparameters must be written here before Phase 2 begins.
They must not change after Phase 1 is closed.

**8. Seed list:**
At minimum 3 seeds per (system, condition) cell. 5 seeds preferred.
Seeds must be fixed before Phase 2 begins.

### Go Criteria

- All 8 decisions above answered and written into the "Phase 1 Specification" section below
- If v3 is chosen: implementation exists and passes validation run (v3 validation is a precondition, not part of Phase 1)
- If v2.2 is chosen: current implementation confirmed to run correctly on at least 3 systems
- No hyperparameter is left as "TBD"

### Phase 1 Specification (to be filled in)

> **This section is empty.** It will be filled in when Phase 1 is closed.
> No runs may begin before this section is complete.

```
Final variant:          [TBD]
Stage progression:      [TBD]
Stage usage policy:     [TBD]
Basis:                  StagedPolynomialBasis (5 stages)
pop_size:               [TBD]
n_levels:               [TBD]
children_per_parent:    [TBD]
max_terms_per_eq:       [TBD]
λ:                      [TBD]
min_levels_per_stage:   [TBD]
BFGSOptimizer maxiters: [TBD]
BFGSOptimizer time_limit_s: [TBD]
loss_tol:               [TBD]
plateau_window:         [TBD]
plateau_tol:            [TBD]
Seeds:                  [TBD]
Conditions:             pretuning=true | pretuning=false
```

---

## Phase 2 — ODEBench Protocol Implementation

### Goal

Implement the complete data loading, system classification, metric definition, and run schema
for the full ODEBench benchmark. No experiments run yet. Only infrastructure.

### System Scope

All 63 systems from `benchmarks/data/strogatz_extended.json`.

Systems are classified into two categories before any runs begin:

**Exact systems:** Exactly representable in the current `StagedPolynomialBasis`.
- Score using: exact structural recovery (`exact_support_match`), R², loss, final stage,
  stage overshoot, wasted levels.
- Basis representability must be verified by inspecting each system's true structure.

**Surrogate systems:** Not exactly representable (e.g., constant offsets, fractional exponents,
terms outside the polynomial/trig basis).
- Score using: R², loss, final stage reached, stability of predicted trajectory.
- Do NOT score on `exact_support_match`. Do NOT report exact_match_rate.
- These systems are not failures — they test approximation quality and robustness.

The exact/surrogate classification must be written and committed before Phase 3 begins.
It is immutable after that point.

### Metrics

All metrics below must be defined, implemented, and verified before Phase 3.

**Per-run metrics (recorded in result.json and metrics.json):**

| Metric | Definition |
|--------|-----------|
| `loss` | Simulation MSE: `mean((Yhat - Ytrue)^2)` over all timesteps and dimensions |
| `r2` | R² coefficient of determination: `1 - SS_res / SS_tot`, computed per dimension, averaged |
| `r2_above_threshold` | Boolean: `r2 > 0.9` (ODEBench accuracy criterion) |
| `exact_support_match` | True iff discovered term indices match ground truth exactly (exact systems only) |
| `final_stage` | Last stage active at termination |
| `stage_overshoot` | `final_stage - expected_stage` (exact systems only; expected_stage from classification) |
| `wasted_levels` | Levels spent in stages above `expected_stage` (exact systems only) |
| `elapsed_s` | Wall time for full discover() call |
| `solver_failures` | Count of ODE solve failures (NaN outputs) during search |
| `use_pretuning` | Boolean — which condition this run belongs to |
| `system_id` | ODEBench system ID |
| `seed` | RNG seed |
| `git_hash` | Git commit hash at time of execution |
| `status` | queued / running / finished / failed / interrupted |
| `failure_reason` | exception / all_invalid / write_failure / unknown (only for failed runs) |

**Aggregate metrics (per system × condition cell, across seeds):**

| Metric | Definition |
|--------|-----------|
| `mean_loss` | Mean loss over valid runs |
| `std_loss` | Std of loss over valid runs |
| `mean_r2` | Mean R² over valid runs |
| `accuracy` | Fraction of valid runs with `r2_above_threshold = true` |
| `exact_match_rate` | Fraction of valid runs with `exact_support_match = true` (exact systems only) |
| `mean_final_stage` | Mean final stage over valid runs |
| `mean_stage_overshoot` | Mean stage_overshoot over valid runs (exact systems only) |
| `mean_wasted_levels` | Mean wasted_levels over valid runs (exact systems only) |
| `mean_elapsed_s` | Mean elapsed time over valid runs |
| `mean_solver_failures` | Mean solver failures over valid runs |
| `n_valid` | Count of valid runs (non-NaN loss) |
| `n_seeds` | Total run attempts |

A run is valid if `loss` is not NaN.

### Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Run registry | `experiments/<experiment_id>/run_registry.csv` | One row per run |
| Aggregate CSV | `analysis/data/<experiment_id>/aggregate_by_system_condition.csv` | One row per system × condition |
| Exact-only aggregate | `analysis/data/<experiment_id>/aggregate_exact_systems.csv` | Exact systems only |
| Surrogate aggregate | `analysis/data/<experiment_id>/aggregate_surrogate_systems.csv` | Surrogate systems only |
| System classification | `analysis/data/<experiment_id>/system_classification.csv` | System ID → exact/surrogate, expected_stage |

### Go Criteria

- All 63 systems loaded and inspected from `strogatz_extended.json`
- System classification written and committed (exact vs. surrogate, with reasoning per system)
- All per-run and aggregate metrics defined and test-computed on at least one dummy result
- Run schema (`config.json`, `result.json`, `metrics.json`) validated end-to-end
- Phase 1 Specification section is complete

### Work Packages

#### WP-2.1 — System classification

**Language:** Python (analysis) + manual inspection

**What:** For each of the 63 ODEBench systems, determine:
- Is the system exactly representable in `StagedPolynomialBasis` (5 stages: linear, self-quad,
  cross, self-cubic, trig)?
- If yes: what is the expected stage? (minimum stage containing all true terms)
- If no: why not? (constant offset, fractional power, product of 3+ variables, etc.)

Output: `analysis/data/paper1_phaseB_v1/system_classification.csv` with columns:
`system_id, name, dim, classification (exact/surrogate), expected_stage, basis_gap_reason`.

**Scope:** 1 analysis script or manual inspection table. No runs.

#### WP-2.2 — R² metric implementation

**Language:** Python

**What:** Write `analysis/utils/r2.py` implementing:
- `compute_r2(y_pred, y_true)`: R² averaged across dimensions
- `load_prediction_from_result_json(path)`: loads predicted trajectory from result.json
- `load_groundtruth(system_id, strogatz_path)`: re-simulates ground truth at same ICs/tspan

Validate on at least 3 Phase A result.json files (Phase A data available as test fixtures).

**Scope:** 1 utility module, test on existing data.

#### WP-2.3 — Run schema validation

**Language:** Julia

**What:** Confirm that `experiments/run_experiment.jl` correctly writes `use_pretuning` to
both `config.json` and `metrics.json`. Add a schema check script that validates a completed
run folder against the required fields listed in the metric table above.

**Scope:** Schema check script. Minor additions to run infrastructure if fields are missing.

---

## Phase 3 — Small Validation Run

### Goal

Validate correctness, runtime, and output schema before committing to a full cluster run.
**No paper claims are derived from this phase.**

### Scope

- 3–5 systems (spanning 1D, 2D, 3D, and at least one surrogate system)
- Both conditions: pretuning=true and pretuning=false
- 3 seeds per cell
- Run locally (not on cluster)

Suggested systems (to be confirmed in Phase 1):
- 1 exact 1D system
- 1 exact 2D system
- 1 exact 3D system (e.g., System 54 Lorenz)
- 1 surrogate system

### Go Criteria

- All runs complete without crashes
- `result.json` and `metrics.json` contain all required fields (validated by WP-2.3 schema check)
- R² computation returns valid values for all completed runs
- Pretuning=true vs. pretuning=false runs show distinct behavior (sanity check: not identical outputs)
- Runtime per run within acceptable limits for cluster planning
- No aggregate metric is NaN for any system that completed

### Work Packages

#### WP-3.1 — Validation run execution

**Language:** Julia / shell

**What:** Write a small experiment manifest for 3–5 systems, both conditions, 3 seeds.
Run using existing `experiments/run_experiment.jl`. Record runtimes.

**Scope:** Manifest config file + run command. No new code unless WP-2.3 reveals missing fields.

#### WP-3.2 — Validation analysis

**Language:** Python

**What:** Run the Phase 2 aggregation and R² pipeline on the validation run output.
Verify all output artifacts are produced correctly. Check for schema violations.
Write a short validation report (markdown, not committed as paper artifact).

**Scope:** 1 short analysis script or notebook (exploratory, not part of main pipeline).

---

## Phase 4 — Full ODEBench Cluster Run

### Goal

Execute the complete final experiment: all 63 ODEBench systems, both conditions (pretuning=true,
pretuning=false), fixed seeds, on a cluster. This is the only source of final paper results.

### Experiment Identity

Experiment ID: `paper1_phaseB_v1` (exact name TBD — must be set before Phase 4 begins)

### Runs

Total: 63 systems × 2 conditions × N seeds = (at minimum) 378 runs (with 3 seeds), or 630 runs (with 5 seeds).

Seed count fixed in Phase 1.

### Cluster Requirements

- Multiple parallel `run_experiment.jl` instances, each picking queued runs atomically
- Existing tmp→rename atomic write protocol is the locking mechanism — validate before use
- Julia version pinned via `Manifest.toml` (no package drift)
- Per-run `config.json` records: julia version, git commit hash, hostname, started_at, finished_at
- Failed runs are NOT deleted. They remain in the registry with `status=failed` and `failure_reason`.
- Interrupted runs (process killed) are detected by aggregator from `status=running` + `finished_at=null`
- No run is re-run silently. Any re-run is logged with a restart marker in `log.txt`

### What Is NOT in This Experiment

- No GP baseline
- No EvoGrow v1
- No EvoGrow v2.1
- No comparison to Phase A results within the experiment itself
- No legacy variants

### Go Criteria

- Phase 3 complete (schema validated, runtime known)
- Phase 1 Specification section complete and closed
- System classification from WP-2.1 committed
- Experiment manifest generated (`generate_manifest.jl` output verified)
- Cluster runner tested: ≥ 10 parallel runs without race conditions or file corruption
- All runs either `status=finished` or `status=failed` after completion (no `status=running` remainders)

### Work Packages

#### WP-4.1 — Cluster runner validation

**Language:** Julia / shell

**What:** Run 10–20 runs in parallel using multiple `run_experiment.jl` instances on the local
machine (simulating cluster parallelism). Verify that no two instances write to the same run
directory simultaneously. Verify that all completed runs have valid `result.json` and `metrics.json`.

**Scope:** Shell script launching multiple runners. No code changes unless race conditions found.

#### WP-4.2 — Full experiment manifest

**Language:** Julia

**What:** Run `generate_manifest.jl` for `paper1_phaseB_v1` covering all 63 systems,
both conditions, all seeds. Verify manifest completeness before any runs start.

**Scope:** Config file for the experiment + one invocation of `generate_manifest.jl`.

#### WP-4.3 — Cluster execution

**Language:** Shell / cluster job script

**What:** Submit all runs to the cluster. Monitor progress. Record any systematic failures
(e.g., OOM on high-dimensional systems, ODE solve timeout patterns).

**Scope:** Job submission scripts. No Julia code changes.

#### WP-4.4 — Aggregation

**Language:** Julia + Python

**What:** After all runs complete (or after declaring the run set closed), run:
1. `experiments/aggregate.jl paper1_phaseB_v1` → `run_registry.csv`
2. Phase 2 analysis pipeline → all aggregate CSVs

**Scope:** Two command invocations. No new code unless Phase 2 pipeline needs adaptation.

---

## Phase 5 — Analysis and Paper

### Analyses Required

After Phase 4 is complete, the following analyses must be produced:

**Primary analysis (all 63 systems, both conditions):**
- Accuracy (% runs with R² > 0.9) per system and per condition
- Mean R² per system and per condition
- Pretuning effect: paired comparison (pretuning=true vs. pretuning=false) for each system
- Solver failure rate per system and condition

**Exact systems only:**
- Exact structural recovery rate (exact_match_rate) per system
- Stage overshoot distribution
- Wasted levels distribution
- Stage-wise complexity allocation (how many levels per stage)

**Surrogate systems only:**
- R², loss, final stage reached
- Whether the highest necessary stage was reached
- Qualitative: which surrogate term classes (trig, cubic) were included in best structure

**Comparison to published ODEBench baselines (for context only):**
- Published numbers for SINDy (poly), PySR, ODEFormer at σ=0 may be cited
- Must be clearly labeled as "published results from d'Ascoli et al. 2023"
- Must note: EvoODE uses identical ICs and σ=0, but protocol differences may exist
- These numbers are NOT part of EvoODE's own experimental runs

**Pretuning narrative:**
The paper's secondary contribution is a systematic analysis of pretuning in simulation-based ODE discovery:
- Does pretuning improve accuracy across all system classes, or only specific ones?
- Does pretuning affect runtime (fewer BFGS iterations)?
- Does pretuning affect solver stability (fewer NaN outputs)?

### Planned Paper Structure

1. Introduction: ODE discovery, the role of initialization, staged complexity control
2. Related Work: SINDy, GP/PySR, ODEFormer — positioned honestly; no unfair comparisons
3. Method: final EvoODE variant, staged basis, pretuning mechanism
4. Experiments: ODEBench evaluation — full 63 systems, exact + surrogate split
5. Analysis: pretuning effect, staged complexity allocation, failure modes
6. Limitations and Future Work
7. Conclusion

### Allowed Claims (to be determined from Phase 4 results)

Claims will be defined after Phase 4. The following claim templates exist; only those
supported by Phase 4 evidence may appear in the paper:

- **Accuracy claim:** "EvoODE achieves X% accuracy (R² > 0.9) on the Y exact systems of ODEBench."
- **Pretuning claim:** "OLS warm-start pretuning improves accuracy by Z percentage points on average
  across the ODEBench suite."
- **Complexity control claim:** "Stage-local progression restricts wasted complexity to [metric]
  on systems where the expected stage is known."
- **Robustness claim:** "EvoODE completes successfully (non-NaN result) on N of 63 ODEBench systems."

No claim may be made from Phase A results. Phase A results may appear as supplementary material
or a brief historical footnote only.

---

## EvoGrow v3 — Equation-wise Staged Progression (Optional)

### Status

EvoGrow v3 (equation-wise promotion) is a candidate for Phase 1 selection. It is not yet implemented.
If Phase 1 selects v3 as the final variant, it must be implemented and validated before Phase 2 begins.
If Phase 1 selects v2.2, v3 is deferred to future work.

### Scientific Motivation

In v2.2, stage progression is system-wide: if any equation needs higher-stage terms, all equations promote together.
For coupled systems where some equations are already well-explained by low-stage terms, this wastes computation.

**v3 hypothesis:** Equation-local stage progression reduces wasted complexity exploration and produces
sparser discovered structures on multi-dimensional coupled systems.

### Design Specification

#### Core change
Replace single `current_stage::Int` with `eq_stages::Vector{Int}` — one per equation.

Each equation independently tracks:
- `stage_level_count[k]` — levels spent in current stage for equation k
- `stage_history[k]` — plateau-detection history for equation k
- Promotion decision for equation k, independent of all other equations

#### Per-equation loss proxy (open design question)
Equation-wise promotion requires a per-equation progress signal.
The system is optimized jointly (single loss function), so no exact per-equation loss decomposition exists.
**This must be resolved before any v3 implementation begins:**
- Option A: per-equation residual MSE (requires per-equation simulation, expensive)
- Option B: proxy from per-equation parameter magnitude change across levels
- Option C: per-equation term coefficient variance as a proxy for plateau

Document the chosen option here as a design note before WP-v3.1 begins.

#### New struct
`EvoGrowV3` in `src/structure/evogrow_v3.jl`.
This is not a replacement for `EvoGrow`. v2.2 code paths are untouched.

#### New metrics
- `eq_final_stages::Vector{Int}` — final stage per equation
- `eq_stage_overshoot::Vector{Int}` — overshoot per equation (against expected per-equation stage)
- `eq_wasted_levels::Vector{Int}` — wasted levels per equation
- Global `final_stage = maximum(eq_final_stages)` for backward compat

#### Work Packages (conditional on Phase 1 selection)

| WP | What |
|----|------|
| WP-v3.1 | Design note: per-equation loss proxy decision |
| WP-v3.2 | `EvoGrowV3` struct and `eq_stages` state |
| WP-v3.3 | Equation-aware child generation |
| WP-v3.4 | Per-equation plateau detection and promotion logic |
| WP-v3.5 | New metric fields in `result.json` (backward-compatible) |
| WP-v3.6 | Validation run: v3 on 3–5 systems, compared to v2.2 |

---

## Implementation Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Cluster runner: race condition on run acquisition | Low | Existing tmp→rename protocol is atomic; validate in WP-4.1 before full run |
| Julia version / package drift on cluster | Medium | `Manifest.toml` frozen; Julia version logged in `config.json` |
| ODE solve failures on high-dimensional or stiff systems | Medium | Record as `solver_failures` metric; failed runs retained, not deleted |
| BFGS time limit insufficient for large systems | Medium | Validate runtime in Phase 3; adjust `time_limit_s` before Phase 4 |
| pretuning OLS unstable on short trajectories | Medium | Existing NaN/norm fallback in `pretune.jl`; record failure rate in Phase 3 |
| R² computation requires re-simulating ground truth | Low | Ground truth reproducible from ICs/tspan in system JSON; ICs verified |
| v3 per-equation loss proxy not well-defined | High | Resolve in WP-v3.1 before any implementation; if unresolvable, fall back to v2.2 |
| Surrogate systems produce unstable ODE trajectories | Medium | Record and report; surrogate systems analyzed separately, not excluded |

---

## Scientific Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Pretuning effect too small to report as a finding | Medium | Honest reporting; "no significant effect" is a valid finding |
| EvoODE accuracy on full ODEBench suite too low to support any positive claim | Medium | Surrogate analysis + failure analysis still contribute; robustness is reportable |
| v3 (if selected) not measurably better than v2.2 | Medium | Frame as "precision allocation" — different behavior is the contribution, not necessarily better numbers |
| Protocol differences vs. published ODEBench numbers invalidate comparison | Medium | Do not frame as a direct comparison; cite published numbers for context only, with explicit caveats |
| 63 systems exceed available cluster budget | Low | Reduce seeds to 3 per cell; prioritize exact systems if budget is tight |

---

## Frozen Elements

### Phase A (permanently frozen, not used for paper claims)

- `paper1_phaseA_v1` run data: `experiments/paper1_phaseA_v1/`
- Phase A system selection (IDs: 2, 3, 11, 23, 24, 26, 31, 37, 54, 63)
- Phase A hyperparameters and seed list
- H1–H4 verdicts: `docs/paper1_freeze_memo_phaseA.md`
- Phase A metric definitions: `docs/paper1_study_protocol.md`

### After Phase 1 closes (immutable)

- Final variant specification (Phase 1 Specification section)
- All hyperparameters
- Seed list

### After Phase 2 closes (immutable)

- System classification (exact vs. surrogate, expected_stage per exact system)
- All metric definitions
- Run schema

### After Phase 4 begins (immutable)

- Experiment manifest for `paper1_phaseB_v1`
- All system ICs and tspan (from `strogatz_extended.json`, no changes)

---

## Document Maintenance

This document is updated at each phase transition:
- Mark completed WPs as done (add ✓ and date)
- Fill in Phase 1 Specification when Phase 1 closes
- Record Go/No-Go decisions with date
- Add v3 design note (per-equation proxy) when WP-v3.1 resolves
- Add paper claim decisions after Phase 4 results are available

Last updated: 2026-05-11
Current phase: Phase 0
