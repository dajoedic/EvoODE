using Test

include(joinpath(@__DIR__, "..", "studies", "lookahead", "stage_potential_probe.jl"))

function synthetic_traj_1d(; n = 90)
    t = collect(range(0.0, 1.0; length = n))
    x = reshape(collect(range(0.2, 1.7; length = n)), n, 1)
    return Trajectory(t, x)
end

function row_for(rows, stage, split)
    return only([r for r in rows if r["row_type"] == "stage_capacity" &&
                 r["tested_stage"] == stage && r["split"] == split])
end

@testset "stage potential split construction" begin
    splits = make_splits(100)

    @test splits["A"].fit == collect(1:70)
    @test splits["A"].holdout == collect(71:100)
    @test splits["B"].fit == collect(31:100)
    @test splits["B"].holdout == collect(1:30)
    @test splits["C"].fit == vcat(collect(1:35), collect(66:100))
    @test splits["C"].holdout == collect(36:65)

    for split in values(splits)
        @test isempty(intersect(split.fit, split.holdout))
        @test sort(vcat(split.fit, split.holdout)) == collect(1:100)
    end
end

@testset "stage potential empty stages and normalisation" begin
    traj = synthetic_traj_1d()
    basis = default_staged_polynomial_basis(1)
    dX = traj.x .^ 3
    rows, _, _ = stage_rows_for_equation(
        PROBE_SYSTEMS[3],
        basis,
        traj,
        dX,
        1,
        4,
    )

    @test row_for(rows, 3, "A")["empty_stage"] == true
    @test row_for(rows, 3, "A")["new_terms"] == 0
    @test normalised_mse([1.0, -1.0], [0.0, 2.0]) == 1.0
    @test isinf(normalised_mse([1.0, 1.0], [2.0, 2.0]))
end

@testset "stage potential synthetic stage gains" begin
    traj = synthetic_traj_1d(n = 120)
    basis = default_staged_polynomial_basis(1)

    cubic_dX = traj.x .^ 3
    cubic_rows, cubic_metrics, cubic_new_counts = stage_rows_for_equation(
        PROBE_SYSTEMS[3],
        basis,
        traj,
        cubic_dX,
        1,
        4,
    )
    @test row_for(cubic_rows, 3, "A")["absolute_gain"] > 1e-8
    @test row_for(cubic_rows, 4, "A")["holdout_residual"] < 1e-20
    @test max_useful_stage(cubic_metrics, cubic_new_counts, "A", 1e-4, 1e-10) == 4

    linear_dX = 2.0 .* traj.x
    linear_rows, linear_metrics, linear_new_counts = stage_rows_for_equation(
        PROBE_SYSTEMS[1],
        basis,
        traj,
        linear_dX,
        1,
        1,
    )
    @test row_for(linear_rows, 1, "A")["holdout_residual"] < 1e-20
    @test row_for(linear_rows, 1, "A")["absolute_gain"] <= 1e-20
    @test max_useful_stage(linear_metrics, linear_new_counts, "A", 1e-4, 1e-10) == 1
end
