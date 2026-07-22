import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf
using Random

include(joinpath(@__DIR__, "..", "..", "src", "EvoODE.jl"))
using .EvoODE
include(joinpath(@__DIR__, "..", "regression", "diagnostic_systems.jl"))

const SCRIPT_SLUG = "solver_tolerance_noise_floor"
const OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "numerics", SCRIPT_SLUG)
const SYSTEM_IDS = (3, 11)
const TOLERANCES = (1e-5, 1e-6, 1e-8, 1e-10, 1e-12)
const SEED = 42

const BASELINE_V0 = Dict(
    3 => (loss = 2.663641831768419e-10, final_stage = 3),
    11 => (loss = 4.402192340718147e-15, final_stage = 4),
)

function build_options(seed::Int)
    return DiscoveryOptions(
        rng_seed = seed,
        verbose = 0,
        min_levels = 2,
        max_levels = 50,
        loss_tol = 1e-8,
        plateau_window = 3,
        plateau_tol = 1e-4,
        plateau_relative = false,
        plateau_rtol = 1e-3,
    )
end

function build_optimizer(tol::Float64)
    return BFGSOptimizer(
        maxiters = 200,
        abstol = tol,
        reltol = tol,
        maxiters_solve = 10^6,
        clamp_val = 10.0,
        time_limit_s = 86_400.0,
        reject_nonfinite = false,
        divergence_limit = Inf,
    )
end

function system_by_id(system_id::Int)
    return only([system for system in REGRESSION_SYSTEMS if Int(system[:system_id]) == system_id])
end

function build_trajectory(system)
    tspan = system[:tspan]
    t_grid = collect(range(tspan[1], tspan[2]; length = Int(system[:T])))
    u0 = Float64[x for x in system[:u0]]
    prob = ODEProblem(rhs_for_system(Int(system[:system_id])), copy(u0), tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    return Trajectory(t_grid, Array(sol)')
end

function true_coefficients(system_id::Int)
    if system_id == 3
        # rhs_03!: 0.79*u1*(1 - u1/74.3) = 0.79*u1 - (0.79/74.3)*u1^2
        return Dict("u1" => 0.79, "u1^2" => -0.79 / 74.3)
    elseif system_id == 11
        # rhs_11!: -u1^3
        return Dict("u1^3" => -1.0)
    end
    error("Unsupported system_id=$(system_id)")
end

function known_structure_and_params(system_id::Int, basis::AbstractBasis)
    active_idxs = expected_active_idxs(system_id, basis)
    coeffs = true_coefficients(system_id)
    params = Float64[]
    for eq_idxs in active_idxs
        for term_idx in eq_idxs
            term_name = basis_term_name(basis, term_idx)
            push!(params, coeffs[term_name])
        end
    end
    return StructureSpec(active_idxs), params
end

function perturbed_params(params::Vector{Float64})
    return [p * (1.0 + (isodd(i) ? 0.01 : -0.01)) for (i, p) in enumerate(params)]
end

function default_start_params(n_params::Int, system_id::Int, tol_index::Int)
    Random.seed!(SEED + 10_000 * system_id + tol_index)
    return 0.1 .* randn(n_params)
end

function loss_at_params(f!, params::Vector{Float64}, traj::Trajectory, tol::Float64)
    opt = build_optimizer(tol)
    yhat = simulate(
        f!,
        params,
        traj;
        abstol = opt.abstol,
        reltol = opt.reltol,
        maxiters = opt.maxiters_solve,
        clamp_val = opt.clamp_val,
        reject_nonfinite = opt.reject_nonfinite,
        divergence_limit = opt.divergence_limit,
        options = build_options(SEED),
    )
    return evaluate_loss(MSELoss(), yhat, traj.x)
end

function run_floor_cell(system_id::Int, tol::Float64, tol_index::Int)
    system = system_by_id(system_id)
    traj = build_trajectory(system)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    structure, true_params = known_structure_and_params(system_id, basis)
    f!, _, _ = build_rhs(structure, basis)

    local loss_value
    elapsed_s = @elapsed begin
        yhat = simulate(
            f!,
            true_params,
            traj;
            abstol = tol,
            reltol = tol,
            maxiters = 10^6,
            clamp_val = 10.0,
            reject_nonfinite = false,
            divergence_limit = Inf,
            options = build_options(SEED),
        )
        loss_value = evaluate_loss(MSELoss(), yhat, traj.x)
    end

    baseline = BASELINE_V0[system_id]
    return Dict{String, Any}(
        "part" => "A_floor",
        "system_id" => system_id,
        "system_name" => String(system[:system_name]),
        "tol" => tol,
        "true_params" => true_params,
        "floor_loss_true_params" => loss_value,
        "elapsed_s" => elapsed_s,
        "baseline_v0_loss" => baseline.loss,
        "baseline_v0_loss_below_floor" => baseline.loss < loss_value,
        "baseline_v0_loss_to_floor_ratio" => loss_value == 0.0 ? Inf : baseline.loss / loss_value,
    )
end

function start_params_for(start_kind::String,
                          system_id::Int,
                          tol_index::Int,
                          n_params::Int,
                          structure::StructureSpec,
                          basis::AbstractBasis,
                          traj::Trajectory,
                          true_params::Vector{Float64})
    if start_kind == "default"
        return default_start_params(n_params, system_id, tol_index)
    elseif start_kind == "pretune"
        return EvoODE.pretune_parameters(structure, basis, traj)
    elseif start_kind == "true_perturbed_1pct"
        return perturbed_params(true_params)
    end
    error("Unsupported start kind $(start_kind)")
end

function run_fit_cell(system_id::Int, tol::Float64, tol_index::Int, start_kind::String)
    system = system_by_id(system_id)
    traj = build_trajectory(system)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    structure, true_params = known_structure_and_params(system_id, basis)
    f!, n_params, _ = build_rhs(structure, basis)
    p0 = start_params_for(start_kind, system_id, tol_index, n_params, structure, basis, traj, true_params)
    start_loss = loss_at_params(f!, p0, traj, tol)

    local params
    local final_loss
    local meta
    elapsed_s = @elapsed begin
        params, final_loss, meta =
            fit_parameters(build_optimizer(tol), f!, traj, n_params, MSELoss(), build_options(SEED); p0 = p0)
    end

    ode_solves = Int(meta.ode_solves)
    fit_time_s = Float64(meta.fit_time_s)
    solve_time_s = Float64(meta.solve_time_s)
    ms_per_solve = ode_solves == 0 ? nothing : 1000.0 * solve_time_s / ode_solves
    fits_per_level = 20.0

    return Dict{String, Any}(
        "part" => "B_fit",
        "system_id" => system_id,
        "system_name" => String(system[:system_name]),
        "tol" => tol,
        "start_kind" => start_kind,
        "true_params" => true_params,
        "start_params" => p0,
        "final_params" => params,
        "start_loss" => start_loss,
        "final_loss" => final_loss,
        "loss_improvement" => start_loss - final_loss,
        "loss_improvement_factor" => final_loss == 0.0 ? Inf : start_loss / final_loss,
        "retcode" => String(meta.retcode),
        "method" => String(meta.method),
        "loss_evals" => Int(meta.loss_evals),
        "invalid_evals" => Int(meta.invalid_evals),
        "ode_solves" => ode_solves,
        "invalid_solves" => Int(meta.invalid_solves),
        "optimizer_failure_hits" => Int(meta.optimizer_failure_hits),
        "optimizer_iteration_limit_hits" => Int(meta.optimizer_iteration_limit_hits),
        "optimizer_retcodes" => collect(meta.optimizer_retcodes),
        "elapsed_s" => elapsed_s,
        "fit_time_s" => fit_time_s,
        "solve_time_s" => solve_time_s,
        "ms_per_ode_solve" => ms_per_solve,
        "projected_level_time_s_at_20_fits" => fit_time_s * fits_per_level,
        "projected_level_ode_solves_at_20_fits" => ode_solves * fits_per_level,
    )
end

function csv_value(value)
    value === nothing && return ""
    text = string(value)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::String, records, columns)
    open(path, "w") do io
        println(io, join(columns, ","))
        for record in records
            println(io, join([csv_value(get(record, column, nothing)) for column in columns], ","))
        end
    end
end

function write_json(path::String, value)
    open(path, "w") do io
        JSON3.pretty(io, value)
        write(io, '\n')
    end
end

function print_floor(record)
    @printf(
        "FLOOR system=%d tol=%.0e floor_loss=%.16e baseline=%.16e baseline_below_floor=%s ratio=%.6g elapsed=%.3fs\n",
        record["system_id"],
        record["tol"],
        record["floor_loss_true_params"],
        record["baseline_v0_loss"],
        string(record["baseline_v0_loss_below_floor"]),
        record["baseline_v0_loss_to_floor_ratio"],
        record["elapsed_s"],
    )
end

function print_fit(record)
    @printf(
        "FIT system=%d tol=%.0e start=%s start_loss=%.16e final_loss=%.16e improvement=%.3e factor=%.6g retcode=%s evals=%d solves=%d fit_time=%.3fs ms_per_solve=%s projected_level_time=%.3fs\n",
        record["system_id"],
        record["tol"],
        record["start_kind"],
        record["start_loss"],
        record["final_loss"],
        record["loss_improvement"],
        record["loss_improvement_factor"],
        record["retcode"],
        record["loss_evals"],
        record["ode_solves"],
        record["fit_time_s"],
        string(record["ms_per_ode_solve"]),
        record["projected_level_time_s_at_20_fits"],
    )
end

function main()
    mkpath(OUTPUT_DIR)
    floor_records = Dict{String, Any}[]
    fit_records = Dict{String, Any}[]
    start_kinds = ("default", "pretune", "true_perturbed_1pct")

    println("Writing outputs to $(OUTPUT_DIR)")
    for system_id in SYSTEM_IDS
        for (tol_index, tol) in enumerate(TOLERANCES)
            floor_record = run_floor_cell(system_id, tol, tol_index)
            push!(floor_records, floor_record)
            print_floor(floor_record)
            for start_kind in start_kinds
                fit_record = run_fit_cell(system_id, tol, tol_index, start_kind)
                push!(fit_records, fit_record)
                print_fit(fit_record)
            end
        end
    end

    floor_columns = [
        "system_id", "system_name", "tol", "floor_loss_true_params", "elapsed_s",
        "baseline_v0_loss", "baseline_v0_loss_below_floor", "baseline_v0_loss_to_floor_ratio",
        "true_params",
    ]
    fit_columns = [
        "system_id", "system_name", "tol", "start_kind", "start_loss", "final_loss",
        "loss_improvement", "loss_improvement_factor", "retcode", "method", "loss_evals",
        "invalid_evals", "ode_solves", "invalid_solves", "optimizer_failure_hits",
        "optimizer_iteration_limit_hits", "optimizer_retcodes", "elapsed_s", "fit_time_s",
        "solve_time_s", "ms_per_ode_solve", "projected_level_time_s_at_20_fits",
        "projected_level_ode_solves_at_20_fits", "start_params", "final_params", "true_params",
    ]

    summary = Dict{String, Any}(
        "script" => SCRIPT_SLUG,
        "timestamp" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "systems" => collect(SYSTEM_IDS),
        "tolerances" => collect(TOLERANCES),
        "seed" => SEED,
        "trajectory_solver" => Dict("algorithm" => "Tsit5", "abstol" => 1e-9, "reltol" => 1e-9),
        "optimizer_maxiters" => 200,
        "floor_records" => floor_records,
        "fit_records" => fit_records,
        "notes" => [
            "Only systems 3 and 11 are run.",
            "Known correct structures come from expected_active_idxs.",
            "True parameters are derived from diagnostic_systems.jl RHS definitions.",
            "Projected level cost assumes 20 fixed-structure parameter fits per level.",
            "No records are written to studies/regression/history.jsonl.",
        ],
    )

    write_json(joinpath(OUTPUT_DIR, "summary.json"), summary)
    write_json(joinpath(OUTPUT_DIR, "floor_records.json"), floor_records)
    write_json(joinpath(OUTPUT_DIR, "fit_records.json"), fit_records)
    write_csv(joinpath(OUTPUT_DIR, "floor_records.csv"), floor_records, floor_columns)
    write_csv(joinpath(OUTPUT_DIR, "fit_records.csv"), fit_records, fit_columns)
    println("Wrote summary.json, floor_records.*, fit_records.*")
end

main()
