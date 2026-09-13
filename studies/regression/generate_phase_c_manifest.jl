import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_c_config.jl"))

# Measured dimension-class means in seconds per cell, from docs/hpc_requirements.md Section 2.
const PHASE_C_DIMENSION_MEAN_SECONDS = Dict(
    1 => 250.0,
    2 => 10_440.0,
    3 => 63_800.0,
    4 => 2_300.0,
)

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

function _phase_c_arm_variants(condition::String)
    return [variant for variant in PHASE_C_VARIANTS if String(variant.condition) == condition]
end

function phase_c_manifest_rows()
    fingerprint = phase_c_fingerprint()
    rows = NamedTuple[]
    index = 1
    capped = only(_phase_c_arm_variants("capped"))
    uncapped = only(_phase_c_arm_variants("uncapped"))
    pretune = only(_phase_c_arm_variants("pretune_on"))

    # C-1 and C-2 are the paired Claim-B comparison. The pair members are
    # adjacent for each (system, IC, seed), so an early abort leaves roughly the
    # same prefix coverage in both arms instead of a one-arm-only dataset.
    for system in sort(PHASE_C_SYSTEMS; by = s -> Int(s[:system_id]))
        for ic_set in PHASE_C_IC_SETS
            for seed in PHASE_C_SEEDS
                for variant in (capped, uncapped)
                    push!(
                        rows,
                        (
                            index = index,
                            campaign = PHASE_C_ID,
                            config_fingerprint = fingerprint,
                            variant = String(variant.label),
                            condition = String(variant.condition),
                            use_pretuning = Bool(variant.use_pretuning),
                            basis_name = String(variant.basis_name),
                            max_fit_attempts = Int(variant.max_fit_attempts),
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

    for system in sort(phase_c_exact_systems(); by = s -> Int(s[:system_id]))
        for ic_set in PHASE_C_IC_SETS
            for seed in PHASE_C_SEEDS
                push!(
                    rows,
                    (
                        index = index,
                        campaign = PHASE_C_ID,
                        config_fingerprint = fingerprint,
                        variant = String(pretune.label),
                        condition = String(pretune.condition),
                        use_pretuning = Bool(pretune.use_pretuning),
                        basis_name = String(pretune.basis_name),
                        max_fit_attempts = Int(pretune.max_fit_attempts),
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
    return rows
end

function phase_c_identity(row)
    return (
        row.campaign,
        row.variant,
        row.system_id,
        row.initial_condition_set,
        row.seed,
    )
end

function phase_c_unique_identity_count(rows)
    return length(Set(phase_c_identity(row) for row in rows))
end

function write_phase_c_manifest(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "index,campaign,config_fingerprint,variant,condition,use_pretuning,basis_name,max_fit_attempts,system_id,system_dim,initial_condition_set,seed,representability")
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
                        row.max_fit_attempts,
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

function write_phase_c_dimension_index_list(path::AbstractString, rows, dimension::Int)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            row.system_dim == dimension && println(io, row.index)
        end
    end
end

function write_phase_c_all_index_list(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            println(io, row.index)
        end
    end
end

function phase_c_cost_desc_rows(rows)
    return sort(
        rows;
        by = row -> PHASE_C_DIMENSION_MEAN_SECONDS[row.system_dim],
        rev = true,
        alg = MergeSort,
    )
end

function write_phase_c_cost_desc_index_list(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in phase_c_cost_desc_rows(rows)
            println(io, row.index)
        end
    end
end

function _phase_c_condition_rows(rows, conditions)
    condition_set = Set(String(condition) for condition in conditions)
    return [row for row in rows if row.condition in condition_set]
end

function write_phase_c_condition_cost_desc_index_list(path::AbstractString, rows, conditions)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in phase_c_cost_desc_rows(_phase_c_condition_rows(rows, conditions))
            println(io, row.index)
        end
    end
end

function phase_c_smoke_rows(rows)
    smoke_rows = NamedTuple[]
    for condition in ("capped", "uncapped", "pretune_on")
        row = findfirst(row -> row.condition == condition && row.system_dim == 1, rows)
        row === nothing && error("No dim-1 Phase C smoke row found for condition $(condition)")
        push!(smoke_rows, rows[row])
    end
    return smoke_rows
end

function write_phase_c_smoke_index_list(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in phase_c_smoke_rows(rows)
            println(io, row.index)
        end
    end
end

function phase_c_limit_rows(rows, limit::Union{Nothing, Int})
    limit === nothing && return rows
    limit >= 3 || error("--limit must be at least 3 so the smoke manifest covers all Phase C arms")
    smoke_rows = phase_c_smoke_rows(rows)
    limited = copy(smoke_rows)
    smoke_indices = Set(row.index for row in smoke_rows)
    for row in rows
        length(limited) >= limit && break
        if row.index in smoke_indices
            continue
        end
        push!(limited, row)
    end
    return limited
end

function main(args = ARGS)
    output = get(ENV, "EVO_PHASE_C_MANIFEST", PHASE_C_MANIFEST_PATH)
    arg_output = _arg_value(args, "--output")
    arg_output !== nothing && (output = arg_output)

    dimension = _parse_optional_int(_arg_value(args, "--dimension"))
    limit = _parse_optional_int(_arg_value(args, "--limit"))
    all_dimensions = _has_flag(args, "--all-dimensions")
    dimension !== nothing && all_dimensions && error("Use either --dimension or --all-dimensions, not both")
    index_output = _arg_value(args, "--index-output")
    index_output !== nothing && all_dimensions && error("--index-output is only valid with --dimension")

    rows = phase_c_limit_rows(phase_c_manifest_rows(), limit)
    unique_identities = phase_c_unique_identity_count(rows)
    unique_identities == length(rows) || error("Phase C manifest identities are not unique")
    write_phase_c_manifest(output, rows)

    if dimension !== nothing
        index_output === nothing && (index_output = joinpath(dirname(output), "indices_dim$(dimension).txt"))
        write_phase_c_dimension_index_list(index_output, rows, dimension)
    elseif all_dimensions
        write_phase_c_all_index_list(joinpath(dirname(output), "indices_all.txt"), rows)
        write_phase_c_cost_desc_index_list(joinpath(dirname(output), "indices_cost_desc.txt"), rows)
        write_phase_c_condition_cost_desc_index_list(
            joinpath(dirname(output), "indices_c1_c2_cost_desc.txt"),
            rows,
            ("capped", "uncapped"),
        )
        write_phase_c_condition_cost_desc_index_list(
            joinpath(dirname(output), "indices_c3_cost_desc.txt"),
            rows,
            ("pretune_on",),
        )
        write_phase_c_smoke_index_list(joinpath(dirname(output), "indices_smoke_dim1_all_arms.txt"), rows)
        for dim in sort(unique(row.system_dim for row in rows))
            write_phase_c_dimension_index_list(joinpath(dirname(output), "indices_dim$(dim).txt"), rows, dim)
        end
    end

    counts = phase_c_representability_counts()
    arm_counts = Dict(condition => count(row -> row.condition == condition, rows) for condition in unique(row.condition for row in rows))
    missing_expected_stage = count(system -> system[:expected_stage] === nothing, PHASE_C_SYSTEMS)
    println("manifest=$(output)")
    println("phase_c_fingerprint=$(phase_c_fingerprint())")
    println("regression_fingerprint=$(config_fingerprint())")
    println("rows=$(length(rows))")
    limit !== nothing && println("limit=$(limit)")
    println("unique_identities=$(unique_identities)")
    println("systems=$(length(PHASE_C_SYSTEMS))")
    println("expected_stage_missing=$(missing_expected_stage)")
    println("representability_exact=$(counts["exact"])")
    println("representability_surrogate=$(counts["surrogate"])")
    for condition in sort(collect(keys(arm_counts)))
        println("arm_$(condition)_rows=$(arm_counts[condition])")
    end
    println("basis_name=$(PHASE_C_BASIS_NAME)")
    println("max_fit_attempts=$(PHASE_C_MAX_FIT_ATTEMPTS)")
    if dimension !== nothing
        count_dim = count(row -> row.system_dim == dimension, rows)
        println("dimension=$(dimension)")
        println("dimension_rows=$(count_dim)")
        println("dimension_index_output=$(index_output)")
    elseif all_dimensions
        println("all_index_output=$(joinpath(dirname(output), "indices_all.txt"))")
        println("all_index_rows=$(length(rows))")
        println("cost_desc_index_output=$(joinpath(dirname(output), "indices_cost_desc.txt"))")
        println("cost_desc_index_rows=$(length(rows))")
        c1_c2_rows = _phase_c_condition_rows(rows, ("capped", "uncapped"))
        c3_rows = _phase_c_condition_rows(rows, ("pretune_on",))
        smoke_rows = phase_c_smoke_rows(rows)
        println("c1_c2_cost_desc_index_output=$(joinpath(dirname(output), "indices_c1_c2_cost_desc.txt"))")
        println("c1_c2_cost_desc_index_rows=$(length(c1_c2_rows))")
        println("c3_cost_desc_index_output=$(joinpath(dirname(output), "indices_c3_cost_desc.txt"))")
        println("c3_cost_desc_index_rows=$(length(c3_rows))")
        println("smoke_dim1_all_arms_index_output=$(joinpath(dirname(output), "indices_smoke_dim1_all_arms.txt"))")
        println("smoke_dim1_all_arms_index_rows=$(length(smoke_rows))")
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
