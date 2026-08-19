import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf

include(joinpath(@__DIR__, "..", "output_path_guard.jl"))

const BUDGET = 20_000
const INPUTS = [
    ("wp_f1", joinpath(@__DIR__, "..", "..", "outputs", "studies", "linesearch", "wp_f1", "fit_records.jsonl")),
    ("wp_f2", joinpath(@__DIR__, "..", "..", "outputs", "studies", "linesearch", "wp_f2", "fit_records.jsonl")),
]
const OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "linesearch", "wp_f3"), ARGS)
const OUTPUT_CSV = joinpath(OUTPUT_DIR, "budget_20000_replay.csv")

function csv_escape(x)
    text = string(x)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function finite_best_until(evaluations, budget::Int)
    best = Inf
    last_idx = min(length(evaluations), budget)
    for i in 1:last_idx
        loss = Float64(evaluations[i]["loss"])
        if isfinite(loss) && loss < best
            best = loss
        end
    end
    return best
end

function record_field(record, name::String, default = "")
    haskey(record, name) ? record[name] : default
end

function replay_record(source::String, record)
    evaluations = record["evaluations"]
    total = length(evaluations)
    final_loss = Float64(record["final_loss"])
    would_stop = total > BUDGET
    replay_loss = would_stop ? finite_best_until(evaluations, BUDGET) : final_loss
    factor = isfinite(final_loss) && final_loss > 0.0 ? replay_loss / final_loss : Inf
    identical = isequal(replay_loss, final_loss)
    condition = String(record_field(record, "variant_condition", record_field(record, "condition", "")))
    return (
        source = source,
        system_id = Int(record["system_id"]),
        dim = haskey(record, "dim") ? Int(record["dim"]) : "",
        condition = condition,
        structure = String(record["structure"]),
        line_search = String(record_field(record, "line_search", "default")),
        n_params = haskey(record, "n_params") ? Int(record["n_params"]) : "",
        total_evals = total,
        would_stop_at_20000 = would_stop,
        actual_final_loss = final_loss,
        replay_loss_20000 = replay_loss,
        factor = factor,
        identical = identical,
    )
end

function read_records()
    rows = NamedTuple[]
    for (source, path) in INPUTS
        isfile(path) || error("Missing input $(path)")
        open(path, "r") do io
            for line in eachline(io)
                isempty(strip(line)) && continue
                push!(rows, replay_record(source, JSON3.read(line)))
            end
        end
    end
    return rows
end

function write_csv(rows)
    mkpath(OUTPUT_DIR)
    header = [
        "source",
        "system_id",
        "dim",
        "condition",
        "structure",
        "line_search",
        "n_params",
        "total_evals",
        "would_stop_at_20000",
        "actual_final_loss",
        "replay_loss_20000",
        "factor",
        "identical",
    ]
    open(OUTPUT_CSV, "w") do io
        println(io, join(header, ","))
        for row in rows
            println(io, join(csv_escape.([getfield(row, Symbol(h)) for h in header]), ","))
        end
    end
end

function main()
    rows = read_records()
    write_csv(rows)
    differing = [row for row in rows if !row.identical]
    stopping = [row for row in rows if row.would_stop_at_20000]
    println("output=$(OUTPUT_CSV)")
    println("records=$(length(rows))")
    println("would_stop_at_20000=$(length(stopping))")
    println("differences=$(length(differing))")
    for row in differing
        @printf(
            "DIFF source=%s sys=%d dim=%s condition=%s structure=%s n_params=%s total=%d replay=%.17g final=%.17g factor=%.17g\n",
            row.source,
            row.system_id,
            string(row.dim),
            row.condition,
            row.structure,
            string(row.n_params),
            row.total_evals,
            row.replay_loss_20000,
            row.actual_final_loss,
            row.factor,
        )
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
