# src/core/discover.jl

using Random

"""
    discover(traj::Trajectory;
             structure,
             optimizer,
             basis,
             loss,
             options=DiscoveryOptions())

Run data-driven discovery of an interpretable ODE model from `traj`.

Pipeline:
1) structure search
2) build RHS from discovered structure + basis
3) simulate final model using discovered parameters
4) validate loss on final simulated trajectory

Notes:
- `search_structure(...)` is expected to return the best structure together with
  fitted parameters, loss, objective, and metadata.
- `discover(...)` does NOT blindly refit parameters again.
- The returned `loss` in `DiscoveryResult` is the validated loss on the final
  simulated trajectory (`loss_sanity`).
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
        if options.verbose >= 1
            println("  basis was dim=0 -> using default_polynomial_basis(dim=$dim)")
        end
    end

    # ------------------------------------------------------------
    # 1) Structure search
    # ------------------------------------------------------------
    sres = search_structure(structure, traj, basis, loss, optimizer, options)

    discovered_structure = sres.structure
    params               = sres.params
    search_loss          = sres.loss
    search_objective     = sres.objective
    struct_meta          = haskey(sres, :meta) ? sres.meta : (;)

    # ------------------------------------------------------------
    # 2) Build RHS from structure + basis
    # ------------------------------------------------------------
    f!, n_params, build_meta = build_rhs(discovered_structure, basis)

    # Guard against inconsistent structure search output
    if length(params) != n_params
        if options.verbose >= 1
            println("  WARNING: parameter count mismatch after structure search.")
            println("           expected $n_params but got $(length(params)).")
            println("           Re-fitting parameters once for consistency.")
        end

        params, search_loss, opt_meta =
            fit_parameters(optimizer, f!, traj, n_params, loss, options)
    else
        opt_meta = (method = "from_structure_search",)
    end

    # ------------------------------------------------------------
    # 3) Final simulation
    # Use optimizer-specific settings if available
    # ------------------------------------------------------------
    if optimizer isa BFGSOptimizer
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
    else
        Yhat = simulate(f!, params, traj; options=options)
    end

    # ------------------------------------------------------------
    # 4) Sanity check: validated final loss
    # ------------------------------------------------------------
    loss_sanity = evaluate_loss(loss, Yhat, traj.x)

    if options.verbose >= 1
        println("Sanity: loss(search)=", search_loss,
                "  loss(simulate)=", loss_sanity,
                "  Δ=", (loss_sanity - search_loss))
    end

    # ------------------------------------------------------------
    # Return unified result object
    # ------------------------------------------------------------
    return DiscoveryResult(
        discovered_structure,
        params,
        loss_sanity,      # validated final loss
        search_objective, # objective from structure search
        (
            structure = struct_meta,
            build     = build_meta,
            optimize  = opt_meta,
            search    = (
                loss = search_loss,
                objective = search_objective,
            ),
            prediction = (
                Yhat = Yhat,
            ),
            sanity = (
                loss_simulate = loss_sanity,
                delta = loss_sanity - search_loss,
            )
        )
    )
end

"""
    discover(t::AbstractVector, X::AbstractMatrix; kwargs...)

Convenience overload: accepts raw time vector and state matrix.
"""
function discover(t::AbstractVector, X::AbstractMatrix; kwargs...)
    traj = Trajectory(Vector{Float64}(t), Matrix{Float64}(X))
    return discover(traj; kwargs...)
end