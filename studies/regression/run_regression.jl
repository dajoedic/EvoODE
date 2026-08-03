import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf
using ProgressMeter
using SHA

include(joinpath(@__DIR__, "..", "..", "src", "EvoODE.jl"))
using .EvoODE
include(joinpath(@__DIR__, "diagnostic_systems.jl"))

const HISTORY_PATH = get(ENV, "EVO_REGRESSION_HISTORY_PATH", joinpath(@__DIR__, "history.jsonl"))
const OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression")
const RUN_LOG_PATH = joinpath(OUTPUT_DIR, "run.log")

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
const BFGS_MAX_LOSS_EVALS = 100_000

const SCREENING_BUDGETS_ENABLED = lowercase(strip(get(ENV, "EVO_SCREENING_BUDGETS", ""))) in ("1", "true", "yes")
const SCREENING_BFGS_ABSTOL = 1e-5
const SCREENING_BFGS_RELTOL = 1e-5
const SCREENING_BFGS_MAXITERS_SOLVE = 20_000
const SCREENING_DIVERGENCE_LIMIT = 1e6
const DERIVATIVE_SCREEN_K = POP_SIZE
const DERIVATIVE_POLISH_MAXITERS = 20
const DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES = 2

const LOOKAHEAD_CAP_POLICY = (
    estimator = :local_poly,
    weighting = :richardson_wls,
    aggregation = :majority_no_undecided_at_or_below,
    lookahead_horizon = 2,
    tau_rel = 1e-4,
    tau_abs = 1e-8,
    cond_cap = 1e10,
    excitation_floor = 1e-10,
)

const OPTIONS_CONFIG = (
    verbose = 1,
    min_levels = 2,
    max_levels = 50,
    loss_tol = 1e-8,
    plateau_window = 3,
    plateau_tol = 1e-4,
    plateau_relative = false,
    plateau_rtol = 1e-3,
)

const VARIANTS = [
    (
        label = "evogrow_v2_2_stage_local",
        constructor = (level_callback, screening_optimizer) -> EvoGrow(
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
            level_callback = level_callback,
        ),
    ),
    (
        label = "evogrow_v3",
        constructor = (level_callback, screening_optimizer) -> EvoGrowV3(
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
            level_callback = level_callback,
        ),
    ),
    (
        label = "evogrow_v2_2_stage_capped",
        constructor = (level_callback, screening_optimizer) -> EvoGrow(
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
            level_callback = level_callback,
            stage_cap_policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...),
        ),
    ),
    (
        label = "evogrow_v3_stage_capped",
        constructor = (level_callback, screening_optimizer) -> EvoGrowStageCapped(
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
            level_callback = level_callback,
            cap_policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...),
        ),
    ),
]

const FINGERPRINT_VARIANT_LABELS = [
    "evogrow_v2_2_stage_local",
    "evogrow_screening_derivative",
    "evogrow_v3",
    "evogrow_v3_stage_capped",
]

function build_options(seed::Int)
    return DiscoveryOptions(
        rng_seed = seed,
        verbose = OPTIONS_CONFIG.verbose,
        min_levels = OPTIONS_CONFIG.min_levels,
        max_levels = OPTIONS_CONFIG.max_levels,
        loss_tol = OPTIONS_CONFIG.loss_tol,
        plateau_window = OPTIONS_CONFIG.plateau_window,
        plateau_tol = OPTIONS_CONFIG.plateau_tol,
        plateau_relative = OPTIONS_CONFIG.plateau_relative,
        plateau_rtol = OPTIONS_CONFIG.plateau_rtol,
    )
end

function build_reference_optimizer()
    return BFGSOptimizer(
        maxiters = BFGS_MAXITERS,
        abstol = BFGS_ABSTOL,
        reltol = BFGS_RELTOL,
        maxiters_solve = BFGS_MAXITERS_SOLVE,
        max_loss_evals = BFGS_MAX_LOSS_EVALS,
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
        max_loss_evals = BFGS_MAX_LOSS_EVALS,
        reject_nonfinite = true,
        divergence_limit = SCREENING_DIVERGENCE_LIMIT,
    )
end

function canonical_value(x)
    if x isa NamedTuple
        parts = String[]
        for key in sort(collect(keys(x)); by = string)
            push!(parts, string(key, "=", canonical_value(getfield(x, key))))
        end
        return "{" * join(parts, ",") * "}"
    elseif x isa AbstractDict
        parts = String[]
        for key in sort(collect(keys(x)); by = string)
            push!(parts, string(key, "=", canonical_value(x[key])))
        end
        return "{" * join(parts, ",") * "}"
    elseif x isa Tuple
        return "(" * join(canonical_value.(collect(x)), ",") * ")"
    elseif x isa AbstractVector
        return "[" * join(canonical_value.(x), ",") * "]"
    else
        return repr(x)
    end
end

function config_fingerprint()
    system_payload = [
        (
            system_id = Int(system[:system_id]),
            dim = Int(system[:dim]),
            init_sets = [Float64[x for x in init] for init in system[:init_sets]],
            t_grid = Float64[t for t in system[:t_grid]],
            tspan = system[:tspan],
            T = Int(system[:T]),
            expected_stage = Int(system[:expected_stage]),
        )
        for system in sort(REGRESSION_SYSTEMS; by = s -> Int(s[:system_id]))
    ]
    payload = (
        system_ids = sort([Int(system[:system_id]) for system in REGRESSION_SYSTEMS]),
        initial_condition_sets = REGRESSION_IC_SETS,
        systems = system_payload,
        seeds = REGRESSION_SEEDS,
        pop_size = POP_SIZE,
        n_levels = N_LEVELS,
        children_per_parent = CHILDREN_PER_PARENT,
        max_terms_per_eq = MAX_TERMS,
        lambda = LAMBDA,
        min_levels_per_stage = STAGE_MIN,
        new_term_bias_prob = SOFT_BIAS,
        use_pretuning = USE_PRETUNING,
        bfgs_maxiters = BFGS_MAXITERS,
        bfgs_abstol = BFGS_ABSTOL,
        bfgs_reltol = BFGS_RELTOL,
        bfgs_maxiters_solve = BFGS_MAXITERS_SOLVE,
        bfgs_max_loss_evals = BFGS_MAX_LOSS_EVALS,
        screening_budgets_enabled = SCREENING_BUDGETS_ENABLED,
        screening_bfgs_abstol = SCREENING_BFGS_ABSTOL,
        screening_bfgs_reltol = SCREENING_BFGS_RELTOL,
        screening_bfgs_maxiters_solve = SCREENING_BFGS_MAXITERS_SOLVE,
        screening_divergence_limit = SCREENING_DIVERGENCE_LIMIT,
        variants = FINGERPRINT_VARIANT_LABELS,
        derivative_screen_k = DERIVATIVE_SCREEN_K,
        derivative_polish_maxiters = DERIVATIVE_POLISH_MAXITERS,
        derivative_rejected_diagnostic_samples = DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES,
        lookahead_stage_cap = (
            variant = "evogrow_v3_stage_capped",
            estimator = String(LOOKAHEAD_CAP_POLICY.estimator),
            weighting = String(LOOKAHEAD_CAP_POLICY.weighting),
            aggregation = String(LOOKAHEAD_CAP_POLICY.aggregation),
            lookahead_horizon = LOOKAHEAD_CAP_POLICY.lookahead_horizon,
            tau_rel = LOOKAHEAD_CAP_POLICY.tau_rel,
            tau_abs = LOOKAHEAD_CAP_POLICY.tau_abs,
            cond_cap = LOOKAHEAD_CAP_POLICY.cond_cap,
            excitation_floor = LOOKAHEAD_CAP_POLICY.excitation_floor,
        ),
        discovery_options = OPTIONS_CONFIG,
        trajectory_solver = (
            algorithm = "Tsit5",
            saveat = "dataset solutions[1][1].t grid; shipped y ignored",
            abstol = 1e-9,
            reltol = 1e-9,
        ),
        basis = "default_staged_polynomial_basis(dim)",
        loss = "MSELoss",
    )
    bytes = sha256(codeunits(canonical_value(payload)))
    return bytes2hex(bytes)[1:16]
end

function git_output(args::Vector{String})
    try
        return chomp(read(`git $args`, String))
    catch
        return nothing
    end
end

function git_provenance()
    hash = git_output(["rev-parse", "--short", "HEAD"])
    dirty = git_output(["status", "--porcelain"])
    return (
        git_hash = hash === nothing || isempty(hash) ? "unknown" : hash,
        git_dirty = dirty === nothing ? nothing : !isempty(dirty),
    )
end

function history_line_count()
    isfile(HISTORY_PATH) || return 0
    count = 0
    open(HISTORY_PATH, "r") do io
        for _ in eachline(io)
            count += 1
        end
    end
    return count
end

function fresh_requested()
    flag = lowercase(strip(get(ENV, "FRESH", "")))
    return flag in ("1", "true", "yes")
end

function _env_filter(name::String)
    value = strip(get(ENV, name, ""))
    return isempty(value) ? nothing : value
end

function selected_variants()
    label = _env_filter("EVO_REGRESSION_VARIANT")
    label === nothing && return VARIANTS

    selected = [variant for variant in VARIANTS if String(variant.label) == label]
    isempty(selected) && error("Unknown EVO_REGRESSION_VARIANT=$(label)")
    return selected
end

function selected_systems()
    value = _env_filter("EVO_REGRESSION_SYSTEM_ID")
    value === nothing && return REGRESSION_SYSTEMS

    system_id = parse(Int, value)
    selected = [system for system in REGRESSION_SYSTEMS if Int(system[:system_id]) == system_id]
    isempty(selected) && error("Unknown EVO_REGRESSION_SYSTEM_ID=$(system_id)")
    return selected
end

function selected_seeds()
    value = _env_filter("EVO_REGRESSION_SEED")
    value === nothing && return REGRESSION_SEEDS

    seed = parse(Int, value)
    selected = [s for s in REGRESSION_SEEDS if s == seed]
    isempty(selected) && error("Unknown EVO_REGRESSION_SEED=$(seed)")
    return selected
end

function selected_ic_sets()
    value = _env_filter("EVO_REGRESSION_IC_SET")
    value === nothing && return REGRESSION_IC_SETS

    ic_set = parse(Int, value)
    selected = [s for s in REGRESSION_IC_SETS if s == ic_set]
    isempty(selected) && error("Unknown EVO_REGRESSION_IC_SET=$(ic_set)")
    return selected
end

function completed_key(variant, system, ic_set::Int, seed::Int)
    return (String(variant.label), Int(system[:system_id]), ic_set, seed)
end

function load_completed_cells(fingerprint::String)
    completed = Set{Tuple{String, Int, Int, Int}}()
    isfile(HISTORY_PATH) || return completed

    open(HISTORY_PATH, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            try
                record = JSON3.read(line)
                if getproperty(record, :config_fingerprint) == fingerprint &&
                   getproperty(record, :error) === nothing
                    variant = String(getproperty(record, :variant))
                    system_id = Int(getproperty(record, :system_id))
                    ic_set = haskey(record, :initial_condition_set) ? Int(getproperty(record, :initial_condition_set)) : 1
                    seed = Int(getproperty(record, :seed))
                    push!(completed, (variant, system_id, ic_set, seed))
                end
            catch
                continue
            end
        end
    end

    return completed
end

function iso_timestamp()
    return Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ")
end

function append_run_log_line!(line::AbstractString)
    mkpath(dirname(RUN_LOG_PATH))
    open(RUN_LOG_PATH, "a") do io
        println(io, line)
        flush(io)
    end
end

function open_evo_logger_append!(path::String)
    mkpath(dirname(path))
    close_log_file()
    EvoODE.EvoLogger.LOGGER.log_io = open(path, "a")
    return nothing
end

function close_evo_logger!()
    close_log_file()
    return nothing
end

function build_trajectory(system, ic_set::Int)
    system_id = Int(system[:system_id])
    tspan = system[:tspan]
    t_grid = Float64[t for t in system[:t_grid]]
    ic_set in REGRESSION_IC_SETS || error("Unsupported initial-condition set $(ic_set)")
    u0 = Float64[x for x in system[:init_sets][ic_set]]
    prob = ODEProblem(rhs_for_system(system_id), copy(u0), tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function true_rhs_matrix(system_id::Int, traj::Trajectory)
    f! = rhs_for_system(system_id)
    T, dim = size(traj.x)
    out = zeros(Float64, T, dim)
    du = zeros(Float64, dim)
    @inbounds for i in 1:T
        f!(du, view(traj.x, i, :), nothing, traj.t[i])
        out[i, :] .= du
    end
    return out
end

function derivative_active_fraction(rhs_values::AbstractVector{Float64})
    max_abs = maximum(abs, rhs_values)
    max_abs == 0.0 && return 0.0
    return count(abs.(rhs_values) .> 0.01 * max_abs) / length(rhs_values)
end

function derivative_active_fractions(system_id::Int, traj::Trajectory)
    rhs = true_rhs_matrix(system_id, traj)
    return [derivative_active_fraction(rhs[:, eq]) for eq in 1:size(rhs, 2)]
end

function active_term_names(structure::StructureSpec, basis::AbstractBasis)
    return [[basis_term_name(basis, term_idx) for term_idx in eq_terms] for eq_terms in structure.active_idxs]
end

function run_one(variant, system, ic_set::Int, seed::Int, fingerprint::String, provenance)
    timestamp = iso_timestamp()
    system_id = Int(system[:system_id])
    system_name = String(system[:system_name])
    dim = Int(system[:dim])
    expected_stage = Int(system[:expected_stage])
    u0 = Float64[x for x in system[:init_sets][ic_set]]

    base_record = Dict{String, Any}(
        "timestamp" => timestamp,
        "git_hash" => provenance.git_hash,
        "git_dirty" => provenance.git_dirty,
        "variant" => String(variant.label),
        "config_fingerprint" => fingerprint,
        "system_id" => system_id,
        "system_name" => system_name,
        "initial_condition_set" => ic_set,
        "u0" => u0,
        "tspan" => Tuple(Float64[x for x in system[:tspan]]),
        "T" => Int(system[:T]),
        "seed" => seed,
        "loss" => nothing,
        "pruned_match" => nothing,
        "final_stage" => nothing,
        "expected_stage" => expected_stage,
        "stage_overshoot" => nothing,
        "wasted_levels" => nothing,
        "elapsed_s" => nothing,
        "eq_final_stages" => nothing,
        "eq_overshoot" => nothing,
        "eq_wasted_levels" => nothing,
        "derivative_active_fractions" => nothing,
        "support_terms" => nothing,
        "n_levels" => N_LEVELS,
        "use_pretuning" => USE_PRETUNING,
        "screening_budgets_active" => nothing,
        "derivative_screening_active" => nothing,
        "total_loss_evals" => nothing,
        "total_parameter_fits" => nothing,
        "total_ode_solves" => nothing,
        "total_invalid_solves" => nothing,
        "total_diverged_solves" => nothing,
        "total_nonfinite_solves" => nothing,
        "total_step_limit_solves" => nothing,
        "total_solver_unstable_solves" => nothing,
        "total_optimizer_limit_hits" => nothing,
        "total_optimizer_iteration_limit_hits" => nothing,
        "total_optimizer_safety_limit_hits" => nothing,
        "total_optimizer_eval_budget_limit_hits" => nothing,
        "total_optimizer_failure_hits" => nothing,
        "total_optimizer_unknown_retcode_hits" => nothing,
        "total_parameter_optimization_time_s" => nothing,
        "total_simulation_time_s" => nothing,
        "screening_evals" => nothing,
        "invalid_screening_evals" => nothing,
        "polished_candidates" => nothing,
        "polish_budget_exhausted" => nothing,
        "polish_convergence_failures" => nothing,
        "rejected_diagnostic_candidates" => nothing,
        "rejected_diagnostic_budget_exhausted" => nothing,
        "rejected_diagnostic_convergence_failures" => nothing,
        "rejected_beats_best_selected" => nothing,
        "screening_time_s" => nothing,
        "polish_time_s" => nothing,
        "rejected_diagnostic_time_s" => nothing,
        "rank_agreement_spearman" => nothing,
        "screen_k" => nothing,
        "polish_maxiters" => nothing,
        "rejected_diagnostic_samples" => nothing,
        "solver_retcodes" => nothing,
        "optimizer_retcodes" => nothing,
        "error" => nothing,
    )

    level_cap = min(N_LEVELS, OPTIONS_CONFIG.max_levels)
    # The inner bar ticks once per completed EvoGrow level. One level can still
    # pause for the BFGS time limit if fitting is slow, but this is much finer
    # than the outer per-run progress bar.
    inner_progress = Progress(
        level_cap;
        desc = "Levels",
        showspeed = true,
        offset = 1,
    )
    level_callback = snapshot -> begin
        next!(
            inner_progress;
            showvalues = [
                (:system_id, system_id),
                (:ic_set, ic_set),
                (:seed, seed),
                (:level, snapshot.level),
                (:stage, snapshot.stage),
                (:best_loss, @sprintf("%.3e", snapshot.best_loss)),
            ],
        )
    end

    try
        traj = build_trajectory(system, ic_set)
        base_record["derivative_active_fractions"] = derivative_active_fractions(system_id, traj)
        optimizer = build_reference_optimizer()
        screening_optimizer = SCREENING_BUDGETS_ENABLED ? build_screening_optimizer() : nothing
        strategy = variant.constructor(level_callback, screening_optimizer)
        basis = default_staged_polynomial_basis(dim)
        options = build_options(seed)

        result = nothing
        elapsed = @elapsed redirect_stdout(devnull) do
            result = discover(
                traj;
                structure = strategy,
                optimizer = optimizer,
                basis = basis,
                loss = MSELoss(),
                options = options,
            )
        end

        meta = result.meta.structure
        required_meta_fields = (
            :screening_budgets_active,
            :total_parameter_fits,
            :total_loss_evals,
            :total_ode_solves,
            :total_invalid_solves,
            :solver_retcodes,
            :optimizer_retcodes,
        )
        for field in required_meta_fields
            if !haskey(meta, field)
                error("Structure search meta is missing $(field)")
            end
        end
        final_stage = haskey(meta, :final_stage) ? Int(meta.final_stage) : nothing
        stage_level_counts = haskey(meta, :stage_level_counts) ? collect(meta.stage_level_counts) : Int[]
        stage_overshoot = final_stage === nothing ? nothing : max(0, final_stage - expected_stage)
        wasted_levels = isempty(stage_level_counts) ? 0 : sum(stage_level_counts[(expected_stage + 1):end]; init = 0)
        expected_idxs = expected_active_idxs(system_id, basis)
        pruned_match = expected_idxs === nothing ? false : support_match_pruned(result.structure, result.params, expected_idxs)
        eq_final_stages = haskey(meta, :eq_final_stages) && meta.eq_final_stages !== nothing ? collect(meta.eq_final_stages) : nothing
        eq_stage_histories = haskey(meta, :eq_stage_histories) && meta.eq_stage_histories !== nothing ? [collect(hist) for hist in meta.eq_stage_histories] : nothing
        has_eq_stage_data = eq_final_stages !== nothing && eq_stage_histories !== nothing
        local_eq_overshoot = has_eq_stage_data ? eq_overshoot(eq_final_stages, expected_stage) : nothing
        local_eq_wasted_levels = has_eq_stage_data ? eq_wasted_levels(eq_stage_histories, expected_stage) : nothing

        base_record["loss"] = result.loss
        base_record["pruned_match"] = pruned_match
        base_record["final_stage"] = final_stage
        base_record["stage_overshoot"] = stage_overshoot
        base_record["wasted_levels"] = wasted_levels
        base_record["elapsed_s"] = elapsed
        base_record["eq_final_stages"] = eq_final_stages
        base_record["eq_overshoot"] = local_eq_overshoot
        base_record["eq_wasted_levels"] = local_eq_wasted_levels
        base_record["support_terms"] = active_term_names(result.structure, basis)
        base_record["screening_budgets_active"] = meta.screening_budgets_active
        base_record["derivative_screening_active"] = haskey(meta, :derivative_screening_active) ? meta.derivative_screening_active : false
        base_record["stage_caps"] = haskey(meta, :stage_caps) ? meta.stage_caps : nothing
        base_record["stage_cap_policy_active"] = haskey(meta, :stage_cap_policy_active) ? meta.stage_cap_policy_active : false
        base_record["total_loss_evals"] = haskey(meta, :total_loss_evals) ? meta.total_loss_evals : nothing
        base_record["total_parameter_fits"] = haskey(meta, :total_parameter_fits) ? meta.total_parameter_fits : nothing
        base_record["total_ode_solves"] = haskey(meta, :total_ode_solves) ? meta.total_ode_solves : nothing
        base_record["total_invalid_solves"] = haskey(meta, :total_invalid_solves) ? meta.total_invalid_solves : nothing
        base_record["total_diverged_solves"] = haskey(meta, :total_diverged_solves) ? meta.total_diverged_solves : nothing
        base_record["total_nonfinite_solves"] = haskey(meta, :total_nonfinite_solves) ? meta.total_nonfinite_solves : nothing
        base_record["total_step_limit_solves"] = haskey(meta, :total_step_limit_solves) ? meta.total_step_limit_solves : nothing
        base_record["total_solver_unstable_solves"] = haskey(meta, :total_solver_unstable_solves) ? meta.total_solver_unstable_solves : nothing
        base_record["total_optimizer_limit_hits"] = haskey(meta, :total_optimizer_limit_hits) ? meta.total_optimizer_limit_hits : nothing
        base_record["total_optimizer_iteration_limit_hits"] = haskey(meta, :total_optimizer_iteration_limit_hits) ? meta.total_optimizer_iteration_limit_hits : nothing
        base_record["total_optimizer_safety_limit_hits"] = haskey(meta, :total_optimizer_safety_limit_hits) ? meta.total_optimizer_safety_limit_hits : nothing
        base_record["total_optimizer_eval_budget_limit_hits"] = haskey(meta, :total_optimizer_eval_budget_limit_hits) ? meta.total_optimizer_eval_budget_limit_hits : nothing
        base_record["total_optimizer_failure_hits"] = haskey(meta, :total_optimizer_failure_hits) ? meta.total_optimizer_failure_hits : nothing
        base_record["total_optimizer_unknown_retcode_hits"] = haskey(meta, :total_optimizer_unknown_retcode_hits) ? meta.total_optimizer_unknown_retcode_hits : nothing
        base_record["total_parameter_optimization_time_s"] = haskey(meta, :total_parameter_optimization_time_s) ? meta.total_parameter_optimization_time_s : nothing
        base_record["total_simulation_time_s"] = haskey(meta, :total_simulation_time_s) ? meta.total_simulation_time_s : nothing
        base_record["screening_evals"] = haskey(meta, :screening_evals) ? meta.screening_evals : nothing
        base_record["invalid_screening_evals"] = haskey(meta, :invalid_screening_evals) ? meta.invalid_screening_evals : nothing
        base_record["polished_candidates"] = haskey(meta, :polished_candidates) ? meta.polished_candidates : nothing
        base_record["polish_budget_exhausted"] = haskey(meta, :polish_budget_exhausted) ? meta.polish_budget_exhausted : nothing
        base_record["polish_convergence_failures"] = haskey(meta, :polish_convergence_failures) ? meta.polish_convergence_failures : nothing
        base_record["rejected_diagnostic_candidates"] = haskey(meta, :rejected_diagnostic_candidates) ? meta.rejected_diagnostic_candidates : nothing
        base_record["rejected_diagnostic_budget_exhausted"] = haskey(meta, :rejected_diagnostic_budget_exhausted) ? meta.rejected_diagnostic_budget_exhausted : nothing
        base_record["rejected_diagnostic_convergence_failures"] = haskey(meta, :rejected_diagnostic_convergence_failures) ? meta.rejected_diagnostic_convergence_failures : nothing
        base_record["rejected_beats_best_selected"] = haskey(meta, :rejected_beats_best_selected) ? meta.rejected_beats_best_selected : nothing
        base_record["screening_time_s"] = haskey(meta, :screening_time_s) ? meta.screening_time_s : nothing
        base_record["polish_time_s"] = haskey(meta, :polish_time_s) ? meta.polish_time_s : nothing
        base_record["rejected_diagnostic_time_s"] = haskey(meta, :rejected_diagnostic_time_s) ? meta.rejected_diagnostic_time_s : nothing
        base_record["rank_agreement_spearman"] = haskey(meta, :rank_agreement_spearman) ? meta.rank_agreement_spearman : nothing
        base_record["screen_k"] = haskey(meta, :screen_k) ? meta.screen_k : nothing
        base_record["polish_maxiters"] = haskey(meta, :polish_maxiters) ? meta.polish_maxiters : nothing
        base_record["rejected_diagnostic_samples"] = haskey(meta, :rejected_diagnostic_samples) ? meta.rejected_diagnostic_samples : nothing
        base_record["solver_retcodes"] = haskey(meta, :solver_retcodes) ? collect(meta.solver_retcodes) : nothing
        base_record["optimizer_retcodes"] = haskey(meta, :optimizer_retcodes) ? collect(meta.optimizer_retcodes) : nothing
    catch err
        base_record["error"] = sprint(showerror, err)
    finally
        finish!(inner_progress)
    end

    return base_record
end

function append_record!(record)
    mkpath(dirname(HISTORY_PATH))
    open(HISTORY_PATH, "a") do io
        JSON3.write(io, record)
        write(io, '\n')
    end
end

function done_log_line(record, index::Int, total::Int)
    if record["error"] !== nothing
        return @sprintf(
            "[%d/%d] variant=%s sys=%d ic=%d seed=%d - done loss=null stage=null/%d pruned=null elapsed=nulls error=%s",
            index,
            total,
            record["variant"],
            record["system_id"],
            record["initial_condition_set"],
            record["seed"],
            record["expected_stage"],
            record["error"],
        )
    end
    return @sprintf(
        "[%d/%d] variant=%s sys=%d ic=%d seed=%d - done loss=%.3e stage=%s/%d pruned=%s elapsed=%.1fs",
        index,
        total,
        record["variant"],
        record["system_id"],
        record["initial_condition_set"],
        record["seed"],
        record["loss"],
        string(record["final_stage"]),
        record["expected_stage"],
        string(record["pruned_match"]),
        record["elapsed_s"],
    )
end

function summary_line(record)
    if record["error"] !== nothing
        return @sprintf(
            "variant=%s sys=%d ic=%d seed=%d loss=null stage=null/%d pruned=null elapsed=nulls error=%s",
            record["variant"],
            record["system_id"],
            record["initial_condition_set"],
            record["seed"],
            record["expected_stage"],
            record["error"],
        )
    end
    return @sprintf(
        "variant=%s sys=%d ic=%d seed=%d loss=%.3e stage=%s/%d pruned=%s elapsed=%.1fs",
        record["variant"],
        record["system_id"],
        record["initial_condition_set"],
        record["seed"],
        record["loss"],
        string(record["final_stage"]),
        record["expected_stage"],
        string(record["pruned_match"]),
        record["elapsed_s"],
    )
end

function main()
    mkpath(OUTPUT_DIR)
    set_level(INFO)

    fingerprint = config_fingerprint()
    provenance = git_provenance()
    appended = 0
    skipped = 0
    completed = fresh_requested() ? Set{Tuple{String, Int, Int, Int}}() : load_completed_cells(fingerprint)

    println("Regression history fingerprint: $(fingerprint)")
    println("Git: $(provenance.git_hash), dirty=$(provenance.git_dirty)")
    println("Resume: completed=$(length(completed)), fresh=$(fresh_requested())")

    variants = selected_variants()
    systems = selected_systems()
    ic_sets = selected_ic_sets()
    seeds = selected_seeds()
    total_runs = length(variants) * length(systems) * length(ic_sets) * length(seeds)
    run_index = 0

    append_run_log_line!("=== Started at $(iso_timestamp()) ===")
    open_evo_logger_append!(RUN_LOG_PATH)
    try
        # The progress bar ticks once per completed run. A single run can take
        # minutes to hours; within-run liveness is written to run.log by EvoGrow.
        progress = Progress(
            total_runs;
            desc = "Regression",
            showspeed = true,
            offset = 0,
        )

        for variant in variants
            for system in systems
                for ic_set in ic_sets
                    for seed in seeds
                    run_index += 1
                    key = completed_key(variant, system, ic_set, seed)
                    if key in completed
                        skipped += 1
                        append_run_log_line!(
                            @sprintf(
                                "[%d/%d] variant=%s sys=%d ic=%d seed=%d - skipped (already in history)",
                                run_index,
                                total_runs,
                                variant.label,
                                Int(system[:system_id]),
                                ic_set,
                                seed,
                            )
                        )
                        next!(
                            progress;
                            showvalues = [
                                (:variant, variant.label),
                                (:system_id, Int(system[:system_id])),
                                (:ic_set, ic_set),
                                (:seed, seed),
                            ],
                        )
                        continue
                    end

                    append_run_log_line!(
                        @sprintf(
                            "[%d/%d] variant=%s sys=%d ic=%d seed=%d - start %s",
                            run_index,
                            total_runs,
                            variant.label,
                            Int(system[:system_id]),
                            ic_set,
                            seed,
                            iso_timestamp(),
                        )
                    )

                    record = run_one(variant, system, ic_set, seed, fingerprint, provenance)
                    append_record!(record)
                    appended += 1

                    done_line = done_log_line(record, run_index, total_runs)
                    append_run_log_line!(done_line)
                    next!(
                        progress;
                        showvalues = [
                            (:variant, variant.label),
                            (:system_id, Int(system[:system_id])),
                            (:ic_set, ic_set),
                            (:seed, seed),
                        ],
                    )
                    println(summary_line(record))
                    end
                end
            end
        end

        finish!(progress)
    finally
        close_evo_logger!()
        append_run_log_line!("=== Finished at $(iso_timestamp()) ===")
    end

    total_lines = history_line_count()
    println("Total cells: $(total_runs)")
    println("Skipped completed: $(skipped)")
    println("Run this invocation: $(appended)")
    println("Appended $(appended) records to $(HISTORY_PATH)")
    println("History line count: $(total_lines)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
