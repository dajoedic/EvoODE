# Phase C — Canonical EvoGrow Evaluation: Benchmark Plan

**Status: matrix complete (P8, 2026-09-10), not frozen. Nothing long-running starts from this
document yet.** Every claim now names an arm, a script, an output path and a pass criterion, and the
five questions this document left open are decided in section 7. What still blocks the freeze is
listed in section 8: the canonical basis (P2/P3), and the declaration of the restart policy in the
Phase C fingerprint (the code half of P6/B3 landed on 2026-09-10 with WP-N11).

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

Every row names an arm, a script, an output path and a pass criterion. **Completed 2026-09-10
(P8).** A row whose script column says *to build* is a work package, not an open question: the
experiment is decided, the code is not written yet. Section 2a lists them.

### 1a - Question, comparison, metric

| Claim | Question | Arm | Comparison | Metric | Output |
|---|---|---|---|---|---|
| **A** | Can EvoGrow recover governing structure from trajectory data? | C-1 | ground truth | exact recovery **raw and pruned**, term precision, term recall, structural F1, coefficient error, reconstruction R2, trajectory MSE - all by representability class | Main Table |
| **B** | Does stage capping reduce search effort, and at what cost in quality? | C-1 vs C-2 | paired per (system, seed, IC set) | explored stages, executed levels, nonlinear fits, ODE integrations, final loss, structural F1, exact recovery, reconstruction, generalization; core hours as context only | Main Figure (savings vs quality delta) |
| **C** | Does a discovered model describe an unseen trajectory of the same system? | C-5 on C-1 | train IC vs test IC, both directions | R2, share R2 > 0.9, paired reconstruction vs generalization, by dimension and by exact/non-exact structure | Main Figure |
| **D** | Where does EvoGrow stand against an established sparse-regression baseline? | C-1 vs C-4 | paired per (system, IC set), **all 63 systems**, stratified | quality (A and C metrics) **and** cost — structural per method, see §6a; core hours are context, never the headline | Main Table |
| **Diag** | Is a failure a search failure or an optimization failure? | C-5 on C-1 | true structure supplied | success rate, sentinel-loss rate, reconstruction R2 | Appendix |
| **Abl-1** | What does the stage cap change, mechanism-wise? | C-1 vs C-2 | paired | cap decisions, reached stage, truncation | Ablation |
| **Abl-2** | What does pretuning do? | C-3 vs C-1 subset | paired seeds, grouped on **raw** support | seed diversity, support pattern collapse, R2, loss | Ablation |
| **Abl-3** | How does recovery depend on restarts? | C-5 on C-1 | k in {1, 2, 3, 5, 10} | recovery against **fits**, never against k; R2, total fits, `StructureSpec` duplicate rate | Ablation |

### 1b - Script, output path, pass criterion

| Claim | Script | Output path | Pass criterion |
|---|---|---|---|
| **A** | `studies/regression/generate_phase_c_manifest.jl` *(to build)* -> `studies/regression/run_k8s_indexed_cell.jl` -> `analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py` *(campaign-id parameter to build)* + `aggregate_representability_threeway.py` | records `outputs/studies/regression/phase_c/tasks/`; derived `analysis/data/paper1_phaseC_v1/phasec_structure_metrics_by_cell.csv`, `..._by_equation.csv`; tables `analysis/tables/paper1_phaseC_v1/` | 378/378 records, zero `error`, 378 unique identities, **one identity triple**; every cell carries raw support, pruned match, coefficients, `basis_name` and the support-definition tag non-null; raw **and** pruned reported side by side in every stratum; representability class present for all 63 systems |
| **B** | same runner with `EVO_REGRESSION_VARIANT=evogrow_v2_2_stage_local` -> `analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py` *(to build)* | `analysis/data/paper1_phaseC_v1/phasec_cap_ablation_paired.csv`; figure `analysis/figures/paper1_phaseC_v1/` | **378 complete pairs**; the identical-conditions check of section 2b passes as a **computed diff**, not an assertion; savings stated in counts first, core hours labelled context; quality delta as quantiles and a full threshold grid, cluster-robust per system |
| **C** | `studies/regression/wp_n5_ic_generalization.jl --input <phase_c history>` | `outputs/phase_c_generalization/`; `analysis/data/paper1_phaseC_v1/phasec_generalization.csv` | the WP-N5 reconstruction control is **exact to zero on 378/378** - a nonzero control means the record cannot rebuild the model and invalidates the arm; both directions reported separately, never averaged; structure recovery reported beside every R2 figure (DP 9) |
| **D** | `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py` on the C-1 trajectories | `analysis/data/paper1_phaseC_v1/phasec_sindy_paired.csv`; table `analysis/tables/paper1_phaseC_v1/` | trajectories **verified byte-identical** to those C-1 consumed, by hash, not by assertion; paired per (system, IC set) over all 63; stratified by dimension **and** three-way representability with **no cross-stratum headline number**; all SINDy configurations reported, none selected post hoc; cost axis beside every quality number; EvoGrow seed handling declared explicitly |
| **Diag** | `studies/regression/wp_n3_oracle_refit.jl --input <phase_c history>` | `outputs/phase_c_oracle/`; `analysis/data/paper1_phaseC_v1/phasec_oracle.csv` | covers every exact-system cell of C-1; sentinel-loss rate and R2 > 0.9 share reported; each failure class named as search or optimizer, never left implicit |
| **Abl-1** | folded into Claim B, same script | same as B, columns `stage_caps`, `final_stage`, `eq_final_stages` | truncated equation rows are **counted and named per system**, never reported only as an aggregate |
| **Abl-2** | C-3 arm -> `analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py` | `analysis/data/paper1_phaseC_v1/phasec_pretuning_collapse.json` | **180/180 cells** (WP-N16 grew the arm with the basis; the running Job confirms it at 180); grouping on **raw** `support_terms`, which is what makes the result threshold-independent; per-system permutation test primary, McNemar secondary; reported beside the Phase B WP-A7 figure **with the basis label on each** |
| **Abl-3** | `studies/regression/wp_n4_multistart_refit.jl --input <phase_c history> --starts 10` | `analysis/data/paper1_phaseC_v1/phasec_restart_curve.csv` | recovery plotted against **fits**, never against k; the measured `StructureSpec` duplicate rate from C-1 reported beside it as the implicit multistart; the text states that k is a **per-structure parameter start count, not a beam size** |

---

## 2. The five arms

Costs are **derived from the Phase B registry**, not estimated:
`experiments/paper1_phaseB_v1/run_registry.csv`, 756 cells, 5,248.0 core hours. Timing is capacity
planning and is labelled as such (Design Principle 7); it is never evidence for a claim.

| Arm | Variant / script | Basis | Scope | Core hours |
|---|---|---|---|---|
| **C-1** capped canonical | `evogrow_v2_2_stage_capped`, `pretuning = false` | canonical (P3) | 63 systems x 3 seeds x 2 IC sets = **378 cells** | **~3,900** |
| **C-2** uncapped mirror | `evogrow_v2_2_stage_local`, otherwise identical | canonical | full mirror, **378 paired cells** | **~6,000-9,600** |
| **C-3** pretuning confirmation | `evogrow_v2_2_stage_capped`, `pretuning = true` | canonical | **30** exact systems x 3 seeds x 2 IC sets = **180 cells** | **~2,400** |
| **C-4** SINDy baseline | `run_wp_n6_sindy_baseline.py` | n/a | 63 systems x 2 IC sets, all configurations | minutes |
| **C-5** derived arms | `wp_n3_oracle_refit.jl`, `wp_n4_multistart_refit.jl`, `wp_n5_ic_generalization.jl` | canonical | no new search - all three read C-1's `history.jsonl` | **< 50** |
| **Total** | | | | **~12,300-15,900, 5-7 weeks on Orion** |

**C-3 grew with the basis (2026-09-13, WP-N16).** Under the canonical basis **30 of 63 systems are
exact**, not 20 — the ten that failed on the constant alone (1, 5, 9, 17, 23, 43, 52, 57, 58, 59)
are now representable. C-3 covers all exact systems, so it is **180 cells, not 120**, and its cost
rises with it. Every other count derived from "20 exact systems" is stale for Phase C in the same
way, the Phase B figures of 240 exact / 516 surrogate cells included.

**The figures were raised again on 2026-09-13, when P3 froze the constant basis.** The Phase B
registry measures the **old** basis, so every number derived from it understates the canonical arm.
The dim-2 probe measures the premium directly, over both arms. On the 335 cells available when the
table was written: `total_loss_evals` **+19.8 %** in sum (3.51e8 against 4.20e8),
`total_parameter_fits` **+3.2 %**, with stage 5 reached by exactly 121 cells in either arm. On the
**complete 336** (2026-09-14) it is **+20.8 %** (3.507e8 against 4.237e8) and **+4.0 %**, with stage 5
at 122 constant against 121 old cells. The table carries **+20 % on the counting quantities**,
applied to C-1, C-2 and C-3 — **now marginally below the measured premium**. The campaign is frozen
and running, so the figure stays as it is and the shortfall is declared here rather than corrected;
it is the same one-sided risk the cautions below describe.

Three cautions travel with that. Core hours are **not** readable off loss-eval counts (Design
Principle 7) — this is a proportional carry-over, not a measurement in hours. The premium was
measured on **dimension 2 only**, while dim 3 carried 75.6 % of Phase B's compute and is unmeasured
under the constant basis. And in the nine paired exact systems the premium is far larger (about
+60 % in median loss evaluations) than in the whole probe, so the aggregate is not a bound. **Treat
the total as a planning figure with a one-sided risk: it can be exceeded, and the uncapped mirror is
where that would show first.**

**The C-1 figure supersedes the "~2,600 core hours" this document carried until 2026-09-10.** That
number was an estimate; 3,249.3 h is the measured cost of the equivalent Phase B arm
(`pretune_off`, 378 cells) on the old basis. C-2 dominates because it executes the full 30 levels where the capped
arm stops early: Phase B averaged about 19.7 executed levels per cell and the late levels are the
expensive ones, so the factor exceeds the naive 30/19.7.

The uncapped arm keeps all 63 systems deliberately. dim 3 carried 75.6 % of Phase B's compute, which
is exactly where the cap's saving is largest; a demonstration that omits the expensive class invites
the obvious objection.

**C-3's cost is concentrated in 24 cells, and that is recorded rather than hidden.** The
breakdown below is measured on the arm's **pre-WP-N16 scope of 120 cells** and on the old basis;
the current arm is 180 cells at ~2,400 h (section 2 table), and the 60 cells added by the ten
newly-exact systems are not in these figures. Of the measured 1,331.4 h, **1,314.5 h (98.7 %) fall
on the four dim-3 exact systems** - system 56 alone costs 602.3 h over six cells - while the
remaining 96 cells run in 17.0 h. The median exact `pretune_on`
cell costs 0.02 h against a maximum of 289.7 h, so no mean over this distribution means anything.
Including dim 3 was decided on 2026-09-10 so that the collapse is measured under the canonical
configuration on the class where the method is weakest, accepting that this spends about 16 % of the
budget on an ablation.

### 2a - What must be built before C-1 starts

Decided experiments whose code does not exist yet. None is an open question; each is a work package.

| # | Item | Why |
|---|---|---|
| B1 | ~~`studies/regression/phase_c_config.jl` + `generate_phase_c_manifest.jl`~~ **done (WP-N16, `6212809`)** — Phase C identity is `0c9672de35c75a9d`, 936 manifest rows (378 + 378 + 180) | Phase C needs its own campaign id, variant list and fingerprint; the Phase B pair is frozen and must not be edited. **Carries the record-column requirements from WP-N14 and the restart-parameter declaration from WP-N11 — see below** |
| B2 | ~~Record fields for raw/pruned support and the definition tag~~ **done (WP-N12, `47920a2`)** | Section 4b: one column name carried two definitions. Records now write `pruned_support_terms`, `exact_support_match_raw`, `exact_support_match_pruned` and `exact_support_match_definition`; the frozen pruning threshold has exactly one implementation instead of five inline copies |
| B3 | ~~Restart policy in the optimizer~~ **done (WP-N11, `4908b07`)**; remaining part is declaring it in the Phase C fingerprint, which belongs to B1 | P6 - the policy had no code at all until 2026-09-10; `max_fit_attempts` now exists with default 1, verified behaviour-neutral |
| B4 | ~~`phase_c_support.json` via `derive_phase_b_support.jl` on the canonical basis~~ **done (WP-N16)** — 30 exact / 33 surrogate | true support and representability are basis-dependent; if P3 freezes the constant basis, the Phase B table is wrong for Phase C |
| B5 | ~~`analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py`~~ **done (WP-N14, `e738b0c`)** | The identical-conditions check is an allowlist, so a column nobody has defined yet still has to match. The script refuses to substitute `n_levels` for executed levels, and refuses arms that are not the capped/uncapped pair -- Phase B's 378 pairs look mechanically identical but are both capped |
| B6 | ~~Campaign-id parameter for the existing aggregate scripts~~ **done (WP-N13, `1c984a6`)** | The stated premise was wrong: the scripts already took `--registry`, `--classification` and `--output-dir`, only their defaults pointed at Phase B. The real gap was that `verify_campaign_registry.py` never checked `experiment_id` at all, so a two-campaign registry passed. Now `--campaign` derives the paths and a mismatch aborts before any file is written. `.gitignore` also gained the missing `paper1_phaseC_v1` negations, without which every output path named in section 1b would have been silently untracked |
| B7 | ~~k8s manifests for C-1, C-2, C-3 plus their smoke jobs~~ **done (WP-N17, `29a0030`)** — **two** campaign Jobs, not three: C-1 and C-2 share one because their pairing is binding, C-3 runs alone so it stays cuttable | the Phase B manifests carry the Phase B campaign path |

**Carried into B1 from WP-N13:** `verify_campaign_registry.py` still defaults to Phase B counts —
756 rows, 756 unique identities, 378 per condition, 240 exact, 516 surrogate. A Phase C run must
pass its own values explicitly (378 cells per arm), or the verifier passes on the wrong
expectations.

**Carried into B1 from WP-N14 — the columns Phase C records must provide.** The cap-ablation script
requires them and aborts without them:

`executed_levels` (the **executed** level count, never `n_levels`, which is the constant 30),
`structural_f1`, `term_precision`, `term_recall`, `coefficient_relative_error_mean`,
`exact_support_match_raw`, `exact_support_match_pruned`, `total_parameter_fits`,
`total_parameter_fit_attempts`, `total_loss_evals`, `total_ode_solves`, `final_stage`,
`system_expected_stage`. Generalization columns are used when present.

**Carried into B1 from WP-N11:** the restart parameter must enter the **Phase C** fingerprint, and
k = 3 is set in the Phase C configuration — never in the optimizer default, which stays at 1.

Good news from the same audit, which is why this list is short: the uncapped mirror needs **no new
search code** - `evogrow_v2_2_stage_local` is already a shipped variant selectable through
`EVO_REGRESSION_VARIANT`; the basis is already a per-variant parameter
(`build_variant_basis`, `studies/regression/run_regression.jl:413`); coefficients are already
persisted (`model_terms`, `run_regression.jl:871`); and the oracle diagnostic, the restart curve and
the generalization pass are three existing scripts that read a `history.jsonl` and need no arm of
their own.

### 2b - Identical-conditions requirement for Claim B

Capped and uncapped differ in **one** thing: whether the stage cap is applied. Everything else is
identical and must be **verified identical by a computed diff before submission**, not assumed:

systems, trajectories, initial conditions, seeds, basis, stage definitions, optimizer,
initialisation, restart policy, parameter budgets, search operators, selection, pruning,
integration settings, maximum reachable search space, level budget.

The check is part of B5, and its failure is a hard stop rather than a caveat.

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

**P2 — Run the dim-2 constant-term probe.** Prepared and unstarted; command in
`codex/reports/REPORT_WP_N1.md`.

> **Cost corrected 2026-09-09, and the old figure was wrong by an order of magnitude.** The
> "114 core hours" quoted here, in `CLAUDE.md` and in the diary is **unsourced** — `REPORT_WP_N1.md`
> contains no cost estimate at all. Derived instead from the campaign's own dim-2 arm, which is the
> same cell count under the same configuration family: **336 cells at a mean of 3.47 h and a median
> of 1.12 h, totalling 1,167.5 h**. The probe is 28 dim-2 systems x 2 bases x 2 IC sets x 3 seeds =
> **336 cells**, so the realistic figure is **~1,200 core hours**, not 114. The constant basis
> searches a larger space, so if anything this is optimistic. (Timing used for capacity planning
> only, per Design Principle 7 — never as evidence for a claim.)
>
> **Consequences.** The probe cannot run on the laptop: 1,200 core hours serial is roughly seven
> weeks. It needs the cluster, and `wp_n1_basis_probe.jl` has **no sharding or index support** — it
> is a single serial loop appending to one `history.jsonl`, so it cannot use the
> `run_k8s_indexed_cell.jl` path the campaign used. Either the script gains sharding, or the probe
> scope is cut. Both are decisions, and they are recorded before the run rather than after. This is ~1 % of Phase C's cost and it decides the most consequential
frozen parameter. Until it exists, the trade-off is measured on dimension 1 alone: the constant
halves structure recovery there (83.3 % → 38.9 %) while markedly improving generalization
(72.7 % → 87.9 % and 45.5 % → 66.7 %), and all nine diverging integrations fall on the old basis.

**P3 — Decide and freeze the canonical basis. CLOSED 2026-09-13: the canonical basis is
`staged_polynomial_basis_with_constant`.** Every Phase C arm uses it.

The decision was taken **against** the probe's recovery numbers, and it is reported that way. On the
nine dim-2 systems exact under both bases the constant costs recovery — pruned 55.6 % → 35.2 %, raw
13.0 % → 7.4 % — at an identical R² > 0.9 rate of 94.4 %. What decides it is representability, which
is not a tuning parameter: the old basis represents 20 of 63 systems exactly where SINDy's plain
polynomial library represents 40 and ProGED's rational grammar 53, and ten systems fail on the
constant alone. A search-strategy contribution cannot be claimed over half the search space of the
baseline it is compared against.

The evidence base and its limits: WP-N15 over the dim-2 probe (335 of 336 cells at decision time,
**336 of 336 since 2026-09-14**; the missing cell was indeed a surrogate and touched only one R²
denominator — the constant arm's surrogate R² > 0.9 rate fell 90.7 % → 89.8 %, nothing else moved),
plus WP-N1 and WP-N5 on
dimension 1, where the constant halves structure recovery (83.3 % → 38.9 %) and markedly improves
generalization (72.7 % → 87.9 %). **Generalization was never measured on dim 2**, so the strongest
argument in the constant's favour rests on dimension 1 alone. Phase C's Claim C closes that gap for
the canonical basis, but it will have no old-basis counterpart on dim 2 — deliberately, since the
probe is not re-run.

**Two consequences are carried forward rather than absorbed.** Costs rise by about 20 % on the
counting quantities (see §2). And the raw structure-recovery rate will be very low: on dim 2 the
pruning rule already produces 77 % of the old basis's hits (30 pruned against 7 raw), and the
constant is a false-positive magnet — on dim 1 it appears in 31 of 37 missed cells. Raw **and**
pruned are reported everywhere, which is already the standing rule from WP-N7 and Design Principle 9.
This is a reason to report the threshold dependence, **never** to retune the threshold.

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

**P6 — Implement and declare the restart policy. Implemented 2026-09-10 (WP-N11, `4908b07`);
declaration in the Phase C fingerprint still open.** Retry-on-failure up to k = 3, as an explicit
parameter inside the config fingerprint — not as a side effect of random initialisation.

> **It did not exist until 2026-09-10.** `grep -rn "restart\|retry\|multistart\|n_starts" src/`
> returned nothing: the policy was frozen in this document and absent from the code, so the effective
> restart count was whatever the search's structure duplication happened to produce.
>
> **Now built (WP-N11).** `BFGSOptimizer.max_fit_attempts`, default **1**, so existing behaviour is
> unchanged — verified bit-identical on a real regression cell across 84 fields. Attempt 1 takes the
> canonical start, later attempts fire only after a failure and always draw a fresh random start.
> Failure is the named predicate `fit_attempt_failed`. Attempt costs are summed;
> `total_parameter_fit_attempts` is a new counter and `total_parameter_fits` keeps its meaning.
>
> **Still open, and B1 owns it:** the parameter is deliberately outside the Phase B fingerprint,
> whose value the 756 campaign records depend on. It must enter the **Phase C** fingerprint, and
> Phase C must set k = 3 there rather than in the optimizer default. Section 8 records why the
> ordering against P7 stays uncomfortable.

**P7 — Measure the `StructureSpec` duplicate rate. Counter built (WP-N10, commit `22a9059`); the
distribution comes from C-1.** Without it the k = 1 reference point is not
defined, because today a structure is only re-started when the search happens to regenerate it. This
also settles whether candidate deduplication would change the experimental condition rather than
merely accelerate it.

**P8 — Complete this matrix. DONE 2026-09-10.** Every row of section 1b names a script, an output
path and a pass criterion; the five open questions are decided in section 7; the work packages the
matrix implies are listed in section 2a.

**P9 — ~~Smoke test on a small system~~ built 2026-09-14 (WP-N17 manifest, WP-N18 pilot and checker); only the execution is left.** Per the standing rule for multi-hour runs, before any cluster
submission. Distinct from the 12-cell pilot of Q5: the smoke test asks whether the path runs, the
pilot asks whether the records support the claims.

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

### 6a — Cross-method cost, and why time cannot carry it (decided 2026-09-18)

**The rule above assumes a shared unit, and across methods there is none.** Within EvoGrow, cost is
`total_parameter_fits`, `total_loss_evals`, `total_ode_solves`. SINDy performs one linear regression
per equation. ODEFormer performs one transformer forward pass, a beam over its candidates, and a
single parameter optimization. These three quantities are not convertible into one another. Wall
clock is the only axis all three share — which is exactly why it is tempting and exactly why it must
not carry the claim.

**Decision: the headline cost statement is structural, not timed.** The defensible form is the one
WP-N6 already uses — *SINDy runs one linear regression per equation; EvoODE runs a median of 410
nonlinear fits per cell, each with ODE integrations* — extended to ODEFormer by naming its
per-instance work. A statement of that shape needs no stopwatch, no hardware footnote, and survives
review. It is what Claim D reports.

**Timing is permitted, secondary, and declaration-bound.** Design Principle 7 allows timing "on a
dedicated machine", and the campaign pods are one: 1 CPU, `JULIA_NUM_THREADS=1`,
`OPENBLAS_NUM_THREADS=1`, `requests == limits`. Any cross-method timing is measured **in that same
pod shape on Orion**, never on the laptop, and is reported as a secondary axis with the confounders
below stated in full. It never appears as the headline of Claim D.

**Four confounders, and all four are declared — in both directions.** Declaring only the ones that
favour us is the failure mode:

| Confounder | Direction |
|---|---|
| ODEFormer is a neural model built for GPU; Orion is CPU | **against ODEFormer** — the number measures our hardware, not their method |
| Julia against Python/torch | neither — implementation quality, with no defensible correction |
| **ODEFormer's pretraining cost is excluded** | **for ODEFormer** — its forward pass is cheap *because* a large one-time training already happened |
| Orion is shared | neither — co-tenant load moved from 36.55 to ~3.4 cores within four days of 2026-09-18 |

**Practical requirement for the baseline image.** ODEFormer fetches its weights from Google Drive
via `gdown` (`odeformer/model/sklearn_wrapper.py:60-66`). The weights must be **baked into the
image**. Otherwise every pod either fails without egress, or 32 pods request Google Drive at once.

**ODEFormer arm — decided 2026-09-23 (WP-N21).** The published ODEFormer numbers come from the
**reference environment** — torch 2.0.0, sympy 1.11.1, numpy 1.23.5, i.e. the environment ODEFormer
was built and published with. WP-N21 measured that the environment moves its output: every
environment is bit-reproducible, the seed is inert (`transformer.py:495` resets
`torch.manual_seed(0)`), and between torch 2.0 and 2.14 0 of 6 expressions agree, R² values move by
up to 0.04. A reviewer must not be able to say we ran a different ODEFormer. The candidate
environment (torch 2.14) runs the same grid as a **sensitivity check**, reported beside it — the
shift itself is a reportable reproducibility finding about the literature baseline. The reference
image's HIGH/CRITICAL findings are a documented exception (`CHANGELOG.md` E7).
**Configurations: all four, all reported, none selected** — beam size 10 and 50, each with and
without ODEFormer's own constant optimisation (`param_optimizer.py`, `ConstantOptimizer`, its own
defaults). The same rule as SINDy's ten configurations. SINDy runs in its own environment:
pysindy 2.1.0 needs `numpy >= 2.0`, ODEFormer `numpy==1.23.5`.

**The output is not deterministic, and the integration limit stays at ODEFormer's 1 s — decided
2026-09-25 (WP-N24).** The sentence "one run per cell, because the output is deterministic" stood
here until 2026-09-25 and is refuted. ODEFormer's `_integrate_ode` carries a 1-s wall-clock
`SIGALRM` timeout that acts in candidate ranking, constant optimisation and evaluation. The
repeatability measurement (38 cells × 3 repetitions, six runs, `DIARY.md` 2026-09-25) shows:
**every** non-reproducible cell has a timeout, with none in any run lacking one; more parallel
load gives more spread; and a 10-s limit does **not** restore determinism, because some candidate
ODEs integrate for longer than 10 s. Every limit in seconds stays a race against the clock.
Decision: **the canonical mode is `faithful` (1 s)**, the protocol ODEFormer's published numbers
were produced under. The reference grid runs **three repetitions per cell** with one ODEFormer
process per CPU and no co-scheduled work in the same process, and is reported as a rate **with its
spread across repetitions**. The non-determinism is declared as a property of the baseline, not
smoothed. The candidate environment stays a sensitivity check. A deterministic step budget in
place of the clock was considered and rejected as the canonical choice: it would leave ODEFormer's
protocol and add a constant of our own. Three repetitions of the reference grid cost about 25 h
sequentially, measured from the WP-N23 grid (8.35 h per repetition; capacity planning, not
evidence), so the run belongs on Orion.

**The baseline environment carries a dependency conflict (found 2026-09-23).** `torch==2.0.0` has
a CRITICAL and several HIGH advisories (`CHANGELOG.md` E6). Every torch release that clears them
(≥ 2.10, which needs Python ≥ 3.10) requires `sympy ≥ 1.13.3`, while the pinned ODEFormer commit
requires exactly `sympy==1.11.1`. The ODEFormer work package resolves this, and its acceptance
includes: ODEFormer loads its weights under torch ≥ 2.10 — mind that `torch.load` defaults to
`weights_only=True` from 2.6 on — and reproduces, on a test system, the prediction it gives under
`sympy==1.11.1`. A silent change in the symbolic output would change a baseline number, so this is
a comparison, not an install check. Also: before 2026-09-23 the baseline image could not be built
at all, because the root `.dockerignore` excluded `baselines/`; `baselines/Dockerfile.dockerignore`
fixes that.

**Why this section was written before the measurement.** `CLAUDE.md` records that the three
candidate framings of 2026-09-07 were shapes fitted to whichever data happened to exist, and rejects
that move. Deciding what a timing run may claim *after* seeing its numbers is the same mistake in a
smaller place.

### 6b — Which R² aggregation the R² > 0.9 rate uses (decided 2026-09-18)

**Two aggregations exist and they are not the same quantity.** We average the per-dimension R²
arithmetically (`run_regression.jl:675`; the stored `r2` is exactly `mean(r2_by_dim)`, verified on
52 of 52 Phase C records to 1e-12). ODEFormer weights by the variance of each dimension
(`odeformer/metrics.py`, `r2_score(..., multioutput='variance_weighted')`). On one-dimensional
systems they coincide; on multidimensional ones they do not.

**Decision: both are reported everywhere, and the variance-weighted figure is the one labelled as
the literature comparison** — because it is ODEBench's own definition, and Design Principle 9
justifies carrying an R² > 0.9 rate at all by the external comparison it makes possible. A rate
computed under a different convention than the work it is compared against is not a comparison. The
arithmetic mean remains the internal figure: it is what the records store and what every earlier
result in `DIARY.md` and the Phase B tables cites.

**That reason is stated first because the numbers push the other way, and must not be the reason.**
Measured on the 52 Phase C records available on 2026-09-18 — all dimension 3, the hardest class and
the first block of the cost-ordered queue:

| | |
|---|---|
| median absolute difference | 3.3e-02 |
| maximum absolute difference | 5.3e-01 |
| cells that change side of the 0.9 threshold | **14 of 52** |

The direction is one-sided: **variance weighting is the higher number**, because a badly fitted
low-variance dimension drags the arithmetic mean down and is nearly ignored by the weighting.
System 52, seed 42, IC set 2 moves from 0.5727 to 0.9175. Choosing the aggregation after seeing
that it flatters us is the pruning-threshold mistake and the WP-V1 mistake in a third place. The
choice therefore rests on the definition, and would stand unchanged had the numbers fallen the other
way.

**The flip rate is itself a result and is published as a declared sensitivity**, not smoothed away.
It states how strongly the literature metric depends on a convention on multidimensional systems.
Two cautions travel with the figure above: those 52 records are dimension 3 only, where the two
aggregations diverge most, so the campaign-wide rate will be lower; and the rate is recomputed on
the complete campaign rather than carried forward.

**No re-run is required.** The variance-weighted figure is reconstructable from what is already
stored: `r2_by_dim` is present in every record, and the weights are variances of the reference
trajectory, which the hashed export under `outputs/phase_c_trajectory_hashes/wp_c4c/` supplies. The
reconstruction is exact, not approximate — the control is that recomputing the arithmetic mean from
`r2_by_dim` reproduces the stored `r2`. This is implemented in the analysis pipeline, never in the
campaign path.

**Built and measured on the whole of Phase B (WP-N20, 2026-09-18).**
`analysis/scripts/aggregate/aggregate_variance_weighted_r2.py` takes the campaign identifier as a
parameter. The control holds on **756 of 756** cells at a maximum error of 1.1e-16, and the
one-dimensional cells agree in **276 of 276**, as they must. Over the full campaign **53 of 756
cells change side of the threshold, every one of them upward, none downward.** The rate rises with
dimension — 0 % on dim 1, 3.6 to 9.5 % on dim 2, 13 to 30 % on dim 3, and 67 % in one dim-4 group of
six. Differences themselves go both ways (the quantiles of `variance_weighted − arithmetic` reach
−5.1e-02), but no downward difference crosses the threshold. These are **Phase B diagnostics** and
never appear beside a Phase C number; the Phase C rate is computed on the Phase C records.

**One assumption is declared rather than verified.** The weights for the Phase B analysis are read
from the **Phase C** trajectory export, because Phase B's own trajectories are not tracked. The
reference trajectory for a given system and IC set depends only on the sampling protocol — 512 points
over t ∈ [0,10], self-integrated with `Tsit5` at 1e-9 — and not on the basis, the arm or the search,
and that protocol is frozen and identical across both phases, so the two should be the same numbers.
**Nothing in the pipeline checks it**, and the controls above cannot: they test `r2_by_dim` against
`r2`, which is internal to the record and passes whatever the weights are. The Phase B registry
carries no `u0`, so it cannot be checked after the fact either. For Phase C the question does not
arise, since export and records come from the same run.

---

## 7. Decisions on the questions this document left open

All five were open on 2026-09-09 and all five are **decided 2026-09-10**. They are recorded here
with their reasoning because a decision without its reason is re-opened by the next reader.

**Q1 - Scope of the SINDy comparison (Claim D). Decided: all 63 systems, paired and stratified.**
Pairing is per (system, IC set); stratification is by dimension **and** by three-way
representability; there is **no aggregated headline number across strata**. The WP-N6 objection was
never about the system count but about mismatched aggregation units - 11 selected systems x 2 bases
against all 23 dim-1 systems. Phase C removes that mismatch by construction: C-1 covers all 63
systems on the same self-integrated trajectories SINDy receives, so the pairing costs nothing. Two
declarations travel with the table: SINDy is deterministic while EvoGrow carries three seeds, so the
seed handling is stated explicitly rather than implied; and SINDy's figure remains the maximum over
its reported configuration set, deliberately in its favour.

**Q2 - How the restart ablation runs. Decided: through the oracle path, not through full search.**
`wp_n4_multistart_refit.jl` reads C-1's `history.jsonl`, holds the structure fixed and varies only
the parameter start, over k in {1, 2, 3, 5, 10}. This is the only design that isolates k: in the
full search the implicit multistart from structure duplicates varies at the same time, so a
recovery-versus-k curve from full runs would measure two things at once. Cost is under 20 core hours
and no campaign arm is added. The measured `StructureSpec` duplicate rate from C-1 is reported
beside the curve as the implicit multistart, and the curve's x-axis is **fits, never k**.

**Q3 - Basis of the oracle arm. Decided: canonical basis only.**
The oracle answers whether a failure belongs to the search or to the optimizer **in the method as
configured**. Running it on both bases would answer a basis question, and the basis question is what
P2 and P3 exist for. The argument is scope, not cost.

**Q4 - Pretuning ablation. Decided: a confirmation arm of 120 cells, not a citation and not a full
mirror.** The 20 exact systems x 3 seeds x 2 IC sets with `pretuning = true` on the canonical basis,
arm C-3. Citing Phase B's WP-A7 would have been defensible - it is measured on raw `support_terms`
and therefore threshold-independent - but if P3 freezes a different basis, the citation crosses a
configuration boundary in the paper's own ablation section. A full 378-cell mirror was rejected as
disproportionate. **The cost of this decision is stated in section 2 and is not small: ~2,400 core
hours at the current 180-cell scope, and in the 120-cell measurement it was 1,331 h with 98.7 % of
it in 24 dim-3 cells.** Including dim 3 was chosen deliberately so the collapse is
measured where the method is weakest.

**Q5 - Pilot and go criterion. Decided: a ~~12~~ **16**-cell pilot, distinct from the P9 smoke test.**
**Corrected 2026-09-14 (WP-N18): "12 cells" does not follow from this rule.** All four dimension
classes have exact systems under the canonical basis, so the rule yields 4 x 2 arms x 1 seed x 2 IC
sets = **16**. The rule is kept and the count corrected - narrowing a pre-registered rule so a
number matches would be the wrong direction. Frozen selection: systems **2, 24, 52, 63**, seed
**42**, four cells per dimension class, all eight pairs adjacent in the index list. Two properties
are declared: system 52 is one of the ten newly exact systems, so its Phase B cost figure comes
from a basis under which it was a surrogate; and system 63 is the identifiability limit whose cap
was `nothing` everywhere on the old basis - whether that still holds under the canonical basis is
unknown, and the pilot will show it.
The smoke test asks whether the cluster path runs at all; the pilot asks whether the **records are
fit for the claims**. Scope: the cheapest exact system per dimension class, selected by Phase B
median cell cost - a rule fixed in advance, not a pick after seeing Phase C - crossed with arms C-1
and C-2, one seed, both IC sets. The go criterion is all five of:

1. every cell completes with `success == true` and no `failure_reason`;
2. one identity triple across all pilot records, and it matches the manifest;
3. every new field is present and non-null: raw support, pruned match, coefficients, `basis_name`,
   support-definition tag, duplicate counters, restart counters;
4. the section 2b identical-conditions diff between the paired C-1 and C-2 cells shows differences
   **only** in stage-cap fields;
5. `wp_n5_ic_generalization.jl` reproduces the reconstruction control exactly to zero on every pilot
   cell, proving the records can rebuild their own models.

A failure of (4) or (5) is a hard stop: (4) invalidates Claim B and (5) invalidates Claim C, and
both are cheaper to find now than after 11,500 core hours.

---

## 8. What remains open

Not questions about this document any more, but work and one genuine unknown.

**~~The canonical basis (P2/P3) is the last open frozen parameter.~~ Closed 2026-09-13** — the
constant basis is canonical, and the basis-shaped hole in section 2's arms is filled. B1, B4 and B7
are unblocked. What remains open about the basis is not a decision but a declared limitation: the
constant's benefit is measured on dimension 1 (generalization) and its cost on dimension 2
(structure recovery), and no single run measures both on the same dimension.

**The restart policy's premise was in doubt and the first coupled measurement supports it.** `k = 3`
was frozen on WP-N4, which measured that a single fit hits the sentinel loss in 15 of 102 cells.
WP-N10 then measured that on dim 1 a structure receives 55 to 97 fits, so "a single fit" is a state
the search does not produce there, and the premise looked unfounded.

The first dim-2 cell (system 26, seed 42, IC 1) points the other way. The aggregate duplicate rate is
comparable — 85.5 % against 98.2 % and 99.0 % — but **the distribution is not**: repeats per structure
run from a minimum of **1** through a median of **5** to a maximum of 32, against 55 to 97 on
dimension 1. Structures that receive exactly one fit **do** occur on coupled systems, and that is
precisely where an explicit retry-on-failure bites. **One cell decides nothing** — it shows the order
of magnitude. C-1 supplies the distribution over 378 cells. C-1 supplies that distribution over 378 cells at no extra cost, but the
policy had to be built before C-1 starts — and it was, on 2026-09-10 (WP-N11), **before its premise
is settled**. What softens this is that the implementation is behaviour-neutral at its default of
k = 1 and was verified so; the choice of k = 3 is a separate act, and it happens in the Phase C
configuration where it can still be revised on C-1's own duplicate-rate distribution.
**The ordering remains a known defect of the plan and is declared rather than hidden:** if the
duplicate rate on dim 2 and 3 turns out high, the honest reporting is that the explicit retry adds
little on top of a large implicit multistart, and that statement is made from Phase C's own data.
