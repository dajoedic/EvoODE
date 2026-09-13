using LinearAlgebra

const PHASE_C_ID = "paper1_phaseC_v1"
const PHASE_C_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "phase_c")
const PHASE_C_MANIFEST_PATH = joinpath(PHASE_C_OUTPUT_DIR, "manifest.csv")
const PHASE_C_HISTORY_PATH = joinpath(PHASE_C_OUTPUT_DIR, "history.jsonl")
const PHASE_C_TASK_OUTPUT_DIR = joinpath(PHASE_C_OUTPUT_DIR, "tasks")
const PHASE_C_SEEDS = REGRESSION_SEEDS
const PHASE_C_IC_SETS = REGRESSION_IC_SETS
const PHASE_C_TSPAN = REGRESSION_TSPAN
const PHASE_C_T = REGRESSION_T
const PHASE_C_BASIS_NAME = "staged_polynomial_basis_with_constant"
const PHASE_C_MAX_FIT_ATTEMPTS = 3
const PHASE_C_SUPPORT_PATH = joinpath(@__DIR__, "phase_c_support.json")

function load_phase_c_support()
    isfile(PHASE_C_SUPPORT_PATH) ||
        error("Missing $(PHASE_C_SUPPORT_PATH); run studies/regression/derive_phase_b_support.jl --basis $(PHASE_C_BASIS_NAME) --output $(PHASE_C_SUPPORT_PATH)")
    raw = JSON3.read(read(PHASE_C_SUPPORT_PATH, String))
    haskey(raw, "basis_name") || error("$(PHASE_C_SUPPORT_PATH) does not declare basis_name")
    String(raw["basis_name"]) == PHASE_C_BASIS_NAME ||
        error("$(PHASE_C_SUPPORT_PATH) basis_name=$(raw["basis_name"]) but Phase C requires $(PHASE_C_BASIS_NAME)")

    table = Dict{Int, Any}()
    for e in raw["systems"]
        idxs = e["support_idxs"]
        table[Int(e["system_id"])] = (
            representability = String(e["representability"]),
            status = String(e["status"]),
            support = idxs === nothing ? nothing : [Int[Int(i) for i in eq] for eq in idxs],
        )
    end
    return table
end

function phase_c_basis(dim::Int)
    return staged_polynomial_basis_with_constant(dim)
end

function phase_c_stage_for_term_idx(basis::StagedPolynomialBasis, term_idx::Int)
    for (stage, terms) in enumerate(basis.term_groups)
        term_idx in terms && return stage
    end
    error("Term index $(term_idx) is not present in staged basis")
end

function phase_c_expected_stage_from_support(dim::Int, support)
    support === nothing && return nothing
    basis = phase_c_basis(dim)
    stages = Int[]
    for eq_support in support
        append!(stages, phase_c_stage_for_term_idx.(Ref(basis), eq_support))
    end
    isempty(stages) && error("Cannot derive expected_stage from empty support")
    return maximum(stages)
end

function _phase_c_dataset_rows()
    raw = JSON3.read(read(REGRESSION_DATA_PATH, String))
    return sort(collect(raw); by = row -> Int(row["id"]))
end

function _phase_c_normalize_expr(text::AbstractString)
    return replace(String(text), "**" => "^")
end

function _phase_c_eval_expr(expr, u, t)
    expr isa Integer && return Float64(expr)
    expr isa AbstractFloat && return Float64(expr)
    expr isa Rational && return Float64(expr)
    if expr isa Symbol
        name = String(expr)
        name == "t" && return Float64(t)
        if startswith(name, "x_")
            return Float64(u[parse(Int, name[3:end]) + 1])
        end
        error("Unsupported Phase C symbol: $(name)")
    end
    expr isa Expr || error("Unsupported Phase C expression node: $(expr)")
    expr.head == :call || error("Unsupported Phase C expression head: $(expr.head)")

    op = expr.args[1]
    args = expr.args[2:end]
    if op == :+
        return sum(_phase_c_eval_expr(arg, u, t) for arg in args)
    elseif op == :-
        length(args) == 1 && return -_phase_c_eval_expr(args[1], u, t)
        value = _phase_c_eval_expr(args[1], u, t)
        for arg in args[2:end]
            value -= _phase_c_eval_expr(arg, u, t)
        end
        return value
    elseif op == :*
        value = 1.0
        for arg in args
            value *= _phase_c_eval_expr(arg, u, t)
        end
        return value
    elseif op == :/
        length(args) == 2 || error("Unsupported Phase C division arity: $(length(args))")
        return _phase_c_eval_expr(args[1], u, t) / _phase_c_eval_expr(args[2], u, t)
    elseif op == :^
        length(args) == 2 || error("Unsupported Phase C power arity: $(length(args))")
        return _phase_c_eval_expr(args[1], u, t) ^ _phase_c_eval_expr(args[2], u, t)
    elseif op == :sin
        return sin(_phase_c_eval_expr(args[1], u, t))
    elseif op == :cos
        return cos(_phase_c_eval_expr(args[1], u, t))
    elseif op == :tan
        return tan(_phase_c_eval_expr(args[1], u, t))
    elseif op == :cot
        return cot(_phase_c_eval_expr(args[1], u, t))
    elseif op == :exp
        return exp(_phase_c_eval_expr(args[1], u, t))
    elseif op == :log
        return log(_phase_c_eval_expr(args[1], u, t))
    elseif op == :sqrt
        return sqrt(_phase_c_eval_expr(args[1], u, t))
    elseif op == :abs || op == :Abs
        return abs(_phase_c_eval_expr(args[1], u, t))
    end
    error("Unsupported Phase C operator: $(op)")
end

function _phase_c_rhs_function(exprs::Vector{String})
    parsed = [Meta.parse(_phase_c_normalize_expr(expr)) for expr in exprs]
    return function (du, u, _, t)
        @inbounds for eq in eachindex(parsed)
            du[eq] = _phase_c_eval_expr(parsed[eq], u, t)
        end
        return nothing
    end
end

function _phase_c_solution_trajectory(row, ic_set::Int)
    solution = row["solutions"][1][ic_set]
    t = Float64[x for x in solution["t"]]
    y_rows = [Float64[x for x in state] for state in solution["y"]]
    x = reduce(hcat, y_rows)
    return Trajectory(t, Matrix{Float64}(x))
end

function phase_c_systems()
    systems = Dict{Symbol, Any}[]
    support_table = load_phase_c_support()
    for row in _phase_c_dataset_rows()
        system_id = Int(row["id"])
        dim = Int(row["dim"])
        protocol = REGRESSION_PROTOCOL_BY_ID[system_id]
        init_sets = protocol.init_sets
        length(init_sets) >= maximum(PHASE_C_IC_SETS) ||
            error("Phase C system $(system_id) has fewer IC sets than requested")
        exprs = [String(expr) for expr in row["substituted"][1]]
        length(exprs) == dim || error("Phase C system $(system_id) dim/RHS mismatch")
        rhs! = _phase_c_rhs_function(exprs)
        reference_traj = _phase_c_solution_trajectory(row, first(PHASE_C_IC_SETS))
        protocol.t_grid == reference_traj.t || error("Phase C system $(system_id) protocol time grid mismatch")
        length(reference_traj.t) == PHASE_C_T || error("Phase C system $(system_id) unexpected T")
        haskey(support_table, system_id) ||
            error("Phase C system $(system_id) missing from $(PHASE_C_SUPPORT_PATH); regenerate it")
        support_entry = support_table[system_id]
        expected_stage = phase_c_expected_stage_from_support(dim, support_entry.support)
        push!(
            systems,
            Dict{Symbol, Any}(
                :system_id => system_id,
                :system_name => String(row["eq_description"]),
                :dim => dim,
                :init_sets => init_sets,
                :t_grid => protocol.t_grid,
                :tspan => PHASE_C_TSPAN,
                :T => PHASE_C_T,
                :expected_stage => expected_stage,
                :rhs! => rhs!,
                :representability => support_entry.representability,
                :expected_support => support_entry.support,
                :equations => exprs,
            ),
        )
    end
    return systems
end

const PHASE_C_SYSTEMS = phase_c_systems()

const PHASE_C_VARIANTS = [
    (
        label = "evogrow_v2_2_stage_capped",
        condition = "capped",
        use_pretuning = false,
        basis_name = PHASE_C_BASIS_NAME,
        max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
        constructor = (level_callback, screening_optimizer) -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = false,
            screening_optimizer = screening_optimizer,
            level_callback = level_callback,
            stage_cap_policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...),
        ),
    ),
    (
        label = "evogrow_v2_2_stage_local",
        condition = "uncapped",
        use_pretuning = false,
        basis_name = PHASE_C_BASIS_NAME,
        max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
        constructor = (level_callback, screening_optimizer) -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = false,
            screening_optimizer = screening_optimizer,
            level_callback = level_callback,
        ),
    ),
    (
        label = "evogrow_v2_2_stage_capped_pretune_on",
        condition = "pretune_on",
        use_pretuning = true,
        basis_name = PHASE_C_BASIS_NAME,
        max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
        constructor = (level_callback, screening_optimizer) -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = true,
            screening_optimizer = screening_optimizer,
            level_callback = level_callback,
            stage_cap_policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...),
        ),
    ),
]

function phase_c_validate_variants()
    for variant in PHASE_C_VARIANTS
        haskey(variant, :basis_name) ||
            error("Phase C variant $(variant.label) is missing explicit basis_name")
        String(variant.basis_name) == PHASE_C_BASIS_NAME ||
            error("Phase C variant $(variant.label) basis_name=$(variant.basis_name), expected $(PHASE_C_BASIS_NAME)")
    end
    return nothing
end

phase_c_validate_variants()

function phase_c_fingerprint()
    system_payload = [
        (
            system_id = Int(system[:system_id]),
            dim = Int(system[:dim]),
            init_sets = [Float64[x for x in init] for init in system[:init_sets]],
            t_grid = Float64[t for t in system[:t_grid]],
            tspan = system[:tspan],
            T = Int(system[:T]),
            expected_stage = system[:expected_stage] === nothing ? nothing : Int(system[:expected_stage]),
            representability = String(system[:representability]),
            expected_support = system[:expected_support] === nothing ? nothing :
                               [Int[i for i in eq] for eq in system[:expected_support]],
            equations = [String(expr) for expr in system[:equations]],
        )
        for system in sort(PHASE_C_SYSTEMS; by = s -> Int(s[:system_id]))
    ]
    payload = (
        campaign = PHASE_C_ID,
        basis_name = PHASE_C_BASIS_NAME,
        system_ids = sort([Int(system[:system_id]) for system in PHASE_C_SYSTEMS]),
        initial_condition_sets = PHASE_C_IC_SETS,
        systems = system_payload,
        seeds = PHASE_C_SEEDS,
        pop_size = POP_SIZE,
        n_levels = N_LEVELS,
        children_per_parent = CHILDREN_PER_PARENT,
        max_terms_per_eq = MAX_TERMS,
        lambda = LAMBDA,
        min_levels_per_stage = STAGE_MIN,
        new_term_bias_prob = SOFT_BIAS,
        bfgs_maxiters = BFGS_MAXITERS,
        bfgs_abstol = BFGS_ABSTOL,
        bfgs_reltol = BFGS_RELTOL,
        bfgs_maxiters_solve = BFGS_MAXITERS_SOLVE,
        bfgs_max_loss_evals = BFGS_MAX_LOSS_EVALS,
        bfgs_clamp_val = BFGS_CLAMP_VAL,
        bfgs_time_limit_s = BFGS_TIME_LIMIT_S,
        bfgs_reject_nonfinite = BFGS_REJECT_NONFINITE,
        bfgs_divergence_limit = BFGS_DIVERGENCE_LIMIT,
        bfgs_max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
        screening_budgets_enabled = SCREENING_BUDGETS_ENABLED,
        screening_bfgs_abstol = SCREENING_BFGS_ABSTOL,
        screening_bfgs_reltol = SCREENING_BFGS_RELTOL,
        screening_bfgs_maxiters_solve = SCREENING_BFGS_MAXITERS_SOLVE,
        screening_bfgs_max_loss_evals = SCREENING_BFGS_MAX_LOSS_EVALS,
        screening_bfgs_clamp_val = SCREENING_BFGS_CLAMP_VAL,
        screening_bfgs_time_limit_s = SCREENING_BFGS_TIME_LIMIT_S,
        screening_reject_nonfinite = SCREENING_REJECT_NONFINITE,
        screening_divergence_limit = SCREENING_DIVERGENCE_LIMIT,
        variants = [
            (
                label = String(variant.label),
                condition = String(variant.condition),
                use_pretuning = Bool(variant.use_pretuning),
                basis_name = String(variant.basis_name),
                max_fit_attempts = Int(variant.max_fit_attempts),
            )
            for variant in PHASE_C_VARIANTS
        ],
        derivative_screen_k = DERIVATIVE_SCREEN_K,
        derivative_polish_maxiters = DERIVATIVE_POLISH_MAXITERS,
        derivative_rejected_diagnostic_samples = DERIVATIVE_REJECTED_DIAGNOSTIC_SAMPLES,
        lookahead_stage_cap = (
            variant = "evogrow_v2_2_stage_capped",
            estimator = String(LOOKAHEAD_CAP_POLICY.estimator),
            weighting = String(LOOKAHEAD_CAP_POLICY.weighting),
            aggregation = String(LOOKAHEAD_CAP_POLICY.aggregation),
            lookahead_horizon = LOOKAHEAD_CAP_POLICY.lookahead_horizon,
            tau_rel = LOOKAHEAD_CAP_POLICY.tau_rel,
            tau_abs = LOOKAHEAD_CAP_POLICY.tau_abs,
            cond_cap = LOOKAHEAD_CAP_POLICY.cond_cap,
            excitation_floor = LOOKAHEAD_CAP_POLICY.excitation_floor,
            post_floor_significant_drop_ratio = LOOKAHEAD_CAP_POLICY.post_floor_significant_drop_ratio,
            post_floor_min_floor_ratio = LOOKAHEAD_CAP_POLICY.post_floor_min_floor_ratio,
        ),
        discovery_options = OPTIONS_CONFIG,
        trajectory_solver = (
            algorithm = "Tsit5",
            saveat = "dataset solutions[1][1].t grid; shipped y ignored",
            abstol = 1e-9,
            reltol = 1e-9,
        ),
        metrics = (
            loss = "MSELoss",
            r2 = "per-dimension coefficient of determination on final simulated trajectory, arithmetic mean across dimensions",
            exact_support_match = "support_match_pruned for exact systems only",
            expected_stage = "derived from phase_c_support support_idxs and staged basis term_groups for exact systems; nothing for surrogate systems",
            executed_levels = "sum of executed stage_level_counts from the search meta; distinct from configured n_levels",
        ),
    )
    bytes = sha256(codeunits(canonical_value(payload)))
    return bytes2hex(bytes)[1:16]
end

function phase_c_variant(label::String)
    matches = [variant for variant in PHASE_C_VARIANTS if String(variant.label) == label]
    isempty(matches) && error("Unknown Phase C variant in manifest: $(label)")
    return matches[1]
end

function phase_c_system(system_id::Int)
    matches = [system for system in PHASE_C_SYSTEMS if Int(system[:system_id]) == system_id]
    isempty(matches) && error("Unknown Phase C system_id in manifest: $(system_id)")
    return matches[1]
end

function phase_c_exact_systems()
    return [system for system in PHASE_C_SYSTEMS if String(system[:representability]) == "exact"]
end

function phase_c_representability_counts()
    return Dict(label => count(system -> system[:representability] == label, PHASE_C_SYSTEMS) for label in ("exact", "surrogate"))
end
