using Test
using Random

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

function _logistic_traj(; n = 60)
    t = collect(range(0.0, 4.0; length = n))
    r = 0.79
    K = 74.3
    x0 = 7.3
    x = [K / (1.0 + (K / x0 - 1.0) * exp(-r * ti)) for ti in t]
    return Trajectory(t, reshape(x, :, 1))
end

@testset "look-ahead stage cap is data-only" begin
    traj = _logistic_traj()
    basis = default_staged_polynomial_basis(1)
    policy = LookAheadStageCapPolicy()

    caps = estimate_stage_caps(traj, basis; policy = policy)
    withheld_truth_caps = estimate_stage_caps(Trajectory(copy(traj.t), copy(traj.x)), basis; policy = policy)

    @test caps == withheld_truth_caps
    @test length(caps) == 1
    @test all(cap -> cap === nothing || 1 <= cap <= 5, caps)
end

@testset "look-ahead cap limits promotion only" begin
    strategy = EvoGrowV3(
        progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 2)
    )
    options = DiscoveryOptions(
        min_levels = 2,
        max_levels = 20,
        loss_tol = 1e-8,
        plateau_window = 3,
        plateau_tol = 1e-4,
    )

    histories = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]

    uncapped = EvoODE._evogrow_v3_promotion_decisions(
        [1, 1, 1], [4, 4, 4], histories, 5, strategy, options
    )
    @test uncapped == [true, true, true]

    capped = EvoODE._evogrow_v3_promotion_decisions(
        [1, 1, 1], [4, 4, 4], histories, 5, strategy, options;
        stage_caps = Union{Nothing,Int}[1, 2, nothing]
    )
    @test capped == [false, true, true]

    below_current = EvoODE._evogrow_v3_promotion_decisions(
        [3], [4], [[1.0, 1.0, 1.0]], 5, strategy, options;
        stage_caps = Union{Nothing,Int}[2]
    )
    @test below_current == [false]

    low_loss = EvoODE._evogrow_v3_promotion_decisions(
        [1], [4], [[1e-10, 1e-10, 1e-10]], 5, strategy, options;
        stage_caps = Union{Nothing,Int}[3]
    )
    @test low_loss == [false]
end

@testset "capped search smoke path executes" begin
    Random.seed!(42)
    traj = _logistic_traj(n = 30)
    basis = default_staged_polynomial_basis(1)
    strategy = EvoGrowStageCapped(
        pop_size = 2,
        n_levels = 2,
        children_per_parent = 1,
        max_terms_per_eq = 2,
        progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 1),
        use_pretuning = false,
    )
    result = discover(
        traj;
        structure = strategy,
        optimizer = BFGSOptimizer(maxiters = 2, time_limit_s = 5.0, maxiters_solve = 2_000),
        basis = basis,
        loss = MSELoss(),
        options = DiscoveryOptions(rng_seed = 42, max_levels = 2, plateau_window = 1, verbose = 0),
    )

    meta = result.meta.structure
    @test haskey(meta, :stage_caps)
    @test haskey(meta, :stage_cap_policy_active)
    @test meta.stage_cap_policy_active == true
    @test isfinite(result.loss) || isnan(result.loss)
end

@testset "EvoGrowV3 cap disabled is bit-identical" begin
    traj = _logistic_traj(n = 25)
    basis = default_staged_polynomial_basis(1)
    common = (
        pop_size = 2,
        n_levels = 2,
        children_per_parent = 1,
        max_terms_per_eq = 2,
        progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = 1),
        use_pretuning = false,
    )
    optimizer = BFGSOptimizer(maxiters = 2, time_limit_s = 5.0, maxiters_solve = 2_000)
    options = DiscoveryOptions(rng_seed = 123, max_levels = 2, plateau_window = 1, verbose = 0)

    implicit = discover(
        traj;
        structure = EvoGrowV3(; common...),
        optimizer = optimizer,
        basis = basis,
        loss = MSELoss(),
        options = options,
    )
    explicit = discover(
        traj;
        structure = EvoGrowV3(; common..., stage_caps = nothing),
        optimizer = optimizer,
        basis = basis,
        loss = MSELoss(),
        options = options,
    )

    @test implicit.structure.active_idxs == explicit.structure.active_idxs
    @test implicit.params == explicit.params
    @test implicit.loss == explicit.loss
    @test implicit.meta.structure.eq_final_stages == explicit.meta.structure.eq_final_stages
end
