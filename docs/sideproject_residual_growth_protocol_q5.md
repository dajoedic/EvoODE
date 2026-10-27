# Side project "residual-guided growth" — protocol for Q5 (noise)

**Frozen 2026-10-27, approved by the user, before any Q5 number was computed.** Part 4 of the side project; parts 1–3:
`docs/sideproject_residual_growth_protocol.md` (`e61f48f`), `_q3.md` (`c81e7c6`), `_q4.md` (`24ede2d`). Q4 result and
the reference correction: `DIARY.md` 2026-10-27. Literature position: `docs/sideproject_residual_growth_literature.md`.
User decisions 2026-10-27: reference is the matching-library Weak-SINDy at its better threshold; full C-6 grid; Orion on
the 8 free cores before ODEFormer; finish within 7 days; bound-infeasible dim-3 systems dropped for cost; a probe first;
**no pass/fail rules and no pre-written reading** — Q5 reports, the interpretation is made jointly after the numbers.
Frozen are what is measured, against what, on which data, and the controls.
Thresholds are human design choices, not derived from data.

## 1. Question

How does the Q4 pipeline, unchanged, compare with Weak-SINDy when the training trajectory is noisy and irregularly
subsampled, per noise level? Where it loses, is the loss in the path (truth not among the candidates) or in the size
choice (truth among them, not chosen)?

## 2. Units, data, strata

- Unit: (system, training IC) of the 30 exact systems, as Q4. **Strata, all reported alike with their unit count:**
  `dim1` (22 units), `dim2` (20), `dim3_feasible` (52, 61; 4 units), `dim4` (63; 2 units). **Not run:** `dim3_bound_infeasible` (54–59) — ~1,250–3,800 core-h projected, and Q4 already
  loses there on clean data (2/12); declared exclusion for cost, not for result.
- Data: the C-6 export `phase_c_c6_data_conditions_5dd1df8` — the same observed data the C-6 baselines consumed
  (per-cell `observed_data_sha256` must match the baseline rows). Noise multiplicative Gaussian,
  σ ∈ {0.01, 0.02, 0.03, 0.04, 0.05} × subsampling ρ ∈ {0, 0.5}, plus (0, 0.5); three realizations each — 11 noisy or
  subsampled conditions × 3 realizations = 33 data sets per unit, plus (0, 0) as control.
- The method sees only the observed (noisy, subsampled) training data. **Evaluation** is against clean targets, with the
  C-6 baseline definitions: reconstruction against the clean training trajectory, generalization from the other IC
  against its clean trajectory.

## 3. The pipeline — unchanged from Q4

Q4 §3.1–3.3 apply verbatim: weak design and basis as WP-FA2; growth path with the normalised FROLS step and the FoBa
backward check (ν = 0.5); path end at 6 terms per equation or normalised SSE < 1e-14; every path state a candidate;
each candidate fitted from its weak start with one `fit_parameters` call, `max_fit_attempts = 1`, bound 10; size rules
(c) trajectory BIC (primary), (a) weak BIC, (b) EvoGrow objective; sentinel or diverged fits never chosen by (b)/(c).
Upper bounds (path at true size, weak best-subset at true size) reported only.

Two bindings that Q4 did not need, to be fixed by the work package **from existing code, not chosen anew**, and stated
in its report before any run:
- **Irregular time grid (ρ = 0.5).** If the Q4 weak quadrature assumes uniform spacing, it is evaluated on the actual
  observation times (same test functions, quadrature on the observed grid). Trajectory loss and BIC use the observed
  times; N = observed samples × dimension.
- **Initial state of every simulation** (fit, selection, reconstruction): the same convention as the C-6 baseline
  harness. Generalization starts from the clean test IC, as for the baselines.

**Declared consequence:** under noise the SSE stop cannot fire, so the 6-term cap — the one use of the truth in the
design — becomes the only path end. §7 measures whether it carries the result.

## 4. Metrics

Per (unit, σ, ρ, realization) and chosen model: raw and pruned exact structure (pruning `max(1e-6, 1e-3·max_abs)` per
equation), R² > 0.9 reconstruction and generalization, variance-weighted primary, arithmetic reported; number of
candidates; total loss evaluations and ODE solves.

## 5. References (same cells, existing data, no new baseline run)

Source: `outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv` (WP-N47, canonical; tracked summary
`analysis/data/paper1_phaseC_v1/c6_sindy_family_dop853_e935c37/`).
- **Primary reference:** Weak-SINDy, library `poly_deg3_sin_cos`, thresholds 0.01 and 0.1. Per stratum × σ and **per
  metric separately**, the better threshold — deliberately in Weak-SINDy's favour.
- Reported: SINDy and E-SINDy with the same library, same selection; Weak-SINDy all ten configurations (median, range).
- **EvoGrow C-6 is not read** (blind rule until §9.4d of the Phase C plan).

## 6. What is reported

Per stratum × σ ∈ {0.01, …, 0.05}, pooled over ρ and the three realizations, and per ρ separately; the
subsampling-only condition (0, 0.5) as its own row. Unit counts beside every rate.
- Size rule (c): pruned and raw exact structure, R² > 0.9 reconstruction and generalization — beside the Weak-SINDy
  reference, SINDy and E-SINDy (same library), and the Weak-SINDy median and range over all ten configurations.
- Size rules (a) and (b) on the same metrics — whether the trajectory check still adds over the weak space.
- Upper bounds; cost (loss evaluations, ODE solves, candidates).

No pass/fail rule, no pre-written reading.

## 7. Diagnostics fixed in advance (the path end)

Per stratum × σ:
- **D1** share of paths that end at the 6-term cap;
- **D2** share of units whose (c) choice is the **last** path state (the cap, not BIC, limited the size);
- **D3** truth on the path: share of units where the true structure is among the candidates (path failure vs selection
  failure);
- **D4** size error k_chosen − k_true, distribution.

## 8. Controls

- (0, 0): the pipeline on the export's clean cells reproduces Q4 — candidate lists, chosen models and losses —
  bit-identically (laptop vs Orion was bit-identical in Q4 for `sys0024_ic1`).
- Path determinism: two runs of the path builder give identical candidate lists on one noisy cell.
- Per-cell `observed_data_sha256` equal to the WP-N47 baseline rows.
- Optimizer settings fingerprint equal to Q4.

## 9. Execution and cost

- **Probe first** (Orion, one Job, before the grid): one unit each of dim1, dim2, `dim3_feasible` at (σ, ρ) = (0.05, 0)
  and (0.05, 0.5), realization 1, plus the (0, 0) control of the same units. Purpose: bound the noise cost factor and
  pass the controls. Gate: user decides the grid after the probe numbers.
- **Grid:** 48 units × 33 data sets + 48 controls = 1,632 pipeline runs; Orion, ≤ 8 pods, dim1/dim2 shards first, no
  deadline. Planning estimate from Q4 fit times (wall-clock, planning only): ~230–700 core-h ≈ 350–1,050 €, ~1.5–4 days
  on 8 pods; raised to the user if the probe projects more than 7 days.

## 10. Open, not decided by Q5 — for discussion

**The path end is not principled.** On clean data the path stops when the weak residual reaches numerical zero; under
noise only the truth-derived cap stops it. The cap does not choose the size — BIC does — but it bounds the candidate
set and the cost, and if BIC overfits under noise (serially correlated residuals mis-scale its penalty) the cap becomes
the de-facto brake on growth. Candidate replacements to discuss after Q5: a stop at a data-estimated noise floor (Track
S, S-01: such a floor would have stopped EvoGrow correctly in both stage-1 cells), a stop when trajectory BIC has not
improved for m steps, or an effective-sample-size correction of the BIC penalty. None is tested in Q5.
