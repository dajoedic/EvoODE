# src/structure/evogrow_v3.jl

"""
EvoGrow v3 structure search strategy.

This first v3 slice carries per-equation stage state while preserving the
EvoGrow v2.2 `:stage_local` algorithm in lockstep form.
"""
Base.@kwdef struct EvoGrowV3 <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
    progression::StageProgressionPolicy = StageProgressionPolicy()
    usage::StageUsagePolicy = StageUsagePolicy()
    use_pretuning::Bool = true
    level_callback::Union{Nothing, Function} = nothing
end

function _evogrow_v2_bridge(strategy::EvoGrowV3)
    return EvoGrow(
        pop_size = strategy.pop_size,
        n_levels = strategy.n_levels,
        children_per_parent = strategy.children_per_parent,
        max_terms_per_eq = strategy.max_terms_per_eq,
        λ = strategy.λ,
        progression = strategy.progression,
        usage = strategy.usage,
        use_pretuning = strategy.use_pretuning,
        level_callback = strategy.level_callback
    )
end

function _validate_policy(strategy::EvoGrowV3)
    _validate_policy(_evogrow_v2_bridge(strategy))
    if strategy.progression.mode != :stage_local
        error("EvoGrowV3 currently supports only StageProgressionPolicy.mode=:stage_local")
    end
    return nothing
end

function _init_eq_stage_state(dim::Int)
    return (
        eq_stages = fill(1, dim),
        eq_levels_in_stage = zeros(Int, dim),
        eq_plateau_histories = [Float64[] for _ in 1:dim],
        eq_stage_histories = [Int[] for _ in 1:dim]
    )
end

function _record_eq_stage_level!(
    eq_levels_in_stage::Vector{Int},
    eq_plateau_histories::Vector{Vector{Float64}},
    eq_stage_histories::Vector{Vector{Int}},
    eq_stages::Vector{Int},
    objective::Float64
)
    for k in eachindex(eq_stages)
        eq_levels_in_stage[k] += 1
        push!(eq_plateau_histories[k], objective)
        push!(eq_stage_histories[k], eq_stages[k])
    end
    return nothing
end

function _lockstep_stage_progression_decision(
    strategy::EvoGrowV3,
    stage_best_J_hist::Vector{Float64},
    stage_level_count::Int,
    best_loss::Float64,
    current_stage::Int,
    max_stage::Int,
    level::Int,
    n_steps::Int,
    options::DiscoveryOptions
)
    return _stage_progression_decision(
        _evogrow_v2_bridge(strategy),
        stage_best_J_hist,
        stage_level_count,
        best_loss,
        current_stage,
        max_stage,
        level,
        n_steps,
        options
    )
end

function _apply_lockstep_stage_update!(
    eq_stages::Vector{Int},
    eq_levels_in_stage::Vector{Int},
    eq_plateau_histories::Vector{Vector{Float64}}
)
    for k in eachindex(eq_stages)
        eq_stages[k] += 1
        eq_levels_in_stage[k] = 0
        empty!(eq_plateau_histories[k])
    end
    return maximum(eq_stages)
end

"""
    search_structure(strategy::EvoGrowV3, traj, basis, loss, optimizer, options)

Incremental evolutionary growth with v3 per-equation stage-state scaffolding.
In WP-v3.2, promotion remains lockstep-global and reproduces EvoGrow v2.2
`:stage_local` behavior.
"""
function search_structure(strategy::EvoGrowV3,
                          traj::Trajectory,
                          basis::AbstractBasis,
                          loss::AbstractLoss,
                          optimizer::AbstractOptimizer,
                          options::DiscoveryOptions)

    _validate_policy(strategy)

    dim = size(traj.x, 2)
    eq_state = _init_eq_stage_state(dim)
    eq_stages = eq_state.eq_stages
    eq_levels_in_stage = eq_state.eq_levels_in_stage
    eq_plateau_histories = eq_state.eq_plateau_histories
    eq_stage_histories = eq_state.eq_stage_histories

    current_stage = maximum(eq_stages)
    max_stage = _max_stage(basis)

    bridge = _evogrow_v2_bridge(strategy)
    allowed_terms = _allowed_terms(basis, current_stage)
    pop = _init_population(bridge, dim, allowed_terms)

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
    vis_history = NamedTuple[]

    n_steps = min(strategy.n_levels, options.max_levels)

    if options.verbose >= 1
        log_info(
            "EvoGrowV3 search start",
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
        level_t0 = time()
        level_prev_best_objective = isempty(global_best_J_hist) ? Inf : global_best_J_hist[end]
        level_stage_at_start = current_stage
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

                _, fit_meta = _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options, strategy.use_pretuning)
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

            _, fit_meta = _evaluate!(child, traj, basis, loss, optimizer, strategy.λ, options, strategy.use_pretuning)
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
        _record_eq_stage_level!(
            eq_levels_in_stage,
            eq_plateau_histories,
            eq_stage_histories,
            eq_stages,
            best.objective
        )

        uses_current_stage_terms = _structure_uses_terms(best.structure, current_stage_terms)
        if uses_current_stage_terms && stage_first_use_level[current_stage] == -1
            stage_first_use_level[current_stage] = level
        end
        level_elapsed_s = time() - level_t0

        push!(
            level_log,
            (
                level = level,
                stage = current_stage,
                best_loss = best.loss,
                best_objective = best.objective,
                n_params = length(best.params),
                uses_current_stage_terms = uses_current_stage_terms,
                elapsed_s = level_elapsed_s
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

        stop, reason, action = _lockstep_stage_progression_decision(
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

                current_stage = _apply_lockstep_stage_update!(
                    eq_stages,
                    eq_levels_in_stage,
                    eq_plateau_histories
                )
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

        _push_vis_snapshot!(false, nothing, nothing)
    end

    best = pop[1]

    if options.verbose >= 1
        log_info(
            "EvoGrowV3 search finished",
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
            final_stage = maximum(eq_stages),
            eq_final_stages = copy(eq_stages),
            eq_stage_histories = [copy(hist) for hist in eq_stage_histories],
            termination_reason = termination_reason,
            progression_mode = strategy.progression.mode,
            usage_mode = strategy.usage.mode
        )
    )
end
