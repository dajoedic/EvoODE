############################################################
# main_mvp.jl
#
# MVP-Pipeline:
#  - lädt die ersten 5 2D-Systeme aus data/strogatz_extended.json
#  - fitten ein einfaches lineares 2D-ODE-Modell auf jedes System
#  - gibt gefittete Parameter und Loss aus
#
# WICHTIG:
#  - Das Projekt wird in der REPL aktiviert, NICHT hier im Skript:
#      using Pkg
#      Pkg.activate(".")
#      include("main_mvp.jl")
############################################################

# Eigenes Package (im Ordner src/) in den LOAD_PATH hängen,
# damit `using EvoODE` funktioniert.
push!(LOAD_PATH, joinpath(@__DIR__, "src"))

# Hauptmodul laden – exportiert u.a.:
#   Trajectory, SystemData, load_2d_systems, make_model, fit_parameters
using EvoODE

# Pfad zur JSON-Datei mit den Strogatz-Systemen
data_path = joinpath(@__DIR__, "data", "strogatz_extended.json")

println("Lade Systeme...")

# Lade die ersten 5 Systeme mit dim == 2
systems = load_2d_systems(data_path; n = 5)

println("Geladene Systeme (id, dim, Beschreibung):")
for s in systems
    println("  id=$(s.id), dim=$(s.dim) – ", s.eq_description)
end

println()
println("Starte Parameter-Fits...")
println()

# Iteriere über alle geladenen Systeme und fitte jeweils das lineare Modell
for (i, sys) in enumerate(systems)
    println("----------------------------------------------------")
    println("System $(i): id=$(sys.id)")
    println("Beschreibung: ", sys.eq_description)
    println("Roh-Gleichung: ", sys.eq)

    traj = sys.traj
    println("  Trajektorie: length(t) = $(length(traj.t)), size(x) = $(size(traj.x))")

    # Einfaches lineares 2D-Modell:
    #   du1 = p1*u1 + p2*u2
    #   du2 = p3*u1 + p4*u2
    f! = make_model()

    # Parameter-Fit für dieses System
    result = fit_parameters(f!, traj; maxiters = 300)

    println("  Gefittete Parameter p*: ", result.p)
    println("  Finaler Loss:          ", result.loss)
end

println()
println("Fertig 🚀")
