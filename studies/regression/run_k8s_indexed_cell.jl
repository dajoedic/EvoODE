import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

include(joinpath(@__DIR__, "run_batch_cell.jl"))

function _env_path(name::String, default::String)
    value = strip(get(ENV, name, ""))
    return isempty(value) ? default : value
end

function _has_flag(args::Vector{String}, name::String)
    return any(==(name), args)
end

function _read_index_list(path::AbstractString)
    isfile(path) || error("Index list not found: $(path)")
    values = Int[]
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            push!(values, parse(Int, strip(line)))
        end
    end
    isempty(values) && error("Index list is empty: $(path)")
    return values
end

function resolve_k8s_manifest_index(completion_index::Int, index_list_path::AbstractString)
    completion_index >= 0 || error("JOB_COMPLETION_INDEX must be >= 0, got $(completion_index)")
    values = _read_index_list(index_list_path)
    line_number = completion_index + 1
    line_number <= length(values) ||
        error("JOB_COMPLETION_INDEX=$(completion_index) maps to line $(line_number), but $(index_list_path) has only $(length(values)) rows")
    return (
        completion_index = completion_index,
        index_list_line = line_number,
        manifest_index = values[line_number],
        index_list_rows = length(values),
    )
end

function _completion_index()
    value = strip(get(ENV, "JOB_COMPLETION_INDEX", ""))
    isempty(value) && error("Set JOB_COMPLETION_INDEX")
    return parse(Int, value)
end

function main(args = ARGS)
    manifest_path = _env_path("EVO_BATCH_MANIFEST", "/outputs/manifest.csv")
    output_dir = _env_path("EVO_BATCH_OUTPUT_DIR", "/outputs/tasks")
    index_list_path = _env_path("EVO_BATCH_INDEX_LIST", "/outputs/indices_dim1.txt")
    mapping = resolve_k8s_manifest_index(_completion_index(), index_list_path)

    println("job_completion_index=$(mapping.completion_index)")
    println("index_list=$(index_list_path)")
    println("index_list_line=$(mapping.index_list_line)")
    println("index_list_rows=$(mapping.index_list_rows)")
    println("manifest_index=$(mapping.manifest_index)")

    row = _manifest_row(manifest_path, mapping.manifest_index)
    println("manifest_row_system_id=$(row["system_id"])")
    println("manifest_row_system_dim=$(row["system_dim"])")
    println("manifest_row_variant=$(row["variant"])")
    println("manifest_row_initial_condition_set=$(row["initial_condition_set"])")
    println("manifest_row_seed=$(row["seed"])")

    if _has_flag(args, "--dry-run")
        return nothing
    end

    record = run_batch_cell(mapping.manifest_index, manifest_path, output_dir)
    println(summary_line(record))
    println("output=$(record["batch_output_file"])")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
