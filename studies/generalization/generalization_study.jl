import Pkg
Pkg.activate(dirname(dirname(@__DIR__)))

using DifferentialEquations
using Optimization
using OptimizationOptimJL
using Printf
using Statistics

include(joinpath(dirname(dirname(@__DIR__)), "src", "EvoODE.jl"))
using .EvoODE

# ============================================================
# Configuration
# ============================================================

const POP_SIZE = 10
const N_LEVELS = 20
const CHILDREN_PER_PARENT = 2
const MAX_TERMS_PER_EQ = 6
const BFGS_MAXITERS = 200
const REFIT_MAXITERS = 500
const SEEDS = [42, 123, 7]
const VARIANTS = ["evogrow_v2_2_stage_local", "gp_baseline"]
const OUT_DIR = joinpath(dirname(dirname(@__DIR__)), "outputs", "studies", "generalization")

# ============================================================
# System families
# ============================================================

Base.@kwdef struct GeneralizationSystem
    name::String
    slug::String
    dim::Int
    u0::Vector{Float64}
    tspan::Tuple{Float64,Float64}
    T::Int
    train_params::NamedTuple
    test_params::Vector{NamedTuple}
    expected_terms::Vector{Vector{String}}
    rhs_builder::Function
end

function logistic_rhs(params::NamedTuple)
    r = params.r
    k = params.k
    return function (du, u, _, _)
        du[1] = r * u[1] - k * u[1]^2
    end
end

function lotka_rhs(params::NamedTuple)
    a = params.a
    b = params.b
    c = params.c
    d = params.d
    return function (du, u, _, _)
        du[1] = a * u[1] - b * u[1] * u[2]
        du[2] = c * u[1] * u[2] - d * u[2]
    end
end

function sir_rhs(params::NamedTuple)
    beta = params.beta
    gamma = params.gamma
    return function (du, u, _, _)
        du[1] = -beta * u[1] * u[2]
        du[2] = beta * u[1] * u[2] - gamma * u[2]
    end
end

const SYSTEMS = GeneralizationSystem[
    GeneralizationSystem(
        name = "Logistic growth",
        slug = "logistic_growth",
        dim = 1,
        u0 = [10.0],
        tspan = (0.0, 10.0),
        T = 100,
        train_params = (r = 0.79, k = 0.0106),
        test_params = [
            (r = 0.50, k = 0.008),
            (r = 1.20, k = 0.020),
            (r = 0.60, k = 0.015),
            (r = 1.00, k = 0.005)
        ],
        expected_terms = [["u1", "u1^2"]],
        rhs_builder = logistic_rhs
    ),
    GeneralizationSystem(
        name = "Lotka-Volterra competition",
        slug = "lotka_volterra",
        dim = 2,
        u0 = [1.0, 1.0],
        tspan = (0.0, 5.0),
        T = 100,
        train_params = (a = 3.0, b = 2.0, c = 1.0, d = 2.0),
        test_params = [
            (a = 2.0, b = 1.5, c = 0.8, d = 1.5),
            (a = 4.0, b = 2.5, c = 1.5, d = 2.5),
            (a = 2.5, b = 1.0, c = 0.5, d = 1.0),
            (a = 3.5, b = 3.0, c = 2.0, d = 3.0)
        ],
        expected_terms = [["u1", "u1*u2"], ["u1*u2", "u2"]],
        rhs_builder = lotka_rhs
    ),
    GeneralizationSystem(
        name = "SIR model",
        slug = "sir_model",
        dim = 2,
        u0 = [0.99, 0.01],
        tspan = (0.0, 30.0),
        T = 100,
        train_params = (beta = 0.4, gamma = 0.314),
        test_params = [
            (beta = 0.2, gamma = 0.1),
            (beta = 0.6, gamma = 0.5),
            (beta = 0.3, gamma = 0.2),
            (beta = 0.8, gamma = 0.6)
        ],
        expected_terms = [["u1*u2"], ["u1*u2", "u2"]],
        rhs_builder = sir_rhs
    )
]

# ============================================================
# Helpers
# ============================================================

function generate_trajectory(sys::GeneralizationSystem, params::NamedTuple)
    t_grid = collect(range(sys.tspan[1], sys.tspan[2]; length = sys.T))
    prob = ODEProblem(sys.rhs_builder(params), copy(sys.u0), sys.tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function build_strategy(variant::String, dim::Int)
    if variant == "evogrow_v2_2_stage_local"
        kwargs = Dict{Symbol,Any}(
            :pop_size => POP_SIZE,
            :n_levels => N_LEVELS,
            :children_per_parent => CHILDREN_PER_PARENT,
            :max_terms_per_eq => MAX_TERMS_PER_EQ,
            :use_pretuning => true,
            :progression => StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 2),
            :usage => StageUsagePolicy(mode = :hard, new_term_bias_prob = 0.75),
            Symbol("\u03bb") => 1e-3
        )
        return EvoGrow(; kwargs...)
    elseif variant == "gp_baseline"
        kwargs = Dict{Symbol,Any}(
            :pop_size => POP_SIZE,
            :n_generations => N_LEVELS,
            :tournament_k => 3,
            :p_crossover => 0.7,
            :p_mutation => 0.3,
            :max_terms_per_eq => MAX_TERMS_PER_EQ,
            :init_min_terms => 1,
            :init_max_terms => 2,
            Symbol("\u03bb") => 1e-3
        )
        return GPStructureSearch(; kwargs...)
    end
    error("Unsupported variant=$(variant)")
end

function discovery_options(seed::Int)
    return DiscoveryOptions(
        rng_seed = seed,
        verbose = 1,
        min_levels = 2,
        max_levels = 50,
        loss_tol = 1e-8,
        plateau_window = 3,
        plateau_tol = 1e-4,
        plateau_relative = false,
        plateau_rtol = 1e-3
    )
end

function basis_name_to_idx(basis::AbstractBasis)
    return Dict(basis_term_name(basis, i) => i for i in 1:basis_num_terms(basis))
end

function expected_active_idxs(sys::GeneralizationSystem, basis::AbstractBasis)
    name_to_idx = basis_name_to_idx(basis)
    return [sort([name_to_idx[name] for name in eq_terms]) for eq_terms in sys.expected_terms]
end

function support_match(structure::StructureSpec, expected_idxs::Vector{Vector{Int}})
    if length(structure.active_idxs) != length(expected_idxs)
        return false
    end
    for (got, expected) in zip(structure.active_idxs, expected_idxs)
        if sort(unique(got)) != sort(unique(expected))
            return false
        end
    end
    return true
end

function format_csv_value(value)
    if value === nothing
        return ""
    elseif value isa Bool
        return value ? "true" : "false"
    else
        s = string(value)
        s = replace(s, "\"" => "\"\"")
        if occursin(',', s) || occursin('"', s) || occursin('\n', s) || occursin('\r', s)
            return "\"" * s * "\""
        end
        return s
    end
end

function write_csv(path::String, header::Vector{String}, rows::Vector{<:Tuple})
    open(path, "w") do io
        println(io, join(header, ","))
        for row in rows
            println(io, join([format_csv_value(v) for v in row], ","))
        end
    end
    return path
end

function run_discovery(traj::Trajectory,
                       sys::GeneralizationSystem,
                       variant::String,
                       seed::Int,
                       log_path::String)
    basis = default_staged_polynomial_basis(sys.dim)
    structure = build_strategy(variant, sys.dim)
    optimizer = BFGSOptimizer(maxiters = BFGS_MAXITERS)
    options = discovery_options(seed)

    set_log_file(log_path)
    reset_timer()

    try
        t0 = time()
        result = discover(
            traj;
            structure = structure,
            optimizer = optimizer,
            basis = basis,
            loss = MSELoss(),
            options = options
        )
        return result, time() - t0, basis
    catch err
        log_exception(
            "Discovery failed",
            err;
            context = Dict(
                :system => sys.slug,
                :variant => variant,
                :seed => seed
            )
        )
        return nothing, nothing, basis
    finally
        close_log_file()
    end
end

function refit_structure(structure::StructureSpec,
                         basis::AbstractBasis,
                         traj::Trajectory)
    f!, n_params, _ = build_rhs(structure, basis)
    loss = MSELoss()

    if n_params == 0
        Yhat = simulate(f!, Float64[], traj; clamp_val = 10.0)
        return evaluate_loss(loss, Yhat, traj.x), Float64[]
    end

    function objective(p)
        params = Vector{Float64}(p)
        Yhat = simulate(f!, params, traj; clamp_val = 10.0)
        any(isnan, Yhat) && return Inf
        l = evaluate_loss(loss, Yhat, traj.x)
        return isfinite(l) ? l : Inf
    end

    p0 = zeros(Float64, n_params)

    try
        optfun = OptimizationFunction((p, _) -> objective(p), Optimization.AutoFiniteDiff())
        optprob = OptimizationProblem(optfun, p0)
        result = Optimization.solve(
            optprob,
            OptimizationOptimJL.BFGS();
            maxiters = REFIT_MAXITERS
        )
        best_loss = result.minimum
        best_params = Vector{Float64}(result.u)
        return isfinite(best_loss) ? best_loss : nothing, best_params
    catch
        return nothing, nothing
    end
end

function mean_or_nothing(values)
    valid = [x for x in values if x !== nothing]
    isempty(valid) && return nothing
    return mean(valid)
end

function min_or_nothing(values)
    valid = [x for x in values if x !== nothing]
    isempty(valid) && return nothing
    return minimum(valid)
end

function max_or_nothing(values)
    valid = [x for x in values if x !== nothing]
    isempty(valid) && return nothing
    return maximum(valid)
end

# ============================================================
# Main study
# ============================================================

mkpath(OUT_DIR)

summary_rows = Tuple[]
detail_rows = Tuple[]
report_rows = NamedTuple[]

for sys in SYSTEMS
    train_traj = generate_trajectory(sys, sys.train_params)

    for variant in VARIANTS
        for seed in SEEDS
            train_log = joinpath(OUT_DIR, @sprintf("gen_%s_%s_seed%d_train.log", sys.slug, variant, seed))
            train_result, train_elapsed_s, basis = run_discovery(train_traj, sys, variant, seed, train_log)

            train_loss = train_result === nothing ? nothing : train_result.loss
            train_exact_support_match = nothing
            if train_result !== nothing
                train_exact_support_match = support_match(train_result.structure, expected_active_idxs(sys, basis))
            end

            refit_losses = Vector{Union{Nothing,Float64}}()
            fresh_losses = Vector{Union{Nothing,Float64}}()
            refit_success_count = 0

            for (param_set_id, test_params) in enumerate(sys.test_params)
                test_traj = generate_trajectory(sys, test_params)

                refit_loss = nothing
                if train_result !== nothing
                    refit_loss, _ = refit_structure(train_result.structure, basis, test_traj)
                end

                fresh_log = joinpath(
                    OUT_DIR,
                    @sprintf("gen_%s_%s_seed%d_test%d.log", sys.slug, variant, seed, param_set_id)
                )
                fresh_result, _, _ = run_discovery(test_traj, sys, variant, seed, fresh_log)
                fresh_loss = fresh_result === nothing ? nothing : fresh_result.loss

                refit_success = nothing
                if train_loss !== nothing && refit_loss !== nothing
                    refit_success = refit_loss < 10 * train_loss
                    if refit_success
                        refit_success_count += 1
                    end
                end

                push!(refit_losses, refit_loss)
                push!(fresh_losses, fresh_loss)

                push!(
                    detail_rows,
                    (
                        sys.name,
                        variant,
                        seed,
                        param_set_id,
                        train_loss,
                        refit_loss,
                        fresh_loss,
                        refit_success
                    )
                )
            end

            mean_refit_loss = mean_or_nothing(refit_losses)
            min_refit_loss = min_or_nothing(refit_losses)
            max_refit_loss = max_or_nothing(refit_losses)
            mean_fresh_loss = mean_or_nothing(fresh_losses)

            push!(
                summary_rows,
                (
                    sys.name,
                    variant,
                    seed,
                    train_loss,
                    train_exact_support_match,
                    mean_refit_loss,
                    min_refit_loss,
                    max_refit_loss,
                    mean_fresh_loss
                )
            )

            push!(
                report_rows,
                (
                    system_name = sys.name,
                    variant = variant,
                    seed = seed,
                    train_loss = train_loss,
                    mean_refit_loss = mean_refit_loss,
                    mean_fresh_loss = mean_fresh_loss,
                    refit_success_count = refit_success_count
                )
            )
        end
    end
end

summary_header = [
    "system_name",
    "variant",
    "seed",
    "train_loss",
    "train_exact_support_match",
    "mean_refit_loss",
    "min_refit_loss",
    "max_refit_loss",
    "mean_fresh_loss"
]

detail_header = [
    "system_name",
    "variant",
    "seed",
    "param_set_id",
    "train_loss",
    "refit_loss",
    "fresh_loss",
    "refit_success"
]

summary_path = joinpath(OUT_DIR, "generalization_summary.csv")
detail_path = joinpath(OUT_DIR, "generalization_detail.csv")

write_csv(summary_path, summary_header, summary_rows)
write_csv(detail_path, detail_header, detail_rows)

println("=== Generalization Study ===")
for row in report_rows
    println("System: $(row.system_name)")
    println("  Variant: $(row.variant) | Seed: $(row.seed)")
    println("    train_loss:       $(row.train_loss === nothing ? "" : row.train_loss)")
    println("    mean_refit_loss:  $(row.mean_refit_loss === nothing ? "" : row.mean_refit_loss)")
    println("    mean_fresh_loss:  $(row.mean_fresh_loss === nothing ? "" : row.mean_fresh_loss)")
    println("    refit_success:    $(row.refit_success_count)/4")
end
