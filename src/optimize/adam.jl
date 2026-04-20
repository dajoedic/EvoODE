# src/optimize/adam.jl
# Stub — not yet implemented. Use BFGSOptimizer for all current experiments.

"""
    AdamOptimizer(; lr=1e-3, maxiters=1000)

Adam-based parameter optimizer (not yet implemented).

Planned as a differentiable alternative to BFGS for smooth loss landscapes.
Use `BFGSOptimizer` for all current experiments.
"""
Base.@kwdef struct AdamOptimizer <: AbstractOptimizer
    lr::Float64 = 1e-3
    maxiters::Int = 1000
end

"""
    fit_parameters(::AdamOptimizer, f!, traj, n_params, loss, options)

Not yet implemented.
"""
function fit_parameters(::AdamOptimizer,
                        f!::Function,
                        traj::Trajectory,
                        n_params::Int,
                        loss::AbstractLoss,
                        options::DiscoveryOptions)
    error("AdamOptimizer is not yet implemented. Use BFGSOptimizer instead.")
end
