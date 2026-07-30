using Test

include(joinpath(@__DIR__, "..", "studies", "gate2_do_or_die", "readout.jl"))

function _record(; eq_final_stages, support_terms, loss = 5e-4)
    return Dict{String, Any}(
        "variant" => "evogrow_v3",
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
        eq_final_stages = [3, 5],
        support_terms = [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]],
    ))
    @test passing["verdict"] == "PASS"
    @test all(values(passing["criteria"]))

    stage_fail = evaluate_gate2_record(_record(
        eq_final_stages = [5, 5],
        support_terms = [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]],
    ))
    @test stage_fail["verdict"] == "PARTIAL"
    @test stage_fail["criteria"]["a_du1_stage3_no_overshoot"] == false
    @test stage_fail["criteria"]["b_du1_support_exact"] == true
    @test stage_fail["criteria"]["c_loss_not_worse_than_anchor"] == true

    support_fail = evaluate_gate2_record(_record(
        eq_final_stages = [3, 5],
        support_terms = [["u1", "u1^2"], ["u2", "u1*u2", "u2^2"]],
    ))
    @test support_fail["verdict"] == "FAIL"
    @test support_fail["criteria"]["a_du1_stage3_no_overshoot"] == true
    @test support_fail["criteria"]["b_du1_support_exact"] == false
end
