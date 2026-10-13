using Test
using Random

include(joinpath(@__DIR__, "..", "studies", "regression", "run_regression.jl"))
include(joinpath(@__DIR__, "..", "studies", "regression", "phase_c_config.jl"))
include(joinpath(@__DIR__, "..", "studies", "regression", "paper2_t2a_pilot_v1.jl"))

@testset "CandidatePrior validation" begin
    @test_throws ErrorException CandidatePrior([[1, 1, 2]])
    @test_throws ErrorException CandidatePrior([[1, 2, 3], [1, 2]])
    @test_throws ErrorException CandidatePrior([[1, 2, 3]]; epsilon = -0.1)
    @test_throws ErrorException CandidatePrior([[1, 2, 3]]; mapping = "linear")

    prior = CandidatePrior([[2, 1, 3], [1, 3, 2]]; arm = "guided_prior")
    @test prior.epsilon == 0.2
    @test prior.rank_by_equation[1][2] == 1
end

@testset "CandidatePrior weighted draw" begin
    prior = CandidatePrior([[1, 2, 3, 4]]; epsilon = 0.2, arm = "oracle_prior")
    candidates = [1, 3, 4]
    weights = [1.0, 1 / 3, 1 / 4]
    z = sum(weights)
    expected = Dict(candidates[i] => 0.8 * weights[i] / z + 0.2 / length(candidates) for i in eachindex(candidates))
    counts = Dict(term => 0 for term in candidates)

    Random.seed!(12345)
    n = 80_000
    for _ in 1:n
        term = candidate_prior_draw(prior, 1, candidates)
        @test term in candidates
        counts[term] += 1
    end

    for term in candidates
        @test abs(counts[term] / n - expected[term]) < 0.01
    end
end

@testset "CandidatePrior epsilon one is uniform over current candidates" begin
    prior = CandidatePrior([[1, 2, 3, 4]]; epsilon = 1.0)
    candidates = [2, 4]
    counts = Dict(term => 0 for term in candidates)

    Random.seed!(20261013)
    n = 40_000
    for _ in 1:n
        term = candidate_prior_draw(prior, 1, candidates)
        @test term in candidates
        counts[term] += 1
    end

    @test abs(counts[2] / n - 0.5) < 0.015
    @test abs(counts[4] / n - 0.5) < 0.015
end

@testset "Phase C fingerprint remains unchanged without prior and prior payload changes identity" begin
    @test phase_c_fingerprint() == "0c9672de35c75a9d"
    prior_a = CandidatePrior([[1, 2, 3, 4, 5, 6]]; arm = "guided_prior", source_hash = "a")
    prior_b = CandidatePrior([[2, 1, 3, 4, 5, 6]]; arm = "guided_prior", source_hash = "a")
    payload_a = canonical_value((base_phase_c_config_fingerprint = phase_c_fingerprint(), candidate_prior = candidate_prior_payload(prior_a)))
    payload_b = canonical_value((base_phase_c_config_fingerprint = phase_c_fingerprint(), candidate_prior = candidate_prior_payload(prior_b)))
    @test payload_a != payload_b
end

function _t2a_test_manifest_row(path::AbstractString, predicate)
    lines = readlines(path)
    header = split(lines[1], ",")
    for line in lines[2:end]
        isempty(strip(line)) && continue
        values = split(line, ",")
        row = Dict(header .=> values)
        predicate(row) && return row
    end
    error("No matching T2a manifest row found in $(path)")
end

@testset "T2a manifest prior paths are portable" begin
    rows = t2a_manifest_rows()
    @test all(row -> !isabspath(row.candidate_prior_path), rows)
    @test all(row -> occursin('/', row.candidate_prior_path), rows)
    @test all(row -> !occursin('\\', row.candidate_prior_path), rows)

    mktempdir() do dir
        repo_dir = joinpath(dir, "repo")
        copied_dir = joinpath(dir, "copied")
        mkpath(repo_dir)
        mkpath(copied_dir)
        cp(PAPER2_T2A_PRIOR_DIR, joinpath(repo_dir, "priors"))
        cp(PAPER2_T2A_PRIOR_DIR, joinpath(copied_dir, "priors"))

        repo_manifest = joinpath(repo_dir, "manifest.csv")
        copied_manifest = joinpath(copied_dir, "manifest.csv")
        write_t2a_manifest(repo_manifest, rows)
        cp(repo_manifest, copied_manifest)

        row = _t2a_test_manifest_row(repo_manifest) do row
            row["candidate_prior_arm"] == "oracle_prior" &&
                parse(Int, row["system_id"]) == 24 &&
                parse(Int, row["seed"]) == 42 &&
                parse(Int, row["initial_condition_set"]) == 1
        end
        target_index = row["index"]
        copied_row = _t2a_test_manifest_row(copied_manifest) do row
            row["index"] == target_index &&
                row["candidate_prior_arm"] == "oracle_prior" &&
                parse(Int, row["system_id"]) == 24 &&
                parse(Int, row["seed"]) == 42 &&
                parse(Int, row["initial_condition_set"]) == 1
        end

        resolved = resolve_t2a_candidate_prior_path(row["candidate_prior_path"], dirname(repo_manifest))
        @test isfile(resolved)
        @test t2a_fingerprint_from_row(row, dirname(repo_manifest)) == "52edf2893b9d9e70"
        @test t2a_fingerprint_from_row(copied_row, dirname(copied_manifest)) == t2a_fingerprint_from_row(row, dirname(repo_manifest))

        absolute_row = copy(row)
        absolute_row["candidate_prior_path"] = abspath(resolved)
        @test_throws ErrorException t2a_fingerprint_from_row(absolute_row, dirname(repo_manifest))

        windows_absolute_row = copy(row)
        windows_absolute_row["candidate_prior_path"] = "C:\\stale\\prior.json"
        @test_throws ErrorException t2a_fingerprint_from_row(windows_absolute_row, dirname(repo_manifest))
    end
end
