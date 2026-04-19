# src/structure/utils.jl

using Printf

"""
Pretty-print a StructureSpec with fitted parameters.
"""
function structure_with_params_string(
    structure::StructureSpec,
    basis::AbstractBasis,
    params::Vector{Float64}
)
    buf = IOBuffer()
    idx = 1
    for eq_index in 1:length(structure.active_idxs)
        parts = String[]
        for term_idx in structure.active_idxs[eq_index]
            coef = params[idx]
            name = basis_term_name(basis, term_idx)
            push!(parts, @sprintf("(%0.4f)*%s", coef, name))
            idx += 1
        end
        println(buf, "du_$eq_index = " * join(parts, " + "))
    end
    return String(take!(buf))
end
