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
