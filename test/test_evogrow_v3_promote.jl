using Test

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

struct ConstantTestBasis <: EvoODE.AbstractBasis end
EvoODE.basis_num_terms(::ConstantTestBasis) = 1
EvoODE.basis_term_name(::ConstantTestBasis, ::Int) = "one"
EvoODE.basis_term_func(::ConstantTestBasis, ::Int) = (u, t) -> 1.0

@testset "EvoGrowV3 equation-local promotion decisions" begin
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

    promote = EvoODE._evogrow_v3_promotion_decisions(
        [1, 1],
        [4, 4],
        [[1.0, 1.0 + 1e-6, 1.0 + 2e-6], [1.0, 1.1, 1.0]],
        5,
        strategy,
        options
    )
    @test promote == [true, false]

    promote_low_residual = EvoODE._evogrow_v3_promotion_decisions(
        [1, 1],
        [4, 4],
        [[1e-10, 1e-10, 1e-10], [1.0, 1.0, 1.0]],
        5,
        strategy,
        options
    )
    @test promote_low_residual == [false, true]

    promote_low_budget = EvoODE._evogrow_v3_promotion_decisions(
        [1, 1],
        [2, 2],
        [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]],
        5,
        strategy,
        options
    )
    @test promote_low_budget == [false, false]

    promote_max_stage = EvoODE._evogrow_v3_promotion_decisions(
        [5, 1],
        [4, 4],
        [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]],
        5,
        strategy,
        options
    )
    @test promote_max_stage == [false, true]
end

@testset "EvoGrowV3 equation residual signal" begin
    t = collect(range(0.0, 1.0; length = 11))
    x = hcat(1.0 .+ 2.0 .* t, 1.0 .+ 3.0 .* t)
    traj = Trajectory(t, x)
    basis = ConstantTestBasis()
    structure = StructureSpec([[1], Int[]])
    params = [2.0]
    options = DiscoveryOptions(verbose = 0)

    residuals, fallback = EvoODE._evogrow_v3_equation_residuals(
        structure,
        params,
        basis,
        traj,
        options
    )

    @test fallback == false
    @test residuals[1] ≈ 0.0 atol = 1e-12
    @test residuals[2] > 1.0
end
