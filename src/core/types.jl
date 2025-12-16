"""
    Trajectory(t, x)

Time series data for an ODE system.

- `t :: Vector{Float64}`: time stamps (length T)
- `x :: Matrix{Float64}`: observed states (T × dim)
"""
struct Trajectory
    t::Vector{Float64}
    x::Matrix{Float64}
end

"""
    DiscoveryOptions(; rng_seed=42, verbose=1)

Generic options for `discover`.
- `rng_seed`: RNG seed for reproducibility
- `verbose`: 0=silent, 1=level logs, 2=more details, 3=population snapshots
"""
Base.@kwdef struct DiscoveryOptions
    rng_seed::Int = 42
    verbose::Int = 1
end

"""
    DiscoveryResult

Return object of `discover`.

- `structure`: discovered structure object
- `params`: fitted parameter vector
- `loss`: validated loss computed on final simulation output
- `objective`: objective value (Phase 1: equals `loss`)
- `meta`: metadata (structure search, build, optimization, prediction diagnostics)
"""
struct DiscoveryResult
    structure::Any
    params::Vector{Float64}
    loss::Float64
    objective::Float64
    meta::NamedTuple
end
