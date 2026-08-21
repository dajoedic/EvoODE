import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using JSON3
using Printf
using Statistics

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const OUTPUT_DIR = joinpath(REPO_ROOT, "outputs", "studies", "regression", "wp_b1_wasted_levels")
const REPORT_PATH = joinpath(REPO_ROOT, "docs", "WP-B1.md")
const SYSTEM_DATA_PATH = joinpath(REPO_ROOT, "benchmarks", "data", "strogatz_extended.json")
const SUPPORT_PATH = joinpath(REPO_ROOT, "studies", "regression", "phase_b_support.json")
const SHARE_ROOT = raw"S:\BigDataOrion\data-science\joedicke"
const EPS_SENTINEL = 1e6
const PROMILLE = 1e-3
const K_VALUES = (3, 5, 8)

const SOURCES = [
    (label = "pilot_sweep_tasks", root = joinpath(SHARE_ROOT, "pilot_sweep_tasks"), kind = "pilot"),
    (label = "pilot_sweep3_tasks", root = joinpath(SHARE_ROOT, "pilot_sweep3_tasks"), kind = "pilot"),
    (label = "pilot_e20af80", root = joinpath(SHARE_ROOT, "pilot_e20af80"), kind = "pilot"),
    (
        label = "pretune_off_probe",
        root = joinpath(SHARE_ROOT, "campaign_88eaeb6fd6c4d9a1832baeb4b28033752ddb370d", "tasks_pretune_off_probe"),
        kind = "pretune_off_probe",
    ),
    (
        label = "regression_88eaeb6f",
        root = joinpath(SHARE_ROOT, "regression_88eaeb6fd6c4d9a1832baeb4b28033752ddb370d", "tasks"),
        kind = "regression",
    ),
    (
        label = "regression2_f6143eb",
        root = joinpath(SHARE_ROOT, "regression2_f6143eb49d5b72784f85cde07f032895ee516d08", "tasks"),
        kind = "regression",
    ),
]

struct LevelEvent
    level::Int
    stage::Union{Missing, Int}
    best_loss::Float64
    timestamp::DateTime
end

function parse_timestamp(text::AbstractString)
    s = replace(String(text), r"Z$" => "")
    if occursin('.', s)
        head, frac = split(s, '.', limit = 2)
        frac = rpad(frac[1:min(end, 3)], 3, '0')
        return DateTime(head * "." * frac, dateformat"yyyy-mm-ddTHH:MM:SS.sss")
    end
    return DateTime(s, dateformat"yyyy-mm-ddTHH:MM:SS")
end

function read_json_line(path::AbstractString)
    return open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            return JSON3.read(line)
        end
        return nothing
    end
end

function json_has(obj, key::Symbol)
    obj === nothing && return false
    try
        getproperty(obj, key)
        return true
    catch
    end
    for candidate in (key, String(key))
        try
            haskey(obj, candidate) && return true
        catch
        end
    end
    return false
end

function json_get(obj, key::Symbol, default = nothing)
    obj === nothing && return default
    try
        return getproperty(obj, key)
    catch
    end
    for candidate in (key, String(key))
        try
            haskey(obj, candidate) && return obj[candidate]
        catch
        end
    end
    return default
end

function read_heartbeat(path::AbstractString)
    levels = LevelEvent[]
    start_time = missing
    first_level_row = nothing
    malformed = 0
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            try
                row = JSON3.read(line)
                haskey(row, :timestamp) || continue
                event = String(get(row, :event, ""))
                if event == "start"
                    start_time = parse_timestamp(String(row[:timestamp]))
                elseif event == "level"
                    first_level_row === nothing && (first_level_row = row)
                    stage = haskey(row, :stage) && row[:stage] !== nothing ? Int(row[:stage]) : missing
                    push!(levels, LevelEvent(Int(row[:level]), stage, Float64(row[:best_loss]), parse_timestamp(String(row[:timestamp]))))
                end
            catch
                malformed += 1
            end
        end
    end
    sort!(levels; by = x -> x.level)
    return start_time, levels, first_level_row, malformed
end

function load_system_maps()
    systems = JSON3.read(read(SYSTEM_DATA_PATH, String))
    dims = Dict{Int, Int}()
    names = Dict{Int, String}()
    for row in systems
        dims[Int(row[:id])] = Int(row[:dim])
        names[Int(row[:id])] = String(row[:eq_description])
    end
    support = JSON3.read(read(SUPPORT_PATH, String))
    repr = Dict{Int, String}()
    for row in support[:systems]
        repr[Int(row[:system_id])] = String(row[:representability])
    end
    return dims, names, repr
end

csv_escape(x) = x === missing ? "" : begin
    s = string(x)
    occursin(Regex("[,\"\n\r]"), s) ? "\"" * replace(s, "\"" => "\"\"") * "\"" : s
end

function write_csv(path::AbstractString, header, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(csv_escape.(header), ","))
        for row in rows
            println(io, join((csv_escape(get(row, col, missing)) for col in header), ","))
        end
    end
end

function finite_loss(record)
    record === nothing && return false
    json_has(record, :loss) || return false
    loss = json_get(record, :loss)
    nullish(loss) && return false
    value = Float64(loss)
    return isfinite(value) && value < EPS_SENTINEL
end

function bool_value(x)
    x === nothing && return false
    x === missing && return false
    x isa Bool && return x
    return lowercase(String(x)) == "true"
end

function nullish(x)
    x === nothing && return true
    x === missing && return true
    return occursin("JSON3.Null", string(typeof(x)))
end

function normalize_pretune(record, variant::String)
    if record !== nothing
        if json_has(record, :condition)
            c = String(json_get(record, :condition))
            c in ("pretune_on", "pretune_off") && return c
        end
        if json_has(record, :use_pretuning)
            return bool_value(json_get(record, :use_pretuning)) ? "pretune_on" : "pretune_off"
        end
    end
    occursin("pretune_off", variant) && return "pretune_off"
    occursin("pretune_on", variant) && return "pretune_on"
    return "unknown"
end

function normalize_variant(record, heartbeat_first)
    for obj in (record, heartbeat_first)
        obj === nothing && continue
        json_has(obj, :variant) && return String(json_get(obj, :variant))
    end
    return "unknown"
end

function identity_from(record, first_level, source_label::String, heartbeat_path::String)
    objs = (record, first_level)
    manifest_index = missing
    system_id = missing
    ic_set = missing
    seed = missing
    for obj in objs
        obj === nothing && continue
        manifest_index === missing && json_has(obj, :manifest_index) && (manifest_index = Int(json_get(obj, :manifest_index)))
        system_id === missing && json_has(obj, :system_id) && (system_id = Int(json_get(obj, :system_id)))
        ic_set === missing && json_has(obj, :initial_condition_set) && (ic_set = Int(json_get(obj, :initial_condition_set)))
        seed === missing && json_has(obj, :seed) && (seed = Int(json_get(obj, :seed)))
    end
    cell_file = replace(basename(heartbeat_path), ".heartbeat.jsonl" => "")
    return manifest_index, system_id, ic_set, seed, "$(source_label):$(cell_file)"
end

function improvement_metrics(levels::Vector{LevelEvent})
    isempty(levels) && error("empty heartbeat")
    best = Inf
    last_improvement = first(levels).level
    last_promille = first(levels).level
    previous_best = Inf
    improvement_rows = Dict{String, Any}[]
    silent = 0
    max_pause_before_improvement = 0
    for ev in levels
        if ev.best_loss < best
            abs_drop = isfinite(previous_best) ? previous_best - ev.best_loss : missing
            rel_drop = isfinite(previous_best) && previous_best != 0.0 ? abs_drop / abs(previous_best) : missing
            if isfinite(previous_best)
                push!(
                    improvement_rows,
                    Dict(
                        "level" => ev.level,
                        "stage" => ev.stage,
                        "old_best_loss" => previous_best,
                        "new_best_loss" => ev.best_loss,
                        "abs_drop" => abs_drop,
                        "rel_drop" => rel_drop,
                        "silent_levels_before" => silent,
                        "timestamp" => ev.timestamp,
                    ),
                )
                max_pause_before_improvement = max(max_pause_before_improvement, silent)
            end
            if !isfinite(previous_best) || (previous_best != 0.0 && (previous_best - ev.best_loss) / abs(previous_best) >= PROMILLE)
                last_promille = ev.level
            end
            best = ev.best_loss
            previous_best = ev.best_loss
            last_improvement = ev.level
            silent = 0
        else
            silent += 1
        end
    end
    return last_improvement, last_promille, improvement_rows, max_pause_before_improvement
end

function duration_seconds(a::DateTime, b::DateTime)
    return Dates.value(b - a) / 1000.0
end

function level_time_at(levels, level)
    idx = findlast(ev -> ev.level <= level, levels)
    idx === nothing && return first(levels).timestamp
    return levels[idx].timestamp
end

function stop_metrics(levels, k::Int)
    best = Inf
    silent = 0
    abort_level = missing
    abort_time = missing
    missed = false
    missed_rows = Dict{String, Any}[]
    previous_best = Inf
    for ev in levels
        improved = ev.best_loss < best
        if abort_level !== missing && improved
            missed = true
            abs_drop = previous_best - ev.best_loss
            rel_drop = previous_best != 0.0 ? abs_drop / abs(previous_best) : missing
            push!(
                missed_rows,
                Dict(
                    "k" => k,
                    "level" => ev.level,
                    "stage" => ev.stage,
                    "old_best_loss" => previous_best,
                    "new_best_loss" => ev.best_loss,
                    "abs_drop" => abs_drop,
                    "rel_drop" => rel_drop,
                    "silent_levels_before" => silent,
                    "timestamp" => ev.timestamp,
                ),
            )
        end
        if improved
            best = ev.best_loss
            previous_best = ev.best_loss
            silent = 0
        else
            silent += 1
            if abort_level === missing && silent >= k
                abort_level = ev.level
                abort_time = ev.timestamp
            end
        end
    end
    if abort_level === missing
        abort_level = last(levels).level
        abort_time = last(levels).timestamp
    end
    saved_levels = last(levels).level - abort_level
    saved_time_s = duration_seconds(abort_time, last(levels).timestamp)
    return abort_level, saved_levels, saved_time_s, missed, missed_rows
end

function mean_or_missing(values)
    clean = [Float64(v) for v in values if v !== missing && isfinite(Float64(v))]
    isempty(clean) ? missing : mean(clean)
end

function summarize_group(rows, key)
    buckets = Dict{String, Vector{Dict{String, Any}}}()
    for row in rows
        label = string(get(row, key, "unknown"))
        push!(get!(buckets, label, Dict{String, Any}[]), row)
    end
    out = Dict{String, Any}[]
    for label in sort(collect(keys(buckets)))
        group = buckets[label]
        push!(
            out,
            Dict(
                "split" => String(key),
                "value" => label,
                "n_cells" => length(group),
                "mean_total_levels" => mean_or_missing(get.(group, "total_levels", missing)),
                "mean_silent_tail_levels" => mean_or_missing(get.(group, "silent_tail_levels", missing)),
                "mean_silent_tail_time_share" => mean_or_missing(get.(group, "silent_tail_time_share", missing)),
                "mean_small_change_tail_levels" => mean_or_missing(get.(group, "small_change_tail_levels", missing)),
                "usable_cells" => count(r -> get(r, "usable_solution", false) == true, group),
            ),
        )
    end
    return out
end

function collect_heartbeat_paths(source)
    if !isdir(source.root)
        return String[], "missing source directory"
    end
    paths = String[]
    for (root, _, files) in walkdir(source.root)
        for file in files
            endswith(file, ".heartbeat.jsonl") && push!(paths, joinpath(root, file))
        end
    end
    sort!(paths)
    return paths, ""
end

function analyze()
    mkpath(OUTPUT_DIR)
    dims, names, repr_map = load_system_maps()
    cell_rows = Dict{String, Any}[]
    late_rows = Dict{String, Any}[]
    source_rows = Dict{String, Any}[]
    savings_rows = Dict{String, Any}[]
    malformed_total = 0

    for source in SOURCES
        paths, note = collect_heartbeat_paths(source)
        source_row = Dict("source" => source.label, "path" => source.root, "heartbeat_files" => length(paths), "records_read" => 0, "records_missing" => 0, "note" => note, "record_error" => "")
        push!(source_rows, source_row)
        for hb_path in paths
            start_time, levels, first_level_row, malformed = read_heartbeat(hb_path)
            malformed_total += malformed
            isempty(levels) && continue
            record_path = replace(hb_path, ".heartbeat.jsonl" => ".jsonl")
            record = try
                read_json_line(record_path)
            catch err
                isempty(source_row["record_error"]) && (source_row["record_error"] = "$(typeof(err)): $(err)")
                nothing
            end
            if record === nothing
                source_row["records_missing"] += 1
            else
                source_row["records_read"] += 1
            end
            manifest_index, system_id, ic_set, seed, cell_key = identity_from(record, first_level_row, source.label, hb_path)
            variant = normalize_variant(record, first_level_row)
            pretune = normalize_pretune(record, variant)
            dim = system_id === missing ? missing : get(dims, system_id, missing)
            record_representability = json_get(record, :representability)
            representability = !nullish(record_representability) ?
                String(record_representability) :
                (system_id === missing ? "unknown" : get(repr_map, system_id, "unknown"))
            usable = finite_loss(record)
            if !nullish(json_get(record, :error))
                usable = false
            end
            last_improvement, last_promille, improvement_rows, max_pause = improvement_metrics(levels)
            total_levels = last(levels).level
            total_start = start_time === missing ? first(levels).timestamp : start_time
            total_time_s = max(0.0, duration_seconds(total_start, last(levels).timestamp))
            tail_start_time = level_time_at(levels, last_improvement)
            silent_time_s = max(0.0, duration_seconds(tail_start_time, last(levels).timestamp))
            time_share = total_time_s > 0 ? silent_time_s / total_time_s : missing
            small_tail_levels = total_levels - last_promille

            row = Dict(
                "source" => source.label,
                "kind" => source.kind,
                "cell_key" => cell_key,
                "manifest_index" => manifest_index,
                "system_id" => system_id,
                "system_name" => system_id === missing ? missing : get(names, system_id, missing),
                "dimension_class" => dim,
                "representability" => representability,
                "pretune" => pretune,
                "variant" => variant,
                "initial_condition_set" => ic_set,
                "seed" => seed,
                "usable_solution" => usable,
                "final_loss" => !nullish(json_get(record, :loss)) ? Float64(json_get(record, :loss)) : last(levels).best_loss,
                "last_improvement_level" => last_improvement,
                "total_levels" => total_levels,
                "silent_tail_levels" => total_levels - last_improvement,
                "silent_tail_time_s" => silent_time_s,
                "total_heartbeat_time_s" => total_time_s,
                "silent_tail_time_share" => time_share,
                "last_promille_improvement_level" => last_promille,
                "small_change_tail_levels" => small_tail_levels,
                "max_silent_pause_before_improvement" => max_pause,
                "heartbeat_path" => hb_path,
            )
            push!(cell_rows, row)

            for k in K_VALUES
                abort_level, saved_levels, saved_time_s, missed, missed_rows = stop_metrics(levels, k)
                push!(
                    savings_rows,
                    Dict(
                        "k" => k,
                        "cell_key" => cell_key,
                        "saved_levels" => saved_levels,
                        "saved_time_s" => saved_time_s,
                        "missed_improvement" => missed,
                        "abort_level" => abort_level,
                    ),
                )
                for miss in missed_rows
                    merged = copy(row)
                    for (mk, mv) in miss
                        merged[mk] = mv
                    end
                    push!(late_rows, merged)
                end
            end
        end
    end

    split_rows = Dict{String, Any}[]
    for key in ("dimension_class", "representability", "pretune", "variant", "usable_solution")
        append!(split_rows, summarize_group(cell_rows, key))
    end

    hypothetic_rows = Dict{String, Any}[]
    for k in K_VALUES
        rows = [r for r in savings_rows if r["k"] == k]
        push!(
            hypothetic_rows,
            Dict(
                "k" => k,
                "n_cells" => length(rows),
                "saved_levels" => sum(Int(r["saved_levels"]) for r in rows),
                "saved_time_s" => sum(Float64(r["saved_time_s"]) for r in rows),
                "missed_improvement_cells" => count(r -> r["missed_improvement"] == true, rows),
            ),
        )
    end

    write_csv(joinpath(OUTPUT_DIR, "cell_wasted_levels.csv"), [
        "source", "kind", "cell_key", "manifest_index", "system_id", "system_name", "dimension_class",
        "representability", "pretune", "variant", "initial_condition_set", "seed", "usable_solution",
        "final_loss", "last_improvement_level", "total_levels", "silent_tail_levels",
        "silent_tail_time_s", "total_heartbeat_time_s", "silent_tail_time_share",
        "last_promille_improvement_level", "small_change_tail_levels", "max_silent_pause_before_improvement",
        "heartbeat_path",
    ], cell_rows)
    write_csv(joinpath(OUTPUT_DIR, "breakdowns.csv"), [
        "split", "value", "n_cells", "mean_total_levels", "mean_silent_tail_levels",
        "mean_silent_tail_time_share", "mean_small_change_tail_levels", "usable_cells",
    ], split_rows)
    write_csv(joinpath(OUTPUT_DIR, "hypothetical_savings.csv"), [
        "k", "n_cells", "saved_levels", "saved_time_s", "missed_improvement_cells",
    ], hypothetic_rows)
    write_csv(joinpath(OUTPUT_DIR, "late_improvements.csv"), [
        "k", "source", "cell_key", "system_id", "system_name", "dimension_class", "representability",
        "pretune", "variant", "initial_condition_set", "seed", "level", "stage",
        "silent_levels_before", "old_best_loss", "new_best_loss", "abs_drop", "rel_drop",
    ], late_rows)
    write_csv(joinpath(OUTPUT_DIR, "sources.csv"), ["source", "path", "heartbeat_files", "records_read", "records_missing", "note", "record_error"], source_rows)

    return cell_rows, split_rows, hypothetic_rows, late_rows, source_rows, malformed_total
end

function fmt_float(x; digits = 4)
    x === missing && return ""
    x isa AbstractFloat || return string(x)
    isfinite(x) || return string(x)
    return @sprintf("%.*g", digits, x)
end

function write_markdown_table(io, header, rows; limit = nothing)
    println(io, "| ", join(header, " | "), " |")
    println(io, "|", join(fill("---", length(header)), "|"), "|")
    shown = limit === nothing ? rows : rows[1:min(end, limit)]
    for row in shown
        println(io, "| ", join((fmt_float(get(row, col, "")) for col in header), " | "), " |")
    end
    if limit !== nothing && length(rows) > limit
        println(io)
        println(io, "_Table truncated in report: $(length(rows) - limit) additional rows are in the CSV._")
    end
end

function write_report(cell_rows, split_rows, hypothetic_rows, late_rows, source_rows, malformed_total)
    open(REPORT_PATH, "w") do io
        println(io, "# WP-B1 - Wasted Search Levels")
        println(io)
        println(io, "Generated by `studies/regression/analyze_wasted_search_levels.jl` from heartbeat JSONL files only. No productive code, search loop, `n_levels`, fingerprint-relevant setting, cluster job, campaign, or Orion run was changed or started.")
        println(io)
        println(io, "Outputs:")
        println(io, "- `outputs/studies/regression/wp_b1_wasted_levels/cell_wasted_levels.csv`")
        println(io, "- `outputs/studies/regression/wp_b1_wasted_levels/breakdowns.csv`")
        println(io, "- `outputs/studies/regression/wp_b1_wasted_levels/hypothetical_savings.csv`")
        println(io, "- `outputs/studies/regression/wp_b1_wasted_levels/late_improvements.csv`")
        println(io, "- `outputs/studies/regression/wp_b1_wasted_levels/sources.csv`")
        println(io)
        println(io, "Definitions:")
        println(io, "- Improvement: strict decrease of `best_loss` at a level event.")
        println(io, "- Silent tail levels: `total_levels - last_improvement_level`.")
        println(io, "- Silent tail time share: time from the last improving level timestamp to the last level timestamp, divided by time from the start heartbeat timestamp to the last level timestamp.")
        println(io, "- Last promille improvement level: last level whose strict decrease was at least `0.001 * previous_best_loss`; `small_change_tail_levels` is `total_levels - last_promille_improvement_level`.")
        println(io, "- Usable solution: cell record has no error and a finite `loss < 1e6`, matching the existing MSE sentinel convention.")
        println(io)
        println(io, "## Source coverage")
        write_markdown_table(io, ["source", "heartbeat_files", "records_read", "records_missing", "note", "record_error", "path"], source_rows)
        println(io)
        println(io, "- Cells with heartbeat data analyzed: $(length(cell_rows))")
        println(io, "- Malformed heartbeat lines skipped: $(malformed_total)")
        println(io)
        println(io, "## Per-cell table")
        write_markdown_table(io, [
            "source", "manifest_index", "system_id", "dimension_class", "representability", "pretune",
            "variant", "initial_condition_set", "seed", "usable_solution", "final_loss",
            "last_improvement_level", "total_levels", "silent_tail_levels", "silent_tail_time_share",
            "last_promille_improvement_level", "small_change_tail_levels",
        ], cell_rows; limit = 80)
        println(io)
        println(io, "Full per-cell table has $(length(cell_rows)) rows in `cell_wasted_levels.csv`.")
        println(io)
        println(io, "## Breakdowns")
        write_markdown_table(io, [
            "split", "value", "n_cells", "mean_total_levels", "mean_silent_tail_levels",
            "mean_silent_tail_time_share", "mean_small_change_tail_levels", "usable_cells",
        ], split_rows)
        println(io)
        println(io, "## Hypothetical savings")
        write_markdown_table(io, ["k", "n_cells", "saved_levels", "saved_time_s", "missed_improvement_cells"], hypothetic_rows)
        println(io)
        println(io, "## Late improvements after more than k silent levels")
        if isempty(late_rows)
            println(io, "No strict improvement after an abort point for k = 3, 5, or 8 was found.")
        else
            write_markdown_table(io, [
                "k", "source", "manifest_index", "system_id", "dimension_class", "representability",
                "pretune", "variant", "initial_condition_set", "seed", "level", "stage",
                "silent_levels_before", "old_best_loss", "new_best_loss", "abs_drop", "rel_drop",
            ], late_rows; limit = 120)
            println(io)
            println(io, "Full late-improvement table has $(length(late_rows)) rows in `late_improvements.csv`.")
        end
    end
end

function main()
    cell_rows, split_rows, hypothetic_rows, late_rows, source_rows, malformed_total = analyze()
    write_report(cell_rows, split_rows, hypothetic_rows, late_rows, source_rows, malformed_total)
    println("cells=$(length(cell_rows))")
    println("late_improvement_rows=$(length(late_rows))")
    println("report=$(REPORT_PATH)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
