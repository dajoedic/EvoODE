using Test
using EvoODE
using SciMLBase
using OptimizationOptimJL

struct RetryLoss <: AbstractLoss end

function retry_rhs!(du, u, p, t)
    du[1] = p[1]
    return nothing
end

function EvoODE.evaluate_loss(::RetryLoss, Yhat, X)
    return Yhat[end, 1]
end

function retry_traj()
    return Trajectory([0.0, 1.0], zeros(2, 1))
end

function retry_options()
    return DiscoveryOptions(verbose = 0)
end

function retry_test_isapprox(actual, expected)
    return isapprox(actual, expected; rtol = 1e-12, atol = 1e-12)
end

function with_retry_solve_hook(f::Function, hook::Function)
    old = EvoODE._BFGS_SOLVE_HOOK[]
    EvoODE._BFGS_SOLVE_HOOK[] = hook
    try
        return f()
    finally
        EvoODE._BFGS_SOLVE_HOOK[] = old
    end
end

function retry_eval_objective(optprob, p)
    return optprob.f(Vector{Float64}(p), nothing)
end

@testset "BFGS retry failure predicate" begin
    @test EvoODE.fit_attempt_failed(Inf, true)
    @test EvoODE.fit_attempt_failed(EvoODE.MSE_SENTINEL_LOSS, true)
    @test EvoODE.fit_attempt_failed(1.0, false)
    @test !EvoODE.fit_attempt_failed(0.5, true)
end

@testset "BFGS retry does not repeat at k=1" begin
    opt = BFGSOptimizer(max_fit_attempts = 1)
    calls = Ref(0)

    local lval
    local meta
    with_retry_solve_hook(
        function ()
            _, lval, meta = fit_parameters(
                opt,
                retry_rhs!,
                retry_traj(),
                1,
                RetryLoss(),
                retry_options();
                p0 = [0.5],
            )
        end,
        function (optprob, algorithm; maxiters, time_limit)
            calls[] += 1
            return (u = [0.5], minimum = EvoODE.MSE_SENTINEL_LOSS, retcode = SciMLBase.ReturnCode.Success)
        end,
    )

    @test calls[] == 1
    @test retry_test_isapprox(lval, EvoODE.MSE_SENTINEL_LOSS)
    @test meta.fit_attempts == 1
    @test meta.accepted_attempt == 1
    @test meta.retry_triggered == false
    @test meta.fit_failed == true
end

@testset "BFGS retry accepts second attempt" begin
    opt = BFGSOptimizer(max_fit_attempts = 3)
    calls = Ref(0)

    local params
    local lval
    local meta
    with_retry_solve_hook(
        function ()
            params, lval, meta = fit_parameters(
                opt,
                retry_rhs!,
                retry_traj(),
                1,
                RetryLoss(),
                retry_options();
                p0 = [0.5],
            )
        end,
        function (optprob, algorithm; maxiters, time_limit)
            calls[] += 1
            if calls[] == 1
                return (u = [0.5], minimum = EvoODE.MSE_SENTINEL_LOSS, retcode = SciMLBase.ReturnCode.Success)
            end
            return (u = [0.25], minimum = 0.25, retcode = SciMLBase.ReturnCode.Success)
        end,
    )

    @test calls[] == 2
    @test retry_test_isapprox(params, [0.25])
    @test retry_test_isapprox(lval, 0.25)
    @test meta.fit_attempts == 2
    @test meta.accepted_attempt == 2
    @test meta.retry_triggered == true
    @test meta.fit_failed == false
end

@testset "BFGS retry exhausts all attempts" begin
    opt = BFGSOptimizer(max_fit_attempts = 3)
    calls = Ref(0)

    local meta
    with_retry_solve_hook(
        function ()
            _, _, meta = fit_parameters(
                opt,
                retry_rhs!,
                retry_traj(),
                1,
                RetryLoss(),
                retry_options();
                p0 = [0.5],
            )
        end,
        function (optprob, algorithm; maxiters, time_limit)
            calls[] += 1
            return (u = [Float64(calls[])], minimum = EvoODE.MSE_SENTINEL_LOSS, retcode = SciMLBase.ReturnCode.Success)
        end,
    )

    @test calls[] == 3
    @test meta.fit_attempts == 3
    @test meta.accepted_attempt == 3
    @test meta.retry_triggered == true
    @test meta.fit_failed == true
end

@testset "BFGS retry sums cost counters" begin
    opt = BFGSOptimizer(max_fit_attempts = 3, clamp_val = 100.0)
    calls = Ref(0)

    local lval
    local meta
    with_retry_solve_hook(
        function ()
            _, lval, meta = fit_parameters(
                opt,
                retry_rhs!,
                retry_traj(),
                1,
                RetryLoss(),
                retry_options();
                p0 = [0.5],
            )
        end,
        function (optprob, algorithm; maxiters, time_limit)
            calls[] += 1
            if calls[] == 1
                retry_eval_objective(optprob, [1.0])
                retry_eval_objective(optprob, [2.0])
                return (u = [2.0], minimum = EvoODE.MSE_SENTINEL_LOSS, retcode = SciMLBase.ReturnCode.Success)
            end
            minimum = retry_eval_objective(optprob, [0.25])
            return (u = [0.25], minimum = minimum, retcode = SciMLBase.ReturnCode.Success)
        end,
    )

    @test retry_test_isapprox(lval, 0.25)
    @test meta.fit_attempts == 2
    @test meta.loss_evals == 3
    @test meta.ode_solves == 3
end

@testset "BFGS retry leaves first success as one attempt" begin
    opt = BFGSOptimizer(max_fit_attempts = 3)
    calls = Ref(0)

    local params
    local lval
    local meta
    with_retry_solve_hook(
        function ()
            params, lval, meta = fit_parameters(
                opt,
                retry_rhs!,
                retry_traj(),
                1,
                RetryLoss(),
                retry_options();
                p0 = [0.5],
            )
        end,
        function (optprob, algorithm; maxiters, time_limit)
            calls[] += 1
            return (u = [0.125], minimum = 0.125, retcode = SciMLBase.ReturnCode.Success)
        end,
    )

    @test calls[] == 1
    @test retry_test_isapprox(params, [0.125])
    @test retry_test_isapprox(lval, 0.125)
    @test meta.method == "BFGS"
    @test meta.retcode == string(SciMLBase.ReturnCode.Success)
    @test meta.fit_attempts == 1
    @test meta.accepted_attempt == 1
    @test meta.retry_triggered == false
    @test meta.fit_failed == false
end
