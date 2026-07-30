using Test

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

@testset "EvoGrowV3 per-equation overshoot metrics" begin
    @test eq_overshoot([3, 1], 3) == [0, 0]
    @test eq_overshoot([5, 4], 3) == [2, 1]
    @test eq_overshoot([2, 1], 3) == [0, 0]

    histories = [[1, 1, 2, 3, 4], [1, 1, 1, 1, 1]]
    @test eq_wasted_levels(histories, 2) == [2, 0]

    eq_final_stages = [2, 5, 4]
    expected_stage = 3
    @test maximum(eq_overshoot(eq_final_stages, expected_stage)) ==
          max(0, maximum(eq_final_stages) - expected_stage)
end
