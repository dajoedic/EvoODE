using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "export_phase_c_data_conditions.jl"))

@testset "Phase-C export index CSV quoting" begin
    @test _csv_field("plain") == "plain"
    @test _csv_field("[512,1]") == "\"[512,1]\""
    @test _csv_field("a\"b") == "\"a\"\"b\""
    @test _csv_field("a\nb") == "\"a\nb\""

    mktempdir() do dir
        path = joinpath(dir, "index.csv")
        _write_index(
            path,
            [
                Dict{String, String}(
                    "system_id" => "1",
                    "initial_condition_set" => "1",
                    "dimension" => "1",
                    "time_shape" => "[512]",
                    "state_shape" => "[512,1]",
                    "time_sha256" => repeat("a", 64),
                    "state_sha256" => repeat("b", 64),
                ),
            ],
        )
        lines = readlines(path)
        @test length(split(lines[1], ",")) == 25
        @test occursin("[512],\"[512,1]\"", lines[2])
    end
end
