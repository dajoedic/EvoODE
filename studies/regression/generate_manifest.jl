import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

include(joinpath(@__DIR__, "run_regression.jl"))

const DEFAULT_BATCH_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "wp_b2")
const DEFAULT_MANIFEST_PATH = joinpath(DEFAULT_BATCH_DIR, "manifest.csv")

function _arg_value(args::Vector{String}, name::String)
    idx = findfirst(==(name), args)
    idx === nothing && return nothing
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _parse_optional_int(value)
    value === nothing && return nothing
    return parse(Int, value)
end

function manifest_rows()
    fingerprint = config_fingerprint()
    rows = NamedTuple[]
    index = 1
    for variant in VARIANTS
        for system in sort(REGRESSION_SYSTEMS; by = s -> Int(s[:system_id]))
            for ic_set in REGRESSION_IC_SETS
                for seed in REGRESSION_SEEDS
                    push!(
                        rows,
                        (
                            index = index,
                            config_fingerprint = fingerprint,
                            variant = String(variant.label),
                            system_id = Int(system[:system_id]),
                            system_dim = Int(system[:dim]),
                            initial_condition_set = ic_set,
                            seed = seed,
                        ),
                    )
                    index += 1
                end
            end
        end
    end
    return rows
end

function write_manifest(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "index,config_fingerprint,variant,system_id,system_dim,initial_condition_set,seed")
        for row in rows
            println(
                io,
                join(
                    (
                        row.index,
                        row.config_fingerprint,
                        row.variant,
                        row.system_id,
                        row.system_dim,
                        row.initial_condition_set,
                        row.seed,
                    ),
                    ",",
                ),
            )
        end
    end
end

function write_dimension_index_list(path::AbstractString, rows, dimension::Int)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            row.system_dim == dimension && println(io, row.index)
        end
    end
end

function main(args = ARGS)
    output = get(ENV, "EVO_BATCH_MANIFEST", DEFAULT_MANIFEST_PATH)
    arg_output = _arg_value(args, "--output")
    arg_output !== nothing && (output = arg_output)

    dimension = _parse_optional_int(_arg_value(args, "--dimension"))
    index_output = _arg_value(args, "--index-output")

    rows = manifest_rows()
    write_manifest(output, rows)
    if dimension !== nothing
        index_output === nothing && (index_output = joinpath(dirname(output), "indices_dim$(dimension).txt"))
        write_dimension_index_list(index_output, rows, dimension)
    end

    println("manifest=$(output)")
    println("config_fingerprint=$(config_fingerprint())")
    println("rows=$(length(rows))")
    if dimension !== nothing
        count_dim = count(row -> row.system_dim == dimension, rows)
        println("dimension=$(dimension)")
        println("dimension_rows=$(count_dim)")
        println("dimension_index_output=$(index_output)")
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
