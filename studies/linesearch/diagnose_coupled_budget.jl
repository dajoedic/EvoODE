import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf
using Random

include(joinpath(@__DIR__, "..", "output_path_guard.jl"))
include(joinpath(@__DIR__, "..", "regression", "run_regression.jl"))
include(joinpath(@__DIR__, "..", "regression", "phase_b_config.jl"))

const OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "linesearch", "wp_f2"), ARGS; allow_append = true)
const JSONL_PATH = joinpath(OUTPUT_DIR, "fit_records.jsonl")
const SUMMARY_CSV_PATH = joinpath(OUTPUT_DIR, "fit_summary.csv")
const BUDGETS = [500, 1_000, 2_000, 5_000, 10_000, 20_000]
const SELECTED_SYSTEMS = [26, 31, 54]
const SELECTED_PRETUNE = [true, false]
const IC_SET = 1
const SEED = 42

const LAST_COUPLED_LINESEARCH_P = Ref(Float64[])

mutable struct CoupledRecordingMSELoss <: AbstractLoss
    records::Vector{NamedTuple{(:params, :loss), Tuple{Vector{Float64}, Float64}}}
end

function EvoODE.evaluate_loss(loss::CoupledRecordingMSELoss, Yhat, X)
    value = EvoODE.evaluate_loss(MSELoss(), Yhat, X)
    push!(loss.records, (params = copy(LAST_COUPLED_LINESEARCH_P[]), loss = Float64(value)))
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

function csv_escape(x)
    text = string(x)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function _arg_value(args::Vector{String}, name::String)
    idx = findfirst(==(name), args)
    idx === nothing && return nothing
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _parse_int_list(value::Union{Nothing, String}, default::Vector{Int})
    value === nothing && return default
    isempty(strip(value)) && return default
    return [parse(Int, strip(part)) for part in split(value, ",")]
end

function _parse_string_list(value::Union{Nothing, String}, default::Vector{String})
    value === nothing && return default
    isempty(strip(value)) && return default
    return [strip(part) for part in split(value, ",")]
end

function selected_systems(args::Vector{String})
    value = _arg_value(args, "--systems")
    value === nothing && (value = strip(get(ENV, "EVO_LINESEARCH_SYSTEMS", "")))
    return _parse_int_list(isempty(value) ? nothing : value, SELECTED_SYSTEMS)
end

function selected_structure_labels(args::Vector{String})
    value = _arg_value(args, "--structures")
    value === nothing && (value = strip(get(ENV, "EVO_LINESEARCH_STRUCTURES", "")))
    return _parse_string_list(isempty(value) ? nothing : value, ["true", "oversized"])
end

function selected_conditions(args::Vector{String})
    value = _arg_value(args, "--conditions")
    value === nothing && (value = strip(get(ENV, "EVO_LINESEARCH_CONDITIONS", "")))
    labels = _parse_string_list(isempty(value) ? nothing : value, ["pretune_on", "pretune_off"])
    for label in labels
        label in ("pretune_on", "pretune_off") || error("Unknown condition $(label)")
    end
    return [label == "pretune_on" for label in labels]
end

function append_requested(args::Vector{String})
    "--append" in args && return true
    flag = lowercase(strip(get(ENV, "EVO_LINESEARCH_APPEND", "")))
    return flag in ("1", "true", "yes")
end

function tracing_rhs(f!::Function)
    return function (du, u, p, t)
        LAST_COUPLED_LINESEARCH_P[] = copy(Vector{Float64}(p))
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

function true_structure_case(system_id::Int, basis)
    active = expected_active_idxs(system_id, basis)
    active === nothing && error("No exact expected structure for system $(system_id)")
    names = [[basis_term_name(basis, idx) for idx in eq_terms] for eq_terms in active]
    return (label = "true", active_idxs = active, term_names = names)
end

function oversized_structure_case(dim::Int, basis)
    term_limit = MAX_TERMS
    active = [collect(1:min(term_limit, basis_num_terms(basis))) for _ in 1:dim]
    names = [[basis_term_name(basis, idx) for idx in eq_terms] for eq_terms in active]
    return (label = "oversized_$(term_limit)_per_eq", active_idxs = active, term_names = names)
end

function best_finite_summary(records, final_loss::Float64)
    finite = [(i = i, loss = r.loss) for (i, r) in enumerate(records) if isfinite(r.loss)]
    if isempty(finite)
        return (
            best_loss = Inf,
            first_best_index = nothing,
            first_best_fraction = nothing,
            budget_losses = Dict(string(b) => Inf for b in BUDGETS),
            budget_factors = Dict(string(b) => Inf for b in BUDGETS),
        )
    end

    best_loss = minimum(x.loss for x in finite)
    first_idx = first(x.i for x in finite if x.loss == best_loss)
    denom = isfinite(final_loss) && final_loss > 0.0 ? final_loss : best_loss
    budget_losses = Dict{String, Float64}()
    budget_factors = Dict{String, Float64}()
    for budget in BUDGETS
        upto = [x.loss for x in finite if x.i <= budget]
        budget_loss = isempty(upto) ? Inf : minimum(upto)
        budget_losses[string(budget)] = budget_loss
        budget_factors[string(budget)] = isfinite(budget_loss) && isfinite(denom) && denom > 0.0 ? budget_loss / denom : Inf
    end

    return (
        best_loss = best_loss,
        first_best_index = first_idx,
        first_best_fraction = first_idx / length(records),
        budget_losses = budget_losses,
        budget_factors = budget_factors,
    )
end

function run_fit(system_id::Int, structure_case, use_pretuning::Bool)
    system = phase_b_system(system_id)
    traj = build_trajectory(system, IC_SET)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    structure = StructureSpec([copy(v) for v in structure_case.active_idxs])
    f!, n_params, _ = build_rhs(structure, basis)
    loss = CoupledRecordingMSELoss(NamedTuple{(:params, :loss), Tuple{Vector{Float64}, Float64}}[])
    p0 = initial_p0(structure, basis, traj, SEED, use_pretuning)
    opt = optimizer()
    options = DiscoveryOptions(rng_seed = SEED, verbose = 0)
    wrapped_rhs! = tracing_rhs(f!)

    LAST_COUPLED_LINESEARCH_P[] = copy(p0)
    elapsed = @elapsed params, final_loss, meta =
        fit_parameters(opt, wrapped_rhs!, traj, n_params, loss, options; p0 = p0)
    best_summary = best_finite_summary(loss.records, Float64(final_loss))

    return Dict{String, Any}(
        "system_id" => system_id,
        "system_name" => String(system[:system_name]),
        "dim" => Int(system[:dim]),
        "variant_condition" => use_pretuning ? "pretune_on" : "pretune_off",
        "use_pretuning" => use_pretuning,
        "initial_condition_set" => IC_SET,
        "seed" => SEED,
        "structure" => structure_case.label,
        "term_names" => structure_case.term_names,
        "active_idxs" => structure_case.active_idxs,
        "n_params" => n_params,
        "p0" => p0,
        "params" => params,
        "final_loss" => final_loss,
        "fit_meta" => meta,
        "elapsed_s" => elapsed,
        "summary" => (
            total_evals = length(loss.records),
            finite_loss_evals = count(r -> isfinite(r.loss), loss.records),
            best_finite_loss = best_summary.best_loss,
            first_best_index = best_summary.first_best_index,
            first_best_fraction = best_summary.first_best_fraction,
            budget_losses = best_summary.budget_losses,
            budget_factors = best_summary.budget_factors,
        ),
        "evaluations" => [
            Dict("index" => i, "params" => r.params, "loss" => r.loss)
            for (i, r) in enumerate(loss.records)
        ],
    )
end

function structure_cases(system_id::Int)
    system = phase_b_system(system_id)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    return [
        true_structure_case(system_id, basis),
        oversized_structure_case(Int(system[:dim]), basis),
    ]
end

function csv_header()
    return [
        "system_id",
        "dim",
        "condition",
        "structure",
        "n_params",
        "total_evals",
        "first_best_index",
        "first_best_fraction",
        "final_loss",
        "best_finite_loss",
        "factor_500",
        "factor_1000",
        "factor_2000",
        "factor_5000",
        "factor_10000",
        "factor_20000",
        "retcode",
        "stop_reason",
        "elapsed_s",
    ]
end

function csv_row(record)
    summary = record["summary"]
    factors = summary.budget_factors
    return [
        record["system_id"],
        record["dim"],
        record["variant_condition"],
        record["structure"],
        record["n_params"],
        summary.total_evals,
        summary.first_best_index,
        @sprintf("%.6f", summary.first_best_fraction),
        record["final_loss"],
        summary.best_finite_loss,
        factors["500"],
        factors["1000"],
        factors["2000"],
        factors["5000"],
        factors["10000"],
        factors["20000"],
        record["fit_meta"].retcode,
        record["fit_meta"].stop_reason,
        @sprintf("%.6f", record["elapsed_s"]),
    ]
end

function prepare_outputs(; append::Bool = false)
    mkpath(OUTPUT_DIR)
    if !append
        open(JSONL_PATH, "w") do _ end
        open(SUMMARY_CSV_PATH, "w") do io
            println(io, join(csv_header(), ","))
        end
    elseif !isfile(JSONL_PATH) || !isfile(SUMMARY_CSV_PATH)
        prepare_outputs(append = false)
    end
end

function append_record!(record)
    open(JSONL_PATH, "a") do io
        JSON3.write(io, json_safe(record))
        write(io, '\n')
        flush(io)
    end
    open(SUMMARY_CSV_PATH, "a") do io
        println(io, join(csv_escape.(csv_row(record)), ","))
        flush(io)
    end
end

function print_compact_summary(records)
    println("regression_fingerprint=$(config_fingerprint())")
    println("phase_b_fingerprint=$(phase_b_fingerprint())")
    println("jsonl=$(JSONL_PATH)")
    println("csv=$(SUMMARY_CSV_PATH)")
    max_first_best = maximum(Int(record["summary"].first_best_index) for record in records)
    println("max_first_best_index=$(max_first_best)")
    for record in records
        summary = record["summary"]
        @printf(
            "sys=%d dim=%d condition=%s structure=%s n_params=%d evals=%d first_best=%d fraction=%.6f final_loss=%.6e retcode=%s\n",
            record["system_id"],
            record["dim"],
            record["variant_condition"],
            record["structure"],
            record["n_params"],
            summary.total_evals,
            summary.first_best_index,
            summary.first_best_fraction,
            record["final_loss"],
            record["fit_meta"].retcode,
        )
    end
end

function main(args = ARGS)
    system_ids = selected_systems(args)
    structure_labels = selected_structure_labels(args)
    use_pretuning_values = selected_conditions(args)
    append = append_requested(args)
    records = Dict{String, Any}[]
    prepare_outputs(append = append)
    println("regression_fingerprint=$(config_fingerprint())")
    println("phase_b_fingerprint=$(phase_b_fingerprint())")
    println("jsonl=$(JSONL_PATH)")
    println("csv=$(SUMMARY_CSV_PATH)")
    for system_id in system_ids
        cases = [case for case in structure_cases(system_id) if replace(case.label, r"_.*" => "") in structure_labels || case.label in structure_labels]
        isempty(cases) && error("No selected structures for system $(system_id)")
        for structure_case in cases
            for use_pretuning in use_pretuning_values
                record = run_fit(system_id, structure_case, use_pretuning)
                push!(records, record)
                append_record!(record)
                summary = record["summary"]
                @printf(
                    "sys=%d dim=%d condition=%s structure=%s n_params=%d evals=%d first_best=%d fraction=%.6f final_loss=%.6e retcode=%s\n",
                    record["system_id"],
                    record["dim"],
                    record["variant_condition"],
                    record["structure"],
                    record["n_params"],
                    summary.total_evals,
                    summary.first_best_index,
                    summary.first_best_fraction,
                    record["final_loss"],
                    record["fit_meta"].retcode,
                )
            end
        end
    end
    !isempty(records) && println("max_first_best_index=$(maximum(Int(record["summary"].first_best_index) for record in records))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
