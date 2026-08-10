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
    DiscoveryOptions(; rng_seed=42, verbose=1, ...)

Generic options for `discover`.

Stopping criteria are algorithm-agnostic and apply to *all*
structure search strategies (EvoGrow, GP, ...).
"""
Base.@kwdef struct DiscoveryOptions
    # reproducibility / logging
    rng_seed::Int = 42
    verbose::Int = 1

    # --- stopping: safety ---
    min_levels::Int = 2          # never stop before this many generations
    max_levels::Int = 50         # hard cap (used by GP as well)

    # --- stopping: loss ---
    loss_tol::Float64 = 1e-8     # absolute loss threshold

    # --- stopping: plateau detection ---
    plateau_window::Int = 3      # n generations
    plateau_tol::Float64 = 1e-4  # absolute ΔJ threshold
    plateau_relative::Bool = false
    plateau_rtol::Float64 = 1e-3
end


"""
    DiscoveryResult

Return object of `discover`.

- `structure`: discovered structure object
- `params`: fitted parameter vector
- `loss`: validated loss computed on final simulation output
- `objective`: objective value reported by the structure search; it may use
  search-specific penalties and is not necessarily recomputed from `loss`
- `meta`: metadata (structure search, build, optimization, prediction diagnostics)
"""
struct DiscoveryResult
    structure::Any
    params::Vector{Float64}
    loss::Float64
    objective::Float64
    meta::NamedTuple
end
