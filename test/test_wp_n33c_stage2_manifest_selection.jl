using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "select_phase_c_stage2_manifest.jl"))

@testset "WP-N33c Stage-2 manifest selection" begin
    tmp = mktempdir()
    source_a = joinpath(tmp, "sigma_0p01_rho_0", "manifest.csv")
    source_b = joinpath(tmp, "sigma_0p05_rho_0p5", "manifest.csv")
    mkpath(dirname(source_a))
    mkpath(dirname(source_b))

    header = "index,campaign,variant,condition,system_id,initial_condition_set,seed,noise_sigma,subsample_rho,noise_realization,clamp_val"
    write(
        source_a,
        join(
            [
                header,
                "1,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,1,1,42,0.01,0,1,10",
                "2,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,18,1,42,0.01,0,1,10",
                "3,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,24,1,42,0.01,0,1,10",
                "4,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_uncapped,uncapped,18,1,42,0.01,0,1,10",
                "",
            ],
            "\n",
        ),
    )
    write(
        source_b,
        join(
            [
                header,
                "1,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,18,1,42,0.05,0.5,1,10",
                "2,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,24,1,42,0.05,0.5,1,10",
                "",
            ],
            "\n",
        ),
    )

    stage2_output = joinpath(tmp, "manifest.csv")
    stage2_indices = joinpath(tmp, "indices_stage2.txt")
    smoke_output = joinpath(tmp, "smoke_manifest.csv")
    smoke_indices = joinpath(tmp, "indices_smoke.txt")

    main([
        "--source", source_a,
        "--source", source_b,
        "--stage2-output", stage2_output,
        "--stage2-indices", stage2_indices,
        "--smoke-output", smoke_output,
        "--smoke-indices", smoke_indices,
        "--stage2-systems", "18,24",
        "--smoke-system", "1",
    ])

    _, stage2_rows = read_manifest(stage2_output)
    _, smoke_rows = read_manifest(smoke_output)

    @test [row["index"] for row in stage2_rows] == ["1", "2", "3", "4"]
    @test [row["system_id"] for row in stage2_rows] == ["18", "18", "24", "24"]
    @test [row["noise_sigma"] for row in stage2_rows] == ["0.01", "0.05", "0.01", "0.05"]
    @test [row["subsample_rho"] for row in stage2_rows] == ["0", "0.5", "0", "0.5"]
    @test read(stage2_indices, String) == "1\n2\n3\n4\n"
    @test length(smoke_rows) == 1
    @test smoke_rows[1]["index"] == "1"
    @test smoke_rows[1]["system_id"] == "1"
    @test read(smoke_indices, String) == "1\n"
end

@testset "WP-N41 explicit multi-IC and clamp selection" begin
    tmp = mktempdir()
    source_1000 = joinpath(tmp, "bound_1000", "manifest.csv")
    source_inf = joinpath(tmp, "bound_Inf", "manifest.csv")
    mkpath(dirname(source_1000))
    mkpath(dirname(source_inf))

    header = "index,campaign,variant,condition,system_id,initial_condition_set,seed,noise_sigma,subsample_rho,noise_realization,clamp_val"
    write(
        source_1000,
        join(
            [
                header,
                "1,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,1,1,42,0.0,0.0,0,1000",
                "2,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,24,1,42,0.0,0.0,0,1000",
                "3,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,52,1,42,0.0,0.0,0,1000",
                "4,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,52,2,42,0.0,0.0,0,1000",
                "5,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,57,1,42,0.0,0.0,0,1000",
                "6,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,57,2,42,0.0,0.0,0,1000",
                "",
            ],
            "\n",
        ),
    )
    write(
        source_inf,
        join(
            [
                header,
                "1,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,24,1,42,0.0,0.0,0,Inf",
                "2,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,24,2,42,0.0,0.0,0,Inf",
                "3,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,52,1,42,0.0,0.0,0,Inf",
                "4,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,52,2,42,0.0,0.0,0,Inf",
                "5,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,57,1,42,0.0,0.0,0,Inf",
                "6,paper1_phaseC_robustness_v1,evogrow_v2_2_stage_capped,capped,57,2,42,0.0,0.0,0,Inf",
                "",
            ],
            "\n",
        ),
    )

    stage2_output = joinpath(tmp, "manifest.csv")
    stage2_indices = joinpath(tmp, "indices_stage2.txt")
    smoke_output = joinpath(tmp, "smoke_manifest.csv")
    smoke_indices = joinpath(tmp, "indices_smoke.txt")

    main([
        "--source", source_1000,
        "--source", source_inf,
        "--stage2-output", stage2_output,
        "--stage2-indices", stage2_indices,
        "--smoke-output", smoke_output,
        "--smoke-indices", smoke_indices,
        "--stage2-cells", "24:1:Inf,24:2:Inf,52:1:1000,52:2:1000,52:1:Inf,52:2:Inf,57:1:1000,57:2:1000,57:1:Inf,57:2:Inf",
        "--smoke-system", "1",
    ])

    _, stage2_rows = read_manifest(stage2_output)
    _, smoke_rows = read_manifest(smoke_output)

    @test [row["index"] for row in stage2_rows] == string.(1:10)
    @test [(row["system_id"], row["initial_condition_set"], row["clamp_val"]) for row in stage2_rows] == [
        ("24", "1", "Inf"),
        ("24", "2", "Inf"),
        ("52", "1", "1000"),
        ("52", "2", "1000"),
        ("52", "1", "Inf"),
        ("52", "2", "Inf"),
        ("57", "1", "1000"),
        ("57", "2", "1000"),
        ("57", "1", "Inf"),
        ("57", "2", "Inf"),
    ]
    @test read(stage2_indices, String) == join(string.(1:10), "\n") * "\n"
    @test length(smoke_rows) == 1
    @test smoke_rows[1]["system_id"] == "1"
    @test smoke_rows[1]["clamp_val"] == "1000"
    @test read(smoke_indices, String) == "1\n"
end
