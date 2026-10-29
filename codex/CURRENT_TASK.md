# WP-FA6 — Side project Q5-W: the published WSINDy as reference (implementation, acceptance, smoke)
**Language: Python**

Stand 2026-10-30. Authority: `docs/sideproject_residual_growth_protocol_q5w.md` (`374e553`). Read it in full first; this
spec only adds the work split. Background: Q5 compared against pysindy's fixed-threshold Weak-SINDy; the published
WSINDy (Messenger & Bortz) selects its threshold from the data (MSTLS). Q5-W builds that opponent faithfully so the
comparison is fair: same data, same library, same size prior.

## Sources you must use

- The official MATLAB code, read-only, at `outputs/reference_wsindy_ode_72d8d6e/` (commit `72d8d6e`, archive SHA-256 in
  `ARCHIVE_SHA256.txt` there). It is "All Rights Reserved": **read it and re-implement the algorithm; never copy code,
  comments or text from it into the repository.** Entry points: `wsindy_ode_script.m` (settings and their `DEFAULT`
  comments), `wsindy_ode_fun.m` (pipeline), `wsindy_pde_RGLS_seq.m` (λ loop and loss), `sparsifyDynamics.m` (MSTLS with
  per-term bounds), `findcorners.m` / `findcornerpts.m` (corner point → test-function support and degree),
  `get_optimal_SMAF.m` / `estimate_sigma.m` (smoothing decision), `phi_int_weights.m` (test functions and derivatives),
  `build_theta.m`, `gen_noise.m`, `gen_data.m`, `sim_ode.m` (the Lorenz example of the acceptance).
- The paper PDF in that folder and Messenger & Bortz, J. Comput. Phys. 443 (2021), eqs. (4.4)–(4.8) and Appendix A, for
  anything the code leaves open. Where code and paper differ, the code wins (protocol §3); list every such place in the
  report.
- Existing project code to **reuse, not re-implement**: export reading, data hashes, library construction for L-C6,
  the pysindy weak design, evaluation (clean-IC simulation with DOP853, R², raw/pruned structure hits, pruning rule),
  truth terms — all in `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py` and its imports. L-Q5 term names
  come from the canonical Phase C basis (see how Q5's path builder names terms:
  `analysis/scripts/aggregate/build_sideproject_q5_paths.py` → `phasec_basis`).

## Scope

1. **WSINDy module** (Python, numpy/scipy only, no MATLAB): the published pipeline with the protocol's settings —
   corner-point test-function selection, piecewise-polynomial test functions, `K_frac = 1`, column scaling
   `scale_Theta = 2`, the automatic smoothing decision, MSTLS with the per-term bounds, the λ grid, the
   `alpha_loss = 0.8` loss, per-equation λ selection with ties to the smallest λ. Library passed in as a list of named
   column functions. The irregular-grid binding of protocol §3 (trapezoidal weak integrals on the actual observed
   times). Watch the point the code review flagged: in `wsindy_pde_RGLS_seq.m` the λ sweep divides by the scale vector
   but the final re-solve at λ̂ does not — determine from the code what the returned coefficients are and make sure the
   coefficients you report are on the original data scale; state in the report how you verified it.
2. **Arms**: W1, W1-cap (per equation: loss minimiser among grid λ with ≤ 6 terms in that equation; none → equation
   unselected), W2 (MSTLS + λ grid + loss + scaling on the existing pysindy weak design of WP-N34/N47, seeded as
   WP-N45b), each on L-C6 and L-Q5 — six configurations. Record per equation: λ̂, the full loss curve, whether λ̂ sits
   at a grid end, the chosen test-function support and degree, the smoothing window actually used.
3. **Runner** over the C-6 export with the WP-N47 row schema extended by the fields above, writing to its own folder
   `outputs/sideproject_q5w_wsindy/`, resumable, cells selectable (`--limit`, `--cells`), configuration selectable.
   Data hash per cell checked against the WP-N47 rows. A projection of the full-run cost from the smoke (counts; time as
   context).
4. **Acceptance (protocol §5)**, all four points, each with its numbers in the report. Point 1(ii) runs 20 numpy seeds
   0–19 for the noise.
5. **Smoke**: 20 **(0, 0)** cells of **surrogate** systems only (not one of the 30 exact systems), all six
   configurations; report technical facts only (completed, errors, runtime, counts).
6. Focused tests for the new code (fixtures derived from real export rows, `CODEX_PROTOCOL.md`), fast enough to stay
   well inside the 15-minute limit; run only those plus the existing tests of the files you touch.

## Verboten

- Running any configuration on the C-6 cells beyond the smoke of scope 5; running anything on noisy cells; computing or
  reporting any rate, comparison or table against Q5 or the existing baselines. The full run is Claude's, after the user.
- Copying code, comments or text from `outputs/reference_wsindy_ode_72d8d6e/`.
- Tuning anything so that acceptance 1 passes. If 1(ii) gives fewer than 15 of 20, report `blocked` with the numbers.
- Changing any frozen file: the Q5 scripts and runner, `run_phasec_noise_sindy_baselines.py` behaviour (adding an
  importable helper is fine if WP-N47 output stays identical — then show it), the export, WP-N47 outputs.
- Touching the uncommitted WP-N48b files in the working tree: `analysis/scripts/aggregate/aggregate_c6_symbolic_baselines.py`,
  `analysis/scripts/aggregate/run_k8s_symbolic_shard.py`, `baselines/c6_shards.py`,
  `baselines/tests/test_c6_symbolic_execution.py`, `codex/reports/REPORT_WP_N48.md`, `k8s/phase_c_c6_pysr*.yaml`.
- Git operations of any kind; cluster jobs; anything running longer than 15 minutes; time cuts inside the runner.

## Abnahme

- Protocol §5 points 1–4 pass with numbers in `codex/reports/REPORT_WP_FA6.md`, or the WP is `blocked` with the
  failing numbers.
- Every setting of protocol §3 appears in the report with the code file/line or paper equation it comes from; every
  code/paper discrepancy and every place you had to decide something the sources leave open is listed.
- The six configurations complete on the 20 smoke cells without error; the cost projection for all 4,536 cells × 6 is
  in the report.
- The new tests pass; their command and output are in the report.
- `codex/STATUS.md` set as `CODEX_PROTOCOL.md` prescribes.
