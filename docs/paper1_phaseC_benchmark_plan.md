# Phase C — Canonical EvoGrow Evaluation: Benchmark Plan

**Status: draft, incomplete, not frozen. Nothing long-running starts from this document yet.**

This is the operational authority for Phase C. `PAPER_1.md` holds the paper scope and the claims;
this document holds the experiment matrix, the freeze list and the prerequisites. Where the two
drift on an operational detail, this document decides; where they drift on scope, `PAPER_1.md`
decides.

Created 2026-09-09 after the scope decision that made Paper 1 a method paper.

**The governing rule.** No long-running job starts until, for every claim, the question, the
experiment, the comparison, the metric and the resulting figure or table are fixed — and the
configuration is frozen. This rule exists because Phase B was computed before the methodological
audit closed and therefore cannot serve as the main benchmark, at a cost of 5,248 core hours.

---

## 1. The claim matrix

| Claim | Question | Experiment | Comparison | Metric | Output |
|---|---|---|---|---|---|
| **A** | Can EvoGrow recover governing structure from trajectory data? | canonical capped arm | ground truth | exact recovery, term precision, term recall, structural F1, coefficient error, reconstruction R², trajectory MSE — all by representability class | Main Table |
| **B** | Does stage capping reduce search effort, and at what cost in quality? | capped vs uncapped, full mirror | paired per (system, seed, IC set) | explored stages, explored levels, nonlinear fits, ODE integrations, core hours, final loss, structural F1, exact recovery, reconstruction, generalization | Main Figure (savings vs Δquality) |
| **C** | Does a discovered model describe an unseen trajectory of the same system? | canonical capped arm, both directions | train IC vs test IC | R², share R² > 0.9, paired reconstruction vs generalization, by dimension and by exact/non-exact structure | Main Figure |
| **D** | Where does EvoGrow stand against an established sparse-regression baseline? | EvoGrow vs SINDy, identical trajectories | defined common subset, paired where possible | quality (A and C metrics) **and** cost (fits, integrations, core hours) | Main Table |
| **Diag** | Is a failure a search failure or an optimization failure? | oracle-structure fit | true structure supplied | success rate, sentinel-loss rate, reconstruction R² | Appendix |
| **Abl-1** | What does the stage cap change, mechanism-wise? | folded into Claim B | paired | cap decisions, reached stage, truncation | Ablation |
| **Abl-2** | What does pretuning do? | pretune on vs off | paired seeds | seed diversity, support pattern collapse, R², loss | Ablation |
| **Abl-3** | How does recovery depend on restarts? | subset, varying k | recovery against **fits**, never against k | recovery, R², total fits, `StructureSpec` duplicate rate | Ablation |

**Open cells in this matrix are blockers.** The matrix is not complete until every row names a
concrete script, an output path and a pass criterion. That is the remaining work on this document.

---

## 2. The four arms

| Arm | Function | Scope | Estimated cost |
|---|---|---|---|
| EvoGrow capped | the proposed final method | 63 systems × 3 seeds × 2 IC sets = **378 cells** | ~2,600 core hours |
| EvoGrow uncapped | stage-cap ablation (Claim B) | full mirror, **378 paired cells** | ~5,200–7,900 core hours |
| SINDy | external baseline (Claim D) | all configurations, identical trajectories | minutes |
| Oracle-structure fit | search-vs-optimizer diagnostic | true structure supplied, parameters only | < 20 core hours |
| **Total** | | | **~8,000–11,000 core hours, 3–5 weeks on Orion** |

Cost derived from Phase B's measured 5,248 core hours over 756 cells. The uncapped arm dominates
because it executes the full 30 levels where the capped arm stops early; Phase B averaged about 19.7
executed levels per cell and the late levels are the expensive ones, so the factor is above the
naive 30/19.7.

The uncapped arm keeps all 63 systems deliberately. dim 3 carried 75.6 % of Phase B's compute, which
is exactly where the cap's saving is largest; a demonstration that omits the expensive class invites
the obvious objection.

### Identical-conditions requirement for Claim B

Capped and uncapped differ in **one** thing: whether the stage cap is applied. Everything else is
identical and must be verified identical before submission, not assumed:

systems · trajectories · initial conditions · seeds · basis · stage definitions · optimizer ·
initialisation · restart policy · parameter budgets · search operators · selection · pruning ·
integration settings · maximum reachable search space · level budget.

---

## 3. Frozen configuration

Everything in this list is fixed before the campaign starts and is reported in the paper's
Experimental Setup. **Nothing here is adjusted on the basis of observed benchmark results.**

| Group | Item | Value | State |
|---|---|---|---|
| Data | ODEBench version / system set | 63 systems, `benchmarks/data/strogatz_extended.json` | frozen |
| Data | sampling | 512 points over `t ∈ [0, 10]` | frozen (Phase 3) |
| Data | integrator / tolerances | `Tsit5`, `abstol = reltol = 1e-9`, self-integrated | frozen (Phase 3) |
| Data | noise level | none | frozen |
| Data | train IC / test IC | both directions, never averaged | frozen |
| Method | basis | **OPEN — decided by the dim-2 constant-term probe** | **blocking** |
| Method | stage definitions | as shipped, degree-staged | frozen |
| Method | stage cap | `lookahead_horizon = 5`, `post_floor_significant_drop_ratio = 0.35`, `post_floor_min_floor_ratio = 0.1`, reopen branch | frozen (WP-C5) |
| Method | pruning rule | `max(1e-6, 1e-3 * max_abs)` | frozen — **no post-hoc change** (WP-V1, WP-N2) |
| Method | pretuning | `false` (canonical) | frozen 2026-09-09 |
| Method | restart policy | retry-on-failure, up to **k = 3** | frozen 2026-09-09 |
| Method | level budget | 30, no stopping rule | frozen (WP-B1) |
| Method | seeds | 3 | frozen |
| Method | expansion / selection | as shipped, add-only | frozen |
| Reporting | representability | three-way: fully / partially / non-representable | **to build** |
| Reporting | structural metrics | exact recovery, precision, recall, F1, coefficient error | **to build** |
| Provenance | identity triple | git hash + config fingerprint + behaviour fingerprint | frozen (WP-P1) |

### Two prohibitions the project has already violated once

- **No pruning threshold chosen after seeing results.** WP-V1 is that mistake, and WP-N2 showed over
  a 24-rule grid that hits + deleted-true-term + surviving-extra-term stays constant at 45 — raising
  the threshold trades one error class for the other roughly one-for-one. There is no better
  threshold to find.
- **No library component removed because it produces false positives.** That is precisely the
  constant-term question. It is decided before the freeze, on probe evidence, and never after the
  benchmark on benchmark evidence.

---

## 4. Blocking prerequisites

Ordered. None may be skipped, and the campaign is not submitted while any is open.

**P1 — Repair `git_hash` in the basis probe.** `studies/regression/wp_n1_basis_probe.jl` writes
`git_hash = "not_collected"`, which contradicts the project's identity rule. Repair before the probe
data are used for anything beyond exploration.

**P2 — Run the dim-2 constant-term probe.** 114 core hours, prepared and unstarted; command in
`codex/reports/REPORT_WP_N1.md`. This is ~1 % of Phase C's cost and it decides the most consequential
frozen parameter. Until it exists, the trade-off is measured on dimension 1 alone: the constant
halves structure recovery there (83.3 % → 38.9 %) while markedly improving generalization
(72.7 % → 87.9 % and 45.5 % → 66.7 %), and all nine diverging integrations fall on the old basis.

**P3 — Decide and freeze the canonical basis.** On the probe evidence, with the reasoning and the
date recorded. Representability is declared either way: the old basis represents 20 of 63 systems
exactly where SINDy's plain polynomial library represents 40 and ProGED's rational grammar 53.

**P4 — Build the structural metrics.** Term precision, term recall, structural F1 and coefficient
error appear **nowhere** in `src/`, `analysis/`, `experiments/` or `studies/`. Claim A cannot be
reported without them. **Partly done (WP-N7/N7b, 2026-09-09)**, and the validation attempt produced a
finding of its own — see §4a.

### §4a — Raw versus pruned support, and what Phase C must therefore store

The original acceptance criterion for WP-N7 required the new metrics to reproduce the registry's
`exact_support_match` on all 756 Phase B cells. **That criterion was wrong, and being wrong exposed
something the project had not stated.** Verified against the raw data:

- `run_registry.exact_support_match` for Phase B is **identical to `pruned_match`** — 756 of 756
  cells, no exception. It is the **pruned** match.
- `support_terms` is the **raw**, unpruned active term set (`active_term_names`,
  `studies/regression/run_regression.jl:870`).

Two different quantities under one comparison. And the pruned state is **not reconstructible** from
Phase B records, because pruning needs coefficients and Phase B stores none.

**The size of the gap is the finding.** On the 240 exact Phase B cells:

| quantity | cells | share of exact cells |
|---|---:|---:|
| all true terms present in the raw support (`missing == 0`) | 119 | 49.6 % |
| **pruned** support match — the reported campaign figure | **110** | **45.8 %** |
| **raw** exact structural match | **70** | **29.2 %** |
| hits owed **entirely** to the pruning rule | **40** | 16.7 % |

**40 of the campaign's 110 support hits — 36.4 % — exist only because the pruning rule removed
surviving extra terms.** The reported structure-recovery number is therefore substantially
threshold-dependent, on a threshold that WP-V1 showed cannot be selected from data and WP-N2 showed
is a zero-sum dial. The containment is exact and directional: `pruned_match == True` implies
`missing == 0` in 110 of 110 cells, and never the reverse — 9 cells carry every true term and still
fail because extras survive pruning.

**Per dimension the aggregate is misleading, and the split is the real result** (WP-N7b):

| dim | exact cells | raw match | pruned match | rescued by pruning |
|---|---:|---:|---:|---:|
| 1 | 72 | 51 (70.8 %) | 57 (79.2 %) | 6 (8.3 %) |
| **2** | **108** | **19 (17.6 %)** | **53 (49.1 %)** | **34 (31.5 %)** |
| 3 | 48 | 0 | 0 | 0 |
| 4 | 12 | 0 | 0 | 0 |

On dimension 1 pruning barely matters — six cells. **On dimension 2 it nearly triples the recovery
rate, and 34 of the 53 hits (64 %) are produced by the threshold rather than by the search.** The
honest reading of dim-2 structure recovery is therefore not "about half" but: *the search almost
never lands on the exact support; it lands on a superset, and the threshold cleans it up.*

That sharpens the known coupled-system limitation rather than softening it, and it is the form in
which the result belongs in the paper. It also means the dim-2 constant-term probe (P2) will be read
against a raw baseline of 17.6 %, not 49.1 %.

**Consequences, binding for Phase C:**

1. **Records store raw support, pruned support and coefficients** — all three. Phase B stored one of
   the three and is therefore not re-analysable on this axis at all.
2. **Both figures are reported wherever structure recovery appears**, raw and pruned, never one
   alone. Reporting only the pruned figure overstates recovery by roughly half; reporting only the
   raw figure understates the method as configured.
3. The pruning rule stays frozen. This finding is a **reason to report the dependence**, never a
   reason to retune the threshold.

### §4a-bis — Which earlier findings the raw/pruned split touches, and which it does not

Checked when the split was discovered, because a threshold-dependent quantity underneath a published
finding would change what that finding means:

- **WP-A7, the pretuning seed collapse — unaffected.** It groups on `support_terms`
  (`analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py:183`), i.e. the **raw**
  set. The collapse result (96/126 against 61/126 on support pattern, cluster-robust p = 1.0e-5, not
  one reverse pair) is therefore **threshold-independent** and stands as measured.
- **WP-A6, the retracted structural contrast — was pruned.** It reads `exact_support_match`
  (`analyze_pretuning_contrast.py:40`), so the 60/120 against 50/120 figure carried the pruning
  dependence on top of the clustering problem that already retracted it. It stays retracted, now for
  two independent reasons.
- **The T3 descriptive table — pruned throughout.** Every support-recovery figure in
  `descriptive_t3_exact_support.csv` is the pruned quantity. Wherever it is cited, the raw
  counterpart from `phaseb_raw_pruned_support_comparison.csv` is cited beside it.

The pattern is worth keeping in view: the pretuning finding the project kept is the one that does not
depend on the threshold, and the one it retracted is the one that did.

### §4b — One column name, two definitions

The two runners disagree, and the registry column does not say which it carries:

- `experiments/run_experiment.jl:405` sets `exact_support_match` to the **raw** match, and
  additionally stores `exact_support_match_raw` and `exact_support_match_pruned` separately. This is
  the **Phase A** path.
- `studies/regression/run_regression.jl` stores only `pruned_match`, which reaches the registry as
  `exact_support_match`. This is the **Phase B** path.

**A join of Phase A and Phase B on that column compares different quantities.** Phase C must name
the definition in the record itself, and the analysis must fail loudly rather than silently merge
files carrying different definitions.

**P5 — Build the three-way representability class.** Derived from `system_classification.csv`
(`unmatched_terms`, `gap_reason`) and `representational_adequacy.csv`. Structural metrics are never
reported without it.

**P6 — Implement and declare the restart policy.** Retry-on-failure up to k = 3, as an explicit
parameter inside the config fingerprint — not as a side effect of random initialisation.

**P7 — Measure the `StructureSpec` duplicate rate.** Without it the k = 1 reference point is not
defined, because today a structure is only re-started when the search happens to regenerate it. This
also settles whether candidate deduplication would change the experimental condition rather than
merely accelerate it.

**P8 — Complete this matrix.** Every row names a script, an output path and a pass criterion.

**P9 — Smoke test on a small system**, per the standing rule for multi-hour runs, before any cluster
submission.

---

## 5. What Phase B still supplies, and under what label

Phase B (`paper1_phaseB_v1`, 756 cells, 5,248 core hours, one identity triple) is **demoted from main
benchmark to diagnostics and ablation source**. It keeps supplying:

- **algorithm diagnostics** — dimension effects, coupling effects, search path dependence, failure
  cases
- **efficiency analysis** — runtime, fit counts, silent levels, cost distribution
- **the pretuning ablation** — seed diversity and anchoring (WP-A7)
- **stage-cap behaviour** — 690 of 756 cells execute fewer than 30 levels, and the count tracks the
  reached stage
- **failure analysis material** — dim-3/4 collapse, Lorenz cases, identifiability, wasted effort

**The label that must travel with all of it.** If Phase C freezes a different basis, Phase B ran a
differently configured method. Where Phase C covers the same ground — and for the failure analysis it
does, with 378 capped cells across all 63 systems and all dimensions — the **Phase C numbers are the
ones reported**, and Phase B is cited only for what Phase C does not cover. Phase B and Phase C
numbers never appear in the same table.

Two Phase B instrumentation findings carry forward regardless, because they are about the recording
and not about the configuration:

- `total_diverged_solves` and `total_solver_unstable_solves` are identical in all 756 cells — one
  quantity counted twice. They must never be reported as two independent robustness measures.
- **The optimizer retcode carries no statement about result quality in either direction.** 18 cells
  reach losses down to 1.9e-12 at R² ≈ 0.9999 without a single `Success`, and the sentinel loss `1e6`
  occurs *at* retcode `Success`.

---

## 6. Cost and evidence discipline

**Counts are evidence; time is context.** Design Principle 7 is unchanged by the move to a dedicated
cluster. Every cost, saving or efficiency statement rests on `total_parameter_fits`,
`total_loss_evals`, `total_ode_solves`, levels and stages. Core hours are reported as capacity
context and labelled as such — including in Claim B, where the saving is stated in counts first.

**No mean or median as an effect size.** Quantiles and threshold grids, and the threshold is never
picked after seeing the data — the grid is reported in full. This rule comes from WP-A6/A7, where a
median averaged two different phenomena to nothing and would have made the campaign look
resultless.

**Cluster-robust statistics are primary.** Cells are not independent: they cluster by system. The
Phase B pretuning difference was significant under exact McNemar (p = 0.021) and not significant
under a per-system permutation test (p = 0.218) — 120 pairs from 20 systems means an effective sample
size of 20. The cluster-robust procedure is the primary one throughout Phase C.

**Both metrics, always.** Design Principle 9: structure recovery **and** the R² > 0.9 rate, in every
table and every claim. They disagree — structurally wrong cells reach a median R² of 0.9997 with
92 % above 0.9 — and the R² > 0.9 rate is what makes any external comparison possible at all.

---

## 7. Open questions on this document

1. Does the SINDy arm get a paired subset defined by representability, by dimension, or both? Claim D
   currently compares dim 1 like-for-like; the all-system comparison has different aggregation units
   and must not be presented as a counterpart.
2. Which systems form the Abl-3 restart subset, and which values of k? Both fixed before running.
3. Does the oracle arm run on the canonical basis only, or on both bases?
4. Does Phase C re-run the pretuning ablation, or is Phase B's WP-A7 result cited as-is under the
   predecessor label? Re-running costs a second 378-cell arm.
5. Pilot before full submission: which subset, and what is the go criterion?
