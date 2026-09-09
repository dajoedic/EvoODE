using Statistics: mean

const MSE_SENTINEL_LOSS = 1e6

"""
Mean squared error loss.
"""
struct MSELoss <: AbstractLoss end

"""
    evaluate_loss(::MSELoss, Ŷ, Y)

Returns a large penalty if sizes mismatch or prediction contains non-finite values.
"""
function evaluate_loss(::MSELoss, Ŷ::AbstractArray, Y::AbstractArray)
    if size(Ŷ) != size(Y)
        return MSE_SENTINEL_LOSS
    end
    if any(x -> !isfinite(x), Ŷ)
        return MSE_SENTINEL_LOSS
    end
    l = mean(@. (Ŷ - Y)^2)
    return isfinite(l) ? l : MSE_SENTINEL_LOSS
end
