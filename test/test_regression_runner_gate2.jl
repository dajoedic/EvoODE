using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "run_regression.jl"))

function _with_env(f::Function, updates::Dict{String, String})
    old = Dict{String, Union{Nothing, String}}()
    for (key, value) in updates
        old[key] = haskey(ENV, key) ? ENV[key] : nothing
        ENV[key] = value
    end
    try
        return f()
    finally
        for (key, value) in old
            if value === nothing
                delete!(ENV, key)
            else
                ENV[key] = value
            end
        end
    end
end

@testset "Gate 2 regression runner selection" begin
    @test [String(v.label) for v in VARIANTS] == ["evogrow_v2_2_stage_local", "evogrow_v3", "evogrow_v3_stage_capped"]
    @test BFGS_TIME_LIMIT_S == 1800.0
    @test FINGERPRINT_VARIANT_LABELS == [
        "evogrow_v2_2_stage_local",
        "evogrow_screening_derivative",
        "evogrow_v3",
        "evogrow_v3_stage_capped",
    ]

    selected = _with_env(
        Dict(
            "EVO_REGRESSION_VARIANT" => "evogrow_v3_stage_capped",
            "EVO_REGRESSION_SYSTEM_ID" => "3",
            "EVO_REGRESSION_SEED" => "42",
        )
    ) do
        return (
            variants = [String(v.label) for v in selected_variants()],
            systems = [Int(s[:system_id]) for s in selected_systems()],
            seeds = selected_seeds(),
        )
    end

    @test selected.variants == ["evogrow_v3_stage_capped"]
    @test selected.systems == [3]
    @test selected.seeds == [42]
end
