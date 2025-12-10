# src/loss.jl

"""
Einfacher MSE zwischen zwei Matrizen gleicher Größe.
"""
function mse_loss(ŷ::AbstractArray, y::AbstractArray)
    # Wenn Dimensionen nicht passen oder ŷ kaputt ist → großer Loss
    if size(ŷ) != size(y) || any(!isfinite, ŷ)
        return 1e6
    end

    l = mean(@. (ŷ - y)^2)

    # Falls trotzdem irgendwas schiefgeht
    if !isfinite(l)
        return 1e6
    end

    return l
end
