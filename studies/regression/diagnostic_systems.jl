# studies/regression/diagnostic_systems.jl

const REGRESSION_SEEDS = [42, 123, 7]

# Runtime is dominated by Systems 26 and 63; System 63 can take hours.
# Keep this full list as the default suite. If it is trimmed later, the changed
# system-id list becomes part of the config fingerprint and forms a separate track.
const REGRESSION_SYSTEMS = [
    Dict(
        :system_id => 3,
        :system_name => "Logistic growth",
        :dim => 1,
        :u0 => [7.3],
        :tspan => (0.0, 20.0),
        :T => 200,
        :expected_stage => 2,
    ),
    Dict(
        :system_id => 11,
        :system_name => "Critical slowing down",
        :dim => 1,
        :u0 => [3.4],
        :tspan => (0.0, 5.0),
        :T => 100,
        :expected_stage => 4,
    ),
    Dict(
        :system_id => 26,
        :system_name => "Lotka-Volterra competition",
        :dim => 2,
        :u0 => [5.0, 4.3],
        :tspan => (0.0, 10.0),
        :T => 200,
        :expected_stage => 3,
    ),
    Dict(
        :system_id => 31,
        :system_name => "SIR infection model",
        :dim => 2,
        :u0 => [7.2, 0.98],
        :tspan => (0.0, 20.0),
        :T => 200,
        :expected_stage => 3,
    ),
    Dict(
        :system_id => 63,
        :system_name => "SEIR epidemic",
        :dim => 4,
        :u0 => [0.6, 0.3, 0.09, 0.01],
        :tspan => (0.0, 30.0),
        :T => 300,
        :expected_stage => 3,
    ),
]

function rhs_03!(du, u, _, _)
    du[1] = 0.79 * u[1] * (1.0 - u[1] / 74.3)
end

function rhs_11!(du, u, _, _)
    du[1] = -u[1]^3
end

function rhs_26!(du, u, _, _)
    du[1] = u[1] * (3.0 - u[1] - 2.0 * u[2])
    du[2] = u[2] * (2.0 - u[1] - u[2])
end

function rhs_31!(du, u, _, _)
    du[1] = -0.4 * u[1] * u[2]
    du[2] = 0.4 * u[1] * u[2] - 0.314 * u[2]
end

function rhs_63!(du, u, _, _)
    du[1] = -0.28 * u[1] * u[3]
    du[2] = 0.28 * u[1] * u[3] - 0.47 * u[2]
    du[3] = 0.47 * u[2] - 0.30 * u[3]
    du[4] = 0.30 * u[3]
end

function rhs_for_system(system_id::Int)
    if system_id == 3
        return rhs_03!
    elseif system_id == 11
        return rhs_11!
    elseif system_id == 26
        return rhs_26!
    elseif system_id == 31
        return rhs_31!
    elseif system_id == 63
        return rhs_63!
    end
    error("Unsupported system_id=$(system_id)")
end

function expected_terms_for(system_id::Int)
    if system_id == 2
        return [["u1"]]
    elseif system_id == 3
        return [["u1", "u1^2"]]
    elseif system_id == 11
        return [["u1^3"]]
    elseif system_id == 23
        return nothing
    elseif system_id == 24
        return [["u2"], ["u1"]]
    elseif system_id == 26
        return [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]]
    elseif system_id == 31
        return [["u1*u2"], ["u1*u2", "u2"]]
    elseif system_id == 37
        return nothing
    elseif system_id == 54
        return [["u1", "u2"], ["u1", "u2", "u1*u3"], ["u1*u2", "u3"]]
    elseif system_id == 63
        return [["u1*u3"], ["u1*u3", "u2"], ["u2", "u3"], ["u3"]]
    end
    error("Unsupported system_id=$(system_id)")
end

function basis_name_to_idx(basis::AbstractBasis)
    return Dict(basis_term_name(basis, i) => i for i in 1:basis_num_terms(basis))
end

function expected_active_idxs(system_id::Int, basis::AbstractBasis)
    expected_terms = expected_terms_for(system_id)
    expected_terms === nothing && return nothing
    name_to_idx = basis_name_to_idx(basis)
    return [sort([name_to_idx[name] for name in eq_terms]) for eq_terms in expected_terms]
end

function support_match(structure::StructureSpec, expected_idxs::Vector{Vector{Int}})
    if length(structure.active_idxs) != length(expected_idxs)
        return false
    end
    for (got, expected) in zip(structure.active_idxs, expected_idxs)
        if sort(unique(got)) != sort(unique(expected))
            return false
        end
    end
    return true
end

function support_match_pruned(
    structure::StructureSpec,
    params::Vector{Float64},
    expected_idxs::Vector{Vector{Int}}
)
    if length(structure.active_idxs) != length(expected_idxs)
        return false
    end

    offset = 0
    for (got_idxs, exp_idxs) in zip(structure.active_idxs, expected_idxs)
        n_terms = length(got_idxs)
        eq_params = params[(offset + 1):(offset + n_terms)]
        offset += n_terms

        max_abs = isempty(eq_params) ? 0.0 : maximum(abs, eq_params)
        threshold = max(1e-6, 1e-3 * max_abs)

        pruned_idxs = sort([got_idxs[i] for i in 1:n_terms if abs(eq_params[i]) >= threshold])

        if pruned_idxs != sort(unique(exp_idxs))
            return false
        end
    end
    return true
end
