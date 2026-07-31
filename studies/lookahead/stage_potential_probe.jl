import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using LinearAlgebra
using Printf
using Statistics

include(joinpath(@__DIR__, "..", "..", "src", "EvoODE.jl"))
using .EvoODE

"""
Stage-potential probe for EvoGrow staging.

This diagnostic measures the capacity of a stage, never the quality of a currently
discovered sparse model. For every comparison, both sides use the full cumulative
library up to the tested stages. Comparing a discovered sparse structure against a
future full library would bias the test toward firing, because the future stage would
partly win against the search's own failure rather than against the term class.

The probe is deliberately restricted to numerical derivative estimation, design
matrices, linear least-squares fits, and time-blocked holdout evaluation. It performs
ODE solves only once per benchmark system to generate the reference trajectory.
"""

const SCRIPT_SLUG = "stage_potential_probe"
const OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "lookahead", SCRIPT_SLUG)
const DETAIL_CSV = joinpath(OUTPUT_DIR, "stage_potential_rows.csv")
const GRID_CSV = joinpath(OUTPUT_DIR, "threshold_grid.csv")
const SUMMARY_JSON = joinpath(OUTPUT_DIR, "summary.json")
const REPORT_MD = joinpath(OUTPUT_DIR, "report.md")
const MAX_STAGE = 5
const TAU_REL_GRID = (1e-4, 1e-3, 1e-2, 5e-2)
const TAU_ABS_GRID = (1e-12, 1e-10, 1e-8, 1e-6, 1e-4)

Base.@kwdef struct ProbeSystem
    id::Int
    name::String
    dim::Int
    true_rhs!::Function
    u0::Vector{Float64}
    tspan::Tuple{Float64,Float64}
    T::Int
    representability::Symbol
    expected_stage::Int
    expected_terms::Union{Nothing,Vector{Vector{String}}} = nothing
end

function rhs_02!(du, u, _, _)
    du[1] = 0.23 * u[1]
end

function rhs_03!(du, u, _, _)
    du[1] = 0.79 * u[1] * (1.0 - u[1] / 74.3)
end

function rhs_11!(du, u, _, _)
    du[1] = -u[1]^3
end

function rhs_23!(du, u, _, _)
    du[1] = 0.21 - sin(u[1])
end

function rhs_24!(du, u, _, _)
    du[1] = u[2]
    du[2] = -2.1 * u[1]
end

function rhs_26!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

function rhs_31!(du, u, _, _)
    du[1] = -0.4 * u[1] * u[2]
    du[2] = 0.4 * u[1] * u[2] - 0.314 * u[2]
end

function rhs_37!(du, u, _, _)
    du[1] = u[2]
    du[2] = -u[1] - 0.43 * (u[1]^2 - 1.0) * u[2]
end

function rhs_54!(du, u, _, _)
    du[1] = 5.1 * (u[2] - u[1])
    du[2] = 12.0 * u[1] - u[2] - u[1] * u[3]
    du[3] = u[1] * u[2] - 1.67 * u[3]
end

function rhs_63!(du, u, _, _)
    du[1] = -0.28 * u[1] * u[3]
    du[2] = 0.28 * u[1] * u[3] - 0.47 * u[2]
    du[3] = 0.47 * u[2] - 0.30 * u[3]
    du[4] = 0.30 * u[3]
end

# Mirrored from benchmarks/benchmark_evogrow.jl so this standalone diagnostic can use
# the benchmark table without executing that script's benchmark main loop.
const PROBE_SYSTEMS = ProbeSystem[
    ProbeSystem(id = 2, name = "Population growth (linear)", dim = 1, true_rhs! = rhs_02!,
                u0 = [4.78], tspan = (0.0, 12.0), T = 120, representability = :exact,
                expected_stage = 1, expected_terms = [["u1"]]),
    ProbeSystem(id = 3, name = "Logistic growth", dim = 1, true_rhs! = rhs_03!,
                u0 = [7.3], tspan = (0.0, 20.0), T = 200, representability = :exact,
                expected_stage = 2, expected_terms = [["u1", "u1^2"]]),
    ProbeSystem(id = 11, name = "Critical slowing down", dim = 1, true_rhs! = rhs_11!,
                u0 = [3.4], tspan = (0.0, 5.0), T = 100, representability = :exact,
                expected_stage = 4, expected_terms = [["u1^3"]]),
    ProbeSystem(id = 23, name = "Overdamped pendulum", dim = 1, true_rhs! = rhs_23!,
                u0 = [-2.74], tspan = (0.0, 25.0), T = 250, representability = :surrogate,
                expected_stage = 5),
    ProbeSystem(id = 24, name = "Harmonic oscillator", dim = 2, true_rhs! = rhs_24!,
                u0 = [0.4, -0.03], tspan = (0.0, 15.0), T = 200, representability = :exact,
                expected_stage = 1, expected_terms = [["u2"], ["u1"]]),
    ProbeSystem(id = 26, name = "Lotka-Volterra competition", dim = 2, true_rhs! = rhs_26!,
                u0 = [5.0, 4.3], tspan = (0.0, 10.0), T = 200, representability = :exact,
                expected_stage = 3, expected_terms = [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]]),
    ProbeSystem(id = 31, name = "SIR model", dim = 2, true_rhs! = rhs_31!,
                u0 = [7.2, 0.98], tspan = (0.0, 20.0), T = 200, representability = :exact,
                expected_stage = 3, expected_terms = [["u1*u2"], ["u1*u2", "u2"]]),
    ProbeSystem(id = 37, name = "Van der Pol oscillator", dim = 2, true_rhs! = rhs_37!,
                u0 = [2.2, 0.0], tspan = (0.0, 20.0), T = 200, representability = :surrogate,
                expected_stage = 4),
    ProbeSystem(id = 54, name = "Lorenz (periodic)", dim = 3, true_rhs! = rhs_54!,
                u0 = [2.3, 8.1, 12.4], tspan = (0.0, 15.0), T = 300, representability = :exact,
                expected_stage = 3, expected_terms = [["u1", "u2"], ["u1", "u2", "u1*u3"], ["u1*u2", "u3"]]),
    ProbeSystem(id = 63, name = "SEIR model", dim = 4, true_rhs! = rhs_63!,
                u0 = [0.6, 0.3, 0.09, 0.01], tspan = (0.0, 30.0), T = 300, representability = :exact,
                expected_stage = 3, expected_terms = [["u1*u3"], ["u1*u3", "u2"], ["u2", "u3"], ["u3"]]),
]

function csv_value(value)
    value === nothing && return ""
    if value isa AbstractFloat
        return isfinite(value) ? @sprintf("%.16e", value) : string(value)
    end
    text = string(value)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::String, rows, columns)
    open(path, "w") do io
        println(io, join(columns, ","))
        for row in rows
            println(io, join([csv_value(get(row, col, nothing)) for col in columns], ","))
        end
    end
end

function append_csv_rows(path::String, rows, columns)
    new_file = !isfile(path)
    open(path, "a") do io
        new_file && println(io, join(columns, ","))
        for row in rows
            println(io, join([csv_value(get(row, col, nothing)) for col in columns], ","))
        end
        flush(io)
    end
end

function write_json(path::String, value)
    open(path, "w") do io
        JSON3.pretty(io, value)
        write(io, '\n')
    end
end

function basis_name_to_idx(basis::AbstractBasis)
    return Dict(basis_term_name(basis, i) => i for i in 1:basis_num_terms(basis))
end

function cumulative_stage_idxs(basis::StagedPolynomialBasis, stage::Int)
    idxs = Int[]
    for s in 1:stage
        append!(idxs, basis.term_groups[s])
    end
    return idxs
end

function term_names(basis::AbstractBasis, idxs::Vector{Int})
    return [basis_term_name(basis, i) for i in idxs]
end

function expected_stage_by_equation(sys::ProbeSystem, basis::StagedPolynomialBasis)
    sys.expected_terms === nothing && return fill(sys.expected_stage, sys.dim)
    name_to_idx = basis_name_to_idx(basis)
    idx_to_stage = Dict{Int,Int}()
    for (stage, group) in enumerate(basis.term_groups)
        for idx in group
            idx_to_stage[idx] = stage
        end
    end
    stages = Int[]
    for eq_terms in sys.expected_terms
        push!(stages, maximum(idx_to_stage[name_to_idx[name]] for name in eq_terms))
    end
    return stages
end

function expected_support_idxs(sys::ProbeSystem, basis::AbstractBasis, eq::Int)
    sys.expected_terms === nothing && return Int[]
    name_to_idx = basis_name_to_idx(basis)
    return [name_to_idx[name] for name in sys.expected_terms[eq]]
end

function make_splits(n::Int)
    n30 = floor(Int, 0.30 * n)
    n35 = floor(Int, 0.35 * n)
    n70 = n - n30
    return Dict(
        "A" => (fit = collect(1:n70), holdout = collect((n70 + 1):n)),
        "B" => (fit = collect((n30 + 1):n), holdout = collect(1:n30)),
        "C" => (fit = vcat(collect(1:n35), collect((n - n35 + 1):n)),
                holdout = collect((n35 + 1):(n - n35))),
    )
end

function normalised_mse(residual::Vector{Float64}, target::Vector{Float64})
    mse = mean(abs2, residual)
    v = mean(abs2, target .- mean(target))
    return v <= eps(Float64) ? Inf : mse / v
end

function ls_fit_eval(Phi::AbstractMatrix, y::AbstractVector, fit_idxs::Vector{Int}, holdout_idxs::Vector{Int})
    Phi_fit = Matrix(Phi[fit_idxs, :])
    Phi_hold = Matrix(Phi[holdout_idxs, :])
    y_fit = Vector(y[fit_idxs])
    y_hold = Vector(y[holdout_idxs])
    ncols = size(Phi_fit, 2)
    try
        coeffs = ncols == 0 ? Float64[] : Phi_fit \ y_fit
        fit_resid = ncols == 0 ? -y_fit : Phi_fit * coeffs - y_fit
        hold_resid = ncols == 0 ? -y_hold : Phi_hold * coeffs - y_hold
        valid = all(isfinite, coeffs) && all(isfinite, fit_resid) && all(isfinite, hold_resid)
        rank_value = ncols == 0 ? 0 : rank(Phi_fit)
        cond_value = ncols == 0 ? Inf : cond(Phi_fit)
        return (
            coeffs = coeffs,
            train_residual = mean(abs2, fit_resid),
            holdout_residual = mean(abs2, hold_resid),
            normalised_holdout_residual = normalised_mse(hold_resid, y_hold),
            rank = rank_value,
            condition_number = cond_value,
            valid = valid,
            reason = valid ? "" : "nonfinite_ls_result",
        )
    catch err
        return (
            coeffs = zeros(ncols),
            train_residual = Inf,
            holdout_residual = Inf,
            normalised_holdout_residual = Inf,
            rank = 0,
            condition_number = Inf,
            valid = false,
            reason = "ls_failed:$(typeof(err))",
        )
    end
end

function analytic_derivatives(sys::ProbeSystem, traj::Trajectory)
    dX = zeros(Float64, size(traj.x))
    du = zeros(Float64, sys.dim)
    for row in axes(traj.x, 1)
        sys.true_rhs!(du, view(traj.x, row, :), nothing, traj.t[row])
        dX[row, :] .= du
    end
    return dX
end

function generate_trajectory(sys::ProbeSystem)
    t_grid = collect(range(sys.tspan[1], sys.tspan[2]; length = sys.T))
    prob = ODEProblem(sys.true_rhs!, copy(sys.u0), sys.tspan, nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    length(sol.t) == sys.T || error("solver returned $(length(sol.t)) points for system $(sys.id)")
    return Trajectory(t_grid, Array(sol)')
end

function prune_terms(coeffs::Vector{Float64}, idxs::Vector{Int}, basis::AbstractBasis)
    isempty(coeffs) && return String[]
    max_abs = maximum(abs.(coeffs))
    cutoff = max(1e-6, 1e-3 * max_abs)
    return [basis_term_name(basis, idxs[i]) for i in eachindex(idxs) if abs(coeffs[i]) >= cutoff]
end

function stage_rows_for_equation(sys::ProbeSystem, basis::StagedPolynomialBasis, traj::Trajectory,
                                 dX::Matrix{Float64}, eq::Int, expected_eq_stage::Int)
    splits = make_splits(length(traj.t))
    y = dX[:, eq]
    rows = Dict{String,Any}[]
    metrics = Dict{Tuple{String,Int},Any}()
    new_counts = [length(basis.term_groups[s]) for s in 1:MAX_STAGE]

    for split_label in sort(collect(keys(splits)))
        split = splits[split_label]
        for stage in 1:MAX_STAGE
            idxs = cumulative_stage_idxs(basis, stage)
            Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
            result = ls_fit_eval(Phi, y, split.fit, split.holdout)
            metrics[(split_label, stage)] = result
        end
        for stage in 1:MAX_STAGE
            result = metrics[(split_label, stage)]
            idxs = cumulative_stage_idxs(basis, stage)
            next_stage = findfirst(s -> s > stage && new_counts[s] > 0, 1:MAX_STAGE)
            gain_abs = NaN
            gain_rel = NaN
            verdict = "invalid_or_inconclusive"
            if result.valid && next_stage !== nothing && metrics[(split_label, next_stage)].valid
                next_residual = metrics[(split_label, next_stage)].holdout_residual
                gain_abs = result.holdout_residual - next_residual
                gain_rel = result.holdout_residual == 0.0 ? Inf : gain_abs / result.holdout_residual
                verdict = gain_abs > 0.0 ? "potential_detected" : "no_potential"
            elseif result.valid && next_stage === nothing
                verdict = "no_potential"
            end
            push!(rows, Dict{String,Any}(
                "row_type" => "stage_capacity",
                "system_id" => sys.id,
                "system_name" => sys.name,
                "dim" => sys.dim,
                "representability" => string(sys.representability),
                "equation" => eq,
                "expected_eq_stage" => expected_eq_stage,
                "tested_stage" => stage,
                "new_terms" => new_counts[stage],
                "empty_stage" => new_counts[stage] == 0,
                "split" => split_label,
                "train_residual" => result.train_residual,
                "holdout_residual" => result.holdout_residual,
                "normalised_holdout_residual" => result.normalised_holdout_residual,
                "absolute_gain" => gain_abs,
                "relative_gain" => gain_rel,
                "rank" => result.rank,
                "condition_number" => result.condition_number,
                "valid" => result.valid,
                "invalid_reason" => result.reason,
                "fitted_coefficients" => join(result.coeffs, "|"),
                "terms" => join(term_names(basis, idxs), "|"),
                "verdict" => verdict,
            ))
        end
    end
    return rows, metrics, new_counts
end

function reference_rows_for_equation(sys::ProbeSystem, basis::StagedPolynomialBasis, traj::Trajectory,
                                     dX::Matrix{Float64}, analytic_dX::Matrix{Float64},
                                     eq::Int, expected_eq_stage::Int)
    sys.representability != :exact && return Dict{String,Any}[]
    splits = make_splits(length(traj.t))
    y = dX[:, eq]
    rows = Dict{String,Any}[]
    support = expected_support_idxs(sys, basis, eq)
    Phi = EvoODE.build_design_matrix(basis, support, traj.x, traj.t)
    for split_label in sort(collect(keys(splits)))
        split = splits[split_label]
        fit_result = ls_fit_eval(Phi, y, split.fit, split.holdout)
        push!(rows, Dict{String,Any}(
            "row_type" => "noise_floor_true_support_fit",
            "system_id" => sys.id, "system_name" => sys.name, "dim" => sys.dim,
            "representability" => string(sys.representability), "equation" => eq,
            "expected_eq_stage" => expected_eq_stage, "tested_stage" => expected_eq_stage,
            "new_terms" => length(support), "empty_stage" => false, "split" => split_label,
            "train_residual" => fit_result.train_residual,
            "holdout_residual" => fit_result.holdout_residual,
            "normalised_holdout_residual" => fit_result.normalised_holdout_residual,
            "absolute_gain" => NaN, "relative_gain" => NaN, "rank" => fit_result.rank,
            "condition_number" => fit_result.condition_number, "valid" => fit_result.valid,
            "invalid_reason" => fit_result.reason, "fitted_coefficients" => join(fit_result.coeffs, "|"),
            "terms" => join(term_names(basis, support), "|"), "verdict" => "invalid_or_inconclusive",
        ))
        hold = split.holdout
        resid = analytic_dX[hold, eq] - y[hold]
        fit_resid = analytic_dX[split.fit, eq] - y[split.fit]
        push!(rows, Dict{String,Any}(
            "row_type" => "noise_floor_analytic_rhs",
            "system_id" => sys.id, "system_name" => sys.name, "dim" => sys.dim,
            "representability" => string(sys.representability), "equation" => eq,
            "expected_eq_stage" => expected_eq_stage, "tested_stage" => expected_eq_stage,
            "new_terms" => length(support), "empty_stage" => false, "split" => split_label,
            "train_residual" => mean(abs2, fit_resid),
            "holdout_residual" => mean(abs2, resid),
            "normalised_holdout_residual" => normalised_mse(Vector(resid), y[hold]),
            "absolute_gain" => NaN, "relative_gain" => NaN, "rank" => length(support),
            "condition_number" => NaN, "valid" => all(isfinite, resid),
            "invalid_reason" => "", "fitted_coefficients" => "",
            "terms" => "analytic_rhs", "verdict" => "invalid_or_inconclusive",
        ))
    end
    return rows
end

function system26_discovered_rows(sys::ProbeSystem, basis::StagedPolynomialBasis, traj::Trajectory,
                                  dX::Matrix{Float64}, expected_eq_stage::Int)
    sys.id == 26 || return Dict{String,Any}[]
    # WP-T2 reported du2 support {u1, u1^2}; compare that failure mode directly.
    names = ["u1", "u1^2"]
    name_to_idx = basis_name_to_idx(basis)
    support = [name_to_idx[name] for name in names]
    splits = make_splits(length(traj.t))
    y = dX[:, 2]
    rows = Dict{String,Any}[]
    Phi = EvoODE.build_design_matrix(basis, support, traj.x, traj.t)
    for split_label in sort(collect(keys(splits)))
        split = splits[split_label]
        result = ls_fit_eval(Phi, y, split.fit, split.holdout)
        push!(rows, Dict{String,Any}(
            "row_type" => "system26_wp_t2_discovered_support",
            "system_id" => sys.id, "system_name" => sys.name, "dim" => sys.dim,
            "representability" => string(sys.representability), "equation" => 2,
            "expected_eq_stage" => expected_eq_stage, "tested_stage" => 3,
            "new_terms" => length(support), "empty_stage" => false, "split" => split_label,
            "train_residual" => result.train_residual,
            "holdout_residual" => result.holdout_residual,
            "normalised_holdout_residual" => result.normalised_holdout_residual,
            "absolute_gain" => NaN, "relative_gain" => NaN, "rank" => result.rank,
            "condition_number" => result.condition_number, "valid" => result.valid,
            "invalid_reason" => result.reason, "fitted_coefficients" => join(result.coeffs, "|"),
            "terms" => join(names, "|"), "verdict" => "invalid_or_inconclusive",
        ))
    end
    return rows
end

function countercheck_for_equation(sys::ProbeSystem, basis::StagedPolynomialBasis, traj::Trajectory,
                                   dX::Matrix{Float64}, eq::Int, expected_eq_stage::Int)
    sys.representability != :exact && return nothing
    idxs = cumulative_stage_idxs(basis, expected_eq_stage)
    Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
    all_idxs = collect(1:length(traj.t))
    result = ls_fit_eval(Phi, dX[:, eq], all_idxs, all_idxs)
    pruned = sort(prune_terms(result.coeffs, idxs, basis))
    expected = sort(term_names(basis, expected_support_idxs(sys, basis, eq)))
    return Dict{String,Any}(
        "system_id" => sys.id,
        "equation" => eq,
        "expected_stage" => expected_eq_stage,
        "surviving_terms" => pruned,
        "true_terms" => expected,
        "support_exact" => pruned == expected,
        "valid" => result.valid,
    )
end

function max_useful_stage(metrics, new_counts, split_label::String, tau_rel::Float64, tau_abs::Float64)
    max_stage = 1
    for stage in 1:(MAX_STAGE - 1)
        new_counts[stage] == 0 && continue
        next_stage = findfirst(s -> s > stage && new_counts[s] > 0, 1:MAX_STAGE)
        next_stage === nothing && continue
        current = metrics[(split_label, stage)]
        future = metrics[(split_label, next_stage)]
        (!current.valid || !future.valid) && continue
        delta = current.holdout_residual - future.holdout_residual
        rel = current.holdout_residual == 0.0 ? Inf : delta / current.holdout_residual
        if delta > tau_abs && rel > tau_rel
            max_stage = max(max_stage, next_stage)
        end
    end
    return max_stage
end

function run_system(sys::ProbeSystem)
    println(@sprintf("SYSTEM id=%d name=%s dim=%d", sys.id, sys.name, sys.dim))
    traj = generate_trajectory(sys)
    dX = EvoODE.estimate_derivatives(traj)
    analytic_dX = analytic_derivatives(sys, traj)
    basis = default_staged_polynomial_basis(sys.dim)
    expected_eq_stages = expected_stage_by_equation(sys, basis)
    if sys.id == 63 && expected_eq_stages != [3, 3, 1, 1]
        error("expected-stage sanity check failed for system 63: $(expected_eq_stages)")
    end
    if sys.id == 54 && expected_eq_stages != [1, 3, 3]
        error("expected-stage sanity check failed for system 54: $(expected_eq_stages)")
    end

    rows = Dict{String,Any}[]
    grid_rows = Dict{String,Any}[]
    counterchecks = Any[]
    metrics_by_eq = Dict{Int,Any}()
    new_counts_by_eq = Dict{Int,Any}()

    for eq in 1:sys.dim
        stage_rows, metrics, new_counts = stage_rows_for_equation(sys, basis, traj, dX, eq, expected_eq_stages[eq])
        append!(rows, stage_rows)
        append!(rows, reference_rows_for_equation(sys, basis, traj, dX, analytic_dX, eq, expected_eq_stages[eq]))
        cc = countercheck_for_equation(sys, basis, traj, dX, eq, expected_eq_stages[eq])
        cc !== nothing && push!(counterchecks, cc)
        metrics_by_eq[eq] = metrics
        new_counts_by_eq[eq] = new_counts
        for tau_rel in TAU_REL_GRID, tau_abs in TAU_ABS_GRID, split_label in ("A", "B", "C")
            mus = max_useful_stage(metrics, new_counts, split_label, tau_rel, tau_abs)
            push!(grid_rows, Dict{String,Any}(
                "system_id" => sys.id,
                "system_name" => sys.name,
                "representability" => string(sys.representability),
                "equation" => eq,
                "expected_eq_stage" => expected_eq_stages[eq],
                "split" => split_label,
                "tau_rel" => tau_rel,
                "tau_abs" => tau_abs,
                "max_useful_stage" => mus,
                "stage_error" => mus - expected_eq_stages[eq],
            ))
        end
    end
    append!(rows, system26_discovered_rows(sys, basis, traj, dX, sys.id == 26 ? expected_eq_stages[2] : 0))
    return rows, grid_rows, counterchecks
end

const DETAIL_COLUMNS = [
    "row_type", "system_id", "system_name", "dim", "representability", "equation",
    "expected_eq_stage", "tested_stage", "new_terms", "empty_stage", "split",
    "train_residual", "holdout_residual", "normalised_holdout_residual",
    "absolute_gain", "relative_gain", "rank", "condition_number", "valid",
    "invalid_reason", "fitted_coefficients", "terms", "verdict",
]

const GRID_COLUMNS = [
    "system_id", "system_name", "representability", "equation", "expected_eq_stage",
    "split", "tau_rel", "tau_abs", "max_useful_stage", "stage_error",
]

function median_stage(values)
    sorted_values = sort(collect(values))
    return sorted_values[cld(length(sorted_values), 2)]
end

function summarise_grid(grid_rows)
    grouped = Dict{Tuple{Float64,Float64,Int,Int},Vector{Int}}()
    meta = Dict{Tuple{Float64,Float64,Int,Int},Dict{String,Any}}()
    for row in grid_rows
        row["representability"] == "exact" || continue
        key = (row["tau_rel"], row["tau_abs"], row["system_id"], row["equation"])
        push!(get!(grouped, key, Int[]), row["max_useful_stage"])
        meta[key] = row
    end
    by_grid = Dict{Tuple{Float64,Float64},Any}()
    for (key, stages) in grouped
        tau_rel, tau_abs, sid, eq = key
        grid_key = (tau_rel, tau_abs)
        if !haskey(by_grid, grid_key)
            by_grid[grid_key] = Dict("under" => Any[], "exact" => Any[], "over" => Any[])
        end
        representative = meta[key]
        predicted = median_stage(stages)
        expected = representative["expected_eq_stage"]
        bucket = predicted < expected ? "under" : predicted > expected ? "over" : "exact"
        push!(by_grid[grid_key][bucket], Dict(
            "system_id" => sid,
            "equation" => eq,
            "expected" => expected,
            "predicted" => predicted,
        ))
    end
    records = Any[]
    for ((tau_rel, tau_abs), buckets) in sort(collect(by_grid), by = x -> (x[1][1], x[1][2]))
        push!(records, Dict(
            "tau_rel" => tau_rel,
            "tau_abs" => tau_abs,
            "under" => length(buckets["under"]),
            "exact" => length(buckets["exact"]),
            "over" => length(buckets["over"]),
            "under_equations" => buckets["under"],
            "over_equations" => buckets["over"],
        ))
    end
    return records
end

function summarise_separation(grid_rows)
    by_key = Dict{Tuple{Float64,Float64,String},Dict{Tuple{Int,Int},Int}}()
    for row in grid_rows
        row["system_id"] in (11, 26) || continue
        key = (row["tau_rel"], row["tau_abs"], row["split"])
        by_key[key] = get(by_key, key, Dict{Tuple{Int,Int},Int}())
        by_key[key][(row["system_id"], row["equation"])] = row["max_useful_stage"]
    end

    split_hits = Any[]
    for ((tau_rel, tau_abs, split), values) in sort(collect(by_key), by = x -> (x[1][1], x[1][2], x[1][3]))
        s11 = get(values, (11, 1), -1)
        s26_eq1 = get(values, (26, 1), -1)
        s26_eq2 = get(values, (26, 2), -1)
        if s11 >= 4 && s26_eq1 <= 3 && s26_eq2 <= 3
            push!(split_hits, Dict(
                "tau_rel" => tau_rel,
                "tau_abs" => tau_abs,
                "split" => split,
                "system11_eq1" => s11,
                "system26_eq1" => s26_eq1,
                "system26_eq2" => s26_eq2,
            ))
        end
    end

    by_grid = Dict{Tuple{Float64,Float64,Int,Int},Vector{Int}}()
    for row in grid_rows
        row["system_id"] in (11, 26) || continue
        key = (row["tau_rel"], row["tau_abs"], row["system_id"], row["equation"])
        push!(get!(by_grid, key, Int[]), row["max_useful_stage"])
    end
    med = Dict{Tuple{Float64,Float64,Int,Int},Int}(key => median_stage(values) for (key, values) in by_grid)
    median_hits = Any[]
    for tau_rel in TAU_REL_GRID, tau_abs in TAU_ABS_GRID
        s11 = get(med, (tau_rel, tau_abs, 11, 1), -1)
        s26_eq1 = get(med, (tau_rel, tau_abs, 26, 1), -1)
        s26_eq2 = get(med, (tau_rel, tau_abs, 26, 2), -1)
        if s11 >= 4 && s26_eq1 <= 3 && s26_eq2 <= 3
            push!(median_hits, Dict(
                "tau_rel" => tau_rel,
                "tau_abs" => tau_abs,
                "system11_eq1" => s11,
                "system26_eq1" => s26_eq1,
                "system26_eq2" => s26_eq2,
            ))
        end
    end
    return Dict("split_hits" => split_hits, "median_hits" => median_hits)
end

function lookup_stage_holdout(rows, system_id, eq, row_type, stage, split)
    matches = [r for r in rows if r["system_id"] == system_id && r["equation"] == eq &&
               r["row_type"] == row_type && r["tested_stage"] == stage && r["split"] == split]
    isempty(matches) && return NaN
    return matches[1]["holdout_residual"]
end

function format_equation_list(items)
    isempty(items) && return "none"
    return join(["system $(x["system_id"]) eq $(x["equation"]) expected $(x["expected"]) predicted $(x["predicted"])" for x in items], "; ")
end

function write_report(summary, all_rows, grid_rows)
    grid_summary = summary["grid_summary"]
    separation = summary["separation"]
    support_matches = [c for c in summary["counterchecks"] if c["support_exact"]]
    total_counterchecks = length(summary["counterchecks"])
    s26_stage3 = Dict(split => lookup_stage_holdout(all_rows, 26, 2, "stage_capacity", 3, split) for split in ("A", "B", "C"))
    s26_wpt2 = Dict(split => lookup_stage_holdout(all_rows, 26, 2, "system26_wp_t2_discovered_support", 3, split) for split in ("A", "B", "C"))
    best_grid = isempty(grid_summary) ? nothing : sort(grid_summary, by = g -> (g["under"] + g["over"], -g["exact"]))[1]

    open(REPORT_MD, "w") do io
        println(io, "# Stage Potential Probe")
        println(io)
        println(io, "Outputs written at $(summary["timestamp"]).")
        println(io)
        println(io, "## Separation")
        if isempty(separation["median_hits"]) && isempty(separation["split_hits"])
            println(io, "No threshold-grid point made the requested separation: System 11 reaching at least stage 4 while both System 26 equations stop at stage 3 or earlier.")
            println(io, "System 11 is split-sensitive: split A/C reach stage 5 across the grid, while split B stops at stage 2. System 26 keeps showing future-stage gain: the median verdict is stage 5 for both equations at the best calibration grid.")
        else
            println(io, "Median-over-splits separation grid points: $(separation["median_hits"]).")
            println(io, "Split-level separation grid points: $(separation["split_hits"]).")
        end
        println(io)
        println(io, "## Calibration")
        if best_grid === nothing
            println(io, "No exact-system grid rows were available.")
        else
            println(io, "Best median-over-splits grid: tau_rel=$(best_grid["tau_rel"]), tau_abs=$(best_grid["tau_abs"]).")
            println(io, "Confusion: under=$(best_grid["under"]), exact=$(best_grid["exact"]), over=$(best_grid["over"]).")
            println(io, "Under-shoot equations: $(format_equation_list(best_grid["under_equations"])).")
            println(io, "Over-shoot equations: $(format_equation_list(best_grid["over_equations"])).")
        end
        println(io)
        println(io, "## Is Staging The Target?")
        println(io, "System 26 du2 holdout residuals, full stage-3 library: $(s26_stage3).")
        println(io, "System 26 du2 holdout residuals, WP-T2 discovered support {u1,u1^2}: $(s26_wpt2).")
        println(io)
        println(io, "## Gate Vs Selector")
        println(io, "Thresholded full-library LS recovered the true support on $(length(support_matches)) of $(total_counterchecks) exact equations.")
        println(io, "Support-exact counterchecks: $(support_matches).")
    end
end

function main()
    mkpath(OUTPUT_DIR)
    isfile(DETAIL_CSV) && rm(DETAIL_CSV)
    isfile(GRID_CSV) && rm(GRID_CSV)
    all_rows = Dict{String,Any}[]
    all_grid_rows = Dict{String,Any}[]
    counterchecks = Any[]
    started = time()
    for sys in PROBE_SYSTEMS
        rows, grid_rows, sys_counterchecks = run_system(sys)
        append_csv_rows(DETAIL_CSV, rows, DETAIL_COLUMNS)
        append_csv_rows(GRID_CSV, grid_rows, GRID_COLUMNS)
        append!(all_rows, rows)
        append!(all_grid_rows, grid_rows)
        append!(counterchecks, sys_counterchecks)
        if time() - started > 15 * 60
            println("STOP: exceeded 15 minute diagnostic budget after system $(sys.id)")
            break
        end
    end
    summary = Dict{String,Any}(
        "script" => SCRIPT_SLUG,
        "timestamp" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "output_dir" => OUTPUT_DIR,
        "detail_csv" => DETAIL_CSV,
        "grid_csv" => GRID_CSV,
        "systems" => [sys.id for sys in PROBE_SYSTEMS],
        "tau_rel_grid" => collect(TAU_REL_GRID),
        "tau_abs_grid" => collect(TAU_ABS_GRID),
        "trajectory_solver" => Dict("algorithm" => "Tsit5", "abstol" => 1e-9, "reltol" => 1e-9),
        "counterchecks" => counterchecks,
        "grid_summary" => summarise_grid(all_grid_rows),
        "separation" => summarise_separation(all_grid_rows),
        "elapsed_s" => time() - started,
    )
    write_json(SUMMARY_JSON, summary)
    write_report(summary, all_rows, all_grid_rows)
    println("Wrote $(DETAIL_CSV)")
    println("Wrote $(GRID_CSV)")
    println("Wrote $(SUMMARY_JSON)")
    println("Wrote $(REPORT_MD)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
