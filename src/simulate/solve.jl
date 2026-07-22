using DifferentialEquations
using SciMLBase
using Logging

"""
    simulate(f!, params, traj; abstol=1e-6, reltol=1e-6, maxiters=10^6, param_clamp=Inf, options=DiscoveryOptions())

Simulates the ODE RHS `f!` with `params` on the time grid of `traj`.
Returns Ŷ with shape (T × dim). On failure returns NaNs.

Important:
- `param_clamp` clamps parameters using `Base.clamp` (does NOT shadow the function).
- `reject_nonfinite` and `divergence_limit` are deterministic early-rejection
  controls; defaults preserve previous behavior.
"""
function simulate(f!::Function,
                  params::Vector{Float64},
                  traj::Trajectory;
                  abstol::Float64 = 1e-6,
                  reltol::Float64 = 1e-6,
                  maxiters::Int = 10^6,
                  clamp_val::Union{Nothing,Float64} = nothing,
                  reject_nonfinite::Bool = false,
                  divergence_limit::Float64 = Inf,
                  options::DiscoveryOptions = DiscoveryOptions())
    t = traj.t
    X = traj.x
    u0 = collect(X[1, :])
    tspan = (t[1], t[end])

    p_use = clamp_val === nothing ? params : clamp.(params, -clamp_val, clamp_val)
    prob = ODEProblem(f!, u0, tspan, p_use)

    local sol
    try
        sol = with_logger(SimpleLogger(stderr, Logging.Error)) do
            out_of_domain = reject_nonfinite ?
                ((u, _, _) -> any(!isfinite, u) || any(abs.(u) .> divergence_limit)) :
                ((_, _, _) -> false)
            solve(prob, Tsit5(); saveat=t, abstol=abstol, reltol=reltol, maxiters=maxiters, isoutofdomain=out_of_domain, verbose=false)
        end
    catch
        return fill(NaN, size(X))
    end

    if sol.retcode != SciMLBase.ReturnCode.Success || length(sol.t) != length(t)
        return fill(NaN, size(X))
    end
    Yhat = Array(sol)'  # (T x dim)
    if any(!isfinite, Yhat) || (isfinite(divergence_limit) && any(abs.(Yhat) .> divergence_limit))
        return fill(NaN, size(X))
    end
    return Yhat
end
