import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf

include(joinpath(@__DIR__, "run_batch_cell.jl"))

const CAP_PRECHECK_DIMENSION_MEAN_SECONDS = Dict(
    1 => 250.0,
    2 => 10_440.0,
    3 => 63_800.0,
    4 => 2_300.0,
)
const CAP_PRECHECK_MANIFEST_HEADER = [
    "index", "campaign", "config_fingerprint", "variant", "condition", "use_pretuning",
    "basis_name", "max_fit_attempts", "system_id", "system_dim", "initial_condition_set",
    "seed", "representability", "noise_sigma", "subsample_rho", "noise_realization",
    "clamp_val",
]

function _cap_arg_values(args::Vector{String}, name::String)
    values = String[]
    idx = 1
    while idx <= length(args)
        if args[idx] == name
            idx == length(args) && error("Missing value for $(name)")
            push!(values, args[idx + 1])
            idx += 2
        else
            idx += 1
        end
    end
    return values
end

function _cap_arg_value(args::Vector{String}, name::String; default = nothing)
    values = _cap_arg_values(args, name)
    length(values) > 1 && error("Expected at most one $(name), got $(length(values))")
    isempty(values) && return default
    return only(values)
end

function _parse_int_list(value::AbstractString)
    items = split(value, ",")
    isempty(items) && error("Expected at least one row index")
    return [parse(Int, strip(item)) for item in items if !isempty(strip(item))]
end

function _row_indices(args::Vector{String})
    manifest_path = _cap_arg_value(args, "--manifest"; default = nothing)
    if _has_cap_flag(args, "--all-rows")
        manifest_path === nothing && error("Missing required argument --manifest")
        return sort([parse(Int, row["index"]) for row in _read_manifest(manifest_path)])
    end
    value = _cap_arg_value(args, "--rows"; default = nothing)
    if value !== nothing
        return _parse_int_list(value)
    end
    positional = String[]
    idx = 1
    while idx <= length(args)
        if args[idx] in ("--manifest", "--rows")
            idx += 2
        else
            push!(positional, args[idx])
            idx += 1
        end
    end
    isempty(positional) && error("Pass --rows i,j,k or positional row indices")
    return parse.(Int, positional)
end

function _has_cap_flag(args::Vector{String}, name::String)
    return any(==(name), args)
end

function _basis_for_variant(variant, dim::Int)
    basis_name = String(variant.basis_name)
    basis_name == PHASE_C_BASIS_NAME && return phase_c_basis(dim)
    error("Unsupported Phase-C basis_name=$(basis_name)")
end

function _stage_caps_for_row(manifest_path::AbstractString, index::Int)
    row = _manifest_row(manifest_path, index)
    _is_phase_c_row(row) || error("Manifest row $(index) is not a Phase-C row")
    current_fingerprint = _batch_fingerprint(row)
    current_fingerprint == row["config_fingerprint"] ||
        error("Fingerprint mismatch for manifest $(manifest_path): manifest=$(row["config_fingerprint"]), runtime=$(current_fingerprint)")

    variant = _batch_variant(row)
    system = _batch_system(row, variant)
    dim = Int(system[:dim])
    ic_set = parse(Int, row["initial_condition_set"])
    noise_sigma = parse(Float64, get(row, "noise_sigma", "0"))
    subsample_rho = parse(Float64, get(row, "subsample_rho", "0"))
    noise_realization = parse(Int, get(row, "noise_realization", "0"))
    clean_traj = build_trajectory(system, ic_set)
    observed_traj = apply_phase_c_data_condition(
        clean_traj,
        Int(system[:system_id]),
        ic_set,
        noise_sigma,
        subsample_rho,
        noise_realization,
    )
    basis = _basis_for_variant(variant, dim)
    stage_caps = estimate_stage_caps(observed_traj, basis; policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...))
    return row, stage_caps
end

function _json_string(value)
    return sprint(io -> JSON3.write(io, json_safe(value)))
end

function _csv_field(value)
    text = string(value)
    if occursin(',', text) || occursin('"', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function _has_finite_cap_lt5(stage_caps)
    return any(cap -> cap !== nothing && Int(cap) < 5, stage_caps)
end

function _write_cap_csv(path::AbstractString, rows)
    mkpath(dirname(path))
    header = [
        "index", "system_id", "initial_condition_set", "seed", "noise_sigma",
        "subsample_rho", "noise_realization", "stage_caps", "has_finite_cap_lt5",
    ]
    open(path, "w") do io
        println(io, join(header, ","))
        for item in rows
            row = item.row
            values = [
                item.index,
                row["system_id"],
                row["initial_condition_set"],
                row["seed"],
                get(row, "noise_sigma", "0"),
                get(row, "subsample_rho", "0"),
                get(row, "noise_realization", "0"),
                _json_string(item.stage_caps),
                item.has_finite_cap_lt5,
            ]
            println(io, join((_csv_field(value) for value in values), ","))
        end
    end
end

function _uncapped_manifest_rows(cap_rows)
    selected = [item for item in cap_rows if item.has_finite_cap_lt5]
    sorted = sort(
        selected;
        by = item -> CAP_PRECHECK_DIMENSION_MEAN_SECONDS[parse(Int, item.row["system_dim"])],
        rev = true,
        alg = MergeSort,
    )
    rows = Dict{String, String}[]
    for (idx, item) in enumerate(sorted)
        row = copy(item.row)
        row["index"] = string(idx)
        row["variant"] = "evogrow_v2_2_stage_local"
        row["condition"] = "uncapped"
        row["use_pretuning"] = "false"
        push!(rows, row)
    end
    return rows
end

function _write_manifest(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(CAP_PRECHECK_MANIFEST_HEADER, ","))
        for row in rows
            println(io, join((row[column] for column in CAP_PRECHECK_MANIFEST_HEADER), ","))
        end
    end
end

function _write_indices(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            println(io, row["index"])
        end
    end
end

function main(args = ARGS)
    manifest_path = _cap_arg_value(args, "--manifest"; default = nothing)
    manifest_path === nothing && error("Missing required argument --manifest")
    rows = _row_indices(args)
    output_csv = _cap_arg_value(args, "--output-csv"; default = nothing)
    uncapped_manifest = _cap_arg_value(args, "--uncapped-manifest-output"; default = nothing)
    uncapped_indices = _cap_arg_value(args, "--uncapped-index-output"; default = nothing)
    println("manifest=$(manifest_path)")
    cap_rows = NamedTuple[]
    for index in rows
        row, stage_caps = _stage_caps_for_row(manifest_path, index)
        has_finite_cap_lt5 = _has_finite_cap_lt5(stage_caps)
        push!(cap_rows, (index = index, row = row, stage_caps = stage_caps, has_finite_cap_lt5 = has_finite_cap_lt5))
        payload = Dict{String, Any}(
            "manifest_index" => index,
            "system_id" => parse(Int, row["system_id"]),
            "variant" => row["variant"],
            "condition" => row["condition"],
            "initial_condition_set" => parse(Int, row["initial_condition_set"]),
            "seed" => parse(Int, row["seed"]),
            "noise_sigma" => parse(Float64, get(row, "noise_sigma", "0")),
            "subsample_rho" => parse(Float64, get(row, "subsample_rho", "0")),
            "noise_realization" => parse(Int, get(row, "noise_realization", "0")),
            "clamp_val" => get(row, "clamp_val", "10"),
            "stage_caps" => stage_caps,
            "has_finite_cap_lt5" => has_finite_cap_lt5,
        )
        JSON3.write(stdout, json_safe(payload))
        write(stdout, '\n')
    end
    if output_csv !== nothing
        _write_cap_csv(output_csv, cap_rows)
        println("output_csv=$(output_csv)")
        println("output_csv_rows=$(length(cap_rows))")
    end
    if uncapped_manifest !== nothing
        uncapped_rows = _uncapped_manifest_rows(cap_rows)
        _write_manifest(uncapped_manifest, uncapped_rows)
        uncapped_indices === nothing && (uncapped_indices = joinpath(dirname(uncapped_manifest), "indices_cost_desc.txt"))
        _write_indices(uncapped_indices, uncapped_rows)
        println("uncapped_manifest=$(uncapped_manifest)")
        println("uncapped_rows=$(length(uncapped_rows))")
        println("uncapped_index_output=$(uncapped_indices)")
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
