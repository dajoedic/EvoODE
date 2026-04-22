"""
Abstract optimizer interface.
"""
abstract type AbstractOptimizer end

"""
    fit_parameters(optimizer, f!, traj, n_params, loss, options)
-> (params::Vector{Float64}, loss_value::Float64, meta::NamedTuple)

Implementations may accept an optional keyword argument `p0::Union{Vector{Float64}, Nothing}`
as a warm-start parameter vector. If not provided or `nothing`, random initialization is used.
"""
function fit_parameters end
