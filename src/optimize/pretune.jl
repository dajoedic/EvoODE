using LinearAlgebra

function estimate_derivatives(traj::Trajectory)
    t = traj.t
    X = traj.x
    T, dim = size(X)

    dX = zeros(Float64, T, dim)

    if T < 2
        return dX
    end

    dX[1, :] .= (X[2, :] .- X[1, :]) ./ (t[2] - t[1])

    for i in 2:(T - 1)
        dX[i, :] .= (X[i + 1, :] .- X[i - 1, :]) ./ (t[i + 1] - t[i - 1])
    end

    dX[end, :] .= (X[end, :] .- X[end - 1, :]) ./ (t[end] - t[end - 1])

    return dX
end

function build_design_matrix(basis::AbstractBasis,
                             active_idxs::Vector{Int},
                             X::AbstractMatrix,
                             t::AbstractVector)
    T = size(X, 1)
    Phi = zeros(Float64, T, length(active_idxs))

    for (col, term_idx) in enumerate(active_idxs)
        f = basis_term_func(basis, term_idx)
        for row in 1:T
            u = view(X, row, :)
            Phi[row, col] = f(u, t[row])
        end
    end

    return Phi
end

function pretune_parameters(structure::StructureSpec,
                            basis::AbstractBasis,
                            traj::Trajectory)
    n_params_total = sum(length(eq) for eq in structure.active_idxs)

    if n_params_total == 0
        return Float64[]
    end

    dX = estimate_derivatives(traj)

    p0 = Float64[]
    for k in 1:length(structure.active_idxs)
        active = structure.active_idxs[k]
        if isempty(active)
            continue
        end
        Phi = build_design_matrix(basis, active, traj.x, traj.t)
        p_k = Phi \ dX[:, k]
        append!(p0, p_k)
    end

    if length(p0) != n_params_total || any(isnan, p0) || any(isinf, p0) || norm(p0) > 1e6
        return zeros(n_params_total)
    end

    return p0
end

"""
    derivative_screening_diagnostics(structure, basis, traj; parameter_norm_limit=1e6)

Fit the active terms of `structure` to finite-difference derivatives by closed-form
least squares and return `(params, residual, valid, invalid_reason, n_params)`.

Unlike `pretune_parameters`, invalid LS systems are reported explicitly instead
of silently returning a zero warm start. This matters for structure screening:
non-finite parameters, failed solves, or excessive parameter norms must count as
invalid candidates rather than receiving an artificially benign all-zero score.
The residual is the mean squared derivative residual over all state components
and time points, so smaller values rank candidates higher.
"""
function derivative_screening_diagnostics(structure::StructureSpec,
                                          basis::AbstractBasis,
                                          traj::Trajectory;
                                          parameter_norm_limit::Float64 = 1e6)
    n_params_total = sum(length(eq) for eq in structure.active_idxs)
    dX = estimate_derivatives(traj)
    T, dim = size(dX)

    params = Float64[]
    per_equation_residuals = fill(Inf, length(structure.active_idxs))
    invalid_reasons = String[]
    residual_ss = 0.0
    residual_count = 0

    for k in 1:length(structure.active_idxs)
        active = structure.active_idxs[k]
        target = dX[:, k]

        if isempty(active)
            residual_vec = target
            per_equation_residuals[k] = sum(abs2, residual_vec) / max(length(residual_vec), 1)
            residual_ss += sum(abs2, residual_vec)
            residual_count += length(residual_vec)
            continue
        end

        local p_k
        local residual_vec
        try
            Phi = build_design_matrix(basis, active, traj.x, traj.t)
            p_k = Phi \ target
            residual_vec = Phi * p_k - target
        catch err
            push!(invalid_reasons, "equation_$(k)_ls_failed:$(typeof(err))")
            append!(params, zeros(length(active)))
            continue
        end

        append!(params, p_k)

        if any(!isfinite, p_k)
            push!(invalid_reasons, "equation_$(k)_nonfinite_params")
        end
        if norm(p_k) > parameter_norm_limit
            push!(invalid_reasons, "equation_$(k)_parameter_norm_limit")
        end
        if any(!isfinite, residual_vec)
            push!(invalid_reasons, "equation_$(k)_nonfinite_residual")
        end

        per_equation_residuals[k] = sum(abs2, residual_vec) / max(length(residual_vec), 1)
        residual_ss += sum(abs2, residual_vec)
        residual_count += length(residual_vec)
    end

    if length(params) != n_params_total
        push!(invalid_reasons, "parameter_count_mismatch")
        params = zeros(n_params_total)
    end
    if isempty(invalid_reasons) && norm(params) > parameter_norm_limit
        push!(invalid_reasons, "total_parameter_norm_limit")
    end

    residual = residual_count == 0 ? 0.0 : residual_ss / residual_count
    if !isfinite(residual)
        push!(invalid_reasons, "nonfinite_residual")
    end

    valid = isempty(invalid_reasons)
    if !valid
        residual = Inf
    end

    return (
        params = valid ? params : zeros(n_params_total),
        residual = residual,
        valid = valid,
        invalid_reason = valid ? "" : join(invalid_reasons, ";"),
        n_params = n_params_total,
        per_equation_residuals = per_equation_residuals,
        n_timepoints = T,
        dim = dim
    )
end
