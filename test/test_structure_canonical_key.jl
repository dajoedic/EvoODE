using Test

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

@testset "StructureSpec canonical support key" begin
    left = StructureSpec([[3, 1, 2], [4, 2]])
    right = StructureSpec([[2, 3, 1], [2, 4]])

    @test EvoODE._canonical_structure_key(left) == EvoODE._canonical_structure_key(right)
    @test hash(EvoODE._canonical_structure_key(left)) == hash(EvoODE._canonical_structure_key(right))

    eq_swapped = StructureSpec([[4, 2], [3, 1, 2]])
    @test EvoODE._canonical_structure_key(left) != EvoODE._canonical_structure_key(eq_swapped)

    same_support_a = EvoODE.Individual(StructureSpec([[1, 2], [3]]), [0.1, 0.2, 0.3], 1.0, 1.0)
    same_support_b = EvoODE.Individual(StructureSpec([[2, 1], [3]]), [9.0, 8.0, 7.0], 2.0, 2.0)
    @test EvoODE._canonical_structure_key(same_support_a.structure) ==
          EvoODE._canonical_structure_key(same_support_b.structure)
end

@testset "Structure duplicate stats" begin
    counter = Dict{Any, Int}()

    EvoODE._record_structure_evaluation!(counter, StructureSpec([[1, 2], [3]]))
    EvoODE._record_structure_evaluation!(counter, StructureSpec([[2, 1], [3]]))
    EvoODE._record_structure_evaluation!(counter, StructureSpec([[1], [2, 3]]))

    stats = EvoODE._structure_duplicate_stats(counter)
    @test stats.total_evaluated == 3
    @test stats.unique_structures == 2
    @test stats.duplicate_evaluations == 1
    @test stats.repeat_histogram == Dict("1" => 1, "2" => 1)
    @test stats.repeat_quantiles.q100 == 2
end
