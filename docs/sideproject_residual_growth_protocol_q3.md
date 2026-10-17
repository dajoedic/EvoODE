# Side project "residual-guided growth" — frozen protocol for Q3 (weak-form warm start)

**Frozen 2026-10-17, before any Q3 number was computed.** Part 2 of the side project; part 1 (Q1/Q2) is
`docs/sideproject_residual_growth_protocol.md` (`e61f48f`) and stays unchanged. Order decided by the user on
2026-10-17: Q3, then model-size selection without oracle, then noise. Thresholds are Claude's proposal under the
user's mandate, human design choices, not derived from data.

## 1. Question

Does a start at the weak-form least-squares coefficients defuse the trajectory-space parameter fit (failure class B)?
Measured on the **true** structure, against the existing P-04 restart curve (random starts, same optimizer).

Not claimed: anything about wrong structures, noise, or generalisation; not a method yet.

## 2. Units, data, strata

- Unit: (system, IC) of the 30 exact systems — 60 units. The weak start does not depend on the seed, so one fit per
  unit. Training trajectory = the campaign trajectory of that (system, IC) (WP-C4c export; in Julia the trajectory the
  P-04 runner builds — both must agree, see controls).
- Strata as WP-FA1/WP-FA2: **primary** `dim1`, `dim2`, `dim3_feasible` (52, 61); **reported only**
  `dim3_bound_infeasible` (54–59), `dim4` (63).

## 3. Arms

- **Weak coefficients c_w:** per equation, least squares of the WP-T1 weak design (as in WP-FA2: uncentred, constant
  as an ordinary column, orthogonal-factorisation solver) on the columns of the true support only. Parameter order =
  the order `build_rhs` uses for the true `StructureSpec`.
- **W0 (no optimisation):** simulate c_w on the training trajectory with exactly the simulation settings of the P-04
  fit (`build_reference_optimizer(max_fit_attempts = 1)`: tolerances, `clamp_val = 10`, divergence guards) → loss,
  R².
- **W1 (one fit from the weak start):** exactly the P-04 single fit (`_fit_fixed_structure_once` semantics:
  reference optimizer, `max_fit_attempts = 1`, same loss-evaluation budget, bound 10), with `p0 = c_w` instead of the
  random start → loss, R², loss evaluations.
- **Reference P-04** (existing, not re-run): the 10 single-attempt random starts per C-1 exact cell
  (`outputs/phase_c_c5_restart_curve_5dd1df8/`), best-of-k by loss for k = 1, 3, 10, as in the restart-curve
  aggregation. Three cells (seeds) per unit.

## 4. Metrics and rules

R² > 0.9 on the training trajectory (reconstruction) is the success criterion. Rates: weak arms over units, P-04 over
cells (each unit carries three cells; the rate is comparable because the weak arm is seed-free).

| Rule | Criterion, per primary stratum | Question |
|---|---|---|
| R5 | W1 rate ≥ P-04 best-of-10 rate | Does one weak-start fit match ten random starts? |
| R6 | W1 rate ≥ P-04 best-of-3 rate | Does it beat the C-1 condition (k = 3)? |

Reported, no rule: W0 rate; W1 loss evaluations against the P-04 sum over k = 3 and k = 10 starts (median per unit);
W1 loss against the P-04 best-of-10 loss (better / equal within 1e-12 relative / worse); number of c_w entries with
|c| > 10 (clipped by the bound); units where W1 ends at the sentinel loss.

## 5. Reading (fixed in advance)

- **R5 passes** → one weak-start fit is at least as good as ten random starts on the true structure: class B is
  defused at σ = 0, and a weak warm start in EvoGrow is justified.
- **R6 passes, R5 fails** → better than C-1's three starts, short of ten: partial help.
- **R6 fails** → the weak start does not defuse the trajectory-space fit; the difficulty is in the trajectory loss
  itself (dynamics, bound, divergence), not in the start.
- Whatever the outcome, W0 shows whether the optimiser is needed at all on top of the weak fit.

## 6. Controls

- The Julia trajectory and the WP-C4c export agree for every unit (time grid identical, state within the hash of the
  export or, if hashes differ by construction, max relative difference reported and < 1e-8).
- A W1 fit with `p0 = nothing` and the P-04 start seed for start 1 reproduces the P-04 start-1 loss bit-identically on
  at least three units (dim 1, dim 2, dim 3).
