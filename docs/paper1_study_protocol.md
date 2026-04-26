# Paper 1 — Study Protocol

This document is the single source of truth for all experiments, analysis, and
evidence related to Paper 1.

Every result that appears in the paper must be traceable to a hypothesis defined
here, an experiment defined here, and a metric defined here.

If a result cannot be traced — it must not appear in the paper.

---

## 0. Core Goal

Paper 1 is not about building the best ODE discovery system.

The paper studies:

> Staged growth as a mechanism for controlled complexity increase in
> data-driven ODE discovery.

The contribution is a **design principle and its empirical validation**,
not a state-of-the-art benchmark result.

---

## 1. Core Claims

### Main Claim

Staged complexity release with stage-local stopping criteria improves complexity
efficiency — reducing stage overshoot and wasted search levels — in data-driven
ODE structure discovery, without sacrificing recovery quality.

Throughout this protocol, the term **complexity efficiency** refers to the joint
behavior of `stage_overshoot` and `wasted_levels`. Controlled complexity increase
means low complexity efficiency cost. Lower values indicate more efficient use of
the search budget.

### Sub-Claims

**C1 — Overshoot reduction**
Stage-local plateau detection reduces stage overshoot compared to global plateau
detection and flat growth.

**C2 — Recovery quality**
EvoGrow variants with staged release achieve exact structure recovery at rates
comparable to flat search (EvoGrow v1) and GP baseline, while achieving lower
complexity efficiency cost — lower stage_overshoot and wasted_levels than
EvoGrow v1 and v2.1. Recovery quality and complexity efficiency are jointly
evaluated but represent distinct dimensions of the contribution.

**C3 — Usage policy effect (secondary)**
The usage policy after stage unlock (hard / soft / passive) has a measurable but
secondary effect on recovery rate in higher-complexity systems.

Each claim is specific, testable, and falsifiable.
A claim is falsified if the stated direction does not hold across the majority of
systems and seeds.

---

## 2. Hypotheses

Each hypothesis maps exactly to one claim and one measurable outcome.

---

**H1** (→ C1)
For exact systems with expected stage ≥ 2, EvoGrow v2.2 (stage_local progression)
shows lower mean `stage_overshoot` than EvoGrow v2.1 (global_plateau) and
EvoGrow v1 (flat).

- Measurable outcome: `mean_stage_overshoot` per (variant, system)
- Required systems: exact systems with expected_stage ≥ 2 (IDs: 3, 11, 24, 26, 31, 54, 63)
- System 2 (expected_stage = 1) is excluded from this hypothesis — overshoot is
  undefined when no promotion is possible

---

**H2** (→ C2)
For exact systems, EvoGrow v2.2 (stage_local progression) achieves competitive
exact_match_rate alongside demonstrably lower complexity efficiency cost (H1, H3).
"Competitive" is defined as: exact_match_rate does not show systematic degradation
relative to the GP baseline across the majority of exact systems. The claim is the combination —
comparable recovery with reduced complexity efficiency cost — not recovery
superiority alone.

- Measurable outcome: `exact_match_rate` per (variant, system), evaluated
  jointly with `mean_stage_overshoot` and `mean_wasted_levels`
- Required systems: all 8 exact systems
- Falsified if: EvoGrow v2.2 shows lower exact_match_rate than GP on the
  majority of exact systems AND shows no improvement in complexity efficiency
  (stage_overshoot, wasted_levels) relative to EvoGrow v1

---

**H3** (→ C2)
For exact systems with expected stage ≥ 2, EvoGrow v2.2 (stage_local progression)
shows lower `mean_wasted_levels` than EvoGrow v1 (flat) and EvoGrow v2.1
(global_plateau). This is a comparison between EvoGrow variants only.

- Measurable outcome: `mean_wasted_levels` per (variant, system)
- Required systems: exact systems with expected_stage ≥ 2
- GP baseline: excluded. `wasted_levels` is undefined for methods without staged
  structure. GP participates only in the recovery comparison (H2).

---

**H4** (→ C3, secondary)
Among EvoGrow v2.2 variants, hard usage policy achieves higher `exact_match_rate`
than passive on systems requiring stage ≥ 3. Soft is intermediate.

- Measurable outcome: `exact_match_rate` per (variant, system) for
  {v2.2_progression, v2.2_passive, v2.2_soft}
- Required systems: exact systems with expected_stage ≥ 3
  (IDs: 11, 26, 31, 54, 63)
- This hypothesis is **secondary**. If results are ambiguous, C3 is weakened
  but C1 and C2 remain unaffected.

---

## 3. Experiment Scope

### 3.1 Systems

Ten systems total. Split into two evaluation categories that must never be merged.

#### Exact systems (8)

| ID | Name | Dim | Expected stage | Role |
|----|------|-----|----------------|------|
| 2 | Population growth | 1 | 1 | Sanity check only |
| 3 | Logistic growth | 1 | 2 | Mechanism visualization + quantitative |
| 11 | Critical slowing down | 1 | 4 | Quantitative (high complexity) |
| 24 | Harmonic oscillator | 2 | 1 | Sanity check only |
| 26 | Lotka-Volterra competition | 2 | 3 | Quantitative |
| 31 | SIR model | 2 | 3 | Quantitative |
| 54 | Lorenz (periodic) | 3 | 3 | Quantitative (high dim) |
| 63 | SEIR model | 4 | 3 | Quantitative (high dim) |

Systems 2 and 24 (expected_stage = 1) are included only as sanity checks.
They verify that all methods find trivial structure. They are reported separately
and excluded from H1, H3, H4.

System 3 (logistic) is the primary mechanism visualization system: simplest
non-trivial case, exact structure known, stage progression is interpretable.

#### Surrogate systems (2)

| ID | Name | Dim | Expected stage | Role |
|----|------|-----|----------------|------|
| 23 | Overdamped pendulum | 1 | 5 | Surrogate analysis only |
| 37 | Van der Pol oscillator | 2 | 4 | Surrogate analysis only |

Surrogate systems are evaluated separately on:
- stage reached
- whether target term class appears in discovered structure
- fit quality (mean_loss)

`exact_support_match` must not be reported for surrogate systems.
Surrogate results may appear in an appendix or a dedicated discussion paragraph,
but must not be used to support H1–H4.

### 3.2 Variants

Six variants are included. All are already implemented and present in Phase A.

| Label | Slug | Included in | Notes |
|-------|------|-------------|-------|
| EvoGrow v1 (flat) | `evogrow_v1` | H2, H3 | Flat baseline |
| EvoGrow v2.1 | `evogrow_v2_1` | H1, H2, H3 | Global plateau baseline |
| EvoGrow v2.2 progression | `evogrow_v2_2_stage_local` | H1, H2, H3, H4 | Primary variant |
| EvoGrow v2.2 passive | `evogrow_v2_2_passive` | H4 | Usage policy comparison |
| EvoGrow v2.2 soft | `evogrow_v2_2_soft` | H4 | Usage policy comparison |
| GP baseline | `gp_baseline` | H2 (recovery comparison only) | External baseline; excluded from H3 |

Minimum viable set for the main claims (H1–H3):
`evogrow_v1`, `evogrow_v2_1`, `evogrow_v2_2_stage_local`, `gp_baseline`

The three v2.2 usage-policy variants are required only for H4.
If H4 results are ambiguous, they may be moved to supplementary material.

GP baseline does not participate in H1 or H4 — no stage structure, no usage policy.
Stage overshoot metrics must not be computed or reported for GP.

### 3.3 Seeds

Five seeds per (variant, system) cell: `[42, 123, 7, 99, 17]`.

Multi-seed is mandatory for all quantitative claims.
Single-seed results are allowed only for mechanism visualization (e.g. showing
a single stage progression trace for System 3).
No quantitative claim may rest on fewer than 3 valid runs.

A cell with fewer than 3 valid runs is reported as `n_valid < 3` and excluded
from hypothesis evaluation. It is not excluded from the table — it appears with
a note.

### 3.4 Budgets

Budgets are fixed as defined in `CLAUDE.md` (Paper 1 Reproducibility Protocol):

```
EvoGrow: n_levels = 20
GP:      n_generations = 20
```

Budgets are equalized across methods (20 iterations each).
This is an approximation: one EvoGrow level and one GP generation are not
computationally identical. This approximation is acceptable and must be stated
explicitly in the paper.

No budget adjustments are made post-hoc. If a method requires more budget
to succeed, that is a finding, not a reason to re-run.

---

## 4. Metrics

### 4.1 Primary Metrics

These metrics directly support the core claims. They appear in main-paper tables
and figures.

---

**`exact_match_rate`**

Definition: fraction of valid runs in a (variant, system) cell where discovered
term indices match ground-truth term indices exactly for all equations.

Valid: exact systems only (IDs 2, 3, 11, 24, 26, 31, 54, 63).
Must NOT be used: surrogate systems.
Aggregation: mean over valid runs. Report `n_valid` alongside.

---

The following two metrics jointly operationalize **complexity efficiency** —
the central measurable construct of C1 and C2.

**`mean_stage_overshoot`**

Definition: mean of `stage_overshoot = final_stage - expected_stage` over valid
runs. Negative values indicate undershooting.

Valid: EvoGrow variants only. Exact systems with expected_stage ≥ 2 only.
Must NOT be used: GP baseline (no stage structure). System 2 and 24
(expected_stage = 1, promotion never triggered).
Aggregation: mean over valid runs. Report alongside `std_stage_overshoot`.

---

**`mean_wasted_levels`**

Definition: mean of `wasted_levels` over valid runs. `wasted_levels` is defined
as the number of levels spent in stages beyond `expected_stage`.

Valid: exact systems with expected_stage ≥ 2.
GP baseline: excluded. `wasted_levels` is not defined for GP.
Aggregation: mean over valid runs.

---

### 4.2 Secondary Metrics

These support interpretation. They appear in tables or supplementary material
but do not directly support claims.

---

**`mean_loss`**

Definition: mean simulation MSE over valid runs.

Valid: all runs, all systems.
Use: to confirm that low-overshoot variants are not sacrificing fit quality.
Do not use to rank methods as primary criterion.

---

**`mean_final_stage`**

Definition: mean of `final_stage` over valid runs.

Valid: EvoGrow variants only.
Use: to interpret stage progression behavior, especially for surrogate systems.
GP: set to -1 by convention. Do not report as a numeric mean.

---

**`mean_elapsed_s`**

Definition: mean wall time in seconds over valid runs.

Valid: all runs.
Use: to characterize runtime cost, not as a primary claim.
Do not claim runtime superiority without controlled comparison conditions.

---

**`mean_invalid_evals`**

Definition: mean number of evaluations producing NaN or failed simulation per
run, over valid runs in a (variant, system) cell.

Valid: all runs, all variants.
Use: to characterize search stability. A high invalid rate on a system indicates
that the search space contains many numerically unstable candidates for that
system — this contextualizes low exact_match_rate results without making a
stability claim.
Do not use to rank methods. Do not claim one method is more stable without
consistent directional evidence across multiple systems.
This interpretation is contextual only — high invalid rates do not constitute
evidence of method inferiority.

---

### 4.3 Tertiary Metrics

Exploratory only. Not used to support any claim in the paper.

- `total_loss_evals`: total loss function call count
- solver failure rate per system

These may appear in a methods discussion paragraph but must not appear in tables
or figures used as evidence.

---

### 4.4 Statistical Treatment

All metrics are reported as descriptive statistics only.
No significance tests. No p-values. No confidence intervals.

For each (variant, system) cell, report:
- `n_valid` (count of valid runs)
- mean and standard deviation of the metric over valid runs

When `n_valid = 1`: report the single value, note `n=1`, exclude from
cross-variant comparisons.
When `n_valid = 0`: report as `—` in tables. Exclude from all comparisons.

Claims are supported by consistent directional patterns across multiple systems
and seeds, not by individual cells.

---

## 5. Success and Failure Semantics

### 5.1 Run-level definitions

**`status`** (written by runner):

| Value | Meaning |
|-------|---------|
| `queued` | Not yet started |
| `running` | Started; if `finished_at = null` after process death → `interrupted` |
| `finished` | Completed without exception |
| `failed` | Exception caught by runner |
| `interrupted` | Inferred by aggregator only |

**`success`** (boolean):

`true` if and only if: run completed, finite loss is available, result and metrics
were written successfully.

`success` is a **technical judgment only**. It does not imply that the discovered
structure is correct or scientifically meaningful.

**`failure_reason`** (controlled enum):

| Value | Meaning |
|-------|---------|
| `exception` | Unhandled exception during discovery |
| `all_invalid` | All candidate evaluations produced NaN |
| `write_failure` | Result or metrics could not be written |
| `unknown` | Failure cause not determinable |

### 5.2 Analysis-level exclusions

A run is **excluded from metric computation** if `loss` is NaN.
All other valid runs are included regardless of loss magnitude.

Do not exclude runs based on loss threshold ("the loss was too high").
High loss is a scientific result, not a reason for exclusion.

Failed runs are not hidden. Tables report `n_valid` and `n_seeds` for every cell.
If `n_valid < n_seeds`, the discrepancy must be visible.

---

## 6. Allowed Evidence

### 6.1 Tables

**Table 1 — Main results (exact systems)**

Purpose: support H2 (recovery quality).
Rows: variants in fixed order.
Columns: exact systems, ordered by system_id.
Cell content: `exact_match_rate` (as percentage) and `mean_loss`.
Footnote: `n_valid` per cell.
Source: `aggregate_by_variant_system.csv`, exact systems only.

**Table 2 — Stage overshoot summary**

Purpose: support H1 and H3.
Rows: EvoGrow variants only (GP excluded — no stage structure).
Columns: exact systems with expected_stage ≥ 2.
Cell content: `mean_stage_overshoot` and `mean_wasted_levels`.
Optional third value per cell: `mean_invalid_evals` (if space allows; otherwise
reported in supplementary material).
Source: `aggregate_by_variant_system.csv`.

These are the only two tables allowed in the main paper.
Additional tables may appear in supplementary material for:
- surrogate system results
- per-seed breakdowns
- runtime characterization

### 6.2 Figures

**Figure 1 — Exact match rate (bar chart)**

Purpose: visual summary of H2.
Systems: all 8 exact systems on x-axis.
Variants: all 6, one bar per variant per system.
Y-axis: exact_match_rate (0–1).
Script: `scripts/plot/plot_exact_match_rates.py`

**Figure 2 — Stage overshoot (bar chart)**

Purpose: visual summary of H1.
Systems: exact systems with expected_stage ≥ 2.
Variants: EvoGrow only (GP excluded from this figure).
Y-axis: mean_stage_overshoot, reference line at 0.
Script: `scripts/plot/plot_stage_overshoot.py`

**Figure 3 — Stage progression trace for System 3 (qualitative mechanism illustration)**

Purpose: illustrate how stage-local and global plateau detection differ in
practice on the simplest non-trivial system. This figure supports narrative
and aids reader comprehension of the mechanism. It does not test a hypothesis,
must not be interpreted as quantitative evidence, and is not representative
of aggregate behavior across seeds or systems.

Content: best-objective-per-level for System 3 (logistic growth), variants
{evogrow_v1, evogrow_v2_1, evogrow_v2_2_stage_local}, seed = 42 (single seed,
explicitly stated in caption). Stage boundaries marked as vertical lines.

Placement: first figure in the paper, before Figure 1 and Figure 2.
Caption must state: "Single representative run (seed = 42). This figure is
illustrative and not representative of aggregate behavior. For aggregate
recovery results across all seeds, see Figure 1."

**Hard constraints on figures:**

- Maximum 3 figures in the main paper.
- Every figure must be generated by a script in `analysis/scripts/plot/`.
- No manually assembled figures.
- No figure may present surrogate system results as structural correctness evidence.

---

## 7. Generalization Study Role

The generalization study (`generalization_study.jl`) is **auxiliary evidence**.
It is not part of the main contribution.

### What it is allowed to claim

> A structure discovered by EvoGrow on one parameter set of a given ODE family
> can be refitted to unseen parameter sets of the same family with low loss,
> when the discovered structure is exact.

This supports the interpretation that exact recovery has practical meaning beyond
the training trajectory.

### What it is NOT allowed to claim

- That EvoGrow generalizes better than GP or SINDy
- That discovered structures are robust to out-of-distribution conditions
- That generalization performance is a valid substitute for exact_support_match
- That refit loss below any specific threshold implies structural correctness

### Interpretation rules

Runs without `exact_support_match = true` are excluded from the generalization
analysis. This is a hard filter, not an interpretation criterion: generalization
is only meaningful when the discovered structure is correct.

The claim is supported if, across systems with sufficient exact recoveries
(`n_exact_runs ≥ 3`), there is a consistent tendency for `mean_refit_loss` to be
lower than or comparable to `mean_fresh_loss`. No per-system strict inequality is
required. A single system where refit loss exceeds fresh loss does not falsify the
claim.

### Output

One supplementary table:

| System | n_exact_runs | mean_refit_loss | mean_fresh_loss |
|--------|-------------|-----------------|-----------------|

- `n_exact_runs`: number of training runs with `exact_support_match = true`
- `mean_refit_loss`: mean loss after refitting the discovered structure to unseen
  parameter sets, computed over valid exact runs only
- `mean_fresh_loss`: mean loss of fresh discovery runs on the same test trajectories

This table is placed in the supplementary material. It is referenced in the
discussion section with exactly one interpretive sentence. It does not appear
in the main results section. It does not generate a main-paper figure.

**Interpretation rule:** the table is interpreted as supporting the auxiliary
claim if there is a consistent tendency for `mean_refit_loss` to be lower than
or comparable to `mean_fresh_loss` across systems with `n_exact_runs ≥ 3`.
No strict inequality is required across all systems. If no such tendency is
visible in the data, the generalization claim is stated with explicit caution
rather than as a positive result.

---

## 8. Exclusion Rules

The following are explicitly **not part of Paper 1**:

**Algorithmic contributions excluded:**
- Pretuning (OLS warm-start) as a standalone contribution. It is an
  implementation detail. It may be mentioned in the methods section but
  cannot be framed as a result.
- Any optimization trick that reduces runtime without changing recovery behavior.

**Claim types excluded:**
- Runtime efficiency as a primary claim. `elapsed_s` is reported but not used
  to argue superiority.
- Large-scale benchmark claims. Ten systems with 5 seeds is not a large-scale
  benchmark. The paper makes no claim about performance across hundreds of systems.
- Statistical significance claims. No p-values, no hypothesis tests.

**System-level exclusions:**
- Surrogate systems (23, 37) in any structural correctness metric.
- Systems 2 and 24 in H1, H3, H4 (expected_stage = 1, overshoot undefined).

**Method-level exclusions:**
- GP baseline in stage overshoot or stage progression metrics.
- Any comparison against SINDy (not implemented, not reproduced here).

**Experiment-level exclusions:**
- Noise robustness experiments (not in Phase A).
- Sampling density experiments (not in Phase A).
- Dimensionality scaling experiments (not in Phase A).
- Any experiment not defined before results were seen. Post-hoc experiment
  design is not allowed.

**Analysis-level exclusions:**
- Cherry-picked seeds or runs.
- Excluding failed runs without reporting them.
- Any result derived from manually edited CSV files.

---

## 9. Experimental Phases

### Phase A — `paper1_phaseA_v1`

**Status:** primary evidence source for Paper 1.
**Scope:** 10 systems × 6 variants × 5 seeds = 300 runs.
**Role:** generates all main-paper evidence for H1–H4.
**Classification:** predefined, frozen evaluation protocol. All systems, variants,
seeds, hyperparameters, and metrics were fixed before aggregate results were
inspected. The internal config field `run_type = exploratory` reflects the
phase labeling scheme of the research project, not the scientific status of
the results. Phase A results are final.

Phase A is the only source of primary evidence for this paper.
Results from Phase A are final once all 300 runs complete.

If individual cells remain invalid after Phase A completes (n_valid = 0),
a targeted Phase B re-run may be initiated for those cells only.
Phase B re-runs must use identical configuration. They must be documented
separately and their results merged transparently into the analysis.

### Phase B — Targeted re-runs (conditional)

**Trigger:** cells with n_valid = 0 after Phase A.
**Scope:** only the affected (variant, system, seed) triples.
**Configuration:** identical to Phase A. No parameter changes.
**Status:** not yet initiated.

### Phases C and D

Not defined for Paper 1. Any future phase addresses a different research question
and generates a new paper or a follow-up study.

---

## 10. Minimal Execution Plan

Steps in dependency order. Do not proceed to a step before the previous one is complete.

**Step 1 — Complete Phase A**
Ensure all 300 runs have reached status `finished` or `failed`.
Run `julia experiments/aggregate.jl paper1_phaseA_v1` to produce `run_registry.csv`.
Acceptance criterion: `run_registry.csv` contains exactly 300 rows.

**Step 2 — Aggregate**
Run `python scripts/aggregate/aggregate_run_registry.py --config configs/paper1_phaseA_v1.json`.
Inspect `aggregate_by_variant_system.csv`.
For each (variant, system) cell: verify `n_valid` is plausible.
Flag all cells with `n_valid = 0` for potential Phase B.
Acceptance criterion: no unexpected structural issues in the aggregate CSV.

**Step 3 — Primary metric analysis**
Evaluate H1, H2, H3 using primary metrics from the aggregate CSV.
Do not generate paper figures yet. Work from the CSV directly.
Goal: determine whether the directional patterns in the data support the claims.
If H1 is clearly not supported → the paper's main claim must be revised.
This step must not be skipped or rushed.

**Step 4 — Freeze conclusions**
Write a short internal memo (not a paper section) stating:
- which hypotheses are supported
- which are ambiguous
- which are falsified
This memo defines what the paper is allowed to claim.
Nothing beyond the memo may appear in the paper.

**Step 5 — Generate figures and tables**
Run the three analysis scripts to generate Figure 1, Figure 2, and Table 1, Table 2.
Inspect outputs. Verify against the aggregate CSV.
No manual editing of figures or tables.

**Step 6 — Generalization study analysis**
Run `generalization_study.jl` if not already complete.
Evaluate refit vs fresh results for valid runs with exact_support_match = true.
Write the auxiliary discussion paragraph.

**Step 7 — Final validation**
Verify that every result in the paper draft traces to:
- a hypothesis in this document
- an experiment in Phase A (or Phase B if applicable)
- a metric defined in Section 4
If any result cannot be traced → remove it from the paper.

**Freeze condition**
The experimental setup is considered frozen when Phase A is complete and
Step 3 has been executed. After the freeze, no new experiments may be added
to Paper 1. If a new experiment is needed, it belongs to a future paper.

---

## 11. Open Questions (to be resolved before Step 4)

This question does not block Steps 1–3 but must be answered before writing.

1. **Phase B trigger:** Define the minimum `n_valid` below which a cell triggers
   a Phase B re-run. Suggested threshold: `n_valid < 3`.
   Confirm this threshold before Step 2 completes.
