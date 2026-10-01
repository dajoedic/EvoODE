using Random

const DATA_CONDITION_SEED_SCHEMA_VERSION = "phase_c_data_condition_seed_v1"
const DATA_CONDITION_NOISE_MODEL = "multiplicative_gaussian_iid"
const DATA_CONDITION_SUBSAMPLE_RULE = "remove_floor_n_rho_uniform_without_replacement_after_noise"

function _condition_float_string(value::Real)
    return isfinite(Float64(value)) ? @sprintf("%.17g", Float64(value)) : string(Float64(value))
end

function data_condition_fingerprint(noise_sigma::Real, subsample_rho::Real, noise_realization::Integer)
    payload = (
        sigma = _condition_float_string(noise_sigma),
        rho = _condition_float_string(subsample_rho),
        realization = Int(noise_realization),
        noise_model = DATA_CONDITION_NOISE_MODEL,
        subsampling_rule = DATA_CONDITION_SUBSAMPLE_RULE,
        seed_schema_version = DATA_CONDITION_SEED_SCHEMA_VERSION,
    )
    return bytes2hex(sha256(codeunits(canonical_value(payload))))[1:16]
end

function _data_condition_seed(system_id::Integer, ic_set::Integer, noise_sigma::Real,
                              subsample_rho::Real, noise_realization::Integer,
                              stream::AbstractString)
    payload = (
        seed_schema_version = DATA_CONDITION_SEED_SCHEMA_VERSION,
        system_id = Int(system_id),
        ic_set = Int(ic_set),
        sigma = _condition_float_string(noise_sigma),
        rho = _condition_float_string(subsample_rho),
        realization = Int(noise_realization),
        stream = String(stream),
    )
    digest = sha256(codeunits(canonical_value(payload)))
    seed = UInt64(0)
    @inbounds for i in 1:8
        seed |= UInt64(digest[i]) << (8 * (i - 1))
    end
    return seed
end

function apply_phase_c_data_condition(traj::Trajectory, system_id::Integer, ic_set::Integer,
                                      noise_sigma::Real, subsample_rho::Real,
                                      noise_realization::Integer)
    sigma = Float64(noise_sigma)
    rho = Float64(subsample_rho)
    sigma >= 0.0 || error("noise_sigma must be non-negative, got $(noise_sigma)")
    0.0 <= rho <= 1.0 || error("subsample_rho must be in [0, 1], got $(subsample_rho)")
    if sigma == 0.0 && rho == 0.0
        return traj
    end

    observed_x = copy(traj.x)
    if sigma != 0.0
        rng_noise = Xoshiro(_data_condition_seed(system_id, ic_set, sigma, rho, noise_realization, "noise"))
        observed_x .= observed_x .+ sigma .* observed_x .* randn(rng_noise, size(observed_x))
    end

    observed_t = copy(traj.t)
    n_remove = floor(Int, length(observed_t) * rho)
    if n_remove > 0
        rng_subsample = Xoshiro(_data_condition_seed(system_id, ic_set, sigma, rho, noise_realization, "subsample"))
        removed = Set(randperm(rng_subsample, length(observed_t))[1:n_remove])
        keep = [idx for idx in eachindex(observed_t) if !(idx in removed)]
        observed_t = observed_t[keep]
        observed_x = observed_x[keep, :]
    end

    return Trajectory(observed_t, observed_x)
end

function observed_data_sha256(traj::Trajectory)
    return Dict(
        "hash_format" => HASH_FORMAT,
        "time_sha256" => sha256_vector_float64_le(traj.t),
        "state_sha256" => sha256_matrix_float64_le_c_order(traj.x),
    )
end
