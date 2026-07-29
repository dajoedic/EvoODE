include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

function _system3_trajectory()
    t_grid = collect(range(0.0, 2.0; length = 25))
    r = 0.79
    K = 74.3
    u0 = 7.3
    x = reshape([K / (1.0 + (K / u0 - 1.0) * exp(-r * t)) for t in t_grid], :, 1)
    return Trajectory(t_grid, x)
end

function _system11_trajectory()
    t_grid = collect(range(0.0, 1.0; length = 25))
    u0 = 3.4
    x = reshape([1.0 / sqrt(2.0 * t + 1.0 / u0^2) for t in t_grid], :, 1)
    return Trajectory(t_grid, x)
end

function _run_scalar_smoke(label::String, traj::Trajectory)
    strategy = EvoGrowV3(
        pop_size = 4,
        n_levels = 5,
        children_per_parent = 1,
        max_terms_per_eq = 4,
        progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 2),
        usage = StageUsagePolicy(mode = :hard),
        use_pretuning = false,
    )
    optimizer = BFGSOptimizer(
        maxiters = 5,
        abstol = 1e-6,
        reltol = 1e-6,
        maxiters_solve = 10_000,
        time_limit_s = 30.0,
        reject_nonfinite = false,
        divergence_limit = Inf,
    )
    options = DiscoveryOptions(
        rng_seed = 42,
        verbose = 0,
        min_levels = 2,
        max_levels = 5,
        loss_tol = 1e-10,
        plateau_window = 2,
        plateau_tol = 1e-4,
    )

    result = discover(
        traj;
        structure = strategy,
        optimizer = optimizer,
        basis = default_staged_polynomial_basis(1),
        loss = MSELoss(),
        options = options,
    )
    meta = result.meta.structure

    if length(result.structure.active_idxs) != 1 || isempty(result.structure.active_idxs[1])
        error("$label did not return a valid scalar structure")
    end
    if !isfinite(result.loss)
        error("$label returned a non-finite loss")
    end
    if length(meta.eq_residual_log) != 1 || isempty(meta.eq_residual_log[1])
        error("$label did not populate eq_residual_log")
    end
    if length(meta.eq_promotion_levels) != 1
        error("$label did not populate eq_promotion_levels container")
    end

    println(
        label,
        ": loss=", result.loss,
        " final_stage=", meta.final_stage,
        " eq_final_stages=", meta.eq_final_stages,
        " eq_residual_log=", meta.eq_residual_log,
        " eq_promotion_levels=", meta.eq_promotion_levels,
        " derivative_residual_fallback=", meta.derivative_residual_fallback,
        " structure=", result.structure.active_idxs
    )
end

_run_scalar_smoke("system3", _system3_trajectory())
_run_scalar_smoke("system11", _system11_trajectory())
