using Plots

# --- formatting helpers for German-style CSV output ---
_format_de(x::Real) = replace(string(x), "." => ",")
_format_de(x::AbstractString) = x

"""
    solve_and_save_plot(f!, params, traj; filename, title="", csv_filename=nothing)

Simulates the ODE defined by `f!` with fitted parameters `params`
on the time grid of `traj` and saves a comparison plot between
data (points) and model prediction (line).

If `csv_filename` is provided, writes a CSV with:
t; x1; x2; ...; yhat1; yhat2; ...
with decimal comma.
"""
function solve_and_save_plot(f!::Function,
                             params::Vector{Float64},
                             traj::Trajectory;
                             filename::String,
                             title::String = "",
                             csv_filename::Union{Nothing,String} = nothing)

    # Use package simulate() to stay consistent
    Ŷ = EvoODE.simulate(f!, params, traj)

    t = traj.t
    X = traj.x
    dim = size(X, 2)

    plt = plot(layout=(dim, 1), legend=:bottomright)

    for k in 1:dim
        scatter!(plt[k], t, X[:, k], label="data u$k", markersize=3)
        plot!(plt[k], t, Ŷ[:, k], label="model u$k", linewidth=2)
    end

    if title != ""
        plot!(plt, title=title)
    end

    savefig(plt, filename)

    if csv_filename !== nothing
        open(csv_filename, "w") do io
            # header
            cols = ["t"]
            append!(cols, ["x$k" for k in 1:dim])
            append!(cols, ["yhat$k" for k in 1:dim])
            println(io, join(cols, ";"))

            for i in 1:length(t)
                row = String[]
                push!(row, _format_de(t[i]))
                for k in 1:dim
                    push!(row, _format_de(X[i, k]))
                end
                for k in 1:dim
                    push!(row, _format_de(Ŷ[i, k]))
                end
                println(io, join(row, ";"))
            end
        end
    end

    return filename
end
