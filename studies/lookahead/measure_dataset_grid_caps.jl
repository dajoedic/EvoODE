import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf
using Statistics

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))

include(joinpath(REPO_ROOT, "benchmarks", "run_odebench.jl"))

const TARGET_SYSTEM_IDS = [3, 11, 26, 31, 54, 63]
const IC_SETS = [1, 2]
const OUTPUT_DIR = joinpath(REPO_ROOT, "outputs", "studies", "lookahead", "wp_g1")
const CSV_PATH = joinpath(OUTPUT_DIR, "dataset_grid_caps.csv")
const REPORT_PATH = joinpath(REPO_ROOT, "docs", "wp_g1_dataset_grid_caps.md")
const DATA_SOURCES = ["stored", "self_integrated"]

const LOOKAHEAD_CAP_POLICY_REGRESSION = (
    estimator = :local_poly,
    weighting = :richardson_wls,
    aggregation = :majority_no_undecided_at_or_below,
    lookahead_horizon = 2,
    tau_rel = 1e-4,
    tau_abs = 1e-8,
    cond_cap = 1e10,
    excitation_floor = 1e-10,
)

const TRUE_STAGES = Dict(
    3 => [2],
    11 => [4],
    26 => [3, 3],
    31 => [3, 3],
    54 => [3, 3, 3],
    63 => [3, 3, 1, 1],
)

const CURRENT_PER_SYSTEM_GRID_CAPS = Dict(
    3 => Union{Nothing,Int}[2],
    11 => Union{Nothing,Int}[4],
    26 => Union{Nothing,Int}[3, 3],
    31 => Union{Nothing,Int}[3, 3],
    54 => Union{Nothing,Int}[nothing, 2, 2],
    63 => Union{Nothing,Int}[nothing, nothing, nothing, nothing],
)

function rhs_03!(du, u, _, _)
    du[1] = 0.79 * u[1] * (1.0 - u[1] / 74.3)
end

function rhs_11!(du, u, _, _)
    du[1] = -u[1]^3
end

function rhs_26!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

function rhs_31!(du, u, _, _)
    du[1] = -0.4 * u[1] * u[2]
    du[2] = 0.4 * u[1] * u[2] - 0.314 * u[2]
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

const RHS_BY_SYSTEM = Dict(
    3 => rhs_03!,
    11 => rhs_11!,
    26 => rhs_26!,
    31 => rhs_31!,
    54 => rhs_54!,
    63 => rhs_63!,
)

function json_string(value)
    if value === nothing
        return "null"
    elseif value isa AbstractString
        escaped = replace(value, "\\" => "\\\\", "\"" => "\\\"")
        return "\"" * escaped * "\""
    elseif value isa Symbol
        return json_string(String(value))
    elseif value isa Bool
        return value ? "true" : "false"
    elseif value isa Real
        isfinite(value) && return string(value)
        return json_string(string(value))
    elseif value isa AbstractVector
        return "[" * join(json_string.(value), ",") * "]"
    elseif value isa AbstractDict
        parts = String[]
        for key in sort(collect(keys(value)); by = string)
            push!(parts, json_string(string(key)) * ":" * json_string(value[key]))
        end
        return "{" * join(parts, ",") * "}"
    end
    return json_string(string(value))
end

function wp_g1_csv_escape(value)
    text = string(value)
    if occursin('"', text) || occursin(',', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::String, rows)
    headers = [
        "system_id",
        "ic_set",
        "data_source",
        "equation_index",
        "dim",
        "description",
        "cap",
        "true_stage",
        "classification",
        "current_per_system_grid_cap",
        "dataset_caps",
        "residuals_by_split_stage",
        "floors_by_split_stage",
        "noise_floor_mean_by_stage",
        "usable_by_split_stage",
        "split_decisions",
        "derivative_active_fraction",
        "state_below_1pct_spread_time",
        "t_length",
        "t_start",
        "t_end",
        "source",
    ]
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(headers, ","))
        for row in rows
            println(io, join([wp_g1_csv_escape(getfield(row, Symbol(header))) for header in headers], ","))
        end
    end
end

function classify_cap(cap, true_stage::Int)
    cap === nothing && return "nothing"
    cap < true_stage && return "violation"
    cap == true_stage && return "correct"
    return "conservative"
end

function decision_record(decision)
    return Dict(
        "kind" => String(decision.kind),
        "cap" => decision.cap,
        "stage" => decision.stage,
    )
end

function format_cap(cap)
    cap === nothing && return "nothing"
    return string(cap)
end

function _split_stage_diagnostics(traj::Trajectory, basis::StagedPolynomialBasis, eq::Int, policy::LookAheadStageCapPolicy)
    EvoODE._cap_validate_policy(policy)
    dX = EvoODE._cap_estimate_derivatives(traj, policy.estimator)
    rich = EvoODE._cap_richardson_error_estimate(traj, policy.estimator)
    y = dX[:, eq]
    weights = policy.weighting == :richardson_wls ? EvoODE._cap_weights_from_richardson(rich[:, eq]) : ones(length(y))
    max_basis_stage = EvoODE._max_stage(basis)
    new_counts = [length(basis.term_groups[s]) for s in 1:max_basis_stage]
    applicable_stages = [s for s in 1:max_basis_stage if new_counts[s] > 0]

    residuals_by_split = Vector{Vector{Float64}}()
    floors_by_split = Vector{Vector{Float64}}()
    usable_by_split = Vector{Vector{Bool}}()
    raw_split_decisions = NamedTuple[]
    split_decisions = Dict{String,Any}[]

    for split in EvoODE._cap_splits(length(traj.t))
        residuals = fill(Inf, max_basis_stage)
        floors = fill(Inf, max_basis_stage)
        usable = falses(max_basis_stage)
        for stage in 1:max_basis_stage
            idxs = EvoODE._cap_cumulative_stage_idxs(basis, stage)
            Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
            usable[stage] = EvoODE._cap_stage_condition(Phi, y, split.fit, policy)
            fit = EvoODE._cap_fit_eval(Phi, y, split.fit, split.holdout, weights)
            residuals[stage] = fit.residual
            floors[stage] = mean(abs2, rich[split.holdout, eq])
            usable[stage] &= fit.valid
        end
        push!(residuals_by_split, residuals)
        push!(floors_by_split, floors)
        push!(usable_by_split, usable)
        decision = EvoODE._cap_split_decision(residuals, usable, floors, applicable_stages, policy)
        push!(raw_split_decisions, decision)
        push!(split_decisions, decision_record(decision))
    end

    cap = EvoODE._cap_aggregate_split_decisions(raw_split_decisions, policy)
    return (
        cap = cap,
        residuals_by_split = residuals_by_split,
        floors_by_split = floors_by_split,
        usable_by_split = usable_by_split,
        split_decisions = split_decisions,
    )
end

function _load_target_systems(path::String, ic_set::Int)
    systems = load_systems_json(path; ic_set = ic_set)
    return Dict(system.id => system for system in systems if system.id in TARGET_SYSTEM_IDS)
end

function integrate_dataset_grid(system::SystemData)
    f! = RHS_BY_SYSTEM[system.id]
    t = system.traj.t
    u0 = Vector{Float64}(system.traj.x[1, :])
    prob = ODEProblem(f!, copy(u0), (first(t), last(t)), nothing)
    sol = solve(prob, Tsit5(); saveat = t, abstol = 1e-9, reltol = 1e-9)
    if sol.retcode != ReturnCode.Success
        error("Self-integration failed for system $(system.id): $(sol.retcode)")
    end
    return SystemData(system.id, system.eq, system.eq_description, system.dim, Trajectory(t, Array(sol)'))
end

function true_rhs_matrix(system::SystemData)
    f! = RHS_BY_SYSTEM[system.id]
    T, dim = size(system.traj.x)
    out = zeros(Float64, T, dim)
    du = zeros(Float64, dim)
    @inbounds for i in 1:T
        f!(du, view(system.traj.x, i, :), nothing, system.traj.t[i])
        out[i, :] .= du
    end
    return out
end

function derivative_active_fraction(rhs_values::AbstractVector{Float64})
    max_abs = maximum(abs, rhs_values)
    max_abs == 0.0 && return 0.0
    return count(abs.(rhs_values) .> 0.01 * max_abs) / length(rhs_values)
end

function state_below_1pct_spread_time(t::AbstractVector{Float64}, x::AbstractVector{Float64})
    spread = maximum(x) - minimum(x)
    spread == 0.0 && return nothing
    threshold = minimum(x) + 0.01 * spread
    idx = findfirst(value -> value <= threshold, x)
    idx === nothing && return nothing
    return t[idx]
end

function mean_by_stage(values_by_split::Vector{Vector{Float64}})
    isempty(values_by_split) && return Float64[]
    n_stage = length(values_by_split[1])
    return [mean(split_values[stage] for split_values in values_by_split) for stage in 1:n_stage]
end

function _raw_source_by_id(path::String)
    raw = open(path, "r") do io
        JSON3.read(io)
    end
    return Dict(Int(obj["id"]) => String(get(obj, "source", "")) for obj in raw)
end

function _cap_vector(rows, system_id::Int, ic_set::Int)
    selected = sort(
        [row for row in rows if row.system_id == system_id && row.ic_set == ic_set],
        by = row -> row.equation_index,
    )
    return [row.cap == "nothing" ? "nothing" : row.cap for row in selected]
end

function measure_rows()
    data_path = joinpath(REPO_ROOT, "benchmarks", "data", "strogatz_extended.json")
    sources = _raw_source_by_id(data_path)
    policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY_REGRESSION...)
    rows = NamedTuple[]

    for ic_set in IC_SETS
        systems = _load_target_systems(data_path, ic_set)
        for system_id in TARGET_SYSTEM_IDS
            stored_system = systems[system_id]
            source_systems = [
                ("stored", stored_system),
                ("self_integrated", integrate_dataset_grid(stored_system)),
            ]
            for (data_source, system) in source_systems
            basis = default_staged_polynomial_basis(system.dim)
            rhs = true_rhs_matrix(system)
            equation_rows = NamedTuple[]
            for eq in 1:system.dim
                diag = _split_stage_diagnostics(system.traj, basis, eq, policy)
                true_stage = TRUE_STAGES[system_id][eq]
                push!(
                    equation_rows,
                    (
                        equation_index = eq,
                        cap_value = diag.cap,
                        true_stage = true_stage,
                        classification = classify_cap(diag.cap, true_stage),
                        residuals_by_split_stage = diag.residuals_by_split,
                        floors_by_split_stage = diag.floors_by_split,
                        noise_floor_mean_by_stage = mean_by_stage(diag.floors_by_split),
                        usable_by_split_stage = diag.usable_by_split,
                        split_decisions = diag.split_decisions,
                        derivative_active_fraction = derivative_active_fraction(rhs[:, eq]),
                        state_below_1pct_spread_time = state_below_1pct_spread_time(system.traj.t, system.traj.x[:, eq]),
                    ),
                )
            end
            dataset_caps = [row.cap_value for row in sort(equation_rows, by = row -> row.equation_index)]
            for row in equation_rows
                push!(
                    rows,
                    (
                        system_id = system_id,
                        ic_set = ic_set,
                        data_source = data_source,
                        equation_index = row.equation_index,
                        dim = system.dim,
                        description = system.eq_description,
                        cap = format_cap(row.cap_value),
                        true_stage = row.true_stage,
                        classification = row.classification,
                        current_per_system_grid_cap = format_cap(CURRENT_PER_SYSTEM_GRID_CAPS[system_id][row.equation_index]),
                        dataset_caps = json_string(dataset_caps),
                        residuals_by_split_stage = json_string(row.residuals_by_split_stage),
                        floors_by_split_stage = json_string(row.floors_by_split_stage),
                        noise_floor_mean_by_stage = json_string(row.noise_floor_mean_by_stage),
                        usable_by_split_stage = json_string(row.usable_by_split_stage),
                        split_decisions = json_string(row.split_decisions),
                        derivative_active_fraction = row.derivative_active_fraction,
                        state_below_1pct_spread_time = row.state_below_1pct_spread_time === nothing ? "nothing" : string(row.state_below_1pct_spread_time),
                        t_length = length(system.traj.t),
                        t_start = first(system.traj.t),
                        t_end = last(system.traj.t),
                        source = sources[system_id],
                    ),
                )
            end
            end
        end
    end

    return rows
end

function markdown_table(headers, rows)
    lines = String[
        "| " * join(headers, " | ") * " |",
        "| " * join(fill("---", length(headers)), " | ") * " |",
    ]
    for row in rows
        push!(lines, "| " * join(string.(row), " | ") * " |")
    end
    return join(lines, "\n")
end

function vector_string(values)
    return "[" * join(string.(values), ", ") * "]"
end

function cap_summary_rows(rows)
    out = []
    for system_id in TARGET_SYSTEM_IDS
        current = [format_cap(cap) for cap in CURRENT_PER_SYSTEM_GRID_CAPS[system_id]]
        caps = []
        for data_source in DATA_SOURCES
            for ic_set in IC_SETS
            selected = sort(
                [
                    row for row in rows
                    if row.system_id == system_id &&
                       row.ic_set == ic_set &&
                       row.data_source == data_source
                ],
                by = row -> row.equation_index,
            )
            push!(caps, vector_string([row.cap for row in selected]))
            end
        end
        push!(out, [system_id, vector_string(current), caps...])
    end
    return out
end

function classification_count_rows(rows, data_source::String)
    classes = ["correct", "conservative", "violation", "nothing"]
    selected = [row for row in rows if row.data_source == data_source]
    return [[data_source, class, count(row -> row.classification == class, selected)] for class in classes]
end

function violation_rows(rows)
    violations = [
        row for row in rows
        if row.classification == "violation"
    ]
    return [
        [row.system_id, row.ic_set, row.data_source, row.equation_index, row.true_stage, row.cap]
        for row in sort(violations, by = row -> (row.system_id, row.ic_set, row.equation_index))
    ]
end

function system54_prediction_rows(rows)
    selected = [
        row for row in rows
        if row.system_id == 54 && row.equation_index in (2, 3)
    ]
    return [
        [row.ic_set, row.data_source, row.equation_index, row.true_stage, row.cap, row.classification]
        for row in sort(selected, by = row -> (row.ic_set, row.data_source, row.equation_index))
    ]
end

function system63_prediction_rows(rows)
    selected = [row for row in rows if row.system_id == 63]
    return [
        [row.ic_set, row.data_source, row.equation_index, row.true_stage, row.cap, row.classification]
        for row in sort(selected, by = row -> (row.ic_set, row.data_source, row.equation_index))
    ]
end

function _row_for(rows, system_id, ic_set, data_source, equation_index)
    matches = [
        row for row in rows
        if row.system_id == system_id &&
           row.ic_set == ic_set &&
           row.data_source == data_source &&
           row.equation_index == equation_index
    ]
    length(matches) == 1 || error("Expected one row for $(system_id), ic=$(ic_set), source=$(data_source), eq=$(equation_index); got $(length(matches))")
    return matches[1]
end

function arm_comparison_rows(rows)
    out = []
    for system_id in TARGET_SYSTEM_IDS
        for ic_set in IC_SETS
            dim = length(TRUE_STAGES[system_id])
            for eq in 1:dim
                stored = _row_for(rows, system_id, ic_set, "stored", eq)
                self = _row_for(rows, system_id, ic_set, "self_integrated", eq)
                push!(
                    out,
                    [
                        system_id,
                        ic_set,
                        eq,
                        stored.true_stage,
                        stored.cap,
                        self.cap,
                        stored.cap == self.cap,
                        stored.noise_floor_mean_by_stage,
                        self.noise_floor_mean_by_stage,
                    ],
                )
            end
        end
    end
    return out
end

function signal_rows(rows)
    selected = [row for row in rows if row.data_source == "self_integrated"]
    return [
        [
            row.system_id,
            row.ic_set,
            row.equation_index,
            @sprintf("%.6g", row.derivative_active_fraction),
            row.state_below_1pct_spread_time,
            row.classification,
        ]
        for row in sort(selected, by = row -> (row.system_id, row.ic_set, row.equation_index))
    ]
end

function low_signal_failure_summary(rows)
    self_rows = [row for row in rows if row.data_source == "self_integrated"]
    low_signal = [row for row in self_rows if row.derivative_active_fraction <= 0.10]
    failing = [row for row in self_rows if row.classification in ("violation", "nothing")]
    overlap = [
        row for row in failing
        if any(ls -> ls.system_id == row.system_id && ls.ic_set == row.ic_set && ls.equation_index == row.equation_index, low_signal)
    ]
    return (
        low_signal = length(low_signal),
        failing = length(failing),
        overlap = length(overlap),
    )
end

function write_report(path::String, rows)
    grid_lengths = sort(unique(row.t_length for row in rows))
    grid_starts = sort(unique(row.t_start for row in rows))
    grid_ends = sort(unique(row.t_end for row in rows))
    violations = violation_rows(rows)
    system54_rows = system54_prediction_rows(rows)
    system63_rows = system63_prediction_rows(rows)
    system54_pass = all(row[6] != "violation" for row in system54_rows)
    system63_identifiable = any(row[6] != "nothing" for row in system63_rows)
    arm_rows = arm_comparison_rows(rows)
    arm_same = all(row[7] for row in arm_rows)
    signal_summary = low_signal_failure_summary(rows)

    lines = String[
        "# WP-G1 Dataset-Grid Look-Ahead Caps",
        "",
        "Generated by `studies/lookahead/measure_dataset_grid_caps.jl` at $(Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")).",
        "",
        "The measured trajectories in this run have t lengths `$(grid_lengths)`, starts `$(grid_starts)`, and ends `$(grid_ends)`.",
        "",
        "## Cap Comparison",
        "",
        markdown_table(
            [
                "system",
                "per-system grid caps",
                "stored IC1",
                "stored IC2",
                "self-integrated IC1",
                "self-integrated IC2",
            ],
            cap_summary_rows(rows),
        ),
        "",
        "## Classification Counts",
        "",
        markdown_table(
            ["data_source", "classification", "equations"],
            vcat(classification_count_rows(rows, "stored"), classification_count_rows(rows, "self_integrated")),
        ),
        "",
        "## Arm A vs Arm B",
        "",
        markdown_table(
            [
                "system",
                "ic_set",
                "equation",
                "true_stage",
                "stored_cap",
                "self_integrated_cap",
                "same_cap",
                "stored_noise_floor_mean_by_stage",
                "self_noise_floor_mean_by_stage",
            ],
            arm_rows,
        ),
        "",
        "All stored and self-integrated caps match: `$(arm_same)`.",
        "",
        "## Violations",
        "",
    ]

    if isempty(violations)
        push!(lines, "No cap-below-truth violations were measured.")
    else
        push!(
            lines,
            markdown_table(
                ["system", "ic_set", "data_source", "equation", "true_stage", "cap"],
                violations,
            ),
        )
    end

    append!(
        lines,
        [
            "",
            "## Prediction 1: System 54",
            "",
            markdown_table(["ic_set", "data_source", "equation", "true_stage", "cap", "classification"], system54_rows),
            "",
            "Prediction outcome: System 54 equations 2 and 3 have no measured violation across the two dataset-grid initial-condition sets: `$(system54_pass)`.",
            "",
            "## Prediction 2: System 63",
            "",
            markdown_table(["ic_set", "data_source", "equation", "true_stage", "cap", "classification"], system63_rows),
            "",
            "Prediction outcome: at least one System 63 equation is identifiable on the dataset grid: `$(system63_identifiable)`.",
            "",
            "## Dynamics Horizon",
            "",
            markdown_table(
                [
                    "system",
                    "ic_set",
                    "equation",
                    "derivative_active_fraction",
                    "state_below_1pct_spread_time",
                    "self_integrated_classification",
                ],
                signal_rows(rows),
            ),
            "",
            "Low-signal cells use `derivative_active_fraction <= 0.10`. Low-signal count: `$(signal_summary.low_signal)`, failing count among self-integrated cells: `$(signal_summary.failing)`, overlap: `$(signal_summary.overlap)`.",
            "",
            "## Outputs",
            "",
            "- CSV: `outputs/studies/lookahead/wp_g1/dataset_grid_caps.csv`",
            "",
        ],
    )

    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(lines, "\n"))
    end
end

function main()
    rows = measure_rows()
    write_csv(CSV_PATH, rows)
    write_report(REPORT_PATH, rows)
    println("Wrote $(CSV_PATH)")
    println("Wrote $(REPORT_PATH)")
    println("Rows: $(length(rows))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
