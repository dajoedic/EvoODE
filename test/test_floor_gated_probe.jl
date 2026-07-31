using Test

include(joinpath(@__DIR__, "..", "studies", "lookahead", "floor_gated_probe.jl"))

@testset "floor-gated firing rule" begin
    @test !rule_counts_gain("floor_gated", 1.0e-5, 5.0e-6, 1.0e-4, 1e-4, 1e-8)
    @test !rule_counts_gain("floor_gated", 1.0e-2, 5.0e-3, 1.0e-2, 1e-4, 1e-8)
    @test rule_counts_gain("floor_gated", 1.0e-1, 5.0e-2, 1.0e-4, 1e-4, 1e-8)
    @test rule_counts_gain("threshold_only", 1.0e-5, 5.0e-6, 1.0e-4, 1e-4, 1e-8)
end

@testset "rank deficiency detection" begin
    collinear = hcat(ones(20), 2.0 .* ones(20))
    deficient, reason, r, c = is_rank_deficient(collinear)
    @test deficient
    @test r < size(collinear, 2)
    @test occursin("rank", reason)

    well = hcat(ones(20), collect(range(-1.0, 1.0; length = 20)))
    deficient2, reason2, r2, c2 = is_rank_deficient(well)
    @test !deficient2
    @test reason2 == ""
    @test r2 == 2
    @test isfinite(c2)
end

@testset "ridge tends to unregularized fit" begin
    x = collect(range(-1.0, 1.0; length = 40))
    Phi = hcat(ones(40), x, x .^ 2)
    y = 1.0 .+ 0.5 .* x .- 2.0 .* x .^ 2
    fit = collect(1:25)
    hold = collect(26:40)
    ols = weighted_ls_fit_eval(Phi, y, fit, hold, ones(40))
    ridge = ridge_fit_eval(Phi, y, fit, hold, ones(40); alpha = 1e-14)
    @test isapprox(ols.coeffs, ridge.coeffs; rtol = 1e-8, atol = 1e-8)
    @test isapprox(ols.holdout_residual, ridge.holdout_residual; atol = 1e-18)
end

@testset "density sweep benchmark density" begin
    sys54 = only([s for s in PROBE_SYSTEMS if s.id == 54])
    traj = trajectory_at_multiplier(sys54, 1)
    @test length(traj.t) == sys54.T
end
