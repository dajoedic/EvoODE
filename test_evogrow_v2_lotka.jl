import Pkg
Pkg.activate(@__DIR__)

using EvoODE
using DifferentialEquations

# -----------------------
# Create synthetic dataset: Lotka–Volterra
# -----------------------

# Parameters
α = 1.5
β = 1.0
δ = 1.0
γ = 3.0

function lotka!(du, u, p, t)
    x, y = u
    du[1] = α * x - β * x * y
    du[2] = δ * x * y - γ * y
end

u0 = [1.2, 1.1]
t0, t1 = 0.0, 10.0
T = 200
t = collect(range(t0, t1; length=T))

prob = ODEProblem(lotka!, u0, (t0, t1))
sol = solve(prob, Tsit5(); saveat=t, abstol=1e-10, reltol=1e-10)

X = Array(sol)'   # (T × dim)

# -----------------------
# Define structure search
# -----------------------
structure = EvoGrow(
    pop_size = 10,
    n_levels = 8,
    children_per_parent = 2,
    max_terms_per_eq = 5,
    λ = 1e-3
)

# -----------------------
# Basis / optimizer / loss
# -----------------------
dim = size(X, 2)
basis = default_staged_polynomial_basis(dim)

optimizer = BFGSOptimizer(
    maxiters = 60,
    abstol = 1e-8,
    reltol = 1e-8,
    maxiters_solve = 100000,
    clamp_val = 10.0
)

loss = MSELoss()

options = DiscoveryOptions(
    verbose = 3,
    min_levels = 2,
    max_levels = 8,
    loss_tol = 1e-6,
    plateau_window = 2,
    plateau_tol = 1e-4,
    plateau_relative = false,
    plateau_rtol = 1e-3
)

# -----------------------
# Run discovery
# -----------------------
res = discover(
    t, X;
    structure = structure,
    optimizer = optimizer,
    basis = basis,
    loss = loss,
    options = options
)

# -----------------------
# Print summary
# -----------------------
println()
println("=== LOTKA–VOLTERRA TEST RESULT ===")
println("Final validated loss: ", res.loss)

if haskey(res.meta, :structure) && haskey(res.meta.structure, :best_structure_pretty)
    println("Discovered structure:")
    println(res.meta.structure.best_structure_pretty)
end

if haskey(res.meta, :search) && haskey(res.meta.search, :objective)
    println("Search objective: ", res.meta.search.objective)
end

if haskey(res.meta, :sanity) && haskey(res.meta.sanity, :delta)
    println("Sanity delta: ", res.meta.sanity.delta)
end

# -----------------------
# Build RHS for plotting
# -----------------------
f!, _, _ = build_rhs(res.structure, basis)

# -----------------------
# Plot + CSV export
# -----------------------
solve_and_save_plot(
    f!, res.params, Trajectory(t, X);
    filename = "fit_lotka_v2.png",
    title = "EvoGrow v2 on Lotka–Volterra",
    csv_filename = "fit_lotka_v2.csv"
)

println("Done. Wrote fit_lotka_v2.png and fit_lotka_v2.csv")