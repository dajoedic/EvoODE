import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3

include(joinpath(@__DIR__, "run_regression.jl"))

const DEFAULT_BATCH_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "wp_b2")
const DEFAULT_TASK_OUTPUT_DIR = joinpath(DEFAULT_BATCH_DIR, "tasks")
const DEFAULT_MERGED_HISTORY_PATH = joinpath(DEFAULT_BATCH_DIR, "history.jsonl")

function _arg_value(args::Vector{String}, name::String)
    idx = findfirst(==(name), args)
    idx === nothing && return nothing
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _record_key(record)
    return (
        String(getproperty(record, :variant)),
        Int(getproperty(record, :system_id)),
        haskey(record, :initial_condition_set) ? Int(getproperty(record, :initial_condition_set)) : 1,
        Int(getproperty(record, :seed)),
        String(getproperty(record, :config_fingerprint)),
    )
end

function _load_existing_keys(path::AbstractString)
    keys = Set{Tuple{String, Int, Int, Int, String}}()
    isfile(path) || return keys
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            try
                record = JSON3.read(line)
                push!(keys, _record_key(record))
            catch err
                error("Cannot parse existing history $(path): $(err)")
            end
        end
    end
    return keys
end

function _task_files(input_dir::AbstractString)
    isdir(input_dir) || error("Input directory not found: $(input_dir)")
    return sort(
        [joinpath(input_dir, name) for name in readdir(input_dir) if endswith(name, ".jsonl")],
    )
end

function merge_batch_records(input_dir::AbstractString, history_path::AbstractString)
    existing = _load_existing_keys(history_path)
    added = 0
    skipped_duplicates = 0
    skipped_failed = 0
    considered = 0
    mkpath(dirname(history_path))
    open(history_path, "a") do out
        for path in _task_files(input_dir)
            open(path, "r") do io
                for line in eachline(io)
                    isempty(strip(line)) && continue
                    considered += 1
                    record = JSON3.read(line)
                    if haskey(record, :error) && getproperty(record, :error) !== nothing
                        skipped_failed += 1
                        continue
                    end
                    key = _record_key(record)
                    if key in existing
                        skipped_duplicates += 1
                        continue
                    end
                    print(out, line)
                    write(out, '\n')
                    push!(existing, key)
                    added += 1
                end
            end
        end
    end
    return (
        considered = considered,
        added = added,
        skipped_duplicates = skipped_duplicates,
        skipped_failed = skipped_failed,
        history_path = history_path,
    )
end

function main(args = ARGS)
    input_dir = get(ENV, "EVO_BATCH_TASK_DIR", DEFAULT_TASK_OUTPUT_DIR)
    history_path = get(ENV, "EVO_BATCH_HISTORY_PATH", DEFAULT_MERGED_HISTORY_PATH)
    arg_input_dir = _arg_value(args, "--input-dir")
    arg_history_path = _arg_value(args, "--history")
    arg_input_dir !== nothing && (input_dir = arg_input_dir)
    arg_history_path !== nothing && (history_path = arg_history_path)

    result = merge_batch_records(input_dir, history_path)
    println("considered=$(result.considered)")
    println("added=$(result.added)")
    println("skipped_duplicates=$(result.skipped_duplicates)")
    println("skipped_failed=$(result.skipped_failed)")
    println("history=$(result.history_path)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
