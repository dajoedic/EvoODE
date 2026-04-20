# src/structure/evogrow.jl

using Random
using Printf

"""
EvoGrow structure search strategy.

- pop_size: population size
- n_levels: number of growth levels
- children_per_parent: number of children sampled per parent per level
- max_terms_per_eq: maximum number of active terms per equation
- λ: complexity penalty (objective = loss + λ * n_params)

Version note:
- v1: flat growth over all terms
- v2: staged growth over predefined basis groups
- v2.1: stage-aware child generation
"""
Base.@kwdef struct EvoGrow <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
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

Stage-aware growth:
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
    params, lval, _ = fit_parameters(optimizer, f!, traj, n_params, loss, options)

    ind.params = params
    ind.loss = lval
    ind.objective = lval + λ * length(params)
    return ind
end

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------

"""
    search_structure(strategy::EvoGrow, traj, basis, loss, optimizer, options)

Incremental evolutionary growth.

v2/v2.1 behavior:
- if `basis` is staged, only terms up to `current_stage` are allowed
- on plateau, the next stage is unlocked
- once a new stage is unlocked, child generation becomes stage-aware:
  newly generated children preferentially include at least one term from the
  currently unlocked stage
- on sufficiently low loss, the search stops
- current best population is preserved when stage increases

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

    dim = size(traj.x, 2)

    current_stage = 1
    max_stage = _max_stage(basis)

    allowed_terms = _allowed_terms(basis, current_stage)
    pop = _init_population(strategy, dim, allowed_terms)

    best_J_hist = Float64[]

    n_steps = min(strategy.n_levels, options.max_levels)

    if options.verbose >= 1
        log_info(
            "EvoGrow search start",
            context = Dict(
                :dim => dim,
                :pop_size => strategy.pop_size,
                :n_levels => n_steps,
                :children_per_parent => strategy.children_per_parent,
                :max_stage => max_stage
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

                _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options)

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
            else
                if options.verbose >= 3
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
        end

        # -----------------------------------
        # Generate children
        # -----------------------------------
        if options.verbose >= 2
            log_info("Generating children", context=level_ctx)
        end

        gen_done = options.verbose >= 2 ? time_block("child generation", level=INFO, context=level_ctx) : nothing

        children = Individual[]

        if current_stage == 1
            for ind in pop
                append!(children,
                        _expand(ind, dim, allowed_terms;
                                n_children = strategy.children_per_parent,
                                max_terms_per_eq = strategy.max_terms_per_eq))
            end
        else
            for ind in pop
                append!(children,
                        _expand_stage_aware(ind, dim, allowed_terms, current_stage_terms;
                                            n_children = strategy.children_per_parent,
                                            max_terms_per_eq = strategy.max_terms_per_eq))
            end
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

            _evaluate!(child, traj, basis, loss, optimizer, strategy.λ, options)

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
        push!(best_J_hist, best.objective)

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
                        :n_params => length(best.params)
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
        stop, reason = should_stop(best_J_hist, best.loss, level, options)

        if stop
            if reason == :loss_tol
                if options.verbose >= 1
                    log_info("Stopping due to loss tolerance", context=merge(level_ctx, Dict(:reason => reason)))
                end
                break
            end

            if (reason == :plateau_absolute || reason == :plateau_relative) && current_stage < max_stage
                current_stage += 1

                if options.verbose >= 1
                    log_info(
                        "Plateau reached, increasing complexity",
                        context = merge(level_ctx, Dict(:reason => reason, :new_stage => current_stage))
                    )
                end

                continue
            end

            if options.verbose >= 1
                log_info("Stopping", context=merge(level_ctx, Dict(:reason => reason)))
            end
            break
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
                :n_params => length(best.params)
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
            best_J_hist = best_J_hist,
            final_stage = current_stage
        )
    )
end