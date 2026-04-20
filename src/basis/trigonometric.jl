# src/basis/trigonometric.jl
# Stub — not yet implemented.
# Note: sin/cos terms are already available as Stage 5 of StagedPolynomialBasis.
# This file is reserved for a standalone TrigonometricBasis (e.g., Fourier features).

"""
    TrigonometricBasis

Standalone trigonometric basis: sin/cos per state variable (not yet implemented).

For trigonometric terms in the current framework, use `default_staged_polynomial_basis(dim)`,
which includes sin/cos as Stage 5.
"""
struct TrigonometricBasis <: AbstractBasis
    dim::Int
end

"""
    default_trigonometric_basis(dim)

Not yet implemented.
"""
function default_trigonometric_basis(_::Int)
    error("TrigonometricBasis is not yet implemented. Use `default_staged_polynomial_basis(dim)` instead.")
end

basis_num_terms(::TrigonometricBasis) =
    error("TrigonometricBasis is not yet implemented.")

basis_term_name(::TrigonometricBasis, ::Int) =
    error("TrigonometricBasis is not yet implemented.")

basis_term_func(::TrigonometricBasis, ::Int) =
    error("TrigonometricBasis is not yet implemented.")
