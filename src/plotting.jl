using DifferentialEquations
using SciMLBase
using Plots

"""
    solve_and_save_plot(f!, params, traj; filename, title="")

Simulates the ODE defined by `f!` with fitted parameters `params`
on the time grid of `traj` and saves a comparison plot between
observations (scatter points) and model prediction (line).
"""
function solve_and_save_plot(f!,
                             params::Vector{Float64},
                             traj::Trajectory;
                             filename::String,
                             title::String = "")

    t = traj.t
    X = traj.x
    u0 = collect(X[1, :])
    tspan = (t[1], t[end])

    # --- simulate model robustly ---
    local sol
    try
        prob = ODEProblem(f!, u0, tspan, params)
        sol = solve(prob, Tsit5(); saveat = t, abstol=1e-6, reltol=1e-6, maxiters=10^6)
    catch e
        @warn "solve_and_save_plot: ODE solve failed, skipping plot." exception = (e, catch_backtrace())
        return nothing
    end

    if sol.retcode != SciMLBase.ReturnCode.Success || length(sol.t) != length(t)
        @warn "solve_and_save_plot: Solver did not succeed (retcode=$(sol.retcode)), skipping plot."
        return nothing
    end

    Ŷ = Array(sol)'  # (T × dim)

    dim = size(X, 2)
    plt = plot(layout = (dim, 1), legend = :bottomright, size=(900, 300*dim))

    for k in 1:dim
        # data as points
        scatter!(plt[k], t, X[:, k];
                 label = "data u$k",
                 markersize = 3)

        # model as line
        plot!(plt[k], t, Ŷ[:, k];
              label = "model u$k",
              linewidth = 2)

        xlabel!(plt[k], "t")
        ylabel!(plt[k], "u$k")
    end

    if !isempty(title)
        plot!(plt, title = title)
    end

    savefig(plt, filename)
    return filename
end
