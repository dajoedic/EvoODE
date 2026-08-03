# scripts/run_odebench.jl
#
# Run EvoODE on ODEBench-style datasets.
# - writes results incrementally to CSV (sep=";", decimal=",")
# - computes both trajectory-fit metrics and derivative metrics (ODEBench-like)
# - optionally saves plots + per-case CSV with t, X, Xhat

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using EvoODE
using Random
using Printf
using Dates
using JSON3

# Local container type for benchmark systems (kept outside the EvoODE package)
struct SystemData
    id::Int
    eq::String
    eq_description::String
    dim::Int
    traj::EvoODE.Trajectory
end


# -----------------------------
# Config
# -----------------------------
data_path = joinpath(@__DIR__, "data", "strogatz_extended.json")
out_root  = joinpath(dirname(@__DIR__), "outputs", "benchmarks", "odebench")
out_path  = joinpath(out_root, "evoode_results.csv")

# Discovery config
structure = EvoGrow(pop_size=20, n_levels=5, children_per_parent=2, max_terms_per_eq=5, λ=1e-3)
optimizer = BFGSOptimizer(maxiters=300)     # adjust as you like
basis     = PolynomialBasis()               # dim will be auto-set in discover if dim=0
loss      = MSELoss()
options   = DiscoveryOptions(rng_seed=42, verbose=2)

# Output options
save_plots = true
save_case_csv = true

# -----------------------------
# Helpers
# -----------------------------
# Convert Float -> decimal comma string
fmt(x::Real; digits=10) = replace(@sprintf("%0.*g", digits, float(x)), "." => ",")

# Safe string field for CSV
function csv_escape(s::AbstractString)
    s2 = replace(s, "\"" => "''")
    return "\"" * s2 * "\""
end

# Central finite differences for dX/dt (shape: T×dim)
# - endpoints: forward/backward diff
function finite_diff(t::AbstractVector{<:Real}, X::AbstractMatrix{<:Real})
    T, dim = size(X)
    dX = zeros(Float64, T, dim)

    @inbounds begin
        # forward
        dt = t[2] - t[1]
        dX[1, :] .= (X[2, :] .- X[1, :]) ./ dt

        # central
        for i in 2:(T-1)
            dt = t[i+1] - t[i-1]
            dX[i, :] .= (X[i+1, :] .- X[i-1, :]) ./ dt
        end

        # backward
        dt = t[T] - t[T-1]
        dX[T, :] .= (X[T, :] .- X[T-1, :]) ./ dt
    end

    return dX
end

# Evaluate RHS f!(du,u,p,t) along a trajectory X(t)
function eval_rhs_along_traj(f!, params::Vector{Float64}, t::Vector{Float64}, X::Matrix{Float64})
    T, dim = size(X)
    FX = zeros(Float64, T, dim)
    du = zeros(Float64, dim)

    @inbounds for i in 1:T
        u = view(X, i, :)
        f!(du, u, params, t[i])
        FX[i, :] .= du
    end
    return FX
end

# RMSE / MAE between same-sized matrices
rmse(A, B) = sqrt(sum((A .- B).^2) / length(A))
mae(A, B)  = sum(abs.(A .- B)) / length(A)
mse(A, B)  = sum((A .- B).^2) / length(A)

# ODEBench-like derivative metrics:
# compare inferred RHS vs numerical derivative from data.
function derivative_metrics(f!, params, traj::Trajectory; drop_edges::Int=1)
    t = traj.t
    X = traj.x
    dX = finite_diff(t, X)
    FX = eval_rhs_along_traj(f!, params, t, X)

    # often people drop edges for fairness (finite-diff artifacts)
    if drop_edges > 0 && size(X, 1) > 2drop_edges
        r = (1+drop_edges):(size(X,1)-drop_edges)
        dX = dX[r, :]
        FX = FX[r, :]
    end

    return (rmse = rmse(FX, dX), mae = mae(FX, dX), mse = mse(FX, dX))
end

# Minimal loader for "strogatz_extended-like" JSON
# Expect: obj["solutions"][1][1]["t"], obj["solutions"][1][1]["y"] where y is list of dim arrays
function load_systems_json(path::String; nmax::Int=typemax(Int), ic_set::Int=1)
    raw = open(path, "r") do io
        JSON3.read(io)
    end

    systems = SystemData[]
    for obj in raw
        dim = Int(obj["dim"])
        sols = obj["solutions"]
        first_set = sols[1]
        sol = first_set[ic_set]

        t = Vector{Float64}(sol["t"])
        y = sol["y"]
        ys = [Vector{Float64}(yi) for yi in y]
        X = reduce(hcat, ys)  # (T×dim)

        traj = Trajectory(t, X)

        push!(systems, SystemData(
            Int(obj["id"]),
            String(obj["eq"]),
            String(obj["eq_description"]),
            dim,
            traj,
        ))

        length(systems) >= nmax && break
    end
    return systems
end

# -----------------------------
# Run
# -----------------------------
if abspath(PROGRAM_FILE) == @__FILE__
mkpath(dirname(out_path))
println("Loading ODEBench-like systems from: ", data_path)
systems = load_systems_json(data_path)
println("Loaded ", length(systems), " systems.")

# CSV header (write once)
if !isfile(out_path)
    open(out_path, "w") do io
        println(io, join([
            "timestamp",
            "sys_id",
            "dim",
            "eq",
            "eq_description",
            "fit_loss",         # discovery-reported loss
            "traj_mse",         # MSE(Xhat,X)
            "deriv_rmse",       # RMSE(f(x), dX/dt)
            "deriv_mae",
            "deriv_mse",
            "n_params",
            "structure_pretty",
            "plot_file",
            "case_csv"
        ], ";"))
    end
end

for sys in systems
    println("\n=== System ", sys.id, " (dim=", sys.dim, ") ===")
    println("eq:  ", sys.eq)
    println("desc:", sys.eq_description)

    # Run discovery
    res = discover(sys.traj;
        structure = structure,
        optimizer = optimizer,
        basis     = basis,
        loss      = loss,
        options   = options
    )

    # Build final RHS + simulate (use EvoODE internals explicitly)
    f!, n_params, _ = EvoODE.build_rhs(res.structure, (hasproperty(basis, :dim) && getproperty(basis, :dim) == 0) ? EvoODE.default_polynomial_basis(sys.dim) : basis)
    Xhat = EvoODE.simulate(f!, res.params, sys.traj; options=options)

    traj_mse = mse(Xhat, sys.traj.x)
    dmet = derivative_metrics(f!, res.params, sys.traj)

    # Optional outputs per case
    ts = Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")
    plot_file = ""
    case_csv = ""

    if save_plots || save_case_csv
        mkpath(joinpath(out_root, "sys_$(sys.id)"))
        base = joinpath(out_root, "sys_$(sys.id)", "fit_sys$(sys.id)")
        if save_plots
            plot_file = base * ".png"
        end
        if save_case_csv
            case_csv = base * ".csv"
        end

        # NOTE: use your package plotting function signature:
        # solve_and_save_plot(f!, params, traj; filename=..., csv_filename=..., title=...)
        title = "EvoODE fit | sys=$(sys.id) | dim=$(sys.dim)"
        EvoODE.solve_and_save_plot(
            f!, res.params, sys.traj;
            filename = plot_file,
            title = title,
            csv_filename = case_csv
        )
    end

    # Structure pretty string (if available)
    pretty = ""
    if haskey(res.meta, :structure) && haskey(res.meta.structure, :best_structure_pretty)
        pretty = replace(String(res.meta.structure.best_structure_pretty), '\n' => ' ')
    end

    # Append one row immediately (batch-safe)
    open(out_path, "a") do io
        fields = String[
            csv_escape(ts),
            string(sys.id),
            string(sys.dim),
            csv_escape(sys.eq),
            csv_escape(sys.eq_description),
            fmt(res.loss),
            fmt(traj_mse),
            fmt(dmet.rmse),
            fmt(dmet.mae),
            fmt(dmet.mse),
            string(length(res.params)),
            csv_escape(pretty),
            csv_escape(plot_file),
            csv_escape(case_csv)
        ]
        println(io, join(fields, ";"))
    end

    println("Wrote row -> ", out_path)
end

println("\nDone. Results at: ", out_path)
end
