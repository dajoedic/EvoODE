using Random
using Printf

"""
EvoGrow structure search strategy.

- pop_size: population size
- n_levels: number of growth levels
- children_per_parent: number of children sampled per parent per level
- max_terms_per_eq: maximum number of active terms per equation
- λ: complexity penalty (objective = loss + λ * n_params)
"""
Base.@kwdef struct EvoGrow <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
end

mutable struct Individual
    structure::StructureSpec
    params::Vector{Float64}
    loss::Float64
    objective::Float64
end

function _init_population(strategy::EvoGrow, dim::Int, n_basis::Int)
    pop = Individual[]
    for _ in 1:strategy.pop_size
        active = Vector{Vector{Int}}(undef, dim)
        for k in 1:dim
            active[k] = [rand(1:n_basis)]
        end
        push!(pop, Individual(StructureSpec(active), Float64[], Inf, Inf))
    end
    return pop
end

function _expand(ind::Individual, dim::Int, n_basis::Int; n_children::Int, max_terms_per_eq::Int)
    children = Individual[]
    for _ in 1:n_children
        new_idxs = [copy(v) for v in ind.structure.active_idxs]
        k = rand(1:dim)

        existing = new_idxs[k]
        candidates = setdiff(1:n_basis, existing)

        if !isempty(candidates) && length(existing) < max_terms_per_eq
            push!(new_idxs[k], rand(candidates))
        end

        push!(children, Individual(StructureSpec(new_idxs), Float64[], Inf, Inf))
    end
    return children
end

function _evaluate!(ind::Individual,
                    traj::Trajectory,
                    basis::AbstractBasis,
                    loss::AbstractLoss,
                    optimizer::AbstractOptimizer,
                    λ::Float64,
                    options::DiscoveryOptions)

    # Build model for this structure
    f!, n_params, _ = build_rhs(ind.structure, basis)

    # Fit parameters
    params, lval, _ = fit_parameters(optimizer, f!, traj, n_params, loss, options)

    ind.params = params
    ind.loss = lval
    ind.objective = lval + λ * length(params)
    return ind
end


"""
    search_structure(strategy::EvoGrow, traj, basis, loss, optimizer, options)

Incremental evolutionary growth:
- start with 1-term-per-equation models
- each level: evaluate parents, generate children by adding one term, evaluate children
- select best `pop_size` by objective
"""
function search_structure(strategy::EvoGrow,
                          traj::Trajectory,
                          basis::AbstractBasis,
                          loss::AbstractLoss,
                          optimizer::AbstractOptimizer,
                          options::DiscoveryOptions)

    dim = size(traj.x, 2)
    n_basis = basis_num_terms(basis)

    pop = _init_population(strategy, dim, n_basis)
	
	best_J_hist = Float64[]

    for level in 1:strategy.n_levels
        options.verbose >= 1 && println("\nLevel $level")

        # Evaluate parents (lazy)
        for ind in pop
            if !isfinite(ind.objective)
                _evaluate!(ind, traj, basis, loss, optimizer, strategy.λ, options)
            end
        end

        # Generate children
        children = Individual[]
        for ind in pop
            append!(children,
                    _expand(ind, dim, n_basis;
                            n_children = strategy.children_per_parent,
                            max_terms_per_eq = strategy.max_terms_per_eq))
        end

        # Evaluate children
        for child in children
            _evaluate!(child, traj, basis, loss, optimizer, strategy.λ, options)
        end

        # Select best
        all_inds = vcat(pop, children)
        sort!(all_inds, by = x -> x.objective)
        pop = all_inds[1:strategy.pop_size]

        best = pop[1]
		
		push!(best_J_hist, best.objective)

		stop, reason = should_stop(
			best_J_hist,
			best.loss,
			level,
			options
		)

		if stop
			options.verbose >= 1 && println("  -> stopping: ", reason)
			break
		end


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

    end

	best = pop[1]
	return (
		structure = best.structure,
		params    = best.params,
		loss      = best.loss,
		objective = best.objective,
		meta      = (
			best_structure_pretty = structure_with_params_string(best.structure, basis, best.params),
		)
	)

end
