"""
Abstract optimizer interface.
"""
abstract type AbstractOptimizer end

"""
    fit_parameters(optimizer, f!, traj, n_params, loss, options)
-> (params::Vector{Float64}, loss_value::Float64, meta::NamedTuple)
"""
function fit_parameters end
