# src/optimize.jl

using DifferentialEquations
using SciMLBase
using Optimization, OptimizationOptimJL
using Zygote
using SciMLSensitivity

"""
    fit_parameters(f!, traj::Trajectory; maxiters=300)

Fit von Parametern p für ein gegebenes 2D-Modell `f!`
auf die Trajektorie `traj`.
"""
function fit_parameters(f!, traj::Trajectory; maxiters::Int = 300)
    t = traj.t                 # Vector{Float64}, Länge T
    X = traj.x                 # Matrix (T × dim), hier dim = 2

    @assert size(X, 1) == length(t) "X muss Größe (T × dim) haben, T = length(t)"

    dim = size(X, 2)

    # Anfangszustand: erster Zeitschritt als Vector
    u0 = collect(X[1, :])      # Vector{Float64} der Länge dim

    tspan = (t[1], t[end])

    # 4 Parameter für unser lineares Modell, klein starten
    p0 = 0.1 .* randn(4)

    prob = ODEProblem(f!, u0, tspan, p0)

    # Vorhersage: gib Matrix (T × dim) zurück
    function predict(p)
        # Parameter begrenzen, damit der Solver nicht komplett explodiert
        p_clamped = clamp.(p, -10.0, 10.0)

        _prob = remake(prob; p = p_clamped)

        sol = solve(
            _prob,
            Tsit5();
            saveat = t,
            abstol = 1e-8,
            reltol = 1e-6,
            maxiters = 10^6,
        )

        # Wenn der Solver nicht sauber durchläuft:
        if sol.retcode != SciMLBase.ReturnCode.Success || length(sol.t) != length(t)
            # Matrix voller NaN in korrekter Größe zurückgeben
            return fill(NaN, size(X))
        end

        Y = Array(sol)          # (dim × T)
        return permutedims(Y)   # (T × dim)
    end

    function loss(p)
        pred = predict(p)

        # Wenn Solver gescheitert / NaNs erzeugt hat → hoher Penalty-Loss
        if any(!isfinite, pred)
            return 1e6
        end

        mse_loss(pred, X)
    end

    loss_fun = OptimizationFunction((p, _) -> loss(p), Optimization.AutoZygote())
    optprob  = OptimizationProblem(loss_fun, p0)

    res = Optimization.solve(optprob, OptimizationOptimJL.BFGS(); maxiters = maxiters)

    return (p = res.u, loss = res.minimum)
end
