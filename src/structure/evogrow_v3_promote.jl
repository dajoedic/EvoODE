# src/structure/evogrow_v3_promote.jl

function _evogrow_v3_trajectory_residuals(
    f!::Function,
    params::Vector{Float64},
    traj::Trajectory,
    options::DiscoveryOptions
)
    Yhat = simulate(f!, params, traj; options = options)
    _, dim = size(traj.x)
    residuals = zeros(Float64, dim)
    for k in 1:dim
        residuals[k] = sum(abs2, Yhat[:, k] .- traj.x[:, k]) / size(traj.x, 1)
    end
    return residuals
end

function _evogrow_v3_equation_residuals(
    structure::StructureSpec,
    params::Vector{Float64},
    basis::AbstractBasis,
    traj::Trajectory,
    options::DiscoveryOptions
)
    f!, _, _ = build_rhs(structure, basis)
    dX = estimate_derivatives(traj)

    if any(!isfinite, dX)
        return _evogrow_v3_trajectory_residuals(f!, params, traj, options), true
    end

    T, dim = size(traj.x)
    residuals = zeros(Float64, dim)
    du = zeros(Float64, dim)

    for row in 1:T
        f!(du, view(traj.x, row, :), params, traj.t[row])
        for k in 1:dim
            residuals[k] += abs2(dX[row, k] - du[k])
        end
    end

    residuals ./= T
    return residuals, false
end

function _record_eq_stage_level!(
    eq_levels_in_stage::Vector{Int},
    eq_plateau_histories::Vector{Vector{Float64}},
    eq_stage_histories::Vector{Vector{Int}},
    eq_residual_log::Vector{Vector{Float64}},
    eq_stages::Vector{Int},
    eq_residuals::Vector{Float64}
)
    for k in eachindex(eq_stages)
        eq_levels_in_stage[k] += 1
        push!(eq_plateau_histories[k], eq_residuals[k])
        push!(eq_residual_log[k], eq_residuals[k])
        push!(eq_stage_histories[k], eq_stages[k])
    end
    return nothing
end

function _evogrow_v3_equation_plateaued(
    history::Vector{Float64},
    plateau_window::Int,
    plateau_tol::Float64
)
    if length(history) < plateau_window
        return false
    end
    window = history[(end - plateau_window + 1):end]
    return maximum(window) - minimum(window) < plateau_tol
end

function _evogrow_v3_promotion_decisions(
    eq_stages::Vector{Int},
    eq_levels_in_stage::Vector{Int},
    eq_plateau_histories::Vector{Vector{Float64}},
    max_stage::Int,
    strategy,
    options::DiscoveryOptions
)
    effective_min_per_stage = max(
        strategy.progression.min_levels_per_stage,
        options.plateau_window + 1
    )
    promote = falses(length(eq_stages))

    for k in eachindex(eq_stages)
        if eq_stages[k] >= max_stage
            continue
        end
        if eq_levels_in_stage[k] < effective_min_per_stage
            continue
        end
        if !_evogrow_v3_equation_plateaued(
            eq_plateau_histories[k],
            options.plateau_window,
            options.plateau_tol
        )
            continue
        end
        if eq_plateau_histories[k][end] <= options.loss_tol
            continue
        end
        promote[k] = true
    end

    return promote
end

function _apply_eq_stage_update!(
    eq_stages::Vector{Int},
    eq_levels_in_stage::Vector{Int},
    eq_plateau_histories::Vector{Vector{Float64}},
    eq_promotion_levels::Vector{Vector{Int}},
    promote::AbstractVector{Bool},
    level::Int
)
    for k in eachindex(eq_stages)
        if promote[k]
            eq_stages[k] += 1
            eq_levels_in_stage[k] = 0
            empty!(eq_plateau_histories[k])
            push!(eq_promotion_levels[k], level)
        end
    end
    return any(promote)
end

function _evogrow_v3_all_max_plateaued(
    eq_stages::Vector{Int},
    eq_plateau_histories::Vector{Vector{Float64}},
    max_stage::Int,
    options::DiscoveryOptions
)
    if !all(==(max_stage), eq_stages)
        return false
    end
    return all(
        hist -> _evogrow_v3_equation_plateaued(hist, options.plateau_window, options.plateau_tol),
        eq_plateau_histories
    )
end

function _evogrow_v3_termination_decision(
    best_loss::Float64,
    level::Int,
    eq_stages::Vector{Int},
    eq_plateau_histories::Vector{Vector{Float64}},
    max_stage::Int,
    options::DiscoveryOptions
)
    if level >= options.max_levels
        return true, :max_levels
    end
    if level < options.min_levels
        return false, :min_levels
    end
    if best_loss < options.loss_tol
        return true, :loss_tol
    end
    if _evogrow_v3_all_max_plateaued(eq_stages, eq_plateau_histories, max_stage, options)
        return true, :all_equations_max_stage_plateau
    end
    return false, :continue
end
