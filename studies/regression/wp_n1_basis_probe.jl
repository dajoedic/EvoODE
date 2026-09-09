using JSON3
using LinearAlgebra
using Printf
using Random
using SHA
using Statistics

if !isdefined(@__MODULE__, :run_one)
    include(joinpath(@__DIR__, "run_regression.jl"))
end
if !isdefined(@__MODULE__, :PHASE_B_VARIANTS)
    include(joinpath(@__DIR__, "phase_b_config.jl"))
end

const WP_N1_DIM1_SYSTEM_IDS = [2, 3, 6, 8, 11, 12, 1, 5, 9, 17, 23]
const WP_N1_SEEDS = [7, 42, 123]
const WP_N1_IC_SETS = [1, 2]

const WP_N1_SUPPORT_N_SCATTER = 400
const WP_N1_SUPPORT_SCATTER_SEED = 20260907
const WP_N1_SUPPORT_ATOL = 1e-9
const WP_N1_SUPPORT_RTOL = 1e-9
const WP_N1_IDENTITY_OVERRIDE_ENV = "WP_N1_ALLOW_PLACEHOLDER_IDENTITY"
const WP_N1_PROBE_IDENTITY_DEFINITION = "collected_git_identity_v1"

function _wp_n1_output_root(dim::Int)
    return joinpath(@__DIR__, "..", "..", "outputs", "wp_n1_dim$(dim)_probe")
end

_wp_n1_history_path(dim::Int) = joinpath(_wp_n1_output_root(dim), "history.jsonl")
_wp_n1_summary_path(dim::Int) = joinpath(_wp_n1_output_root(dim), "summary.csv")

function _wp_n1_arg_dim()
    value = get(ENV, "WP_N1_DIM", "1")
    for arg in ARGS
        startswith(arg, "--dim=") && (value = split(arg, "=", limit = 2)[2])
    end
    return parse(Int, value)
end

function _wp_n1_arg_limit()
    value = nothing
    for arg in ARGS
        startswith(arg, "--limit=") && (value = split(arg, "=", limit = 2)[2])
    end
    value === nothing && return nothing
    limit = parse(Int, value)
    limit >= 0 || error("--limit must be non-negative, got $(limit)")
    return limit
end

function _wp_n1_truthy_env(name::String)
    return lowercase(strip(get(ENV, name, ""))) in ("1", "true", "yes")
end

function _wp_n1_basis_modes()
    return [
        (
            label = "wp_n1_old_basis",
            condition = "old_basis",
            basis_name = "default_staged_polynomial_basis",
            use_pretuning = false,
            constructor = PHASE_B_VARIANTS[2].constructor,
        ),
        (
            label = "wp_n1_constant_basis",
            condition = "constant_basis",
            basis_name = "staged_polynomial_basis_with_constant",
            use_pretuning = false,
            constructor = PHASE_B_VARIANTS[2].constructor,
        ),
    ]
end

function _wp_n1_build_basis(name::String, dim::Int)
    if name == "default_staged_polynomial_basis"
        return default_staged_polynomial_basis(dim)
    elseif name == "staged_polynomial_basis_with_constant"
        return staged_polynomial_basis_with_constant(dim)
    end
    error("Unknown basis $(name)")
end

function _wp_n1_support_eval_points(row, dim::Int)
    states = Matrix{Float64}[]
    for ic in WP_N1_IC_SETS
        push!(states, _phase_b_solution_trajectory(row, ic).x)
    end
    X = reduce(vcat, states)
    lo = vec(minimum(X; dims = 1))
    hi = vec(maximum(X; dims = 1))
    rng = MersenneTwister(WP_N1_SUPPORT_SCATTER_SEED)
    S = zeros(Float64, WP_N1_SUPPORT_N_SCATTER, dim)
    for i in 1:WP_N1_SUPPORT_N_SCATTER, j in 1:dim
        S[i, j] = lo[j] + rand(rng) * (hi[j] - lo[j])
    end
    return vcat(X, S)
end

function _wp_n1_design_and_rhs(rhs!, X::Matrix{Float64}, basis, dim::Int)
    p = basis_num_terms(basis)
    n = size(X, 1)
    phi = zeros(Float64, n, p)
    rhs = zeros(Float64, n, dim)
    du = zeros(Float64, dim)
    valid = trues(n)
    for r in 1:n
        u = view(X, r, :)
        ok = true
        try
            for c in 1:p
                phi[r, c] = basis_term_func(basis, c)(u, 0.0)
            end
            rhs!(du, u, nothing, 0.0)
            rhs[r, :] .= du
        catch
            ok = false
        end
        valid[r] = ok && all(isfinite, view(phi, r, :)) && all(isfinite, du)
    end
    return phi[valid, :], rhs[valid, :]
end

function _wp_n1_derive_support(rhs!, X::Matrix{Float64}, basis, dim::Int)
    phi, rhs = _wp_n1_design_and_rhs(rhs!, X, basis, dim)
    size(phi, 1) >= size(phi, 2) || return (nothing, "too_few_valid_points")
    all(isfinite, phi) || return (nothing, "nonfinite_design")
    all(isfinite, rhs) || return (nothing, "nonfinite_rhs")
    rank(phi) == size(phi, 2) || return (nothing, "rank_deficient")

    support = Vector{Vector{Int}}()
    for eq in 1:dim
        target = rhs[:, eq]
        tol = WP_N1_SUPPORT_ATOL + WP_N1_SUPPORT_RTOL * max(norm(target), 1.0)
        coefs = phi \ target
        norm(phi * coefs - target) <= tol || return (nothing, "eq$(eq)_not_representable")

        keep = collect(1:size(phi, 2))
        for cand in sort(keep; by = i -> abs(coefs[i]))
            trial = filter(!=(cand), keep)
            if isempty(trial)
                norm(target) <= tol && (keep = trial)
                continue
            end
            sub = @view phi[:, trial]
            if norm(sub * (sub \ target) - target) <= tol
                keep = trial
            end
        end
        push!(support, sort(keep))
    end
    return (support, "ok")
end

function _wp_n1_stage_for_term_idx(basis::StagedPolynomialBasis, term_idx::Int)
    for (stage, terms) in enumerate(basis.term_groups)
        term_idx in terms && return stage
    end
    error("Term index $(term_idx) is not present in staged basis")
end

function _wp_n1_system_for_basis(system, basis_name::String, rows)
    dim = Int(system[:dim])
    basis = _wp_n1_build_basis(basis_name, dim)
    X = _wp_n1_support_eval_points(rows[Int(system[:system_id])], dim)
    support, status = _wp_n1_derive_support(system[:rhs!], X, basis, dim)
    expected_stage = support === nothing ? nothing :
        maximum(_wp_n1_stage_for_term_idx(basis, idx) for eq in support for idx in eq)
    copy_system = Dict{Symbol, Any}(system)
    copy_system[:expected_support] = support
    copy_system[:expected_stage] = expected_stage
    copy_system[:representability] = support === nothing ? "surrogate" : "exact"
    copy_system[:wp_n1_support_status] = status
    copy_system[:wp_n1_support_terms] = support === nothing ? nothing :
        [[basis_term_name(basis, idx) for idx in eq] for eq in support]
    return copy_system
end

function _wp_n1_fingerprint(dim::Int)
    payload = (
        task = "WP-N1",
        dim = dim,
        system_ids = dim == 1 ? WP_N1_DIM1_SYSTEM_IDS : [Int(s[:system_id]) for s in PHASE_B_SYSTEMS if Int(s[:dim]) == dim],
        seeds = WP_N1_SEEDS,
        ic_sets = WP_N1_IC_SETS,
        variants = [(label = String(v.label), basis_name = String(v.basis_name), use_pretuning = Bool(v.use_pretuning)) for v in _wp_n1_basis_modes()],
        base_config_fingerprint = phase_b_fingerprint(),
        stage_cap_behavior_fingerprint = stage_cap_behavior_fingerprint(),
    )
    return bytes2hex(sha256(codeunits(canonical_value(payload))))[1:16]
end

function _wp_n1_has_identity(record, identity_context::AbstractDict)
    haskey(record, :probe_identity_definition) || return false
    haskey(record, :probe_identity_mode) || return false
    String(getproperty(record, :probe_identity_definition)) == WP_N1_PROBE_IDENTITY_DEFINITION || return false
    String(getproperty(record, :probe_identity_mode)) == String(identity_context["probe_identity_mode"]) || return false
    return true
end

function _wp_n1_completed(path::String, fingerprint::String, identity_context::AbstractDict)
    completed = Set{Tuple{String, Int, Int, Int}}()
    isfile(path) || return completed
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            record = JSON3.read(line)
            getproperty(record, :config_fingerprint) == fingerprint || continue
            _wp_n1_has_identity(record, identity_context) || continue
            getproperty(record, :error) === nothing || continue
            push!(
                completed,
                (
                    String(getproperty(record, :variant)),
                    Int(getproperty(record, :system_id)),
                    Int(getproperty(record, :initial_condition_set)),
                    Int(getproperty(record, :seed)),
                ),
            )
        end
    end
    return completed
end

function _wp_n1_invalid_git_hash_reason(provenance)
    git_hash = provenance.git_hash
    git_hash === nothing && return "git_hash is missing"
    value = strip(String(git_hash))
    isempty(value) && return "git_hash is empty"
    lowercase(value) in ("not_collected", "unknown") && return "git_hash is placeholder $(repr(value))"
    return nothing
end

function _wp_n1_identity_context(provenance)
    reason = _wp_n1_invalid_git_hash_reason(provenance)
    if reason === nothing
        return Dict{String, Any}(
            "probe_identity_definition" => WP_N1_PROBE_IDENTITY_DEFINITION,
            "probe_identity_mode" => "collected",
            "probe_identity_override_env" => nothing,
            "probe_identity_override_reason" => nothing,
        )
    end
    if _wp_n1_truthy_env(WP_N1_IDENTITY_OVERRIDE_ENV)
        return Dict{String, Any}(
            "probe_identity_definition" => WP_N1_PROBE_IDENTITY_DEFINITION,
            "probe_identity_mode" => "development",
            "probe_identity_override_env" => WP_N1_IDENTITY_OVERRIDE_ENV,
            "probe_identity_override_reason" => reason,
        )
    end
    error(
        "WP-N1 identity guard failed: $(reason). " *
        "A probe run without collected git identity is invalid for configuration decisions; " *
        "set $(WP_N1_IDENTITY_OVERRIDE_ENV)=1 only for development records."
    )
end

function _wp_n1_append!(path::String, record)
    mkpath(dirname(path))
    open(path, "a") do io
        JSON3.write(io, json_safe(record))
        write(io, '\n')
    end
end

function _wp_n1_quote_csv(value)
    value === nothing && return ""
    text = String(value)
    return "\"" * replace(text, "\"" => "\"\"") * "\""
end

function _wp_n1_write_summary(history_path::String, summary_path::String, fingerprint::String, identity_context::AbstractDict)
    records = Any[]
    if isfile(history_path)
        open(history_path, "r") do io
            for line in eachline(io)
                isempty(strip(line)) && continue
                record = JSON3.read(line)
                getproperty(record, :config_fingerprint) == fingerprint || continue
                _wp_n1_has_identity(record, identity_context) || continue
                push!(records, record)
            end
        end
    end

    mkpath(dirname(summary_path))
    open(summary_path, "w") do io
        println(io, "basis_name,system_id,representability,successful_runs,exact_matches,exact_match_rate,median_loss,support_terms")
        if !isempty(records)
            for basis_name in ("default_staged_polynomial_basis", "staged_polynomial_basis_with_constant")
                for system_id in sort(unique(Int(getproperty(r, :system_id)) for r in records))
                    group = [r for r in records if String(getproperty(r, :basis_name)) == basis_name && Int(getproperty(r, :system_id)) == system_id]
                    isempty(group) && continue
                    successful = [r for r in group if getproperty(r, :error) === nothing]
                    losses = Float64[Float64(getproperty(r, :loss)) for r in successful if getproperty(r, :loss) !== nothing]
                    matches = count(r -> getproperty(r, :pruned_match) === true, successful)
                    comparable = [r for r in successful if getproperty(r, :pruned_match) !== nothing]
                    exact_rate = isempty(comparable) ? nothing : matches / length(comparable)
                    support_terms = haskey(group[1], :wp_n1_expected_support_terms) ? getproperty(group[1], :wp_n1_expected_support_terms) : nothing
                    fields = [
                        basis_name,
                        string(system_id),
                        String(getproperty(group[1], :representability)),
                        string(length(successful)),
                        string(matches),
                        exact_rate === nothing ? "" : @sprintf("%.6f", exact_rate),
                        isempty(losses) ? "" : @sprintf("%.12e", median(losses)),
                        JSON3.write(support_terms),
                    ]
                    println(io, join(_wp_n1_quote_csv.(fields), ","))
                end
            end
        end
    end
end

function main()
    dim = _wp_n1_arg_dim()
    dim <= 2 || error("WP-N1 probe only prepares dim=1 or dim=2 commands")
    limit = _wp_n1_arg_limit()
    allow_dim2 = _wp_n1_truthy_env("WP_N1_ALLOW_DIM2")
    if dim != 1 && !allow_dim2
        error("WP-N1 Codex run is limited to dimension 1; set WP_N1_ALLOW_DIM2=1 to run dim=$(dim)")
    end

    output_root = _wp_n1_output_root(dim)
    history_path = _wp_n1_history_path(dim)
    summary_path = _wp_n1_summary_path(dim)
    mkpath(output_root)
    rows = Dict(Int(r["id"]) => r for r in _phase_b_dataset_rows())
    if dim == 1
        base_systems = [s for s in PHASE_B_SYSTEMS if Int(s[:dim]) == dim && Int(s[:system_id]) in WP_N1_DIM1_SYSTEM_IDS]
        order = Dict(id => i for (i, id) in enumerate(WP_N1_DIM1_SYSTEM_IDS))
        sort!(base_systems; by = s -> order[Int(s[:system_id])])
    else
        base_systems = sort([s for s in PHASE_B_SYSTEMS if Int(s[:dim]) == dim]; by = s -> Int(s[:system_id]))
    end

    variants = _wp_n1_basis_modes()
    fingerprint = _wp_n1_fingerprint(dim)
    provenance = git_provenance()
    identity_context = _wp_n1_identity_context(provenance)
    completed = fresh_requested() ? Set{Tuple{String, Int, Int, Int}}() : _wp_n1_completed(history_path, fingerprint, identity_context)
    base_config_fingerprint = phase_b_fingerprint()
    full_total = length(variants) * length(base_systems) * length(WP_N1_IC_SETS) * length(WP_N1_SEEDS)
    total = limit === nothing ? full_total : min(limit, full_total)
    run_index = 0
    appended = 0
    skipped = 0

    println("WP-N1 fingerprint: $(fingerprint)")
    println("Git: $(provenance.git_hash), dirty=$(provenance.git_dirty), identity_mode=$(identity_context["probe_identity_mode"])")
    println("Output: $(output_root)")
    println("Total cells: $(total)")

    for variant in variants
        systems = [_wp_n1_system_for_basis(system, String(variant.basis_name), rows) for system in base_systems]
        for system in systems
            for ic_set in WP_N1_IC_SETS
                for seed in WP_N1_SEEDS
                    run_index >= total && break
                    run_index += 1
                    key = (String(variant.label), Int(system[:system_id]), ic_set, seed)
                    if key in completed
                        skipped += 1
                        println(@sprintf("[%d/%d] skipped variant=%s sys=%d ic=%d seed=%d", run_index, total, variant.label, Int(system[:system_id]), ic_set, seed))
                        continue
                    end
                    record = run_one(
                        variant,
                        system,
                        ic_set,
                        seed,
                        fingerprint,
                        provenance;
                        heartbeat_path = joinpath(output_root, "heartbeats", "$(variant.label)_sys$(Int(system[:system_id]))_ic$(ic_set)_seed$(seed).heartbeat.jsonl"),
                        heartbeat_extra = Dict(
                            "entry_point" => "wp_n1_basis_probe",
                            "basis_name" => String(variant.basis_name),
                        ),
                    )
                    record["base_config_fingerprint"] = base_config_fingerprint
                    merge!(record, identity_context)
                    record["wp_n1_expected_support_terms"] = system[:wp_n1_support_terms]
                    record["wp_n1_support_status"] = system[:wp_n1_support_status]
                    _wp_n1_append!(history_path, record)
                    appended += 1
                    println(summary_line(record))
                end
            end
        end
    end

    _wp_n1_write_summary(history_path, summary_path, fingerprint, identity_context)
    println("Skipped completed: $(skipped)")
    println("Appended: $(appended)")
    println("Summary: $(summary_path)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
