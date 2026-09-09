import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

include(joinpath(@__DIR__, "wp_n1_basis_probe.jl"))

const WP_N1_PROBE_CAMPAIGN_ID = "wp_n1_basis_probe"
const WP_N1_DIM2_MANIFEST_DIR = joinpath(@__DIR__, "..", "..", "outputs", "wp_n1_dim2_probe")
const WP_N1_DIM2_MANIFEST_PATH = joinpath(WP_N1_DIM2_MANIFEST_DIR, "manifest.csv")

function _arg_value(args::Vector{String}, name::String)
    idx = findfirst(==(name), args)
    idx === nothing && return nothing
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _wp_n1_manifest_systems(dim::Int)
    dim <= 2 || error("WP-N1 basis probe only supports dim=1 or dim=2 manifests")
    if dim == 1
        systems = [s for s in PHASE_B_SYSTEMS if Int(s[:dim]) == dim && Int(s[:system_id]) in WP_N1_DIM1_SYSTEM_IDS]
        order = Dict(id => i for (i, id) in enumerate(WP_N1_DIM1_SYSTEM_IDS))
        sort!(systems; by = s -> order[Int(s[:system_id])])
        return systems
    end
    return sort([s for s in PHASE_B_SYSTEMS if Int(s[:dim]) == dim]; by = s -> Int(s[:system_id]))
end

function wp_n1_basis_probe_manifest_rows(dim::Int)
    fingerprint = _wp_n1_fingerprint(dim)
    rows = NamedTuple[]
    index = 1
    for variant in _wp_n1_basis_modes()
        for system in _wp_n1_manifest_systems(dim)
            for ic_set in WP_N1_IC_SETS
                for seed in WP_N1_SEEDS
                    push!(
                        rows,
                        (
                            index = index,
                            campaign = WP_N1_PROBE_CAMPAIGN_ID,
                            config_fingerprint = fingerprint,
                            variant = String(variant.label),
                            condition = String(variant.condition),
                            use_pretuning = Bool(variant.use_pretuning),
                            basis_name = String(variant.basis_name),
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

function wp_n1_basis_probe_identity(row)
    return (
        row.campaign,
        row.variant,
        row.system_id,
        row.initial_condition_set,
        row.seed,
    )
end

function write_wp_n1_basis_probe_manifest(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "index,campaign,config_fingerprint,variant,condition,use_pretuning,basis_name,system_id,system_dim,initial_condition_set,seed")
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
                        row.basis_name,
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

function write_wp_n1_basis_probe_index_list(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            println(io, row.index)
        end
    end
end

function main(args = ARGS)
    dim_value = _arg_value(args, "--dimension")
    dim = dim_value === nothing ? 2 : parse(Int, dim_value)
    output = something(_arg_value(args, "--output"), WP_N1_DIM2_MANIFEST_PATH)
    index_output = something(_arg_value(args, "--index-output"), joinpath(dirname(output), "indices_dim$(dim).txt"))

    rows = wp_n1_basis_probe_manifest_rows(dim)
    unique_identities = length(Set(wp_n1_basis_probe_identity(row) for row in rows))
    unique_identities == length(rows) || error("WP-N1 manifest identities are not unique")
    expected_rows = dim == 1 ? 132 : 336
    length(rows) == expected_rows || error("WP-N1 dim=$(dim) manifest row count changed: $(length(rows))")

    write_wp_n1_basis_probe_manifest(output, rows)
    write_wp_n1_basis_probe_index_list(index_output, rows)

    println("manifest=$(output)")
    println("index_output=$(index_output)")
    println("campaign=$(WP_N1_PROBE_CAMPAIGN_ID)")
    println("wp_n1_fingerprint=$(_wp_n1_fingerprint(dim))")
    println("base_phase_b_fingerprint=$(phase_b_fingerprint())")
    println("stage_cap_behavior_fingerprint=$(stage_cap_behavior_fingerprint())")
    println("dimension=$(dim)")
    println("systems=$(length(_wp_n1_manifest_systems(dim)))")
    println("variants=$(length(_wp_n1_basis_modes()))")
    println("ic_sets=$(length(WP_N1_IC_SETS))")
    println("seeds=$(length(WP_N1_SEEDS))")
    println("rows=$(length(rows))")
    println("unique_identities=$(unique_identities)")
    println("index_rows=$(length(rows))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
