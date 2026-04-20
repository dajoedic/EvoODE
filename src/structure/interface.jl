"""
Abstract interface for structure search algorithms.
"""
abstract type AbstractStructureSearch end

"""
    StructureSpec(active_idxs)

Generic structure representation:
`active_idxs[k]` = list of active term indices for equation k.
"""
struct StructureSpec
    active_idxs::Vector{Vector{Int}}
end

"""
    search_structure(strategy, traj, basis, loss, optimizer, options) -> NamedTuple

Run structure search and return a NamedTuple with:
- `structure`: discovered `StructureSpec`
- `params::Vector{Float64}`: fitted parameters for the best structure
- `loss::Float64`: best loss value
- `objective::Float64`: best penalized objective (loss + λ * n_params)
- `meta`: algorithm-specific diagnostics (optional but encouraged)
"""
function search_structure end
