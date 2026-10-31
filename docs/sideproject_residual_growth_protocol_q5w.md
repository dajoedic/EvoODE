# Side project "residual-guided growth" — protocol Q5-W (published WSINDy as the reference)

**Drafted 2026-10-30; frozen 2026-10-30 by the user, with acceptance §5 revised the same day (see §5, "Revision") before any C-6 cell was run.** Companion to Q5
(`docs/sideproject_residual_growth_protocol_q5.md`, `f737939`). Reason: Q5's primary reference is pysindy's
`WeakPDELibrary` + `STLSQ` at two fixed thresholds — **not** the published WSINDy, which selects its threshold from the
data. An interim look at system 61 (`DIARY.md` 2026-10-29) showed the fixed-threshold Weak-SINDy finding the true terms
with near-exact coefficients and losing only to spurious sin/cos terms the threshold did not cut. A comparison claim
needs the stronger opponent, on the same library, with the same size prior.

**Declared prior knowledge:** before this protocol, Q5 results and the existing Weak-SINDy rows were seen for
**system 61 only** (44 noisy cells). Nothing of the arms below has been computed.

## 1. Question

On identical data and an identical candidate library, does Q5 (rule c) still recover structure more often than the
published WSINDy with automatic threshold selection — with and without the same 6-term-per-equation size limit — and at
what cost? Q5-W reports; there is no pass/fail rule and no pre-written reading. The interpretation is made jointly.

## 2. Data and units

- All **4,536 cells** of the C-6 export `outputs/phase_c_c6_data_conditions_5dd1df8` (63 systems × 2 training ICs ×
  (0, 0) and 11 noisy/subsampled conditions × 3 realizations; the (0, 0) cells as exported). Per-cell
  `observed_data_sha256` must equal the WP-N47 rows (`outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv`).
- **Comparison with Q5:** only the cells Q5 ran (48 units × 34 data sets; strata as Q5 §2), joined on
  (system, training IC, σ, ρ, realization). The remaining cells serve Paper 1 as an additional C-6 baseline row; they do
  **not** change the frozen decision rule §9.4d of the Phase C plan and are reported apart from it.
- The method sees only the observed training data. Evaluation exactly as the C-6 baselines
  (`analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`): reconstruction from the clean training IC against
  the clean training trajectory, generalization from the clean other IC, DOP853 as WP-N47, same R² definitions, same
  raw/pruned structure hits (pruning `max(1e-6, 1e-3·max_abs)` per equation), same truth (`true_terms`).

## 3. Reference implementation: WSINDy as published

Source of truth, in this order:
1. **The official ODE code**, MathBioCU/WSINDy_ODE, commit `72d8d6e5be2b80bcfe5015dced399ace1ceca43f`, archive SHA-256
   `7ea9c4a427294a4dc707d1bed51d7ebbeae55c592071cac571774f90adcf6ca4`, kept read-only under
   `outputs/reference_wsindy_ode_72d8d6e/` (gitignored: the code is "All Rights Reserved", it is **read and
   re-implemented, never copied** into the repository). Entry points: `wsindy_ode_script.m`, `wsindy_ode_fun.m`,
   `wsindy_pde_RGLS_seq.m`, `sparsifyDynamics.m`, `findcorners.m`, `get_optimal_SMAF.m`, `phi_int_weights.m`,
   `build_theta.m`.
2. **Messenger & Bortz, J. Comput. Phys. 443 (2021), arXiv 2007.02848**: MSTLS (4.4)–(4.6), scaling (4.7)–(4.8),
   test-function selection Appendix A — where the code is silent.
3. The ODE paper (Multiscale Model. Simul. 2021, arXiv 2005.04339) is **not** the reference for thresholding: it sets
   λ = ¼·min|w*| from the true coefficients (§3.2–3.3), i.e. oracle information.

**Settings: the code's documented `DEFAULT` values**, where the script's value and the `DEFAULT` comment differ the
`DEFAULT` comment wins (only `K_frac`: `DEFAULT 1` → K = number of time points; the script's 1000 is an example
setting). Concretely: `phi_class = 1` (piecewise polynomial), `[tau, tauhat] = [1e-16, -1]` (corner point),
`K_frac = 1`, `scale_Theta = 2`, `lambda = 10.^linspace(-4, 0, 100)`, `alpha_loss = 0.8`, `gamma = 0`,
`smoothing_window = ceil(M/100)` with the code's automatic smoothing decision, `max_d = 1`, `overlap_frac = 1`,
`relax_AG = 0`, `useGLS = 0`. λ is chosen **per equation** (`wsindy_ode_fun.m` calls `wsindy_pde_RGLS_seq` per state),
ties to the smallest λ. The library is **not** the code default (`polys 0:5`) but the libraries of §4.

**Two bindings the code does not cover, declared deviations:**
- **Irregular time grids (ρ = 0.5).** The code assumes uniform spacing (`dt = mean(diff(t))`, convolution). Binding:
  test functions are defined in time units (support from the corner method with `dt = mean(diff(t_obs))`), centred on
  observed times, and every weak integral is evaluated by the trapezoidal rule on the **actual** observed times — the
  same treatment Q5 received. Corner detection and smoothing run on the observed samples as if uniform (the code's own
  behaviour); stated, not repaired.
- **Noise model.** The code and papers assume additive white noise; C-6 noise is multiplicative Gaussian. Applied
  unchanged.

## 4. Arms (all on the same cells)

Libraries, both used for every arm:
- **L-C6**: `poly_deg3_sin_cos` exactly as the C-6 baselines (constant, all monomials to degree 3 incl. mixed,
  `sin(x_i)`, `cos(x_i)`).
- **L-Q5**: the canonical Phase C basis Q5 searches (`staged_polynomial_basis_with_constant`: `1, u_i, u_i², u_i·u_j,
  u_i³, sin(u_i), cos(u_i)`), term names mapped one-to-one; the mapping is part of the acceptance.

Arms:
- **W1 — WSINDy as published** (§3).
- **W1-cap — W1 with Q5's size prior:** per equation, λ̂ is the loss minimiser among the grid λ whose model has
  **≤ 6 terms in that equation** (Q5's cap, which is derived from the truth: twice the largest true equation size).
  If no grid λ qualifies, the equation is reported as unselected (counted as a miss).
- **W2 — MSTLS only:** the existing pysindy weak design of WP-N34/N47 (`WeakPDELibrary`, K = 100, p = 4, seeded as
  WP-N45b) with MSTLS + the §3 λ grid, loss and scaling instead of fixed-threshold STLSQ. Isolates the threshold
  selection from the test functions.

Q5 side: Q5 rule (c) as frozen; Q5 rules (a), (b) reported beside it as in Q5 §6.

## 4a. Addendum 2026-10-31 — arm W1-interp (added after the provisional opening)

**Declared:** drafted on 2026-10-31 **after** the user opened the Q5-W results provisionally (`DIARY.md` 2026-10-31).
Known at drafting time: on ρ = 0.5 cells W1 falls far below W1 on ρ = 0 already at σ = 0 (dim 1 reconstruction 49/138
against 138/138), and below the fixed-threshold Weak-SINDy. The arm is added because the irregular-grid binding of §3 is
our own construction, not the published method; it is **not** added to improve any rate, and both W1 and W1-interp are
reported on ρ = 0.5.

- **W1-interp:** on every ρ = 0.5 cell, the observed data are interpolated **piecewise linearly, per state**, onto a
  uniform grid of **M = number of observed points** spanning [first, last observed time]; then W1 runs unchanged (§3, the
  uniform-grid path) on that grid, libraries L-C6 and L-Q5. Linear, because it adds no smoothing and no extrapolation of
  its own; WSINDy's own smoothing decision then applies. No other interpolant is run.
- On ρ = 0 cells the interpolation is the identity; W1-interp is not run there (a test shows identity on a sample).
- Evaluation, truth and metrics exactly as §2. Interpolation never touches the evaluation data.
- **Identity with the original (§5.5 extension):** because the interpolated input is uniform, W1-interp × L-C6 (and L-Q5
  if expressible) is exported and checked against the MATLAB original with the §5.5 criterion — the same gate, the same
  consequence on failure.
- Reporting: W1 and W1-interp side by side on ρ = 0.5, neither replacing the other; Q5 receives no interpolation.
- **Literature check, same day (`DIARY.md` 2026-10-31):** no WSINDy/WENDy paper or official code handles irregular
  sampling within a trajectory; WENDy (§2.1) and WENDy-MLE (fn. 2, §4) name actual-grid quadrature weights as the
  extension "in principle" — the binding W1 already uses. Interpolation onto a uniform grid has no precedent in ODE
  discovery benchmarks (ODEFormer feeds baselines the raw irregular times) and documented bias. Hence: **W1 is the
  primary row on ρ = 0.5, W1-interp a declared sensitivity arm.**

## 5. Acceptance before any C-6 cell is run

1. **Published example:** the official script's own example — Lorenz (σ = 10, β = 8/3, ρ = 28), x0 = (−8, 7, 27),
   t = 0:0.001:10, ode tolerance 1e-12, code defaults with `polys = 0:5`. (i) Noise-free: exact support, relative
   coefficient error E∞ ≤ 1e-4. (ii) 10 % additive white noise as `gen_noise.m` (σ = 0.1·rms), 20 numpy seeds:
   reported in full (support hits, E∞, E2, λ̂). **Reported only, not a gate** (revision below).
2. **Library mapping:** L-C6 column names and order identical to the pysindy library of WP-N47; L-Q5 term names
   identical to Q5's basis names after mapping.
3. **Evaluation identity:** fed WP-N47's stored `weak_sindy_poly_deg3_sin_cos_stlsq_0.1` coefficients, the evaluation
   path reproduces WP-N47's R² and structure fields on ≥ 100 cells bit-identically (or names the exception).
4. **Determinism:** two runs on 20 cells, identical output.
5. **Identity with the original code, run in MATLAB** (base MATLAB, no toolbox; the code's own noise generator is not
   used, every input is passed in). The unmodified official code (§3, commit `72d8d6e`) is called through
   `wsindy_ode_fun` with the §3 settings on:
   (a) the 21 Lorenz data sets of point 1 (clean + 20 noisy seeds, identical arrays), and
   (b) **every C-6 cell with a uniform time grid (ρ = 0)**, arm W1, library L-C6; L-Q5 as well if the code's
   `polys`/`trigs`/`custom` inputs express it exactly (decided by the mapping test of point 2, not by results).
   Pass: in every equation of every cell the same support and the same λ̂ grid index as the port, and coefficients
   equal up to max |Δc| ≤ 1e-6·max |c| per equation. Any cell outside this is a failure: the port is not accepted, the
   cause is investigated and reported to the user, nothing is tuned. Irregular-grid cells (ρ = 0.5), W1-cap and W2 have
   no counterpart in the original code and are covered by the port only — declared.

**Revision 2026-10-30 (user), before any C-6 cell was run.** The draft's gate "exact support in ≥ 15 of 20" for point
1(ii) had no published basis (the paper reports no such rate) and was set by Claude. The port gave 6/20 — all true
terms present in all 20, 1–3 small extra terms in the 14 misses — and a line-by-line audit against the original found
no deviation on uniform grids (`DIARY.md` 2026-10-30). The gate is replaced by point 5: fidelity is shown by identity
with the original code on the same data, not by a hit rate. Point 1(ii) stays reported in full.

## 6. What is reported

As Q5 §6, per stratum × σ (pooled over ρ and realizations, and per ρ; (0, 0.5) as its own row), unit counts beside
every rate: raw and pruned exact structure, R² > 0.9 reconstruction and generalization (variance-weighted primary,
arithmetic reported), for Q5 (c)/(a)/(b), W1, W1-cap, W2 × L-C6, L-Q5, and the existing fixed-threshold Weak-SINDy
reference. Per arm also the learned λ̂ distribution and the share of equations whose λ̂ sits at a grid end. Cost: counts
only (library evaluations, least-squares solves; Q5: loss evaluations, ODE solves) — wall-clock as context only.
All 63 systems separately for the Paper 1 baseline row, exact and surrogate systems never mixed.

## 7. Execution

Laptop, Python. Codex implements and runs the acceptance (§5) and a smoke on 20 cells; the full run (6 arm × library
combinations × 4,536 cells) is started by Claude after points 1–4 pass, on the laptop if the smoke projects < 1 h,
otherwise discussed. **Its results stay sealed until point 5 passes:** before that only technical checks (cell count,
errors, data hashes, determinism) — no rate, no structure, no comparison. The MATLAB run of point 5 is started by
Claude on the laptop once MATLAB is installed, under the same < 1 h rule. The Q5 comparison table is produced once the Q5 grid has finished; until then only
the W-arms are aggregated.

## 8. Open, not decided by Q5-W

- **A data-derived path end for Q5** instead of the truth-derived cap (noise-floor stop, Track S). Not tested here;
  W1-cap and W1 bound how much the cap matters on the opponent's side only.
- WENDy (weak-form errors-in-variables) and E-WSINDy as further opponents.
