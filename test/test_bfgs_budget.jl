using Test
using EvoODE

const LAST_BFGS_TEST_P = Ref(Float64[])

mutable struct RecordingQuadraticLoss <: AbstractLoss
    target::Float64
    records::Vector{NamedTuple{(:params, :loss), Tuple{Vector{Float64}, Float64}}}
end

struct ConstantLoss <: AbstractLoss
    value::Float64
end

function tracking_constant_rhs!(du, u, p, t)
    LAST_BFGS_TEST_P[] = copy(Vector{Float64}(p))
    du[1] = p[1]
    return nothing
end

function EvoODE.evaluate_loss(loss::RecordingQuadraticLoss, Yhat, X)
    p = copy(LAST_BFGS_TEST_P[])
    value = (p[1] - loss.target)^2
    push!(loss.records, (params = p, loss = value))
    return value
end

function EvoODE.evaluate_loss(loss::ConstantLoss, Yhat, X)
    return loss.value
end

function one_dim_traj()
    return Trajectory([0.0, 1.0], zeros(2, 1))
end

function quiet_options()
    return DiscoveryOptions(verbose = 0)
end

@testset "BFGS budget returns best observed evaluation" begin
    loss = RecordingQuadraticLoss(2.0, NamedTuple{(:params, :loss), Tuple{Vector{Float64}, Float64}}[])
    opt = BFGSOptimizer(
        maxiters = 100,
        max_loss_evals = 4,
        clamp_val = 100.0,
        abstol = 1e-9,
        reltol = 1e-9,
    )

    params, lval, meta = fit_parameters(
        opt,
        tracking_constant_rhs!,
        one_dim_traj(),
        1,
        loss,
        quiet_options();
        p0 = [0.5],
    )

    finite_records = filter(r -> isfinite(r.loss), loss.records)
    expected = finite_records[argmin([r.loss for r in finite_records])]

    @test meta.stop_reason == "loss_eval_budget"
    @test meta.retcode == "MaxLossEvals"
    @test meta.method == "BFGS"
    @test meta.result_valid == true
    @test meta.result_source == "best_observed"
    @test meta.loss_evals == opt.max_loss_evals
    @test length(loss.records) == opt.max_loss_evals
    @test lval == expected.loss
    @test params == expected.params
end

@testset "BFGS distinguishes no valid loss from sentinel loss" begin
    opt = BFGSOptimizer(maxiters = 100, max_loss_evals = 1, clamp_val = 100.0)

    _, no_valid_loss, no_valid_meta = fit_parameters(
        opt,
        tracking_constant_rhs!,
        one_dim_traj(),
        1,
        ConstantLoss(NaN),
        quiet_options();
        p0 = [0.5],
    )

    _, sentinel_loss, sentinel_meta = fit_parameters(
        opt,
        tracking_constant_rhs!,
        one_dim_traj(),
        1,
        ConstantLoss(1e6),
        quiet_options();
        p0 = [0.5],
    )

    @test no_valid_meta.result_valid == false
    @test no_valid_meta.best_loss_seen == false
    @test no_valid_loss == Inf

    @test sentinel_meta.result_valid == true
    @test sentinel_meta.best_loss_seen == true
    @test sentinel_loss == 1e6
    @test sentinel_meta.best_observed_loss == 1e6
end
