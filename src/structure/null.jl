# src/structure/null.jl

"""
    NullStructure()

Baseline structure search:
- Uses zero RHS: du/dt = 0
"""
struct NullStructure <: AbstractStructureSearch end

"""
    search_structure(::NullStructure, traj; basis, loss, optimizer, options)
"""
function search_structure(::NullStructure,
                          traj::Trajectory;
                          basis,
                          loss,
                          optimizer,
                          options)

    dim = size(traj.x, 2)

    # Zero model
    function model_builder(p, traj)
        zeros(size(traj.x))
    end

    fit = fit_parameters(optimizer, model_builder, traj;
                         loss = loss,
                         options = options)

    return StructureSearchResult(
        :zero_rhs,
        fit.params,
        fit.loss,
        fit.loss,
        (algorithm = :null,)
    )
end
