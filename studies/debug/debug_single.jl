import Pkg
Pkg.activate(dirname(dirname(@__DIR__)))

using DifferentialEquations
using Plots
using Dates
using Printf

include(joinpath(dirname(dirname(@__DIR__)), "src", "EvoODE.jl"))
using .EvoODE

# ============================================================
# Configuration
# ============================================================

const SEED = 42
const POP_SIZE = 5
const N_LEVELS = 15
const CHILDREN_PER_PARENT = 2
const MAX_TERMS_PER_EQ = 5
const BFGS_MAXITERS = 100
const VERBOSE = 3

const PROGRESSION_MODE = :stage_local
const USAGE_MODE = :hard
const SOFT_BIAS = 0.75

# ============================================================
# Lotka-Volterra competition data
# ============================================================

function lotka_competition!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

u0 = [5.0, 4.3]
tspan = (0.0, 10.0)
T = 200
t_grid = collect(range(tspan[1], tspan[2]; length = T))

prob = ODEProblem(lotka_competition!, copy(u0), tspan, nothing)
sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
traj = Trajectory(t_grid, Array(sol)')

# ============================================================
# Discovery setup
# ============================================================

dim = size(traj.x, 2)
basis = default_staged_polynomial_basis(dim)

structure = EvoGrow(
    pop_size = POP_SIZE,
    n_levels = N_LEVELS,
    children_per_parent = CHILDREN_PER_PARENT,
    max_terms_per_eq = MAX_TERMS_PER_EQ,
    λ = 1e-3,
    progression = StageProgressionPolicy(
        mode = PROGRESSION_MODE,
        min_levels_per_stage = 2
    ),
    usage = StageUsagePolicy(
        mode = USAGE_MODE,
        new_term_bias_prob = SOFT_BIAS
    )
)

optimizer = BFGSOptimizer(maxiters = BFGS_MAXITERS)
loss = MSELoss()

options = DiscoveryOptions(
    rng_seed = SEED,
    verbose = VERBOSE,
    min_levels = 2,
    max_levels = 50,
    loss_tol = 1e-8,
    plateau_window = 3,
    plateau_tol = 1e-4,
    plateau_relative = false,
    plateau_rtol = 1e-3
)

out_dir = joinpath(dirname(dirname(@__DIR__)), "outputs", "studies", "debug")
mkpath(out_dir)
_log_io = open(joinpath(out_dir, "run.log"), "a")

function log_println(msg::String)
    println(msg)
    println(_log_io, msg)
    flush(_log_io)
end

macro logf(fmt, args...)
    return esc(:(log_println(@sprintf($fmt, $(args...)))))
end

log_println("=== Started at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")) ===")
log_println("Running single-system debug experiment on Lotka-Volterra competition...")
log_println("progression=$(PROGRESSION_MODE) | usage=$(USAGE_MODE) | seed=$(SEED)")

log_file = joinpath(out_dir, "debug_lotka.log")
set_log_file(log_file)

result = discover(
    traj;
    structure = structure,
    optimizer = optimizer,
    basis = basis,
    loss = loss,
    options = options
)

# ============================================================
# Exact support check
# ============================================================

name_to_idx = Dict(basis_term_name(basis, i) => i for i in 1:basis_num_terms(basis))
expected_support = [
    sort([name_to_idx["u1"], name_to_idx["u1^2"], name_to_idx["u1*u2"]]),
    sort([name_to_idx["u2"], name_to_idx["u1*u2"], name_to_idx["u2^2"]])
]

recovered_exact_support = true
for (got, expected) in zip(result.structure.active_idxs, expected_support)
    if sort(unique(got)) != expected
        recovered_exact_support = false
        break
    end
end

# ============================================================
# Summary
# ============================================================

meta = result.meta.structure
stage_budget = haskey(meta, :stage_level_counts) ? join(meta.stage_level_counts, "|") : "NA"
final_stage = haskey(meta, :final_stage) ? string(meta.final_stage) : "NA"
termination_reason = haskey(meta, :termination_reason) ? string(meta.termination_reason) : "NA"
history = haskey(meta, :best_J_hist) ? join([@sprintf("%.4e", x) for x in meta.best_J_hist], " | ") : "NA"
total_loss_evals = haskey(meta, :total_loss_evals) ? string(meta.total_loss_evals) : "NA"
total_invalid_evals = haskey(meta, :total_invalid_evals) ? string(meta.total_invalid_evals) : "NA"
pretty_structure = haskey(meta, :best_structure_pretty) ? meta.best_structure_pretty : structure_with_params_string(result.structure, basis, result.params)
summary_lines = [
    "=" ^ 72,
    "DEBUG SUMMARY -- LOTKA-VOLTERRA COMPETITION",
    "=" ^ 72,
    @sprintf("Final loss:              %.6e", result.loss),
    @sprintf("Final objective:         %.6e", result.objective),
    @sprintf("Number of parameters:    %d", length(result.params)),
    "Final stage reached:     $final_stage",
    "Termination reason:      $termination_reason",
    "Stage budget:            $stage_budget",
    "Exact support recovered: $(recovered_exact_support ? "YES" : "NO")",
    "Discovered structure:",
    pretty_structure,
    "Convergence history:     $history",
    "Total loss evaluations:  $total_loss_evals",
    "Total invalid evals:     $total_invalid_evals",
    "=" ^ 72
]

log_println("")
log_println("=" ^ 72)
log_println("DEBUG SUMMARY -- LOTKA-VOLTERRA COMPETITION")
log_println("=" ^ 72)
@logf("Final loss:              %.6e", result.loss)
@logf("Final objective:         %.6e", result.objective)
@logf("Number of parameters:    %d", length(result.params))
log_println("Final stage reached:     $final_stage")
log_println("Termination reason:      $termination_reason")
log_println("Stage budget:            $stage_budget")
log_println("Exact support recovered: $(recovered_exact_support ? "YES" : "NO")")
log_println("Discovered structure:")
log_println(pretty_structure)
log_println("Convergence history:     $history")
log_println("Total loss evaluations:  $total_loss_evals")
log_println("Total invalid evals:     $total_invalid_evals")
log_println("=" ^ 72)

open(log_file, "a") do io
    println(io)
    for line in summary_lines
        println(io, line)
    end
end

# ============================================================
# Plot
# ============================================================

f!, _, _ = build_rhs(result.structure, basis)
plot_file = joinpath(out_dir, "debug_lotka.png")

solve_and_save_plot(
    f!,
    result.params,
    traj;
    filename = plot_file,
    title = "Lotka-Volterra debug | $(String(PROGRESSION_MODE)) | $(String(USAGE_MODE))"
)

close_log_file()
log_println("Saved plot to: $plot_file")
log_println("Saved log to:  $log_file")
log_println("=== Finished at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")) ===")
close(_log_io)
