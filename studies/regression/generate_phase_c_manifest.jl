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

# WP-N18/P9 pilot selection is frozen before Phase-C data exist: cheapest exact
# Phase-B system per dimension class under the canonical support table, crossed
# with C-1/C-2, one predeclared seed, and both IC sets.
const PHASE_C_P9_PILOT_SYSTEM_IDS = Set([2, 24, 52, 63])
const PHASE_C_P9_PILOT_SEED = 42
const PHASE_C_P9_PILOT_CONDITIONS = Set(["capped", "uncapped"])
const PHASE_C_C6_SIGMAS = (0.0, 0.01, 0.02, 0.03, 0.04, 0.05)
const PHASE_C_C6_RHOS = (0.0, 0.5)

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

function _has_option(args::Vector{String}, name::String)
    return any(==(name), args)
end

function _phase_c_arm_variants(condition::String)
    return [variant for variant in PHASE_C_VARIANTS if String(variant.condition) == condition]
end

function phase_c_manifest_rows(; noise_sigma::Real = 0.0, subsample_rho::Real = 0.0,
                               noise_realization::Integer = 0, clamp_val::Real = BFGS_CLAMP_VAL,
                               campaign::AbstractString = PHASE_C_ID)
    fingerprint = phase_c_fingerprint(clamp_val = clamp_val)
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
                            campaign = String(campaign),
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
                            noise_sigma = Float64(noise_sigma),
                            subsample_rho = Float64(subsample_rho),
                            noise_realization = Int(noise_realization),
                            clamp_val = clamp_val_json(clamp_val),
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
                        campaign = String(campaign),
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
                        noise_sigma = Float64(noise_sigma),
                        subsample_rho = Float64(subsample_rho),
                        noise_realization = Int(noise_realization),
                        clamp_val = clamp_val_json(clamp_val),
                    ),
                )
                index += 1
            end
        end
    end
    return rows
end

function phase_c_c6_grid_conditions(; include_clean::Bool = false)
    conditions = NamedTuple[]
    for sigma in PHASE_C_C6_SIGMAS
        for rho in PHASE_C_C6_RHOS
            if !include_clean && sigma == 0.0 && rho == 0.0
                continue
            end
            push!(conditions, (noise_sigma = sigma, subsample_rho = rho))
        end
    end
    return conditions
end

function phase_c_c6_grid_rows(; clamp_val::Real = BFGS_CLAMP_VAL,
                              campaign::AbstractString = PHASE_C_ROBUSTNESS_ID)
    fingerprint = phase_c_fingerprint(clamp_val = clamp_val)
    rows = NamedTuple[]
    index = 1
    capped = only(_phase_c_arm_variants("capped"))
    systems = [system for system in sort(PHASE_C_SYSTEMS; by = s -> Int(s[:system_id])) if Int(system[:dim]) <= 2]
    conditions = phase_c_c6_grid_conditions()

    for system in systems
        for ic_set in PHASE_C_IC_SETS
            for (realization, seed) in enumerate(PHASE_C_SEEDS)
                for condition in conditions
                    push!(
                        rows,
                        (
                            index = index,
                            campaign = String(campaign),
                            config_fingerprint = fingerprint,
                            variant = String(capped.label),
                            condition = String(capped.condition),
                            use_pretuning = Bool(capped.use_pretuning),
                            basis_name = String(capped.basis_name),
                            max_fit_attempts = Int(capped.max_fit_attempts),
                            system_id = Int(system[:system_id]),
                            system_dim = Int(system[:dim]),
                            initial_condition_set = ic_set,
                            seed = seed,
                            representability = String(system[:representability]),
                            noise_sigma = Float64(condition.noise_sigma),
                            subsample_rho = Float64(condition.subsample_rho),
                            noise_realization = Int(realization),
                            clamp_val = clamp_val_json(clamp_val),
                        ),
                    )
                    index += 1
                end
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
        row.noise_sigma,
        row.subsample_rho,
        row.noise_realization,
        row.clamp_val,
    )
end

function phase_c_unique_identity_count(rows)
    return length(Set(phase_c_identity(row) for row in rows))
end

function write_phase_c_manifest(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "index,campaign,config_fingerprint,variant,condition,use_pretuning,basis_name,max_fit_attempts,system_id,system_dim,initial_condition_set,seed,representability,noise_sigma,subsample_rho,noise_realization,clamp_val")
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
                        row.noise_sigma,
                        row.subsample_rho,
                        row.noise_realization,
                        row.clamp_val,
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

function phase_c_p9_pilot_rows(rows)
    selected = [
        row for row in rows
        if row.system_id in PHASE_C_P9_PILOT_SYSTEM_IDS &&
           row.seed == PHASE_C_P9_PILOT_SEED &&
           row.condition in PHASE_C_P9_PILOT_CONDITIONS
    ]
    expected = length(PHASE_C_P9_PILOT_SYSTEM_IDS) * length(PHASE_C_IC_SETS) * length(PHASE_C_P9_PILOT_CONDITIONS)
    length(selected) == expected ||
        error("WP-N18/P9 pilot expected $(expected) rows, got $(length(selected))")
    return sort(selected; by = row -> row.index)
end

function write_phase_c_p9_pilot_index_list(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in phase_c_p9_pilot_rows(rows)
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

    c6_grid = _has_flag(args, "--c6-grid")
    dimension = _parse_optional_int(_arg_value(args, "--dimension"))
    limit = _parse_optional_int(_arg_value(args, "--limit"))
    noise_sigma = parse(Float64, something(_arg_value(args, "--noise-sigma"), "0"))
    subsample_rho = parse(Float64, something(_arg_value(args, "--subsample-rho"), "0"))
    noise_realization = parse(Int, something(_arg_value(args, "--noise-realization"), "0"))
    clamp_val = parse_clamp_val(something(_arg_value(args, "--clamp-val"), "10"))
    explicit_data_condition = any(_has_option(args, name) for name in ("--noise-sigma", "--subsample-rho", "--noise-realization", "--clamp-val"))
    campaign = c6_grid || explicit_data_condition || noise_sigma != 0.0 || subsample_rho != 0.0 || clamp_val != 10.0 ? PHASE_C_ROBUSTNESS_ID : PHASE_C_ID
    all_dimensions = _has_flag(args, "--all-dimensions")
    c6_grid && dimension !== nothing && error("Use either --c6-grid or --dimension, not both")
    dimension !== nothing && all_dimensions && error("Use either --dimension or --all-dimensions, not both")
    index_output = _arg_value(args, "--index-output")
    index_output !== nothing && all_dimensions && error("--index-output is only valid with --dimension")

    rows = if c6_grid
        base_rows = phase_c_c6_grid_rows(clamp_val = clamp_val, campaign = campaign)
        limit === nothing ? base_rows : base_rows[1:min(limit, length(base_rows))]
    else
        phase_c_limit_rows(phase_c_manifest_rows(
            noise_sigma = noise_sigma,
            subsample_rho = subsample_rho,
            noise_realization = noise_realization,
            clamp_val = clamp_val,
            campaign = campaign,
        ), limit)
    end
    unique_identities = phase_c_unique_identity_count(rows)
    unique_identities == length(rows) || error("Phase C manifest identities are not unique")
    write_phase_c_manifest(output, rows)

    if c6_grid
        write_phase_c_all_index_list(joinpath(dirname(output), "indices_all.txt"), rows)
        write_phase_c_cost_desc_index_list(joinpath(dirname(output), "indices_cost_desc.txt"), rows)
    elseif dimension !== nothing
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
        write_phase_c_p9_pilot_index_list(joinpath(dirname(output), "indices_p9_pilot_c1_c2.txt"), rows)
        for dim in sort(unique(row.system_dim for row in rows))
            write_phase_c_dimension_index_list(joinpath(dirname(output), "indices_dim$(dim).txt"), rows, dim)
        end
    end

    counts = phase_c_representability_counts()
    arm_counts = Dict(condition => count(row -> row.condition == condition, rows) for condition in unique(row.condition for row in rows))
    missing_expected_stage = count(system -> system[:expected_stage] === nothing, PHASE_C_SYSTEMS)
    println("manifest=$(output)")
    println("phase_c_fingerprint=$(phase_c_fingerprint(clamp_val = clamp_val))")
    println("campaign=$(campaign)")
    c6_grid && println("c6_grid=true")
    println("noise_sigma=$(noise_sigma)")
    println("subsample_rho=$(subsample_rho)")
    println("noise_realization=$(noise_realization)")
    println("clamp_val=$(clamp_val_json(clamp_val))")
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
    if c6_grid
        c6_systems = sort(unique(row.system_id for row in rows))
        c6_conditions = sort(unique((row.noise_sigma, row.subsample_rho) for row in rows))
        c6_realizations = sort(unique(row.noise_realization for row in rows))
        println("c6_systems=$(length(c6_systems))")
        println("c6_conditions=$(length(c6_conditions))")
        println("c6_realizations=$(join(c6_realizations, ","))")
        println("c6_seed_realization_pairs=$(join(["$(idx):$(seed)" for (idx, seed) in enumerate(PHASE_C_SEEDS)], ","))")
        println("all_index_output=$(joinpath(dirname(output), "indices_all.txt"))")
        println("all_index_rows=$(length(rows))")
        println("cost_desc_index_output=$(joinpath(dirname(output), "indices_cost_desc.txt"))")
        println("cost_desc_index_rows=$(length(rows))")
    elseif dimension !== nothing
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
        pilot_rows = phase_c_p9_pilot_rows(rows)
        println("p9_pilot_index_output=$(joinpath(dirname(output), "indices_p9_pilot_c1_c2.txt"))")
        println("p9_pilot_index_rows=$(length(pilot_rows))")
        println("p9_pilot_seed=$(PHASE_C_P9_PILOT_SEED)")
        println("p9_pilot_system_ids=$(join(sort(collect(PHASE_C_P9_PILOT_SYSTEM_IDS)), ","))")
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
