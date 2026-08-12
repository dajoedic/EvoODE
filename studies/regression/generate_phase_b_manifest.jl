import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_b_config.jl"))

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

function _has_flag(args::Vector{String}, name::String)
    return any(==(name), args)
end

function phase_b_manifest_rows()
    fingerprint = phase_b_fingerprint()
    rows = NamedTuple[]
    index = 1
    for variant in PHASE_B_VARIANTS
        for system in sort(PHASE_B_SYSTEMS; by = s -> Int(s[:system_id]))
            for ic_set in PHASE_B_IC_SETS
                for seed in PHASE_B_SEEDS
                    push!(
                        rows,
                        (
                            index = index,
                            campaign = PHASE_B_ID,
                            config_fingerprint = fingerprint,
                            variant = String(variant.label),
                            condition = String(variant.condition),
                            use_pretuning = Bool(variant.use_pretuning),
                            system_id = Int(system[:system_id]),
                            system_dim = Int(system[:dim]),
                            initial_condition_set = ic_set,
                            seed = seed,
                            representability = String(system[:representability]),
                        ),
                    )
                    index += 1
                end
            end
        end
    end
    return rows
end

function phase_b_identity(row)
    return (
        row.campaign,
        row.variant,
        row.system_id,
        row.initial_condition_set,
        row.seed,
    )
end

function phase_b_unique_identity_count(rows)
    return length(Set(phase_b_identity(row) for row in rows))
end

function write_phase_b_manifest(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "index,campaign,config_fingerprint,variant,condition,use_pretuning,system_id,system_dim,initial_condition_set,seed,representability")
        for row in rows
            println(
                io,
                join(
                    (
                        row.index,
                        row.campaign,
                        row.config_fingerprint,
                        row.variant,
                        row.condition,
                        row.use_pretuning,
                        row.system_id,
                        row.system_dim,
                        row.initial_condition_set,
                        row.seed,
                        row.representability,
                    ),
                    ",",
                ),
            )
        end
    end
end

function write_phase_b_dimension_index_list(path::AbstractString, rows, dimension::Int)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            row.system_dim == dimension && println(io, row.index)
        end
    end
end

function main(args = ARGS)
    output = get(ENV, "EVO_PHASE_B_MANIFEST", PHASE_B_MANIFEST_PATH)
    arg_output = _arg_value(args, "--output")
    arg_output !== nothing && (output = arg_output)

    dimension = _parse_optional_int(_arg_value(args, "--dimension"))
    all_dimensions = _has_flag(args, "--all-dimensions")
    dimension !== nothing && all_dimensions && error("Use either --dimension or --all-dimensions, not both")
    index_output = _arg_value(args, "--index-output")
    index_output !== nothing && all_dimensions && error("--index-output is only valid with --dimension")

    rows = phase_b_manifest_rows()
    unique_identities = phase_b_unique_identity_count(rows)
    unique_identities == length(rows) || error("Phase B manifest identities are not unique")
    length(rows) == 756 || error("Phase B manifest row count changed: $(length(rows))")
    write_phase_b_manifest(output, rows)

    if dimension !== nothing
        index_output === nothing && (index_output = joinpath(dirname(output), "indices_dim$(dimension).txt"))
        write_phase_b_dimension_index_list(index_output, rows, dimension)
    elseif all_dimensions
        for dim in sort(unique(row.system_dim for row in rows))
            write_phase_b_dimension_index_list(joinpath(dirname(output), "indices_dim$(dim).txt"), rows, dim)
        end
    end

    counts = phase_b_representability_counts()
    missing_expected_stage = count(system -> system[:expected_stage] === nothing, PHASE_B_SYSTEMS)
    println("manifest=$(output)")
    println("phase_b_fingerprint=$(phase_b_fingerprint())")
    println("regression_fingerprint=$(config_fingerprint())")
    println("rows=$(length(rows))")
    println("unique_identities=$(unique_identities)")
    println("systems=$(length(PHASE_B_SYSTEMS))")
    println("expected_stage_missing=$(missing_expected_stage)")
    println("representability_exact=$(counts["exact"])")
    println("representability_surrogate=$(counts["surrogate"])")
    if dimension !== nothing
        count_dim = count(row -> row.system_dim == dimension, rows)
        println("dimension=$(dimension)")
        println("dimension_rows=$(count_dim)")
        println("dimension_index_output=$(index_output)")
    elseif all_dimensions
        for dim in sort(unique(row.system_dim for row in rows))
            count_dim = count(row -> row.system_dim == dim, rows)
            println("dimension_$(dim)_rows=$(count_dim)")
            println("dimension_$(dim)_index_output=$(joinpath(dirname(output), "indices_dim$(dim).txt"))")
        end
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
