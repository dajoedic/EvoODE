using SHA

const PAPER2_T2A_ID = "paper2_t2a_pilot_v1"
const PAPER2_T2A_ARMS = ("oracle_prior", "guided_prior")
const PAPER2_T2A_EPSILON = 0.2
const PAPER2_T2A_PRIOR_MAPPING = "harmonic"
const PAPER2_T2A_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "experiments", PAPER2_T2A_ID)
const PAPER2_T2A_MANIFEST_PATH = joinpath(PAPER2_T2A_OUTPUT_DIR, "manifest.csv")
const PAPER2_T2A_PRIOR_DIR = joinpath(PAPER2_T2A_OUTPUT_DIR, "priors")
const PAPER2_T2A_S1_INDEX_PATH = joinpath(PAPER2_T2A_OUTPUT_DIR, "indices_s1_oracle_dim2_seed42.txt")

function _t2a_json_vector_int(value)
    return Int[Int(x) for x in value]
end

function _t2a_json_rankings(value)
    return [_t2a_json_vector_int(eq) for eq in value]
end

function load_t2a_candidate_prior(path::AbstractString)
    isfile(path) || error("Candidate prior JSON not found: $(path)")
    raw = JSON3.read(read(path, String))
    rankings = _t2a_json_rankings(raw["rankings"])
    return CandidatePrior(
        rankings;
        epsilon = Float64(raw["epsilon"]),
        mapping = String(raw["mapping"]),
        arm = String(raw["arm"]),
        source_tag = String(raw["source_tag"]),
        source_hash = String(raw["source_sha256"]),
    )
end

function t2a_prior_path(arm::AbstractString, system_id::Int, ic_set::Int)
    return joinpath(PAPER2_T2A_PRIOR_DIR, "$(arm)_system_$(lpad(system_id, 4, '0'))_ic$(ic_set).json")
end

function _portable_t2a_prior_path(path::AbstractString)
    return replace(String(path), Char(0x5c) => '/')
end

function t2a_manifest_prior_path(arm::AbstractString, system_id::Int, ic_set::Int)
    return _portable_t2a_prior_path(joinpath("priors", basename(t2a_prior_path(arm, system_id, ic_set))))
end

function _is_windows_absolute_path(path::AbstractString)
    s = String(path)
    drive_absolute = length(s) >= 3 && isletter(s[1]) && s[2] == ':' && (s[3] == '\\' || s[3] == '/')
    return drive_absolute || startswith(s, "\\")
end

function resolve_t2a_candidate_prior_path(path::AbstractString, manifest_dir::AbstractString)
    isempty(strip(String(path))) && error("T2a candidate_prior_path is empty")
    if isabspath(path) || _is_windows_absolute_path(path)
        error("T2a candidate_prior_path must be relative to the manifest directory, got absolute path: $(path)")
    end
    return normpath(joinpath(manifest_dir, split(_portable_t2a_prior_path(path), '/')...))
end

function t2a_prior_fingerprint(prior_path::AbstractString)
    prior = load_t2a_candidate_prior(prior_path)
    payload = (
        base_phase_c_config_fingerprint = phase_c_fingerprint(),
        candidate_prior = candidate_prior_payload(prior),
    )
    bytes = sha256(codeunits(canonical_value(payload)))
    return bytes2hex(bytes)[1:16]
end

function t2a_variant_for_prior(prior::CandidatePrior)
    return (
        label = "evogrow_v2_2_stage_capped",
        condition = prior.arm,
        use_pretuning = false,
        basis_name = PHASE_C_BASIS_NAME,
        max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
        constructor = (level_callback, screening_optimizer) -> EvoGrow(
            pop_size = POP_SIZE,
            n_levels = N_LEVELS,
            children_per_parent = CHILDREN_PER_PARENT,
            max_terms_per_eq = MAX_TERMS,
            λ = LAMBDA,
            progression = StageProgressionPolicy(mode = :stage_local, min_levels_per_stage = STAGE_MIN),
            usage = StageUsagePolicy(mode = :hard, new_term_bias_prob = SOFT_BIAS),
            use_pretuning = false,
            screening_optimizer = screening_optimizer,
            level_callback = level_callback,
            stage_cap_policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...),
            candidate_prior = prior,
        ),
    )
end

function t2a_manifest_rows()
    rows = NamedTuple[]
    index = 1
    systems = [system for system in sort(phase_c_exact_systems(); by = s -> Int(s[:system_id])) if Int(system[:dim]) <= 2]
    for arm in PAPER2_T2A_ARMS
        for system in systems
            for ic_set in PHASE_C_IC_SETS
                prior_path = t2a_prior_path(arm, Int(system[:system_id]), ic_set)
                fingerprint = t2a_prior_fingerprint(prior_path)
                manifest_prior_path = t2a_manifest_prior_path(arm, Int(system[:system_id]), ic_set)
                for seed in PHASE_C_SEEDS
                    push!(
                        rows,
                        (
                            index = index,
                            campaign = PAPER2_T2A_ID,
                            config_fingerprint = fingerprint,
                            variant = "evogrow_v2_2_stage_capped",
                            condition = arm,
                            use_pretuning = false,
                            basis_name = PHASE_C_BASIS_NAME,
                            max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
                            system_id = Int(system[:system_id]),
                            system_dim = Int(system[:dim]),
                            initial_condition_set = ic_set,
                            seed = seed,
                            representability = String(system[:representability]),
                            noise_sigma = 0.0,
                            subsample_rho = 0.0,
                            noise_realization = 0,
                            clamp_val = clamp_val_json(BFGS_CLAMP_VAL),
                            candidate_prior_arm = arm,
                            candidate_prior_path = manifest_prior_path,
                        ),
                    )
                    index += 1
                end
            end
        end
    end
    return rows
end

function write_t2a_manifest(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "index,campaign,config_fingerprint,variant,condition,use_pretuning,basis_name,max_fit_attempts,system_id,system_dim,initial_condition_set,seed,representability,noise_sigma,subsample_rho,noise_realization,clamp_val,candidate_prior_arm,candidate_prior_path")
        for row in rows
            println(
                io,
                join(
                    (
                        row.index,
                        row.campaign,
                        row.config_fingerprint,
                        row.variant,
                        row.condition,
                        row.use_pretuning,
                        row.basis_name,
                        row.max_fit_attempts,
                        row.system_id,
                        row.system_dim,
                        row.initial_condition_set,
                        row.seed,
                        row.representability,
                        row.noise_sigma,
                        row.subsample_rho,
                        row.noise_realization,
                        row.clamp_val,
                        row.candidate_prior_arm,
                        row.candidate_prior_path,
                    ),
                    ",",
                ),
            )
        end
    end
end

function t2a_s1_rows(rows)
    selected = [
        row for row in rows
        if row.candidate_prior_arm == "oracle_prior" &&
           row.system_dim == 2 &&
           row.seed == 42
    ]
    length(selected) == 20 || error("T2a S1 expected 20 rows, got $(length(selected))")
    return sort(selected; by = row -> row.index)
end

function write_t2a_s1_index_list(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in t2a_s1_rows(rows)
            println(io, row.index)
        end
    end
end

function is_t2a_row(row)
    return get(row, "campaign", "") == PAPER2_T2A_ID
end

function t2a_variant_from_row(row, manifest_dir::AbstractString)
    prior_path = resolve_t2a_candidate_prior_path(row["candidate_prior_path"], manifest_dir)
    prior = load_t2a_candidate_prior(prior_path)
    String(prior.arm) == row["candidate_prior_arm"] ||
        error("T2a prior arm mismatch: row=$(row["candidate_prior_arm"]) prior=$(prior.arm)")
    return t2a_variant_for_prior(prior)
end

function t2a_fingerprint_from_row(row, manifest_dir::AbstractString)
    prior_path = resolve_t2a_candidate_prior_path(row["candidate_prior_path"], manifest_dir)
    return t2a_prior_fingerprint(prior_path)
end
