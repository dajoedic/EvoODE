# studies/numerics/system26_tolerance_screening.jl
#
# WP-T2 - Evaluation tolerance and derivative screening on System 26 (Lotka-Volterra, 2D),
# the system on which Gate 1 failed.
#
# Three conditions, System 26, seed 42, 30 levels:
#   D8  EvoGrowScreening, screening_score = :nested_f, polish_start = :reference, eval tol 1e-8
#   R8  reference path (EvoGrow v2.2 stage_local, use_pretuning = false),      eval tol 1e-8
#   R6  reference path, identical,                                            eval tol 1e-6
#
# Conditions run in order of increasing expected runtime (D8, R8, R6) and every condition is
# written and flushed to disk immediately after it finishes, so an abort costs at most the
# condition currently running.
#
# The run is watched externally over several hours, so every level prints one compact live line
# to the terminal and to `run.log` in the output directory. That output is purely additive: the
# level callback only reads the level snapshot, never touches the RNG or search state, and
# `verbose` stays at 0, so results are bit-identical to a run without it.
#
# Prediction under test (WP-T2): on System 26 the loss floor is ~1.4e-3, three orders of
# magnitude above even the 1e-6 tolerance, so `loss_tol = 1e-8` can never fire and the stage
# escalation is driven by plateau detection, not by the loss threshold. Predicted: the tighter
# tolerance does not change `final_stage` / `stage_overshoot` on System 26.
#
# Anchor: R6 must reproduce Baseline v0 (config_fingerprint 0c739d4e36ee6498):
#   loss = 0.001391623174905009, final_stage = 5, stage_overshoot = 2, wasted_levels = 8,
#   pruned_match = false. A deviation means the setup is wrong; it is reported, never smoothed.
#
# Rough cost expectation of the external run: D8 below one hour, R8 open (part of the
# measurement), R6 about 3 hours. Total plausibly 5-8 hours.
#
# Execution (target configuration is the default; no environment variables needed):
#   julia studies/numerics/system26_tolerance_screening.jl
#
# Cheap smoke test only (never for results):
#   EVO_T2_SYSTEM_ID=3 EVO_T2_N_LEVELS=4 julia studies/numerics/system26_tolerance_screening.jl
#
# Nothing is written to studies/regression/history.jsonl. src/ and the regression configuration
# are untouched.

import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf

include(joinpath(@__DIR__, "..", "..", "src", "EvoODE.jl"))
using .EvoODE
include(joinpath(@__DIR__, "..", "regression", "diagnostic_systems.jl"))
include(joinpath(@__DIR__, "..", "output_path_guard.jl"))

const SCRIPT_SLUG = "system26_tolerance_screening"
const OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "numerics", SCRIPT_SLUG), ARGS)

# Target configuration. The environment variables exist only for the cheap smoke test
# described in the header; unset, this script runs the WP-T2 target configuration.
const SYSTEM_ID = parse(Int, get(ENV, "EVO_T2_SYSTEM_ID", "26"))
const N_LEVELS = parse(Int, get(ENV, "EVO_T2_N_LEVELS", "30"))
const SEED = 42

# Hyperparameters mirror studies/regression/run_regression.jl. That script is not included
# because it executes main() on include.
const POP_SIZE = 10
const CHILDREN_PER_PARENT = 2
const MAX_TERMS = 6
const LAMBDA = 1e-3
const STAGE_MIN = 2
const SOFT_BIAS = 0.75
const USE_PRETUNING = false
const BFGS_MAXITERS = 200
const BFGS_MAXITERS_SOLVE = 10^6
const BFGS_TIME_LIMIT_S = 86_400.0
const DERIVATIVE_SCREEN_K = POP_SIZE
const DERIVATIVE_POLISH_MAXITERS = 20
const DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES = 2

const TOL_LOOSE = 1e-6
const TOL_TIGHT = 1e-8

# Baseline v0, seed 42, 30 levels, evaluation tolerance 1e-6, variant evogrow_v2_2_stage_local
# (studies/regression/history.jsonl, config_fingerprint 0c739d4e36ee6498).
const BASELINE_V0 = Dict(
    3 => (loss = 2.663641831768419e-10, final_stage = 3, stage_overshoot = 1, wasted_levels = 2, pruned_match = true),
    11 => (loss = 4.402192340718147e-15, final_stage = 4, stage_overshoot = 0, wasted_levels = 0, pruned_match = true),
    26 => (loss = 0.001391623174905009, final_stage = 5, stage_overshoot = 2, wasted_levels = 8, pruned_match = false),
)
const BASELINE_V0_FINGERPRINT = "0c739d4e36ee6498"
const BASELINE_V0_N_LEVELS = 30
const BASELINE_V0_SEED = 42

# Ordered by increasing expected runtime: cheapest condition first.
const CONDITIONS = (
    (label = "D8", kind = :screening, eval_tol = TOL_TIGHT,
     description = "screening nested_f / polish_start=reference, evaluation tolerance 1e-8"),
    (label = "R8", kind = :reference, eval_tol = TOL_TIGHT,
     description = "reference path v2.2 stage_local, evaluation tolerance 1e-8"),
    (label = "R6", kind = :reference, eval_tol = TOL_LOOSE,
     description = "reference path v2.2 stage_local, evaluation tolerance 1e-6 (Baseline v0 anchor)"),
)

const ANCHOR_LABEL = "R6"

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

function build_optimizer(eval_tol::Float64)
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

"""
One compact live line per level, so a multi-hour condition is distinguishable from a hang.

The callback only reads the level snapshot and prints; it never touches the RNG or any search
state, which is what keeps results bit-identical to a run without it. `EvoGrow` passes a
`vis_history` snapshot without per-level timing, `EvoGrowScreening` passes its `level_log`
entry which carries `elapsed_s`; the wall time between callbacks covers the first case.
"""
function make_level_callback(label::String)
    last_tick = Ref(time())
    return snapshot -> begin
        now_t = time()
        level_elapsed_s = hasproperty(snapshot, :elapsed_s) ?
            Float64(snapshot.elapsed_s) : now_t - last_tick[]
        last_tick[] = now_t
        n_params = hasproperty(snapshot, :n_params) ?
            Int(snapshot.n_params) : length(snapshot.best_params)
        log_info(@sprintf(
            "[%s] level %d/%d stage=%d best_loss=%.6e n_params=%d level_elapsed=%.1fs",
            label, Int(snapshot.level), N_LEVELS, Int(snapshot.stage),
            Float64(snapshot.best_loss), n_params, level_elapsed_s,
        ))
        flush(stdout)
    end
end

function build_strategy(kind::Symbol, level_callback)
    progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN)
    usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS)
    if kind === :reference
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
            level_callback = level_callback,
        )
    elseif kind === :screening
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
            level_callback = level_callback,
            screening_score = :nested_f,
            polish_start = :reference,
        )
    end
    error("Unsupported condition kind: $(kind)")
end

function system_by_id(system_id::Int)
    return only([system for system in REGRESSION_SYSTEMS if Int(system[:system_id]) == system_id])
end

function build_trajectory(system)
    tspan = system[:tspan]
    t_grid = collect(range(tspan[1], tspan[2]; length = Int(system[:T])))
    u0 = Float64[x for x in system[:u0]]
    prob = ODEProblem(rhs_for_system(Int(system[:system_id])), copy(u0), tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function get_meta(meta, key::Symbol, default = nothing)
    return haskey(meta, key) ? getfield(meta, key) : default
end

function ms_per_ode_solve(solves, sim_time_s)
    (solves === nothing || sim_time_s === nothing || solves == 0) && return nothing
    return 1000.0 * sim_time_s / solves
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

"""
Per-stage cost breakdown in the same cut as the WP-T2 baseline table recorded in DIARY.md:
levels, time, share of total time, seconds per level - plus integrations and
cost per integration, so a tolerance-driven shift of the cost profile is readable.
"""
function stage_cost_rows(label::String, eval_tol::Float64, level_log)
    level_log === nothing && return Dict{String, Any}[]
    stages = sort(unique(Int(entry.stage) for entry in level_log))
    total_time = sum(Float64(entry.elapsed_s) for entry in level_log; init = 0.0)
    rows = Dict{String, Any}[]
    for stage in stages
        entries = [entry for entry in level_log if Int(entry.stage) == stage]
        n_levels = length(entries)
        time_s = sum(Float64(entry.elapsed_s) for entry in entries; init = 0.0)
        solves = sum(Int(entry.ode_solves) for entry in entries; init = 0)
        fits = sum(Int(entry.parameter_fits) for entry in entries; init = 0)
        sim_time_s = sum(Float64(entry.simulation_time_s) for entry in entries; init = 0.0)
        push!(rows, Dict{String, Any}(
            "condition" => label,
            "eval_tol" => eval_tol,
            "stage" => stage,
            "levels" => n_levels,
            "time_s" => time_s,
            "time_h" => time_s / 3600.0,
            "time_share" => total_time == 0.0 ? nothing : time_s / total_time,
            "s_per_level" => n_levels == 0 ? nothing : time_s / n_levels,
            "parameter_fits" => fits,
            "ode_solves" => solves,
            "simulation_time_s" => sim_time_s,
            "ms_per_ode_solve" => ms_per_ode_solve(solves, sim_time_s),
        ))
    end
    return rows
end

function level_cost_rows(label::String, eval_tol::Float64, level_log)
    level_log === nothing && return Dict{String, Any}[]
    return [
        Dict{String, Any}(
            "condition" => label,
            "eval_tol" => eval_tol,
            "level" => Int(entry.level),
            "stage" => Int(entry.stage),
            "best_loss" => Float64(entry.best_loss),
            "best_objective" => Float64(entry.best_objective),
            "n_params" => Int(entry.n_params),
            "elapsed_s" => Float64(entry.elapsed_s),
            "parameter_fits" => Int(entry.parameter_fits),
            "ode_solves" => Int(entry.ode_solves),
            "invalid_solves" => Int(entry.invalid_solves),
            "simulation_time_s" => Float64(entry.simulation_time_s),
            "parameter_optimization_time_s" => Float64(entry.parameter_optimization_time_s),
        )
        for entry in level_log
    ]
end

function anchor_check(label::String, record)
    baseline = get(BASELINE_V0, SYSTEM_ID, nothing)
    config_matches = SYSTEM_ID in keys(BASELINE_V0) &&
                     N_LEVELS == BASELINE_V0_N_LEVELS &&
                     SEED == BASELINE_V0_SEED &&
                     record["eval_tol"] == TOL_LOOSE
    check = Dict{String, Any}(
        "condition" => label,
        "system_id" => SYSTEM_ID,
        "seed" => SEED,
        "n_levels" => N_LEVELS,
        "eval_tol" => record["eval_tol"],
        "baseline_v0_fingerprint" => BASELINE_V0_FINGERPRINT,
        "baseline_available" => baseline !== nothing,
        "config_matches_baseline_v0" => config_matches,
        "measured_loss" => record["loss"],
        "measured_final_stage" => record["final_stage"],
        "measured_stage_overshoot" => record["stage_overshoot"],
        "measured_wasted_levels" => record["wasted_levels"],
        "measured_pruned_match" => record["pruned_match"],
        "baseline_loss" => baseline === nothing ? nothing : baseline.loss,
        "baseline_final_stage" => baseline === nothing ? nothing : baseline.final_stage,
        "baseline_stage_overshoot" => baseline === nothing ? nothing : baseline.stage_overshoot,
        "baseline_wasted_levels" => baseline === nothing ? nothing : baseline.wasted_levels,
        "baseline_pruned_match" => baseline === nothing ? nothing : baseline.pruned_match,
    )
    if baseline === nothing
        check["loss_equal"] = nothing
        check["final_stage_equal"] = nothing
        check["stage_overshoot_equal"] = nothing
        check["wasted_levels_equal"] = nothing
        check["pruned_match_equal"] = nothing
        check["anchor_reproduced"] = nothing
        check["note"] = "No Baseline v0 record for this system; anchor not evaluated."
        return check
    end
    check["loss_equal"] = record["loss"] == baseline.loss
    check["final_stage_equal"] = record["final_stage"] == baseline.final_stage
    check["stage_overshoot_equal"] = record["stage_overshoot"] == baseline.stage_overshoot
    check["wasted_levels_equal"] = record["wasted_levels"] == baseline.wasted_levels
    check["pruned_match_equal"] = record["pruned_match"] == baseline.pruned_match
    check["anchor_reproduced"] = check["loss_equal"] && check["final_stage_equal"] &&
                                check["stage_overshoot_equal"] && check["wasted_levels_equal"] &&
                                check["pruned_match_equal"]
    check["note"] = config_matches ?
        "Anchor evaluated under the Baseline v0 configuration." :
        "Configuration deviates from Baseline v0 (system/levels/seed/tolerance); comparison is informational only."
    return check
end

function run_condition(condition)
    system = system_by_id(SYSTEM_ID)
    expected_stage = Int(system[:expected_stage])
    traj = build_trajectory(system)
    basis = default_staged_polynomial_basis(Int(system[:dim]))

    record = Dict{String, Any}(
        "condition" => condition.label,
        "description" => condition.description,
        "kind" => String(condition.kind),
        "eval_tol" => condition.eval_tol,
        "system_id" => SYSTEM_ID,
        "system_name" => String(system[:system_name]),
        "dim" => Int(system[:dim]),
        "seed" => SEED,
        "n_levels" => N_LEVELS,
        "expected_stage" => expected_stage,
        "started_at" => iso_timestamp(),
        "error" => nothing,
    )
    stage_rows = Dict{String, Any}[]
    level_rows = Dict{String, Any}[]

    try
        result = nothing
        elapsed_s = @elapsed begin
            result = discover(
                traj;
                structure = build_strategy(condition.kind, make_level_callback(condition.label)),
                optimizer = build_optimizer(condition.eval_tol),
                basis = basis,
                loss = MSELoss(),
                options = build_options(SEED),
            )
        end

        meta = result.meta.structure
        final_refit_meta = get_meta(meta, :final_refit_meta, (;))
        final_stage = Int(get_meta(meta, :final_stage))
        stage_level_counts = collect(get_meta(meta, :stage_level_counts, Int[]))
        wasted_levels = isempty(stage_level_counts) ? 0 :
            sum(stage_level_counts[(expected_stage + 1):end]; init = 0)
        expected_idxs = expected_active_idxs(SYSTEM_ID, basis)
        solves = get_meta(meta, :total_ode_solves)
        sim_time_s = get_meta(meta, :total_simulation_time_s)
        level_log = get_meta(meta, :level_log)

        record["elapsed_s"] = elapsed_s
        record["elapsed_h"] = elapsed_s / 3600.0
        record["loss"] = result.loss
        record["objective"] = result.objective
        record["final_stage"] = final_stage
        record["stage_overshoot"] = max(0, final_stage - expected_stage)
        record["wasted_levels"] = wasted_levels
        record["stage_level_counts"] = stage_level_counts
        record["levels_run"] = level_log === nothing ? nothing : length(level_log)
        record["pruned_match"] = expected_idxs === nothing ? nothing :
            support_match_pruned(result.structure, result.params, expected_idxs)
        record["pruned_support"] = pruned_support(result.structure, result.params)
        record["structure"] =
            replace(structure_to_string(result.structure, basis, result.params), '\n' => " | ")
        record["params"] = result.params
        record["termination_reason"] = string(get_meta(meta, :termination_reason))
        record["total_parameter_fits"] = get_meta(meta, :total_parameter_fits)
        record["total_ode_solves"] = solves
        record["total_invalid_solves"] = get_meta(meta, :total_invalid_solves)
        record["total_diverged_solves"] = get_meta(meta, :total_diverged_solves)
        record["total_simulation_time_s"] = sim_time_s
        record["total_parameter_optimization_time_s"] =
            get_meta(meta, :total_parameter_optimization_time_s)
        record["ms_per_ode_solve"] = ms_per_ode_solve(solves, sim_time_s)
        record["total_optimizer_iteration_limit_hits"] =
            get_meta(meta, :total_optimizer_iteration_limit_hits)
        record["total_optimizer_failure_hits"] = get_meta(meta, :total_optimizer_failure_hits)
        record["solver_retcodes"] = get_meta(meta, :solver_retcodes)
        record["optimizer_retcodes"] = get_meta(meta, :optimizer_retcodes)

        # Screening diagnostics (nothing on the reference path).
        record["screening_score_mode"] = get_meta(meta, :screening_score_mode)
        record["polish_start"] = get_meta(meta, :polish_start)
        record["nested_test_alpha"] = get_meta(meta, :nested_test_alpha)
        record["nested_gate_children"] = get_meta(meta, :nested_gate_children)
        record["nested_gate_failed_children"] = get_meta(meta, :nested_gate_failed_children)
        record["selection_diff_from_residual"] = get_meta(meta, :selection_diff_from_residual)
        record["levels_with_selection_diff_from_residual"] =
            get_meta(meta, :levels_with_selection_diff_from_residual)
        record["screening_evals"] = get_meta(meta, :screening_evals)
        record["invalid_screening_evals"] = get_meta(meta, :invalid_screening_evals)
        record["polished_candidates"] = get_meta(meta, :polished_candidates)
        record["polish_budget_exhausted"] = get_meta(meta, :polish_budget_exhausted)
        record["polish_budget_exhausted_share"] = begin
            polished = get_meta(meta, :polished_candidates)
            exhausted = get_meta(meta, :polish_budget_exhausted)
            (polished === nothing || exhausted === nothing || polished == 0) ? nothing :
                exhausted / polished
        end
        record["polish_convergence_failures"] = get_meta(meta, :polish_convergence_failures)
        record["rank_agreement_spearman"] = get_meta(meta, :rank_agreement_spearman)
        record["rank_agreement_spearman_median"] = get_meta(meta, :rank_agreement_spearman_median)
        record["rank_agreement_spearman_min"] = get_meta(meta, :rank_agreement_spearman_min)
        record["rank_agreement_spearman_max"] = get_meta(meta, :rank_agreement_spearman_max)
        record["rank_agreement_finite_levels"] = get_meta(meta, :rank_agreement_finite_levels)
        record["rank_agreement_total_levels"] = get_meta(meta, :rank_agreement_total_levels)
        record["rejected_diagnostic_candidates"] = get_meta(meta, :rejected_diagnostic_candidates)
        record["rejected_beats_best_selected"] = get_meta(meta, :rejected_beats_best_selected)
        record["screening_time_s"] = get_meta(meta, :screening_time_s)
        record["polish_time_s"] = get_meta(meta, :polish_time_s)
        record["rejected_diagnostic_time_s"] = get_meta(meta, :rejected_diagnostic_time_s)
        record["final_refit_time_s"] = get_meta(meta, :final_refit_time_s)
        record["final_refit_retcode"] = get_meta(final_refit_meta, :retcode)

        stage_rows = stage_cost_rows(condition.label, condition.eval_tol, level_log)
        level_rows = level_cost_rows(condition.label, condition.eval_tol, level_log)
    catch err
        record["error"] = sprint(showerror, err)
    finally
        record["finished_at"] = iso_timestamp()
    end

    return record, stage_rows, level_rows
end

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

const RECORD_COLUMNS = [
    "condition", "description", "eval_tol", "system_id", "system_name", "seed", "n_levels",
    "expected_stage", "loss", "final_stage", "stage_overshoot", "wasted_levels", "pruned_match",
    "elapsed_s", "elapsed_h", "levels_run", "termination_reason", "total_parameter_fits",
    "total_ode_solves", "total_invalid_solves", "total_simulation_time_s",
    "total_parameter_optimization_time_s", "ms_per_ode_solve",
    "total_optimizer_iteration_limit_hits", "total_optimizer_failure_hits", "structure",
    "stage_level_counts", "pruned_support", "screening_score_mode", "polish_start",
    "nested_test_alpha", "nested_gate_children", "nested_gate_failed_children",
    "selection_diff_from_residual", "levels_with_selection_diff_from_residual",
    "screening_evals", "invalid_screening_evals", "polished_candidates",
    "polish_budget_exhausted", "polish_budget_exhausted_share", "polish_convergence_failures",
    "rank_agreement_spearman", "rank_agreement_spearman_median", "rank_agreement_spearman_min",
    "rank_agreement_spearman_max", "rank_agreement_finite_levels",
    "rank_agreement_total_levels", "rejected_diagnostic_candidates",
    "rejected_beats_best_selected", "screening_time_s", "polish_time_s",
    "rejected_diagnostic_time_s", "final_refit_time_s", "final_refit_retcode",
    "started_at", "finished_at", "error",
]

const STAGE_COLUMNS = [
    "condition", "eval_tol", "stage", "levels", "time_s", "time_h", "time_share", "s_per_level",
    "parameter_fits", "ode_solves", "simulation_time_s", "ms_per_ode_solve",
]

const LEVEL_COLUMNS = [
    "condition", "eval_tol", "level", "stage", "best_loss", "best_objective", "n_params",
    "elapsed_s", "parameter_fits", "ode_solves", "invalid_solves", "simulation_time_s",
    "parameter_optimization_time_s",
]

function iso_timestamp()
    return Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ")
end

function csv_value(value)
    value === nothing && return ""
    text = string(value)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::String, records, columns)
    open(path, "w") do io
        println(io, join(columns, ","))
        for record in records
            println(io, join([csv_value(get(record, column, nothing)) for column in columns], ","))
        end
        flush(io)
    end
end

function write_json(path::String, value)
    open(path, "w") do io
        JSON3.pretty(io, value)
        write(io, '\n')
        flush(io)
    end
end

function append_jsonl(path::String, value)
    open(path, "a") do io
        JSON3.write(io, value)
        write(io, '\n')
        flush(io)
    end
end

function build_summary(records, stage_rows, anchor)
    return Dict{String, Any}(
        "script" => SCRIPT_SLUG,
        "work_package" => "WP-T2",
        "timestamp" => iso_timestamp(),
        "system_id" => SYSTEM_ID,
        "seed" => SEED,
        "n_levels" => N_LEVELS,
        "is_target_configuration" => SYSTEM_ID == 26 && N_LEVELS == 30 && SEED == 42,
        "condition_order" => [String(condition.label) for condition in CONDITIONS],
        "records" => records,
        "stage_costs" => stage_rows,
        "anchor_check" => anchor,
        "prediction" =>
            "The tighter evaluation tolerance does not change final_stage / stage_overshoot on " *
            "System 26; the overshoot there is algorithmic, not numerical.",
        "notes" => [
            "Hyperparameters and DiscoveryOptions match studies/regression/run_regression.jl; only the evaluation tolerance varies.",
            "Trajectory generation stays at abstol = reltol = 1e-9.",
            "Conditions run in order D8, R8, R6 (increasing expected runtime); each is written and flushed immediately.",
            "R6 is the Baseline v0 anchor (config_fingerprint $(BASELINE_V0_FINGERPRINT)).",
            "No records are written to studies/regression/history.jsonl.",
        ],
    )
end

function find_record(records, label::String)
    idx = findfirst(record -> record["condition"] == label, records)
    return idx === nothing ? nothing : records[idx]
end

# `full = true` prints a Float64 round-trip representation, which is what the anchor
# comparison needs; otherwise a compact form is enough for reading the tables.
function fmt(value; full = false)
    value === nothing && return "n/a"
    value isa AbstractFloat && return full ? repr(value) : @sprintf("%.6g", value)
    return string(value)
end

"""
Readable answer sheet for the four WP-T2 questions. Only measured values are written;
the interpretation is not part of this script.
"""
function write_questions(path::String, records, stage_rows, anchor)
    d8 = find_record(records, "D8")
    r8 = find_record(records, "R8")
    r6 = find_record(records, "R6")

    open(path, "w") do io
        println(io, "WP-T2 - measured values, system $(SYSTEM_ID), seed $(SEED), $(N_LEVELS) levels")
        println(io, "Generated $(iso_timestamp())")
        if !(SYSTEM_ID == 26 && N_LEVELS == 30)
            println(io, "WARNING: not the WP-T2 target configuration (system 26, 30 levels).")
        end
        println(io)

        println(io, "Q1  Does R6 reproduce the Baseline v0 anchor?")
        if anchor === nothing
            println(io, "    R6 did not produce a record.")
        else
            @printf(io, "    %-18s %-24s %-24s %s\n", "field", "measured (R6)", "Baseline v0", "equal")
            for (field, measured, baseline, equal) in (
                ("loss", "measured_loss", "baseline_loss", "loss_equal"),
                ("final_stage", "measured_final_stage", "baseline_final_stage", "final_stage_equal"),
                ("stage_overshoot", "measured_stage_overshoot", "baseline_stage_overshoot", "stage_overshoot_equal"),
                ("wasted_levels", "measured_wasted_levels", "baseline_wasted_levels", "wasted_levels_equal"),
                ("pruned_match", "measured_pruned_match", "baseline_pruned_match", "pruned_match_equal"),
            )
                @printf(io, "    %-18s %-24s %-24s %s\n", field,
                    fmt(get(anchor, measured, nothing); full = true),
                    fmt(get(anchor, baseline, nothing); full = true),
                    fmt(get(anchor, equal, nothing)))
            end
            println(io, "    anchor_reproduced = $(fmt(get(anchor, "anchor_reproduced", nothing)))")
            println(io, "    config_matches_baseline_v0 = $(fmt(get(anchor, "config_matches_baseline_v0", nothing)))")
            println(io, "    note: $(get(anchor, "note", ""))")
        end
        println(io)

        println(io, "Q2  Does the tighter tolerance change the overshoot?  (R6 vs R8)")
        @printf(io, "    %-24s %-24s %-24s\n", "field", "R6 (tol 1e-6)", "R8 (tol 1e-8)")
        for field in ("loss", "final_stage", "stage_overshoot", "wasted_levels", "levels_run",
                      "elapsed_s", "pruned_match")
            @printf(io, "    %-24s %-24s %-24s\n", field,
                fmt(r6 === nothing ? nothing : get(r6, field, nothing); full = true),
                fmt(r8 === nothing ? nothing : get(r8, field, nothing); full = true))
        end
        println(io)

        println(io, "Q3  Does condition D carry over to a coupled system?  (D8 vs R8)")
        @printf(io, "    %-24s %-24s %-24s\n", "field", "D8", "R8 (reference)")
        for field in ("loss", "final_stage", "stage_overshoot", "wasted_levels", "pruned_match",
                      "elapsed_s", "total_parameter_fits", "total_ode_solves", "ms_per_ode_solve")
            @printf(io, "    %-24s %-24s %-24s\n", field,
                fmt(d8 === nothing ? nothing : get(d8, field, nothing); full = true),
                fmt(r8 === nothing ? nothing : get(r8, field, nothing); full = true))
        end
        if d8 !== nothing && r8 !== nothing &&
           get(d8, "elapsed_s", nothing) !== nothing && get(r8, "elapsed_s", nothing) !== nothing
            @printf(io, "    %-24s %s\n", "speedup R8/D8", fmt(r8["elapsed_s"] / d8["elapsed_s"]))
        end
        println(io, "    structure D8: $(d8 === nothing ? "n/a" : get(d8, "structure", "n/a"))")
        println(io, "    structure R8: $(r8 === nothing ? "n/a" : get(r8, "structure", "n/a"))")
        println(io, "    structure R6: $(r6 === nothing ? "n/a" : get(r6, "structure", "n/a"))")
        if d8 !== nothing
            println(io, "    screening diagnostics (D8):")
            for field in ("rank_agreement_spearman", "rank_agreement_spearman_median",
                          "rank_agreement_finite_levels", "rank_agreement_total_levels",
                          "nested_gate_children", "nested_gate_failed_children",
                          "selection_diff_from_residual",
                          "levels_with_selection_diff_from_residual",
                          "polished_candidates", "polish_budget_exhausted",
                          "polish_budget_exhausted_share", "polish_convergence_failures")
                @printf(io, "      %-42s %s\n", field, fmt(get(d8, field, nothing)))
            end
        end
        println(io)

        println(io, "Q4  Where does the time go?  (per-stage cost breakdown)")
        @printf(io, "    %-6s %-6s %-7s %-11s %-9s %-9s %-11s %-13s %s\n",
            "cond", "tol", "stage", "levels", "time_s", "time_h", "share", "s/level", "ms/ode_solve")
        for row in stage_rows
            @printf(io, "    %-6s %-6s %-7s %-11s %-9s %-9s %-11s %-13s %s\n",
                row["condition"], fmt(row["eval_tol"]), string(row["stage"]),
                string(row["levels"]), fmt(row["time_s"]), fmt(row["time_h"]),
                fmt(row["time_share"]), fmt(row["s_per_level"]), fmt(row["ms_per_ode_solve"]))
        end
        println(io)
        println(io, "    cost per integration over the whole run:")
        for record in records
            @printf(io, "      %-6s tol=%-8s ms_per_ode_solve=%-12s ode_solves=%s\n",
                record["condition"], fmt(record["eval_tol"]),
                fmt(get(record, "ms_per_ode_solve", nothing)),
                fmt(get(record, "total_ode_solves", nothing)))
        end
        flush(io)
    end
end

function print_record(record)
    if record["error"] !== nothing
        println("$(record["condition"]) FAILED: $(record["error"])")
        return
    end
    @printf(
        "%s tol=%.0e system=%d seed=%d elapsed=%.1fs loss=%.16e stage=%d/%d overshoot=%d wasted=%d pruned=%s fits=%s solves=%s ms_per_solve=%s\n",
        record["condition"], record["eval_tol"], record["system_id"], record["seed"],
        record["elapsed_s"], record["loss"], record["final_stage"], record["expected_stage"],
        record["stage_overshoot"], record["wasted_levels"], fmt(record["pruned_match"]),
        fmt(record["total_parameter_fits"]), fmt(record["total_ode_solves"]),
        fmt(record["ms_per_ode_solve"]),
    )
    println("  structure: $(record["structure"])")
end

function print_anchor(anchor)
    println("ANCHOR check against Baseline v0 ($(BASELINE_V0_FINGERPRINT)):")
    println("  config_matches_baseline_v0 = $(fmt(get(anchor, "config_matches_baseline_v0", nothing)))")
    println("  anchor_reproduced          = $(fmt(get(anchor, "anchor_reproduced", nothing)))")
    for (field, measured, baseline) in (
        ("loss", "measured_loss", "baseline_loss"),
        ("final_stage", "measured_final_stage", "baseline_final_stage"),
        ("stage_overshoot", "measured_stage_overshoot", "baseline_stage_overshoot"),
        ("wasted_levels", "measured_wasted_levels", "baseline_wasted_levels"),
        ("pruned_match", "measured_pruned_match", "baseline_pruned_match"),
    )
        @printf("  %-16s measured=%-24s baseline=%s\n", field,
            fmt(get(anchor, measured, nothing); full = true),
            fmt(get(anchor, baseline, nothing); full = true))
    end
    if get(anchor, "anchor_reproduced", nothing) === false
        println("  R6 DEVIATES FROM BASELINE v0 - the setup is suspect; report, do not smooth.")
    end
end

function main()
    mkpath(OUTPUT_DIR)
    records_path = joinpath(OUTPUT_DIR, "records.jsonl")
    isfile(records_path) && rm(records_path)

    # Live progress goes through the shared logger, so every level line lands on the terminal
    # and persistently in run.log at the same time.
    set_level(INFO)
    set_log_file(joinpath(OUTPUT_DIR, "run.log"))

    records = Dict{String, Any}[]
    stage_rows = Dict{String, Any}[]
    level_rows = Dict{String, Any}[]
    anchor = nothing

    try
        log_info("WP-T2: system $(SYSTEM_ID), seed $(SEED), $(N_LEVELS) levels")
        if !(SYSTEM_ID == 26 && N_LEVELS == 30)
            log_info("WARNING: not the target configuration (system 26, 30 levels) - smoke-test mode.")
        end
        log_info("Writing outputs to $(OUTPUT_DIR)")
        flush(stdout)

        for condition in CONDITIONS
            log_info(@sprintf(
                "Running condition %s (eval_tol=%.0e): %s",
                condition.label, condition.eval_tol, condition.description,
            ))
            flush(stdout)

            record, condition_stage_rows, condition_level_rows = run_condition(condition)
            push!(records, record)
            append!(stage_rows, condition_stage_rows)
            append!(level_rows, condition_level_rows)

            duration_text = record["error"] === nothing ?
                @sprintf("%.1fs (%.2f h)", record["elapsed_s"], record["elapsed_h"]) : "an error"
            log_info("Finished condition $(condition.label) after $(duration_text)")
            print_record(record)

            if condition.label == ANCHOR_LABEL && record["error"] === nothing
                anchor = anchor_check(condition.label, record)
                print_anchor(anchor)
                write_json(joinpath(OUTPUT_DIR, "anchor_check.json"), anchor)
            end

            # Flush everything after each condition: an abort costs at most the running condition.
            append_jsonl(records_path, record)
            write_csv(joinpath(OUTPUT_DIR, "records.csv"), records, RECORD_COLUMNS)
            write_csv(joinpath(OUTPUT_DIR, "stage_costs.csv"), stage_rows, STAGE_COLUMNS)
            write_csv(joinpath(OUTPUT_DIR, "level_costs.csv"), level_rows, LEVEL_COLUMNS)
            write_json(joinpath(OUTPUT_DIR, "summary.json"), build_summary(records, stage_rows, anchor))
            write_questions(joinpath(OUTPUT_DIR, "questions.txt"), records, stage_rows, anchor)
            log_info("Flushed outputs after condition $(condition.label)")
            flush(stdout)
        end

        log_info("Wrote records.jsonl, records.csv, stage_costs.csv, level_costs.csv, summary.json, questions.txt, anchor_check.json, run.log")
    finally
        close_log_file()
        flush(stdout)
    end
end

main()
