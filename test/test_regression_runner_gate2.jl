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
    # Historical Gate-2 freeze. The values below moved deliberately after Gate 2:
    # evogrow_v2_2_stage_capped became the Paper 1 variant (2026-08-03),
    # WP-B3/D2 replaced the BFGS time limit with an evaluation budget (Inf),
    # and WP-C2 widened the look-ahead horizon to the depth of the staged basis.
    @test [String(v.label) for v in VARIANTS] == [
        "evogrow_v2_2_stage_local",
        "evogrow_v3",
        "evogrow_v2_2_stage_capped",
        "evogrow_v3_stage_capped",
    ]
    @test BFGS_TIME_LIMIT_S == Inf
    @test FINGERPRINT_VARIANT_LABELS == [
        "evogrow_v2_2_stage_local",
        "evogrow_screening_derivative",
        "evogrow_v3",
        "evogrow_v3_stage_capped",
    ]
    @test LOOKAHEAD_CAP_POLICY.aggregation == :majority_no_undecided_at_or_below
    @test LOOKAHEAD_CAP_POLICY.lookahead_horizon == 5

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

    fingerprint = config_fingerprint()
    @test fingerprint != "3f9be6d36c4043de"
end
