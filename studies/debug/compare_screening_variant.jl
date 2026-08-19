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
include(joinpath(@__DIR__, "..", "output_path_guard.jl"))
const OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "debug", SCRIPT_SLUG), ARGS)
const SEED = 42
const SYSTEM_IDS = (3, 11)
const MAIN_EVAL_TOL = 1e-8
const ANCHOR_EVAL_TOL = 1e-6

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

function build_reference_optimizer(eval_tol::Float64)
    return BFGSOptimizer(
        maxiters = BFGS_MAXITERS,
        abstol = eval_tol,
        reltol = eval_tol,
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
    if label in ("A_reference", "anchor_reference_1e-6")
        return EvoGrow(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = progression,
            usage = usage,
            use_pretuning = USE_PRETUNING,
            screening_optimizer = nothing,
            level_callback = nothing,
        )
    elseif label == "B_screening_residual_ls"
        return EvoGrowScreening(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = progression,
            usage = usage,
            screen_k = DERIVATIVE_SCREEN_K,
            polish_maxiters = DERIVATIVE_POLISH_MAXITERS,
            rejected_diagnostic_samples = DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES,
            screening_optimizer = nothing,
            level_callback = nothing,
            screening_score = :residual,
            polish_start = :ls,
        )
    elseif label == "C_screening_nested_ls"
        return EvoGrowScreening(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = progression,
            usage = usage,
            screen_k = DERIVATIVE_SCREEN_K,
            polish_maxiters = DERIVATIVE_POLISH_MAXITERS,
            rejected_diagnostic_samples = DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES,
            screening_optimizer = nothing,
            level_callback = nothing,
            screening_score = :nested_f,
            polish_start = :ls,
        )
    elseif label == "D_screening_nested_reference_start"
        return EvoGrowScreening(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = progression,
            usage = usage,
            screen_k = DERIVATIVE_SCREEN_K,
            polish_maxiters = DERIVATIVE_POLISH_MAXITERS,
            rejected_diagnostic_samples = DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES,
            screening_optimizer = nothing,
            level_callback = nothing,
            screening_score = :nested_f,
            polish_start = :reference,
        )
    end
    error("Unsupported variant label: $(label)")
end

function get_meta(meta, key::Symbol, default = nothing)
    return haskey(meta, key) ? getfield(meta, key) : default
end

function simulation_ms_per_solve(meta)
    solves = get_meta(meta, :total_ode_solves)
    sim_time = get_meta(meta, :total_simulation_time_s)
    if solves === nothing || sim_time === nothing || solves == 0
        return nothing
    end
    return 1000.0 * sim_time / solves
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

function run_cell(label::String, system_id::Int, seed::Int, eval_tol::Float64)
    system = system_by_id(system_id)
    traj = build_trajectory(system)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    result = nothing
    elapsed_s = @elapsed begin
        result = discover(
            traj;
            structure = build_strategy(label),
            optimizer = build_reference_optimizer(eval_tol),
            basis = basis,
            loss = MSELoss(),
            options = build_options(seed),
        )
    end

    meta = result.meta.structure
    final_refit_meta = get_meta(meta, :final_refit_meta, (;))
    expected_idxs = expected_active_idxs(system_id, basis)
    baseline = label == "anchor_reference_1e-6" ? BASELINE_V0[system_id] : nothing

    return Dict{String, Any}(
        "variant" => label,
        "eval_tol" => eval_tol,
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
        "simulation_ms_per_ode_solve" => simulation_ms_per_solve(meta),
        "screening_score_mode" => get_meta(meta, :screening_score_mode),
        "polish_start" => get_meta(meta, :polish_start),
        "nested_test_alpha" => get_meta(meta, :nested_test_alpha),
        "nested_gate_children" => get_meta(meta, :nested_gate_children),
        "nested_gate_failed_children" => get_meta(meta, :nested_gate_failed_children),
        "selection_diff_from_residual" => get_meta(meta, :selection_diff_from_residual),
        "levels_with_selection_diff_from_residual" => get_meta(meta, :levels_with_selection_diff_from_residual),
        "screening_evals" => get_meta(meta, :screening_evals),
        "invalid_screening_evals" => get_meta(meta, :invalid_screening_evals),
        "polished_candidates" => get_meta(meta, :polished_candidates),
        "polish_budget_exhausted" => get_meta(meta, :polish_budget_exhausted),
        "polish_convergence_failures" => get_meta(meta, :polish_convergence_failures),
        "rank_agreement_spearman" => get_meta(meta, :rank_agreement_spearman),
        "rank_agreement_spearman_median" => get_meta(meta, :rank_agreement_spearman_median),
        "rank_agreement_spearman_min" => get_meta(meta, :rank_agreement_spearman_min),
        "rank_agreement_spearman_max" => get_meta(meta, :rank_agreement_spearman_max),
        "rank_agreement_finite_levels" => get_meta(meta, :rank_agreement_finite_levels),
        "rank_agreement_total_levels" => get_meta(meta, :rank_agreement_total_levels),
        "rejected_diagnostic_candidates" => get_meta(meta, :rejected_diagnostic_candidates),
        "rejected_beats_best_selected" => get_meta(meta, :rejected_beats_best_selected),
        "screening_time_s" => get_meta(meta, :screening_time_s),
        "polish_time_s" => get_meta(meta, :polish_time_s),
        "rejected_diagnostic_time_s" => get_meta(meta, :rejected_diagnostic_time_s),
        "final_refit_time_s" => get_meta(meta, :final_refit_time_s),
        "final_refit_method" => get_meta(final_refit_meta, :method),
        "final_refit_retcode" => get_meta(final_refit_meta, :retcode),
        "final_refit_loss_evals" => get_meta(final_refit_meta, :loss_evals),
        "final_refit_invalid_evals" => get_meta(final_refit_meta, :invalid_evals),
        "final_refit_optimizer_retcodes" => get_meta(final_refit_meta, :optimizer_retcodes),
        "final_refit_optimizer_failure_hits" => get_meta(final_refit_meta, :optimizer_failure_hits),
        "final_refit_optimizer_iteration_limit_hits" => get_meta(final_refit_meta, :optimizer_iteration_limit_hits),
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
        "variant", "eval_tol", "system_id", "system_name", "seed", "elapsed_s", "loss", "final_stage",
        "pruned_match", "total_parameter_fits", "total_ode_solves", "total_simulation_time_s",
        "simulation_ms_per_ode_solve", "screening_score_mode", "screening_evals",
        "polish_start", "nested_test_alpha", "nested_gate_children", "nested_gate_failed_children",
        "selection_diff_from_residual", "levels_with_selection_diff_from_residual",
        "invalid_screening_evals", "polished_candidates",
        "polish_budget_exhausted", "polish_convergence_failures", "rank_agreement_spearman",
        "rank_agreement_spearman_median", "rank_agreement_spearman_min",
        "rank_agreement_spearman_max", "rank_agreement_finite_levels",
        "rank_agreement_total_levels",
        "rejected_diagnostic_candidates", "rejected_beats_best_selected", "screening_time_s",
        "polish_time_s", "rejected_diagnostic_time_s", "final_refit_time_s",
        "final_refit_method", "final_refit_retcode", "final_refit_loss_evals",
        "final_refit_invalid_evals", "final_refit_optimizer_retcodes",
        "final_refit_optimizer_failure_hits", "final_refit_optimizer_iteration_limit_hits",
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
        "%s tol=%.0e system=%d seed=%d elapsed=%.3fs loss=%.16e stage=%d pruned=%s fits=%s solves=%s sim_time=%s ms_per_solve=%s\n",
        record["variant"],
        record["eval_tol"],
        record["system_id"],
        record["seed"],
        record["elapsed_s"],
        record["loss"],
        record["final_stage"],
        string(record["pruned_match"]),
        string(record["total_parameter_fits"]),
        string(record["total_ode_solves"]),
        string(record["total_simulation_time_s"]),
        string(record["simulation_ms_per_ode_solve"]),
    )
    if startswith(record["variant"], "B_") || startswith(record["variant"], "C_") || startswith(record["variant"], "D_")
        @printf(
            "  score=%s polish_start=%s gate_failed=%s/%s selection_diff=%s levels_diff=%s rho_mean=%s rho_median=%s rho_range=[%s,%s] rho_levels=%s/%s rejected_diag=%s rejected_beats=%s exhausted=%s failures=%s screen_time=%s polish_time=%s rejected_time=%s final_refit=%s final_refit_method=%s final_refit_retcode=%s final_refit_loss_evals=%s final_refit_optimizer_retcodes=%s\n",
            string(record["screening_score_mode"]),
            string(record["polish_start"]),
            string(record["nested_gate_failed_children"]),
            string(record["nested_gate_children"]),
            string(record["selection_diff_from_residual"]),
            string(record["levels_with_selection_diff_from_residual"]),
            string(record["rank_agreement_spearman"]),
            string(record["rank_agreement_spearman_median"]),
            string(record["rank_agreement_spearman_min"]),
            string(record["rank_agreement_spearman_max"]),
            string(record["rank_agreement_finite_levels"]),
            string(record["rank_agreement_total_levels"]),
            string(record["rejected_diagnostic_candidates"]),
            string(record["rejected_beats_best_selected"]),
            string(record["polish_budget_exhausted"]),
            string(record["polish_convergence_failures"]),
            string(record["screening_time_s"]),
            string(record["polish_time_s"]),
            string(record["rejected_diagnostic_time_s"]),
            string(record["final_refit_time_s"]),
            string(record["final_refit_method"]),
            string(record["final_refit_retcode"]),
            string(record["final_refit_loss_evals"]),
            string(record["final_refit_optimizer_retcodes"]),
        )
    end
end

function main()
    mkpath(OUTPUT_DIR)
    variants = (
        "A_reference",
        "B_screening_residual_ls",
        "C_screening_nested_ls",
        "D_screening_nested_reference_start",
    )
    records = Dict{String, Any}[]
    anchor_records = Dict{String, Any}[]
    comparisons = Dict{String, Any}[]

    println("Writing outputs to $(OUTPUT_DIR)")
    for system_id in SYSTEM_IDS
        println("Running anchor_reference_1e-6, system $(system_id), seed $(SEED)")
        anchor = run_cell("anchor_reference_1e-6", system_id, SEED, ANCHOR_EVAL_TOL)
        push!(anchor_records, anchor)
        print_record(anchor)

        system_records = Dict{String, Any}()
        for variant in variants
            println("Running $(variant), system $(system_id), seed $(SEED)")
            record = run_cell(variant, system_id, SEED, MAIN_EVAL_TOL)
            push!(records, record)
            system_records[variant] = record
            print_record(record)
        end
        reference = system_records["A_reference"]
        for variant in variants[2:end]
            comparison = system_comparison(system_id, reference, system_records[variant])
            push!(comparisons, comparison)
            @printf(
                "COMPARISON system=%d screening=%s runtime_ratio_reference_to_screening=%.6f same_pruned_support=%s\n",
                system_id,
                variant,
                comparison["runtime_ratio_reference_to_screening"],
                string(comparison["same_pruned_support"]),
            )
        end
    end

    summary = Dict{String, Any}(
        "script" => SCRIPT_SLUG,
        "timestamp" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "seed" => SEED,
        "systems" => collect(SYSTEM_IDS),
        "main_eval_tol" => MAIN_EVAL_TOL,
        "anchor_eval_tol" => ANCHOR_EVAL_TOL,
        "records" => records,
        "anchor_records" => anchor_records,
        "comparisons" => comparisons,
        "notes" => [
            "Hyperparameters and DiscoveryOptions match studies/regression/run_regression.jl except main evaluation tolerance is 1e-8 for WP-P2.4.",
            "anchor_reference_1e-6 checks the unchanged reference path against Baseline v0.",
            "Only systems 3 and 11 are run.",
            "No records are written to studies/regression/history.jsonl.",
        ],
    )

    write_json(joinpath(OUTPUT_DIR, "summary.json"), summary)
    write_csv(joinpath(OUTPUT_DIR, "records.csv"), records)
    write_csv(joinpath(OUTPUT_DIR, "anchor_records.csv"), anchor_records)
    write_json(joinpath(OUTPUT_DIR, "comparisons.json"), comparisons)
    println("Wrote summary.json, records.csv, anchor_records.csv, comparisons.json")
end

main()
