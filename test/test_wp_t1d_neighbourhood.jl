using Test

include(joinpath(@__DIR__, "..", "studies", "regression", "wp_t1d_neighbourhood_loss.jl"))

@testset "WP-T1d neighbourhood generation" begin
    systems = phase_c_exact_dim23_systems()
    @test length([system for system in systems if Int(system[:dim]) == 2]) == 10
    @test length([system for system in systems if Int(system[:dim]) == 3]) == 8

    for system in systems
        basis = phase_c_basis(Int(system[:dim]))
        true_terms = canonical_support_terms(system[:expected_support])
        true_key = support_key(true_terms)
        neighbours = neighbourhood(true_terms, basis)
        neighbour_keys = [support_key(record["neighbor_terms"]) for record in neighbours]
        @test length(neighbours) == length(unique(neighbour_keys))
        @test all(support_key(record["neighbor_terms"]) != true_key for record in neighbours)
        @test assert_neighbourhood_counts(true_terms, basis)

        p = basis_num_terms(basis)
        for eq_idx in eachindex(true_terms)
            s = length(true_terms[eq_idx])
            eq_records = [record for record in neighbours if Int(record["equation_idx"]) == eq_idx]
            @test count(record -> record["neighbor_class"] == "add_one", eq_records) == p - s
            @test count(record -> record["neighbor_class"] == "remove_one", eq_records) == s
            @test count(record -> record["neighbor_class"] == "swap_one", eq_records) == s * (p - s)
        end
    end
end

@testset "WP-T1d loss ratio regression" begin
    @test log10_loss_ratio(1e-4, 1e-2) == -2.0
    @test log10_loss_ratio(1e-4, 1e-2; neighbor_budget_exhausted = true) === nothing
    @test log10_loss_ratio(1e-4, 1e-2; true_budget_exhausted = true) === nothing
end
