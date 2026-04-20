# src/optimize/bfgs.jl

using DifferentialEquations
using SciMLBase
using Optimization, OptimizationOptimJL
using Logging
using Random

"""
    BFGSOptimizer(; maxiters=300, abstol=1e-6, reltol=1e-6, maxiters_solve=10^6, clamp_val=10.0)

Parameter optimizer for fixed-structure models.

Uses:
  - DifferentialEquations.jl to simulate the ODE
  - Optimization.jl (with AutoFiniteDiff) for gradients
  - BFGS (and NelderMead as fallback) for optimization
"""
Base.@kwdef struct BFGSOptimizer <: AbstractOptimizer
    maxiters::Int = 300
    abstol::Float64 = 1e-6
    reltol::Float64 = 1e-6
    maxiters_solve::Int = 10^6
    clamp_val::Float64 = 10.0
end

function _predict_traj(f!,
                       traj::Trajectory,
                       p::Vector{Float64},
                       opt::BFGSOptimizer)

    t = traj.t
    X = traj.x
    u0 = collect(X[1, :])
    tspan = (t[1], t[end])

    # Clamp parameters for numerical stability
    p_clamped = Base.clamp.(p, -opt.clamp_val, opt.clamp_val)

    prob = ODEProblem(f!, u0, tspan, p_clamped)

    local sol
    try
        sol = with_logger(SimpleLogger(stderr, Logging.Error)) do
            solve(prob, Tsit5();
                  saveat   = t,
                  abstol   = opt.abstol,
                  reltol   = opt.reltol,
                  maxiters = opt.maxiters_solve,
                  verbose  = false)
        end
    catch
        return fill(NaN, size(X))
    end

    if sol.retcode != SciMLBase.ReturnCode.Success || length(sol.t) != length(t)
        return fill(NaN, size(X))
    end

    return Array(sol)'  # (T × dim)
end

function fit_parameters(opt::BFGSOptimizer,
                        f!::Function,
                        traj::Trajectory,
                        n_params::Int,
                        loss::AbstractLoss,
                        options::DiscoveryOptions)

    X = traj.x
    p0 = 0.1 .* randn(n_params)

    function loss_only(p)
        Ŷ = _predict_traj(f!, traj, p, opt)
        return evaluate_loss(loss, Ŷ, X)
    end

    loss_fun = OptimizationFunction((p, _) -> loss_only(p), Optimization.AutoFiniteDiff())
    optprob = OptimizationProblem(loss_fun, p0)

    p_best = copy(p0)
    l_best = 1e6
    method_used = "none"

    try
        res = Optimization.solve(optprob, OptimizationOptimJL.BFGS(); maxiters = opt.maxiters)
        if isfinite(res.minimum)
            p_best = res.u
            l_best = res.minimum
            method_used = "BFGS"
        end
    catch
        # fall through
    end

    if method_used == "none"
        try
            res2 = Optimization.solve(optprob, OptimizationOptimJL.NelderMead(); maxiters = opt.maxiters)
            if isfinite(res2.minimum)
                p_best = res2.u
                l_best = res2.minimum
                method_used = "NelderMead"
            end
        catch
            method_used = "failed"
        end
    end

    # Ensure returned params match the ones actually evaluated in the loss
    p_best = Base.clamp.(p_best, -opt.clamp_val, opt.clamp_val)

    return p_best, l_best, (method = method_used,)
end