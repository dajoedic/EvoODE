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

@testset "look-ahead split decision semantics" begin
    policy = LookAheadStageCapPolicy(tau_abs = 1e-6, lookahead_horizon = 2)

    fell_to_floor = EvoODE._cap_split_decision(
        [10.0, 11.0, 1e-12],
        [true, true, true],
        [1e-10, 1e-10, 1e-10],
        [1, 2, 3],
        policy,
    )
    @test fell_to_floor == (kind = :positive, cap = 3, stage = 3)

    already_at_floor = EvoODE._cap_split_decision(
        [1e-12, 1e-13],
        [true, true],
        [1e-10, 1e-10],
        [1, 2],
        policy,
    )
    @test already_at_floor == (kind = :undecidable, cap = nothing, stage = 1)

    crosses_useless_intermediate = EvoODE._cap_split_decision(
        [10.0, 11.0, 0.1],
        [true, true, true],
        [1e-3, 1e-3, 1e-3],
        [1, 2, 3],
        policy,
    )
    @test crosses_useless_intermediate == (kind = :positive, cap = 3, stage = 3)

    empty_stage_not_counted = EvoODE._cap_split_decision(
        [10.0, Inf, 0.1],
        [true, false, true],
        [1e-3, 1e-3, 1e-3],
        [1, 3],
        LookAheadStageCapPolicy(tau_abs = 1e-6, lookahead_horizon = 1),
    )
    @test empty_stage_not_counted == (kind = :positive, cap = 3, stage = 3)

    successor_not_evaluable = EvoODE._cap_split_decision(
        [10.0, 0.1],
        [true, false],
        [1e-3, 1e-3],
        [1, 2],
        policy,
    )
    @test EvoODE._cap_aggregate_split_decisions([successor_not_evaluable], policy) === nothing

    tau_abs_relaxed_at_floor = EvoODE._cap_rule_counts_gain(
        1e-7,
        1e-12,
        1e-10,
        policy,
    )
    @test tau_abs_relaxed_at_floor == true

    relative_threshold_still_applies = EvoODE._cap_rule_counts_gain(
        1.0001e-10,
        1e-10,
        1e-12,
        LookAheadStageCapPolicy(tau_abs = 1e-12, tau_rel = 1e-2),
    )
    @test relative_threshold_still_applies == false
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
