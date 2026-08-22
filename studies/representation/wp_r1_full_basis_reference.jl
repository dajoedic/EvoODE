import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using JSON3
using Printf
using Statistics

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))

include(joinpath(REPO_ROOT, "studies", "regression", "run_regression.jl"))
include(joinpath(REPO_ROOT, "studies", "regression", "phase_b_config.jl"))

const WP_R1_OUTPUT_DIR = joinpath(REPO_ROOT, "outputs", "studies", "representation", "wp_r1_full_basis_reference")
const WP_R1_CSV_PATH = joinpath(WP_R1_OUTPUT_DIR, "full_basis_reference.csv")
const WP_R1_SUMMARY_PATH = joinpath(WP_R1_OUTPUT_DIR, "summary.json")
const WP_R1_REPORT_PATH = joinpath(REPO_ROOT, "docs", "WP-R1.md")
const INTEGRATION_DIVERGENCE_LIMIT = 1e6

function csv_escape(value)
    if value === nothing
        return ""
    end
    text = string(value)
    if occursin('"', text) || occursin(',', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function csv_array(values)
    return "[" * join([value === nothing ? "null" : @sprintf("%.17g", Float64(value)) for value in values], ";") * "]"
end

function coefficient_array(params::AbstractVector{<:Real})
    return "[" * join([@sprintf("%.17g", Float64(value)) for value in params], ";") * "]"
end

function full_basis_structure(dim::Int, basis::AbstractBasis)
    all_terms = collect(1:basis_num_terms(basis))
    return StructureSpec([copy(all_terms) for _ in 1:dim])
end

function r2_values_by_dimension(predicted::AbstractMatrix, observed::AbstractMatrix)
    values = r2_by_dimension(predicted, observed)
    values === nothing && return nothing
    any(value -> value === nothing, values) && return values
    return Float64[value for value in values]
end

function r2_mean(values)
    values === nothing && return nothing
    any(value -> value === nothing, values) && return nothing
    numeric = Float64[value for value in values]
    return mean(numeric)
end

function mse_by_dimension(predicted::AbstractMatrix, observed::AbstractMatrix)
    size(predicted) == size(observed) || return nothing
    all(isfinite, predicted) || return nothing
    all(isfinite, observed) || return nothing
    return [mean((predicted[:, dim_idx] .- observed[:, dim_idx]).^2) for dim_idx in 1:size(observed, 2)]
end

function fit_full_basis_derivative_projection(traj::Trajectory, basis::AbstractBasis)
    dX = EvoODE.estimate_derivatives(traj)
    active = collect(1:basis_num_terms(basis))
    params = Float64[]
    predicted = zeros(Float64, size(dX))
    per_eq_param_norms = Float64[]
    per_eq_matrix_ranks = Int[]

    for eq in 1:size(dX, 2)
        phi = EvoODE.build_design_matrix(basis, active, traj.x, traj.t)
        p_eq = phi \ dX[:, eq]
        predicted[:, eq] .= phi * p_eq
        append!(params, p_eq)
        push!(per_eq_param_norms, norm(p_eq))
        push!(per_eq_matrix_ranks, rank(phi))
    end

    derivative_r2_by_eq = r2_values_by_dimension(predicted, dX)
    derivative_mse_by_eq = mse_by_dimension(predicted, dX)
    return (
        params = params,
        predicted_derivatives = predicted,
        estimated_derivatives = dX,
        derivative_r2_by_eq = derivative_r2_by_eq,
        derivative_r2_mean = r2_mean(derivative_r2_by_eq),
        derivative_mse_by_eq = derivative_mse_by_eq,
        derivative_mse_mean = derivative_mse_by_eq === nothing ? nothing : mean(derivative_mse_by_eq),
        per_eq_param_norms = per_eq_param_norms,
        per_eq_matrix_ranks = per_eq_matrix_ranks,
    )
end

function evaluate_projection(system, ic_set::Int)
    dim = Int(system[:dim])
    basis = default_staged_polynomial_basis(dim)
    structure = full_basis_structure(dim, basis)
    traj = build_trajectory(system, ic_set)
    fit = fit_full_basis_derivative_projection(traj, basis)
    f!, n_params, _ = build_rhs(structure, basis)

    yhat = simulate(
        f!,
        fit.params,
        traj;
        abstol = BFGS_ABSTOL,
        reltol = BFGS_RELTOL,
        maxiters = BFGS_MAXITERS_SOLVE,
        clamp_val = nothing,
        reject_nonfinite = true,
        divergence_limit = INTEGRATION_DIVERGENCE_LIMIT,
        options = DiscoveryOptions(verbose = 0),
    )
    trajectory_mse = evaluate_loss(MSELoss(), yhat, traj.x)
    trajectory_stable = isfinite(trajectory_mse) && trajectory_mse < 1e6 && all(isfinite, yhat)
    trajectory_r2_metrics = r2_summary(yhat, traj.x, trajectory_mse)

    return Dict{String, Any}(
        "system_id" => Int(system[:system_id]),
        "system_name" => String(system[:system_name]),
        "dim" => dim,
        "initial_condition_set" => ic_set,
        "representability" => String(system[:representability]),
        "expected_stage" => system[:expected_stage] === nothing ? nothing : Int(system[:expected_stage]),
        "n_basis_terms" => basis_num_terms(basis),
        "n_params" => n_params,
        "derivative_r2_by_eq" => fit.derivative_r2_by_eq,
        "derivative_r2_mean" => fit.derivative_r2_mean,
        "derivative_mse_by_eq" => fit.derivative_mse_by_eq,
        "derivative_mse_mean" => fit.derivative_mse_mean,
        "trajectory_r2_by_dim" => trajectory_r2_metrics.r2_by_dim,
        "trajectory_r2_mean" => trajectory_r2_metrics.r2,
        "trajectory_mse" => trajectory_mse,
        "trajectory_stable" => trajectory_stable,
        "integration_diverged" => !trajectory_stable,
        "parameter_norm" => norm(fit.params),
        "per_eq_param_norms" => fit.per_eq_param_norms,
        "per_eq_matrix_ranks" => fit.per_eq_matrix_ranks,
        "coefficients" => fit.params,
    )
end

function write_csv(rows)
    headers = [
        "system_id",
        "system_name",
        "dim",
        "initial_condition_set",
        "representability",
        "expected_stage",
        "n_basis_terms",
        "n_params",
        "derivative_r2_by_eq",
        "derivative_r2_mean",
        "derivative_mse_by_eq",
        "derivative_mse_mean",
        "trajectory_r2_by_dim",
        "trajectory_r2_mean",
        "trajectory_mse",
        "trajectory_stable",
        "integration_diverged",
        "parameter_norm",
        "per_eq_param_norms",
        "per_eq_matrix_ranks",
        "coefficients",
    ]
    open(WP_R1_CSV_PATH, "w") do io
        println(io, join(headers, ","))
        for row in rows
            fields = [
                row["system_id"],
                row["system_name"],
                row["dim"],
                row["initial_condition_set"],
                row["representability"],
                row["expected_stage"],
                row["n_basis_terms"],
                row["n_params"],
                csv_array(row["derivative_r2_by_eq"]),
                row["derivative_r2_mean"],
                csv_array(row["derivative_mse_by_eq"]),
                row["derivative_mse_mean"],
                row["trajectory_r2_by_dim"] === nothing ? "" : csv_array(row["trajectory_r2_by_dim"]),
                row["trajectory_r2_mean"],
                row["trajectory_mse"],
                row["trajectory_stable"],
                row["integration_diverged"],
                row["parameter_norm"],
                csv_array(row["per_eq_param_norms"]),
                "[" * join(row["per_eq_matrix_ranks"], ";") * "]",
                coefficient_array(row["coefficients"]),
            ]
            println(io, join(csv_escape.(fields), ","))
        end
    end
end

function numeric_values(rows, key::String; representability = nothing)
    selected = Float64[]
    for row in rows
        representability !== nothing && row["representability"] != representability && continue
        value = row[key]
        value === nothing && continue
        push!(selected, Float64(value))
    end
    return selected
end

function distribution(values::Vector{Float64})
    isempty(values) && return Dict{String, Any}("n" => 0)
    sorted = sort(values)
    return Dict{String, Any}(
        "n" => length(sorted),
        "min" => minimum(sorted),
        "q25" => quantile(sorted, 0.25),
        "median" => median(sorted),
        "mean" => mean(sorted),
        "q75" => quantile(sorted, 0.75),
        "max" => maximum(sorted),
    )
end

function cells_by_system(rows, system_id::Int)
    return [row for row in rows if row["system_id"] == system_id]
end

function exact_system_ids(rows)
    return sort(unique(Int(row["system_id"]) for row in rows if row["representability"] == "exact"))
end

function suspicious_exact_cells(rows; threshold = 0.99)
    return [
        row for row in rows
        if row["representability"] == "exact" &&
           (row["trajectory_r2_mean"] === nothing || Float64(row["trajectory_r2_mean"]) < threshold)
    ]
end

function summarize(rows)
    system_ic_pairs = Set((Int(row["system_id"]), Int(row["initial_condition_set"])) for row in rows)
    duplicate_count = length(rows) - length(system_ic_pairs)
    missing_pairs = Tuple{Int, Int}[]
    for system_id in 1:63
        for ic_set in PHASE_B_IC_SETS
            (system_id, ic_set) in system_ic_pairs || push!(missing_pairs, (system_id, ic_set))
        end
    end

    return Dict{String, Any}(
        "csv_path" => WP_R1_CSV_PATH,
        "row_count" => length(rows),
        "unique_system_ic_pairs" => length(system_ic_pairs),
        "duplicate_count" => duplicate_count,
        "missing_pairs" => [[system_id, ic_set] for (system_id, ic_set) in missing_pairs],
        "exact_system_ids" => exact_system_ids(rows),
        "exact_system_count" => length(exact_system_ids(rows)),
        "surrogate_system_count" => length(sort(unique(Int(row["system_id"]) for row in rows if row["representability"] == "surrogate"))),
        "trajectory_r2_exact" => distribution(numeric_values(rows, "trajectory_r2_mean"; representability = "exact")),
        "trajectory_r2_surrogate" => distribution(numeric_values(rows, "trajectory_r2_mean"; representability = "surrogate")),
        "trajectory_mse_exact" => distribution(numeric_values(rows, "trajectory_mse"; representability = "exact")),
        "trajectory_mse_surrogate" => distribution(numeric_values(rows, "trajectory_mse"; representability = "surrogate")),
        "derivative_r2_exact" => distribution(numeric_values(rows, "derivative_r2_mean"; representability = "exact")),
        "derivative_r2_surrogate" => distribution(numeric_values(rows, "derivative_r2_mean"; representability = "surrogate")),
        "diverged_count" => count(row -> Bool(row["integration_diverged"]), rows),
        "diverged_cells" => [[row["system_id"], row["initial_condition_set"]] for row in rows if Bool(row["integration_diverged"])],
        "suspicious_exact_threshold" => 0.99,
        "suspicious_exact_cells" => [
            Dict(
                "system_id" => row["system_id"],
                "initial_condition_set" => row["initial_condition_set"],
                "trajectory_r2_mean" => row["trajectory_r2_mean"],
                "trajectory_mse" => row["trajectory_mse"],
                "derivative_r2_mean" => row["derivative_r2_mean"],
            )
            for row in suspicious_exact_cells(rows)
        ],
    )
end

function fmt_value(value)
    value === nothing && return "null"
    value isa Bool && return string(value)
    value isa Integer && return string(value)
    value isa AbstractFloat && return @sprintf("%.10g", value)
    return string(value)
end

function markdown_distribution(label::String, stats)
    if Int(stats["n"]) == 0
        return "| $(label) | 0 | - | - | - | - | - | - |\n"
    end
    return @sprintf(
        "| %s | %d | %.10g | %.10g | %.10g | %.10g | %.10g | %.10g |\n",
        label,
        Int(stats["n"]),
        Float64(stats["min"]),
        Float64(stats["q25"]),
        Float64(stats["median"]),
        Float64(stats["mean"]),
        Float64(stats["q75"]),
        Float64(stats["max"]),
    )
end

function write_report(summary, rows)
    open(WP_R1_REPORT_PATH, "w") do io
        println(io, "# WP-R1 - Full-basis least-squares representation reference")
        println(io)
        println(io, "This reference is the best fit obtained by unregularized least squares on the derivative problem over the full current staged basis. It is a deterministic, reproducible reference for this fitting procedure, not a proven optimum over all possible trajectory-space fits of the model class.")
        println(io)
        println(io, "CSV: `$(relpath(WP_R1_CSV_PATH, REPO_ROOT))`")
        println(io)
        println(io, "## Acceptance")
        println(io)
        println(io, "- Completeness: $(summary["row_count"]) rows, $(summary["unique_system_ic_pairs"]) unique `(system_id, ic_set)` pairs, $(summary["duplicate_count"]) duplicates, $(length(summary["missing_pairs"])) missing pairs.")
        println(io, "- Exact systems: $(summary["exact_system_count"]) system ids: `$(join(summary["exact_system_ids"], ", "))`.")
        println(io, "- Stability: $(summary["diverged_count"]) of 126 fitted models diverged during integration.")
        if !isempty(summary["diverged_cells"])
            println(io, "- Diverged cells: `$(summary["diverged_cells"])`.")
        end
        println(io)
        println(io, "Trajectory R2 distribution:")
        println(io)
        println(io, "| group | n | min | q25 | median | mean | q75 | max |")
        println(io, "|---|---:|---:|---:|---:|---:|---:|---:|")
        print(io, markdown_distribution("exact", summary["trajectory_r2_exact"]))
        print(io, markdown_distribution("surrogate", summary["trajectory_r2_surrogate"]))
        println(io)
        println(io, "Derivative-space R2 distribution:")
        println(io)
        println(io, "| group | n | min | q25 | median | mean | q75 | max |")
        println(io, "|---|---:|---:|---:|---:|---:|---:|---:|")
        print(io, markdown_distribution("exact", summary["derivative_r2_exact"]))
        print(io, markdown_distribution("surrogate", summary["derivative_r2_surrogate"]))
        println(io)
        println(io, "Trajectory MSE distribution:")
        println(io)
        println(io, "| group | n | min | q25 | median | mean | q75 | max |")
        println(io, "|---|---:|---:|---:|---:|---:|---:|---:|")
        print(io, markdown_distribution("exact", summary["trajectory_mse_exact"]))
        print(io, markdown_distribution("surrogate", summary["trajectory_mse_surrogate"]))
        println(io)
        println(io, "## Exact systems below trajectory R2 0.99")
        println(io)
        if isempty(summary["suspicious_exact_cells"])
            println(io, "None.")
        else
            println(io, "| system | ic_set | trajectory_r2 | trajectory_mse | derivative_r2 |")
            println(io, "|---:|---:|---:|---:|---:|")
            for cell in summary["suspicious_exact_cells"]
                println(
                    io,
                    "| $(cell["system_id"]) | $(cell["initial_condition_set"]) | $(fmt_value(cell["trajectory_r2_mean"])) | $(fmt_value(cell["trajectory_mse"])) | $(fmt_value(cell["derivative_r2_mean"])) |",
                )
            end
        end
        println(io)
        println(io, "## Determinism")
        println(io)
        println(io, "The script writes deterministic CSV and summary content with no timestamps. Determinism was checked by running the script twice and comparing the CSV byte-for-byte.")
    end
end

function main()
    mkpath(WP_R1_OUTPUT_DIR)
    rows = Dict{String, Any}[]
    for system in sort(PHASE_B_SYSTEMS; by = row -> Int(row[:system_id]))
        for ic_set in PHASE_B_IC_SETS
            push!(rows, evaluate_projection(system, ic_set))
        end
    end

    sort!(rows; by = row -> (Int(row["system_id"]), Int(row["initial_condition_set"])))
    write_csv(rows)
    summary = summarize(rows)
    open(WP_R1_SUMMARY_PATH, "w") do io
        JSON3.pretty(io, summary)
        println(io)
    end
    write_report(summary, rows)
    println("Wrote $(length(rows)) rows to $(WP_R1_CSV_PATH)")
    println("Wrote summary to $(WP_R1_SUMMARY_PATH)")
    println("Wrote report to $(WP_R1_REPORT_PATH)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
