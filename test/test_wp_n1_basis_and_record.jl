using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "run_regression.jl"))
using .EvoODE

@testset "WP-N1 constant staged basis" begin
    old = default_staged_polynomial_basis(2)
    new = staged_polynomial_basis_with_constant(2)

    @test basis_num_terms(old) == 11
    @test basis_num_terms(new) == 12
    @test basis_term_name.(Ref(old), 1:basis_num_terms(old)) == [
        "u1", "u2", "u1^2", "u2^2", "u1*u2", "u1^3", "u2^3", "sin(u1)", "cos(u1)", "sin(u2)", "cos(u2)"
    ]
    @test basis_term_name.(Ref(new), 1:basis_num_terms(new)) == [
        "1", "u1", "u2", "u1^2", "u2^2", "u1*u2", "u1^3", "u2^3", "sin(u1)", "cos(u1)", "sin(u2)", "cos(u2)"
    ]
    @test new.term_groups[1] == [1, 2, 3]
    @test basis_term_func(new, 1)([3.0, 4.0], 0.0) == 1.0
end

@testset "WP-N1 record model terms preserve coefficients" begin
    basis = staged_polynomial_basis_with_constant(1)
    structure = StructureSpec([[1, 2, 4]])
    params = [2.5, -1.0, 0.125]

    model = active_model_terms(structure, basis, params)

    @test length(model) == 1
    @test [entry["term_index"] for entry in model[1]] == [1, 2, 4]
    @test [entry["term"] for entry in model[1]] == ["1", "u1", "u1^3"]
    @test [entry["coefficient"] for entry in model[1]] == params
end
