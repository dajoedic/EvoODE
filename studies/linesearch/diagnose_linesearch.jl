import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf
using Random
using Statistics
using Optimization
using OptimizationOptimJL

include(joinpath(@__DIR__, "..", "output_path_guard.jl"))
include(joinpath(@__DIR__, "..", "regression", "run_regression.jl"))
include(joinpath(@__DIR__, "..", "regression", "phase_b_config.jl"))

const OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "linesearch", "wp_f1"), ARGS)
const JSONL_PATH = joinpath(OUTPUT_DIR, "fit_records.jsonl")
const SUMMARY_CSV_PATH = joinpath(OUTPUT_DIR, "fit_summary.csv")
const SENTINEL = 1e6
const SENTINEL_ATOL = 0.0
const SELECTED_SYSTEMS = [2, 17, 11]
const SELECTED_STRUCTURES = [
    (label = "u1", active_idxs = [[1]]),
    (label = "u1_plus_u1_sq", active_idxs = [[1, 2]]),
]
const SELECTED_PRETUNE = [true, false]
const IC_SET = 1
const SEED = 42

const LAST_LINESEARCH_P = Ref(Float64[])

mutable struct RecordingMSELoss <: AbstractLoss
    records::Vector{NamedTuple{(:params, :loss), Tuple{Vector{Float64}, Float64}}}
end

function EvoODE.evaluate_loss(loss::RecordingMSELoss, Yhat, X)
    value = EvoODE.evaluate_loss(MSELoss(), Yhat, X)
    push!(loss.records, (params = copy(LAST_LINESEARCH_P[]), loss = Float64(value)))
    return value
end

function json_safe(x)
    if x isa AbstractFloat
        isfinite(x) && return x
        return string(x)
    elseif x isa AbstractDict
        return Dict(k => json_safe(v) for (k, v) in x)
    elseif x isa NamedTuple
        return Dict(String(k) => json_safe(v) for (k, v) in pairs(x))
    elseif x isa AbstractVector
        return [json_safe(v) for v in x]
    elseif x isa Tuple
        return [json_safe(v) for v in x]
    else
        return x
    end
end

function with_solve_hook(f::Function, hook)
    old = EvoODE._BFGS_SOLVE_HOOK[]
    EvoODE._BFGS_SOLVE_HOOK[] = hook
    try
        return f()
    finally
        EvoODE._BFGS_SOLVE_HOOK[] = old
    end
end

function backtracking_hook(optprob, algorithm; maxiters, time_limit)
    if algorithm isa OptimizationOptimJL.BFGS
        backtracking = OptimizationOptimJL.Optim.LineSearches.BackTracking()
        return Optimization.solve(
            optprob,
            OptimizationOptimJL.BFGS(linesearch = backtracking);
            maxiters = maxiters,
            time_limit = time_limit,
        )
    end
    return Optimization.solve(optprob, algorithm; maxiters = maxiters, time_limit = time_limit)
end

is_sentinel(x::Float64) = isfinite(x) && abs(x - SENTINEL) <= SENTINEL_ATOL
is_finite_non_sentinel(x::Float64) = isfinite(x) && !is_sentinel(x)

function run_lengths(mask::AbstractVector{Bool})
    lengths = Int[]
    current = 0
    for hit in mask
        if hit
            current += 1
        elseif current > 0
            push!(lengths, current)
            current = 0
        end
    end
    current > 0 && push!(lengths, current)
    return lengths
end

function quantiles_or_empty(xs::Vector{Int})
    isempty(xs) && return Dict{String, Any}()
    sorted = sort(xs)
    pick(q) = sorted[clamp(Int(ceil(q * length(sorted))), 1, length(sorted))]
    return Dict(
        "min" => first(sorted),
        "p50" => pick(0.50),
        "p90" => pick(0.90),
        "p99" => pick(0.99),
        "max" => last(sorted),
    )
end

function evaluation_summary(records)
    losses = [r.loss for r in records]
    sentinel_mask = is_sentinel.(losses)
    finite_mask = is_finite_non_sentinel.(losses)
    sentinel_runs = run_lengths(sentinel_mask)
    finite_runs = run_lengths(finite_mask)
    return (
        total_evals = length(records),
        sentinel_evals = count(sentinel_mask),
        finite_non_sentinel_evals = count(finite_mask),
        nonfinite_loss_evals = count(!isfinite, losses),
        distinct_loss_values = length(Set(losses)),
        sentinel_run_count = length(sentinel_runs),
        sentinel_run_lengths = sentinel_runs,
        sentinel_run_distribution = quantiles_or_empty(sentinel_runs),
        longest_sentinel_run = isempty(sentinel_runs) ? 0 : maximum(sentinel_runs),
        finite_run_count = length(finite_runs),
        longest_finite_run = isempty(finite_runs) ? 0 : maximum(finite_runs),
        first_10_losses = losses[1:min(10, length(losses))],
        last_10_losses = losses[max(1, length(losses) - 9):end],
    )
end

function tracing_rhs(f!::Function)
    return function (du, u, p, t)
        LAST_LINESEARCH_P[] = copy(Vector{Float64}(p))
        return f!(du, u, p, t)
    end
end

function optimizer()
    return BFGSOptimizer(
        maxiters = BFGS_MAXITERS,
        abstol = BFGS_ABSTOL,
        reltol = BFGS_RELTOL,
        maxiters_solve = BFGS_MAXITERS_SOLVE,
        max_loss_evals = BFGS_MAX_LOSS_EVALS,
        clamp_val = BFGS_CLAMP_VAL,
        time_limit_s = BFGS_TIME_LIMIT_S,
        reject_nonfinite = BFGS_REJECT_NONFINITE,
        divergence_limit = BFGS_DIVERGENCE_LIMIT,
    )
end

function initial_p0(structure::StructureSpec, basis, traj, seed::Int, use_pretuning::Bool)
    if use_pretuning
        return EvoODE.pretune_parameters(structure, basis, traj)
    end
    _, n_params, _ = build_rhs(structure, basis)
    Random.seed!(seed)
    return 0.1 .* randn(n_params)
end

function run_fit(system_id::Int, structure_case, use_pretuning::Bool, line_search_label::String)
    system = phase_b_system(system_id)
    traj = build_trajectory(system, IC_SET)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    structure = StructureSpec([copy(v) for v in structure_case.active_idxs])
    f!, n_params, _ = build_rhs(structure, basis)
    loss = RecordingMSELoss(NamedTuple{(:params, :loss), Tuple{Vector{Float64}, Float64}}[])
    p0 = initial_p0(structure, basis, traj, SEED, use_pretuning)
    opt = optimizer()
    options = DiscoveryOptions(rng_seed = SEED, verbose = 0)
    wrapped_rhs! = tracing_rhs(f!)

    LAST_LINESEARCH_P[] = copy(p0)
    elapsed = @elapsed begin
        if line_search_label == "default"
            params, final_loss, meta = fit_parameters(opt, wrapped_rhs!, traj, n_params, loss, options; p0 = p0)
        elseif line_search_label == "backtracking"
            params, final_loss, meta = with_solve_hook(
                () -> fit_parameters(opt, wrapped_rhs!, traj, n_params, loss, options; p0 = p0),
                backtracking_hook,
            )
        else
            error("Unknown line_search_label=$(line_search_label)")
        end
    end

    summary = evaluation_summary(loss.records)
    return Dict{String, Any}(
        "system_id" => system_id,
        "system_name" => String(system[:system_name]),
        "variant_condition" => use_pretuning ? "pretune_on" : "pretune_off",
        "use_pretuning" => use_pretuning,
        "initial_condition_set" => IC_SET,
        "seed" => SEED,
        "structure" => structure_case.label,
        "active_idxs" => structure_case.active_idxs,
        "n_params" => n_params,
        "p0" => p0,
        "line_search" => line_search_label,
        "params" => params,
        "final_loss" => final_loss,
        "fit_meta" => meta,
        "elapsed_s" => elapsed,
        "summary" => summary,
        "evaluations" => [
            Dict("index" => i, "params" => r.params, "loss" => r.loss)
            for (i, r) in enumerate(loss.records)
        ],
    )
end

function csv_escape(x)
    text = string(x)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_outputs(records)
    mkpath(OUTPUT_DIR)
    open(JSONL_PATH, "w") do io
        for record in records
            JSON3.write(io, json_safe(record))
            write(io, '\n')
        end
    end

    header = [
        "system_id",
        "condition",
        "structure",
        "line_search",
        "total_evals",
        "sentinel_evals",
        "finite_non_sentinel_evals",
        "distinct_loss_values",
        "sentinel_run_count",
        "longest_sentinel_run",
        "final_loss",
        "retcode",
        "stop_reason",
        "elapsed_s",
    ]
    open(SUMMARY_CSV_PATH, "w") do io
        println(io, join(header, ","))
        for record in records
            summary = record["summary"]
            meta = record["fit_meta"]
            row = [
                record["system_id"],
                record["variant_condition"],
                record["structure"],
                record["line_search"],
                summary.total_evals,
                summary.sentinel_evals,
                summary.finite_non_sentinel_evals,
                summary.distinct_loss_values,
                summary.sentinel_run_count,
                summary.longest_sentinel_run,
                record["final_loss"],
                meta.retcode,
                meta.stop_reason,
                @sprintf("%.6f", record["elapsed_s"]),
            ]
            println(io, join(csv_escape.(row), ","))
        end
    end
end

function print_compact_summary(records)
    println("regression_fingerprint=$(config_fingerprint())")
    println("phase_b_fingerprint=$(phase_b_fingerprint())")
    println("jsonl=$(JSONL_PATH)")
    println("csv=$(SUMMARY_CSV_PATH)")
    for record in records
        summary = record["summary"]
        @printf(
            "sys=%d condition=%s structure=%s line_search=%s evals=%d sentinel=%d finite=%d distinct=%d longest_sentinel_run=%d final_loss=%.6e retcode=%s\n",
            record["system_id"],
            record["variant_condition"],
            record["structure"],
            record["line_search"],
            summary.total_evals,
            summary.sentinel_evals,
            summary.finite_non_sentinel_evals,
            summary.distinct_loss_values,
            summary.longest_sentinel_run,
            record["final_loss"],
            record["fit_meta"].retcode,
        )
    end
end

function main()
    records = Dict{String, Any}[]
    for system_id in SELECTED_SYSTEMS
        for structure_case in SELECTED_STRUCTURES
            for use_pretuning in SELECTED_PRETUNE
                for line_search_label in ("default", "backtracking")
                    push!(records, run_fit(system_id, structure_case, use_pretuning, line_search_label))
                end
            end
        end
    end
    write_outputs(records)
    print_compact_summary(records)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
