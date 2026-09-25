const HASH_FORMAT = "sha256_raw_little_endian_float64"
const TIME_AXIS_ORDER = "time"
const STATE_AXIS_ORDER = "time_by_dimension_c_order"

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

function trajectory_hash_row(system, ic_set::Int)
    traj = build_trajectory(system, ic_set)
    return trajectory_hash_row(system, ic_set, traj)
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
