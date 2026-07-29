using Test
using Random

include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE

function _term_stage_map(basis)
    stages = Dict{Int, Int}()
    for (stage, group) in pairs(basis.term_groups)
        for term_idx in group
            stages[term_idx] = stage
        end
    end
    return stages
end

@testset "EvoGrowV3 equation-aware child generation" begin
    basis = default_staged_polynomial_basis(2)
    stages = _term_stage_map(basis)
    cross_idx = only([i for i in 1:basis_num_terms(basis) if basis_term_name(basis, i) == "u1*u2"])

    allowed_by_eq, current_by_eq = EvoODE._evogrow_v3_equation_terms(basis, [1, 3])

    @test all(stages[t] <= 1 for t in allowed_by_eq[1])
    @test all(stages[t] <= 3 for t in allowed_by_eq[2])
    @test !(cross_idx in allowed_by_eq[1])
    @test !(cross_idx in allowed_by_eq[2])

    parent = EvoODE.Individual(StructureSpec([Int[], Int[]]), Float64[], Inf, Inf)
    Random.seed!(42)
    children = EvoODE._expand_equation_aware_with_usage_policy(
        parent,
        2,
        basis,
        [1, 3],
        EvoODE._allowed_terms(basis, 3),
        EvoODE._current_stage_terms(basis, 3),
        StageUsagePolicy(mode = :hard);
        n_children = 200,
        max_terms_per_eq = 5
    )

    for child in children
        @test all(t in allowed_by_eq[1] for t in child.structure.active_idxs[1])
        @test all(t in allowed_by_eq[2] for t in child.structure.active_idxs[2])
        @test all(stages[t] <= 1 for t in child.structure.active_idxs[1])
        @test !(cross_idx in child.structure.active_idxs[1])
        @test !(cross_idx in child.structure.active_idxs[2])
    end

    uniform_allowed_by_eq, uniform_current_by_eq =
        EvoODE._evogrow_v3_equation_terms(basis, [3, 3])

    @test uniform_allowed_by_eq[1] == EvoODE._allowed_terms(basis, 3)
    @test uniform_allowed_by_eq[2] == EvoODE._allowed_terms(basis, 3)
    @test uniform_current_by_eq[1] == EvoODE._current_stage_terms(basis, 3)
    @test uniform_current_by_eq[2] == EvoODE._current_stage_terms(basis, 3)

    uniform_parent = EvoODE.Individual(StructureSpec([[1], [2]]), Float64[], Inf, Inf)
    allowed_terms = EvoODE._allowed_terms(basis, 3)
    current_stage_terms = EvoODE._current_stage_terms(basis, 3)

    Random.seed!(123)
    expected_children = EvoODE._expand_with_usage_policy(
        uniform_parent,
        2,
        allowed_terms,
        current_stage_terms,
        StageUsagePolicy(mode = :hard);
        n_children = 25,
        max_terms_per_eq = 5
    )

    Random.seed!(123)
    delegated_children = EvoODE._expand_equation_aware_with_usage_policy(
        uniform_parent,
        2,
        basis,
        [3, 3],
        allowed_terms,
        current_stage_terms,
        StageUsagePolicy(mode = :hard);
        n_children = 25,
        max_terms_per_eq = 5
    )

    @test [child.structure.active_idxs for child in delegated_children] ==
          [child.structure.active_idxs for child in expected_children]
end
