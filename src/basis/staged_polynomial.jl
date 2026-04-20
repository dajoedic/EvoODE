# src/basis/staged_polynomial.jl

"""
    StagedPolynomialBasis

Polynomial + trigonometric basis with explicit complexity groups.

Fields:
- term_funcs::Vector{Function}
- term_names::Vector{String}
- term_groups::Vector{Vector{Int}}   # indices per complexity stage
"""
struct StagedPolynomialBasis <: AbstractBasis
    term_funcs::Vector{Function}
    term_names::Vector{String}
    term_groups::Vector{Vector{Int}}
end

# ------------------------------------------------------------
# Interface
# ------------------------------------------------------------

basis_num_terms(b::StagedPolynomialBasis) = length(b.term_funcs)

basis_term_name(b::StagedPolynomialBasis, i::Int) = b.term_names[i]

basis_term_func(b::StagedPolynomialBasis, i::Int) = b.term_funcs[i]

# ------------------------------------------------------------
# Builder
# ------------------------------------------------------------

"""
    default_staged_polynomial_basis(dim)

Builds staged basis with 5 complexity levels:

1. linear
2. self quadratic
3. cross terms
4. cubic (self only)
5. trigonometric (sin/cos per variable)
"""
function default_staged_polynomial_basis(dim::Int)

    term_funcs = Function[]
    term_names = String[]
    term_groups = Vector{Vector{Int}}()

    # Helper
    function add_term!(f, name, group)
        push!(term_funcs, f)
        push!(term_names, name)
        push!(group, length(term_funcs))
    end

    # ------------------------------------------------------------
    # Stage 1: linear
    # ------------------------------------------------------------
    group1 = Int[]
    for i in 1:dim
        ii = i
        add_term!((u, t) -> u[ii], "u$ii", group1)
    end
    push!(term_groups, group1)

    # ------------------------------------------------------------
    # Stage 2: self quadratic
    # ------------------------------------------------------------
    group2 = Int[]
    for i in 1:dim
        ii = i
        add_term!((u, t) -> u[ii]^2, "u$ii^2", group2)
    end
    push!(term_groups, group2)

    # ------------------------------------------------------------
    # Stage 3: cross terms
    # ------------------------------------------------------------
    group3 = Int[]
    for i in 1:dim
        for j in (i+1):dim
            ii, jj = i, j
            add_term!((u, t) -> u[ii] * u[jj], "u$ii*u$jj", group3)
        end
    end
    push!(term_groups, group3)

    # ------------------------------------------------------------
    # Stage 4: cubic (self only)
    # ------------------------------------------------------------
    group4 = Int[]
    for i in 1:dim
        ii = i
        add_term!((u, t) -> u[ii]^3, "u$ii^3", group4)
    end
    push!(term_groups, group4)

    # ------------------------------------------------------------
    # Stage 5: trigonometric
    # ------------------------------------------------------------
    group5 = Int[]
    for i in 1:dim
        ii = i
        add_term!((u, t) -> sin(u[ii]), "sin(u$ii)", group5)
        add_term!((u, t) -> cos(u[ii]), "cos(u$ii)", group5)
    end
    push!(term_groups, group5)

    return StagedPolynomialBasis(term_funcs, term_names, term_groups)
end