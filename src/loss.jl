# src/loss.jl

"""
    mse_loss(ŷ, y)

Mean squared error between two arrays of equal size.
Returns a large penalty if sizes mismatch or numerical issues occur.
"""
function mse_loss(ŷ::AbstractArray, y::AbstractArray)
    # size check and numerical sanity test
    if size(ŷ) != size(y) || any(!isfinite, ŷ)
        return 1e6
    end

    l = mean(@. (ŷ - y)^2)

    # fallback in case of numerical failure
    return isfinite(l) ? l : 1e6
end
