using Test
using EvoODE
using SciMLBase
using OptimizationOptimJL

const LAST_D2B_TEST_P = Ref(Float64[])

struct ControlledLossException <: Exception
    call::Int
end

mutable struct ControlledLoss <: AbstractLoss
    target::Float64
    throw_on_calls::Set{Int}
    calls::Int
    records::Vector{NamedTuple{(:call, :params, :loss), Tuple{Int, Vector{Float64}, Float64}}}
end

function d2b_tracking_rhs!(du, u, p, t)
    LAST_D2B_TEST_P[] = copy(Vector{Float64}(p))
    du[1] = p[1]
    return nothing
end

function EvoODE.evaluate_loss(loss::ControlledLoss, Yhat, X)
    loss.calls += 1
    if loss.calls in loss.throw_on_calls
        throw(ControlledLossException(loss.calls))
    end

    p = copy(LAST_D2B_TEST_P[])
    value = (p[1] - loss.target)^2
    push!(loss.records, (call = loss.calls, params = p, loss = value))
    return value
end

function d2b_traj()
    return Trajectory([0.0, 1.0], zeros(2, 1))
end

function d2b_options()
    return DiscoveryOptions(verbose = 0)
end

function with_solve_hook(f::Function, hook::Function)
    old = EvoODE._BFGS_SOLVE_HOOK[]
    EvoODE._BFGS_SOLVE_HOOK[] = hook
    try
        return f()
    finally
        EvoODE._BFGS_SOLVE_HOOK[] = old
    end
end

function eval_objective(optprob, p)
    return optprob.f(Vector{Float64}(p), nothing)
end

function fallback_result_count(meta)
    return meta.method == "NelderMead" && meta.result_source == "optimizer_return" ? 1 : 0
end

function last_resort_count(meta)
    return meta.result_source == "last_resort_best_observed" ? 1 : 0
end

@testset "BFGS failure falls back before best observed" begin
    loss = ControlledLoss(
        1.25,
        Set([2]),
        0,
        NamedTuple{(:call, :params, :loss), Tuple{Int, Vector{Float64}, Float64}}[],
    )
    opt = BFGSOptimizer(
        maxiters = 2,
        max_loss_evals = 20,
        clamp_val = 100.0,
        abstol = 1e-9,
        reltol = 1e-9,
    )

    local meta
    with_solve_hook(
        function ()
            _, _, meta = fit_parameters(
                opt,
                d2b_tracking_rhs!,
                d2b_traj(),
                1,
                loss,
                d2b_options();
                p0 = [0.5],
            )
        end,
        function (optprob, algorithm; maxiters, time_limit)
            if algorithm isa OptimizationOptimJL.BFGS
                eval_objective(optprob, [0.5])
                eval_objective(optprob, [0.6])
                error("unreachable")
            else
                minimum = eval_objective(optprob, [1.25])
                return (u = [1.25], minimum = minimum, retcode = SciMLBase.ReturnCode.Success)
            end
        end,
    )

    @test meta.method == "NelderMead"
    @test meta.result_valid == true
    @test meta.result_source == "optimizer_return"
    @test meta.result_source != "last_resort_best_observed"
    @test fallback_result_count(meta) == 1
    @test last_resort_count(meta) == 0
    @test meta.loss_evals == loss.calls
    @test meta.loss_evals == 3
    @test meta.loss_evals < opt.max_loss_evals
end

@testset "Best observed is accepted only as last resort" begin
    loss = ControlledLoss(
        1.25,
        Set([2, 3]),
        0,
        NamedTuple{(:call, :params, :loss), Tuple{Int, Vector{Float64}, Float64}}[],
    )
    opt = BFGSOptimizer(
        maxiters = 2,
        max_loss_evals = 20,
        clamp_val = 100.0,
        abstol = 1e-9,
        reltol = 1e-9,
    )

    local params
    local lval
    local meta
    with_solve_hook(
        function ()
            params, lval, meta = fit_parameters(
                opt,
                d2b_tracking_rhs!,
                d2b_traj(),
                1,
                loss,
                d2b_options();
                p0 = [0.5],
            )
        end,
        function (optprob, algorithm; maxiters, time_limit)
            if algorithm isa OptimizationOptimJL.BFGS
                eval_objective(optprob, [0.5])
                eval_objective(optprob, [0.6])
                error("unreachable")
            else
                eval_objective(optprob, [0.7])
                error("unreachable")
            end
        end,
    )

    expected = only(loss.records)

    @test meta.method == "NelderMead"
    @test meta.retcode == "Exception"
    @test meta.stop_reason == "exception"
    @test meta.result_valid == true
    @test meta.result_source == "last_resort_best_observed"
    @test fallback_result_count(meta) == 0
    @test last_resort_count(meta) == 1
    @test meta.loss_evals == 3
    @test lval == expected.loss
    @test params == expected.params
end
