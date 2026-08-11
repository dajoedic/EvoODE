using LinearAlgebra

const PHASE_B_ID = "phase_b"
const PHASE_B_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "phase_b")
const PHASE_B_MANIFEST_PATH = joinpath(PHASE_B_OUTPUT_DIR, "manifest.csv")
const PHASE_B_HISTORY_PATH = joinpath(PHASE_B_OUTPUT_DIR, "history.jsonl")
const PHASE_B_TASK_OUTPUT_DIR = joinpath(PHASE_B_OUTPUT_DIR, "tasks")
const PHASE_B_SEEDS = REGRESSION_SEEDS
const PHASE_B_IC_SETS = REGRESSION_IC_SETS
const PHASE_B_TSPAN = REGRESSION_TSPAN
const PHASE_B_T = REGRESSION_T
const PHASE_B_REPRESENTABILITY_RTOL = 1e-8
const PHASE_B_REPRESENTABILITY_ATOL = 1e-10

function _phase_b_dataset_rows()
    raw = JSON3.read(read(REGRESSION_DATA_PATH, String))
    return sort(collect(raw); by = row -> Int(row["id"]))
end

function _phase_b_normalize_expr(text::AbstractString)
    return replace(String(text), "**" => "^")
end

function _phase_b_eval_expr(expr, u, t)
    expr isa Integer && return Float64(expr)
    expr isa AbstractFloat && return Float64(expr)
    expr isa Rational && return Float64(expr)
    if expr isa Symbol
        name = String(expr)
        name == "t" && return Float64(t)
        if startswith(name, "x_")
            return Float64(u[parse(Int, name[3:end]) + 1])
        end
        error("Unsupported Phase B symbol: $(name)")
    end
    expr isa Expr || error("Unsupported Phase B expression node: $(expr)")
    expr.head == :call || error("Unsupported Phase B expression head: $(expr.head)")

    op = expr.args[1]
    args = expr.args[2:end]
    if op == :+
        return sum(_phase_b_eval_expr(arg, u, t) for arg in args)
    elseif op == :-
        length(args) == 1 && return -_phase_b_eval_expr(args[1], u, t)
        value = _phase_b_eval_expr(args[1], u, t)
        for arg in args[2:end]
            value -= _phase_b_eval_expr(arg, u, t)
        end
        return value
    elseif op == :*
        value = 1.0
        for arg in args
            value *= _phase_b_eval_expr(arg, u, t)
        end
        return value
    elseif op == :/
        length(args) == 2 || error("Unsupported Phase B division arity: $(length(args))")
        return _phase_b_eval_expr(args[1], u, t) / _phase_b_eval_expr(args[2], u, t)
    elseif op == :^
        length(args) == 2 || error("Unsupported Phase B power arity: $(length(args))")
        return _phase_b_eval_expr(args[1], u, t) ^ _phase_b_eval_expr(args[2], u, t)
    elseif op == :sin
        return sin(_phase_b_eval_expr(args[1], u, t))
    elseif op == :cos
        return cos(_phase_b_eval_expr(args[1], u, t))
    elseif op == :tan
        return tan(_phase_b_eval_expr(args[1], u, t))
    elseif op == :cot
        return cot(_phase_b_eval_expr(args[1], u, t))
    elseif op == :exp
        return exp(_phase_b_eval_expr(args[1], u, t))
    elseif op == :log
        return log(_phase_b_eval_expr(args[1], u, t))
    elseif op == :sqrt
        return sqrt(_phase_b_eval_expr(args[1], u, t))
    elseif op == :abs || op == :Abs
        return abs(_phase_b_eval_expr(args[1], u, t))
    end
    error("Unsupported Phase B operator: $(op)")
end

function _phase_b_rhs_function(exprs::Vector{String})
    parsed = [Meta.parse(_phase_b_normalize_expr(expr)) for expr in exprs]
    return function (du, u, _, t)
        @inbounds for eq in eachindex(parsed)
            du[eq] = _phase_b_eval_expr(parsed[eq], u, t)
        end
        return nothing
    end
end

function _phase_b_solution_trajectory(row, ic_set::Int)
    solution = row["solutions"][1][ic_set]
    t = Float64[x for x in solution["t"]]
    y_rows = [Float64[x for x in state] for state in solution["y"]]
    x = reduce(hcat, y_rows)
    return Trajectory(t, Matrix{Float64}(x))
end

function _phase_b_design_matrix(traj::Trajectory, basis)
    n = length(traj.t)
    p = basis_num_terms(basis)
    phi = zeros(Float64, n, p)
    @inbounds for row in 1:n
        u = view(traj.x, row, :)
        t = traj.t[row]
        for col in 1:p
            phi[row, col] = basis_term_func(basis, col)(u, t)
        end
    end
    return phi
end

function _phase_b_rhs_matrix(rhs!, traj::Trajectory)
    n, dim = size(traj.x)
    out = zeros(Float64, n, dim)
    du = zeros(Float64, dim)
    @inbounds for row in 1:n
        rhs!(du, view(traj.x, row, :), nothing, traj.t[row])
        out[row, :] .= du
    end
    return out
end

function _phase_b_representability(rhs!, traj::Trajectory)
    dim = size(traj.x, 2)
    basis = default_staged_polynomial_basis(dim)
    phi = _phase_b_design_matrix(traj, basis)
    rhs = _phase_b_rhs_matrix(rhs!, traj)
    all(isfinite, phi) || return "surrogate"
    all(isfinite, rhs) || return "surrogate"
    for eq in 1:dim
        target = rhs[:, eq]
        coefs = phi \ target
        residual = LinearAlgebra.norm(phi * coefs - target)
        tolerance = PHASE_B_REPRESENTABILITY_ATOL + PHASE_B_REPRESENTABILITY_RTOL * max(LinearAlgebra.norm(target), 1.0)
        residual <= tolerance || return "surrogate"
    end
    return "exact"
end

function phase_b_systems()
    systems = Dict{Symbol, Any}[]
    for row in _phase_b_dataset_rows()
        system_id = Int(row["id"])
        dim = Int(row["dim"])
        protocol = REGRESSION_PROTOCOL_BY_ID[system_id]
        init_sets = protocol.init_sets
        length(init_sets) >= maximum(PHASE_B_IC_SETS) ||
            error("Phase B system $(system_id) has fewer IC sets than requested")
        exprs = [String(expr) for expr in row["substituted"][1]]
        length(exprs) == dim || error("Phase B system $(system_id) dim/RHS mismatch")
        rhs! = _phase_b_rhs_function(exprs)
        reference_traj = _phase_b_solution_trajectory(row, first(PHASE_B_IC_SETS))
        protocol.t_grid == reference_traj.t || error("Phase B system $(system_id) protocol time grid mismatch")
        length(reference_traj.t) == PHASE_B_T || error("Phase B system $(system_id) unexpected T")
        push!(
            systems,
            Dict{Symbol, Any}(
                :system_id => system_id,
                :system_name => String(row["eq_description"]),
                :dim => dim,
                :init_sets => init_sets,
                :t_grid => protocol.t_grid,
                :tspan => PHASE_B_TSPAN,
                :T => PHASE_B_T,
                :expected_stage => nothing,
                :rhs! => rhs!,
                :representability => _phase_b_representability(rhs!, reference_traj),
                :equations => exprs,
            ),
        )
    end
    return systems
end

const PHASE_B_SYSTEMS = phase_b_systems()

const PHASE_B_VARIANTS = [
    (
        label = "evogrow_v2_2_stage_capped_pretune_on",
        condition = "pretune_on",
        use_pretuning = true,
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
    (
        label = "evogrow_v2_2_stage_capped_pretune_off",
        condition = "pretune_off",
        use_pretuning = false,
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
]

function phase_b_fingerprint()
    system_payload = [
        (
            system_id = Int(system[:system_id]),
            dim = Int(system[:dim]),
            init_sets = [Float64[x for x in init] for init in system[:init_sets]],
            t_grid = Float64[t for t in system[:t_grid]],
            tspan = system[:tspan],
            T = Int(system[:T]),
            expected_stage = nothing,
            representability = String(system[:representability]),
            equations = [String(expr) for expr in system[:equations]],
        )
        for system in sort(PHASE_B_SYSTEMS; by = s -> Int(s[:system_id]))
    ]
    payload = (
        campaign = PHASE_B_ID,
        system_ids = sort([Int(system[:system_id]) for system in PHASE_B_SYSTEMS]),
        initial_condition_sets = PHASE_B_IC_SETS,
        systems = system_payload,
        seeds = PHASE_B_SEEDS,
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
            (label = String(variant.label), condition = String(variant.condition), use_pretuning = Bool(variant.use_pretuning))
            for variant in PHASE_B_VARIANTS
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

function phase_b_variant(label::String)
    matches = [variant for variant in PHASE_B_VARIANTS if String(variant.label) == label]
    isempty(matches) && error("Unknown Phase B variant in manifest: $(label)")
    return matches[1]
end

function phase_b_system(system_id::Int)
    matches = [system for system in PHASE_B_SYSTEMS if Int(system[:system_id]) == system_id]
    isempty(matches) && error("Unknown Phase B system_id in manifest: $(system_id)")
    return matches[1]
end

function phase_b_representability_counts()
    return Dict(label => count(system -> system[:representability] == label, PHASE_B_SYSTEMS) for label in ("exact", "surrogate"))
end
