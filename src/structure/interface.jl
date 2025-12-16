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

Must return at least:
- `structure`
Optionally:
- `meta`
"""
function search_structure end
