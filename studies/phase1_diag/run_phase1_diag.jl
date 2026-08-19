import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf

include(joinpath(@__DIR__, "..", "..", "src", "EvoODE.jl"))
using .EvoODE
include(joinpath(@__DIR__, "..", "output_path_guard.jl"))

const OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "phase1_diag"), ARGS)

const POP_SIZE = 10
const N_LEVELS = 30
const MAX_TERMS = 6
const LAMBDA = 1e-3
const STAGE_MIN = 2
const SOFT_BIAS = 0.75
const USE_PRETUNING = false
const SEEDS = [42, 123, 7]

const SYSTEMS = [
    Dict(
        :system_id => 3,
        :system_name => "Logistic growth",
        :dim => 1,
        :u0 => [7.3],
        :tspan => (0.0, 20.0),
        :T => 200,
        :expected_stage => 2,
    ),
    Dict(
        :system_id => 11,
        :system_name => "Critical slowing down",
        :dim => 1,
        :u0 => [3.4],
        :tspan => (0.0, 5.0),
        :T => 100,
        :expected_stage => 4,
    ),
    Dict(
        :system_id => 26,
        :system_name => "Lotka-Volterra competition",
        :dim => 2,
        :u0 => [5.0, 4.3],
        :tspan => (0.0, 10.0),
        :T => 200,
        :expected_stage => 3,
    ),
    Dict(
        :system_id => 31,
        :system_name => "SIR infection model",
        :dim => 2,
        :u0 => [7.2, 0.98],
        :tspan => (0.0, 20.0),
        :T => 200,
        :expected_stage => 3,
    ),
    Dict(
        :system_id => 63,
        :system_name => "SEIR epidemic",
        :dim => 4,
        :u0 => [0.6, 0.3, 0.09, 0.01],
        :tspan => (0.0, 30.0),
        :T => 300,
        :expected_stage => 3,
    ),
]

function rhs_03!(du, u, _, _)
    du[1] = 0.79 * u[1] * (1.0 - u[1] / 74.3)
end

function rhs_11!(du, u, _, _)
    du[1] = -u[1]^3
end

function rhs_26!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

function rhs_31!(du, u, _, _)
    du[1] = -0.4 * u[1] * u[2]
    du[2] = 0.4 * u[1] * u[2] - 0.314 * u[2]
end

function rhs_63!(du, u, _, _)
    du[1] = -0.28 * u[1] * u[3]
    du[2] = 0.28 * u[1] * u[3] - 0.47 * u[2]
    du[3] = 0.47 * u[2] - 0.30 * u[3]
    du[4] = 0.30 * u[3]
end

function rhs_for_system(system_id::Int)
    if system_id == 3
        return rhs_03!
    elseif system_id == 11
        return rhs_11!
    elseif system_id == 26
        return rhs_26!
    elseif system_id == 31
        return rhs_31!
    elseif system_id == 63
        return rhs_63!
    end
    error("Unsupported system_id=$(system_id)")
end

function expected_terms_for(system_id::Int)
    if system_id == 2
        return [["u1"]]
    elseif system_id == 3
        return [["u1", "u1^2"]]
    elseif system_id == 11
        return [["u1^3"]]
    elseif system_id == 23
        return nothing
    elseif system_id == 24
        return [["u2"], ["u1"]]
    elseif system_id == 26
        return [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]]
    elseif system_id == 31
        return [["u1*u2"], ["u1*u2", "u2"]]
    elseif system_id == 37
        return nothing
    elseif system_id == 54
        return [["u1", "u2"], ["u1", "u2", "u1*u3"], ["u1*u2", "u3"]]
    elseif system_id == 63
        return [["u1*u3"], ["u1*u3", "u2"], ["u2", "u3"], ["u3"]]
    end
    error("Unsupported system_id=$(system_id)")
end

function basis_name_to_idx(basis::AbstractBasis)
    return Dict(basis_term_name(basis, i) => i for i in 1:basis_num_terms(basis))
end

function expected_active_idxs(system_id::Int, basis::AbstractBasis)
    expected_terms = expected_terms_for(system_id)
    expected_terms === nothing && return nothing
    name_to_idx = basis_name_to_idx(basis)
    return [sort([name_to_idx[name] for name in eq_terms]) for eq_terms in expected_terms]
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

function support_match_pruned(
    structure::StructureSpec,
    params::Vector{Float64},
    expected_idxs::Vector{Vector{Int}}
)
    if length(structure.active_idxs) != length(expected_idxs)
        return false
    end

    offset = 0
    for (got_idxs, exp_idxs) in zip(structure.active_idxs, expected_idxs)
        n_terms = length(got_idxs)
        eq_params = params[(offset + 1):(offset + n_terms)]
        offset += n_terms

        max_abs = isempty(eq_params) ? 0.0 : maximum(abs, eq_params)
        threshold = max(1e-6, 1e-3 * max_abs)

        pruned_idxs = sort([got_idxs[i] for i in 1:n_terms if abs(eq_params[i]) >= threshold])

        if pruned_idxs != sort(unique(exp_idxs))
            return false
        end
    end
    return true
end

function write_json(path::String, obj)
    open(path, "w") do io
        JSON3.write(io, obj)
    end
end

function build_trajectory(system)
    system_id = Int(system[:system_id])
    tspan = system[:tspan]
    t_grid = collect(range(tspan[1], tspan[2]; length = Int(system[:T])))
    u0 = Float64[x for x in system[:u0]]
    prob = ODEProblem(rhs_for_system(system_id), copy(u0), tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function build_strategy(seed::Int, dim::Int)
    strategy = EvoGrow(
        pop_size = POP_SIZE,
        n_levels = N_LEVELS,
        children_per_parent = 2,
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
    )
    basis = default_staged_polynomial_basis(dim)
    optimizer = BFGSOptimizer(maxiters = 200)
    options = DiscoveryOptions(
        rng_seed = seed,
        verbose = 1,
        min_levels = 2,
        max_levels = 50,
        loss_tol = 1e-8,
        plateau_window = 3,
        plateau_tol = 1e-4,
        plateau_relative = false,
        plateau_rtol = 1e-3,
    )
    return strategy, basis, optimizer, options
end

function plain_level_log(meta)
    if !haskey(meta, :level_log)
        return Any[]
    end
    return [
        Dict(
            "level" => Int(entry.level),
            "stage" => Int(entry.stage),
            "best_loss" => entry.best_loss,
            "best_objective" => entry.best_objective,
            "n_params" => Int(entry.n_params),
        )
        for entry in meta.level_log
    ]
end

function run_one(system, seed::Int)
    system_id = Int(system[:system_id])
    system_name = String(system[:system_name])
    dim = Int(system[:dim])
    expected_stage = Int(system[:expected_stage])
    output_path = joinpath(OUTPUT_DIR, "$(system_id)_$(seed).json")

    try
        traj = build_trajectory(system)
        strategy, basis, optimizer, options = build_strategy(seed, dim)

        result = nothing
        elapsed = @elapsed result = discover(
            traj;
            structure = strategy,
            optimizer = optimizer,
            basis = basis,
            loss = MSELoss(),
            options = options,
        )

        meta = result.meta.structure
        final_stage = haskey(meta, :final_stage) ? Int(meta.final_stage) : nothing
        stage_level_counts = haskey(meta, :stage_level_counts) ? collect(meta.stage_level_counts) : Int[]
        stage_overshoot = final_stage === nothing ? nothing : max(0, final_stage - expected_stage)
        wasted_levels = isempty(stage_level_counts) ? 0 : sum(stage_level_counts[(expected_stage + 1):end]; init = 0)
        expected_idxs = expected_active_idxs(system_id, basis)
        exact_raw = expected_idxs === nothing ? false : support_match(result.structure, expected_idxs)
        exact_pruned = expected_idxs === nothing ? false : support_match_pruned(result.structure, result.params, expected_idxs)

        payload = Dict(
            "system_id" => system_id,
            "system_name" => system_name,
            "seed" => seed,
            "n_levels_config" => N_LEVELS,
            "use_pretuning" => USE_PRETUNING,
            "final_loss" => result.loss,
            "final_stage" => final_stage,
            "expected_stage" => expected_stage,
            "stage_overshoot" => stage_overshoot,
            "wasted_levels" => wasted_levels,
            "structure_pretty" => haskey(meta, :best_structure_pretty) ? String(meta.best_structure_pretty) : "",
            "exact_support_match_raw" => exact_raw,
            "exact_support_match_pruned" => exact_pruned,
            "elapsed_s" => elapsed,
            "stage_level_counts" => stage_level_counts,
            "level_log" => plain_level_log(meta),
        )
        write_json(output_path, payload)
        return payload
    catch err
        payload = Dict(
            "system_id" => system_id,
            "system_name" => system_name,
            "seed" => seed,
            "n_levels_config" => N_LEVELS,
            "use_pretuning" => USE_PRETUNING,
            "final_loss" => nothing,
            "error" => sprint(showerror, err),
            "elapsed_s" => nothing,
        )
        @printf("ERROR sys=%d seed=%d: %s\n", system_id, seed, payload["error"])
        write_json(output_path, payload)
        return payload
    end
end

function summary_line(payload)
    if haskey(payload, "error")
        return @sprintf(
            "sys=%d seed=%d  loss=null  stage=null/%s  pruned_match=null  elapsed=nulls  error=%s",
            payload["system_id"],
            payload["seed"],
            string(get(payload, "expected_stage", "null")),
            payload["error"],
        )
    end
    return @sprintf(
        "sys=%d seed=%d  loss=%.3e  stage=%s/%d  pruned_match=%s  elapsed=%.1fs",
        payload["system_id"],
        payload["seed"],
        payload["final_loss"],
        string(payload["final_stage"]),
        payload["expected_stage"],
        string(payload["exact_support_match_pruned"]),
        payload["elapsed_s"],
    )
end

function main()
    mkpath(OUTPUT_DIR)
    set_level(INFO)

    summary_lines = String[]
    for system in SYSTEMS
        for seed in SEEDS
            @printf("Running sys=%d seed=%d at %s\n", system[:system_id], seed, Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))
            payload = run_one(system, seed)
            line = summary_line(payload)
            push!(summary_lines, line)
            println(line)
        end
    end

    summary_path = joinpath(OUTPUT_DIR, "summary.txt")
    open(summary_path, "w") do io
        for line in summary_lines
            println(io, line)
        end
    end
    println("Wrote $(summary_path)")
end

main()
