import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf

include(joinpath(@__DIR__, "run_batch_cell.jl"))

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

function main(args = ARGS)
    manifest_path = _cap_arg_value(args, "--manifest"; default = nothing)
    manifest_path === nothing && error("Missing required argument --manifest")
    rows = _row_indices(args)
    println("manifest=$(manifest_path)")
    for index in rows
        row, stage_caps = _stage_caps_for_row(manifest_path, index)
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
        )
        JSON3.write(stdout, json_safe(payload))
        write(stdout, '\n')
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
