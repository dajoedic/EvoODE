using Random

"""
    discover(traj::Trajectory;
             structure,
             optimizer,
             basis,
             loss,
             options=DiscoveryOptions())

Run data-driven discovery of an interpretable ODE model from time series data.

This function orchestrates the full pipeline:

1) Structure search (e.g. EvoGrow)
2) Build RHS from structure + basis
3) Parameter optimization
4) Final simulation
5) Sanity check on final trajectory

All components are injected and replaceable via multiple dispatch.
"""
function discover(traj::Trajectory;
                  structure::AbstractStructureSearch,
                  optimizer::AbstractOptimizer,
                  basis::AbstractBasis,
                  loss::AbstractLoss,
                  options::DiscoveryOptions = DiscoveryOptions())

    Random.seed!(options.rng_seed)

    T   = length(traj.t)
    dim = size(traj.x, 2)

    if options.verbose >= 1
        println("EvoODE.discover: starting (T=$T, dim=$dim)")
    end

    # ------------------------------------------------------------
    # Basis handling (convenience: allow dim=0 placeholders)
    # ------------------------------------------------------------
    if hasproperty(basis, :dim) && getproperty(basis, :dim) == 0
        basis = default_polynomial_basis(dim)
        options.verbose >= 1 &&
            println("  basis was dim=0 -> using default_polynomial_basis(dim=$dim)")
    end

    # ------------------------------------------------------------
    # 1) Structure search
    # ------------------------------------------------------------
    struct_res = search_structure(structure, traj, basis, loss, optimizer, options)

    discovered_structure = struct_res.structure
    struct_meta = haskey(struct_res, :meta) ? struct_res.meta : (;)

    # ------------------------------------------------------------
    # 2) Build RHS from structure + basis
    # ------------------------------------------------------------
    f!, n_params, build_meta = build_rhs(discovered_structure, basis)

    # ------------------------------------------------------------
    # 3) Parameter optimization (FINAL fit)
    # ------------------------------------------------------------
	params = haskey(struct_res, :params) ? struct_res.params : nothing
	lval   = haskey(struct_res, :loss)   ? struct_res.loss   : Inf
	opt_meta = (;)

	if params === nothing
		params, lval, opt_meta = fit_parameters(optimizer, f!, traj, n_params, loss, options)
	end


    # ------------------------------------------------------------
    # 4) Final simulation (must use SAME numerical settings)
    # ------------------------------------------------------------
    Yhat = simulate(
        f!,
        params,
        traj;
        abstol    = optimizer.abstol,
        reltol    = optimizer.reltol,
        maxiters  = optimizer.maxiters_solve,
        clamp_val = optimizer.clamp_val,
        options   = options
    )

    # ------------------------------------------------------------
    # 5) Sanity check: recompute loss on simulated trajectory
    # ------------------------------------------------------------
    loss_sanity = evaluate_loss(loss, Yhat, traj.x)

    if options.verbose >= 1
        println("Sanity: loss(fit)=", lval,
                "  loss(simulate)=", loss_sanity,
                "  Δ=", (loss_sanity - lval))
    end

    # ------------------------------------------------------------
    # Return unified result object
    # ------------------------------------------------------------
    return DiscoveryResult(
        discovered_structure,
        params,
        lval,
        lval,  # Phase 1: objective == loss
        (
            structure = struct_meta,
            build     = build_meta,
            optimize  = opt_meta,
            sanity    = (loss_simulate = loss_sanity,),
            prediction = (Yhat = Yhat,)
        )
    )
end


"""
    discover(t::AbstractVector, X::AbstractMatrix; kwargs...)

Convenience overload accepting raw time vector and state matrix.
"""
function discover(t::AbstractVector, X::AbstractMatrix; kwargs...)
    traj = Trajectory(Vector{Float64}(t), Matrix{Float64}(X))
    return discover(traj; kwargs...)
end
