# src/structure/evogrow_v3.jl

"""
EvoGrow v3 structure search strategy.

This v3 variant carries per-equation stage state and promotes equations from
their own derivative-residual plateau signals.
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
    screening_optimizer::Union{Nothing, AbstractOptimizer} = nothing
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
        screening_optimizer = strategy.screening_optimizer,
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

"""
    search_structure(strategy::EvoGrowV3, traj, basis, loss, optimizer, options)

Incremental evolutionary growth with v3 per-equation promotion driven by
derivative residual plateaus.
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
    eq_residual_log = [Float64[] for _ in 1:dim]
    eq_promotion_levels = [Int[] for _ in 1:dim]
    derivative_residual_fallback = false

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

        eq_residuals, used_residual_fallback = _evogrow_v3_equation_residuals(
            best.structure,
            best.params,
            basis,
            traj,
            options
        )
        derivative_residual_fallback |= used_residual_fallback

        _record_eq_stage_level!(
            eq_levels_in_stage,
            eq_plateau_histories,
            eq_stage_histories,
            eq_residual_log,
            eq_stages,
            eq_residuals
        )

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

        stop, reason = _evogrow_v3_termination_decision(
            best.loss,
            level,
            eq_stages,
            eq_plateau_histories,
            max_stage,
            options
        )

        if stop
            termination_reason = reason
            if options.verbose >= 1
                log_info("Stopping", context=merge(level_ctx, Dict(:reason => reason)))
            end
            _push_vis_snapshot!(false, nothing, nothing)
            break
        end

        promote = _evogrow_v3_promotion_decisions(
            eq_stages,
            eq_levels_in_stage,
            eq_plateau_histories,
            max_stage,
            strategy,
            options
        )

        if any(promote)
            for k in eachindex(promote)
                if promote[k]
                    push!(
                        promotion_log,
                        (
                            equation = k,
                            from_stage = eq_stages[k],
                            to_stage = eq_stages[k] + 1,
                            level = level,
                            reason = :equation_residual_plateau,
                            stage_levels = eq_levels_in_stage[k],
                            residual = eq_residuals[k]
                        )
                    )
                end
            end

            _apply_eq_stage_update!(
                eq_stages,
                eq_levels_in_stage,
                eq_plateau_histories,
                eq_promotion_levels,
                promote,
                level
            )
            current_stage = maximum(eq_stages)

            if options.verbose >= 1
                log_info(
                    "Equation-local plateau reached, increasing complexity",
                    context = merge(
                        level_ctx,
                        Dict(
                            :promoted_equations => findall(promote),
                            :eq_stages => copy(eq_stages),
                            :new_stage => current_stage
                        )
                    )
                )
            end

            _push_vis_snapshot!(true, level_stage_at_start, current_stage)
            continue
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
            total_optimizer_failure_hits = total_optimizer_failure_hits,
            total_optimizer_unknown_retcode_hits = total_optimizer_unknown_retcode_hits,
            total_parameter_optimization_time_s = max(0.0, total_fit_time_s - total_solve_time_s),
            total_simulation_time_s = total_solve_time_s,
            solver_retcodes = copy(observed_solver_retcodes),
            optimizer_retcodes = copy(observed_optimizer_retcodes),
            screening_budgets_active = strategy.screening_optimizer !== nothing,
            final_stage = maximum(eq_stages),
            eq_final_stages = copy(eq_stages),
            eq_stage_histories = [copy(hist) for hist in eq_stage_histories],
            eq_residual_log = [copy(hist) for hist in eq_residual_log],
            eq_promotion_levels = [copy(levels) for levels in eq_promotion_levels],
            derivative_residual_fallback = derivative_residual_fallback,
            termination_reason = termination_reason,
            progression_mode = strategy.progression.mode,
            usage_mode = strategy.usage.mode
        )
    )
end
