# src/data.jl

using JSON3

"""
Zeitreihe eines Systems.
t :: Vector{Float64}   – Zeitpunkte (Länge T)
x :: Matrix{Float64}   – Werte (T × dim)
"""
struct Trajectory
    t::Vector{Float64}
    x::Matrix{Float64}
end

"""
Metadaten + eine Beispiel-Trajektorie.
"""
struct SystemData
    id::Int
    eq::String
    eq_description::String
    dim::Int
    traj::Trajectory
end

# gesamtes JSON laden
function _load_all(path::String)
    open(path, "r") do io
        JSON3.read(io)
    end
end

# erste Trajektorie aus einem System-Objekt
function _first_trajectory(obj)
    sols = obj["solutions"]
    first_set = sols[1]
    sol = first_set[1]

    t = Vector{Float64}(sol["t"])
    y = sol["y"]  # Liste von Zustands-Zeitreihen

    ys = [Vector{Float64}(yi) for yi in y]

    # Matrix: Zeilen = Zeit, Spalten = Dimension -> (T × dim)
    x_mat = reduce(hcat, ys)

    return Trajectory(t, x_mat)
end

"""
    load_2d_systems(path; n=5)

Lädt die ersten `n` Systeme mit dim == 2.
"""
function load_2d_systems(path::String; n::Int = 5)
    raw = _load_all(path)  # JSON3.Array
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
