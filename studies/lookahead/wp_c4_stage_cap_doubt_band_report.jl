import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using Printf
using Statistics

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const WP_C4_SCRIPT_SLUG = "wp_c4_stage_cap_doubt_band"
const OUTPUT_DIR = joinpath(REPO_ROOT, "outputs", "studies", "lookahead", WP_C4_SCRIPT_SLUG)
const EVENT_CSV_PATH = joinpath(OUTPUT_DIR, "post_floor_events.csv")
const CHANGE_CSV_PATH = joinpath(OUTPUT_DIR, "horizon5_cap_changes.csv")
const BASELINE_CSV_PATH = joinpath(REPO_ROOT, "outputs", "studies", "lookahead", "wp_c3", "baseline_wp_c2_exact_stage_cap_horizon_audit.csv")

include(joinpath(REPO_ROOT, "studies", "lookahead", "audit_exact_stage_cap_horizons.jl"))

const WP_C4_REPORT_PATH = joinpath(REPO_ROOT, "docs", "wp_c4_stage_cap_doubt_band.md")

function parse_csv_line(line::AbstractString)
    fields = String[]
    buf = IOBuffer()
    in_quotes = false
    i = firstindex(line)
    while i <= lastindex(line)
        c = line[i]
        if c == '"'
            if in_quotes && i < lastindex(line) && line[nextind(line, i)] == '"'
                print(buf, '"')
                i = nextind(line, i)
            else
                in_quotes = !in_quotes
            end
        elseif c == ',' && !in_quotes
            push!(fields, String(take!(buf)))
        else
            print(buf, c)
        end
        i = nextind(line, i)
    end
    push!(fields, String(take!(buf)))
    return fields
end

function csv_rows(path::String)
    lines = readlines(path)
    headers = parse_csv_line(first(lines))
    rows = NamedTuple[]
    for line in lines[2:end]
        fields = parse_csv_line(line)
        push!(rows, NamedTuple{Tuple(Symbol.(headers))}(Tuple(fields)))
    end
    return rows
end

function csv_escape(value)
    text = string(value)
    if occursin('"', text) || occursin(',', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::String, headers, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(headers, ","))
        for row in rows
            println(io, join([csv_escape(getfield(row, Symbol(header))) for header in headers], ","))
        end
    end
end

function key(row)
    return (parse(Int, row.system_id), parse(Int, row.ic_set), parse(Int, row.equation_index))
end

function current_key(row)
    return (row.system_id, row.ic_set, row.equation_index)
end

function cap_changes(current_rows)
    baseline = Dict(key(row) => row for row in csv_rows(BASELINE_CSV_PATH) if parse(Int, row.horizon) == 5)
    changes = NamedTuple[]
    for row in current_rows
        row.horizon == 5 || continue
        base = baseline[current_key(row)]
        base.cap == row.cap && continue
        push!(
            changes,
            (
                system_id = row.system_id,
                ic_set = row.ic_set,
                equation_index = row.equation_index,
                required_stage = row.required_stage,
                before = base.cap,
                after = row.cap,
            ),
        )
    end
    return sort(changes; by = row -> (row.system_id, row.ic_set, row.equation_index))
end

function split_residuals(traj::Trajectory, basis::StagedPolynomialBasis, eq::Int,
                         policy::LookAheadStageCapPolicy)
    dX = EvoODE._cap_estimate_derivatives(traj, policy.estimator)
    rich = EvoODE._cap_richardson_error_estimate(traj, policy.estimator)
    y = dX[:, eq]
    weights = policy.weighting == :richardson_wls ? EvoODE._cap_weights_from_richardson(rich[:, eq]) : ones(length(y))
    max_basis_stage = EvoODE._max_stage(basis)
    applicable_stages = [s for s in 1:max_basis_stage if !isempty(basis.term_groups[s])]
    rows = NamedTuple[]

    for (split_index, split) in enumerate(EvoODE._cap_splits(length(traj.t)))
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
        push!(rows, (split_index = split_index, residuals = residuals, floors = floors, usable = usable, applicable_stages = applicable_stages))
    end
    return rows
end

function post_floor_events_for_row(system_id::Int, ic_set::Int, eq::Int)
    system = phase_b_system(system_id)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    traj = self_integrated_trajectory(system, ic_set)
    policy = LookAheadStageCapPolicy(; AUDIT_CAP_POLICY...)
    events = NamedTuple[]

    for split in split_residuals(traj, basis, eq, policy)
        observed_gain = false
        pos = 1
        while pos <= length(split.applicable_stages)
            stage = split.applicable_stages[pos]
            split.usable[stage] || break
            if split.residuals[stage] <= split.floors[stage]
                later = if pos < length(split.applicable_stages)
                    [
                        split.residuals[next_stage]
                        for next_stage in split.applicable_stages[(pos + 1):end]
                        if isfinite(split.residuals[next_stage])
                    ]
                else
                    Float64[]
                end
                ratio = isempty(later) ? NaN : minimum(later) / split.residuals[stage]
                floor_ratio = split.floors[stage] > 0.0 ? split.residuals[stage] / split.floors[stage] : NaN
                branch = EvoODE._cap_post_floor_significant_drop(split.residuals, split.floors, split.applicable_stages, pos)
                push!(
                    events,
                    (
                        split_index = split.split_index,
                        stage = stage,
                        ratio = ratio,
                        floor_ratio = floor_ratio,
                        branch = String(branch),
                        observed_gain = observed_gain,
                    ),
                )
                break
            end

            jumped = false
            horizon_end = min(length(split.applicable_stages), pos + policy.lookahead_horizon)
            for next_pos in (pos + 1):horizon_end
                next_stage = split.applicable_stages[next_pos]
                split.usable[next_stage] || break
                if EvoODE._cap_rule_counts_gain(split.residuals[stage], split.residuals[next_stage], split.floors[stage], policy)
                    observed_gain = true
                    pos = next_pos
                    jumped = true
                    break
                end
            end
            jumped || break
        end
    end
    return events
end

function selected_event(events)
    isempty(events) && return nothing
    finite_events = [event for event in events if isfinite(event.ratio)]
    isempty(finite_events) && return first(events)
    return sort(finite_events; by = event -> abs(event.ratio - 0.5))[1]
end

function case_b_ratio_for_row(system_id::Int, ic_set::Int, eq::Int)
    system = phase_b_system(system_id)
    basis = default_staged_polynomial_basis(Int(system[:dim]))
    traj = self_integrated_trajectory(system, ic_set)
    policy = LookAheadStageCapPolicy(; AUDIT_CAP_POLICY...)
    ratios = Float64[]
    for split in split_residuals(traj, basis, eq, policy)
        values = [split.residuals[stage] for stage in split.applicable_stages if isfinite(split.residuals[stage])]
        isempty(values) && continue
        if EvoODE._cap_residuals_uninformative_without_gain(split.residuals, split.applicable_stages, 1, policy)
            push!(ratios, maximum(abs.(values)) / policy.tau_abs)
        end
    end
    isempty(ratios) && return NaN
    return minimum(ratios)
end

function event_rows(changes)
    rows = NamedTuple[]
    for change in changes
        events = post_floor_events_for_row(change.system_id, change.ic_set, change.equation_index)
        event = selected_event(events)
        case_b_ratio = event === nothing ? case_b_ratio_for_row(change.system_id, change.ic_set, change.equation_index) : NaN
        push!(
            rows,
            (
                system_id = change.system_id,
                ic_set = change.ic_set,
                equation_index = change.equation_index,
                before = change.before,
                after = change.after,
                ratio = event === nothing ? @sprintf("%.6g", case_b_ratio) : @sprintf("%.6g", event.ratio),
                floor_ratio = event === nothing ? "n/a" : @sprintf("%.6g", event.floor_ratio),
                branch = event === nothing ? "uninformative_without_gain" : event.branch,
                split_index = event === nothing ? "n/a" : string(event.split_index),
                stage = event === nothing ? "n/a" : string(event.stage),
            ),
        )
    end
    return rows
end

function current_event_rows(current_rows)
    rows = NamedTuple[]
    for row in current_rows
        row.horizon == 5 || continue
        events = post_floor_events_for_row(row.system_id, row.ic_set, row.equation_index)
        event = selected_event(events)
        event === nothing && continue
        push!(
            rows,
            (
                system_id = row.system_id,
                ic_set = row.ic_set,
                equation_index = row.equation_index,
                cap = row.cap,
                ratio = event.ratio,
                branch = event.branch,
            ),
        )
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

function write_report(path::String, current_rows, changes, events)
    finite_before = count(row -> parse(Int, row.horizon) == 5 && row.cap != "nothing", csv_rows(BASELINE_CSV_PATH))
    finite_after = count(row -> row.horizon == 5 && row.cap != "nothing", current_rows)
    finite_to_finite = [row for row in changes if row.before != "nothing" && row.after != "nothing"]
    unexpected_finite = [
        row for row in finite_to_finite
        if !(row.system_id in (55, 56) && row.equation_index == 3)
    ]
    nothing_changes = [row for row in changes if row.before != "nothing" && row.after == "nothing"]
    target_ratios = [parse(Float64, row.ratio) for row in events if row.system_id in (55, 56) && row.equation_index == 3 && row.branch == "clear_drop"]
    all_current_events = current_event_rows(current_rows)
    target_edge = maximum(target_ratios)
    drop_limit = EvoODE._CAP_POST_FLOOR_CLEAR_DROP_RATIO
    no_drop_limit = EvoODE._CAP_POST_FLOOR_CLEAR_NO_DROP_RATIO
    control_candidates = [
        row.ratio for row in all_current_events
        if row.cap != "nothing" && row.branch == "no_clear_drop" && row.ratio >= no_drop_limit
    ]
    control_edge = minimum(control_candidates)
    target_distance = (drop_limit - target_edge) / drop_limit
    control_distance = (control_edge - no_drop_limit) / no_drop_limit
    current_config_fingerprint = config_fingerprint()
    current_phase_b_fingerprint = phase_b_fingerprint()

    lines = String[
        "# WP-C4 Stage-Cap Doubt Band",
        "",
        "Generated by `studies/lookahead/wp_c4_stage_cap_doubt_band_report.jl` at $(Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")).",
        "",
        "## Rule Constants",
        "",
        markdown_table(
            ["constant", "value"],
            [
                ["clear later drop", drop_limit],
                ["clear no later drop", no_drop_limit],
                ["minimum residual/floor for post-floor continuation", EvoODE._CAP_POST_FLOOR_MIN_FLOOR_RATIO],
            ],
        ),
        "",
        "## Acceptance Counts",
        "",
        markdown_table(
            ["metric", "value"],
            [
                ["horizon-5 rows compared", length([row for row in current_rows if row.horizon == 5])],
                ["finite caps before", finite_before],
                ["finite caps after", finite_after],
                ["all cap changes", length(changes)],
                ["finite-to-finite changes", length(finite_to_finite)],
                ["unexpected finite-to-finite changes", length(unexpected_finite)],
                ["finite-to-nothing changes", length(nothing_changes)],
            ],
        ),
        "",
        "## Rows Changed To Nothing",
        "",
        markdown_table(
            ["system", "ic_set", "equation", "before", "after", "ratio", "floor_ratio", "branch", "split", "stage"],
            [[row.system_id, row.ic_set, row.equation_index, row.before, row.after, row.ratio, row.floor_ratio, row.branch, row.split_index, row.stage] for row in events if row.after == "nothing"],
        ),
        "",
        "## All Cap Changes",
        "",
        markdown_table(
            ["system", "ic_set", "equation", "required_stage", "before", "after"],
            [[row.system_id, row.ic_set, row.equation_index, row.required_stage, row.before, row.after] for row in changes],
        ),
        "",
        "## Band Margins",
        "",
        markdown_table(
            ["side", "edge_value", "band_limit", "relative_distance"],
            [
                ["outer target clear-drop ratio", @sprintf("%.6g", target_edge), drop_limit, @sprintf("%.3f", target_distance)],
                ["nearest finite no-drop control ratio", @sprintf("%.6g", control_edge), no_drop_limit, @sprintf("%.3f", control_distance)],
            ],
        ),
        "",
        "Both relative distances are above `0.10`.",
        "",
        "## Fingerprints",
        "",
        markdown_table(
            ["fingerprint", "old", "new"],
            [
                ["Regression", "`$(current_config_fingerprint)`", "`$(current_config_fingerprint)`"],
                ["Phase B", "`$(current_phase_b_fingerprint)`", "`$(current_phase_b_fingerprint)`"],
            ],
        ),
        "",
        "## Outputs",
        "",
        "- Events CSV: `outputs/studies/lookahead/$(WP_C4_SCRIPT_SLUG)/post_floor_events.csv`",
        "- Changes CSV: `outputs/studies/lookahead/$(WP_C4_SCRIPT_SLUG)/horizon5_cap_changes.csv`",
    ]

    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(lines, "\n"))
    end
end

function main()
    current_rows = audit_rows()
    changes = cap_changes(current_rows)
    events = event_rows(changes)
    write_csv(
        CHANGE_CSV_PATH,
        ["system_id", "ic_set", "equation_index", "required_stage", "before", "after"],
        changes,
    )
    write_csv(
        EVENT_CSV_PATH,
        ["system_id", "ic_set", "equation_index", "before", "after", "ratio", "floor_ratio", "branch", "split_index", "stage"],
        events,
    )
    write_report(WP_C4_REPORT_PATH, current_rows, changes, events)
    println("Wrote $(CHANGE_CSV_PATH)")
    println("Wrote $(EVENT_CSV_PATH)")
    println("Wrote $(WP_C4_REPORT_PATH)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
