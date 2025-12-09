# src/loss.jl

"""
Einfacher MSE zwischen zwei Matrizen gleicher Größe.
"""
function mse_loss(pred::AbstractMatrix, data::AbstractMatrix)
    return sum(abs2, pred .- data) / length(data)
end
