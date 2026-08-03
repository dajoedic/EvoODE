import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf

include(joinpath(@__DIR__, "run_regression.jl"))

const DEFAULT_BATCH_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "wp_b2")
const DEFAULT_MANIFEST_PATH = joinpath(DEFAULT_BATCH_DIR, "manifest.csv")
const DEFAULT_TASK_OUTPUT_DIR = joinpath(DEFAULT_BATCH_DIR, "tasks")

function _arg_value(args::Vector{String}, name::String)
    idx = findfirst(==(name), args)
    idx === nothing && return nothing
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _task_index(args::Vector{String})
    for (i, arg) in pairs(args)
        startswith(arg, "--") && continue
        if i == 1 || args[i - 1] ∉ ("--manifest", "--output-dir")
            return parse(Int, arg)
        end
    end
    value = strip(get(ENV, "SLURM_ARRAY_TASK_ID", ""))
    isempty(value) && error("Pass an index argument or set SLURM_ARRAY_TASK_ID")
    return parse(Int, value)
end

function _read_manifest(path::AbstractString)
    isfile(path) || error("Manifest not found: $(path)")
    rows = Dict{String, String}[]
    open(path, "r") do io
        header = split(chomp(readline(io)), ",")
        for line in eachline(io)
            isempty(strip(line)) && continue
            values = split(chomp(line), ",")
            length(values) == length(header) || error("Malformed manifest row: $(line)")
            push!(rows, Dict(header[i] => values[i] for i in eachindex(header)))
        end
    end
    return rows
end

function _manifest_row(path::AbstractString, index::Int)
    matches = [row for row in _read_manifest(path) if parse(Int, row["index"]) == index]
    isempty(matches) && error("Manifest index $(index) not found in $(path)")
    length(matches) == 1 || error("Manifest index $(index) is duplicated in $(path)")
    return matches[1]
end

function _variant(label::String)
    matches = [variant for variant in VARIANTS if String(variant.label) == label]
    isempty(matches) && error("Unknown variant in manifest: $(label)")
    return matches[1]
end

function _system(system_id::Int)
    matches = [system for system in REGRESSION_SYSTEMS if Int(system[:system_id]) == system_id]
    isempty(matches) && error("Unknown system_id in manifest: $(system_id)")
    return matches[1]
end

function _task_output_path(output_dir::AbstractString, index::Int)
    return joinpath(output_dir, @sprintf("cell_%06d.jsonl", index))
end

function _portable_path(path::AbstractString)
    return replace(String(path), Char(0x5c) => '/')
end

function write_task_record(path::AbstractString, record)
    mkpath(dirname(path))
    tmp = path * ".tmp"
    open(tmp, "w") do io
        JSON3.write(io, record)
        write(io, '\n')
    end
    mv(tmp, path; force = true)
end

function run_batch_cell(index::Int, manifest_path::AbstractString, output_dir::AbstractString)
    row = _manifest_row(manifest_path, index)
    current_fingerprint = config_fingerprint()
    manifest_fingerprint = row["config_fingerprint"]
    manifest_fingerprint == current_fingerprint ||
        error("Fingerprint mismatch for manifest $(manifest_path): manifest=$(manifest_fingerprint), runtime=$(current_fingerprint)")

    variant = _variant(row["variant"])
    system = _system(parse(Int, row["system_id"]))
    ic_set = parse(Int, row["initial_condition_set"])
    seed = parse(Int, row["seed"])
    record = run_one(variant, system, ic_set, seed, current_fingerprint, git_provenance())
    record["manifest_index"] = index
    record["manifest_path"] = _portable_path(manifest_path)
    output_path = _task_output_path(output_dir, index)
    record["batch_output_file"] = _portable_path(output_path)
    write_task_record(output_path, record)
    record["error"] === nothing || error("Cell $(index) failed: $(record["error"])")
    return record
end

function main(args = ARGS)
    manifest_path = get(ENV, "EVO_BATCH_MANIFEST", DEFAULT_MANIFEST_PATH)
    output_dir = get(ENV, "EVO_BATCH_OUTPUT_DIR", DEFAULT_TASK_OUTPUT_DIR)
    arg_manifest = _arg_value(args, "--manifest")
    arg_output_dir = _arg_value(args, "--output-dir")
    arg_manifest !== nothing && (manifest_path = arg_manifest)
    arg_output_dir !== nothing && (output_dir = arg_output_dir)

    index = _task_index(args)
    record = run_batch_cell(index, manifest_path, output_dir)
    println(summary_line(record))
    println("output=$(record["batch_output_file"])")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
