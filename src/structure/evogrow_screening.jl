# src/structure/evogrow_screening.jl

"""
EvoGrow structure search with derivative-residual candidate screening.

This variant follows EvoGrow v2.2 for growth, selection, stage promotion, and
stopping, but changes the cost profile of each level: all parents and children
are scored by a closed-form least-squares fit to finite-difference derivatives,
then only the best `screen_k` candidates are polished with the simulation loss.
The default `screen_k = pop_size` keeps selection pressure comparable to the
baseline population size, while `polish_maxiters = 20` reflects the WP-P2.2 cost
model: about one tenth of the reference BFGS budget keeps losses on the
simulation scale without spending full fits on every candidate.

`screening_score = :aic` uses the Gaussian least-squares Akaike information
criterion, `n * log(RSS / n) + 2p`, where `RSS / n` is the derivative residual
and `p` is the active parameter count. AIC is scale-invariant for ranking
structures on the same trajectory because any constant rescaling of the
derivative residual adds the same offset to every candidate, while the `2p`
penalty counters the nested-LS bias toward larger structures. The raw residual
score remains available, and is still the default, with
`screening_score = :residual`; comparison scripts should set the intended mode
explicitly.

`screen_k < pop_size` is rejected rather than silently shrinking the population;
callers that want a smaller polished set should reduce `pop_size` as well.
If `screening_optimizer` is supplied, it is used for bounded polish and rejected
diagnostic fits, preserving the existing `screening_budgets_active` meaning:
reduced solver budgets are active. The final refit always uses the full
optimizer and is included in aggregate fit/solve cost totals as well as reported
separately.

Rank agreement is reported as Spearman's rho over selected candidates plus a
small deterministic sample of rejected candidates. Spearman is used because the
screening score and simulation loss have different units; only monotonic
ordering matters for judging whether screening preserves good candidates. The
rejected sample is diagnostic only and never enters the population. Parent
incumbents keep their previous simulated value if bounded polishing makes them
worse, intentionally preserving the search anchor; this makes best-objective
history monotone and can affect plateau timing relative to EvoGrow. `vis_history`
is returned for schema compatibility but is not populated by this variant.
"""
Base.@kwdef struct EvoGrowScreening <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
    progression::StageProgressionPolicy = StageProgressionPolicy()
    usage::StageUsagePolicy = StageUsagePolicy()
    screen_k::Int = 0
    polish_maxiters::Int = 20
    rejected_diagnostic_samples::Int = 2
    screening_optimizer::Union{Nothing, AbstractOptimizer} = nothing
    level_callback::Union{Nothing, Function} = nothing
    screening_score::Symbol = :residual
end

function _validate_policy(strategy::EvoGrowScreening)
    _validate_policy(EvoGrow(
        pop_size = strategy.pop_size,
        n_levels = strategy.n_levels,
        children_per_parent = strategy.children_per_parent,
        max_terms_per_eq = strategy.max_terms_per_eq,
        λ = strategy.λ,
        progression = strategy.progression,
        usage = strategy.usage,
    ))
    if strategy.screen_k < 0
        error("EvoGrowScreening.screen_k must be >= 0; use 0 for pop_size")
    end
    if strategy.screen_k > 0 && strategy.screen_k < strategy.pop_size
        error("EvoGrowScreening.screen_k must be >= pop_size to avoid silent population shrinkage; reduce pop_size for smaller selected sets")
    end
    if strategy.polish_maxiters < 1
        error("EvoGrowScreening.polish_maxiters must be >= 1")
    end
    if strategy.rejected_diagnostic_samples < 0
        error("EvoGrowScreening.rejected_diagnostic_samples must be >= 0")
    end
    if !(strategy.screening_score in (:residual, :aic))
        error("EvoGrowScreening.screening_score must be :residual or :aic")
    end
    return nothing
end

function _polish_optimizer(strategy::EvoGrowScreening, optimizer::BFGSOptimizer)
    return BFGSOptimizer(
        maxiters = strategy.polish_maxiters,
        abstol = optimizer.abstol,
        reltol = optimizer.reltol,
        maxiters_solve = optimizer.maxiters_solve,
        clamp_val = optimizer.clamp_val,
        time_limit_s = optimizer.time_limit_s,
        reject_nonfinite = optimizer.reject_nonfinite,
        divergence_limit = optimizer.divergence_limit,
    )
end

function _polish_optimizer(::EvoGrowScreening, optimizer::AbstractOptimizer)
    error("EvoGrowScreening requires BFGSOptimizer so polish_maxiters can bound the simulation fit budget; got $(typeof(optimizer))")
end

function _evaluate_with_p0!(ind::Individual,
                            traj::Trajectory,
                            basis::AbstractBasis,
                            loss::AbstractLoss,
                            optimizer::AbstractOptimizer,
                            λ::Float64,
                            options::DiscoveryOptions,
                            p0)
    f!, n_params, _ = build_rhs(ind.structure, basis)
    params, lval, fit_meta = fit_parameters(optimizer, f!, traj, n_params, loss, options; p0 = p0)
    ind.params = params
    ind.loss = lval
    ind.objective = lval + λ * length(params)
    return ind, fit_meta
end

function _average_ranks(values::Vector{Float64})
    ranks = zeros(Float64, length(values))
    order = sortperm(values)
    i = 1
    while i <= length(order)
        j = i
        while j < length(order) && values[order[j + 1]] == values[order[i]]
            j += 1
        end
        rank = (i + j) / 2
        for pos in i:j
            ranks[order[pos]] = rank
        end
        i = j + 1
    end
    return ranks
end

function _spearman_rho(xs::Vector{Float64}, ys::Vector{Float64})
    idxs = [i for i in eachindex(xs) if isfinite(xs[i]) && isfinite(ys[i])]
    if length(idxs) < 2
        return NaN
    end

    rx = _average_ranks(xs[idxs])
    ry = _average_ranks(ys[idxs])
    mx = sum(rx) / length(rx)
    my = sum(ry) / length(ry)
    dx = rx .- mx
    dy = ry .- my
    denom = sqrt(sum(abs2, dx) * sum(abs2, dy))
    return denom == 0.0 ? NaN : sum(dx .* dy) / denom
end

function _screening_score(screen, mode::Symbol)
    if !screen.valid
        return Inf
    end
    if mode == :residual
        return screen.residual + 1e-12 * screen.n_params
    elseif mode == :aic
        n_obs = max(screen.n_timepoints * screen.dim, 1)
        mse = max(screen.residual, eps(Float64))
        return n_obs * log(mse) + 2.0 * screen.n_params
    end
    error("Unsupported screening score mode: $(mode)")
end

function _add_fit_stats!(totals::Dict{Symbol, Any}, fit_meta)
    totals[:loss_evals] += _fit_stat(fit_meta, :loss_evals)
    totals[:invalid_evals] += _fit_stat(fit_meta, :invalid_evals)
    totals[:parameter_fits] += 1
    totals[:ode_solves] += _fit_stat(fit_meta, :ode_solves)
    totals[:invalid_solves] += _fit_stat(fit_meta, :invalid_solves)
    totals[:diverged_solves] += _fit_stat(fit_meta, :diverged_solves)
    totals[:nonfinite_solves] += _fit_stat(fit_meta, :nonfinite_solves)
    totals[:step_limit_solves] += _fit_stat(fit_meta, :step_limit_solves)
    totals[:solver_unstable_solves] += _fit_stat(fit_meta, :solver_unstable_solves)
    totals[:optimizer_limit_hits] += _fit_stat(fit_meta, :optimizer_limit_hits)
    totals[:optimizer_iteration_limit_hits] += _fit_stat(fit_meta, :optimizer_iteration_limit_hits)
    totals[:optimizer_safety_limit_hits] += _fit_stat(fit_meta, :optimizer_safety_limit_hits)
    totals[:optimizer_failure_hits] += _fit_stat(fit_meta, :optimizer_failure_hits)
    totals[:optimizer_unknown_retcode_hits] += _fit_stat(fit_meta, :optimizer_unknown_retcode_hits)
    totals[:fit_time_s] += _fit_time_stat(fit_meta, :fit_time_s)
    totals[:solve_time_s] += _fit_time_stat(fit_meta, :solve_time_s)
    _append_unique_strings!(totals[:solver_retcodes], haskey(fit_meta, :solver_retcodes) ? fit_meta.solver_retcodes : String[])
    _append_unique_strings!(totals[:optimizer_retcodes], haskey(fit_meta, :optimizer_retcodes) ? fit_meta.optimizer_retcodes : String[])
    return nothing
end

function _empty_fit_totals()
    return Dict{Symbol, Any}(
        :loss_evals => 0,
        :invalid_evals => 0,
        :parameter_fits => 0,
        :ode_solves => 0,
        :invalid_solves => 0,
        :diverged_solves => 0,
        :nonfinite_solves => 0,
        :step_limit_solves => 0,
        :solver_unstable_solves => 0,
        :optimizer_limit_hits => 0,
        :optimizer_iteration_limit_hits => 0,
        :optimizer_safety_limit_hits => 0,
        :optimizer_failure_hits => 0,
        :optimizer_unknown_retcode_hits => 0,
        :fit_time_s => 0.0,
        :solve_time_s => 0.0,
        :solver_retcodes => String[],
        :optimizer_retcodes => String[],
    )
end

function search_structure(strategy::EvoGrowScreening,
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
    pop = _init_population(
        EvoGrow(pop_size = strategy.pop_size, max_terms_per_eq = strategy.max_terms_per_eq),
        dim,
        allowed_terms,
    )

    eval_optimizer = strategy.screening_optimizer === nothing ? optimizer : strategy.screening_optimizer
    polish_optimizer = _polish_optimizer(strategy, eval_optimizer)
    screen_k = strategy.screen_k == 0 ? strategy.pop_size : strategy.screen_k
    screen_k = min(max(screen_k, 1), strategy.pop_size)

    global_best_J_hist = Float64[]
    stage_level_count = 0
    stage_level_counts = zeros(Int, max_stage)
    stage_histories = [Float64[] for _ in 1:max_stage]
    stage_first_use_level = fill(-1, max_stage)
    promotion_log = NamedTuple[]
    level_log = NamedTuple[]
    vis_history = NamedTuple[]
    termination_reason = :max_levels

    totals = _empty_fit_totals()
    total_screening_evals = 0
    total_invalid_screening_evals = 0
    total_polished_candidates = 0
    total_polish_budget_exhausted = 0
    total_polish_convergence_failures = 0
    total_rejected_diagnostic_candidates = 0
    total_rejected_diagnostic_budget_exhausted = 0
    total_rejected_diagnostic_convergence_failures = 0
    total_rejected_beats_best_selected = 0
    total_screening_time_s = 0.0
    total_polish_time_s = 0.0
    total_rejected_diagnostic_time_s = 0.0
    level_rank_agreements = Float64[]

    n_steps = min(strategy.n_levels, options.max_levels)

    if options.verbose >= 1
        log_info(
            "EvoGrowScreening search start",
            context = Dict(
                :dim => dim,
                :pop_size => strategy.pop_size,
                :n_levels => n_steps,
                :screen_k => screen_k,
                :polish_maxiters => strategy.polish_maxiters,
                :rejected_diagnostic_samples => strategy.rejected_diagnostic_samples,
                :screening_score => strategy.screening_score,
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
        allowed_terms = _allowed_terms(basis, current_stage)
        current_stage_terms = _current_stage_terms(basis, current_stage)

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

        candidates = vcat(pop, children)
        incumbent = isempty(global_best_J_hist) ? nothing : pop[1]

        screen_t0 = time()
        screening = [derivative_screening_diagnostics(ind.structure, basis, traj) for ind in candidates]
        level_screening_time_s = time() - screen_t0
        level_screening_evals = length(screening)
        level_invalid_screening_evals = count(s -> !s.valid, screening)

        scores = [_screening_score(s, strategy.screening_score) for s in screening]
        selected_idxs = Int[]
        if incumbent !== nothing
            incumbent_idx = findfirst(ind -> ind === incumbent, candidates)
            if incumbent_idx !== nothing
                push!(selected_idxs, incumbent_idx)
            end
        end
        for idx in sortperm(scores)
            if length(selected_idxs) >= screen_k
                break
            end
            if !(idx in selected_idxs) && isfinite(scores[idx])
                push!(selected_idxs, idx)
            end
        end
        if isempty(selected_idxs)
            selected_idxs = collect(1:min(screen_k, length(candidates)))
        end
        selected_set = Set(selected_idxs)
        rejected_ranked_idxs = [idx for idx in sortperm(scores) if !(idx in selected_set) && isfinite(scores[idx])]
        diagnostic_idxs = rejected_ranked_idxs[1:min(strategy.rejected_diagnostic_samples, length(rejected_ranked_idxs))]

        level_totals = _empty_fit_totals()
        level_polish_budget_exhausted = 0
        level_polish_convergence_failures = 0
        level_rejected_diagnostic_budget_exhausted = 0
        level_rejected_diagnostic_convergence_failures = 0
        polished = Individual[]
        measured_screen_scores = Float64[]
        measured_sim_losses = Float64[]

        polish_t0 = time()
        for idx in selected_idxs
            ind = candidates[idx]
            screen = screening[idx]
            p0 = screen.valid ? screen.params : nothing
            candidate = Individual(ind.structure, copy(ind.params), ind.loss, ind.objective)
            _, fit_meta = _evaluate_with_p0!(candidate, traj, basis, loss, polish_optimizer, strategy.λ, options, p0)
            _add_fit_stats!(level_totals, fit_meta)
            if _fit_stat(fit_meta, :optimizer_iteration_limit_hits) > 0
                level_polish_budget_exhausted += 1
            end
            if _fit_stat(fit_meta, :optimizer_failure_hits) > 0
                level_polish_convergence_failures += 1
            end
            if isfinite(ind.objective) && ind.objective <= candidate.objective
                candidate = Individual(ind.structure, copy(ind.params), ind.loss, ind.objective)
            end
            push!(polished, candidate)
            push!(measured_screen_scores, scores[idx])
            push!(measured_sim_losses, candidate.loss)
        end
        level_polish_time_s = time() - polish_t0

        best_selected_loss = isempty(polished) ? Inf : minimum(ind.loss for ind in polished)
        level_rejected_beats_best_selected = 0
        rejected_t0 = time()
        for idx in diagnostic_idxs
            ind = candidates[idx]
            screen = screening[idx]
            candidate = Individual(ind.structure, copy(ind.params), ind.loss, ind.objective)
            _, fit_meta = _evaluate_with_p0!(candidate, traj, basis, loss, polish_optimizer, strategy.λ, options, screen.params)
            _add_fit_stats!(level_totals, fit_meta)
            if _fit_stat(fit_meta, :optimizer_iteration_limit_hits) > 0
                level_rejected_diagnostic_budget_exhausted += 1
            end
            if _fit_stat(fit_meta, :optimizer_failure_hits) > 0
                level_rejected_diagnostic_convergence_failures += 1
            end
            if candidate.loss < best_selected_loss
                level_rejected_beats_best_selected += 1
            end
            push!(measured_screen_scores, scores[idx])
            push!(measured_sim_losses, candidate.loss)
        end
        level_rejected_diagnostic_time_s = time() - rejected_t0
        level_rank_agreement = _spearman_rho(measured_screen_scores, measured_sim_losses)
        push!(level_rank_agreements, level_rank_agreement)

        sort!(polished, by = x -> x.objective)
        pop = polished[1:min(strategy.pop_size, length(polished))]
        best = pop[1]

        push!(global_best_J_hist, best.objective)
        push!(stage_histories[current_stage], best.objective)
        stage_level_count += 1
        stage_level_counts[current_stage] += 1

        uses_current_stage_terms = _structure_uses_terms(best.structure, current_stage_terms)
        if uses_current_stage_terms && stage_first_use_level[current_stage] == -1
            stage_first_use_level[current_stage] = level
        end

        for key in keys(level_totals)
            if key in (:solver_retcodes, :optimizer_retcodes)
                _append_unique_strings!(totals[key], level_totals[key])
            else
                totals[key] += level_totals[key]
            end
        end

        level_elapsed_s = time() - level_t0
        level_parameter_overhead_s = max(0.0, level_totals[:fit_time_s] - level_totals[:solve_time_s])
        total_screening_evals += level_screening_evals
        total_invalid_screening_evals += level_invalid_screening_evals
        total_polished_candidates += length(selected_idxs)
        total_polish_budget_exhausted += level_polish_budget_exhausted
        total_polish_convergence_failures += level_polish_convergence_failures
        total_rejected_diagnostic_candidates += length(diagnostic_idxs)
        total_rejected_diagnostic_budget_exhausted += level_rejected_diagnostic_budget_exhausted
        total_rejected_diagnostic_convergence_failures += level_rejected_diagnostic_convergence_failures
        total_rejected_beats_best_selected += level_rejected_beats_best_selected
        total_screening_time_s += level_screening_time_s
        total_polish_time_s += level_polish_time_s
        total_rejected_diagnostic_time_s += level_rejected_diagnostic_time_s

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
                parameter_fits = level_totals[:parameter_fits],
                ode_solves = level_totals[:ode_solves],
                invalid_solves = level_totals[:invalid_solves],
                diverged_solves = level_totals[:diverged_solves],
                nonfinite_solves = level_totals[:nonfinite_solves],
                step_limit_solves = level_totals[:step_limit_solves],
                solver_unstable_solves = level_totals[:solver_unstable_solves],
                optimizer_limit_hits = level_totals[:optimizer_limit_hits],
                optimizer_iteration_limit_hits = level_totals[:optimizer_iteration_limit_hits],
                optimizer_safety_limit_hits = level_totals[:optimizer_safety_limit_hits],
                optimizer_failure_hits = level_totals[:optimizer_failure_hits],
                optimizer_unknown_retcode_hits = level_totals[:optimizer_unknown_retcode_hits],
                parameter_optimization_time_s = level_parameter_overhead_s,
                simulation_time_s = level_totals[:solve_time_s],
                solver_retcodes = copy(level_totals[:solver_retcodes]),
                optimizer_retcodes = copy(level_totals[:optimizer_retcodes]),
                screening_evals = level_screening_evals,
                invalid_screening_evals = level_invalid_screening_evals,
                polished_candidates = length(selected_idxs),
                polish_budget_exhausted = level_polish_budget_exhausted,
                polish_convergence_failures = level_polish_convergence_failures,
                rejected_diagnostic_candidates = length(diagnostic_idxs),
                rejected_diagnostic_budget_exhausted = level_rejected_diagnostic_budget_exhausted,
                rejected_diagnostic_convergence_failures = level_rejected_diagnostic_convergence_failures,
                rejected_beats_best_selected = level_rejected_beats_best_selected,
                screening_time_s = level_screening_time_s,
                polish_time_s = level_polish_time_s,
                rejected_diagnostic_time_s = level_rejected_diagnostic_time_s,
                rank_agreement_spearman = level_rank_agreement,
                screening_score_mode = strategy.screening_score,
                screening_score_best = minimum(scores),
                selected_screening_score_best = minimum(scores[selected_idxs]),
                improvement = isfinite(level_prev_best_objective) ? level_prev_best_objective - best.objective : Inf
            )
        )

        if strategy.level_callback !== nothing
            strategy.level_callback(level_log[end])
        end

        stop, reason, action = _stage_progression_decision(
            EvoGrow(
                progression = strategy.progression,
                usage = strategy.usage,
                n_levels = strategy.n_levels,
                pop_size = strategy.pop_size,
                max_terms_per_eq = strategy.max_terms_per_eq,
                λ = strategy.λ,
            ),
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
                continue
            end
            termination_reason = reason
            break
        end
    end

    best = pop[1]
    final_refit_meta = (;)
    final_refit_time_s = 0.0
    if isfinite(best.loss)
        final_t0 = time()
        _, final_refit_meta = _evaluate_with_p0!(best, traj, basis, loss, optimizer, strategy.λ, options, best.params)
        final_refit_time_s = time() - final_t0
        _add_fit_stats!(totals, final_refit_meta)
    end

    rank_values = [rho for rho in level_rank_agreements if isfinite(rho)]
    mean_rank_agreement = isempty(rank_values) ? NaN : sum(rank_values) / length(rank_values)

    if options.verbose >= 1
        log_info(
            "EvoGrowScreening search finished",
            context = Dict(
                :final_stage => current_stage,
                :best_loss => best.loss,
                :best_objective => best.objective,
                :n_params => length(best.params),
                :termination_reason => termination_reason,
                :total_screening_evals => total_screening_evals,
                :total_polished_candidates => total_polished_candidates,
                :total_rejected_diagnostic_candidates => total_rejected_diagnostic_candidates,
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
            total_loss_evals = totals[:loss_evals],
            total_invalid_evals = totals[:invalid_evals],
            total_parameter_fits = totals[:parameter_fits],
            total_ode_solves = totals[:ode_solves],
            total_invalid_solves = totals[:invalid_solves],
            total_diverged_solves = totals[:diverged_solves],
            total_nonfinite_solves = totals[:nonfinite_solves],
            total_step_limit_solves = totals[:step_limit_solves],
            total_solver_unstable_solves = totals[:solver_unstable_solves],
            total_optimizer_limit_hits = totals[:optimizer_limit_hits],
            total_optimizer_iteration_limit_hits = totals[:optimizer_iteration_limit_hits],
            total_optimizer_safety_limit_hits = totals[:optimizer_safety_limit_hits],
            total_optimizer_failure_hits = totals[:optimizer_failure_hits],
            total_optimizer_unknown_retcode_hits = totals[:optimizer_unknown_retcode_hits],
            total_parameter_optimization_time_s = max(0.0, totals[:fit_time_s] - totals[:solve_time_s]),
            total_simulation_time_s = totals[:solve_time_s],
            solver_retcodes = copy(totals[:solver_retcodes]),
            optimizer_retcodes = copy(totals[:optimizer_retcodes]),
            screening_budgets_active = strategy.screening_optimizer !== nothing,
            derivative_screening_active = true,
            final_stage = current_stage,
            termination_reason = termination_reason,
            progression_mode = strategy.progression.mode,
            usage_mode = strategy.usage.mode,
            screening_evals = total_screening_evals,
            invalid_screening_evals = total_invalid_screening_evals,
            polished_candidates = total_polished_candidates,
            polish_budget_exhausted = total_polish_budget_exhausted,
            polish_convergence_failures = total_polish_convergence_failures,
            rejected_diagnostic_candidates = total_rejected_diagnostic_candidates,
            rejected_diagnostic_budget_exhausted = total_rejected_diagnostic_budget_exhausted,
            rejected_diagnostic_convergence_failures = total_rejected_diagnostic_convergence_failures,
            rejected_beats_best_selected = total_rejected_beats_best_selected,
            screening_time_s = total_screening_time_s,
            polish_time_s = total_polish_time_s,
            rejected_diagnostic_time_s = total_rejected_diagnostic_time_s,
            rank_agreement_spearman = mean_rank_agreement,
            level_rank_agreements_spearman = level_rank_agreements,
            screen_k = screen_k,
            polish_maxiters = strategy.polish_maxiters,
            rejected_diagnostic_samples = strategy.rejected_diagnostic_samples,
            screening_score_mode = strategy.screening_score,
            final_refit_meta = final_refit_meta,
            final_refit_time_s = final_refit_time_s
        )
    )
end
