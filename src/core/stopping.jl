"""
    should_stop(best_J_hist, best_loss, level, options)

Shared stopping logic for all structure search algorithms.

Returns:
- `Bool`
- `Symbol` stop reason
"""
function should_stop(best_J_hist::Vector{Float64},
                     best_loss::Float64,
                     level::Int,
                     options::DiscoveryOptions)

    # hard limit
    if level >= options.max_levels
        return true, :max_levels
    end

    # too early to judge
    if level < options.min_levels
        return false, :min_levels
    end

    # absolute loss threshold
    if best_loss < options.loss_tol
        return true, :loss_tol
    end

    # plateau detection
    w = options.plateau_window
    if length(best_J_hist) >= w + 1
        J_old = best_J_hist[end - w]
        J_new = best_J_hist[end]
        Δ = J_old - J_new

        if options.plateau_relative
            denom = max(abs(J_old), eps())
            if Δ / denom < options.plateau_rtol
                return true, :plateau_relative
            end
        else
            if Δ < options.plateau_tol
                return true, :plateau_absolute
            end
        end
    end

    return false, :continue
end
