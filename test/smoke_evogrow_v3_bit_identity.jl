using Random

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

function _system11_trajectory()
    t_grid = collect(range(0.0, 1.0; length = 20))
    u0 = 3.4
    x = reshape([1.0 / sqrt(2.0 * t + 1.0 / u0^2) for t in t_grid], :, 1)
    return Trajectory(t_grid, x)
end

function _run(strategy)
    traj = _system11_trajectory()
    basis = default_staged_polynomial_basis(1)
    options = DiscoveryOptions(
        rng_seed = 42,
        verbose = 0,
        max_levels = 4,
        min_levels = 2,
        loss_tol = 1e-12,
        plateau_window = 2,
        plateau_tol = 1e-4,
    )
    result = discover(
        traj;
        structure = strategy,
        optimizer = BFGSOptimizer(
            maxiters = 3,
            abstol = 1e-6,
            reltol = 1e-6,
            maxiters_solve = 10_000,
            time_limit_s = 20.0,
            reject_nonfinite = false,
            divergence_limit = Inf,
        ),
        basis = basis,
        loss = MSELoss(),
        options = options,
    )
    meta = result.meta.structure
    return (
        loss = result.loss,
        search_loss = result.meta.search.loss,
        objective = result.objective,
        final_stage = meta.final_stage,
        eq_final_stages = haskey(meta, :eq_final_stages) ? meta.eq_final_stages : [meta.final_stage],
        stage_overshoot = max(0, meta.final_stage - 4),
        structure = result.structure.active_idxs,
    )
end

common_kwargs = (
    pop_size = 6,
    n_levels = 4,
    children_per_parent = 2,
    max_terms_per_eq = 4,
    progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 2),
    usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = 0.75),
    use_pretuning = false,
)

v2 = _run(EvoGrow(; common_kwargs...))
v3 = _run(EvoGrowV3(; common_kwargs...))

println("v2=", v2)
println("v3=", v3)

if v2.loss != v3.loss ||
   v2.search_loss != v3.search_loss ||
   v2.objective != v3.objective ||
   v2.final_stage != v3.final_stage ||
   v2.stage_overshoot != v3.stage_overshoot ||
   v2.structure != v3.structure ||
   v3.eq_final_stages != [v2.final_stage]
    error("EvoGrowV3 lockstep smoke differs from EvoGrow stage-local path")
end
