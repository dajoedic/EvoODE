import Pkg
Pkg.activate(dirname(dirname(@__DIR__)))

using Dates
using DifferentialEquations
using JSON3
using Printf

include(joinpath(dirname(dirname(@__DIR__)), "src", "EvoODE.jl"))
using .EvoODE
include(joinpath(dirname(@__DIR__), "regression", "diagnostic_systems.jl"))

# Micro-benchmark for WP-P1.
#
# Runs exactly one regression cell: System 26, Seed 42, EvoGrow v2.2.
# A uses the current reference budgets explicitly. B enables conservative
# screening budgets: the optimizer iteration count is unchanged, solver
# tolerances are loosened by one order of magnitude, ODE steps are capped at
# 20_000, and non-finite or very large states are rejected early. This is meant
# to measure cost sensitivity without changing growth, selection, promotion, or
# stopping logic.

const OUT_DIR = joinpath(dirname(dirname(@__DIR__)), "outputs", "studies", "profiling", "profile_eval_cost")

const SYSTEM_ID = 26
const SEED = 42
const POP_SIZE = 10
const N_LEVELS = 30
const CHILDREN_PER_PARENT = 2
const MAX_TERMS = 6
const LAMBDA = 1e-3
const STAGE_MIN = 2
const SOFT_BIAS = 0.75
const USE_PRETUNING = false

const BFGS_MAXITERS = 200
const BFGS_ABSTOL = 1e-6
const BFGS_RELTOL = 1e-6
const BFGS_MAXITERS_SOLVE = 10^6
const BFGS_TIME_LIMIT_S = 86_400.0

const SCREENING_BFGS_ABSTOL = 1e-5
const SCREENING_BFGS_RELTOL = 1e-5
const SCREENING_BFGS_MAXITERS_SOLVE = 20_000
const SCREENING_DIVERGENCE_LIMIT = 1e6

function build_options()
    return DiscoveryOptions(
        rng_seed = SEED,
        verbose = 1,
        min_levels = 2,
        max_levels = 50,
        loss_tol = 1e-8,
        plateau_window = 3,
        plateau_tol = 1e-4,
        plateau_relative = false,
        plateau_rtol = 1e-3,
    )
end

function build_reference_optimizer()
    return BFGSOptimizer(
        maxiters = BFGS_MAXITERS,
        abstol = BFGS_ABSTOL,
        reltol = BFGS_RELTOL,
        maxiters_solve = BFGS_MAXITERS_SOLVE,
        time_limit_s = BFGS_TIME_LIMIT_S,
        reject_nonfinite = false,
        divergence_limit = Inf,
    )
end

function build_screening_optimizer()
    return BFGSOptimizer(
        maxiters = BFGS_MAXITERS,
        abstol = SCREENING_BFGS_ABSTOL,
        reltol = SCREENING_BFGS_RELTOL,
        maxiters_solve = SCREENING_BFGS_MAXITERS_SOLVE,
        time_limit_s = BFGS_TIME_LIMIT_S,
        reject_nonfinite = true,
        divergence_limit = SCREENING_DIVERGENCE_LIMIT,
    )
end

function build_strategy(; screening_optimizer = nothing)
    return EvoGrow(
        pop_size = POP_SIZE,
        n_levels = N_LEVELS,
        children_per_parent = CHILDREN_PER_PARENT,
        max_terms_per_eq = MAX_TERMS,
        λ = LAMBDA,
        progression = StageProgressionPolicy(
            mode = :stage_local,
            min_levels_per_stage = STAGE_MIN,
        ),
        usage = StageUsagePolicy(
            mode = :hard,
            new_term_bias_prob = SOFT_BIAS,
        ),
        use_pretuning = USE_PRETUNING,
        screening_optimizer = screening_optimizer,
    )
end

function build_trajectory(system)
    tspan = system[:tspan]
    t_grid = collect(range(tspan[1], tspan[2]; length = Int(system[:T])))
    u0 = Float64[x for x in system[:u0]]
    prob = ODEProblem(rhs_for_system(Int(system[:system_id])), copy(u0), tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function metric(meta, key::Symbol, default = 0)
    return haskey(meta, key) ? getfield(meta, key) : default
end

function run_case(label::String, traj::Trajectory, basis::AbstractBasis; screening_optimizer = nothing)
    result = nothing
    elapsed_s = @elapsed begin
        result = discover(
            traj;
            structure = build_strategy(screening_optimizer = screening_optimizer),
            optimizer = build_reference_optimizer(),
            basis = basis,
            loss = MSELoss(),
            options = build_options(),
        )
    end

    meta = result.meta.structure
    expected_idxs = expected_active_idxs(SYSTEM_ID, basis)
    pruned_match = expected_idxs === nothing ? false : support_match_pruned(result.structure, result.params, expected_idxs)

    return (
        label = label,
        elapsed_s = elapsed_s,
        loss = result.loss,
        final_stage = metric(meta, :final_stage, -1),
        pruned_match = pruned_match,
        structure_idxs = result.structure.active_idxs,
        structure_pretty = metric(meta, :best_structure_pretty, ""),
        total_parameter_fits = metric(meta, :total_parameter_fits),
        total_ode_solves = metric(meta, :total_ode_solves),
        total_invalid_solves = metric(meta, :total_invalid_solves),
        total_diverged_solves = metric(meta, :total_diverged_solves),
        total_nonfinite_solves = metric(meta, :total_nonfinite_solves),
        total_step_limit_solves = metric(meta, :total_step_limit_solves),
        total_optimizer_limit_hits = metric(meta, :total_optimizer_limit_hits),
        total_optimizer_iteration_limit_hits = metric(meta, :total_optimizer_iteration_limit_hits),
        total_optimizer_safety_limit_hits = metric(meta, :total_optimizer_safety_limit_hits),
        total_parameter_optimization_time_s = metric(meta, :total_parameter_optimization_time_s, 0.0),
        total_simulation_time_s = metric(meta, :total_simulation_time_s, 0.0),
    )
end

function csv_line(row)
    return join([
        row.label,
        @sprintf("%.6f", row.elapsed_s),
        @sprintf("%.12e", row.loss),
        string(row.final_stage),
        string(row.pruned_match),
        string(row.total_parameter_fits),
        string(row.total_ode_solves),
        string(row.total_invalid_solves),
        string(row.total_diverged_solves),
        string(row.total_nonfinite_solves),
        string(row.total_step_limit_solves),
        string(row.total_optimizer_limit_hits),
        string(row.total_optimizer_iteration_limit_hits),
        string(row.total_optimizer_safety_limit_hits),
        @sprintf("%.6f", row.total_parameter_optimization_time_s),
        @sprintf("%.6f", row.total_simulation_time_s),
    ], ";")
end

function main()
    mkpath(OUT_DIR)
    set_level(INFO)

    system = only([s for s in REGRESSION_SYSTEMS if Int(s[:system_id]) == SYSTEM_ID])
    traj = build_trajectory(system)
    basis = default_staged_polynomial_basis(Int(system[:dim]))

    log_path = joinpath(OUT_DIR, "run.log")
    set_log_file(log_path)
    reset_timer()
    try
        println("Running profile_eval_cost for system=$(SYSTEM_ID), seed=$(SEED), variant=evogrow_v2_2_stage_local")
        ref = run_case("A_reference", traj, basis)
        screened = run_case("B_screening", traj, basis; screening_optimizer = build_screening_optimizer())

        speedup = ref.elapsed_s / screened.elapsed_s
        structure_changed = ref.structure_idxs != screened.structure_idxs

        rows = [ref, screened]
        csv_path = joinpath(OUT_DIR, "summary.csv")
        open(csv_path, "w") do io
            println(io, "label;elapsed_s;loss;final_stage;pruned_match;total_parameter_fits;total_ode_solves;total_invalid_solves;total_diverged_solves;total_nonfinite_solves;total_step_limit_solves;total_optimizer_limit_hits;total_optimizer_iteration_limit_hits;total_optimizer_safety_limit_hits;total_parameter_optimization_time_s;total_simulation_time_s")
            for row in rows
                println(io, csv_line(row))
            end
            println(io, "speedup_B_over_A;$(speedup)")
            println(io, "structure_changed;$(structure_changed)")
        end

        json_path = joinpath(OUT_DIR, "summary.json")
        open(json_path, "w") do io
            JSON3.write(io, Dict(
                "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
                "system_id" => SYSTEM_ID,
                "seed" => SEED,
                "variant" => "evogrow_v2_2_stage_local",
                "reference" => ref,
                "screening" => screened,
                "speedup_B_over_A" => speedup,
                "structure_changed" => structure_changed,
            ))
        end

        txt_path = joinpath(OUT_DIR, "summary.txt")
        open(txt_path, "w") do io
            println(io, "profile_eval_cost")
            println(io, "System $(SYSTEM_ID), seed $(SEED), variant evogrow_v2_2_stage_local")
            println(io, @sprintf("A elapsed %.2fs, loss %.6e, final_stage %s, pruned_match %s", ref.elapsed_s, ref.loss, string(ref.final_stage), string(ref.pruned_match)))
            println(io, @sprintf("B elapsed %.2fs, loss %.6e, final_stage %s, pruned_match %s", screened.elapsed_s, screened.loss, string(screened.final_stage), string(screened.pruned_match)))
            println(io, @sprintf("Speedup B/A %.3fx", speedup))
            println(io, "Structure changed: $(structure_changed)")
        end

        println("Summary CSV: $(csv_path)")
        println("Summary JSON: $(json_path)")
        println("Summary text: $(txt_path)")
        println(@sprintf("Speedup B/A %.3fx | structure_changed=%s", speedup, string(structure_changed)))
    finally
        close_log_file()
    end
end

main()
