# src/optimize.jl

using DifferentialEquations
using SciMLBase
using Optimization, OptimizationOptimJL
using Logging
using Statistics: mean

"""
    fit_parameters(f!, traj::Trajectory, n_params; maxiters=300)

Fit von `n_params` Parametern p für ein gegebenes Modell `f!`
auf die Trajektorie `traj`.

Nutzt:
- DifferentialEquations.jl zum Lösen
- Optimization.jl mit AutoFiniteDiff für Gradienten
- BFGS als Optimierer
"""

function fit_parameters(f!::Function, traj::Trajectory, n_params::Int; maxiters::Int = 300)
    t = traj.t
    X = traj.x
    dim = size(X, 2)

    u0    = collect(X[1, :])
    tspan = (t[1], t[end])

    # Startwerte für die Parameter
    p0 = 0.1 .* randn(n_params)

    prob = ODEProblem(f!, u0, tspan, p0)

    # --- Vorhersagefunktion: ODE-Solve mit Fehler-Handling ---
    function predict(p)
        # Parameter clampen, um völlig wahnsinnige Werte zu vermeiden
        p_clamped = clamp.(p, -10.0, 10.0)

        local sol
        try
            prob_p = remake(prob; p = p_clamped)
            sol = with_logger(SimpleLogger(stderr, Logging.Error)) do
				solve(
					prob_p,
					Tsit5();
					saveat   = t,
					maxiters = 10^6,
					abstol   = 1e-6,
					reltol   = 1e-6,
					verbose  = false
				)
			end
        catch	
            # Solver völlig eskaliert → NaNs zurückgeben
			@debug "Simulation failed for candidate" exception = (e, catch_backtrace())
            return fill(NaN, size(X))
        end

        # Wenn Solver nicht erfolgreich oder falsche Länge → auch NaNs
        if sol.retcode != SciMLBase.ReturnCode.Success || length(sol.t) != length(t)
            return fill(NaN, size(X))
        end

        # Trajektorie als (T × dim)-Array zurückgeben
        # (das hat vorher ja schon funktioniert – also nicht dran rütteln)
        return Array(sol)'
    end

    # --- Loss-Funktion auf Basis von predict + mse_loss ---
    function loss(p)
        Y = predict(p)

        # mse_loss kümmert sich schon um NaNs / falsche Größe, aber doppelt hält besser
        if any(!isfinite, Y) || size(Y) != size(X)
            return 1e6
        end

        l = mse_loss(Y, X)
        return isfinite(l) ? l : 1e6
    end

    # --- Optimization-Problem mit AutoFiniteDiff (numerische Gradienten) ---
    loss_fun = OptimizationFunction((p, _) -> loss(p),
                                    Optimization.AutoFiniteDiff())
    optprob  = OptimizationProblem(loss_fun, p0)

    # Default-Fallback
    p_best = p0
    l_best = 1e6

    try
        # BFGS behalten – jetzt mit robuster loss-Funktion
        res = Optimization.solve(optprob, OptimizationOptimJL.BFGS();
                                 maxiters = maxiters)

        if isfinite(res.minimum)
            p_best = res.u
            l_best = res.minimum
        end
    catch e
        @warn "Parameteroptimierung mit BFGS fehlgeschlagen, verwende Fallback." e

        # Optional: als Fallback z.B. Nelder-Mead ohne Gradient
        try
            res_nm = Optimization.solve(optprob, OptimizationOptimJL.NelderMead();
                                        maxiters = maxiters)
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

Kompatibilitäts-Wrapper:
nutzt automatisch `n_params = 4` (z.B. für dein aktuelles lineares 2D-Modell).
"""
function fit_parameters(f!, traj::Trajectory; maxiters::Int = 300)
    return fit_parameters(f!, traj, 4; maxiters = maxiters)
end
