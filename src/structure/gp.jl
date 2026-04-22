# src/structure/gp.jl

using Random
using Printf

"""
    GPStructureSearch(; pop_size=50, n_generations=20, ...)

Standard genetic programming baseline for structure search.

Full basis is available from generation 1 (no staged complexity).
Used as comparison baseline against EvoGrow.

# Fields
- `pop_size`: population size
- `n_generations`: number of generations (also bounded by `options.max_levels`)
- `tournament_k`: tournament selection size
- `p_crossover`: probability of crossover per child
- `p_mutation`: probability of mutation per child
- `max_terms_per_eq`: hard cap on active terms per equation
- `init_min_terms`, `init_max_terms`: term count range for random initialization
- `λ`: complexity penalty weight (objective = loss + λ * n_params)
"""
Base.@kwdef struct GPStructureSearch <: AbstractStructureSearch
    pop_size::Int = 50
    n_generations::Int = 20
    tournament_k::Int = 3
    p_crossover::Float64 = 0.7
    p_mutation::Float64 = 0.3
    max_terms_per_eq::Int = 5
    init_min_terms::Int = 1
    init_max_terms::Int = 2
    λ::Float64 = 1e-3
end

"""
Individual in the GP population.
"""
mutable struct GPIndividual
    structure::StructureSpec
    params::Vector{Float64}
    loss::Float64
    objective::Float64
end

# ----------------------------
# Initialization
# ----------------------------

"Sample `n_terms` distinct indices from `1:n_basis`, sorted."
function _rand_terms(n_basis::Int, n_terms::Int)
    n_terms = max(1, min(n_terms, n_basis))
    return sort!(unique(rand(1:n_basis, n_terms)))
end

"Create one random `StructureSpec` with term counts drawn uniformly from `[min_terms, max_terms]`."
function _random_structure(dim::Int,
                           n_basis::Int;
                           min_terms::Int,
                           max_terms::Int,
                           max_terms_per_eq::Int)
    active = Vector{Vector{Int}}(undef, dim)
    for k in 1:dim
        nt = rand(min_terms:max_terms)
        nt = min(nt, max_terms_per_eq)
        active[k] = _rand_terms(n_basis, nt)
    end
    return StructureSpec(active)
end

"Initialize `strategy.pop_size` random individuals using the full basis."
function _init_population(strategy::GPStructureSearch, dim::Int, n_basis::Int)
    pop = GPIndividual[]
    for _ in 1:strategy.pop_size
        s = _random_structure(dim, n_basis;
                              min_terms = strategy.init_min_terms,
                              max_terms = strategy.init_max_terms,
                              max_terms_per_eq = strategy.max_terms_per_eq)
        push!(pop, GPIndividual(s, Float64[], Inf, Inf))
    end
    return pop
end

# ----------------------------
# Evaluation
# ----------------------------

"Fit parameters for `ind` in-place and compute loss and penalized objective."
function _evaluate!(ind::GPIndividual,
                    traj::Trajectory,
                    basis::AbstractBasis,
                    loss::AbstractLoss,
                    optimizer::AbstractOptimizer,
                    λ::Float64,
                    options::DiscoveryOptions)

    f!, n_params, _ = build_rhs(ind.structure, basis)
    p0 = pretune_parameters(ind.structure, basis, traj)
    params, lval, fit_meta = fit_parameters(optimizer, f!, traj, n_params, loss, options; p0 = p0)

    ind.params = params
    ind.loss = lval
    ind.objective = lval + λ * length(params)
    return ind, fit_meta
end

# ----------------------------
# Selection (Tournament)
# ----------------------------

"Select the best individual from a random tournament of size `k`."
function _tournament_select(pop::Vector{GPIndividual}, k::Int)
    k = max(1, min(k, length(pop)))
    best = pop[rand(1:length(pop))]
    for _ in 2:k
        cand = pop[rand(1:length(pop))]
        if cand.objective < best.objective
            best = cand
        end
    end
    return best
end

# ----------------------------
# Genetic operators
# ----------------------------

"Per-equation crossover: independently select each equation from `p1` or `p2` with equal probability."
function _crossover(p1::GPIndividual, p2::GPIndividual, dim::Int)
    active = Vector{Vector{Int}}(undef, dim)
    for k in 1:dim
        active[k] = (rand() < 0.5) ? copy(p1.structure.active_idxs[k]) : copy(p2.structure.active_idxs[k])
    end
    return StructureSpec(active)
end

"""
    _mutate(structure, dim, n_basis; max_terms_per_eq)

Apply one of three mutation operators with equal probability:
- add a random term to a random equation
- remove a random term from a random equation (if more than one remains)
- replace a random term with a different one
"""
function _mutate(structure::StructureSpec,
                 dim::Int,
                 n_basis::Int;
                 max_terms_per_eq::Int)

    k = rand(1:dim)
    terms = copy(structure.active_idxs[k])

    op = rand()
    if op < 0.34
        if length(terms) < max_terms_per_eq
            candidates = setdiff(1:n_basis, terms)
            if !isempty(candidates)
                push!(terms, rand(candidates))
                terms = sort!(unique(terms))
            end
        end
    elseif op < 0.67
        if length(terms) > 1
            deleteat!(terms, rand(1:length(terms)))
        end
    else
        candidates = setdiff(1:n_basis, terms)
        if !isempty(candidates)
            if isempty(terms)
                push!(terms, rand(candidates))
            else
                terms[rand(1:length(terms))] = rand(candidates)
            end
            terms = sort!(unique(terms))
            if isempty(terms)
                push!(terms, rand(1:n_basis))
            end
        end
    end

    new_idxs = [copy(v) for v in structure.active_idxs]
    new_idxs[k] = terms
    return StructureSpec(new_idxs)
end

# ----------------------------
# Main loop
# ----------------------------

"""
    search_structure(strategy::GPStructureSearch, traj, basis, loss, optimizer, options)

Standard GP search over `StructureSpec` individuals.

Uses tournament selection, per-equation crossover, and three-way mutation.
Elitism preserves the best individual each generation.
Stopping is handled by the shared `should_stop` criterion.
Full basis available from generation 1 (no staged complexity).

Returns a NamedTuple with: `structure`, `params`, `loss`, `objective`, `meta`.
"""
function search_structure(strategy::GPStructureSearch,
                          traj::Trajectory,
                          basis::AbstractBasis,
                          loss::AbstractLoss,
                          optimizer::AbstractOptimizer,
                          options::DiscoveryOptions)

    dim = size(traj.x, 2)
    n_basis = basis_num_terms(basis)

    pop = _init_population(strategy, dim, n_basis)
    total_loss_evals = 0
    total_invalid_evals = 0

    if options.verbose >= 1
        log_info(
            "GP search start",
            context = Dict(
                :dim => dim,
                :pop_size => strategy.pop_size,
                :n_generations => strategy.n_generations,
                :tournament_k => strategy.tournament_k,
                :p_crossover => strategy.p_crossover,
                :p_mutation => strategy.p_mutation,
                :n_basis => n_basis
            )
        )
    end

    # ---------------- INITIAL EVAL ----------------
    if options.verbose >= 2
        log_info("Evaluating initial population")
    end

    for (i, ind) in enumerate(pop)
        ind_ctx = Dict(:phase => "init", :individual => i, :pop_size => length(pop))

        done = options.verbose >= 2 ? time_block("initial individual $i", level=INFO, context=ind_ctx) : nothing

        if options.verbose >= 2
            log_info("Initial population evaluation", context=ind_ctx)
        end

        _, fit_meta = _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options)
        total_loss_evals += haskey(fit_meta, :loss_evals) ? fit_meta.loss_evals : 0
        total_invalid_evals += haskey(fit_meta, :invalid_evals) ? fit_meta.invalid_evals : 0

        if options.verbose >= 3
            log_debug(
                "Initial individual result",
                context = merge(
                    ind_ctx,
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
    end

    sort!(pop, by = x -> x.objective)
    best = pop[1]

    best_J_hist = Float64[best.objective]
    n_steps = min(strategy.n_generations, options.max_levels)

    for gen in 1:n_steps
        gen_ctx = Dict(:generation => gen)

        if options.verbose >= 1
            log_info("Generation start", context=gen_ctx)
        end

        new_pop = GPIndividual[]

        # Elitism
        push!(new_pop, GPIndividual(best.structure, best.params, best.loss, best.objective))

        # ---------------- CHILD GENERATION ----------------
        gen_done = options.verbose >= 2 ? time_block("generation $gen child generation", level=INFO, context=gen_ctx) : nothing

        if options.verbose >= 2
            log_info("Generating children", context=gen_ctx)
        end

        while length(new_pop) < strategy.pop_size
            p1 = _tournament_select(pop, strategy.tournament_k)
            p2 = _tournament_select(pop, strategy.tournament_k)

            child_struct = (rand() < strategy.p_crossover) ? _crossover(p1, p2, dim) : p1.structure

            if rand() < strategy.p_mutation
                child_struct = _mutate(child_struct, dim, n_basis;
                                       max_terms_per_eq = strategy.max_terms_per_eq)
            end

            push!(new_pop, GPIndividual(child_struct, Float64[], Inf, Inf))
        end

        if gen_done !== nothing
            gen_done()
        end

        if options.verbose >= 2
            log_info("Generated individuals", context=merge(gen_ctx, Dict(:n_generated => length(new_pop))))
        end

        # ---------------- EVALUATION ----------------
        if options.verbose >= 2
            log_info("Evaluating generation population", context=gen_ctx)
        end

        for (i, ind) in enumerate(new_pop)
            if !isfinite(ind.objective)
                ind_ctx = merge(gen_ctx, Dict(:individual => i, :pop_size => length(new_pop)))

                done = options.verbose >= 2 ? time_block("generation $gen individual $i", level=INFO, context=ind_ctx) : nothing

                if options.verbose >= 2
                    log_info("Generation individual evaluation", context=ind_ctx)
                end

                _, fit_meta = _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options)
                total_loss_evals += haskey(fit_meta, :loss_evals) ? fit_meta.loss_evals : 0
                total_invalid_evals += haskey(fit_meta, :invalid_evals) ? fit_meta.invalid_evals : 0

                if options.verbose >= 3
                    log_debug(
                        "Generation individual result",
                        context = merge(
                            ind_ctx,
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
            end
        end

        sort!(new_pop, by = x -> x.objective)
        pop = new_pop
        best = pop[1]

        push!(best_J_hist, best.objective)

        # ---------------- LOGGING ----------------
        if options.verbose >= 1
            log_info(
                "Best individual",
                context = merge(
                    gen_ctx,
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
                    gen_ctx,
                    Dict(
                        :structure => replace(structure_with_params_string(best.structure, basis, best.params), '\n' => ' ')
                    )
                )
            )
        end

        if options.verbose >= 3
            log_debug("Population snapshot", context=gen_ctx)
            for (i, ind) in enumerate(pop[1:min(5, length(pop))])
                log_debug(
                    "Top individual",
                    context = merge(
                        gen_ctx,
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

        # ---------------- STOPPING ----------------
        stop, reason = should_stop(best_J_hist, best.loss, gen, options)
        if stop
            if options.verbose >= 1
                log_info("Stopping", context=merge(gen_ctx, Dict(:reason => reason)))
            end
            break
        end
    end

    if options.verbose >= 1
        log_info(
            "GP search finished",
            context = Dict(
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
            total_loss_evals = total_loss_evals,
            total_invalid_evals = total_invalid_evals
        )
    )
end
