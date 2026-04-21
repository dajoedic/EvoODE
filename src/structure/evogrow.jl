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
                    options::DiscoveryOptions)

    f!, n_params, _ = build_rhs(ind.structure, basis)
    params, lval, fit_meta = fit_parameters(optimizer, f!, traj, n_params, loss, options)

    ind.params = params
    ind.loss = lval
    ind.objective = lval + λ * length(params)
    return ind, fit_meta
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
    max_stage = _max_stage(basis)

    allowed_terms = _allowed_terms(basis, current_stage)
    pop = _init_population(strategy, dim, allowed_terms)

    global_best_J_hist = Float64[]
    stage_level_count = 0
    stage_level_counts = zeros(Int, max_stage)
    stage_histories = [Float64[] for _ in 1:max_stage]
    stage_first_use_level = fill(-1, max_stage)
    promotion_log = NamedTuple[]
    level_log = NamedTuple[]
    total_loss_evals = 0
    total_invalid_evals = 0
    termination_reason = :max_levels

    n_steps = min(strategy.n_levels, options.max_levels)

    if options.verbose >= 1
        log_info(
            "EvoGrow search start",
            context = Dict(
                :dim => dim,
                :pop_size => strategy.pop_size,
                :n_levels => n_steps,
                :children_per_parent => strategy.children_per_parent,
                :max_stage => max_stage,
                :progression_mode => strategy.progression.mode,
                :usage_mode => strategy.usage.mode
            )
        )
    end

    for level in 1:n_steps
        level_ctx = Dict(:level => level, :stage => current_stage)

        if options.verbose >= 1
            log_info("Level start", context=level_ctx)
        end

        allowed_terms = _allowed_terms(basis, current_stage)
        current_stage_terms = _current_stage_terms(basis, current_stage)
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

                _, fit_meta = _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options)
                total_loss_evals += haskey(fit_meta, :loss_evals) ? fit_meta.loss_evals : 0
                total_invalid_evals += haskey(fit_meta, :invalid_evals) ? fit_meta.invalid_evals : 0

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
                _expand_with_usage_policy(
                    ind,
                    dim,
                    allowed_terms,
                    current_stage_terms,
                    strategy.usage;
                    n_children = strategy.children_per_parent,
                    max_terms_per_eq = strategy.max_terms_per_eq
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

            _, fit_meta = _evaluate!(child, traj, basis, loss, optimizer, strategy.λ, options)
            total_loss_evals += haskey(fit_meta, :loss_evals) ? fit_meta.loss_evals : 0
            total_invalid_evals += haskey(fit_meta, :invalid_evals) ? fit_meta.invalid_evals : 0

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

        uses_current_stage_terms = _structure_uses_terms(best.structure, current_stage_terms)
        if uses_current_stage_terms && stage_first_use_level[current_stage] == -1
            stage_first_use_level[current_stage] = level
        end

        push!(
            level_log,
            (
                level = level,
                stage = current_stage,
                best_loss = best.loss,
                best_objective = best.objective,
                n_params = length(best.params),
                uses_current_stage_terms = uses_current_stage_terms
            )
        )

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

                    continue
                end

                termination_reason = reason
                if options.verbose >= 1
                    log_info("Stopping", context=merge(level_ctx, Dict(:reason => reason)))
                end
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

                    continue
                end

                termination_reason = reason
                if options.verbose >= 1
                    log_info("Stopping", context=merge(level_ctx, Dict(:reason => reason)))
                end
                break
            end
        end
    end

    best = pop[1]

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
            total_loss_evals = total_loss_evals,
            total_invalid_evals = total_invalid_evals,
            final_stage = current_stage,
            termination_reason = termination_reason,
            progression_mode = strategy.progression.mode,
            usage_mode = strategy.usage.mode
        )
    )
end
