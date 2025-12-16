using Printf

"""
    save_comparison_csv(t, X, Ŷ; filename, digits=8)

Writes a CSV with ';' as separator and ',' as decimal separator.

Columns:
  t;
  x1; x2; ...;
  yhat1; yhat2; ...

Assumes:
  - t is length T
  - X is (T × dim)
  - Ŷ is (T × dim)
"""
function save_comparison_csv(t::AbstractVector,
                             X::AbstractMatrix,
                             Ŷ::AbstractMatrix;
                             filename::String,
                             digits::Int = 8)

    T = length(t)
    @assert size(X, 1) == T "X must have T rows"
    @assert size(Ŷ, 1) == T "Ŷ must have T rows"
    dim = size(X, 2)
    @assert size(Ŷ, 2) == dim "Ŷ must have same dim as X"

    # Helper: format float with decimal comma
    fmt(x) = replace(@sprintf("%.*f", digits, float(x)), "." => ",")

    open(filename, "w") do io
        # header
        x_cols    = ["x$(k)" for k in 1:dim]
        yhat_cols = ["yhat$(k)" for k in 1:dim]
        println(io, join(vcat(["t"], x_cols, yhat_cols), ";"))

        # rows
        for i in 1:T
            row = String[]
            push!(row, fmt(t[i]))
            for k in 1:dim
                push!(row, fmt(X[i, k]))
            end
            for k in 1:dim
                push!(row, fmt(Ŷ[i, k]))
            end
            println(io, join(row, ";"))
        end
    end

    return filename
end
