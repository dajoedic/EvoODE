# src/structure/null.jl
# NullStructure is not included in EvoODE.jl by default.
# It can be used directly in experiments as a trivial baseline (du/dt = 0).

"""
    NullStructure()

Trivial baseline: predicts du/dt = 0 (constant trajectory equal to initial conditions).

Not included in the default module — load explicitly with `include("src/structure/null.jl")`
when needed as a lower bound in experiments.
"""
struct NullStructure <: AbstractStructureSearch end

"""
    search_structure(::NullStructure, traj, basis, loss, optimizer, options)

Returns an empty `StructureSpec` (no active terms in any equation), which corresponds
to the zero-RHS model du/dt = 0.
"""
function search_structure(::NullStructure,
                          traj::Trajectory,
                          basis::AbstractBasis,
                          loss::AbstractLoss,
                          optimizer::AbstractOptimizer,
                          options::DiscoveryOptions)

    dim = size(traj.x, 2)

    # Empty structure: du_k/dt = 0 for all k
    structure = StructureSpec([Int[] for _ in 1:dim])
    f!, _, _ = build_rhs(structure, basis)

    params = Float64[]
    Ŷ = simulate(f!, params, traj; options=options)
    l = evaluate_loss(loss, Ŷ, traj.x)

    return (
        structure = structure,
        params    = params,
        loss      = l,
        objective = l,
        meta      = (algorithm = :null,)
    )
end
