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
        log_info(
            "EvoODE.discover start",
            context = Dict(
                :T => T,
                :dim => dim,
                :structure => nameof(typeof(structure)),
                :optimizer => nameof(typeof(optimizer)),
                :basis => nameof(typeof(basis)),
                :loss => nameof(typeof(loss)),
                :rng_seed => options.rng_seed
            )
        )
    end

    # ------------------------------------------------------------
    # Basis handling (convenience: allow dim=0 placeholders)
    # ------------------------------------------------------------
    if hasproperty(basis, :dim) && getproperty(basis, :dim) == 0
        basis = default_polynomial_basis(dim)
        if options.verbose >= 1
            log_info(
                "Basis fallback applied",
                context = Dict(
                    :new_basis => nameof(typeof(basis)),
                    :dim => dim
                )
            )
        end
    end

    # ------------------------------------------------------------
    # 1) Structure search
    # ------------------------------------------------------------
    search_done = nothing
    if options.verbose >= 1
        search_done = time_block(
            "structure search",
            level = INFO,
            context = Dict(
                :structure => nameof(typeof(structure))
            )
        )
    end

    sres = search_structure(structure, traj, basis, loss, optimizer, options)

    if options.verbose >= 1 && search_done !== nothing
        search_done()
    end

    discovered_structure = sres.structure
    params               = sres.params
    search_loss          = sres.loss
    search_objective     = sres.objective
    struct_meta          = haskey(sres, :meta) ? sres.meta : (;)

    if options.verbose >= 1
        log_info(
            "Structure search finished",
            context = Dict(
                :search_loss => search_loss,
                :search_objective => search_objective,
                :n_params => length(params)
            )
        )
    end

    # ------------------------------------------------------------
    # 2) Build RHS from structure + basis
    # ------------------------------------------------------------
    build_done = nothing
    if options.verbose >= 2
        build_done = time_block("build_rhs", level = INFO)
    end

    f!, n_params, build_meta = build_rhs(discovered_structure, basis)

    if options.verbose >= 2 && build_done !== nothing
        build_done()
    end

    # Guard against inconsistent structure search output.
    if length(params) != n_params
        error(
            "Structure search parameter contract violated: " *
            "expected $(n_params) parameters from returned structure, " *
            "received $(length(params)) from $(nameof(typeof(structure))); " *
            "returned_structure=$(repr(discovered_structure))"
        )
    end
    opt_meta = (method = "from_structure_search",)

    # ------------------------------------------------------------
    # 3) Final simulation
    # Use optimizer-specific settings if available
    # ------------------------------------------------------------
    sim_done = nothing
    if options.verbose >= 1
        sim_done = time_block("final simulation", level = INFO)
    end

    if optimizer isa BFGSOptimizer
        Yhat = simulate(
            f!,
            params,
            traj;
            abstol    = optimizer.abstol,
            reltol    = optimizer.reltol,
            maxiters  = optimizer.maxiters_solve,
            clamp_val = optimizer.clamp_val,
            reject_nonfinite = optimizer.reject_nonfinite,
            divergence_limit = optimizer.divergence_limit,
            options   = options
        )
    else
        Yhat = simulate(f!, params, traj; options=options)
    end

    if options.verbose >= 1 && sim_done !== nothing
        sim_done()
    end

    # ------------------------------------------------------------
    # 4) Sanity check: validated final loss
    # ------------------------------------------------------------
    loss_sanity = evaluate_loss(loss, Yhat, traj.x)

    if options.verbose >= 1
        log_info(
            "Sanity check",
            context = Dict(
                :loss_search => search_loss,
                :loss_simulate => loss_sanity,
                :delta => loss_sanity - search_loss
            )
        )
    end

    # ------------------------------------------------------------
    # Return unified result object
    # ------------------------------------------------------------
    if options.verbose >= 1
        log_info(
            "EvoODE.discover finished",
            context = Dict(
                :final_loss => loss_sanity,
                :final_objective => search_objective,
                :n_params => length(params)
            )
        )
    end

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
