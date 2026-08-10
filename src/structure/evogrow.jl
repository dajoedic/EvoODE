# src/structure/evogrow.jl

using Random
using Printf

"""
Controls how EvoGrow decides when to remain in a stage, promote, or stop.

Modes:
- `:global_plateau`: current v2.1 behavior using global objective history
- `:stage_local`: v2.2 behavior with per-stage history and minimum stage budget
"""
Base.@kwdef struct StageProgressionPolicy
    mode::Symbol = :global_plateau
    min_levels_per_stage::Int = 2
end

"""
Controls how EvoGrow encourages usage of newly unlocked stage terms.

Modes:
- `:hard`: always try to insert a current-stage term when possible
- `:passive`: no special treatment after stage unlock
- `:soft`: probabilistic bias toward current-stage terms
"""
Base.@kwdef struct StageUsagePolicy
    mode::Symbol = :hard
    new_term_bias_prob::Float64 = 0.75
end

"""
EvoGrow structure search strategy.

- pop_size: population size
- n_levels: maximum total search levels
- children_per_parent: number of children sampled per parent per level
- max_terms_per_eq: maximum number of active terms per equation
- λ: complexity penalty (objective = loss + λ * n_params)
- progression: stage progression policy
- usage: stage usage policy

Version note:
- v1: flat growth over all terms
- v2.1: global plateau + hard stage-aware child generation
- v2.2: stage-local plateau + configurable usage policy
"""
Base.@kwdef struct EvoGrow <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
    progression::StageProgressionPolicy = StageProgressionPolicy()
    usage::StageUsagePolicy = StageUsagePolicy()
    use_pretuning::Bool = true
    screening_optimizer::Union{Nothing, AbstractOptimizer} = nothing
    level_callback::Union{Nothing, Function} = nothing
    stage_caps::Union{Nothing,Vector{Union{Nothing,Int}}} = nothing
    stage_cap_policy::Union{Nothing,LookAheadStageCapPolicy} = nothing
end

"""
Individual in the EvoGrow population.
"""
mutable struct Individual
    structure::StructureSpec
    params::Vector{Float64}
    loss::Float64
    objective::Float64
end

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

function _validate_policy(strategy::EvoGrow)
    if !(strategy.progression.mode in (:global_plateau, :stage_local))
        error("Unsupported StageProgressionPolicy.mode=$(strategy.progression.mode)")
    end
    if strategy.progression.min_levels_per_stage < 1
        error("StageProgressionPolicy.min_levels_per_stage must be >= 1")
    end
    if !(strategy.usage.mode in (:hard, :passive, :soft))
        error("Unsupported StageUsagePolicy.mode=$(strategy.usage.mode)")
    end
    if !(0.0 <= strategy.usage.new_term_bias_prob <= 1.0)
        error("StageUsagePolicy.new_term_bias_prob must lie in [0, 1]")
    end
    return nothing
end

"""
    _allowed_terms(basis::StagedPolynomialBasis, stage::Int)

Return all basis term indices that are unlocked up to and including `stage`.
"""
function _allowed_terms(basis::StagedPolynomialBasis, stage::Int)
    return vcat(basis.term_groups[1:stage]...)
end

"""
    _current_stage_terms(basis::StagedPolynomialBasis, stage::Int)

Return only the term indices introduced in the current stage.
"""
function _current_stage_terms(basis::StagedPolynomialBasis, stage::Int)
    return basis.term_groups[stage]
end

"""
    _max_stage(basis::StagedPolynomialBasis)

Number of stages in the staged basis.
"""
_max_stage(basis::StagedPolynomialBasis) = length(basis.term_groups)

"""
Fallback for non-staged bases: all terms are available immediately.
This keeps EvoGrow v1-compatible.
"""
function _allowed_terms(basis::AbstractBasis, _::Int)
    return collect(1:basis_num_terms(basis))
end

function _current_stage_terms(basis::AbstractBasis, _::Int)
    return collect(1:basis_num_terms(basis))
end

_max_stage(basis::AbstractBasis) = 1

function _validate_stage_caps(stage_caps, dim::Int, max_stage::Int)
    stage_caps === nothing && return nothing
    length(stage_caps) == dim || error("stage_caps length $(length(stage_caps)) does not match trajectory dimension $(dim)")
    for (k, cap) in enumerate(stage_caps)
        cap === nothing && continue
        1 <= Int(cap) <= max_stage || error("stage_caps[$k]=$(cap) must lie in 1:$max_stage")
    end
    return nothing
end

function _effective_max_stage(max_stage::Int, stage_caps)
    stage_caps === nothing && return max_stage
    isempty(stage_caps) && return max_stage
    return maximum(cap === nothing ? max_stage : Int(cap) for cap in stage_caps)
end

function _effective_eq_stages(current_stage::Int, max_stage::Int, stage_caps, dim::Int)
    stage_caps === nothing && return fill(current_stage, dim)
    return [
        min(current_stage, cap === nothing ? max_stage : Int(cap))
        for cap in stage_caps
    ]
end

"""
    _allowed_term_names(basis, allowed_terms)

Pretty names for currently unlocked basis terms.
"""
function _allowed_term_names(basis::AbstractBasis, allowed_terms::Vector{Int})
    return [basis_term_name(basis, i) for i in allowed_terms]
end

function _structure_uses_terms(structure::StructureSpec, term_idxs::Vector{Int})
    term_set = Set(term_idxs)
    for eq_terms in structure.active_idxs
        for term_idx in eq_terms
            if term_idx in term_set
                return true
            end
        end
    end
    return false
end

function _plateau_reached(best_J_hist::Vector{Float64},
                          plateau_window::Int,
                          plateau_tol::Float64,
                          plateau_relative::Bool,
                          plateau_rtol::Float64)

    if length(best_J_hist) < plateau_window + 1
        return false, :insufficient_history
    end

    J_old = best_J_hist[end - plateau_window]
    J_new = best_J_hist[end]
    delta = J_old - J_new

    if plateau_relative
        denom = max(abs(J_old), eps())
        if delta / denom < plateau_rtol
            return true, :plateau_relative
        end
    else
        if delta < plateau_tol
            return true, :plateau_absolute
        end
    end

    return false, :continue
end

function _stage_progression_decision(strategy::EvoGrow,
                                     stage_best_J_hist::Vector{Float64},
                                     stage_level_count::Int,
                                     best_loss::Float64,
                                     current_stage::Int,
                                     max_stage::Int,
                                     level::Int,
                                     n_steps::Int,
                                     options::DiscoveryOptions)

    if level >= n_steps
        return true, :max_levels, :stop
    end

    if best_loss < options.loss_tol
        return true, :loss_tol, :stop
    end

    if stage_level_count < strategy.progression.min_levels_per_stage
        return false, :stage_budget, :stay
    end

    plateau, reason = _plateau_reached(
        stage_best_J_hist,
        options.plateau_window,
        options.plateau_tol,
        options.plateau_relative,
        options.plateau_rtol
    )

    if !plateau
        return false, reason, :stay
    end

    if current_stage < max_stage
        return true, reason, :promote
    end

    return true, reason, :stop
end

# ------------------------------------------------------------
# Initialization
# ------------------------------------------------------------

function _init_population(strategy::EvoGrow, dim::Int, allowed_terms::Vector{Int})
    pop = Individual[]
    for _ in 1:strategy.pop_size
        active = Vector{Vector{Int}}(undef, dim)
        for k in 1:dim
            active[k] = [rand(allowed_terms)]
        end
        push!(pop, Individual(StructureSpec(active), Float64[], Inf, Inf))
    end
    return pop
end

# ------------------------------------------------------------
# Expansion
# ------------------------------------------------------------

"""
    _expand(ind, dim, allowed_terms; ...)

Standard growth:
- add one random allowed term to one random equation
"""
function _expand(ind::Individual,
                 dim::Int,
                 allowed_terms::Vector{Int};
                 n_children::Int,
                 max_terms_per_eq::Int)

    children = Individual[]

    for _ in 1:n_children
        new_idxs = [copy(v) for v in ind.structure.active_idxs]
        k = rand(1:dim)

        existing = new_idxs[k]
        candidates = setdiff(allowed_terms, existing)

        if !isempty(candidates) && length(existing) < max_terms_per_eq
            push!(new_idxs[k], rand(candidates))
            new_idxs[k] = sort!(unique(new_idxs[k]))
        end

        push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
    end

    return children
end

"""
    _expand_stage_aware(ind, dim, allowed_terms, new_stage_terms; ...)

Hard stage-aware growth:
- tries to add at least one term from `new_stage_terms`
- if impossible, falls back to standard allowed-term expansion
"""
function _expand_stage_aware(ind::Individual,
                             dim::Int,
                             allowed_terms::Vector{Int},
                             new_stage_terms::Vector{Int};
                             n_children::Int,
                             max_terms_per_eq::Int)

    children = Individual[]

    for _ in 1:n_children
        new_idxs = [copy(v) for v in ind.structure.active_idxs]

        growable_eqs = [k for k in 1:dim if length(new_idxs[k]) < max_terms_per_eq]

        if isempty(growable_eqs)
            push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
            continue
        end

        eqs_with_new_terms = Int[]
        for k in growable_eqs
            existing = new_idxs[k]
            candidates_new = setdiff(new_stage_terms, existing)
            if !isempty(candidates_new)
                push!(eqs_with_new_terms, k)
            end
        end

        if !isempty(eqs_with_new_terms)
            k = rand(eqs_with_new_terms)
            existing = new_idxs[k]
            candidates_new = setdiff(new_stage_terms, existing)

            push!(new_idxs[k], rand(candidates_new))
            new_idxs[k] = sort!(unique(new_idxs[k]))
        else
            k = rand(growable_eqs)
            existing = new_idxs[k]
            candidates = setdiff(allowed_terms, existing)

            if !isempty(candidates)
                push!(new_idxs[k], rand(candidates))
                new_idxs[k] = sort!(unique(new_idxs[k]))
            end
        end

        push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
    end

    return children
end

"""
    _expand_stage_soft(ind, dim, allowed_terms, new_stage_terms; ...)

Soft stage-aware growth:
- biases child generation toward current-stage terms with probability `bias_prob`
- otherwise falls back to passive expansion
"""
function _expand_stage_soft(ind::Individual,
                            dim::Int,
                            allowed_terms::Vector{Int},
                            new_stage_terms::Vector{Int};
                            n_children::Int,
                            max_terms_per_eq::Int,
                            bias_prob::Float64)

    children = Individual[]

    for _ in 1:n_children
        new_idxs = [copy(v) for v in ind.structure.active_idxs]

        growable_eqs = [k for k in 1:dim if length(new_idxs[k]) < max_terms_per_eq]
        if isempty(growable_eqs)
            push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
            continue
        end

        try_new_stage = rand() < bias_prob

        if try_new_stage
            eqs_with_new_terms = Int[]
            for k in growable_eqs
                existing = new_idxs[k]
                candidates_new = setdiff(new_stage_terms, existing)
                if !isempty(candidates_new)
                    push!(eqs_with_new_terms, k)
                end
            end

            if !isempty(eqs_with_new_terms)
                k = rand(eqs_with_new_terms)
                existing = new_idxs[k]
                candidates_new = setdiff(new_stage_terms, existing)
                push!(new_idxs[k], rand(candidates_new))
                new_idxs[k] = sort!(unique(new_idxs[k]))

                push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
                continue
            end
        end

        k = rand(growable_eqs)
        existing = new_idxs[k]
        candidates = setdiff(allowed_terms, existing)

        if !isempty(candidates)
            push!(new_idxs[k], rand(candidates))
            new_idxs[k] = sort!(unique(new_idxs[k]))
        end

        push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
    end

    return children
end

function _expand_with_usage_policy(ind::Individual,
                                   dim::Int,
                                   allowed_terms::Vector{Int},
                                   current_stage_terms::Vector{Int},
                                   usage::StageUsagePolicy;
                                   n_children::Int,
                                   max_terms_per_eq::Int)

    if usage.mode == :passive || current_stage_terms == allowed_terms
        return _expand(
            ind,
            dim,
            allowed_terms;
            n_children = n_children,
            max_terms_per_eq = max_terms_per_eq
        )
    elseif usage.mode == :hard
        return _expand_stage_aware(
            ind,
            dim,
            allowed_terms,
            current_stage_terms;
            n_children = n_children,
            max_terms_per_eq = max_terms_per_eq
        )
    else
        return _expand_stage_soft(
            ind,
            dim,
            allowed_terms,
            current_stage_terms;
            n_children = n_children,
            max_terms_per_eq = max_terms_per_eq,
            bias_prob = usage.new_term_bias_prob
        )
    end
end

# ------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------

function _evaluate!(ind::Individual,
                    traj::Trajectory,
                    basis::AbstractBasis,
                    loss::AbstractLoss,
                    optimizer::AbstractOptimizer,
                    λ::Float64,
                    options::DiscoveryOptions,
                    use_pretuning::Bool)

    f!, n_params, _ = build_rhs(ind.structure, basis)
    p0 = use_pretuning ? pretune_parameters(ind.structure, basis, traj) : nothing
    params, lval, fit_meta = fit_parameters(optimizer, f!, traj, n_params, loss, options; p0 = p0)

    ind.params = params
    ind.loss = lval
    ind.objective = lval + λ * length(params)
    return ind, fit_meta
end

function _fit_stat(fit_meta, key::Symbol)
    return haskey(fit_meta, key) ? getfield(fit_meta, key) : 0
end

function _fit_time_stat(fit_meta, key::Symbol)
    return Float64(haskey(fit_meta, key) ? getfield(fit_meta, key) : 0.0)
end

function _fit_string_is(fit_meta, key::Symbol, expected::String)
    haskey(fit_meta, key) || return 0
    return String(getfield(fit_meta, key)) == expected ? 1 : 0
end

function _fit_bool_is(fit_meta, key::Symbol, expected::Bool)
    haskey(fit_meta, key) || return 0
    return Bool(getfield(fit_meta, key)) == expected ? 1 : 0
end

function _fit_fallback_optimizer_return(fit_meta)
    return _fit_string_is(fit_meta, :method, "NelderMead") == 1 &&
           _fit_string_is(fit_meta, :result_source, "optimizer_return") == 1 ? 1 : 0
end

function _append_unique_strings!(target::Vector{String}, values)
    for value in values
        text = String(value)
        if !(text in target)
            push!(target, text)
        end
    end
    return nothing
end

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------

"""
    search_structure(strategy::EvoGrow, traj, basis, loss, optimizer, options)

Incremental evolutionary growth with configurable stage progression and
stage usage policies.

Returns:
- `structure`: best found `StructureSpec`
- `params`: best fitted parameters
- `loss`: best loss
- `objective`: best objective
- `meta`: diagnostics and pretty-print string
"""
function search_structure(strategy::EvoGrow,
                          traj::Trajectory,
                          basis::AbstractBasis,
                          loss::AbstractLoss,
                          optimizer::AbstractOptimizer,
                          options::DiscoveryOptions)

    _validate_policy(strategy)

    dim = size(traj.x, 2)

    current_stage = 1
    basis_max_stage = _max_stage(basis)
    stage_caps = strategy.stage_caps
    if stage_caps === nothing && strategy.stage_cap_policy !== nothing
        stage_caps = estimate_stage_caps(traj, basis; policy = strategy.stage_cap_policy)
    end
    _validate_stage_caps(stage_caps, dim, basis_max_stage)
    max_stage = _effective_max_stage(basis_max_stage, stage_caps)
    cap_metrics_active = stage_caps !== nothing || strategy.stage_cap_policy !== nothing

    allowed_terms = _allowed_terms(basis, current_stage)
    pop = _init_population(strategy, dim, allowed_terms)

    global_best_J_hist = Float64[]
    stage_level_count = 0
    stage_level_counts = zeros(Int, max_stage)
    stage_histories = [Float64[] for _ in 1:max_stage]
    stage_first_use_level = fill(-1, max_stage)
    eq_stage_histories = [Int[] for _ in 1:dim]
    promotion_log = NamedTuple[]
    level_log = NamedTuple[]
    total_loss_evals = 0
    total_invalid_evals = 0
    total_parameter_fits = 0
    total_ode_solves = 0
    total_invalid_solves = 0
    total_diverged_solves = 0
    total_nonfinite_solves = 0
    total_step_limit_solves = 0
    total_solver_unstable_solves = 0
    total_optimizer_limit_hits = 0
    total_optimizer_iteration_limit_hits = 0
    total_optimizer_safety_limit_hits = 0
    total_optimizer_eval_budget_limit_hits = 0
    total_optimizer_budget_stop_fits = 0
    total_optimizer_fallback_result_fits = 0
    total_optimizer_last_resort_fits = 0
    total_optimizer_invalid_result_fits = 0
    total_optimizer_failure_hits = 0
    total_optimizer_unknown_retcode_hits = 0
    total_fit_time_s = 0.0
    total_solve_time_s = 0.0
    observed_solver_retcodes = String[]
    observed_optimizer_retcodes = String[]
    termination_reason = :max_levels
    vis_history = NamedTuple[]

    n_steps = min(strategy.n_levels, options.max_levels)
    eval_optimizer = strategy.screening_optimizer === nothing ? optimizer : strategy.screening_optimizer

    if options.verbose >= 1
        log_info(
            "EvoGrow search start",
            context = Dict(
                :dim => dim,
                :pop_size => strategy.pop_size,
                :n_levels => n_steps,
                :children_per_parent => strategy.children_per_parent,
                :max_stage => max_stage,
                :basis_max_stage => basis_max_stage,
                :progression_mode => strategy.progression.mode,
                :usage_mode => strategy.usage.mode,
                :stage_caps => stage_caps === nothing ? "disabled" : copy(stage_caps)
            )
        )
    end

    for level in 1:n_steps
        level_t0 = time()
        level_prev_best_objective = isempty(global_best_J_hist) ? Inf : global_best_J_hist[end]
        level_stage_at_start = current_stage
        level_ctx = Dict(:level => level, :stage => current_stage)
        level_parameter_fits = 0
        level_ode_solves = 0
        level_invalid_solves = 0
        level_diverged_solves = 0
        level_nonfinite_solves = 0
        level_step_limit_solves = 0
        level_solver_unstable_solves = 0
        level_optimizer_limit_hits = 0
        level_optimizer_iteration_limit_hits = 0
        level_optimizer_safety_limit_hits = 0
        level_optimizer_eval_budget_limit_hits = 0
        level_optimizer_budget_stop_fits = 0
        level_optimizer_fallback_result_fits = 0
        level_optimizer_last_resort_fits = 0
        level_optimizer_invalid_result_fits = 0
        level_optimizer_failure_hits = 0
        level_optimizer_unknown_retcode_hits = 0
        level_fit_time_s = 0.0
        level_solve_time_s = 0.0
        level_solver_retcodes = String[]
        level_optimizer_retcodes = String[]

        if options.verbose >= 1
            log_info("Level start", context=level_ctx)
        end

        allowed_terms = _allowed_terms(basis, current_stage)
        current_stage_terms = _current_stage_terms(basis, current_stage)
        eq_stages = _effective_eq_stages(current_stage, basis_max_stage, stage_caps, dim)
        allowed_names = _allowed_term_names(basis, allowed_terms)
        current_stage_names = _allowed_term_names(basis, current_stage_terms)

        if options.verbose >= 2
            log_info("Allowed terms", context=merge(level_ctx, Dict(:terms => allowed_names)))
            log_info("New terms in current stage", context=merge(level_ctx, Dict(:terms => current_stage_names)))
        end

        # -----------------------------------
        # Evaluate current population lazily
        # -----------------------------------
        if options.verbose >= 2
            log_info("Evaluating parents", context=level_ctx)
        end

        n_parents = length(pop)
        for (i, ind) in enumerate(pop)
            parent_ctx = merge(level_ctx, Dict(:parent => i, :n_parents => n_parents))

            if !isfinite(ind.objective)
                done = options.verbose >= 2 ? time_block("parent $i", level=INFO, context=parent_ctx) : nothing

                if options.verbose >= 2
                    log_info("Parent evaluation", context=parent_ctx)
                end

                _, fit_meta = _evaluate!(ind, traj, basis, loss, eval_optimizer, strategy.λ, options, strategy.use_pretuning)
                total_loss_evals += haskey(fit_meta, :loss_evals) ? fit_meta.loss_evals : 0
                total_invalid_evals += haskey(fit_meta, :invalid_evals) ? fit_meta.invalid_evals : 0
                level_parameter_fits += 1
                level_ode_solves += _fit_stat(fit_meta, :ode_solves)
                level_invalid_solves += _fit_stat(fit_meta, :invalid_solves)
                level_diverged_solves += _fit_stat(fit_meta, :diverged_solves)
                level_nonfinite_solves += _fit_stat(fit_meta, :nonfinite_solves)
                level_step_limit_solves += _fit_stat(fit_meta, :step_limit_solves)
                level_solver_unstable_solves += _fit_stat(fit_meta, :solver_unstable_solves)
                level_optimizer_limit_hits += _fit_stat(fit_meta, :optimizer_limit_hits)
                level_optimizer_iteration_limit_hits += _fit_stat(fit_meta, :optimizer_iteration_limit_hits)
                level_optimizer_safety_limit_hits += _fit_stat(fit_meta, :optimizer_safety_limit_hits)
                level_optimizer_eval_budget_limit_hits += _fit_stat(fit_meta, :optimizer_eval_budget_limit_hits)
                level_optimizer_budget_stop_fits += _fit_string_is(fit_meta, :stop_reason, "loss_eval_budget")
                level_optimizer_fallback_result_fits += _fit_fallback_optimizer_return(fit_meta)
                level_optimizer_last_resort_fits += _fit_string_is(fit_meta, :result_source, "last_resort_best_observed")
                level_optimizer_invalid_result_fits += _fit_bool_is(fit_meta, :result_valid, false)
                level_optimizer_failure_hits += _fit_stat(fit_meta, :optimizer_failure_hits)
                level_optimizer_unknown_retcode_hits += _fit_stat(fit_meta, :optimizer_unknown_retcode_hits)
                level_fit_time_s += _fit_time_stat(fit_meta, :fit_time_s)
                level_solve_time_s += _fit_time_stat(fit_meta, :solve_time_s)
                _append_unique_strings!(level_solver_retcodes, haskey(fit_meta, :solver_retcodes) ? fit_meta.solver_retcodes : String[])
                _append_unique_strings!(level_optimizer_retcodes, haskey(fit_meta, :optimizer_retcodes) ? fit_meta.optimizer_retcodes : String[])

                if options.verbose >= 3
                    log_debug(
                        "Parent result",
                        context = merge(
                            parent_ctx,
                            Dict(
                                :structure => replace(structure_with_params_string(ind.structure, basis, ind.params), '\n' => ' '),
                                :loss => ind.loss,
                                :objective => ind.objective
                            )
                        )
                    )
                end

                if done !== nothing
                    done()
                end
            elseif options.verbose >= 3
                log_debug(
                    "Parent already evaluated",
                    context = merge(
                        parent_ctx,
                        Dict(
                            :structure => replace(structure_with_params_string(ind.structure, basis, ind.params), '\n' => ' '),
                            :loss => ind.loss,
                            :objective => ind.objective
                        )
                    )
                )
            end
        end

        # -----------------------------------
        # Generate children
        # -----------------------------------
        if options.verbose >= 2
            log_info("Generating children", context=level_ctx)
        end

        gen_done = options.verbose >= 2 ? time_block("child generation", level=INFO, context=level_ctx) : nothing

        children = Individual[]
        for ind in pop
            append!(
                children,
                _expand_equation_aware_with_usage_policy(
                    ind,
                    dim,
                    basis,
                    eq_stages,
                    allowed_terms,
                    current_stage_terms,
                    strategy.usage;
                    n_children = strategy.children_per_parent,
                    max_terms_per_eq = strategy.max_terms_per_eq,
                    stage_caps = stage_caps,
                    coupling_coherence = false
                )
            )
        end

        if gen_done !== nothing
            gen_done()
        end

        if options.verbose >= 2
            log_info("Generated children", context=merge(level_ctx, Dict(:n_children => length(children))))
        end

        # -----------------------------------
        # Evaluate children
        # -----------------------------------
        if options.verbose >= 2
            log_info("Evaluating children", context=level_ctx)
        end

        n_children = length(children)
        for (i, child) in enumerate(children)
            child_ctx = merge(level_ctx, Dict(:child => i, :n_children => n_children))

            done = options.verbose >= 2 ? time_block("child $i", level=INFO, context=child_ctx) : nothing

            if options.verbose >= 2
                log_info("Child evaluation", context=child_ctx)
            end

            _, fit_meta = _evaluate!(child, traj, basis, loss, eval_optimizer, strategy.λ, options, strategy.use_pretuning)
            total_loss_evals += haskey(fit_meta, :loss_evals) ? fit_meta.loss_evals : 0
            total_invalid_evals += haskey(fit_meta, :invalid_evals) ? fit_meta.invalid_evals : 0
            level_parameter_fits += 1
            level_ode_solves += _fit_stat(fit_meta, :ode_solves)
            level_invalid_solves += _fit_stat(fit_meta, :invalid_solves)
            level_diverged_solves += _fit_stat(fit_meta, :diverged_solves)
            level_nonfinite_solves += _fit_stat(fit_meta, :nonfinite_solves)
            level_step_limit_solves += _fit_stat(fit_meta, :step_limit_solves)
            level_solver_unstable_solves += _fit_stat(fit_meta, :solver_unstable_solves)
            level_optimizer_limit_hits += _fit_stat(fit_meta, :optimizer_limit_hits)
            level_optimizer_iteration_limit_hits += _fit_stat(fit_meta, :optimizer_iteration_limit_hits)
            level_optimizer_safety_limit_hits += _fit_stat(fit_meta, :optimizer_safety_limit_hits)
            level_optimizer_eval_budget_limit_hits += _fit_stat(fit_meta, :optimizer_eval_budget_limit_hits)
            level_optimizer_budget_stop_fits += _fit_string_is(fit_meta, :stop_reason, "loss_eval_budget")
            level_optimizer_fallback_result_fits += _fit_fallback_optimizer_return(fit_meta)
            level_optimizer_last_resort_fits += _fit_string_is(fit_meta, :result_source, "last_resort_best_observed")
            level_optimizer_invalid_result_fits += _fit_bool_is(fit_meta, :result_valid, false)
            level_optimizer_failure_hits += _fit_stat(fit_meta, :optimizer_failure_hits)
            level_optimizer_unknown_retcode_hits += _fit_stat(fit_meta, :optimizer_unknown_retcode_hits)
            level_fit_time_s += _fit_time_stat(fit_meta, :fit_time_s)
            level_solve_time_s += _fit_time_stat(fit_meta, :solve_time_s)
            _append_unique_strings!(level_solver_retcodes, haskey(fit_meta, :solver_retcodes) ? fit_meta.solver_retcodes : String[])
            _append_unique_strings!(level_optimizer_retcodes, haskey(fit_meta, :optimizer_retcodes) ? fit_meta.optimizer_retcodes : String[])

            if options.verbose >= 3
                log_debug(
                    "Child result",
                    context = merge(
                        child_ctx,
                        Dict(
                            :structure => replace(structure_with_params_string(child.structure, basis, child.params), '\n' => ' '),
                            :loss => child.loss,
                            :objective => child.objective
                        )
                    )
                )
            end

            if done !== nothing
                done()
            end
        end

        # -----------------------------------
        # Selection
        # -----------------------------------
        sel_done = options.verbose >= 2 ? time_block("selection", level=INFO, context=level_ctx) : nothing

        all_inds = vcat(pop, children)
        sort!(all_inds, by = x -> x.objective)
        pop = all_inds[1:strategy.pop_size]

        if sel_done !== nothing
            sel_done()
        end

        best = pop[1]
        push!(global_best_J_hist, best.objective)
        push!(stage_histories[current_stage], best.objective)
        stage_level_count += 1
        stage_level_counts[current_stage] += 1
        for k in 1:dim
            push!(eq_stage_histories[k], eq_stages[k])
        end

        uses_current_stage_terms = _structure_uses_terms(best.structure, current_stage_terms)
        if uses_current_stage_terms && stage_first_use_level[current_stage] == -1
            stage_first_use_level[current_stage] = level
        end
        level_elapsed_s = time() - level_t0
        level_parameter_overhead_s = max(0.0, level_fit_time_s - level_solve_time_s)

        total_parameter_fits += level_parameter_fits
        total_ode_solves += level_ode_solves
        total_invalid_solves += level_invalid_solves
        total_diverged_solves += level_diverged_solves
        total_nonfinite_solves += level_nonfinite_solves
        total_step_limit_solves += level_step_limit_solves
        total_solver_unstable_solves += level_solver_unstable_solves
        total_optimizer_limit_hits += level_optimizer_limit_hits
        total_optimizer_iteration_limit_hits += level_optimizer_iteration_limit_hits
        total_optimizer_safety_limit_hits += level_optimizer_safety_limit_hits
        total_optimizer_eval_budget_limit_hits += level_optimizer_eval_budget_limit_hits
        total_optimizer_budget_stop_fits += level_optimizer_budget_stop_fits
        total_optimizer_fallback_result_fits += level_optimizer_fallback_result_fits
        total_optimizer_last_resort_fits += level_optimizer_last_resort_fits
        total_optimizer_invalid_result_fits += level_optimizer_invalid_result_fits
        total_optimizer_failure_hits += level_optimizer_failure_hits
        total_optimizer_unknown_retcode_hits += level_optimizer_unknown_retcode_hits
        total_fit_time_s += level_fit_time_s
        total_solve_time_s += level_solve_time_s
        _append_unique_strings!(observed_solver_retcodes, level_solver_retcodes)
        _append_unique_strings!(observed_optimizer_retcodes, level_optimizer_retcodes)

        push!(
            level_log,
            (
                level = level,
                stage = current_stage,
                best_loss = best.loss,
                best_objective = best.objective,
                n_params = length(best.params),
                uses_current_stage_terms = uses_current_stage_terms,
                elapsed_s = level_elapsed_s,
                parameter_fits = level_parameter_fits,
                ode_solves = level_ode_solves,
                invalid_solves = level_invalid_solves,
                diverged_solves = level_diverged_solves,
                nonfinite_solves = level_nonfinite_solves,
                step_limit_solves = level_step_limit_solves,
                solver_unstable_solves = level_solver_unstable_solves,
                optimizer_limit_hits = level_optimizer_limit_hits,
                optimizer_iteration_limit_hits = level_optimizer_iteration_limit_hits,
                optimizer_safety_limit_hits = level_optimizer_safety_limit_hits,
                optimizer_eval_budget_limit_hits = level_optimizer_eval_budget_limit_hits,
                optimizer_budget_stop_fits = level_optimizer_budget_stop_fits,
                optimizer_fallback_result_fits = level_optimizer_fallback_result_fits,
                optimizer_last_resort_fits = level_optimizer_last_resort_fits,
                optimizer_invalid_result_fits = level_optimizer_invalid_result_fits,
                optimizer_failure_hits = level_optimizer_failure_hits,
                optimizer_unknown_retcode_hits = level_optimizer_unknown_retcode_hits,
                parameter_optimization_time_s = level_parameter_overhead_s,
                simulation_time_s = level_solve_time_s,
                solver_retcodes = copy(level_solver_retcodes),
                optimizer_retcodes = copy(level_optimizer_retcodes)
            )
        )

        _vis_candidates_structures = [c.structure for c in children]
        _vis_candidates_params = [copy(c.params) for c in children]
        _vis_candidates_loss = [c.loss for c in children]
        _vis_candidates_objective = [c.objective for c in children]
        _vis_accepted_new_best = best.objective < level_prev_best_objective

        function _push_vis_snapshot!(stage_trans, prev_s, new_s)
            push!(
                vis_history,
                (
                    level = level,
                    stage = level_stage_at_start,
                    candidates_structures = _vis_candidates_structures,
                    candidates_params = _vis_candidates_params,
                    candidates_loss = _vis_candidates_loss,
                    candidates_objective = _vis_candidates_objective,
                    best_structure = best.structure,
                    best_params = copy(best.params),
                    best_loss = best.loss,
                    best_objective = best.objective,
                    accepted_new_best = _vis_accepted_new_best,
                    stage_transition = stage_trans,
                    previous_stage = prev_s,
                    new_stage = new_s
                )
            )
            if strategy.level_callback !== nothing
                strategy.level_callback(vis_history[end])
            end
        end

        # -----------------------------------
        # Logging
        # -----------------------------------
        if options.verbose >= 1
            log_info(
                "Best individual",
                context = merge(
                    level_ctx,
                    Dict(
                        :best_objective => best.objective,
                        :best_loss => best.loss,
                        :n_params => length(best.params),
                        :uses_current_stage_terms => uses_current_stage_terms
                    )
                )
            )
            log_info(
                "Level cost summary",
                context = merge(
                    level_ctx,
                    Dict(
                        :elapsed_s => level_elapsed_s,
                        :parameter_fits => level_parameter_fits,
                        :ode_solves => level_ode_solves,
                        :invalid_solves => level_invalid_solves,
                        :diverged_solves => level_diverged_solves,
                        :nonfinite_solves => level_nonfinite_solves,
                        :step_limit_solves => level_step_limit_solves,
                        :solver_unstable_solves => level_solver_unstable_solves,
                        :optimizer_limit_hits => level_optimizer_limit_hits,
                        :optimizer_iteration_limit_hits => level_optimizer_iteration_limit_hits,
                        :optimizer_safety_limit_hits => level_optimizer_safety_limit_hits,
                        :optimizer_eval_budget_limit_hits => level_optimizer_eval_budget_limit_hits,
                        :optimizer_budget_stop_fits => level_optimizer_budget_stop_fits,
                        :optimizer_fallback_result_fits => level_optimizer_fallback_result_fits,
                        :optimizer_last_resort_fits => level_optimizer_last_resort_fits,
                        :optimizer_invalid_result_fits => level_optimizer_invalid_result_fits,
                        :optimizer_failure_hits => level_optimizer_failure_hits,
                        :optimizer_unknown_retcode_hits => level_optimizer_unknown_retcode_hits,
                        :parameter_optimization_time_s => level_parameter_overhead_s,
                        :simulation_time_s => level_solve_time_s,
                        :solver_retcodes => level_solver_retcodes,
                        :optimizer_retcodes => level_optimizer_retcodes
                    )
                )
            )
        end

        if options.verbose >= 2
            log_info(
                "Best structure",
                context = merge(
                    level_ctx,
                    Dict(
                        :structure => replace(structure_with_params_string(best.structure, basis, best.params), '\n' => ' ')
                    )
                )
            )
        end

        if options.verbose >= 3
            log_debug("Population snapshot", context=level_ctx)
            for (i, ind) in enumerate(pop[1:min(5, length(pop))])
                log_debug(
                    "Top individual",
                    context = merge(
                        level_ctx,
                        Dict(
                            :rank => i,
                            :objective => ind.objective,
                            :loss => ind.loss,
                            :n_params => length(ind.params),
                            :structure => replace(structure_with_params_string(ind.structure, basis, ind.params), '\n' => ' ')
                        )
                    )
                )
            end
        end

        # -----------------------------------
        # Shared stopping / stage progression
        # -----------------------------------
        if strategy.progression.mode == :global_plateau
            stop, reason = should_stop(global_best_J_hist, best.loss, level, options)

            if stop
                if reason == :loss_tol
                    termination_reason = :loss_tol
                    if options.verbose >= 1
                        log_info("Stopping due to loss tolerance", context=merge(level_ctx, Dict(:reason => reason)))
                    end
                    _push_vis_snapshot!(false, nothing, nothing)
                    break
                end

                if (reason == :plateau_absolute || reason == :plateau_relative) && current_stage < max_stage
                    push!(
                        promotion_log,
                        (
                            from_stage = current_stage,
                            to_stage = current_stage + 1,
                            level = level,
                            reason = reason,
                            stage_levels = stage_level_count
                        )
                    )

                    current_stage += 1
                    stage_level_count = 0

                    if options.verbose >= 1
                        log_info(
                            "Plateau reached, increasing complexity",
                            context = merge(level_ctx, Dict(:reason => reason, :new_stage => current_stage))
                        )
                    end

                    _push_vis_snapshot!(true, level_stage_at_start, current_stage)
                    continue
                end

                termination_reason = reason
                if options.verbose >= 1
                    log_info("Stopping", context=merge(level_ctx, Dict(:reason => reason)))
                end
                _push_vis_snapshot!(false, nothing, nothing)
                break
            end
        else
            stop, reason, action = _stage_progression_decision(
                strategy,
                stage_histories[current_stage],
                stage_level_count,
                best.loss,
                current_stage,
                max_stage,
                level,
                n_steps,
                options
            )

            if stop
                if action == :promote
                    push!(
                        promotion_log,
                        (
                            from_stage = current_stage,
                            to_stage = current_stage + 1,
                            level = level,
                            reason = reason,
                            stage_levels = stage_level_count
                        )
                    )

                    current_stage += 1
                    stage_level_count = 0

                    if options.verbose >= 1
                        log_info(
                            "Stage-local plateau reached, increasing complexity",
                            context = merge(level_ctx, Dict(:reason => reason, :new_stage => current_stage))
                        )
                    end

                    _push_vis_snapshot!(true, level_stage_at_start, current_stage)
                    continue
                end

                termination_reason = reason
                if options.verbose >= 1
                    log_info("Stopping", context=merge(level_ctx, Dict(:reason => reason)))
                end
                _push_vis_snapshot!(false, nothing, nothing)
                break
            end
        end

        _push_vis_snapshot!(false, nothing, nothing)
    end

    best = pop[1]
    eq_final_stages = _effective_eq_stages(current_stage, basis_max_stage, stage_caps, dim)

    if options.verbose >= 1
        log_info(
            "EvoGrow search finished",
            context = Dict(
                :final_stage => current_stage,
                :best_loss => best.loss,
                :best_objective => best.objective,
                :n_params => length(best.params),
                :termination_reason => termination_reason
            )
        )
    end

    return (
        structure = best.structure,
        params = best.params,
        loss = best.loss,
        objective = best.objective,
        meta = (
            best_loss = best.loss,
            best_objective = best.objective,
            best_structure_pretty = structure_with_params_string(best.structure, basis, best.params),
            best_J_hist = global_best_J_hist,
            stage_histories = stage_histories,
            stage_level_counts = stage_level_counts,
            stage_first_use_level = stage_first_use_level,
            promotion_log = promotion_log,
            level_log = level_log,
            vis_history = vis_history,
            total_loss_evals = total_loss_evals,
            total_invalid_evals = total_invalid_evals,
            total_parameter_fits = total_parameter_fits,
            total_ode_solves = total_ode_solves,
            total_invalid_solves = total_invalid_solves,
            total_diverged_solves = total_diverged_solves,
            total_nonfinite_solves = total_nonfinite_solves,
            total_step_limit_solves = total_step_limit_solves,
            total_solver_unstable_solves = total_solver_unstable_solves,
            total_optimizer_limit_hits = total_optimizer_limit_hits,
            total_optimizer_iteration_limit_hits = total_optimizer_iteration_limit_hits,
            total_optimizer_safety_limit_hits = total_optimizer_safety_limit_hits,
            total_optimizer_eval_budget_limit_hits = total_optimizer_eval_budget_limit_hits,
            total_optimizer_budget_stop_fits = total_optimizer_budget_stop_fits,
            total_optimizer_fallback_result_fits = total_optimizer_fallback_result_fits,
            total_optimizer_last_resort_fits = total_optimizer_last_resort_fits,
            total_optimizer_invalid_result_fits = total_optimizer_invalid_result_fits,
            total_optimizer_failure_hits = total_optimizer_failure_hits,
            total_optimizer_unknown_retcode_hits = total_optimizer_unknown_retcode_hits,
            total_parameter_optimization_time_s = max(0.0, total_fit_time_s - total_solve_time_s),
            total_simulation_time_s = total_solve_time_s,
            solver_retcodes = copy(observed_solver_retcodes),
            optimizer_retcodes = copy(observed_optimizer_retcodes),
            screening_budgets_active = strategy.screening_optimizer !== nothing,
            final_stage = current_stage,
            eq_final_stages = cap_metrics_active ? copy(eq_final_stages) : nothing,
            eq_stage_histories = cap_metrics_active ? eq_stage_histories : nothing,
            stage_caps = stage_caps === nothing ? nothing : copy(stage_caps),
            stage_cap_policy_active = strategy.stage_cap_policy !== nothing,
            termination_reason = termination_reason,
            progression_mode = strategy.progression.mode,
            usage_mode = strategy.usage.mode
        )
    )
end
