# WISP package — specification (`WISP.jl`, with a Python wrapper)

Written 2026-11-12. Implements item 3 of the work order in `CLAUDE.md` ("WISP package spec"). The method it ports is
recorded step by step in `docs/wisp_package_inventory.md`; this file decides the shape of the package and how a port
is accepted. Where the two disagree on what the method does, the inventory and the frozen Q9 code win.

## Decisions (user, 2026-11-12)

- One repository, `github.com/dajoedic/WISP.jl`, private until submission, MIT licence. Local clone `..\WISP.jl`.
- Julia package at the root, Python wrapper under `python/` (via `juliacall`). One version number for both.
- Claude implements directly (Codex cannot run Julia here). Claude may push to this repository; EvoODE rules are
  unchanged.
- No dependency on EvoODE. The pieces of `src/` that the refit uses (basis, ODE right-hand side, simulation, BFGS fit
  with estimated initial state) are re-implemented inside WISP.jl with the same arithmetic.

## Scope

The package runs exactly the final configuration of the paper (Q9, arm C1000): weak-form growth path with FoBa and
the χ² stop (Q7), weak-form starts, one trajectory refit per candidate with the initial state estimated and
coefficients bounded at ±1000, BIC selection (rule c). Every constant of the inventory is a keyword with the frozen
value as default. Nothing else from the side project is ported: no Q4/Q5 6-term cap, no random starts, no
no-refit arm, no fixed-IC control, no upper-subset diagnostic, no truth-based metrics.

## Public API (Julia)

| Function | Returns |
|---|---|
| `Library(dim)` / `default_library(dim)` | the canonical library: `1, u_i, u_i², u_i·u_j (i<j), u_i³, sin(u_i), cos(u_i)`, p = 6/12/19/27 for dim 1–4 |
| `weak_path(t, X; library, options)` | `WeakPath`: candidates (support per equation, weak coefficients, `weak_sse`, step, origin) and the end reason per equation — steps 1–8, no ODE solve |
| `refit(candidate, t, X; library, options)` | `Refit`: coefficients, fitted initial state, training MSE, flags `sentinel`/`diverged`, optimizer metadata — step 9 |
| `wisp(t, X; library, options)` | `WISPResult`: path, all refits, index of the BIC-selected candidate, the selected `Model` — steps 1–10 |
| `simulate(model, t; u0)` | predicted trajectory `(T × d)` |
| `equations(model)` | human-readable equations, one string per state |
| `prune(model)` | the reporting-only pruning rule (step 11); never applied to the selected model itself |

`WISPOptions` holds every constant: window lengths `(1, 2, 4, 8, 16)`, sse stop `1e-14`, FoBa ratio `0.5`, χ²
threshold `6.635`, noise windows `9`/`21`, coefficient bound `1000`, BFGS `maxiters = 200`, loss-eval budget `20_000`,
ODE `abstol = reltol = 1e-6`, solver `maxiters = 10^6`, sentinel `1e6`.

Data contract: `t` strictly increasing `Vector{Float64}` of length T ≥ 17 (the longest window plus one; the noise
estimator needs ≥ 9), `X` a `T × d` matrix, d ≥ 1. Irregular grids are allowed (windows are in index space, as in Q9).

## Python wrapper

`python/` holds the pip package `wisp-ode` (import name `wisp`), built on `juliacall`/`juliapkg`. It exposes
`wisp.fit(t, X, **options)` and `wisp.weak_path(...)`, converts NumPy arrays in and out, and returns plain dataclasses
(equations as strings, coefficients, fitted `u0`, the path). No method code lives in Python.

## Acceptance

Bit-identity of the whole chain is not promised: the weak path ran in NumPy (OpenBLAS, `gelsd`, pairwise sums) and
the port runs in Julia. Acceptance is therefore stated per quantity, against the frozen fixtures, before the port is
called WISP:

| # | Quantity | Fixture | Criterion |
|---|---|---|---|
| A1 | library names and order, dim 1–4 | `phasec_basis` | identical |
| A2 | weak path: number of candidates, `active_idxs`, `step`, `origin` per candidate, end reason per equation | `q9_paths.json`, all 4,284 cells | identical in every cell; any difference is listed cell by cell and explained before acceptance |
| A3 | weak coefficients and `p0` | same | relative difference ≤ 1e-8 per entry (absolute 1e-12 near zero) |
| A4 | refit from the fixture `p0` | Q8 C1000 records (`outputs/sideproject_q8_512dd5b…/out_final`) | bit-identical `params`, fitted initial state and training loss under the pinned validation environment (same package versions as EvoODE); stratified sample over dim 1–4 |
| A5 | selection | the same records | rule c selects the same candidate in every complete cell of the sample |
| A6 | end to end (`wisp` on raw data) | Q8 C1000 sample | same selected support in every sample cell; numbers compared on the outcome (R² > 0.9 status) |
| A7 | Python wrapper | one dim-1 and one dim-2 cell | same result as the Julia call |

The fixtures stay in EvoODE; the package ships only small self-contained tests (synthetic systems, a few rows of
golden numbers). The validation scripts live in `WISP.jl/validation/`, read the EvoODE paths from an environment
variable (`EVOODE_ROOT`), and carry their own pinned `Manifest.toml`.

## Order of work

1. Skeleton (Project, licence, README, CI-free test layout), library (A1).
2. Weak form, weak solver, noise estimator and floor, growth path (A2, A3) — the full 4,284-cell comparison.
3. Refit and selection (A4, A5), then `wisp` end to end (A6).
4. Python wrapper (A7), README example, tag `v0.1.0` (private).

Registration in the Julia General registry and PyPI waits for submission; the name collision check for "WISP" comes
before that.

## Result of the first port (2026-11-12, `WISP.jl` `72e84ad`)

All seven acceptance criteria are met. Steps 1–4 of the order of work are done in one go; only the tag is open.

| # | Result |
|---|---|
| A1 | library identical, dim 1–4 |
| A2 | path structurally identical in **4,264 / 4,284** cells (dim 1 1,564/1,564, dim 2 1,898/1,904, dim 3 672/680, dim 4 130/136). All 20 others are σ = 0 cells of systems 30, 53, 63 where two gains tie to a few ulp (first case: 0.9669016319478188 vs …186, system 30 is symmetric); NumPy and Julia LAPACK round the tie differently. Accepted as declared, not repaired: making the port reproduce NumPy's BLAS kernels is neither possible nor a property of the method |
| A3 | `p0` within 1e-8 relative in 4,231 cells, bit-identical in most; the larger differences (up to 2.5e-3, systems 9, 24, 28, 52, …) occur only at σ = 0, on near-collinear supports |
| A4 | refit from the fixture `p0`: **57 / 57 bit-identical** (coefficients, fitted u0, training MSE, optimizer loss, loss-evaluation count) over 15 cells, 5 strata (dim 1–3). From the port's own `p0` 37 / 57 are bit-identical; every other one has a `p0` differing in the last bits, and the MSE then moves by ~1e-11 relative (worst 7e-8) |
| A5 / A6 | rule c selects the same candidate in **15 / 15** cells, end to end from raw data |
| A7 | Python wrapper bit-identical to the records on a dim-1 and a dim-2 cell |

Two deviations from the plan above: the Julia compat lower bound is **1.10**, not 1.12, because `juliacall` caps Julia
at 1.11 under Python builds with OpenSSL 3.0 (Python 3.12 ships 3.0.16); the validation environment stays pinned to
Julia 1.12.6. And the package uses `OrdinaryDiffEqTsit5` instead of the full `OrdinaryDiffEq` — same Tsit5 at the
pinned version, as A4 shows.
