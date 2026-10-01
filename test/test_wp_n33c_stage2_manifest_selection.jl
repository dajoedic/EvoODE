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
