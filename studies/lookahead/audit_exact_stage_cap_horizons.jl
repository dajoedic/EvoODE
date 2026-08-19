import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
include(joinpath(REPO_ROOT, "studies", "output_path_guard.jl"))

const SCRIPT_SLUG = "audit_exact_stage_cap_horizons"
const OUTPUT_DIR = study_resolve_output_dir(joinpath(REPO_ROOT, "outputs", "studies", "lookahead", SCRIPT_SLUG), ARGS)
const CSV_PATH = joinpath(OUTPUT_DIR, "exact_stage_cap_horizon_audit.csv")
const REPORT_PATH = study_resolve_output_path(joinpath(REPO_ROOT, "docs", "wp_c1_stage_cap_horizon_audit.md"), ARGS; flag = "--report")
const HORIZONS = [2, 3, 4, 5]
const STABILITY_SYSTEM_IDS = [26, 27, 29, 31, 54]
const DEFECT_SYSTEM_IDS = [28, 32]
const OLD_CONFIG_FINGERPRINT = "06e1c71fbd10a3a4"
const OLD_PHASE_B_FINGERPRINT = "41f69abc3670b6c4"

include(joinpath(REPO_ROOT, "studies", "regression", "run_regression.jl"))
include(joinpath(REPO_ROOT, "studies", "regression", "phase_b_config.jl"))

const AUDIT_CAP_POLICY = LOOKAHEAD_CAP_POLICY

function csv_escape(value)
    text = string(value)
    if occursin('"', text) || occursin(',', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function format_cap(cap)
    cap === nothing && return "nothing"
    return string(cap)
end

function classify_cap(cap, required_stage::Int)
    cap === nothing && return "uncapped"
    cap < required_stage && return "truncated"
    return "ok"
end

function equation_required_stages(dim::Int, support)
    support === nothing && error("Cannot derive equation stages for surrogate support")
    basis = default_staged_polynomial_basis(dim)
    stages = Int[]
    for eq_support in support
        isempty(eq_support) && error("Cannot derive required stage from empty equation support")
        push!(stages, maximum(stage_for_term_idx.(Ref(basis), eq_support)))
    end
    return stages
end

function self_integrated_trajectory(system, ic_set::Int)
    dim = Int(system[:dim])
    u0 = Float64[x for x in system[:init_sets][ic_set]]
    length(u0) == dim || error("System $(system[:system_id]) IC$(ic_set) dimension mismatch")
    t_grid = collect(range(0.0, 10.0; length = 512))
    prob = ODEProblem(system[:rhs!], copy(u0), (0.0, 10.0), nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    sol.retcode == ReturnCode.Success ||
        error("Self-integration failed for system $(system[:system_id]), IC$(ic_set): $(sol.retcode)")
    return Trajectory(t_grid, Array(sol)')
end

function exact_phase_b_systems()
    systems = [system for system in PHASE_B_SYSTEMS if String(system[:representability]) == "exact"]
    return sort(systems; by = system -> Int(system[:system_id]))
end

function audit_rows()
    rows = NamedTuple[]
    systems = exact_phase_b_systems()
    length(systems) == 20 || error("Expected 20 exact Phase-B systems, got $(length(systems))")

    for system in systems
        system_id = Int(system[:system_id])
        dim = Int(system[:dim])
        required_stages = equation_required_stages(dim, system[:expected_support])
        basis = default_staged_polynomial_basis(dim)
        for ic_set in PHASE_B_IC_SETS
            traj = self_integrated_trajectory(system, ic_set)
            for horizon in HORIZONS
                policy = LookAheadStageCapPolicy(; AUDIT_CAP_POLICY..., lookahead_horizon = horizon)
                caps = estimate_stage_caps(traj, basis; policy = policy)
                length(caps) == dim || error("Cap length mismatch for system $(system_id), IC$(ic_set)")
                for eq in 1:dim
                    cap = caps[eq]
                    required_stage = required_stages[eq]
                    push!(
                        rows,
                        (
                            system_id = system_id,
                            system_name = String(system[:system_name]),
                            ic_set = ic_set,
                            horizon = horizon,
                            equation_index = eq,
                            dim = dim,
                            required_stage = required_stage,
                            cap = format_cap(cap),
                            classification = classify_cap(cap, required_stage),
                            support_idxs = JSON3.write(system[:expected_support][eq]),
                            equations = JSON3.write(system[:equations]),
                            t_length = length(traj.t),
                            t_start = first(traj.t),
                            t_end = last(traj.t),
                            solver = "Tsit5",
                            abstol = 1e-9,
                            reltol = 1e-9,
                        ),
                    )
                end
            end
        end
    end
    return rows
end

function write_csv(path::String, rows)
    headers = [
        "system_id",
        "system_name",
        "ic_set",
        "horizon",
        "equation_index",
        "dim",
        "required_stage",
        "cap",
        "classification",
        "support_idxs",
        "equations",
        "t_length",
        "t_start",
        "t_end",
        "solver",
        "abstol",
        "reltol",
    ]
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(headers, ","))
        for row in rows
            println(io, join([csv_escape(getfield(row, Symbol(header))) for header in headers], ","))
        end
    end
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

function cap_key(row)
    return (row.system_id, row.ic_set, row.equation_index)
end

function cap_map(rows, horizon::Int)
    selected = [row for row in rows if row.horizon == horizon]
    return Dict(cap_key(row) => row.cap for row in selected)
end

function classification_crosstable(rows)
    classes = ["truncated", "ok", "uncapped"]
    return [
        [horizon, class, count(row -> row.horizon == horizon && row.classification == class, rows)]
        for horizon in HORIZONS for class in classes
    ]
end

function truncated_rows(rows; horizon = nothing)
    selected = [row for row in rows if row.classification == "truncated" && (horizon === nothing || row.horizon == horizon)]
    return sort(selected; by = row -> (row.horizon, row.system_id, row.ic_set, row.equation_index))
end

function truncated_system_count(rows, horizon::Int)
    return length(unique(row.system_id for row in truncated_rows(rows; horizon = horizon)))
end

function defect_systems_ok(rows, horizon::Int)
    for system_id in DEFECT_SYSTEM_IDS
        selected = [row for row in rows if row.horizon == horizon && row.system_id == system_id]
        isempty(selected) && return false
        any(row -> row.classification == "truncated", selected) && return false
    end
    return true
end

function stability_caps_unchanged(rows, horizon::Int)
    base = cap_map(rows, 2)
    current = cap_map(rows, horizon)
    for key in keys(base)
        system_id, _, _ = key
        if system_id in STABILITY_SYSTEM_IDS && current[key] != base[key]
            return false
        end
    end
    return true
end

function selected_horizon(rows)
    for horizon in HORIZONS
        horizon == 2 && continue
        if defect_systems_ok(rows, horizon) && stability_caps_unchanged(rows, horizon)
            return horizon
        end
    end
    return nothing
end

function finite_uncapped_transitions(rows)
    base = cap_map(rows, 2)
    out = []
    for horizon in HORIZONS
        horizon == 2 && continue
        current = cap_map(rows, horizon)
        for key in sort(collect(keys(base)))
            before = base[key]
            after = current[key]
            before_uncapped = before == "nothing"
            after_uncapped = after == "nothing"
            if before_uncapped != after_uncapped
                system_id, ic_set, eq = key
                push!(out, [horizon, system_id, ic_set, eq, before, after])
            end
        end
    end
    return out
end

function cap_change_rows(rows, system_ids::Vector{Int}, horizon::Int)
    base = cap_map(rows, 2)
    current = cap_map(rows, horizon)
    out = []
    for key in sort(collect(keys(base)))
        system_id, ic_set, eq = key
        system_id in system_ids || continue
        before = base[key]
        after = current[key]
        before == after || push!(out, [system_id, ic_set, eq, before, after])
    end
    return out
end

function write_report(path::String, rows, csv_path::String)
    exact_system_ids = sort(unique(row.system_id for row in rows))
    selected = selected_horizon(rows)
    transitions = finite_uncapped_transitions(rows)
    h2_truncated = truncated_rows(rows; horizon = 2)
    h2_truncated_systems = truncated_system_count(rows, 2)
    h3_caps = cap_map(rows, 3)
    h5_caps = cap_map(rows, 5)
    h3_h5_mismatches = []
    for key in sort(collect(keys(h3_caps)))
        if h3_caps[key] != h5_caps[key]
            system_id, ic_set, eq = key
            push!(h3_h5_mismatches, [system_id, ic_set, eq, h3_caps[key], h5_caps[key]])
        end
    end

    lines = String[
        "# WP-C2 Stage-Cap Horizon Audit",
        "",
        "Generated by `studies/lookahead/audit_exact_stage_cap_horizons.jl` at $(Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")).",
        "",
        "Scope: $(length(exact_system_ids)) exact Phase-B systems, $(length(PHASE_B_IC_SETS)) initial-condition sets, $(length(HORIZONS)) horizons, and $(length(rows)) equation-level rows.",
        "",
        "Trajectories were self-integrated on 512 uniform points over `t in [0, 10]` with `Tsit5`, `abstol = reltol = 1e-9`; shipped dataset trajectories were not used for cap estimation.",
        "",
        "Required equation stages were derived from `phase_b_support.json` support indexes via `stage_for_term_idx` and `default_staged_polynomial_basis(dim).term_groups`.",
        "",
        "## Horizon x Classification",
        "",
        markdown_table(["horizon", "classification", "equations"], classification_crosstable(rows)),
        "",
        "## Truncated Cases",
        "",
    ]

    all_truncated = truncated_rows(rows)
    if isempty(all_truncated)
        push!(lines, "No truncated equation-level cases were measured.")
    else
        push!(
            lines,
            markdown_table(
                ["horizon", "system", "ic_set", "equation", "required_stage", "cap"],
                [[row.horizon, row.system_id, row.ic_set, row.equation_index, row.required_stage, row.cap] for row in all_truncated],
            ),
        )
    end

    push!(
        lines,
        "",
        "## Decision",
        "",
        "1. At `horizon = 2`, $(h2_truncated_systems) exact systems are truncated. Equation-level truncated rows: $(length(h2_truncated)).",
        "2. A horizon that moves systems 28 and 32 to `ok` while leaving systems 26, 27, 29, 31, and 54 cap-identical to `horizon = 2`: `$(selected === nothing ? "no" : "yes, horizon = $(selected)")`.",
    )

    for horizon in HORIZONS
        horizon == 2 && continue
        defect_ok = defect_systems_ok(rows, horizon)
        stable_same = stability_caps_unchanged(rows, horizon)
        changes = cap_change_rows(rows, STABILITY_SYSTEM_IDS, horizon)
        push!(
            lines,
            "   Horizon $(horizon): systems 28/32 ok=`$(defect_ok)`, stability systems cap-identical=`$(stable_same)`, stability cap changes=$(length(changes)).",
        )
    end

    push!(lines, "3. Finite/nothing transitions relative to `horizon = 2`: $(length(transitions)).")
    if !isempty(transitions)
        push!(lines, "")
        push!(lines, markdown_table(["horizon", "system", "ic_set", "equation", "horizon_2_cap", "new_cap"], transitions))
    end

    push!(
        lines,
        "",
        "4. Horizon 5 is row-wise cap-identical to horizon 3 across $(length(h3_caps)) `(system, ic_set, equation)` keys: `$(isempty(h3_h5_mismatches))`.",
    )
    if !isempty(h3_h5_mismatches)
        push!(lines, "")
        push!(lines, markdown_table(["system", "ic_set", "equation", "horizon_3_cap", "horizon_5_cap"], h3_h5_mismatches))
    end

    if selected === nothing
        push!(
            lines,
            "",
            "Part 3 was not executed because no tested horizon satisfied both requirements.",
        )
    elseif AUDIT_CAP_POLICY.lookahead_horizon == 5
        push!(
            lines,
            "",
            "WP-C2 default update was executed: the default look-ahead horizon is now `$(AUDIT_CAP_POLICY.lookahead_horizon)` in `LookAheadStageCapPolicy`, `LOOKAHEAD_CAP_POLICY`, and `LOOKAHEAD_CAP_POLICY_REGRESSION`.",
            "",
            "## Fingerprints",
            "",
            markdown_table(
                ["fingerprint", "old", "new"],
                [
                    ["Regression", "`$(OLD_CONFIG_FINGERPRINT)`", "`$(config_fingerprint())`"],
                    ["Phase B", "`$(OLD_PHASE_B_FINGERPRINT)`", "`$(phase_b_fingerprint())`"],
                ],
            ),
        )
    else
        push!(
            lines,
            "",
            "Part 3 criterion is satisfied by `horizon = $(selected)`. Defaults still need to be updated and fingerprints recorded.",
        )
    end

    push!(
        lines,
        "",
        "## Outputs",
        "",
        "- CSV: `$(relpath(csv_path, REPO_ROOT))`",
    )

    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(lines, "\n"))
    end
end

function main()
    rows = audit_rows()
    write_csv(CSV_PATH, rows)
    write_report(REPORT_PATH, rows, CSV_PATH)
    println("Wrote $(CSV_PATH)")
    println("Wrote $(REPORT_PATH)")
    println("Rows: $(length(rows))")
    println("Truncated systems at horizon=2: $(truncated_system_count(rows, 2))")
    selected = selected_horizon(rows)
    println("Selected horizon: $(selected === nothing ? "none" : string(selected))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
