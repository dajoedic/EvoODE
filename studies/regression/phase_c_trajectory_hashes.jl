import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Printf
using SHA

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_c_config.jl"))

const HASH_FORMAT = "sha256_raw_little_endian_float64"
const TIME_AXIS_ORDER = "time"
const STATE_AXIS_ORDER = "time_by_dimension_c_order"
const DEFAULT_PYTHON_HASHES = joinpath(
    @__DIR__,
    "..",
    "..",
    "analysis",
    "data",
    "paper1_phaseC_v1",
    "phasec_sindy_baseline",
    "trajectory_hashes.csv",
)
const DEFAULT_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "phase_c_trajectory_hashes", "wp_c4c")
const DEFAULT_EXPORT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "phase_c_trajectory_hashes", "wp_c4c", "trajectory_export")

function usage()
    return """
    Usage:
      julia --project=. studies/regression/phase_c_trajectory_hashes.jl [options]

    Options:
      --python-hashes PATH   Python trajectory_hashes.csv to compare against.
                             Default: $(DEFAULT_PYTHON_HASHES)
      --output-dir PATH      Output directory for Julia hashes and comparison CSVs.
                             Default: $(DEFAULT_OUTPUT_DIR)
      --export-dir PATH      Directory for raw trajectory bytes and manifest.
                             Default: $(DEFAULT_EXPORT_DIR)
      --limit N              Hash only the first N (system, IC-set) rows for a quick check.
      --help                 Show this help text.
    """
end

function parse_args(args)
    parsed = Dict{String, Any}(
        "python_hashes" => DEFAULT_PYTHON_HASHES,
        "output_dir" => DEFAULT_OUTPUT_DIR,
        "export_dir" => DEFAULT_EXPORT_DIR,
        "limit" => nothing,
    )
    i = 1
    while i <= length(args)
        arg = args[i]
        if arg == "--help"
            println(usage())
            exit(0)
        elseif arg == "--python-hashes"
            i += 1
            i <= length(args) || error("--python-hashes requires a path")
            parsed["python_hashes"] = args[i]
        elseif arg == "--output-dir"
            i += 1
            i <= length(args) || error("--output-dir requires a path")
            parsed["output_dir"] = args[i]
        elseif arg == "--export-dir"
            i += 1
            i <= length(args) || error("--export-dir requires a path")
            parsed["export_dir"] = args[i]
        elseif arg == "--limit"
            i += 1
            i <= length(args) || error("--limit requires an integer")
            parsed["limit"] = parse(Int, args[i])
            parsed["limit"] >= 1 || error("--limit must be positive")
        else
            error("Unknown argument: $(arg)")
        end
        i += 1
    end
    return parsed
end

function append_float64_le!(bytes::Vector{UInt8}, value)
    bits = reinterpret(UInt64, Float64[value])[1]
    @inbounds for shift in 0:8:56
        push!(bytes, UInt8((bits >> shift) & 0xff))
    end
    return bytes
end

function sha256_vector_float64_le(values::AbstractVector)
    bytes = float64_vector_le_bytes(values)
    return bytes2hex(sha256(bytes))
end

function sha256_matrix_float64_le_c_order(values::AbstractMatrix)
    bytes = float64_matrix_le_c_order_bytes(values)
    return bytes2hex(sha256(bytes))
end

function float64_vector_le_bytes(values::AbstractVector)
    bytes = UInt8[]
    sizehint!(bytes, 8 * length(values))
    @inbounds for value in values
        append_float64_le!(bytes, value)
    end
    return bytes
end

function float64_matrix_le_c_order_bytes(values::AbstractMatrix)
    rows, cols = size(values)
    bytes = UInt8[]
    sizehint!(bytes, 8 * rows * cols)
    @inbounds for row in 1:rows
        for col in 1:cols
            append_float64_le!(bytes, values[row, col])
        end
    end
    return bytes
end

shape_string(dims) = "[" * join(string.(collect(dims)), ",") * "]"

function finite_range(values)
    return (minimum(values), maximum(values))
end

function row_key(row)
    return (parse(Int, row["system_id"]), parse(Int, row["initial_condition_set"]))
end

function assert_unique_keys(rows, label::AbstractString)
    seen = Set{Tuple{Int, Int}}()
    for row in rows
        key = row_key(row)
        key in seen && error("Duplicate $(label) row for system_id=$(key[1]) initial_condition_set=$(key[2])")
        push!(seen, key)
    end
    return nothing
end

function trajectory_hash_row(system, ic_set::Int)
    traj = build_trajectory(system, ic_set)
    size(traj.x, 1) == length(traj.t) ||
        error("Trajectory row/time mismatch for system $(system[:system_id]) IC $(ic_set)")
    size(traj.x, 2) == Int(system[:dim]) ||
        error("Trajectory dimension mismatch for system $(system[:system_id]) IC $(ic_set)")

    time_min, time_max = finite_range(traj.t)
    state_min, state_max = finite_range(traj.x)

    return Dict{String, String}(
        "system_id" => string(Int(system[:system_id])),
        "initial_condition_set" => string(ic_set),
        "dimension" => string(Int(system[:dim])),
        "hash_format" => HASH_FORMAT,
        "time_axis_order" => TIME_AXIS_ORDER,
        "state_axis_order" => STATE_AXIS_ORDER,
        "time_shape" => shape_string(size(traj.t)),
        "state_shape" => shape_string(size(traj.x)),
        "time_min" => string(Float64(time_min)),
        "time_max" => string(Float64(time_max)),
        "state_min" => string(Float64(state_min)),
        "state_max" => string(Float64(state_max)),
        "time_sha256" => sha256_vector_float64_le(traj.t),
        "state_sha256" => sha256_matrix_float64_le_c_order(traj.x),
    )
end

function trajectory_hash_row(system, ic_set::Int, traj::Trajectory)
    size(traj.x, 1) == length(traj.t) ||
        error("Trajectory row/time mismatch for system $(system[:system_id]) IC $(ic_set)")
    size(traj.x, 2) == Int(system[:dim]) ||
        error("Trajectory dimension mismatch for system $(system[:system_id]) IC $(ic_set)")

    time_min, time_max = finite_range(traj.t)
    state_min, state_max = finite_range(traj.x)

    return Dict{String, String}(
        "system_id" => string(Int(system[:system_id])),
        "initial_condition_set" => string(ic_set),
        "dimension" => string(Int(system[:dim])),
        "hash_format" => HASH_FORMAT,
        "time_axis_order" => TIME_AXIS_ORDER,
        "state_axis_order" => STATE_AXIS_ORDER,
        "time_shape" => shape_string(size(traj.t)),
        "state_shape" => shape_string(size(traj.x)),
        "time_min" => string(Float64(time_min)),
        "time_max" => string(Float64(time_max)),
        "state_min" => string(Float64(state_min)),
        "state_max" => string(Float64(state_max)),
        "time_sha256" => sha256_vector_float64_le(traj.t),
        "state_sha256" => sha256_matrix_float64_le_c_order(traj.x),
    )
end

function safe_cell_stem(system_id::Int, ic_set::Int)
    return @sprintf("system_%04d_ic%d", system_id, ic_set)
end

function relative_cell_path(stem::AbstractString, suffix::AbstractString)
    return joinpath("cells", stem * suffix)
end

function write_raw_bytes(path::AbstractString, bytes::Vector{UInt8})
    mkpath(dirname(path))
    open(path, "w") do io
        write(io, bytes)
    end
    return bytes2hex(sha256(bytes))
end

function export_trajectory!(export_dir::AbstractString, system, ic_set::Int, traj::Trajectory)
    system_id = Int(system[:system_id])
    stem = safe_cell_stem(system_id, ic_set)
    time_rel = relative_cell_path(stem, "_time_f64le.bin")
    state_rel = relative_cell_path(stem, "_state_f64le_c_order.bin")
    time_bytes = float64_vector_le_bytes(traj.t)
    state_bytes = float64_matrix_le_c_order_bytes(traj.x)
    time_sha = write_raw_bytes(joinpath(export_dir, time_rel), time_bytes)
    state_sha = write_raw_bytes(joinpath(export_dir, state_rel), state_bytes)
    row = trajectory_hash_row(system, ic_set, traj)
    row["time_sha256"] == time_sha ||
        error("Internal time hash mismatch while exporting system $(system_id) IC $(ic_set)")
    row["state_sha256"] == state_sha ||
        error("Internal state hash mismatch while exporting system $(system_id) IC $(ic_set)")
    row["time_path"] = time_rel
    row["state_path"] = state_rel
    row["dtype"] = "float64"
    row["byte_order"] = "little_endian"
    return row
end

function planned_cells(; limit = nothing)
    cells = Tuple{Dict{Symbol, Any}, Int}[]
    for system in sort(PHASE_C_SYSTEMS; by = s -> Int(s[:system_id]))
        for ic_set in PHASE_C_IC_SETS
            push!(cells, (system, Int(ic_set)))
        end
    end
    if limit !== nothing
        return cells[1:min(Int(limit), length(cells))]
    end
    return cells
end

function csv_escape(value)
    text = string(value)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text) || occursin("\r", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::AbstractString, columns::Vector{String}, rows::Vector{Dict{String, String}})
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(csv_escape.(columns), ","))
        for row in rows
            println(io, join([csv_escape(get(row, col, "")) for col in columns], ","))
        end
    end
    return path
end

function parse_csv_line(line::AbstractString)
    fields = String[]
    buf = IOBuffer()
    in_quotes = false
    i = firstindex(line)
    while i <= lastindex(line)
        c = line[i]
        if c == '"'
            if in_quotes && i < lastindex(line) && line[nextind(line, i)] == '"'
                write(buf, UInt8('"'))
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

function read_csv(path::AbstractString)
    lines = readlines(path)
    isempty(lines) && error("Empty CSV: $(path)")
    columns = parse_csv_line(lines[1])
    rows = Dict{String, String}[]
    for (line_no, line) in enumerate(lines[2:end])
        isempty(strip(line)) && continue
        values = parse_csv_line(line)
        length(values) == length(columns) ||
            error("CSV $(path) line $(line_no + 1) has $(length(values)) fields, expected $(length(columns))")
        push!(rows, Dict(columns[i] => values[i] for i in eachindex(columns)))
    end
    return columns, rows
end

function compare_hashes(julia_rows, python_rows)
    assert_unique_keys(julia_rows, "Julia")
    assert_unique_keys(python_rows, "Python")
    julia_by_key = Dict(row_key(row) => row for row in julia_rows)
    python_by_key = Dict(row_key(row) => row for row in python_rows)
    keys_all = sort(collect(union(keys(julia_by_key), keys(python_by_key))))

    rows = Dict{String, String}[]
    counts = Dict(
        "both_hashes_equal" => 0,
        "time_only_equal" => 0,
        "state_only_equal" => 0,
        "neither_equal" => 0,
        "missing_in_julia" => 0,
        "missing_in_python" => 0,
    )

    for key in keys_all
        system_id, ic_set = key
        jrow = get(julia_by_key, key, nothing)
        prow = get(python_by_key, key, nothing)
        status = ""
        time_equal = false
        state_equal = false
        if jrow === nothing
            status = "missing_in_julia"
        elseif prow === nothing
            status = "missing_in_python"
        else
            time_equal = jrow["time_sha256"] == prow["time_sha256"]
            state_equal = jrow["state_sha256"] == prow["state_sha256"]
            status = time_equal && state_equal ? "both_hashes_equal" :
                     time_equal ? "time_only_equal" :
                     state_equal ? "state_only_equal" : "neither_equal"
        end
        counts[status] = get(counts, status, 0) + 1

        row = Dict{String, String}(
            "system_id" => string(system_id),
            "initial_condition_set" => string(ic_set),
            "comparison_status" => status,
            "time_hash_equal" => string(time_equal),
            "state_hash_equal" => string(state_equal),
        )
        for prefix_row in (("julia", jrow), ("python", prow))
            prefix, source_row = prefix_row
            for col in ("dimension", "time_shape", "state_shape", "time_min", "time_max",
                        "state_min", "state_max", "time_sha256", "state_sha256")
                row["$(prefix)_$(col)"] = source_row === nothing ? "" : get(source_row, col, "")
            end
        end
        push!(rows, row)
    end
    return rows, counts
end

function print_comparison(rows, counts)
    for row in rows
        @printf(
            "system_id=%s initial_condition_set=%s status=%s time_equal=%s state_equal=%s\n",
            row["system_id"],
            row["initial_condition_set"],
            row["comparison_status"],
            row["time_hash_equal"],
            row["state_hash_equal"],
        )
        if row["comparison_status"] != "both_hashes_equal"
            @printf(
                "  julia:  time_shape=%s state_shape=%s time_range=[%s,%s] state_range=[%s,%s]\n",
                row["julia_time_shape"],
                row["julia_state_shape"],
                row["julia_time_min"],
                row["julia_time_max"],
                row["julia_state_min"],
                row["julia_state_max"],
            )
            @printf(
                "  python: time_shape=%s state_shape=%s time_range=[%s,%s] state_range=[%s,%s]\n",
                row["python_time_shape"],
                row["python_state_shape"],
                row["python_time_min"],
                row["python_time_max"],
                row["python_state_min"],
                row["python_state_max"],
            )
        end
    end
    println("Summary:")
    for key in sort(collect(keys(counts)))
        println("  $(key): $(counts[key])")
    end
    return nothing
end

function main(args = ARGS)
    parsed = parse_args(args)
    python_hashes = parsed["python_hashes"]
    output_dir = parsed["output_dir"]
    export_dir = parsed["export_dir"]
    limit = parsed["limit"]

    isfile(python_hashes) || error("Missing Python hash CSV: $(python_hashes)")
    cells = planned_cells(; limit = limit)
    if limit === nothing
        length(cells) == 126 || error("Expected 126 Phase-C trajectory cells, got $(length(cells))")
    else
        @warn "Running a limited trajectory hash check" limit rows = length(cells)
    end

    rows = Dict{String, String}[]
    export_rows = Dict{String, String}[]
    for (system, ic_set) in cells
        traj = build_trajectory(system, ic_set)
        push!(rows, trajectory_hash_row(system, ic_set, traj))
        push!(export_rows, export_trajectory!(export_dir, system, ic_set, traj))
    end

    hash_columns = [
        "system_id",
        "initial_condition_set",
        "dimension",
        "hash_format",
        "time_axis_order",
        "state_axis_order",
        "time_shape",
        "state_shape",
        "time_min",
        "time_max",
        "state_min",
        "state_max",
        "time_sha256",
        "state_sha256",
    ]
    hash_path = joinpath(output_dir, "trajectory_hashes_julia.csv")
    write_csv(hash_path, hash_columns, rows)

    manifest_columns = [
        "system_id",
        "initial_condition_set",
        "dimension",
        "hash_format",
        "dtype",
        "byte_order",
        "time_axis_order",
        "state_axis_order",
        "time_shape",
        "state_shape",
        "time_min",
        "time_max",
        "state_min",
        "state_max",
        "time_sha256",
        "state_sha256",
        "time_path",
        "state_path",
    ]
    manifest_path = joinpath(export_dir, "trajectory_manifest.csv")
    write_csv(manifest_path, manifest_columns, export_rows)

    _, python_rows = read_csv(python_hashes)
    if limit !== nothing
        selected_keys = Set(row_key(row) for row in rows)
        python_rows = [row for row in python_rows if row_key(row) in selected_keys]
    end
    comparison_rows, counts = compare_hashes(rows, python_rows)
    comparison_columns = [
        "system_id",
        "initial_condition_set",
        "comparison_status",
        "time_hash_equal",
        "state_hash_equal",
        "julia_dimension",
        "python_dimension",
        "julia_time_shape",
        "python_time_shape",
        "julia_state_shape",
        "python_state_shape",
        "julia_time_min",
        "python_time_min",
        "julia_time_max",
        "python_time_max",
        "julia_state_min",
        "python_state_min",
        "julia_state_max",
        "python_state_max",
        "julia_time_sha256",
        "python_time_sha256",
        "julia_state_sha256",
        "python_state_sha256",
    ]
    comparison_path = joinpath(output_dir, "trajectory_hash_comparison.csv")
    write_csv(comparison_path, comparison_columns, comparison_rows)
    print_comparison(comparison_rows, counts)

    println("Julia hash CSV: $(hash_path)")
    println("Comparison CSV: $(comparison_path)")
    println("Trajectory export manifest: $(manifest_path)")
    return nothing
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
