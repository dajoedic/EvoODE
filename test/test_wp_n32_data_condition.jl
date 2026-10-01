using Test
using JSON3
using Random

include(joinpath(@__DIR__, "..", "studies", "regression", "run_regression.jl"))
include(joinpath(@__DIR__, "..", "studies", "regression", "phase_c_config.jl"))

function _mutable_json(value)
    if value isa JSON3.Object || value isa AbstractDict
        return Dict{String, Any}(String(k) => _mutable_json(v) for (k, v) in pairs(value))
    elseif value isa JSON3.Array || value isa AbstractVector
        return Any[_mutable_json(v) for v in value]
    else
        return value
    end
end

function _real_phase_c_record()
    task_dir = joinpath(@__DIR__, "..", "outputs", "phase_c_dryrun_2026-09-25", "tasks")
    files = sort([joinpath(task_dir, name) for name in readdir(task_dir) if startswith(name, "cell_") && endswith(name, ".jsonl") && !endswith(name, ".heartbeat.jsonl")])
    isempty(files) && error("Need a real Phase-C record under $(task_dir)")
    return _mutable_json(JSON3.read(readline(first(files))))
end

@testset "WP-N32 data condition identity and determinism" begin
    traj = Trajectory([0.0, 1.0, 2.0, 3.0], reshape(collect(1.0:8.0), 4, 2))

    identity = apply_phase_c_data_condition(traj, 1, 1, 0.0, 0.0, 0)
    @test identity === traj
    @test identity.t == traj.t
    @test identity.x == traj.x

    Random.seed!(1234)
    first_draw = apply_phase_c_data_condition(traj, 1, 1, 0.05, 0.25, 1)
    Random.seed!(9876)
    second_draw = apply_phase_c_data_condition(traj, 1, 1, 0.05, 0.25, 1)
    other_realization = apply_phase_c_data_condition(traj, 1, 1, 0.05, 0.25, 2)
    @test first_draw.t == second_draw.t
    @test first_draw.x == second_draw.x
    @test first_draw.t != other_realization.t || first_draw.x != other_realization.x
end

@testset "WP-N32 relative noise and subsampling" begin
    traj = Trajectory(collect(0.0:5.0), reshape(collect(1.0:12.0), 6, 2))
    noisy = apply_phase_c_data_condition(traj, 2, 1, 0.10, 0.0, 7)
    ratio = (noisy.x .- traj.x) ./ traj.x
    @test size(ratio) == size(traj.x)
    @test any(!=(0.0), ratio)

    thinned = apply_phase_c_data_condition(traj, 2, 1, 0.0, 0.5, 7)
    @test length(thinned.t) == length(traj.t) - floor(Int, length(traj.t) * 0.5)
    @test issorted(thinned.t)
    @test length(unique(thinned.t)) == length(thinned.t)
end

@testset "WP-N32 fingerprints and Inf JSON" begin
    @test phase_c_fingerprint() == "0c9672de35c75a9d"
    @test phase_c_fingerprint(clamp_val = 10.0) == "0c9672de35c75a9d"
    @test phase_c_fingerprint(clamp_val = 1000.0) != "0c9672de35c75a9d"
    @test data_condition_fingerprint(0.0, 0.0, 0) == data_condition_fingerprint(0.0, 0.0, 0)
    @test clamp_val_json(Inf) == "Inf"
    @test parse_clamp_val("Inf") == Inf
    encoded = JSON3.write(json_safe(Dict("clamp_val" => clamp_val_json(Inf))))
    @test _mutable_json(JSON3.read(encoded))["clamp_val"] == "Inf"
end

@testset "WP-N32 record fields from real Phase-C fixture" begin
    fixture = _real_phase_c_record()
    for field in ("loss", "support_terms", "model_terms", "total_loss_evals", "stage_caps")
        @test haskey(fixture, field)
    end
    for field in ("noise_sigma", "subsample_rho", "noise_realization", "noise_model",
                  "data_condition_fingerprint", "observed_data_sha256",
                  "n_observed_points", "clamp_val")
        fixture[field] = field == "noise_model" ? DATA_CONDITION_NOISE_MODEL : "fixture"
        @test haskey(fixture, field)
    end
end
