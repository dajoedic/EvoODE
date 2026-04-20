# benchmarks/benchmark_evogrow.jl
#
# EvoGrow v2.1 benchmark: 10 heterogeneous systems from strogatz_extended.json
#
# Selected systems (IDs: 2, 3, 11, 23, 24, 26, 31, 37, 54, 63) cover:
#   - dim = 1, 2, 3, 4
#   - structure: linear, polynomial, cubic, trig, bilinear coupling
#   - difficulty: trivial to hard
#
# Two systems (IDs 23, 37) lie partially outside the current basis scope and
# are deliberately included to measure approximation behaviour.
#
# Usage:
#   julia benchmarks/benchmark_evogrow.jl
#
# Quick mode (reduced settings for fast testing):
#   QUICK=true julia benchmarks/benchmark_evogrow.jl

import Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using DifferentialEquations
using Plots
using Printf
using Random

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

# ============================================================
# Configuration
# ============================================================

const QUICK = get(ENV, "QUICK", "false") == "true"

const POP_SIZE      = QUICK ? 5   : 10
const N_LEVELS      = QUICK ? 4   : 8
const BFGS_MAXITERS = QUICK ? 50  : 200
const VERBOSE       = 1

const OUT_DIR = joinpath(@__DIR__, "results")
mkpath(OUT_DIR)

# ============================================================
# Ground-truth ODE right-hand sides (hardcoded parameters)
# ============================================================

# ID 2: Population growth (linear) — dx = 0.23*x
function rhs_02!(du, u, _, _)
    du[1] = 0.23 * u[1]
end

# ID 3: Logistic growth — dx = 0.79*x*(1 - x/74.3)
function rhs_03!(du, u, _, _)
    du[1] = 0.79 * u[1] * (1.0 - u[1] / 74.3)
end

# ID 11: Critical slowing down — dx = -x^3
function rhs_11!(du, u, _, _)
    du[1] = -u[1]^3
end

# ID 23: Overdamped pendulum — dx = 0.21 - sin(x)
function rhs_23!(du, u, _, _)
    du[1] = 0.21 - sin(u[1])
end

# ID 24: Harmonic oscillator — dx1=x2, dx2=-2.1*x1
function rhs_24!(du, u, _, _)
    du[1] =  u[2]
    du[2] = -2.1 * u[1]
end

# ID 26: Lotka-Volterra competition (Strogatz version, rabbits vs sheeps)
# dx1 = x1*(3 - x1 - 2*x2),  dx2 = x2*(2 - x1 - x2)
function rhs_26!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

# ID 31: SIR model (healthy / sick only)
# dx1 = -0.4*x1*x2,  dx2 = 0.4*x1*x2 - 0.314*x2
function rhs_31!(du, u, _, _)
    du[1] = -0.4  * u[1] * u[2]
    du[2] =  0.4  * u[1] * u[2] - 0.314 * u[2]
end

# ID 37: Van der Pol oscillator
# dx1 = x2,  dx2 = -x1 - 0.43*(x1^2 - 1)*x2
function rhs_37!(du, u, _, _)
    du[1] =  u[2]
    du[2] = -u[1] - 0.43 * (u[1]^2 - 1.0) * u[2]
end

# ID 54: Lorenz (periodic regime, r=12 < r_crit)
# dx1 = 5.1*(x2-x1),  dx2 = 12*x1-x2-x1*x3,  dx3 = x1*x2-1.67*x3
function rhs_54!(du, u, _, _)
    du[1] =  5.1  * (u[2] - u[1])
    du[2] =  12.0 * u[1] - u[2] - u[1] * u[3]
    du[3] =  u[1] * u[2] - 1.67 * u[3]
end

# ID 63: SEIR epidemic model (proportions, S+E+I+R=1)
# dx1=-b*x1*x3, dx2=b*x1*x3-a*x2, dx3=a*x2-c*x3, dx4=c*x3
function rhs_63!(du, u, _, _)
    du[1] = -0.28 * u[1] * u[3]
    du[2] =  0.28 * u[1] * u[3] - 0.47 * u[2]
    du[3] =  0.47 * u[2]         - 0.30 * u[3]
    du[4] =  0.30 * u[3]
end

# ============================================================
# Benchmark system type
# ============================================================

"""
    BenchmarkSystem

One benchmark entry from strogatz_extended.json.

Fields:
- `id`: original dataset ID
- `name`: short human-readable name
- `dim`: state dimension
- `true_rhs!`: ground-truth ODE f!(du, u, _, _) with hardcoded parameters
- `u0`: initial condition vector
- `tspan`: integration interval
- `T`: number of time points for data
- `true_structure`: human-readable ground-truth equation
- `basis_exact`: whether StagedPolynomialBasis can represent the true structure exactly
- `basis_note`: explanation if basis_exact == false
"""
struct BenchmarkSystem
    id::Int
    name::String
    dim::Int
    true_rhs!::Function
    u0::Vector{Float64}
    tspan::Tuple{Float64,Float64}
    T::Int
    true_structure::String
    basis_exact::Bool
    basis_note::String
end

BenchmarkSystem(id, name, dim, rhs, u0, tspan, T, struc, exact) =
    BenchmarkSystem(id, name, dim, rhs, u0, tspan, T, struc, exact, "")

# ============================================================
# System list
# ============================================================

const BENCHMARKS = BenchmarkSystem[

    # dim=1 | linear
    BenchmarkSystem(2, "Population growth (linear)", 1,
        rhs_02!, [4.78], (0.0, 12.0), 120,
        "du1 = 0.23*u1",
        true),

    # dim=1 | quadratic polynomial (Stages 1+2)
    BenchmarkSystem(3, "Logistic growth", 1,
        rhs_03!, [7.3], (0.0, 20.0), 200,
        "du1 = 0.79*u1 - 0.0106*u1^2",
        true),

    # dim=1 | cubic (no params) — tests Stage 4
    BenchmarkSystem(11, "Critical slowing down", 1,
        rhs_11!, [3.4], (0.0, 5.0), 100,
        "du1 = -u1^3",
        true),

    # dim=1 | trig + constant — tests Stage 5
    # NOTE: constant term (0.21) is not in StagedPolynomialBasis.
    # EvoGrow should recover -sin(u1) but cannot fit the constant offset.
    BenchmarkSystem(23, "Overdamped pendulum", 1,
        rhs_23!, [-2.74], (0.0, 25.0), 250,
        "du1 = 0.21 - sin(u1)",
        false,
        "Constant term (0.21) not in basis; -sin(u1) recoverable but offset is not."),

    # dim=2 | linear coupling — easiest 2D case
    BenchmarkSystem(24, "Harmonic oscillator", 2,
        rhs_24!, [0.4, -0.03], (0.0, 15.0), 200,
        "du1 = u2  |  du2 = -2.1*u1",
        true),

    # dim=2 | polynomial + bilinear coupling (Stages 1-3)
    BenchmarkSystem(26, "Lotka-Volterra competition", 2,
        rhs_26!, [5.0, 4.3], (0.0, 10.0), 200,
        "du1 = 3*u1 - u1^2 - 2*u1*u2  |  du2 = 2*u2 - u1*u2 - u2^2",
        true),

    # dim=2 | bilinear coupling (Stages 1+3) — different regime from LV
    BenchmarkSystem(31, "SIR model", 2,
        rhs_31!, [7.2, 0.98], (0.0, 20.0), 200,
        "du1 = -0.4*u1*u2  |  du2 = 0.4*u1*u2 - 0.314*u2",
        true),

    # dim=2 | cubic cross term u1^2*u2 — outside current basis
    # NOTE: Stage 4 has self-cubic u1^3 and u2^3 but not u1^2*u2.
    # Tests approximation behaviour for out-of-basis structures.
    BenchmarkSystem(37, "Van der Pol oscillator", 2,
        rhs_37!, [2.2, 0.0], (0.0, 20.0), 200,
        "du1 = u2  |  du2 = -u1 + 0.43*u2 - 0.43*u1^2*u2",
        false,
        "Cubic cross term u1^2*u2 not in basis (Stage 4 has only self-cubic u1^3, u2^3)."),

    # dim=3 | bilinear coupling — iconic system in periodic regime (r=12)
    BenchmarkSystem(54, "Lorenz (periodic)", 3,
        rhs_54!, [2.3, 8.1, 12.4], (0.0, 15.0), 300,
        "du1 = -5.1*u1 + 5.1*u2  |  du2 = 12*u1 - u2 - u1*u3  |  du3 = u1*u2 - 1.67*u3",
        true),

    # dim=4 | bilinear coupling — epidemic model, clean polynomial structure
    BenchmarkSystem(63, "SEIR model", 4,
        rhs_63!, [0.6, 0.3, 0.09, 0.01], (0.0, 30.0), 300,
        "du1 = -0.28*u1*u3  |  du2 = 0.28*u1*u3 - 0.47*u2  |  du3 = 0.47*u2 - 0.30*u3  |  du4 = 0.30*u3",
        true),
]

# ============================================================
# Ground-truth trajectory generation
# ============================================================

"""
    generate_trajectory(sys) -> Trajectory

Solve the ground-truth ODE for `sys` at high precision and return a `Trajectory`.
"""
function generate_trajectory(sys::BenchmarkSystem)::Trajectory
    t_grid = collect(range(sys.tspan[1], sys.tspan[2]; length = sys.T))
    prob   = ODEProblem(sys.true_rhs!, copy(sys.u0), sys.tspan, nothing)
    sol    = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)

    if length(sol.t) != sys.T
        error("Ground-truth solver returned $(length(sol.t)) points " *
              "(expected $(sys.T)) for system '$(sys.name)'")
    end

    X = Array(sol)'   # T x dim
    return Trajectory(t_grid, X)
end

# ============================================================
# Single benchmark run
# ============================================================

"""
    run_one(sys; seed) -> NamedTuple

Run EvoGrow on `sys`, save plot + CSV to OUT_DIR, return a result record.
"""
function run_one(sys::BenchmarkSystem; seed::Int = 42)
    sep = "=" ^ 72
    @printf("\n%s\n  ID %-3d | %s  (dim=%d)\n", sep, sys.id, sys.name, sys.dim)
    if !sys.basis_exact
        @printf("  [!] Partially out of basis scope: %s\n", sys.basis_note)
    end
    @printf("%s\n", sep)

    traj     = generate_trajectory(sys)
    basis    = default_staged_polynomial_basis(sys.dim)
    strategy = EvoGrow(
        pop_size            = POP_SIZE,
        n_levels            = N_LEVELS,
        children_per_parent = 2,
        max_terms_per_eq    = 6,
        λ                   = 1e-3,
    )
    optimizer = BFGSOptimizer(maxiters = BFGS_MAXITERS)
    opts = DiscoveryOptions(
        rng_seed         = seed,
        verbose          = VERBOSE,
        min_levels       = 2,
        max_levels       = 50,
        loss_tol         = 1e-8,
        plateau_window   = 3,
        plateau_tol      = 1e-4,
        plateau_relative = false,
    )

    t0     = time()
    result = discover(traj;
                      structure = strategy,
                      optimizer = optimizer,
                      basis     = basis,
                      loss      = MSELoss(),
                      options   = opts)
    elapsed = time() - t0

    n_stages = length(basis.term_groups)
    discovered_str = replace(result.meta.structure.best_structure_pretty, '\n' => "\n         ")
    @printf("\n  Discovered:\n         %s\n", discovered_str)
    @printf("  True:    %s\n", sys.true_structure)
    @printf("  Loss:     %.4e\n", result.loss)
    @printf("  n_params: %d\n",   length(result.params))
    @printf("  Stage:    %d / %d\n", result.meta.structure.final_stage, n_stages)
    @printf("  Time:     %.1f s\n", elapsed)

    # Safe filename base
    name_safe = replace(lowercase(sys.name),
                        " " => "_", "(" => "", ")" => "", "/" => "_")
    base = @sprintf("bench_%02d_%s", sys.id, name_safe)

    # Data vs model plot
    f!, _, _ = build_rhs(result.structure, basis)
    plot_file = joinpath(OUT_DIR, base * ".png")
    solve_and_save_plot(f!, result.params, traj;
        filename = plot_file,
        title    = "ID $(sys.id): $(sys.name)  [MSE=$(round(result.loss, sigdigits=3))]")
    @printf("  Plot  -> %s\n", basename(plot_file))

    # Objective convergence history plot
    hist = result.meta.structure.best_J_hist
    if length(hist) >= 2
        hist_file = joinpath(OUT_DIR, base * "_history.png")
        levels = 1:length(hist)
        p_hist = plot(levels, hist;
            xlabel    = "Level",
            ylabel    = "Best objective",
            title     = "ID $(sys.id): EvoGrow convergence",
            yscale    = :log10,
            marker    = :circle,
            legend    = false,
            linewidth = 2)
        savefig(p_hist, hist_file)
        @printf("  Hist  -> %s\n", basename(hist_file))
    end

    # CSV
    csv_file = joinpath(OUT_DIR, base * ".csv")
    save_comparison_csv(traj.t, traj.x, result.meta.prediction.Yhat;
                        filename = csv_file)
    @printf("  CSV   -> %s\n", basename(csv_file))

    return (
        id          = sys.id,
        name        = sys.name,
        dim         = sys.dim,
        basis_exact = sys.basis_exact,
        loss        = result.loss,
        objective   = result.objective,
        n_params    = length(result.params),
        final_stage = result.meta.structure.final_stage,
        elapsed_s   = elapsed,
        structure   = replace(result.meta.structure.best_structure_pretty, '\n' => " | "),
    )
end

# ============================================================
# Main
# ============================================================

@printf("\nEvoGrow v2.1 Benchmark\n")
@printf("Settings: pop_size=%d  n_levels=%d  bfgs_maxiters=%d  quick=%s\n",
        POP_SIZE, N_LEVELS, BFGS_MAXITERS, QUICK)
@printf("Output:   %s\n\n", OUT_DIR)

records = []

for sys in BENCHMARKS
    try
        push!(records, run_one(sys))
    catch e
        @printf("\nERROR on ID %d (%s):\n  %s\n",
                sys.id, sys.name, sprint(showerror, e))
        push!(records, (
            id = sys.id, name = sys.name, dim = sys.dim,
            basis_exact = sys.basis_exact,
            loss = NaN, objective = NaN, n_params = -1,
            final_stage = -1, elapsed_s = NaN, structure = "ERROR",
        ))
    end
end

# ============================================================
# Summary table (stdout)
# ============================================================

@printf("\n\n%s\n", "=" ^ 90)
@printf("  BENCHMARK SUMMARY -- EvoGrow v2.1\n")
@printf("%s\n", "=" ^ 90)
@printf("  %-3s  %-32s  %3s  %-5s  %-10s  %6s  %5s  %6s\n",
        "ID", "Name", "dim", "Exact", "Loss", "Params", "Stage", "Time(s)")
@printf("%s\n", "-" ^ 90)

for r in records
    loss_str  = isnan(r.loss)       ? "  ERROR   " : @sprintf("%.3e", r.loss)
    param_str = r.n_params  == -1   ? " ERR" : @sprintf("%4d", r.n_params)
    stage_str = r.final_stage == -1 ? "ERR" : @sprintf("%2d", r.final_stage)
    time_str  = isnan(r.elapsed_s)  ? "  ERR" : @sprintf("%6.1f", r.elapsed_s)
    @printf("  %-3d  %-32s  %3d  %-5s  %-10s  %6s  %5s  %6s\n",
            r.id, r.name[1:min(32, length(r.name))], r.dim,
            r.basis_exact ? "YES" : "NO",
            loss_str, param_str, stage_str, time_str)
end
@printf("%s\n", "=" ^ 90)

# ============================================================
# Summary CSV
# ============================================================

summary_file = joinpath(OUT_DIR, "summary.csv")
open(summary_file, "w") do io
    println(io, "id;name;dim;basis_exact;loss;objective;n_params;final_stage;elapsed_s;discovered_structure")
    for r in records
        println(io, join([
            r.id,
            "\"$(r.name)\"",
            r.dim,
            r.basis_exact,
            isnan(r.loss)      ? "NA" : @sprintf("%.6e", r.loss),
            isnan(r.objective) ? "NA" : @sprintf("%.6e", r.objective),
            r.n_params  == -1  ? "NA" : string(r.n_params),
            r.final_stage == -1 ? "NA" : string(r.final_stage),
            isnan(r.elapsed_s) ? "NA" : @sprintf("%.2f", r.elapsed_s),
            "\"$(r.structure)\"",
        ], ";"))
    end
end
@printf("\nSummary -> %s\n", summary_file)
@printf("Done.\n")
