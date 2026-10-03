using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "generate_phase_c_manifest.jl"))

function _manifest_row(path::AbstractString, index::Int)
    lines = readlines(path)
    header = split(lines[1], ",")
    for line in lines[2:end]
        isempty(strip(line)) && continue
        values = split(line, ",")
        row = Dict(header .=> values)
        parse(Int, row["index"]) == index && return row
    end
    error("Manifest index $(index) not found in $(path)")
end

function _manifest_payload(row)
    keys = [
        "campaign",
        "config_fingerprint",
        "variant",
        "condition",
        "basis_name",
        "max_fit_attempts",
        "system_id",
        "system_dim",
        "initial_condition_set",
        "seed",
        "representability",
        "noise_sigma",
        "subsample_rho",
        "noise_realization",
        "clamp_val",
    ]
    return Dict(key => row[key] for key in keys)
end

@testset "WP-N42 C-6 grid manifest" begin
    rows = phase_c_c6_grid_rows()
    @test length(rows) == 3366
    @test all(row -> row.variant == "evogrow_v2_2_stage_capped", rows)
    @test all(row -> row.condition == "capped", rows)
    @test all(row -> row.system_dim <= 2, rows)
    @test length(unique(row.system_id for row in rows)) == 51
    @test length(unique((row.noise_sigma, row.subsample_rho) for row in rows)) == 11
    @test !any(row -> row.noise_sigma == 0.0 && row.subsample_rho == 0.0, rows)

    for (realization, seed) in enumerate(PHASE_C_SEEDS)
        matches = [
            row for row in rows
            if row.system_id == 1 &&
               row.initial_condition_set == 1 &&
               row.seed == seed &&
               row.noise_sigma == 0.01 &&
               row.subsample_rho == 0.0
        ]
        @test length(matches) == 1
        @test only(matches).noise_realization == realization
    end
end

@testset "WP-N42 C-6 control manifest row matches Stage 1" begin
    mktempdir() do dir
        output = joinpath(dir, "manifest.csv")
        rows = phase_c_c6_grid_rows()
        write_phase_c_manifest(output, rows)
        grid_row = only([
            row for row in rows
            if row.system_id == 1 &&
               row.initial_condition_set == 1 &&
               row.seed == first(PHASE_C_SEEDS) &&
               row.noise_sigma == 0.01 &&
               row.subsample_rho == 0.0 &&
               row.noise_realization == 1
        ])
        grid_csv_row = _manifest_row(output, grid_row.index)
        stage1_csv_row = _manifest_row(joinpath(@__DIR__, "..", "outputs", "stage1", "s0.01_r0", "manifest.csv"), 1)
        @test _manifest_payload(grid_csv_row) == _manifest_payload(stage1_csv_row)
    end
end
