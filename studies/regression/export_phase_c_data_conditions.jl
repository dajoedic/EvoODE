import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_c_config.jl"))

const DEFAULT_EXPORT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "phase_c_data_conditions")
const PHASE_C_C6_EXPORT_SIGMAS = (0.0, 0.01, 0.02, 0.03, 0.04, 0.05)
const PHASE_C_C6_EXPORT_RHOS = (0.0, 0.5)

function _arg_value(args::Vector{String}, name::String, default = nothing)
    idx = findfirst(==(name), args)
    idx === nothing && return default
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _arg_values(args::Vector{String}, name::String)
    values = String[]
    i = 1
    while i <= length(args)
        if args[i] == name
            i == length(args) && error("Missing value for $(name)")
            push!(values, args[i + 1])
            i += 2
        else
            i += 1
        end
    end
    return values
end

function _parse_csv_ints(text::AbstractString)
    return Int[parse(Int, strip(part)) for part in split(text, ",") if !isempty(strip(part))]
end

function _parse_csv_floats(text::AbstractString)
    return Float64[parse(Float64, strip(part)) for part in split(text, ",") if !isempty(strip(part))]
end

function _has_flag(args::Vector{String}, name::String)
    return any(==(name), args)
end

function _condition_stem(system_id::Int, ic_set::Int, sigma::Real, rho::Real, realization::Int)
    return @sprintf(
        "system_%04d_ic%d_sigma_%s_rho_%s_realization_%d",
        system_id,
        ic_set,
        replace(_condition_float_string(sigma), "." => "p"),
        replace(_condition_float_string(rho), "." => "p"),
        realization,
    )
end

function _export_condition!(output_dir::AbstractString, system, ic_set::Int,
                            sigma::Real, rho::Real, realization::Int)
    clean = build_trajectory(system, ic_set)
    observed = apply_phase_c_data_condition(clean, Int(system[:system_id]), ic_set, sigma, rho, realization)
    stem = _condition_stem(Int(system[:system_id]), ic_set, sigma, rho, realization)
    row = export_trajectory!(joinpath(output_dir, stem), system, ic_set, observed)
    row["noise_sigma"] = string(Float64(sigma))
    row["subsample_rho"] = string(Float64(rho))
    row["noise_realization"] = string(Int(realization))
    row["noise_model"] = DATA_CONDITION_NOISE_MODEL
    row["data_condition_fingerprint"] = data_condition_fingerprint(sigma, rho, realization)
    row["n_observed_points"] = string(length(observed.t))
    row["cell_dir"] = stem
    return row
end

function _write_index(path::AbstractString, rows)
    mkpath(dirname(path))
    header = [
        "system_id", "initial_condition_set", "dimension",
        "noise_sigma", "subsample_rho", "noise_realization", "noise_model",
        "data_condition_fingerprint", "n_observed_points",
        "hash_format", "time_axis_order", "state_axis_order", "time_shape", "state_shape",
        "time_min", "time_max", "state_min", "state_max",
        "time_sha256", "state_sha256", "time_path", "state_path", "cell_dir",
        "dtype", "byte_order",
    ]
    open(path, "w") do io
        println(io, join(header, ","))
        for row in rows
            println(io, join((_csv_field(get(row, key, "")) for key in header), ","))
        end
    end
end

function _csv_field(value)
    text = string(value)
    if occursin(',', text) || occursin('"', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function main(args = ARGS)
    c6_grid = _has_flag(args, "--c6-grid")
    output_dir = _arg_value(args, "--output-dir", DEFAULT_EXPORT_DIR)
    default_systems = join(string.(sort([Int(s[:system_id]) for s in PHASE_C_SYSTEMS])), ",")
    system_ids = _parse_csv_ints(_arg_value(args, "--systems", default_systems))
    ic_sets = _parse_csv_ints(_arg_value(args, "--ic-sets", join(string.(PHASE_C_IC_SETS), ",")))
    sigmas = _parse_csv_floats(_arg_value(args, "--sigmas", c6_grid ? join(string.(PHASE_C_C6_EXPORT_SIGMAS), ",") : "0"))
    rhos = _parse_csv_floats(_arg_value(args, "--rhos", c6_grid ? join(string.(PHASE_C_C6_EXPORT_RHOS), ",") : "0"))
    realizations = _parse_csv_ints(_arg_value(args, "--realizations", c6_grid ? "1,2,3" : "0"))

    rows = Dict{String, String}[]
    for system_id in system_ids
        system = phase_c_system(system_id)
        for ic_set in ic_sets, sigma in sigmas, rho in rhos, realization in realizations
            push!(rows, _export_condition!(output_dir, system, ic_set, sigma, rho, realization))
        end
    end
    _write_index(joinpath(output_dir, "index.csv"), rows)
    println("output_dir=$(output_dir)")
    println("index=$(joinpath(output_dir, "index.csv"))")
    println("rows=$(length(rows))")
    c6_grid && println("c6_grid=true")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
