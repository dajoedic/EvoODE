using Test
using LinearAlgebra

include(joinpath(@__DIR__, "..", "studies", "lookahead", "derivative_estimator_probe.jl"))

function sine_traj(n)
    t = collect(range(0.0, 1.0; length = n))
    x = reshape(sin.(t), n, 1)
    return Trajectory(t, x)
end

function rms_derivative_error(estimator, n)
    traj = sine_traj(n)
    dX = estimate_with(estimator, traj)
    truth = cos.(traj.t)
    return sqrt(mean(abs2, dX[:, 1] .- truth))
end

@testset "derivative estimator refinement" begin
    for estimator in ("central", "fd4", "local_poly")
        coarse = rms_derivative_error(estimator, 41)
        fine = rms_derivative_error(estimator, 81)
        @test fine < coarse
    end
    @test rms_derivative_error("fd4", 81) < rms_derivative_error("central", 81)
end

@testset "richardson tracks true error" begin
    traj = sine_traj(101)
    dX = estimate_with("central", traj)
    truth = cos.(traj.t)
    true_error = abs.(dX[:, 1] .- truth)
    rich = richardson_error_estimate("central", traj)[:, 1]
    @test corr_safe(true_error, rich) > 0.5
    @test sqrt(mean(abs2, rich)) / sqrt(mean(abs2, true_error)) > 0.1
end

@testset "constant weights reduce to unweighted" begin
    t = collect(range(0.0, 1.0; length = 30))
    x = reshape(collect(range(-1.0, 1.0; length = 30)), 30, 1)
    Phi = hcat(ones(30), x[:, 1], x[:, 1] .^ 2)
    y = 1.0 .+ 2.0 .* x[:, 1] .- 0.5 .* x[:, 1] .^ 2
    fit = collect(1:20)
    hold = collect(21:30)
    unweighted = ls_fit_eval(Phi, y, fit, hold)
    weighted = weighted_ls_fit_eval(Phi, y, fit, hold, ones(30))
    @test isapprox(unweighted.coeffs, weighted.coeffs; rtol = 1e-12, atol = 1e-12)
    @test isapprox(unweighted.holdout_residual, weighted.holdout_residual; atol = 1e-24)
end

@testset "split validity rejects degeneracy" begin
    Phi = hcat(ones(20), ones(20) .+ 1e-14 .* collect(1:20))
    y = ones(20)
    valid, reason, cond_value, excitation = split_validity(Phi, y, collect(1:20))
    @test !valid
    @test occursin("condition", reason) || occursin("low_excitation", reason)
    @test cond_value > 1e10 || excitation < 1e-10
end
