if !isdefined(@__MODULE__, :PHASE_C_ID)
    include(joinpath(@__DIR__, "phase_c_config.jl"))
end
if !isdefined(@__MODULE__, :HASH_FORMAT)
    include(joinpath(@__DIR__, "phase_c_trajectory_hash_lib.jl"))
end

const WP_N25_PHASE_C_CAMPAIGN = PHASE_C_ID
const WP_N25_C1_VARIANT = "evogrow_v2_2_stage_capped"

function wp_n25_arg_value(args::Vector{String}, name::String, default)
    idx = findfirst(==(name), args)
    idx === nothing && return default
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function wp_n25_arg_flag(args::Vector{String}, name::String)
    return name in args
end

function wp_n25_phase_c_requested(args::Vector{String})
    campaign = wp_n25_arg_value(args, "--campaign", nothing)
    campaign === nothing && return false
    String(campaign) == WP_N25_PHASE_C_CAMPAIGN ||
        error("Unsupported --campaign $(campaign); expected $(WP_N25_PHASE_C_CAMPAIGN)")
    return true
end

function wp_n25_parse_limit(args::Vector{String}, n::Int)
    limit_value = wp_n25_arg_value(args, "--limit", nothing)
    limit = limit_value === nothing ? n : parse(Int, limit_value)
    limit >= 0 || error("--limit must be non-negative, got $(limit)")
    return min(limit, n)
end

function wp_n25_shard_options(args::Vector{String})
    shards = parse(Int, wp_n25_arg_value(args, "--shards", "1"))
    shard_index = parse(Int, wp_n25_arg_value(args, "--shard-index", "1"))
    shards >= 1 || error("--shards must be positive, got $(shards)")
    1 <= shard_index <= shards || error("--shard-index must be in 1:$(shards), got $(shard_index)")
    return shards, shard_index
end

function wp_n25_record_key(record)
    return @sprintf(
        "sys%04d_seed%d_ic%d",
        Int(_json_require(record, :system_id, "Phase-C cell key")),
        Int(_json_require(record, :seed, "Phase-C cell key")),
        Int(_json_require(record, :initial_condition_set, "Phase-C cell key")),
    )
end

function wp_n25_identity_tuple(record)
    return (
        String(_json_require(record, :git_hash, "Phase-C identity")),
        String(_json_require(record, :config_fingerprint, "Phase-C identity")),
        String(_json_require(record, :stage_cap_behavior_fingerprint, "Phase-C identity")),
    )
end

function wp_n25_counter_add!(counts::Dict{String, Int}, key::AbstractString)
    counts[String(key)] = get(counts, String(key), 0) + 1
    return nothing
end

function wp_n25_phase_c_filter(records; require_exact_support::Bool)
    selected = Any[]
    counts = Dict{String, Any}(
        "total_records" => length(records),
        "selected_c1_records" => 0,
        "skipped_non_c1_records" => 0,
        "skipped_surrogate_records" => 0,
        "non_c1_by_variant_and_pretuning" => Dict{String, Int}(),
        "representability_counts" => Dict{String, Int}(),
    )
    seen_keys = Set{String}()
    identities = Set{Tuple{String, String, String}}()
    for record in records
        variant = String(_json_require(record, :variant, "Phase-C arm filter"))
        use_pretuning = Bool(_json_require(record, :use_pretuning, "Phase-C arm filter"))
        if variant != WP_N25_C1_VARIANT || use_pretuning != false
            counts["skipped_non_c1_records"] += 1
            wp_n25_counter_add!(
                counts["non_c1_by_variant_and_pretuning"],
                "$(variant)|use_pretuning=$(use_pretuning)",
            )
            continue
        end
        key = wp_n25_record_key(record)
        key in seen_keys && error("Duplicate Phase-C C-1 cell: $(key)")
        push!(seen_keys, key)
        push!(identities, wp_n25_identity_tuple(record))
        representability = String(_json_require(record, :representability, "Phase-C representability"))
        wp_n25_counter_add!(counts["representability_counts"], representability)
        if require_exact_support && representability != "exact"
            counts["skipped_surrogate_records"] += 1
            continue
        end
        basis_name = String(_json_require(record, :basis_name, "Phase-C support basis check"))
        basis_name == PHASE_C_BASIS_NAME ||
            error("Record $(key) basis_name=$(basis_name), expected $(PHASE_C_BASIS_NAME)")
        push!(selected, record)
    end
    length(identities) <= 1 || error("Selected Phase-C C-1 records have mixed identity triples")
    counts["selected_c1_records"] = length(selected)
    counts["identity_triples"] = [collect(identity) for identity in sort(collect(identities))]
    sort!(selected; by = record -> wp_n25_record_key(record))
    return selected, counts
end

function wp_n25_shard_records(records, shards::Int, shard_index::Int)
    return [record for (idx, record) in enumerate(records) if mod(idx - 1, shards) + 1 == shard_index]
end

function wp_n25_shard_suffix(shards::Int, shard_index::Int)
    return @sprintf("shard_%03d_of_%03d", shard_index, shards)
end

function wp_n25_shard_path(output_dir::AbstractString, basename::AbstractString, shards::Int, shard_index::Int)
    return joinpath(output_dir, wp_n25_shard_suffix(shards, shard_index), basename)
end

function wp_n25_done_keys(path::AbstractString)
    isfile(path) || return Set{String}()
    keys = Set{String}()
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            row = JSON3.read(line)
            push!(keys, String(_json_require(row, :cell_key, "resume key")))
        end
    end
    return keys
end

function wp_n25_mutable_json(value)
    if value isa JSON3.Object || value isa AbstractDict
        return Dict{String, Any}(String(k) => wp_n25_mutable_json(v) for (k, v) in pairs(value))
    elseif value isa JSON3.Array || value isa AbstractVector
        return Any[wp_n25_mutable_json(v) for v in value]
    else
        return value
    end
end

function wp_n25_read_jsonl(path::AbstractString)
    rows = Dict{String, Any}[]
    isfile(path) || return rows
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            push!(rows, wp_n25_mutable_json(JSON3.read(line)))
        end
    end
    return rows
end

function wp_n25_collect_jsonl(output_dir::AbstractString, basename::AbstractString, shards::Int, expected_keys)
    rows = Dict{String, Any}[]
    seen = Set{String}()
    for shard_index in 1:shards
        path = wp_n25_shard_path(output_dir, basename, shards, shard_index)
        isfile(path) || error("Missing shard result file: $(path)")
        for row in wp_n25_read_jsonl(path)
            key = String(_json_require(row, :cell_key, "collect key"))
            key in seen && error("Duplicate collected cell $(key)")
            push!(seen, key)
            push!(rows, row)
        end
    end
    expected = Set(String[key for key in expected_keys])
    missing = sort(collect(setdiff(expected, seen)))
    extra = sort(collect(setdiff(seen, expected)))
    isempty(missing) || error("Missing collected cells: $(join(missing, ", "))")
    isempty(extra) || error("Unexpected collected cells: $(join(extra, ", "))")
    sort!(rows; by = row -> String(row["cell_key"]))
    return rows
end

function wp_n25_phase_c_systems_by_id()
    return Dict(Int(system[:system_id]) => system for system in phase_c_systems())
end

function wp_n25_trajectory_hash(system, ic_set::Int, traj::Trajectory)
    row = trajectory_hash_row(system, ic_set, traj)
    return Dict{String, Any}(
        "hash_format" => row["hash_format"],
        "time_axis_order" => row["time_axis_order"],
        "state_axis_order" => row["state_axis_order"],
        "time_shape" => row["time_shape"],
        "state_shape" => row["state_shape"],
        "time_sha256" => row["time_sha256"],
        "state_sha256" => row["state_sha256"],
    )
end

function wp_n25_phase_c_support_terms(record, support_table, dim::Int)
    system_id = Int(_json_require(record, :system_id, "Phase-C support"))
    haskey(support_table, system_id) || error("Phase-C support table missing system_id=$(system_id)")
    entry = support_table[system_id]
    String(entry.representability) == "exact" || return nothing
    support = entry.support
    support === nothing && return nothing
    length(support) == dim || error("Phase-C support for system $(system_id) has $(length(support)) equations, expected $(dim)")
    return [sort(unique(Int[x for x in eq])) for eq in support]
end

function wp_n25_loss_eval_seconds(record)
    key = wp_n25_record_key(record)
    elapsed_value = _json_get(record, :elapsed_s)
    elapsed_value === nothing && error("Record $(key) missing elapsed_s for cost estimate")
    total_time = Float64(elapsed_value)
    isfinite(total_time) && total_time > 0.0 ||
        error("Record $(key) has non-positive or non-finite elapsed_s")
    total_evals = Int(_json_require(record, :total_loss_evals, "cost estimate"))
    total_evals > 0 || error("Record $(key) has non-positive total_loss_evals")
    return total_time / total_evals
end

function wp_n25_estimate_rows(records, task_label::AbstractString, fits_per_cell::Int)
    rows = Dict{String, Any}[]
    for record in records
        system = phase_c_system(Int(_json_require(record, :system_id, "cost estimate")))
        dim = Int(system[:dim])
        loss_eval_s = wp_n25_loss_eval_seconds(record)
        bound_s = fits_per_cell * BFGS_MAX_LOSS_EVALS * loss_eval_s
        push!(rows, Dict{String, Any}(
            "task" => task_label,
            "cell_key" => wp_n25_record_key(record),
            "dimension" => dim,
            "system_id" => Int(_json_require(record, :system_id, "cost estimate")),
            "seed" => Int(_json_require(record, :seed, "cost estimate")),
            "initial_condition_set" => Int(_json_require(record, :initial_condition_set, "cost estimate")),
            "fits_per_cell" => fits_per_cell,
            "bfgs_max_loss_evals" => BFGS_MAX_LOSS_EVALS,
            "campaign_elapsed_s_per_loss_eval" => loss_eval_s,
            "planning_upper_bound_s" => bound_s,
        ))
    end
    return rows
end

function wp_n25_write_cost_estimate(rows)
    println("Planning cost estimate only; not runtime evidence.")
    println("Per-loss estimate source: elapsed_s / total_loss_evals for capacity planning only; not runtime evidence.")
    println("cell_key,dimension,fits_per_cell,bfgs_max_loss_evals,campaign_elapsed_s_per_loss_eval,planning_upper_bound_s")
    total = 0.0
    by_dim = Dict{Int, Vector{Float64}}()
    for row in rows
        total += Float64(row["planning_upper_bound_s"])
        dim = Int(row["dimension"])
        if !haskey(by_dim, dim)
            by_dim[dim] = Float64[]
        end
        push!(by_dim[dim], Float64(row["planning_upper_bound_s"]))
        println(join([
            row["cell_key"],
            row["dimension"],
            row["fits_per_cell"],
            row["bfgs_max_loss_evals"],
            row["campaign_elapsed_s_per_loss_eval"],
            row["planning_upper_bound_s"],
        ], ","))
    end
    println("dimension,n_cells,sum_planning_upper_bound_s,max_planning_upper_bound_s")
    for dim in sort(collect(keys(by_dim)))
        values = by_dim[dim]
        println(join([dim, length(values), sum(values), maximum(values)], ","))
    end
    if isempty(rows)
        println("total_planning_upper_bound_s=0")
        println("most_expensive_cell=")
    else
        expensive = rows[argmax(Float64[row["planning_upper_bound_s"] for row in rows])]
        println("total_planning_upper_bound_s=$(total)")
        println("most_expensive_cell=$(expensive["cell_key"]) planning_upper_bound_s=$(expensive["planning_upper_bound_s"])")
    end
    return nothing
end

function wp_n25_write_manifest(path::AbstractString, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON3.write(io, json_safe(payload))
        write(io, '\n')
    end
    return path
end
