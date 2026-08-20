import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using JSON3
using Printf

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
include(joinpath(REPO_ROOT, "studies", "output_path_guard.jl"))
include(joinpath(REPO_ROOT, "studies", "lookahead", "wp_v1_stage_cap_reliability.jl"))

const SCRIPT_SLUG = "wp_c5_stage_cap_binary_audit"
const OUTPUT_DIR = study_resolve_output_dir(joinpath(REPO_ROOT, "outputs", "studies", "lookahead", SCRIPT_SLUG), ARGS)
const ROW_CSV_PATH_C5 = joinpath(OUTPUT_DIR, "row_decisions.csv")
const SUMMARY_JSON_PATH_C5 = joinpath(OUTPUT_DIR, "summary.json")
const REPORT_PATH_C5 = study_resolve_output_path(joinpath(REPO_ROOT, "docs", "WP-C5.md"), ARGS; flag = "--report")
const BASELINE_ROW_CSV = joinpath(REPO_ROOT, "outputs", "studies", "lookahead", "wp_v1_stage_cap_reliability", "row_decisions.csv")

const OLD_FINGERPRINTS = (
    config = "1d0ccf8d53c6576d",
    phase_b = "e361a2af49366670",
    stage_cap = "61b6548ef0014593",
)

function parse_csv_line(line::AbstractString)
    fields = String[]
    buf = IOBuffer()
    quoted = false
    i = firstindex(line)
    while i <= lastindex(line)
        c = line[i]
        if quoted
            if c == '"'
                j = nextind(line, i)
                if j <= lastindex(line) && line[j] == '"'
                    write(buf, '"')
                    i = j
                else
                    quoted = false
                end
            else
                write(buf, c)
            end
        elseif c == '"'
            quoted = true
        elseif c == ','
            push!(fields, String(take!(buf)))
        else
            write(buf, c)
        end
        i = nextind(line, i)
    end
    push!(fields, String(take!(buf)))
    return fields
end

function load_baseline_caps(path::String)
    isfile(path) || error("Missing baseline row CSV: $(path)")
    rows = readlines(path)
    headers = parse_csv_line(rows[1])
    index = Dict(header => i for (i, header) in enumerate(headers))
    out = Dict{Tuple{Int,Int,Int}, String}()
    for line in rows[2:end]
        isempty(strip(line)) && continue
        fields = parse_csv_line(line)
        key = (
            parse(Int, fields[index["system_id"]]),
            parse(Int, fields[index["ic_set"]]),
            parse(Int, fields[index["equation_index"]]),
        )
        out[key] = fields[index["current_cap"]]
    end
    return out
end

function derive_current_rows(cases, policy::LookAheadStageCapPolicy, baseline_caps)
    rows = NamedTuple[]
    for case in cases
        current = decisions_from_states(case.states, policy; binary = false)
        cap_text = format_cap(current.cap)
        key = (case.system_id, case.ic_set, case.equation_index)
        before = baseline_caps[key]
        branch_trace = replace(current.branches, "floor_doubt_band" => "floor_without_prior_gain")
        trigger_trace = replace(current.triggers, "band post-floor" => "binary post-floor")
        push!(
            rows,
            (
                system_id = case.system_id,
                system_name = case.system_name,
                ic_set = case.ic_set,
                equation_index = case.equation_index,
                dim = case.dim,
                required_stage = case.required_stage,
                baseline_cap = before,
                current_cap = cap_text,
                changed = before != cap_text,
                class = row_class(current.cap, case.required_stage),
                branch_trace = branch_trace,
                trigger_trace = trigger_trace,
            ),
        )
    end
    return rows
end

finite_count(rows, field::Symbol) = count(row -> getfield(row, field) != "nothing", rows)
truncated_count(rows) = count(row -> row.class == "wrong_commit", rows)

function target_rows(rows)
    wanted = Dict(
        (12, 1, 1) => "2",
        (31, 1, 1) => "3",
        (55, 2, 2) => "4",
        (31, 2, 1) => "nothing",
        (55, 1, 3) => "3",
        (55, 2, 3) => "3",
        (56, 1, 3) => "3",
        (56, 2, 3) => "3",
    )
    return [
        (
            system_id = key[1],
            ic_set = key[2],
            equation_index = key[3],
            expected = value,
            observed = only(row.current_cap for row in rows if (row.system_id, row.ic_set, row.equation_index) == key),
        )
        for (key, value) in sort(collect(wanted); by = item -> item[1])
    ]
end

function unchanged_violations(rows)
    allowed_changes = Set([(12, 1, 1), (31, 1, 1), (55, 2, 2)])
    return [
        row for row in rows
        if row.changed && !((row.system_id, row.ic_set, row.equation_index) in allowed_changes)
    ]
end

function write_current_csv(path::String, rows)
    headers = [
        "system_id", "system_name", "ic_set", "equation_index", "dim",
        "required_stage", "baseline_cap", "current_cap", "changed", "class",
        "branch_trace", "trigger_trace",
    ]
    write_csv(path, headers, rows)
end

function write_report_c5(path::String, rows, fingerprints, csv_path::String, summary_path::String)
    targets = target_rows(rows)
    violations = unchanged_violations(rows)
    changed_rows = [row for row in rows if row.changed]
    truncated = [row for row in rows if row.class == "wrong_commit"]
    target_ok = all(row -> row.expected == row.observed, targets)
    finite_before = finite_count(rows, :baseline_cap)
    finite_after = finite_count(rows, :current_cap)
    no_truncation = isempty(truncated)

    lines = String[
        "# WP-C5 Stage-Cap Binary Post-Floor Audit",
        "",
        "Generated by `studies/lookahead/wp_c5_stage_cap_binary_audit.jl` at $(Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")).",
        "",
        "Scope: 20 exact Phase-B systems, 2 initial-condition sets, $(length(rows)) equation-level rows.",
        "",
        "## Policy Fields",
        "",
        "- Removed `post_floor_clear_no_drop_ratio`; there is no longer a second band boundary.",
        "- Renamed the surviving clear-drop boundary to `post_floor_significant_drop_ratio = $(LOOKAHEAD_CAP_POLICY.post_floor_significant_drop_ratio)` and kept it configurable in `LOOKAHEAD_CAP_POLICY`.",
        "- Kept `post_floor_min_floor_ratio = $(LOOKAHEAD_CAP_POLICY.post_floor_min_floor_ratio)` with the same value; it gates numerically tiny floor hits and is not a third post-floor outcome.",
        "",
        "## Fingerprints",
        "",
        markdown_table(
            ["fingerprint", "old", "new", "changed"],
            [
                ["config_fingerprint()", "`$(OLD_FINGERPRINTS.config)`", "`$(fingerprints.config)`", OLD_FINGERPRINTS.config != fingerprints.config],
                ["phase_b_fingerprint()", "`$(OLD_FINGERPRINTS.phase_b)`", "`$(fingerprints.phase_b)`", OLD_FINGERPRINTS.phase_b != fingerprints.phase_b],
                ["stage_cap_behavior_fingerprint()", "`$(OLD_FINGERPRINTS.stage_cap)`", "`$(fingerprints.stage_cap)`", OLD_FINGERPRINTS.stage_cap != fingerprints.stage_cap],
            ],
        ),
        "",
        "## Counts",
        "",
        markdown_table(
            ["metric", "value"],
            [
                ["baseline finite caps", finite_before],
                ["current finite caps", finite_after],
                ["truncated current rows", length(truncated)],
                ["changed rows", length(changed_rows)],
                ["unchanged-violation rows", length(violations)],
            ],
        ),
        "",
        "## Target Rows",
        "",
        markdown_table(
            ["system", "ic_set", "equation", "expected", "observed", "match"],
            [[row.system_id, row.ic_set, row.equation_index, row.expected, row.observed, row.expected == row.observed] for row in targets],
        ),
        "",
        "## Changed Rows",
        "",
    ]

    if isempty(changed_rows)
        push!(lines, "No row-level cap changes were observed.")
    else
        push!(
            lines,
            markdown_table(
                ["system", "ic_set", "equation", "required_stage", "before", "after", "class"],
                [[row.system_id, row.ic_set, row.equation_index, row.required_stage, row.baseline_cap, row.current_cap, row.class] for row in changed_rows],
            ),
        )
    end

    push!(lines, "", "## Unchanged Violations", "")
    if isempty(violations)
        push!(lines, "No non-target row changed.")
    else
        push!(
            lines,
            markdown_table(
                ["system", "ic_set", "equation", "before", "after"],
                [[row.system_id, row.ic_set, row.equation_index, row.baseline_cap, row.current_cap] for row in violations],
            ),
        )
    end

    push!(lines, "", "## Truncated Rows", "")
    if isempty(truncated)
        push!(lines, "No current row is truncated.")
    else
        push!(
            lines,
            markdown_table(
                ["system", "ic_set", "equation", "required_stage", "cap"],
                [[row.system_id, row.ic_set, row.equation_index, row.required_stage, row.current_cap] for row in truncated],
            ),
        )
    end

    append!(
        lines,
        [
            "",
            "## Acceptance",
            "",
            "- Target rows match: `$(target_ok)`.",
            "- Finite caps moved from 45 to 48: `$(finite_before == 45 && finite_after == 48)`.",
            "- No truncated rows: `$(no_truncation)`.",
            "- All non-target rows unchanged: `$(isempty(violations))`.",
            "",
            "## Outputs",
            "",
            "- Row CSV: `$(relpath(csv_path, REPO_ROOT))`",
            "- Summary JSON: `$(relpath(summary_path, REPO_ROOT))`",
        ],
    )

    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(lines, "\n"))
    end
end

function main()
    fingerprints = (
        config = config_fingerprint(),
        phase_b = phase_b_fingerprint(),
        stage_cap = stage_cap_behavior_fingerprint(),
    )
    baseline_caps = load_baseline_caps(BASELINE_ROW_CSV)
    cases = collect_cases(DEFAULT_POLICY)
    rows = derive_current_rows(cases, DEFAULT_POLICY, baseline_caps)
    write_current_csv(ROW_CSV_PATH_C5, rows)
    summary = Dict(
        "fingerprints" => Dict("config" => fingerprints.config, "phase_b" => fingerprints.phase_b, "stage_cap" => fingerprints.stage_cap),
        "baseline_finite_caps" => finite_count(rows, :baseline_cap),
        "current_finite_caps" => finite_count(rows, :current_cap),
        "truncated_current_rows" => truncated_count(rows),
        "changed_rows" => count(row -> row.changed, rows),
        "unchanged_violations" => length(unchanged_violations(rows)),
        "target_rows" => target_rows(rows),
    )
    open(SUMMARY_JSON_PATH_C5, "w") do io
        JSON3.pretty(io, summary)
    end
    write_report_c5(REPORT_PATH_C5, rows, fingerprints, ROW_CSV_PATH_C5, SUMMARY_JSON_PATH_C5)
    println("Wrote $(ROW_CSV_PATH_C5)")
    println("Wrote $(SUMMARY_JSON_PATH_C5)")
    println("Wrote $(REPORT_PATH_C5)")
    println("Rows: $(length(rows))")
    println("Finite caps: $(finite_count(rows, :baseline_cap)) -> $(finite_count(rows, :current_cap))")
    println("Truncated current rows: $(truncated_count(rows))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
