"""
Abstract interface for basis libraries / grammars.
"""
abstract type AbstractBasis end

"Number of basis terms."
function basis_num_terms end

"Name of the i-th term (for printing)."
function basis_term_name end

"Callable of the i-th term: (u, t) -> Float64."
function basis_term_func end

"""
    build_rhs(structure::StructureSpec, basis::AbstractBasis) -> (f!, n_params, meta)

Builds the ODE RHS from structure + basis.

- `f!` signature: f!(du, u, p, t)
- `n_params`: number of coefficients needed
- `meta`: optional info
"""
function build_rhs(structure::StructureSpec, basis::AbstractBasis)
    n_params = sum(length(idxs) for idxs in structure.active_idxs)

    function f!(du, u, p, t)
        idx = 1
        for k in 1:length(structure.active_idxs)
            acc = 0.0
            for term_idx in structure.active_idxs[k]
                ϕ = basis_term_func(basis, term_idx)
                acc += p[idx] * ϕ(u, t)
                idx += 1
            end
            du[k] = acc
        end
        return nothing
    end

    meta = (n_params = n_params,)
    return f!, n_params, meta
end
