import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf

include(joinpath(@__DIR__, "..", "..", "src", "EvoODE.jl"))
using .EvoODE
include(joinpath(@__DIR__, "..", "regression", "diagnostic_systems.jl"))

const SCRIPT_SLUG = "compare_screening_variant"
const OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "debug", SCRIPT_SLUG)
const SEED = 42
const SYSTEM_IDS = (3, 11)

# Matches studies/regression/run_regression.jl without importing it, because that
# script executes main() on include.
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
const DERIVATIVE_SCREEN_K = POP_SIZE
const DERIVATIVE_POLISH_MAXITERS = 20
const DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES = 2

const BASELINE_V0 = Dict(
    3 => (loss = 2.663641831768419e-10, final_stage = 3),
    11 => (loss = 4.402192340718147e-15, final_stage = 4),
)

function build_options(seed::Int)
    return DiscoveryOptions(
        rng_seed = seed,
        verbose = 0,
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

function build_trajectory(system)
    tspan = system[:tspan]
    t_grid = collect(range(tspan[1], tspan[2]; length = Int(system[:T])))
    u0 = Float64[x for x in system[:u0]]
    prob = ODEProblem(rhs_for_system(Int(system[:system_id])), copy(u0), tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function system_by_id(system_id::Int)
    return only([system for system in REGRESSION_SYSTEMS if Int(system[:system_id]) == system_id])
end

function build_strategy(label::String)
    progression = StageProgressionPolicy(:stage_local, STAGE_MIN)
    usage = StageUsagePolicy(:hard, SOFT_BIAS)
    if label == "evogrow_v2_2_stage_local"
        return EvoGrow(
            POP_SIZE,
            N_LEVELS,
            CHILDREN_PER_PARENT,
            MAX_TERMS,
            LAMBDA,
            progression,
            usage,
            USE_PRETUNING,
            nothing,
            nothing,
        )
    elseif label == "evogrow_screening_derivative"
        return EvoGrowScreening(
            POP_SIZE,
            N_LEVELS,
            CHILDREN_PER_PARENT,
            MAX_TERMS,
            LAMBDA,
            progression,
            usage,
            DERIVATIVE_SCREEN_K,
            DERIVATIVE_POLISH_MAXITERS,
            DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES,
            nothing,
            nothing,
        )
    end
    error("Unsupported variant label: $(label)")
end

function get_meta(meta, key::Symbol, default = nothing)
    return haskey(meta, key) ? getfield(meta, key) : default
end

function pruned_support(structure::StructureSpec, params::Vector{Float64})
    support = Vector{Vector{Int}}()
    offset = 0
    for got_idxs in structure.active_idxs
        n_terms = length(got_idxs)
        eq_params = params[(offset + 1):(offset + n_terms)]
        offset += n_terms
        max_abs = isempty(eq_params) ? 0.0 : maximum(abs, eq_params)
        threshold = max(1e-6, 1e-3 * max_abs)
        push!(support, sort([got_idxs[i] for i in 1:n_terms if abs(eq_params[i]) >= threshold]))
    end
    return support
end

function run_cell(label::String, system_id::Int, seed::Int)
    system = system_by_id(system_id)
    traj = build_trajectory(system)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    result = nothing
    elapsed_s = @elapsed begin
        result = discover(
            traj;
            structure = build_strategy(label),
            optimizer = build_reference_optimizer(),
            basis = basis,
            loss = MSELoss(),
            options = build_options(seed),
        )
    end

    meta = result.meta.structure
    expected_idxs = expected_active_idxs(system_id, basis)
    baseline = label == "evogrow_v2_2_stage_local" ? BASELINE_V0[system_id] : nothing

    return Dict{String, Any}(
        "variant" => label,
        "system_id" => system_id,
        "system_name" => String(system[:system_name]),
        "seed" => seed,
        "elapsed_s" => elapsed_s,
        "loss" => result.loss,
        "final_stage" => Int(get_meta(meta, :final_stage)),
        "pruned_match" => support_match_pruned(result.structure, result.params, expected_idxs),
        "pruned_support" => pruned_support(result.structure, result.params),
        "structure" => replace(structure_to_string(result.structure, basis, result.params), '\n' => " | "),
        "total_parameter_fits" => get_meta(meta, :total_parameter_fits),
        "total_ode_solves" => get_meta(meta, :total_ode_solves),
        "total_simulation_time_s" => get_meta(meta, :total_simulation_time_s),
        "screening_evals" => get_meta(meta, :screening_evals),
        "invalid_screening_evals" => get_meta(meta, :invalid_screening_evals),
        "polished_candidates" => get_meta(meta, :polished_candidates),
        "polish_budget_exhausted" => get_meta(meta, :polish_budget_exhausted),
        "polish_convergence_failures" => get_meta(meta, :polish_convergence_failures),
        "rank_agreement_spearman" => get_meta(meta, :rank_agreement_spearman),
        "rejected_diagnostic_candidates" => get_meta(meta, :rejected_diagnostic_candidates),
        "rejected_beats_best_selected" => get_meta(meta, :rejected_beats_best_selected),
        "screening_time_s" => get_meta(meta, :screening_time_s),
        "polish_time_s" => get_meta(meta, :polish_time_s),
        "rejected_diagnostic_time_s" => get_meta(meta, :rejected_diagnostic_time_s),
        "final_refit_time_s" => get_meta(meta, :final_refit_time_s),
        "baseline_v0_loss" => baseline === nothing ? nothing : baseline.loss,
        "baseline_v0_final_stage" => baseline === nothing ? nothing : baseline.final_stage,
        "baseline_v0_loss_equal" => baseline === nothing ? nothing : result.loss == baseline.loss,
        "baseline_v0_final_stage_equal" => baseline === nothing ? nothing : Int(get_meta(meta, :final_stage)) == baseline.final_stage,
    )
end

function system_comparison(system_id::Int, reference, screening)
    return Dict{String, Any}(
        "system_id" => system_id,
        "runtime_ratio_reference_to_screening" => reference["elapsed_s"] / screening["elapsed_s"],
        "same_pruned_support" => reference["pruned_support"] == screening["pruned_support"],
        "reference_variant" => reference["variant"],
        "screening_variant" => screening["variant"],
    )
end

function write_json(path::String, value)
    open(path, "w") do io
        JSON3.pretty(io, value)
        write(io, '\n')
    end
end

function csv_value(value)
    value === nothing && return ""
    text = string(value)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::String, records)
    columns = [
        "variant", "system_id", "system_name", "seed", "elapsed_s", "loss", "final_stage",
        "pruned_match", "total_parameter_fits", "total_ode_solves", "total_simulation_time_s",
        "screening_evals", "invalid_screening_evals", "polished_candidates",
        "polish_budget_exhausted", "polish_convergence_failures", "rank_agreement_spearman",
        "rejected_diagnostic_candidates", "rejected_beats_best_selected", "screening_time_s",
        "polish_time_s", "rejected_diagnostic_time_s", "final_refit_time_s",
        "baseline_v0_loss_equal", "baseline_v0_final_stage_equal",
    ]
    open(path, "w") do io
        println(io, join(columns, ","))
        for record in records
            println(io, join([csv_value(get(record, column, nothing)) for column in columns], ","))
        end
    end
end

function print_record(record)
    @printf(
        "%s system=%d seed=%d elapsed=%.3fs loss=%.16e stage=%d pruned=%s fits=%s solves=%s sim_time=%s\n",
        record["variant"],
        record["system_id"],
        record["seed"],
        record["elapsed_s"],
        record["loss"],
        record["final_stage"],
        string(record["pruned_match"]),
        string(record["total_parameter_fits"]),
        string(record["total_ode_solves"]),
        string(record["total_simulation_time_s"]),
    )
    if record["variant"] == "evogrow_screening_derivative"
        @printf(
            "  screening_evals=%s invalid=%s polished=%s exhausted=%s failures=%s rho=%s rejected_diag=%s rejected_beats=%s screen_time=%s polish_time=%s rejected_time=%s final_refit=%s\n",
            string(record["screening_evals"]),
            string(record["invalid_screening_evals"]),
            string(record["polished_candidates"]),
            string(record["polish_budget_exhausted"]),
            string(record["polish_convergence_failures"]),
            string(record["rank_agreement_spearman"]),
            string(record["rejected_diagnostic_candidates"]),
            string(record["rejected_beats_best_selected"]),
            string(record["screening_time_s"]),
            string(record["polish_time_s"]),
            string(record["rejected_diagnostic_time_s"]),
            string(record["final_refit_time_s"]),
        )
    end
end

function main()
    mkpath(OUTPUT_DIR)
    variants = ("evogrow_v2_2_stage_local", "evogrow_screening_derivative")
    records = Dict{String, Any}[]
    comparisons = Dict{String, Any}[]

    println("Writing outputs to $(OUTPUT_DIR)")
    for system_id in SYSTEM_IDS
        system_records = Dict{String, Any}()
        for variant in variants
            println("Running $(variant), system $(system_id), seed $(SEED)")
            record = run_cell(variant, system_id, SEED)
            push!(records, record)
            system_records[variant] = record
            print_record(record)
        end
        comparison = system_comparison(
            system_id,
            system_records["evogrow_v2_2_stage_local"],
            system_records["evogrow_screening_derivative"],
        )
        push!(comparisons, comparison)
        @printf(
            "COMPARISON system=%d runtime_ratio_reference_to_screening=%.6f same_pruned_support=%s\n",
            system_id,
            comparison["runtime_ratio_reference_to_screening"],
            string(comparison["same_pruned_support"]),
        )
    end

    summary = Dict{String, Any}(
        "script" => SCRIPT_SLUG,
        "timestamp" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "seed" => SEED,
        "systems" => collect(SYSTEM_IDS),
        "records" => records,
        "comparisons" => comparisons,
        "notes" => [
            "Hyperparameters and DiscoveryOptions match studies/regression/run_regression.jl.",
            "Only systems 3 and 11 are run.",
            "No records are written to studies/regression/history.jsonl.",
        ],
    )

    write_json(joinpath(OUTPUT_DIR, "summary.json"), summary)
    write_csv(joinpath(OUTPUT_DIR, "records.csv"), records)
    write_json(joinpath(OUTPUT_DIR, "comparisons.json"), comparisons)
    println("Wrote summary.json, records.csv, comparisons.json")
end

main()
