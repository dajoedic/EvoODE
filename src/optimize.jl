# src/optimize.jl

using DifferentialEquations
using SciMLBase
using Optimization, OptimizationOptimJL
using Logging
using Statistics: mean  # aktuell nur indirekt über mse_loss relevant

"""
    fit_parameters(f!, traj::Trajectory, n_params; maxiters=300)

Fits `n_params` parameters `p` for a given ODE model `f!` on the
time series in `traj`.

Uses:
  - DifferentialEquations.jl to simulate the ODE
  - Optimization.jl (with AutoFiniteDiff) for gradients
  - BFGS (and NelderMead as a fallback) for optimization
"""
function fit_parameters(
    f!::Function,
    traj::Trajectory,
    n_params::Int;
    maxiters::Int = 300,
)
    t = traj.t
    X = traj.x

    # Initial condition and time span from data
    u0    = collect(X[1, :])
    tspan = (t[1], t[end])

    # Initial parameter guess
    p0 = 0.1 .* randn(n_params)

    prob = ODEProblem(f!, u0, tspan, p0)

    # --- Prediction: solve ODE for given parameters with error handling ---
    function predict(p)
        # Clamp parameters to avoid completely exploding values
        p_clamped = clamp.(p, -10.0, 10.0)

        local sol
        try
            prob_p = remake(prob; p = p_clamped)

            # Suppress most ODE warnings (e.g. maxiters, small dt)
            sol = with_logger(SimpleLogger(stderr, Logging.Error)) do
                solve(
                    prob_p,
                    Tsit5();
                    saveat   = t,
                    maxiters = 10^6,
                    abstol   = 1e-6,
                    reltol   = 1e-6,
                    verbose  = false,
                )
            end
        catch e
            # Solver completely failed → return NaNs to trigger large loss
            @debug "Simulation failed for candidate" exception = (e, catch_backtrace())
            return fill(NaN, size(X))
        end

        # If solver did not succeed or length doesn't match → also NaNs
        if sol.retcode != SciMLBase.ReturnCode.Success || length(sol.t) != length(t)
            return fill(NaN, size(X))
        end

        # Convert to (T × dim) array
        return Array(sol)'
    end

    # --- Loss based on prediction and mse_loss ---
    function loss(p)
        Y = predict(p)

        # Quick sanity checks before passing into mse_loss
        if any(!isfinite, Y) || size(Y) != size(X)
            return 1e6
        end

        l = mse_loss(Y, X)
        return isfinite(l) ? l : 1e6
    end

    # Optimization problem with numerical gradients
    loss_fun = OptimizationFunction(
        (p, _) -> loss(p),
        Optimization.AutoFiniteDiff(),
    )
    optprob = OptimizationProblem(loss_fun, p0)

    # Default: keep initial guess if everything fails
    p_best = p0
    l_best = 1e6

    try
        # First try: BFGS (gradient-based)
        res = Optimization.solve(
            optprob,
            OptimizationOptimJL.BFGS();
            maxiters = maxiters,
        )

        if isfinite(res.minimum)
            p_best = res.u
            l_best = res.minimum
        end
    catch e
        @warn "Parameteroptimierung mit BFGS fehlgeschlagen, verwende Fallback." e

        # Fallback: Nelder-Mead (gradient-free)
        try
            res_nm = Optimization.solve(
                optprob,
                OptimizationOptimJL.NelderMead();
                maxiters = maxiters,
            )
            if isfinite(res_nm.minimum)
                p_best = res_nm.u
                l_best = res_nm.minimum
            end
        catch e2
            @warn "Fallback (NelderMead) ebenfalls fehlgeschlagen, behalte Startparameter." e2
        end
    end

    return (p = p_best, loss = l_best)
end

"""
    fit_parameters(f!, traj; maxiters=300)

Convenience wrapper:
assumes `n_params = 4` (e.g. for the current linear 2D model).
"""
function fit_parameters(f!, traj::Trajectory; maxiters::Int = 300)
    return fit_parameters(f!, traj, 4; maxiters = maxiters)
end
