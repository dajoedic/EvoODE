using Test

include(joinpath(@__DIR__, "..", "studies", "gate2_do_or_die", "readout.jl"))

function _record(; eq_final_stages, support_terms, loss = 5e-4)
    return Dict{String, Any}(
        "variant" => "evogrow_v3_stage_capped",
        "config_fingerprint" => "test",
        "system_id" => 26,
        "seed" => 42,
        "loss" => loss,
        "final_stage" => maximum(eq_final_stages),
        "eq_final_stages" => eq_final_stages,
        "eq_overshoot" => [max(0, s - 3) for s in eq_final_stages],
        "eq_wasted_levels" => [0, 0],
        "support_terms" => support_terms,
        "error" => nothing,
    )
end

@testset "Gate 2 do-or-die readout criteria" begin
    passing = evaluate_gate2_record(_record(
        eq_final_stages = [3, 3],
        support_terms = [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]],
    ))
    @test passing["verdict"] == "REPORTABLE"
    @test passing["checks"]["construction_eq_final_stages_match_cap"] == true
    @test passing["checks"]["du2_support_exact"] == true

    stage_fail = evaluate_gate2_record(_record(
        eq_final_stages = [5, 5],
        support_terms = [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]],
    ))
    @test stage_fail["verdict"] == "IMPLEMENTATION_CHECK_FAILED"
    @test stage_fail["checks"]["construction_eq_final_stages_match_cap"] == false
    @test stage_fail["checks"]["du1_support_exact"] == true

    support_fail = evaluate_gate2_record(_record(
        eq_final_stages = [3, 3],
        support_terms = [["u1", "u1^2"], ["u2", "u1*u2", "u2^2"]],
    ))
    @test support_fail["verdict"] == "REPORTABLE"
    @test support_fail["checks"]["construction_eq_final_stages_match_cap"] == true
    @test support_fail["checks"]["du1_support_exact"] == false
end
