# src/data.jl

using JSON3

# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------

"""
Trajectory of a dynamical system.

Fields:
- `t::Vector{Float64}`: time points (length T)
- `x::Matrix{Float64}`: states of size (T × dim)
"""
struct Trajectory
    t::Vector{Float64}
    x::Matrix{Float64}
end

"""
Metadata and one sample trajectory of a system.

Fields:
- `id::Int`: system identifier
- `eq::String`: symbolic equation (human-readable)
- `eq_description::String`: textual description
- `dim::Int`: state dimension
- `traj::Trajectory`: one simulated trajectory
"""
struct SystemData
    id::Int
    eq::String
    eq_description::String
    dim::Int
    traj::Trajectory
end


# ----------------------------------------------------------------------
# Internal helper functions for JSON loading
# ----------------------------------------------------------------------

# Load full JSON file (returns JSON3.Array or JSON3.Object)
function _load_all(path::String)
    open(path, "r") do io
        JSON3.read(io)
    end
end

# Extract first available trajectory from a JSON system object
function _first_trajectory(obj)
    sols = obj["solutions"]
    first_set = sols[1]
    sol = first_set[1]

    t = Vector{Float64}(sol["t"])
    y = sol["y"]  # list of per-state time series

    # convert each dimension into Float64 vector
    ys = [Vector{Float64}(yi) for yi in y]

    # assemble matrix: (T × dim)
    x_mat = reduce(hcat, ys)

    return Trajectory(t, x_mat)
end


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

"""
    load_2d_systems(path; n=5)

Load up to `n` systems with state dimension `dim == 2`.
Returns a vector of `SystemData` entries.
"""
function load_2d_systems(path::String; n::Int = 5)
    raw = _load_all(path)
    systems = SystemData[]

    for obj in raw
        dim = Int(obj["dim"])
        dim != 2 && continue

        traj = _first_trajectory(obj)

        push!(systems, SystemData(
            Int(obj["id"]),
            String(obj["eq"]),
            String(obj["eq_description"]),
            dim,
            traj,
        ))

        length(systems) >= n && break
    end

    return systems
end
