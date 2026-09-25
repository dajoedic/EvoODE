using Test
using JSON3

include(joinpath(@__DIR__, "..", "studies", "regression", "wp_n3_oracle_refit.jl"))

module WP_N25LoadWP_N4
include(joinpath(@__DIR__, "..", "studies", "regression", "wp_n4_multistart_refit.jl"))
end

module WP_N25LoadWP_N5
include(joinpath(@__DIR__, "..", "studies", "regression", "wp_n5_ic_generalization.jl"))
end

module WP_N25LoadTrajectoryHashes
include(joinpath(@__DIR__, "..", "studies", "regression", "phase_c_trajectory_hashes.jl"))
end

@testset "WP-N25 script load paths" begin
    @test isdefined(@__MODULE__, :wp_n25_phase_c_filter)
    @test isdefined(WP_N25LoadWP_N4, :wp_n25_phase_c_filter)
    @test isdefined(WP_N25LoadWP_N5, :wp_n25_phase_c_filter)
    @test isdefined(WP_N25LoadTrajectoryHashes, :trajectory_hash_row)
end

function mutable_json(value)
    if value isa JSON3.Object || value isa AbstractDict
        return Dict{String, Any}(String(k) => mutable_json(v) for (k, v) in pairs(value))
    elseif value isa JSON3.Array || value isa AbstractVector
        return Any[mutable_json(v) for v in value]
    else
        return value
    end
end

function real_phase_c_records(n::Int)
    task_dir = joinpath(@__DIR__, "..", "outputs", "phase_c_dryrun_2026-09-25", "tasks")
    files = sort([joinpath(task_dir, name) for name in readdir(task_dir) if startswith(name, "cell_") && endswith(name, ".jsonl") && !endswith(name, ".heartbeat.jsonl")])
    records = Dict{String, Any}[]
    for path in files
        isempty(strip(read(path, String))) && continue
        push!(records, mutable_json(JSON3.read(readline(path))))
        length(records) >= n && break
    end
    length(records) >= n || error("Need $(n) real Phase-C records under $(task_dir)")
    return records
end

@testset "WP-N25 Phase-C arm filter and counting" begin
    records = real_phase_c_records(3)
    selected, counts = wp_n25_phase_c_filter(records; require_exact_support = true)
    @test length(selected) == 2
    @test counts["total_records"] == 3
    @test counts["selected_c1_records"] == 2
    @test counts["skipped_non_c1_records"] == 1
    @test counts["non_c1_by_variant_and_pretuning"]["evogrow_v2_2_stage_local|use_pretuning=false"] == 1
end

@testset "WP-N25 Phase-C rejects mixed identities and duplicate cells" begin
    records = real_phase_c_records(1)
    mixed = [mutable_json(records[1]), mutable_json(records[1])]
    mixed[2]["seed"] = 999_001
    mixed[2]["git_hash"] = "different"
    @test_throws ErrorException wp_n25_phase_c_filter(mixed; require_exact_support = true)

    duplicate = [mutable_json(records[1]), mutable_json(records[1])]
    @test_throws ErrorException wp_n25_phase_c_filter(duplicate; require_exact_support = true)
end

@testset "WP-N25 deterministic sharding and collect completeness" begin
    records = real_phase_c_records(5)
    selected, _ = wp_n25_phase_c_filter(records; require_exact_support = true)
    selected = selected[1:min(3, length(selected))]
    shard1 = wp_n25_shard_records(selected, 2, 1)
    shard2 = wp_n25_shard_records(selected, 2, 2)
    @test sort(vcat([wp_n25_record_key(r) for r in shard1], [wp_n25_record_key(r) for r in shard2])) == sort([wp_n25_record_key(r) for r in selected])

    tmp = mktempdir()
    mkpath(dirname(wp_n25_shard_path(tmp, "results.jsonl", 2, 1)))
    open(wp_n25_shard_path(tmp, "results.jsonl", 2, 1), "w") do io
        JSON3.write(io, Dict("cell_key" => wp_n25_record_key(first(selected))))
        write(io, '\n')
    end
    @test_throws ErrorException wp_n25_collect_jsonl(tmp, "results.jsonl", 2, [wp_n25_record_key(r) for r in selected])
end

@testset "WP-N25 support basis check" begin
    record = first(real_phase_c_records(1))
    support_table = load_phase_c_support()
    system = phase_c_system(Int(record["system_id"]))
    support = wp_n25_phase_c_support_terms(record, support_table, Int(system[:dim]))
    @test support !== nothing
    broken = mutable_json(record)
    broken["basis_name"] = "default_staged_polynomial_basis"
    @test_throws ErrorException wp_n25_phase_c_filter([broken]; require_exact_support = true)
end
