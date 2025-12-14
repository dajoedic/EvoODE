# src/structure.jl

############################
# Basis functions & structure
############################

"""
    BasisTerm

Represents a single basis function ϕ(u, t), e.g. u₁, u₂, u₁², u₁*u₂, ...
- `name`: symbolic name used in pretty-printing
- `func`: callable (u, t) -> Float64
"""
struct BasisTerm
    name::String
    func::Function   # (u, t) -> Float64
end

"""
Convenience alias: a basis library is just a vector of basis terms.
"""
const BasisLibrary = Vector{BasisTerm}

"""
    StructureSpec

Describes which basis terms are active in which state equation.

`active_idxs[k]` = vector of indices into the `BasisLibrary`
                   for the k-th ODE component (du_k / dt).
"""
struct StructureSpec
    active_idxs::Vector{Vector{Int}}  # length = dim, each entry: indices into basis
end

"""
    default_basis_library(dim) -> BasisLibrary

Constructs a simple basis library for `dim`-dimensional systems.

For `dim = 2` this yields:
    u1, u2, u1^2, u2^2, u1*u2
"""
function default_basis_library(dim::Int)::BasisLibrary
    terms = BasisLibrary()

    # linear terms u_i
    for i in 1:dim
        push!(terms, BasisTerm("u$i", (u, t) -> u[i]))
    end

    # quadratic terms u_i^2
    for i in 1:dim
        push!(terms, BasisTerm("u$i^2", (u, t) -> u[i]^2))
    end

    # simple cross term u1*u2 for dim ≥ 2
    if dim >= 2
        push!(terms, BasisTerm("u1*u2", (u, t) -> u[1] * u[2]))
    end

    return terms
end

"""
    build_model(structure, basis) -> (f!, n_params)

Builds an ODE right-hand side

    du[k] = sum_j p[idx] * ϕ_j(u, t)

where ϕ_j are the basis functions whose indices are listed in
`structure.active_idxs[k]`.

Returns:
- `f!(du, u, p, t)` : ODE function compatible with DifferentialEquations.jl
- `n_params :: Int` : total number of parameters (length of `p`)
"""
function build_model(structure::StructureSpec, basis::BasisLibrary)
    # total number of parameters = sum over all active terms in all equations
    n_params = sum(length(idxs) for idxs in structure.active_idxs)

    function f!(du, u, p, t)
        idx = 1
        # loop over equations du_k
        for k in 1:length(structure.active_idxs)
            acc = 0.0
            # loop over active basis terms for equation k
            for j in structure.active_idxs[k]
                acc += p[idx] * basis[j].func(u, t)
                idx += 1
            end
            du[k] = acc
        end
    end

    return f!, n_params
end

"""
    random_structure(dim, basis, max_terms_per_eq) -> StructureSpec

Creates a random structure:
for each equation, chooses between 1 and `max_terms_per_eq` basis functions
uniformly at random (without duplicates).
"""
function random_structure(dim::Int,
                          basis::BasisLibrary,
                          max_terms_per_eq::Int)
    active = Vector{Vector{Int}}(undef, dim)
    n_basis = length(basis)

    for k in 1:dim
        n_terms = rand(1:max_terms_per_eq)
        # sample indices, remove duplicates, keep them sorted for readability
        active[k] = sort(unique(rand(1:n_basis, n_terms)))
    end

    return StructureSpec(active)
end

############################
# Individuals & EvoGrow
############################

"""
    Individual

Represents a single model in the population:

- `structure` : which basis functions are active in each equation
- `params`    : fitted parameters (vector of Float64)
- `loss`      : data-fit (e.g. MSE on trajectories)
- `objective` : scalar objective, typically loss + λ * (#parameters)
"""
mutable struct Individual
    structure::StructureSpec
    params::Vector{Float64}
    loss::Float64
    objective::Float64
end

"""
Abstract base type for search strategies (EvoGrow, later maybe others).
"""
abstract type AbstractSearchStrategy end

"""
    EvoGrow <: AbstractSearchStrategy

Configuration for the EvoGrow structure search:

- `pop_size`           : population size
- `n_levels`           : number of growth levels
- `children_per_parent`: number of children per parent
- `max_terms_per_eq`   : max number of active basis terms per equation
- `λ`                  : regularization weight (e.g. J = loss + λ * n_params)
"""
struct EvoGrow <: AbstractSearchStrategy
    pop_size::Int
    n_levels::Int
    children_per_parent::Int
    max_terms_per_eq::Int
    λ::Float64
end

"""
    init_population(strategy, dim, basis) -> Vector{Individual}

Initializes a population of very simple models.

Current scheme:
- For each individual
  - For each equation: exactly one random basis term is activated.
"""
function init_population(strategy::EvoGrow,
                         dim::Int,
                         basis::BasisLibrary)::Vector{Individual}
    pop = Vector{Individual}()
    n_basis = length(basis)

    for _ in 1:strategy.pop_size
        # Each equation: one random active term
        active = Vector{Vector{Int}}(undef, dim)
        for k in 1:dim
            active[k] = [rand(1:n_basis)]
        end
        structure = StructureSpec(active)
        push!(pop, Individual(structure, Float64[], Inf, Inf))
    end

    return pop
end

"""
    evaluate!(ind, basis, traj; λ, maxiters) -> Individual

Evaluates an individual by:

1. Building a concrete ODE model from its structure.
2. Fitting parameters on the given trajectory.
3. Setting
   - `ind.loss`      = data-fit
   - `ind.objective` = loss + λ * (#parameters)
"""
function evaluate!(ind::Individual,
                   basis::BasisLibrary,
                   traj::Trajectory;
                   λ::Float64,
                   maxiters::Int)

    f!, n_params = build_model(ind.structure, basis)
    res = fit_parameters(f!, traj, n_params; maxiters = maxiters)

    ind.params    = res.p
    ind.loss      = res.loss
    ind.objective = res.loss + λ * length(res.p)

    return ind
end

"""
    expand(ind, basis; n_children, max_terms_per_eq) -> Vector{Individual}

Creates children by **growing** the structure:

- Copy parent's structure.
- Pick a random equation.
- If that equation has free capacity (below `max_terms_per_eq`)
  and there exist unused basis terms, add exactly one new basis term
  to that equation.
"""
function expand(ind::Individual,
                basis::BasisLibrary;
                n_children::Int,
                max_terms_per_eq::Int)

    children = Individual[]
    dim      = length(ind.structure.active_idxs)
    n_basis  = length(basis)

    for _ in 1:n_children
        # deep-ish copy of the active index sets
        new_idxs = [copy(v) for v in ind.structure.active_idxs]

        # choose a random equation
        k = rand(1:dim)

        existing   = new_idxs[k]
        candidates = setdiff(1:n_basis, existing)

        if !isempty(candidates) && length(existing) < max_terms_per_eq
            j = rand(candidates)
            push!(new_idxs[k], j)
        end

        new_struct = StructureSpec(new_idxs)
        push!(children, Individual(new_struct, Float64[], Inf, Inf))
    end

    return children
end

"""
    search_structure(strategy::EvoGrow, traj, basis; maxiters=300)

Main EvoGrow loop:

1. Initialize a population of simple models.
2. For each level:
   - Evaluate all parents.
   - Create children by expanding parents (adding basis terms).
   - Evaluate children.
   - Select the best `pop_size` individuals (parents + children)
     by objective value.
   - Log best model (objective, loss, structure with parameters).
   - Apply early stopping:
       * loss < 1e-8  → "perfect enough"
       * negligible improvement in objective across levels

Returns a named tuple containing:
- `structure`
- `params`
- `loss`
- `objective`
- `basis`
"""
function search_structure(strategy::EvoGrow,
                          traj::Trajectory,
                          basis::BasisLibrary;
                          maxiters::Int = 300)

    dim = size(traj.x, 2)
    pop = init_population(strategy, dim, basis)

    prev_best_J = Inf

    for level in 1:strategy.n_levels
        println("\nLevel $level")

        # --- evaluate parents (only if not evaluated yet) ---
        for ind in pop
            if !isfinite(ind.objective)
                evaluate!(ind, basis, traj; λ = strategy.λ, maxiters = maxiters)
            end
        end

        # --- generate children via structural expansion ---
        children = Individual[]
        for ind in pop
            append!(
                children,
                expand(ind, basis;
                       n_children      = strategy.children_per_parent,
                       max_terms_per_eq = strategy.max_terms_per_eq),
            )
        end

        # --- evaluate children ---
        for child in children
            evaluate!(child, basis, traj; λ = strategy.λ, maxiters = maxiters)
        end

        # --- selection: keep best pop_size by objective ---
        all_inds = vcat(pop, children)
        sort!(all_inds, by = ind -> ind.objective)
        pop = all_inds[1:strategy.pop_size]

        # --- logging: best model for this level ---
        best = pop[1]
        println("  Best J: ", best.objective,
                " | loss=", best.loss,
                " | n_params=", length(best.params))

        println("  Struktur:")
        p   = best.params
        idx = 1
        for eq_index in 1:length(best.structure.active_idxs)
            active_terms = best.structure.active_idxs[eq_index]
            terms_with_params = String[]
            for term_idx in active_terms
                coef = p[idx]
                name = basis[term_idx].name
                push!(terms_with_params,
                      "($(round(coef, digits = 4)))*$name")
                idx += 1
            end
            println("    du_$eq_index = " * join(terms_with_params, " + "))
        end

        # --- early stopping conditions ---

        # 1) Almost perfect fit
        if best.loss < 1e-8
            println("  -> Loss < 1e-8, model is 'good enough'. Stopping after level $level.")
            break
        end

        # 2) Very small improvement in objective
        improvement = prev_best_J - best.objective
        if prev_best_J < Inf && improvement < 1e-4
            println("  -> No significant improvement (ΔJ = $(round(improvement, digits = 6))). Stopping after level $level.")
            break
        end

        prev_best_J = best.objective
    end

    best = pop[1]
    return (structure = best.structure,
            params    = best.params,
            loss      = best.loss,
            objective = best.objective,
            basis     = basis)
end
