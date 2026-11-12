# WISP package — inventory of the code that runs in Q9 (arm C1000)

Written 2026-11-12 as the basis of the standalone WISP package (Julia). It records what the final WISP
configuration (Q9, arm C1000, Q7 stop, estimated initial state, coefficient bound 1000) actually executes, so that
a port reproduces it instead of re-deriving it. Line numbers refer to commit `24c2c70`. [I] marks an inference
that was not checked in the source.

## Pipeline for one cell

| # | Step | Implementation |
|---|---|---|
| 0 | Data: raw little-endian float64 time `(T,)` and state `(T,d)` (C order), sha256-checked, from the C-6 export | `run_phasec_noise_sindy_baselines.py:94,128,175`; Julia `sideproject_q5_noise_fits.jl:31-67` |
| 1 | Library: `1, u_i, u_i², u_i·u_j (i<j), u_i³, sin(u_i), cos(u_i)` (sin/cos interleaved per variable); p = 6/12/19/27 for dim 1–4 | `analysis/exploratory/term_relevance/term_relevance.py:52-95`; `src/basis/staged_polynomial.jl:126-178` |
| 2 | Weak form: for L ∈ {1,2,4,8,16}, every start s = 0…n−L−1: row = trapezoid integral of φ over samples s…s+L, target = x[s+L,e] − x[s,e]. Index-space windows (unequal time lengths on irregular grids). Order L then s; n = 512 → 2,529 rows | `term_relevance.py:186-202` |
| 3 | Weak solver: columns scaled to unit norm, QR of `[A_s, b]` (R only), `sse(S) = ‖b − A_S lstsq(A_S,b)‖²`, cached per support; `b_norm2` = raw target norm²; coefficients = lstsq / column norms | `run_sideproject_residual_growth.py:33-68`; `build_sideproject_q3_weak_starts.py:39-49` |
| 4 | Noise variance per point and component: 9-point window, local cubic fit via SVD, residual² / (1 − leverage), centred 21-point moving mean | `build_sideproject_q6_paths.py:45-71` |
| 5 | Noise operator `L_e = D·diag(sqrt(var_e))` (D = endpoint incidence of the windows); floor `F(S) = max(0, ‖L‖_F² − ‖Lᵀ U_r‖²)`, U_r from the SVD of the unit-norm design on S, rank cut `s > eps·max(shape)·s0` | `q6:74-134`; `q8:108-110` |
| 6 | Growth path, joint over equations: add the (equation, term) with the largest normalised gain `(sse(S) − sse(S∪j))/b_norm2` (ties: lower equation, lower term); end with `no_gain` if ≤ 0. FoBa after each addition of gain g: remove the cheapest active term while its normalised cost < 0.5·g. Revisited joint support → revert, end `cycle`. Each state after a step is one candidate | `q6:159-237` |
| 7 | Per-equation stop (in order): `sse` if sse/b_norm2 < 1e-14; `full`; `floor` (Q7): for every inactive j, `noise_j = F(S) − F(S∪j) > 0` and `(sse(S) − sse(S∪j))/noise_j < 6.635` (raw SSE; `noise_j ≤ 0` counts as significant). Re-checked every step. No size cap | `build_sideproject_q7_paths.py:25-41`; `q6:173-182` |
| 8 | Candidate record: per-equation weak coefficients, `weak_sse`, `n_rows`; `p0` flattened by equation then sorted term index (1-based); `weak_bic` (reported only) | `build_sideproject_q5_paths.py:49-63`; `q3_weak_starts.py:28-36` |
| 9 | Refit of every candidate: start `p0` (unclamped) plus u0 = first observed sample; joint vector `[coefs; u0]`, u0 unbounded, coefficients clamped to ±1000 inside every simulation; objective MSE over T·d entries, sentinel 1e6 on failed solve; Optimization.jl BFGS with `AutoFiniteDiff()`, maxiters 200, loss-eval budget 20,000 (returns best point), Nelder–Mead only on non-budget failure; returned coefficients clamped; Tsit5, abstol = reltol = 1e-6, maxiters 1e6, saveat observed times; one attempt | `sideproject_q9_fits.jl:43-62` → `sideproject_q8_fits.jl:84-141`; `src/optimize/bfgs.jl:166-186, 288-768`; `src/loss/mse.jl:15-24`; `src/basis/interface.jl:24-43` |
| 10 | Selection (rule c): among non-sentinel, non-diverged candidates minimise `n·log(mse) + k·log(n)`, n = T·d, k = coefficients (u0 not counted, constant per cell); mse = 0 → −inf; ties → lower step | `aggregate_sideproject_q4.py:69-79` via `aggregate_sideproject_q8.py:23-70` |
| 11 | Pruning — reporting metric only, the selected model is unpruned: keep |c| ≥ max(1e-6, 1e-3·max|c| per equation) | `diagnostic_systems.jl:183-199` |

The Python builder chain is `q9 → q8.build_path(cell,'q7') → q7 → q6 → q5 → q4 → q3` plus `term_relevance.py` and
`run_sideproject_residual_growth.py`; the Julia chain `q9_fits → q8_fits → q5_noise_fits → q4_path_fits →
q3_weak_start` plus `src/`. Everything else in those files (earlier protocols, other Q8 arms, planning, controls) is
not on the method path.

## Constants

Window lengths 1, 2, 4, 8, 16 · sse stop 1e-14 · FoBa ν = 0.5 · χ² threshold 6.635 · noise windows 9-point cubic and
21-point mean · lstsq `rcond=None` · BFGS maxiters 200 · ODE tolerances 1e-6 · solver maxiters 1e6 · loss-eval budget
20,000 · coefficient bound 1000 · one fit attempt · sentinel 1e6 · BIC rule (c). Seed 7 is set but no random draw
occurs at C1000. Every Q9 record stores its `optimizer_settings`.

## Numerics and dependencies

Python: numpy 2.2.6 (`np.trapz` — deprecated, the port writes the trapezoid out; `qr(mode="r")`, `lstsq` (gelsd),
`svd`, `vander`), scipy 1.13.1 (sparse), `threadpool_limits(1)`. Julia 1.12.6: OrdinaryDiffEq 6.104.0, Optimization
5.2.0, OptimizationOptimJL 0.4.8, Optim 1.13.3, FiniteDiff 2.29.0. [I] Optim's default line search (HagerZhang) and
forward differences in `AutoFiniteDiff()` were not checked.

Bit-identity of a port is not guaranteed across LAPACK builds (the project has seen OpenBLAS kernels flip terms,
WP-N47). Acceptance should therefore be stated per quantity: candidate supports and order exact; weak coefficients
and `p0` to a relative tolerance; fits and selection compared on the outcome.

## Golden fixtures

- `outputs/sideproject_q9_inputs/grid/q9_paths.json` — 4,284 cells, 45,785 candidates (supports, weak
  coefficients, `weak_sse`, `p0`, end reasons per equation). Q9 paths reproduce Q8 C1000 bit-identically (Q9 §5).
- `outputs/sideproject_q8_512dd5b…/out_final/out/*.jsonl` — Q8 fit records (C1000 among them); Q9 fit records
  after W-4.
- Inputs: the C-6 export binaries.
