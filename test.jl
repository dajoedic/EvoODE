import Pkg
Pkg.activate(@__DIR__)
Pkg.instantiate()
Pkg.precompile()

using EvoODE

# -----------------------
# Create synthetic dataset
# -----------------------
T = 200
t0, t1 = 0.0, 10.0
t = collect(range(t0, t1; length=T))

# Harmonic oscillator:
# u1' = u2
# u2' = -u1
u1 = @. cos(t)
u2 = @. -sin(t)

# X is (T × dim)
X = hcat(u1, u2)

# -----------------------
# Run discovery
# -----------------------


# structure = GPStructureSearch(pop_size = 10, n_generations = 3, tournament_k = 2, p_crossover = 0.7, p_mutation = 0.4, max_terms_per_eq = 5, λ = 1e-3)
structure = EvoGrow(pop_size=10, n_levels=8, children_per_parent=2, max_terms_per_eq=5, λ=1e-3)

basis = PolynomialBasis() # dim=0 placeholder
# basis = default_staged_polynomial_basis(size(X, 2))


res = discover(
    t, X;
    structure = structure,
    optimizer = BFGSOptimizer(maxiters = 200),
    basis = basis,   # dim=0 -> will be replaced automatically
    loss = MSELoss(),
    options = DiscoveryOptions(verbose = 2)
)

# -----------------------
# Print summary
# -----------------------
println()
println("=== GOLDEN TEST RESULT ===")
println("Final validated loss: ", res.loss)

if haskey(res.meta, :structure) && haskey(res.meta.structure, :best_structure_pretty)
    println("Discovered structure:")
    println(res.meta.structure.best_structure_pretty)
end

# -----------------------
# Build RHS for plotting
# -----------------------
dim = size(X, 2)
basis_used = default_polynomial_basis(dim)
f!, _, _ = build_rhs(res.structure, basis_used)

# -----------------------
# Plot + CSV export
# -----------------------
solve_and_save_plot(
    f!, res.params, Trajectory(t, X);
    filename = "fit.png",
    title = "EvoODE Golden Test",
    csv_filename = "fit.csv"
)

# -----------------------
# Minimal correctness check
# -----------------------
@assert isfinite(res.loss)
@assert res.loss < 1e-2

println("Done. Wrote fit.png and fit.csv")