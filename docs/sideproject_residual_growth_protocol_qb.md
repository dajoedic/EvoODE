# Side project WISP — protocol Q-B: extended baselines

**Frozen 2026-11-08 before any Q-B number was computed**, after the external review of the manuscript draft (review
point 2) and the user's decisions ("Das mit den Vergleichen klingt super. Machen wir."; WeakIdent in both library
variants; laptop preparation now, Orion runs after W-4). Q-B changes nothing in WISP and decides nothing about it; it widens the comparison. It reopens the
fixed baseline list of the WISP plan (CLAUDE.md, "Baselines (fixed)") by the user's decision.

## 1. Question

Does WISP's lead survive (a) the SINDy family with exactly WISP's library and a fine threshold grid, (b) WeakIdent, the
closest relative (greedy weak-form support search, selection in regression space), and (c) ODEFormer, the method of the
benchmark's authors?

## 2. Cells and evaluation

The **4,284 Q9 cells** (63 systems × 2 training ICs × 11 noisy/subsampled conditions × 3 realizations + clean), the
same observed data (per-cell `observed_data_sha256` checked against the Q9 path file). Evaluation exactly as for WISP and
the existing references: models integrated with DOP853 from the clean training IC (reconstruction) and the clean other
IC (generalization) on the clean 512-point grid; R² > 0.9 variance-weighted, divergence = miss; pruned and raw exact
structure on exact systems with the project's pruning rule. Systems as clusters.

## 3. Arms

**B1 — SINDy family, WISP library, fine grid.** SINDy, Weak-SINDy, E-SINDy exactly as WP-N47 (same pySINDy versions,
differentiation, weak library, ensemble settings, seeds) except: library = the WISP basis
`1, u_i, u_i², u_i u_j, u_i³, sin u_i, cos u_i` (a pySINDy custom library, column order and names identical to
`phasec_basis`), STLSQ threshold λ ∈ 13 log-spaced values 10⁻³ … 1 (10^(−3 + k/4), k = 0…12). Reported as before: the
best λ **per stratum × σ × metric**, chosen after the results in the reference's favour; additionally the single best λ
per stratum over all conditions and the whole λ curve.

**B2 — WeakIdent, two arms (user, 2026-11-08: "beides").** Official code (github.com/sunghakang/WeakIdent, Python,
Apache-2.0, last change 2023-03-31), pinned to one commit, unmodified algorithm.
- **B2a native:** its own polynomial dictionary, `max_poly = 3`, ODE mode (no spatial derivatives). It contains every
  polynomial term of the WISP basis plus mixed cubics; it has no sin/cos.
- **B2b extended:** the same dictionary plus `sin u_i, cos u_i` — the only change, made in the dictionary construction,
  declared as our modification; narrow-fit, trimming and all settings unchanged. Control: with the added columns removed,
  B2b reproduces B2a bit-identically on one cell per stratum.
Trimming parameter τ and all other settings: the authors' values for their ODE examples, fixed before any run. Uniform
grid required: on ρ = 0.5 the observed data are interpolated to the uniform 512-point grid exactly as for WSINDy
(W1-interp), on ρ = 0 used as observed. WeakIdent's coefficients are mapped to our term names; structure is scored where the
true support lies in the arm's library (B2a: exact systems without sin/cos terms; B2b: all exact systems), R² on all
systems.

**B3 — ODEFormer.** The prepared C-6 harness (WP-N48: `run_k8s_symbolic_shard.py`, reference image, manifest
`k8s/phase_c_c6_odeformer_job.yaml`), the four configurations (beam 10/50 × with/without constant optimization) and
three repetitions as in the reference grid. Reported: the best configuration per stratum × σ × metric (in its favour)
and the reference configuration. Structure via the WP-N40 recompute.

## 4. Controls

- B1: at λ ∈ {0.01, 0.1} with the WP-N47 library the harness reproduces WP-N47 rows bit-identically on one cell per
  stratum (same code path, only library and λ list change).
- B2: WeakIdent reproduces one of the authors' published ODE examples from their repository before it touches our data.
- B3: the WP-N48 smoke controls (clean system 1 identical to the Orion reference grid record).
- Data hashes per cell; one environment fingerprint per arm.

## 5. Execution and cost

Cost first measured on a sample (one cell per stratum, laptop, only counts and run time looked at, no metric).
Planning: B3 ~140–180 core-h (WP-N48 projection); B1 ~13/2 × the WP-N47 matching-library share (unmeasured; laptop if
< 1 h by measurement, else Orion); B2 unmeasured. Orion only on cores Q9 leaves free or after W-4 — W-4 keeps absolute
priority, at most 40 EvoODE cores in total, no hard time limits.

## 6. Not in Q-B

PySR (cited from the ODEFormer paper, cost ≥ 3,700 core-h). No change to any WISP component, no new WISP run.
