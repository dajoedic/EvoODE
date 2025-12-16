using Statistics: mean

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
        return 1e6
    end
    if any(x -> !isfinite(x), Ŷ)
        return 1e6
    end
    l = mean(@. (Ŷ - Y)^2)
    return isfinite(l) ? l : 1e6
end
