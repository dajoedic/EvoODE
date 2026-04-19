import Pkg
Pkg.activate(".")
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
res = discover(
    t, X;
    structure = GPStructureSearch(pop_size=60, n_generations=10, p_mutation=0.4),
    optimizer = BFGSOptimizer(maxiters=200),
    basis = PolynomialBasis(),   # dim=0 -> will be replaced automatically
    loss = MSELoss(),
    options = DiscoveryOptions(verbose=3)
)

# -----------------------
# Plot + CSV export
# -----------------------
dim = size(X, 2)
basis_used = default_polynomial_basis(dim)
f!, _, _ = build_rhs(res.structure, basis_used)

solve_and_save_plot(
    f!, res.params, Trajectory(t, X);
    filename = "fit.png",
    title = "EvoODE fit",
    csv_filename = "fit.csv"
)

println("Done. Wrote fit.png and fit.csv")
