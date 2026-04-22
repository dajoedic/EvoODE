import Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

# ============================================================
# Usage / startup
# ============================================================

if isempty(ARGS)
    error("Usage: julia experiments/run_experiment.jl <experiment_id>")
end

const EXPERIMENT_ID = ARGS[1]
const EXPERIMENT_DIR = joinpath(@__DIR__, EXPERIMENT_ID)
const MANIFEST_PATH = joinpath(EXPERIMENT_DIR, "manifest.json")

if !isdir(EXPERIMENT_DIR)
    error("Experiment directory does not exist: $(EXPERIMENT_DIR)")
end

if !isfile(MANIFEST_PATH)
    error("Manifest not found: $(MANIFEST_PATH)")
end

const MANIFEST = try
    JSON3.read(read(MANIFEST_PATH, String))
catch err
    error("Failed to read manifest JSON: $(sprint(showerror, err))")
end

set_level(INFO)

# ============================================================
# Hardcoded benchmark systems / helpers
# ============================================================

function rhs_02!(du, u, _, _)
    du[1] = 0.23 * u[1]
end

function rhs_03!(du, u, _, _)
    du[1] = 0.79 * u[1] * (1.0 - u[1] / 74.3)
end

function rhs_11!(du, u, _, _)
    du[1] = -u[1]^3
end

function rhs_23!(du, u, _, _)
    du[1] = 0.21 - sin(u[1])
end

function rhs_24!(du, u, _, _)
    du[1] = u[2]
    du[2] = -2.1 * u[1]
end

function rhs_26!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

function rhs_31!(du, u, _, _)
    du[1] = -0.4 * u[1] * u[2]
    du[2] = 0.4 * u[1] * u[2] - 0.314 * u[2]
end

function rhs_37!(du, u, _, _)
    du[1] = u[2]
    du[2] = -u[1] - 0.43 * (u[1]^2 - 1.0) * u[2]
end

function rhs_54!(du, u, _, _)
    du[1] = 5.1 * (u[2] - u[1])
    du[2] = 12.0 * u[1] - u[2] - u[1] * u[3]
    du[3] = u[1] * u[2] - 1.67 * u[3]
end

function rhs_63!(du, u, _, _)
    du[1] = -0.28 * u[1] * u[3]
    du[2] = 0.28 * u[1] * u[3] - 0.47 * u[2]
    du[3] = 0.47 * u[2] - 0.30 * u[3]
    du[4] = 0.30 * u[3]
end

function rhs_for_system(system_id::Int)
    if system_id == 2
        return rhs_02!
    elseif system_id == 3
        return rhs_03!
    elseif system_id == 11
        return rhs_11!
    elseif system_id == 23
        return rhs_23!
    elseif system_id == 24
        return rhs_24!
    elseif system_id == 26
        return rhs_26!
    elseif system_id == 31
        return rhs_31!
    elseif system_id == 37
        return rhs_37!
    elseif system_id == 54
        return rhs_54!
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

function iso_timestamp()
    return Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")
end

function current_git_hash()
    try
        return String(strip(read(`git rev-parse HEAD`, String)))
    catch
        return "unknown"
    end
end

function read_json(path::String)
    return JSON3.read(read(path, String))
end

function write_json_atomic(path::String, obj)
    tmp_path = path * ".tmp"
    open(tmp_path, "w") do io
        JSON3.write(io, obj)
    end
    mv(tmp_path, path; force = true)
    return path
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

function prepare_log_file(log_path::String, timestamp::String)
    previous_content = isfile(log_path) ? read(log_path, String) : ""
    restart = isfile(log_path)

    set_log_file(log_path)
    if restart
        io = EvoODE.EvoLogger.LOGGER.log_io
        if io !== nothing
            if !isempty(previous_content)
                write(io, previous_content)
                if !endswith(previous_content, "\n")
                    println(io)
                end
            end
            println(io, "=== RESTART at $(timestamp) ===")
            flush(io)
        end
    end
    reset_timer()
    return nothing
end

function build_trajectory(cfg)
    rhs! = rhs_for_system(Int(cfg.system_id))
    tspan = (Float64(cfg.system_tspan[1]), Float64(cfg.system_tspan[2]))
    t_grid = collect(range(tspan[1], tspan[2]; length = Int(cfg.system_T)))
    u0 = Float64[x for x in cfg.system_u0]
    prob = ODEProblem(rhs!, copy(u0), tspan, nothing)

    try
        sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
        if length(sol.t) != length(t_grid)
            return nothing
        end
        return Trajectory(t_grid, Array(sol)')
    catch
        return nothing
    end
end

function build_strategy_basis_optimizer(cfg)
    dim = Int(cfg.system_dim)
    if startswith(String(cfg.variant), "gp_")
        kwargs = Dict{Symbol,Any}(
            :pop_size => Int(cfg.pop_size),
            :n_generations => Int(cfg.n_levels),
            :tournament_k => 3,
            :p_crossover => 0.7,
            :p_mutation => 0.3,
            :max_terms_per_eq => Int(cfg.max_terms_per_eq),
            :init_min_terms => 1,
            :init_max_terms => 2,
            Symbol("\u03bb") => Float64(cfg.lambda)
        )
        structure = GPStructureSearch(; kwargs...)
        basis = default_staged_polynomial_basis(dim)
    else
        kwargs = Dict{Symbol,Any}(
            :pop_size => Int(cfg.pop_size),
            :n_levels => Int(cfg.n_levels),
            :children_per_parent => Int(cfg.children_per_parent),
            :max_terms_per_eq => Int(cfg.max_terms_per_eq),
            :use_pretuning => Bool(cfg.use_pretuning),
            :progression => StageProgressionPolicy(
                mode = Symbol(String(cfg.progression_mode)),
                min_levels_per_stage = Int(cfg.min_levels_per_stage)
            ),
            :usage => StageUsagePolicy(
                mode = Symbol(String(cfg.usage_mode)),
                new_term_bias_prob = Float64(cfg.new_term_bias_prob)
            ),
            Symbol("\u03bb") => Float64(cfg.lambda)
        )
        structure = EvoGrow(; kwargs...)
        if String(cfg.variant) == "evogrow_v1"
            basis = default_polynomial_basis(dim)
        else
            basis = default_staged_polynomial_basis(dim)
        end
    end

    optimizer = BFGSOptimizer(maxiters = Int(cfg.bfgs_maxiters))
    options = DiscoveryOptions(
        rng_seed = Int(cfg.seed),
        verbose = 1,
        min_levels = 2,
        max_levels = 50,
        loss_tol = 1e-8,
        plateau_window = 3,
        plateau_tol = 1e-4,
        plateau_relative = false,
        plateau_rtol = 1e-3
    )

    return structure, basis, optimizer, options
end

function to_plain_dict(x)
    if x isa NamedTuple
        return Dict(String(k) => to_plain_dict(v) for (k, v) in pairs(x))
    elseif x isa Pair
        return Dict("first" => to_plain_dict(first(x)), "second" => to_plain_dict(last(x)))
    elseif x isa AbstractVector
        return [to_plain_dict(v) for v in x]
    elseif x isa Tuple
        return [to_plain_dict(v) for v in x]
    else
        return x
    end
end

function compute_metrics(result::DiscoveryResult, cfg, basis::AbstractBasis, elapsed_s::Float64)
    meta = result.meta.structure
    stage_level_counts = haskey(meta, :stage_level_counts) ? collect(meta.stage_level_counts) : Int[]
    final_stage = haskey(meta, :final_stage) ? Int(meta.final_stage) : nothing
    representability = String(cfg.system_representability)
    expected_stage = Int(cfg.system_expected_stage)

    exact_support_match = nothing
    stage_overshoot = nothing
    wasted_levels = nothing

    if representability == "exact"
        expected_idxs = expected_active_idxs(Int(cfg.system_id), basis)
        exact_support_match = expected_idxs === nothing ? false : support_match(result.structure, expected_idxs)
        stage_overshoot = final_stage === nothing ? nothing : max(0, final_stage - expected_stage)
        wasted_levels = isempty(stage_level_counts) ? 0 : sum(stage_level_counts[(expected_stage + 1):end]; init = 0)
    end

    return Dict(
        "loss" => result.loss,
        "objective" => result.objective,
        "exact_support_match" => exact_support_match,
        "final_stage" => final_stage,
        "stage_overshoot" => stage_overshoot,
        "wasted_levels" => wasted_levels,
        "total_loss_evals" => haskey(meta, :total_loss_evals) ? Int(meta.total_loss_evals) : nothing,
        "total_invalid_evals" => haskey(meta, :total_invalid_evals) ? Int(meta.total_invalid_evals) : nothing,
        "elapsed_s" => elapsed_s,
        "partial" => false
    )
end

function partial_metrics(elapsed_s::Float64)
    return Dict(
        "loss" => nothing,
        "objective" => nothing,
        "exact_support_match" => nothing,
        "final_stage" => nothing,
        "stage_overshoot" => nothing,
        "wasted_levels" => nothing,
        "total_loss_evals" => nothing,
        "total_invalid_evals" => nothing,
        "elapsed_s" => elapsed_s,
        "partial" => true
    )
end

function build_result_payload(result::DiscoveryResult, cfg, metrics::Dict)
    meta = result.meta.structure
    level_log = haskey(meta, :level_log) ? [
        Dict(
            "level" => Int(entry.level),
            "stage" => Int(entry.stage),
            "best_loss" => entry.best_loss,
            "best_objective" => entry.best_objective,
            "n_params" => Int(entry.n_params),
            "elapsed_s" => entry.elapsed_s
        )
        for entry in meta.level_log
    ] : Any[]

    return Dict(
        "run_id" => String(cfg.run_id),
        "experiment_id" => String(cfg.experiment_id),
        "final_loss" => result.loss,
        "final_objective" => result.objective,
        "final_stage" => metrics["final_stage"],
        "termination_reason" => haskey(meta, :termination_reason) ? string(meta.termination_reason) : "unknown",
        "structure_pretty" => haskey(meta, :best_structure_pretty) ? String(meta.best_structure_pretty) : "",
        "params_length" => length(result.params),
        "exact_support_match" => metrics["exact_support_match"],
        "stage_overshoot" => metrics["stage_overshoot"],
        "wasted_levels" => metrics["wasted_levels"],
        "stage_level_counts" => haskey(meta, :stage_level_counts) ? collect(meta.stage_level_counts) : Int[],
        "stage_histories" => haskey(meta, :stage_histories) ? [collect(hist) for hist in meta.stage_histories] : Any[],
        "promotion_log" => haskey(meta, :promotion_log) ? [to_plain_dict(x) for x in meta.promotion_log] : Any[],
        "level_log" => level_log
    )
end

function write_summary(path::String, cfg, metrics::Dict, termination_reason)
    open(path, "w") do io
        println(io, "run_id: $(cfg.run_id)")
        println(io, "system: $(cfg.system_name)")
        println(io, "variant: $(cfg.variant)")
        println(io, "seed: $(cfg.seed)")
        println(io, "loss: $(metrics["loss"])")
        println(io, "exact_support_match: $(metrics["exact_support_match"])")
        println(io, "final_stage: $(metrics["final_stage"])")
        println(io, "wasted_levels: $(metrics["wasted_levels"])")
        println(io, "elapsed_s: $(metrics["elapsed_s"])")
        println(io, "termination_reason: $(termination_reason)")
    end
    return path
end

function write_status(path::String;
                      status::String,
                      success,
                      failure_reason,
                      failure_detail,
                      started_at,
                      finished_at,
                      git_hash::String)
    obj = Dict(
        "status" => status,
        "success" => success,
        "failure_reason" => failure_reason,
        "failure_detail" => failure_detail,
        "started_at" => started_at,
        "finished_at" => finished_at,
        "git_hash" => git_hash
    )
    write_json_atomic(path, obj)
    return obj
end

function run_one(run_id::String, run_index::Int, total_runs::Int)
    run_dir = joinpath(EXPERIMENT_DIR, "runs", run_id)
    status_path = joinpath(run_dir, "status.json")
    config_path = joinpath(run_dir, "config.json")
    metrics_path = joinpath(run_dir, "metrics.json")
    result_path = joinpath(run_dir, "result.json")
    summary_path = joinpath(run_dir, "summary.txt")
    log_path = joinpath(run_dir, "log.txt")

    cfg = read_json(config_path)
    git_hash = current_git_hash()
    started_at = iso_timestamp()

    @printf("\n[%d/%d] Starting %s | remaining=%d\n",
            run_index,
            total_runs,
            run_id,
            total_runs - run_index + 1)

    write_status(
        status_path;
        status = "running",
        success = nothing,
        failure_reason = nothing,
        failure_detail = nothing,
        started_at = started_at,
        finished_at = nothing,
        git_hash = git_hash
    )

    prepare_log_file(log_path, started_at)

    failure_reason = nothing
    failure_detail = nothing
    elapsed_s = 0.0
    run_t0 = time()
    result = nothing
    metrics = nothing
    success = false

    try
        traj = build_trajectory(cfg)
        if traj === nothing
            failure_reason = "all_invalid"
            error("Ground-truth trajectory generation failed")
        end

        structure, basis, optimizer, options = build_strategy_basis_optimizer(cfg)

        t0 = time()
        result = discover(
            traj;
            structure = structure,
            optimizer = optimizer,
            basis = basis,
            loss = MSELoss(),
            options = options
        )
        elapsed_s = time() - t0

        metrics = compute_metrics(result, cfg, basis, elapsed_s)
        result_payload = build_result_payload(result, cfg, metrics)
        termination_reason = get(result_payload, "termination_reason", "unknown")

        write_json_atomic(metrics_path, metrics)
        write_json_atomic(result_path, result_payload)
        write_summary(summary_path, cfg, metrics, termination_reason)

        write_status(
            status_path;
            status = "finished",
            success = true,
            failure_reason = nothing,
            failure_detail = nothing,
            started_at = started_at,
            finished_at = iso_timestamp(),
            git_hash = git_hash
        )

        success = true
        @printf("Completed %s | loss=%.6e | elapsed=%.2fs | success=true\n",
                run_id,
                result.loss,
                elapsed_s)
    catch err
        elapsed_s = time() - run_t0
        failure_reason = failure_reason === nothing ? "exception" : failure_reason
        failure_detail = sprint(showerror, err)

        log_exception("Run failed", err; context = Dict(:run_id => run_id, :failure_reason => failure_reason))

        metrics = partial_metrics(elapsed_s)
        write_json_atomic(metrics_path, metrics)
        write_summary(summary_path, cfg, metrics, failure_reason)
        write_status(
            status_path;
            status = "failed",
            success = false,
            failure_reason = failure_reason,
            failure_detail = failure_detail,
            started_at = started_at,
            finished_at = iso_timestamp(),
            git_hash = git_hash
        )

        @printf("Completed %s | loss=NA | elapsed=%.2fs | success=false\n",
                run_id,
                elapsed_s)
    finally
        close_log_file()
    end

    return success, metrics, result
end

# ============================================================
# Main run list
# ============================================================

runnable = String[]
for run_id_any in MANIFEST.run_ids
    run_id = String(run_id_any)
    status_path = joinpath(EXPERIMENT_DIR, "runs", run_id, "status.json")
    status_obj = read_json(status_path)
    status = String(status_obj.status)

    if status == "finished"
        continue
    elseif status in ("queued", "running", "interrupted")
        push!(runnable, run_id)
    end
end

@printf("Experiment: %s\n", EXPERIMENT_ID)
@printf("Runnable runs: %d\n", length(runnable))

for (idx, run_id) in enumerate(runnable)
    run_one(run_id, idx, length(runnable))
end
