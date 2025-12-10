# main_evogrow.jl
#
# Demo für EvoGrow:
# - nimmt System 24 (harmonic oscillator ohne Dämpfung)
# - führt EvoGrow-Struktursuche durch
# - zeigt beste Struktur + Parameter

push!(LOAD_PATH, joinpath(@__DIR__, "src"))
using EvoODE

data_path = joinpath(@__DIR__, "data", "strogatz_extended.json")

println("Lade Systeme...")
systems = load_2d_systems(data_path; n = 1)

sys = systems[1]
println("System: id=$(sys.id), dim=$(sys.dim)")
println("Beschreibung: $(sys.eq_description)")
println("Roh-Gleichung: $(sys.eq)")
println()

# Basisbibliothek für dieses System
basis = default_basis_library(sys.dim)

# EvoGrow-Strategie definieren
strategy = EvoGrow(
    20,     # pop_size
    5,      # n_levels (Wachstumsstufen)
    2,      # children_per_parent
    5,      # max_terms_per_eq
    1e-3,   # λ (Komplexitätsstrafe)
)

println("Starte EvoGrow-Struktursuche...")
result = search_structure(strategy, sys.traj, basis; maxiters = 200)

println("\nBeste gefundene Struktur:")
for (k, idxs) in enumerate(result.structure.active_idxs)
    names = [result.basis[j].name for j in idxs]
    println("  du_$k = Σ p * {", join(names, ", "), "}")
end

println("\nBeste Parameter p*: ", result.params)
println("Loss:      ", result.loss)
println("J (Loss + λ * n_params): ", result.objective)

println("\nFertig 🎯")
