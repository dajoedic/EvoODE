"""
Polynomial basis up to degree 2 (Phase 1).

For dim=2:
- u1, u2
- u1^2, u2^2
- u1*u2
"""
struct PolynomialBasis <: AbstractBasis
    dim::Int
    names::Vector{String}
    funcs::Vector{Function}
end

function default_polynomial_basis(dim::Int)
    names = String[]
    funcs = Function[]

    # Linear terms
    for i in 1:dim
        push!(names, "u$i")
        push!(funcs, (u, t) -> u[i])
    end

    # Quadratic terms
    for i in 1:dim
        push!(names, "u$i^2")
        push!(funcs, (u, t) -> u[i]^2)
    end

    # Cross terms u_i*u_j (i<j)
    if dim >= 2
        for i in 1:(dim-1), j in (i+1):dim
            push!(names, "u$i*u$j")
            push!(funcs, (u, t) -> u[i] * u[j])
        end
    end

    return PolynomialBasis(dim, names, funcs)
end

"Convenience constructor with dim=0 (discover will replace with dim from traj)."
PolynomialBasis() = PolynomialBasis(0, String[], Function[])

basis_num_terms(b::PolynomialBasis) = length(b.names)
basis_term_name(b::PolynomialBasis, i::Int) = b.names[i]
basis_term_func(b::PolynomialBasis, i::Int) = b.funcs[i]
