# src/structure/gp.jl

using Random
using Printf

"""
    GPStructureSearch(; pop_size=50,
                       n_generations=20,
                       tournament_k=3,
                       p_crossover=0.7,
                       p_mutation=0.3,
                       max_terms_per_eq=5,
                       init_min_terms=1,
                       init_max_terms=2,
                       λ=1e-3)

Genetic-programming-like structure search over discrete StructureSpec models.

Representation:
- One individual encodes a `StructureSpec` via `active_idxs::Vector{Vector{Int}}`,
  i.e. a set of basis term indices per equation.

Operators:
- Tournament selection
- Crossover: swap term-sets between parents (per equation)
- Mutation: add/remove/replace one term in one equation

Objective:
- `J = loss + λ * n_params`

Notes:
- This is Phase-1 pragmatic GP: it keeps your current `build_rhs(...)` pipeline intact.
- Later you can introduce real expression trees without changing the public API.
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

mutable struct GPIndividual
    structure::StructureSpec
    params::Vector{Float64}
    loss::Float64
    objective::Float64
end

# ----------------------------
# Initialization
# ----------------------------

function _rand_terms(n_basis::Int, n_terms::Int)
    n_terms = max(1, min(n_terms, n_basis))
    return sort!(unique(rand(1:n_basis, n_terms)))
end

function _random_structure(dim::Int, n_basis::Int; min_terms::Int, max_terms::Int, max_terms_per_eq::Int)
    active = Vector{Vector{Int}}(undef, dim)
    for k in 1:dim
        nt = rand(min_terms:max_terms)
        nt = min(nt, max_terms_per_eq)
        active[k] = _rand_terms(n_basis, nt)
    end
    return StructureSpec(active)
end

function _init_population(strategy::GPStructureSearch, dim::Int, n_basis::Int)
    pop = GPIndividual[]
    for _ in 1:strategy.pop_size
        s = _random_structure(dim, n_basis;
                              min_terms=strategy.init_min_terms,
                              max_terms=strategy.init_max_terms,
                              max_terms_per_eq=strategy.max_terms_per_eq)
        push!(pop, GPIndividual(s, Float64[], Inf, Inf))
    end
    return pop
end

# ----------------------------
# Evaluation
# ----------------------------

function _evaluate!(ind::GPIndividual,
                    traj::Trajectory,
                    basis::AbstractBasis,
                    loss::AbstractLoss,
                    optimizer::AbstractOptimizer,
                    λ::Float64,
                    options::DiscoveryOptions)

    # build_rhs must be provided by the basis module
    f!, n_params, _ = build_rhs(ind.structure, basis)

    # parameter fitting must be provided by the optimizer module
    params, lval, _ = fit_parameters(optimizer, f!, traj, n_params, loss, options)

    ind.params = params
    ind.loss = lval
    ind.objective = lval + λ * length(params)
    return ind
end

# ----------------------------
# Selection (Tournament)
# ----------------------------

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

function _crossover(p1::GPIndividual, p2::GPIndividual, dim::Int)
    # Equation-wise swap: for each equation choose term list from one of parents
    active = Vector{Vector{Int}}(undef, dim)
    for k in 1:dim
        if rand() < 0.5
            active[k] = copy(p1.structure.active_idxs[k])
        else
            active[k] = copy(p2.structure.active_idxs[k])
        end
    end
    return StructureSpec(active)
end

function _mutate!(structure::StructureSpec, dim::Int, n_basis::Int; max_terms_per_eq::Int)
    # pick equation
    k = rand(1:dim)
    terms = copy(structure.active_idxs[k])

    op = rand()
    if op < 0.34
        # ADD term
        if length(terms) < max_terms_per_eq
            candidates = setdiff(1:n_basis, terms)
            if !isempty(candidates)
                push!(terms, rand(candidates))
                terms = sort!(unique(terms))
            end
        end
    elseif op < 0.67
        # REMOVE term (keep at least 1)
        if length(terms) > 1
            deleteat!(terms, rand(1:length(terms)))
        end
    else
        # REPLACE term
        candidates = setdiff(1:n_basis, terms)
        if !isempty(candidates)
            if isempty(terms)
                push!(terms, rand(candidates))
            else
                terms[rand(1:length(terms))] = rand(candidates)
            end
            terms = sort!(unique(terms))
            if isempty(terms)
                # Safety: never allow empty equation
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

Runs GP-style structure search and returns:

- `structure`: best found `StructureSpec`
- `meta`: NamedTuple with diagnostics and pretty-print string
"""
function search_structure(strategy::GPStructureSearch,
                          traj::Trajectory,
                          basis::AbstractBasis,
                          loss::AbstractLoss,
                          optimizer::AbstractOptimizer,
                          options::DiscoveryOptions)

    dim = size(traj.x, 2)
    n_basis = basis_num_terms(basis)

    # Initial population
    pop = _init_population(strategy, dim, n_basis)

    # Evaluate initial population
    for ind in pop
        _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options)
    end
    sort!(pop, by = x -> x.objective)

    best = pop[1]
    best_J_prev = best.objective

    for gen in 1:strategy.n_generations
        options.verbose >= 1 && println("\nGen $gen")

        new_pop = GPIndividual[]
        # Elitism: keep best
        push!(new_pop, GPIndividual(best.structure, best.params, best.loss, best.objective))

        while length(new_pop) < strategy.pop_size
            # Parent selection
            p1 = _tournament_select(pop, strategy.tournament_k)
            p2 = _tournament_select(pop, strategy.tournament_k)

            # Recombine
            child_struct = (rand() < strategy.p_crossover) ? _crossover(p1, p2, dim) : p1.structure

            # Mutate
            if rand() < strategy.p_mutation
                child_struct = _mutate!(child_struct, dim, n_basis; max_terms_per_eq=strategy.max_terms_per_eq)
            end

            push!(new_pop, GPIndividual(child_struct, Float64[], Inf, Inf))
        end

        # Evaluate new population
        for ind in new_pop
            if !isfinite(ind.objective)
                _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options)
            end
        end

        sort!(new_pop, by = x -> x.objective)
        pop = new_pop

        best = pop[1]

        if options.verbose >= 1
            println("  Best J: ", best.objective,
                    " | loss=", best.loss,
                    " | n_params=", length(best.params))
        end
        if options.verbose >= 2
            println("  Best structure:")
            println(replace(structure_with_params_string(best.structure, basis, best.params), '\n' => ' '))
        end
        if options.verbose >= 3
            println("  Population snapshot (top 5):")
            for (i, ind) in enumerate(pop[1:min(5, length(pop))])
                println("    #$i  J=$(ind.objective)  loss=$(ind.loss)  n_params=$(length(ind.params))")
            end
        end

        # Early stopping (simple, consistent with EvoGrow Phase-1)
        if best.loss < 1e-8
            options.verbose >= 1 && println("  -> Loss < 1e-8, stopping at generation $gen.")
            break
        end

        improvement = best_J_prev - best.objective
        if improvement < 1e-4
            options.verbose >= 1 && println("  -> No significant improvement (ΔJ=$(round(improvement, digits=6))). Stop at generation $gen.")
            break
        end
        best_J_prev = best.objective
    end

    return (structure = best.structure,
            meta = (best_loss = best.loss,
                    best_objective = best.objective,
                    best_structure_pretty = structure_with_params_string(best.structure, basis, best.params)))
end
