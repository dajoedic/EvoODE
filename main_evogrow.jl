# main_evogrow.jl
#
# Demo script for evaluating the EvoGrow structural search algorithm.
# Steps:
#   1. Load a 2D benchmark system (Strogatz extended dataset)
#   2. Construct a basis library
#   3. Run EvoGrow across several growth levels
#   4. Print the best discovered structure and parameter vector

# Make the local package available
push!(LOAD_PATH, joinpath(@__DIR__, "src"))
using EvoODE

# ---------------------------------------
# 1) Load system data
# ---------------------------------------

data_path = joinpath(@__DIR__, "data", "strogatz_extended.json")

println("Loading systems...")
systems = load_2d_systems(data_path; n = 5)

sys = systems[3]

println("System: id=$(sys.id), dim=$(sys.dim)")
println("Description: $(sys.eq_description)")
println("Raw equation: $(sys.eq)")
println()

# ---------------------------------------
# 2) Build basis library
# ---------------------------------------

basis = default_basis_library(sys.dim)

# ---------------------------------------
# 3) Configure EvoGrow strategy
# ---------------------------------------

strategy = EvoGrow(
    20,     # pop_size: number of individuals in the population
    5,      # n_levels: number of structural growth levels
    2,      # children_per_parent: structural expansions per parent
    5,      # max_terms_per_eq: max active basis terms per equation
    1e-3,   # λ: complexity penalty (objective = loss + λ * num_params)
)

# ---------------------------------------
# 4) Run the structural search
# ---------------------------------------

println("Starting EvoGrow structure search...")
result = search_structure(strategy, sys.traj, basis; maxiters = 200)

# ---------------------------------------
# 5) Pretty-print the resulting model
# ---------------------------------------

println("\nBest discovered structure:")
for (k, idxs) in enumerate(result.structure.active_idxs)
    names = [result.basis[j].name for j in idxs]
    println("  du_$k = Σ p * {", join(names, ", "), "}")
end

println("\nBest parameter vector p* = ", result.params)
println("Loss:      ", result.loss)
println("Objective: ", result.objective)

println("\nDone 🎯")
