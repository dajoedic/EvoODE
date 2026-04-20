"""
    PolynomialBasis

Flat polynomial basis up to degree 2: linear, self-quadratic, and pairwise cross terms.
All terms are available from the start (no staged complexity).

For `dim=2`: `u1, u2, u1^2, u2^2, u1*u2` — 5 terms total.

Use `StagedPolynomialBasis` if you need staged complexity unlocking.
"""
struct PolynomialBasis <: AbstractBasis
    dim::Int
    names::Vector{String}
    funcs::Vector{Function}
end

"""
    default_polynomial_basis(dim) -> PolynomialBasis

Build a flat polynomial basis for `dim`-dimensional state vectors.

Term order: linear (dim), self-quadratic (dim), cross terms (dim*(dim-1)/2).
"""
function default_polynomial_basis(dim::Int)
    names = String[]
    funcs = Function[]

    # Linear terms
    for i in 1:dim
        ii = i
        push!(names, "u$ii")
        push!(funcs, (u, t) -> u[ii])
    end

    # Quadratic terms
    for i in 1:dim
        ii = i
        push!(names, "u$ii^2")
        push!(funcs, (u, t) -> u[ii]^2)
    end

    # Cross terms u_i*u_j (i<j)
    if dim >= 2
        for i in 1:(dim-1), j in (i+1):dim
            ii, jj = i, j
            push!(names, "u$ii*u$jj")
            push!(funcs, (u, t) -> u[ii] * u[jj])
        end
    end

    return PolynomialBasis(dim, names, funcs)
end

"Convenience constructor with dim=0 (discover will replace with dim from traj)."
PolynomialBasis() = PolynomialBasis(0, String[], Function[])

basis_num_terms(b::PolynomialBasis) = length(b.names)
basis_term_name(b::PolynomialBasis, i::Int) = b.names[i]
basis_term_func(b::PolynomialBasis, i::Int) = b.funcs[i]
