using Test
using EvoODE

struct ContractSearch <: AbstractStructureSearch
    params::Vector{Float64}
    objective::Float64
end

function EvoODE.search_structure(
    strategy::ContractSearch,
    traj,
    basis,
    loss,
    optimizer,
    options,
)
    return (
        structure = StructureSpec([[1]]),
        params = copy(strategy.params),
        loss = 0.0,
        objective = strategy.objective,
        meta = (; source = :contract_test),
    )
end

function contract_traj()
    return Trajectory([0.0, 1.0], zeros(2, 1))
end

function contract_discover(strategy::ContractSearch)
    return discover(
        contract_traj();
        structure = strategy,
        optimizer = DummyOptimizer(),
        basis = default_polynomial_basis(1),
        loss = MSELoss(),
        options = DiscoveryOptions(rng_seed = 123, verbose = 0),
    )
end

@testset "discover rejects structure-search parameter count mismatch" begin
    err = try
        contract_discover(ContractSearch(Float64[], 77.0))
        nothing
    catch caught
        caught
    end

    @test err isa ErrorException
    message = sprint(showerror, err)
    @test occursin("expected 1", message)
    @test occursin("received 0", message)
    @test occursin("ContractSearch", message)
    @test occursin("StructureSpec", message)
end

@testset "discover accepts consistent structure-search result" begin
    result = contract_discover(ContractSearch([0.0], 77.0))

    @test result isa DiscoveryResult
    @test result.structure.active_idxs == [[1]]
    @test result.params == [0.0]
    @test result.loss == 0.0
    @test result.objective == 77.0
    @test result.meta.optimize.method == "from_structure_search"
end
