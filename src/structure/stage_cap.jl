# src/structure/stage_cap.jl

using LinearAlgebra
using Statistics

"""
Data-only configuration for the look-ahead stage cap.

`estimate_stage_caps(traj, basis; policy)` may inspect only the observed trajectory,
the staged basis, and ordinary threshold hyperparameters. It deliberately has no
arguments for ground truth, expected terms, expected stages, or system identifiers.

Equations whose usable stage cannot be judged receive `nothing`, which means no cap.
The cap is an upper bound only: it can prevent future promotion but never promote an
equation and never removes terms if an equation is already above the cap.
"""
Base.@kwdef struct LookAheadStageCapPolicy
    estimator::Symbol = :local_poly
    weighting::Symbol = :richardson_wls
    tau_rel::Float64 = 1e-4
    tau_abs::Float64 = 1e-8
    cond_cap::Float64 = 1e10
    excitation_floor::Float64 = 1e-10
end

function _cap_uniform_step(t::AbstractVector)
    length(t) < 2 && return 1.0
    return mean(diff(t))
end

function _cap_local_poly_derivatives(traj::Trajectory; halfwidth::Int = 4, degree::Int = 3)
    t = traj.t
    X = traj.x
    n, dim = size(X)
    dX = zeros(Float64, n, dim)
    for i in 1:n
        lo = max(1, i - halfwidth)
        hi = min(n, i + halfwidth)
        if hi - lo + 1 < degree + 1
            lo = max(1, min(lo, n - degree))
            hi = min(n, max(hi, degree + 1))
        end
        z = t[lo:hi] .- t[i]
        A = hcat([z .^ p for p in 0:degree]...)
        for k in 1:dim
            coeffs = A \ X[lo:hi, k]
            dX[i, k] = coeffs[2]
        end
    end
    return dX
end

function _cap_estimate_derivatives(traj::Trajectory, estimator::Symbol)
    estimator == :central && return estimate_derivatives(traj)
    estimator == :local_poly && return _cap_local_poly_derivatives(traj)
    error("Unsupported LookAheadStageCapPolicy.estimator=$(estimator)")
end

function _cap_coarsened_trajectory(traj::Trajectory)
    idxs = collect(1:2:length(traj.t))
    return Trajectory(traj.t[idxs], traj.x[idxs, :])
end

function _cap_interpolate_to_full(t_full, t_coarse, values_coarse)
    n = length(t_full)
    dim = size(values_coarse, 2)
    out = zeros(Float64, n, dim)
    for k in 1:dim
        j = 1
        for i in 1:n
            while j < length(t_coarse) && t_coarse[j + 1] < t_full[i]
                j += 1
            end
            if t_full[i] <= t_coarse[1]
                out[i, k] = values_coarse[1, k]
            elseif t_full[i] >= t_coarse[end]
                out[i, k] = values_coarse[end, k]
            else
                a = (t_full[i] - t_coarse[j]) / (t_coarse[j + 1] - t_coarse[j])
                out[i, k] = (1 - a) * values_coarse[j, k] + a * values_coarse[j + 1, k]
            end
        end
    end
    return out
end

function _cap_richardson_error_estimate(traj::Trajectory, estimator::Symbol)
    full = _cap_estimate_derivatives(traj, estimator)
    coarse_traj = _cap_coarsened_trajectory(traj)
    coarse = _cap_estimate_derivatives(coarse_traj, estimator)
    coarse_full = _cap_interpolate_to_full(traj.t, coarse_traj.t, coarse)
    return abs.(full .- coarse_full)
end

function _cap_splits(n::Int)
    n30 = floor(Int, 0.30 * n)
    n35 = floor(Int, 0.35 * n)
    n70 = n - n30
    q1 = floor(Int, 0.25 * n)
    q2 = floor(Int, 0.50 * n)
    q3 = floor(Int, 0.75 * n)
    return (
        (fit = collect(1:n70), holdout = collect((n70 + 1):n)),
        (fit = collect((n30 + 1):n), holdout = collect(1:n30)),
        (fit = vcat(collect(1:n35), collect((n - n35 + 1):n)),
         holdout = collect((n35 + 1):(n - n35))),
        (fit = vcat(collect(1:q1), collect((q2 + 1):q3)),
         holdout = vcat(collect((q1 + 1):q2), collect((q3 + 1):n))),
    )
end

function _cap_cumulative_stage_idxs(basis::StagedPolynomialBasis, stage::Int)
    idxs = Int[]
    for s in 1:stage
        append!(idxs, basis.term_groups[s])
    end
    return idxs
end

function _cap_weights_from_richardson(rich_eq::AbstractVector)
    scale = median(rich_eq .^ 2) + eps(Float64)
    return 1.0 ./ (rich_eq .^ 2 .+ scale)
end

function _cap_fit_eval(Phi::AbstractMatrix, y::AbstractVector, fit_idxs, holdout_idxs, weights)
    Phi_fit = Matrix(Phi[fit_idxs, :])
    Phi_hold = Matrix(Phi[holdout_idxs, :])
    y_fit = Vector(y[fit_idxs])
    y_hold = Vector(y[holdout_idxs])
    ncols = size(Phi_fit, 2)
    try
        sqrtw = sqrt.(max.(weights[fit_idxs], 0.0))
        coeffs = ncols == 0 ? Float64[] : (Phi_fit .* sqrtw) \ (y_fit .* sqrtw)
        hold_resid = ncols == 0 ? -y_hold : Phi_hold * coeffs - y_hold
        return (residual = mean(abs2, hold_resid), valid = all(isfinite, coeffs) && all(isfinite, hold_resid))
    catch
        return (residual = Inf, valid = false)
    end
end

function _cap_stage_condition(Phi::AbstractMatrix, y::AbstractVector, fit_idxs, policy::LookAheadStageCapPolicy)
    Phi_fit = Matrix(Phi[fit_idxs, :])
    ncols = size(Phi_fit, 2)
    ncols == 0 && return false
    r = rank(Phi_fit)
    c = cond(Phi_fit)
    excitation = mean(abs2, y[fit_idxs] .- mean(y[fit_idxs]))
    return r == ncols && isfinite(c) && c <= policy.cond_cap && excitation >= policy.excitation_floor
end

function _cap_rule_counts_gain(current_residual::Float64, next_residual::Float64,
                               floor::Float64, policy::LookAheadStageCapPolicy)
    isfinite(current_residual) && isfinite(next_residual) || return false
    current_residual <= floor && return false
    delta = current_residual - next_residual
    rel = current_residual == 0.0 ? Inf : delta / current_residual
    return delta > policy.tau_abs && rel > policy.tau_rel && delta > floor
end

function _cap_median_stage(values::Vector{Int})
    isempty(values) && error("Cannot take median stage of an empty set")
    sorted_values = sort(values)
    return sorted_values[cld(length(sorted_values), 2)]
end

function _cap_for_equation(traj::Trajectory, basis::StagedPolynomialBasis, dX::Matrix{Float64},
                           rich::Matrix{Float64}, eq::Int, policy::LookAheadStageCapPolicy)
    y = dX[:, eq]
    weights = policy.weighting == :richardson_wls ? _cap_weights_from_richardson(rich[:, eq]) : ones(length(y))
    split_caps = Int[]
    max_basis_stage = _max_stage(basis)
    new_counts = [length(basis.term_groups[s]) for s in 1:max_basis_stage]

    for split in _cap_splits(length(traj.t))
        residuals = fill(Inf, max_basis_stage)
        usable = falses(max_basis_stage)
        for stage in 1:max_basis_stage
            idxs = _cap_cumulative_stage_idxs(basis, stage)
            Phi = build_design_matrix(basis, idxs, traj.x, traj.t)
            usable[stage] = _cap_stage_condition(Phi, y, split.fit, policy)
            fit = _cap_fit_eval(Phi, y, split.fit, split.holdout, weights)
            residuals[stage] = fit.residual
            usable[stage] &= fit.valid
        end

        usable[1] || continue
        split_cap = 1
        for stage in 1:(max_basis_stage - 1)
            usable[stage] || break
            next_stage = findfirst(s -> s > stage && new_counts[s] > 0, 1:max_basis_stage)
            next_stage === nothing && break
            usable[next_stage] || break
            floor = mean(abs2, rich[split.holdout, eq])
            if _cap_rule_counts_gain(residuals[stage], residuals[next_stage], floor, policy)
                split_cap = max(split_cap, next_stage)
            end
        end
        push!(split_caps, split_cap)
    end

    isempty(split_caps) && return nothing
    return _cap_median_stage(split_caps)
end

function estimate_stage_caps(traj::Trajectory, basis::StagedPolynomialBasis;
                             policy::LookAheadStageCapPolicy = LookAheadStageCapPolicy())
    dX = _cap_estimate_derivatives(traj, policy.estimator)
    rich = _cap_richardson_error_estimate(traj, policy.estimator)
    _, dim = size(traj.x)
    caps = Union{Nothing,Int}[]
    for eq in 1:dim
        push!(caps, _cap_for_equation(traj, basis, dX, rich, eq, policy))
    end
    return caps
end

estimate_stage_caps(traj::Trajectory, basis::AbstractBasis; policy::LookAheadStageCapPolicy = LookAheadStageCapPolicy()) =
    Union{Nothing,Int}[nothing for _ in 1:size(traj.x, 2)]

