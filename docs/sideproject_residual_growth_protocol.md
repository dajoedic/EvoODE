# Side project "residual-guided growth" — frozen protocol for Q1 and Q2

**Frozen 2026-10-17, before any Q1/Q2 number was computed.** Changes after the first result are not allowed; a
changed question gets a new protocol version. Background and decisions: `DIARY.md` 2026-10-17; concept sketch of the
user: `sideprojekt_residualgesteuertes_strukturwachstum.md` (untracked, repository root); structure inventory:
WP-FA1, `analysis/data/paper1_phaseC_v1/c1_structure_inventory/`.

**Status of the thresholds.** The user asked to fix comparison groups and go rules before evaluation and then
delegated the work ("work until done", 2026-10-17). The thresholds below are Claude's proposal under that mandate.
They are human design choices, not derived from data, and are reported as such.

Q3 (weak-form coefficients as a warm start) is **not** part of this protocol; it belongs to the failure anatomy and
is interpreted together with the user.

## 1. What is tested

- **Q1 — is the truth identifiable in the weak space on one trajectory?** If not, no residual rule can find it there.
- **Q2 — does the weak residual of EvoGrow's actual wrong structures point to the missing true terms, and does
  "add + joint weak refit + remove" reach the truth from there?**

What is **not** claimed: a new method. The guided step is orthogonal least squares (FROLS, Billings, Chen &
Korenberg 1989); Q2 measures the *information* available to such a step from realistic starts, not a novel algorithm.
Weak-space best-subset (Q1) is itself a cheap method; any later EvoGrow integration has to beat it.

## 2. Data and weak design (fixed)

- Clean data only (σ = 0). Training trajectory of each cell = the campaign trajectory of (system, IC) from the WP-C4c
  export (`outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/`, hashes checked on load). The other IC is
  never touched.
- 30 exact systems, true support from `studies/regression/phase_c_support.json`, canonical basis
  `staged_polynomial_basis_with_constant` (Python clone `phasec_basis`, verified by WP-T1). Stages are ignored: every
  basis term of the dimension is a candidate.
- Weak design exactly as WP-T1 (`build_design`, signal `weak`: integral form, box windows of 1, 2, 4, 8, 16 samples,
  trapezoidal rule). Columns are **not centred**; the constant is an ordinary column. Least squares on the raw design
  (columns may be scaled to unit norm for numerics; SSE is scale-invariant). No normal equations.
- SSE(S) = residual sum of squares of the least-squares fit of the target on the columns of S.

## 3. Units and strata

- **Q1 unit:** (system, IC, equation). 59 equations × 2 ICs = 118 units.
- **Q2 unit:** unique (system, IC, equation, S0), where S0 is the **pruned** found term set of that equation in a C-1
  cell (180 exact cells). The weak data do not depend on the seed, so cells with identical S0 collapse into one unit;
  the number of cells per unit is reported. Raw S0 is a secondary analysis.
- **Strata** as WP-FA1: `dim1`, `dim2`, `dim3_feasible` (52, 61) are **primary**; `dim3_bound_infeasible` (54–59)
  and `dim4` (63) are reported, never used for a decision. No pooling across strata in any decision.
- **Groups** (WP-FA1 equation class of S0): `subset`, `mixed`, `disjoint` (need addition); `superset`, `exact`
  (need no addition — negative controls).

## 4. Metrics

**Q1** (per Q1 unit, k* = |S*|):
- **Q1a:** rank of S* among all subsets of size k* by SSE. Ties count against S* (worst rank among equals).
  "Identifiable at known size" ⇔ rank 1.
- **Q1b:** margin log10(SSE of the best subset ≠ S* of size k* / SSE(S*)).

**Q2** (per Q2 unit with addition need, m = |S* \ S0|, an oracle step count — named as such, like oracle-|S| in WP-T1b):
- **G, guided forward (OLS):** m steps; each step adds the candidate with the largest SSE reduction under a joint
  least-squares refit of the current set plus the candidate.
  **Q2a:** all missing true terms added within m steps. Also reported: rank of each missing term in the first step.
- **G+B:** after G, backward elimination — repeatedly remove the term whose removal raises SSE least — down to size k*.
  **Q2b:** final set = S*.
- **Baselines on the same units:** OMP (step adds argmax |a_jᵀ r| / ‖a_j‖ with unprojected columns, then joint refit;
  same m, same backward step); random addition (analytic probability that m random additions out of the p − |S0|
  candidates contain all missing terms); **F0**, OLS forward from ∅ for k* steps on the same (system, IC, equation)
  — exact or not; ceiling: Q1a.

**Q2c, "should it grow at all?"** (every Q2 unit, all classes): the share of the signal explained by the best single
addition, ρ = (SSE(S0) − min_j SSE(S0 ∪ {j})) / ‖b‖². Primary: AUC of ρ separating units that need addition from
units that do not (`exact`, `superset`). Secondary: the same with ρ' = (SSE(S0) − min_j SSE(S0 ∪ {j})) / SSE(S0).

## 5. Go rules (per primary stratum)

| Rule | Criterion | Question |
|---|---|---|
| R1 | Q1a rank 1 in ≥ 80 % of the stratum's Q1 units | Is the information there? |
| R2 | Q2a in ≥ 70 % of the stratum's Q2 units with addition need | Does the residual point to the missing terms from EvoGrow's real starts? |
| R3 | Q2b(G+B) exact count ≥ F0 exact count on the same (system, IC, equation) set | Does EvoGrow's wrong start trap the residual compared with starting empty? |
| R4 | Q2c AUC ≥ 0.80 | Is there a reliable signal *whether* to grow? |

Counting rules, no p-values: the primary strata hold 2 to 11 systems, and S1 showed that a permutation gate at that
size only passes for very large effects.

## 6. Reading (fixed in advance)

- **R1 fails** in a stratum → the weak space on one trajectory does not single out the truth there; residual guidance
  cannot help; the lever is data (more trajectories) or the criterion. Line stops for that stratum.
- **R1, R2, R3 pass** → the information is present and reachable from EvoGrow's wrong structures by add + refit +
  remove; EvoGrow loses it in trajectory-space search or fit. Next step (separate decision with the user): an
  integration experiment that must beat weak best-subset itself.
- **R1 passes, R2 or R3 fails** → EvoGrow's starts trap the residual (substitute terms absorb the missing ones); removal
  or replacement comes before growth.
- **R4 fails** → no reliable "grow or not" signal in the weak space even at σ = 0; a growth trigger needs a different
  criterion.

Reported in every case, per stratum and per system: all four rules, raw S0 next to pruned S0, OMP next to G, and the
condition numbers of the weak designs.
