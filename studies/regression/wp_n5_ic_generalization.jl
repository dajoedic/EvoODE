import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf
using SHA
using Statistics

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_b_config.jl"))
include(joinpath(@__DIR__, "wp_n25_phase_c_c5_common.jl"))

const WP_N5_DEFAULT_INPUT = joinpath(@__DIR__, "..", "..", "outputs", "wp_n1_dim1_probe", "history.jsonl")
const WP_N5_DEFAULT_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "wp_n5_ic_generalization")
const WP_N5_R2_THRESHOLD = 0.9
const WP_N5_RECONSTRUCTION_ATOL = 1e-8
const WP_N5_RECONSTRUCTION_RTOL = 1e-6
const WP_N5_QUANTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]

function _arg_value(args::Vector{String}, name::String, default)
    idx = findfirst(==(name), args)
    idx === nothing && return default
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _arg_flag(args::Vector{String}, name::String)
    return name in args
end

function _json_has(record, key::Symbol)
    if record isa AbstractDict
        return haskey(record, key) || haskey(record, String(key))
    end
    return key in propertynames(record)
end

function _json_get(record, key::Symbol, default = nothing)
    if record isa AbstractDict
        haskey(record, key) && return record[key]
        string_key = String(key)
        haskey(record, string_key) && return record[string_key]
        return default
    end
    return _json_has(record, key) ? getproperty(record, key) : default
end

function _json_require(record, key::Symbol, context::AbstractString)
    value = _json_get(record, key)
    value === nothing && error("Input record missing required field $(key) for $(context)")
    return value
end

function _read_history(path::AbstractString)
    isfile(path) || error("Input history not found: $(path)")
    records = Any[]
    open(path, "r") do io
        for (line_no, line) in enumerate(eachline(io))
            isempty(strip(line)) && continue
            record = JSON3.read(line)
            _json_get(record, :error) === nothing ||
                error("Input line $(line_no) has error=$(_json_get(record, :error))")
            push!(records, record)
        end
    end
    return records
end

function _basis_from_name(name::AbstractString, dim::Int)
    name == "default_staged_polynomial_basis" && return default_staged_polynomial_basis(dim)
    name == "staged_polynomial_basis_with_constant" && return staged_polynomial_basis_with_constant(dim)
    error("Unknown basis_name=$(name)")
end

function _name_to_idx(basis)
    return Dict(basis_term_name(basis, i) => i for i in 1:basis_num_terms(basis))
end

function _terms_from_expected(record, basis, dim::Int)
    terms = _json_get(record, :wp_n1_expected_support_terms)
    terms === nothing && return nothing
    length(terms) == dim ||
        error("wp_n1_expected_support_terms has $(length(terms)) equations, expected $(dim)")
    name_to_idx = _name_to_idx(basis)
    out = Vector{Vector{Int}}()
    for eq in 1:dim
        names = terms[eq]
        names === nothing && error("wp_n1_expected_support_terms[$(eq)] is null")
        eq_terms = Int[]
        for name in names
            term_name = String(name)
            haskey(name_to_idx, term_name) ||
                error("Term $(term_name) from wp_n1_expected_support_terms[$(eq)] is not in basis $(typeof(basis))")
            push!(eq_terms, name_to_idx[term_name])
        end
        push!(out, sort(unique(eq_terms)))
    end
    return out
end

function _model_from_record(record, basis, dim::Int)
    model_terms = _json_require(record, :model_terms, "record model reconstruction")
    length(model_terms) == dim ||
        error("model_terms has $(length(model_terms)) equations, expected $(dim)")

    structure_terms = Vector{Vector{Int}}()
    params = Float64[]
    term_names = Vector{Vector{String}}()
    for eq in 1:dim
        model_terms[eq] === nothing && error("model_terms[$(eq)] is null")
        eq_terms = Int[]
        eq_names = String[]
        for term in model_terms[eq]
            term_idx = Int(_json_require(term, :term_index, "model_terms[$(eq)]"))
            1 <= term_idx <= basis_num_terms(basis) ||
                error("model_terms[$(eq)] term_index $(term_idx) outside basis with $(basis_num_terms(basis)) terms")
            push!(eq_terms, term_idx)
            push!(eq_names, basis_term_name(basis, term_idx))
            push!(params, Float64(_json_require(term, :coefficient, "model_terms[$(eq)]")))
        end
        push!(structure_terms, eq_terms)
        push!(term_names, eq_names)
    end
    return StructureSpec(structure_terms), params, term_names
end

function _pruned_terms(structure::StructureSpec, params::Vector{Float64})
    return pruned_support_idxs(structure, params)
end

function _same_terms(lhs, rhs)
    (lhs === nothing || rhs === nothing) && return false
    length(lhs) == length(rhs) || return false
    return all(sort(unique(l)) == sort(unique(r)) for (l, r) in zip(lhs, rhs))
end

function _target_ic_set(source_ic_set::Int)
    source_ic_set == 1 && return 2
    source_ic_set == 2 && return 1
    error("WP-N5 expects IC set 1 or 2, got $(source_ic_set)")
end

function _record_key(record)
    return @sprintf(
        "%s_sys%d_ic%d_seed%d",
        String(_json_require(record, :condition, "cell key")),
        Int(_json_require(record, :system_id, "cell key")),
        Int(_json_require(record, :initial_condition_set, "cell key")),
        Int(_json_require(record, :seed, "cell key")),
    )
end

function _direction(source_ic_set::Int)
    return source_ic_set == 1 ? "IC1_to_IC2" : "IC2_to_IC1"
end

function _simulate_fixed_model(structure::StructureSpec, basis, params::Vector{Float64}, traj::Trajectory)
    f!, n_params, _ = build_rhs(structure, basis)
    length(params) == n_params ||
        error("Record parameter count $(length(params)) does not match reconstructed RHS parameter count $(n_params)")
    optimizer = build_reference_optimizer()
    options = build_options(0)
    yhat = simulate(
        f!,
        params,
        traj;
        abstol = optimizer.abstol,
        reltol = optimizer.reltol,
        maxiters = optimizer.maxiters_solve,
        clamp_val = optimizer.clamp_val,
        reject_nonfinite = optimizer.reject_nonfinite,
        divergence_limit = optimizer.divergence_limit,
        options = options,
    )
    all(isfinite, yhat) || error("non-finite prediction values")
    loss_value = evaluate_loss(MSELoss(), yhat, traj.x)
    isfinite(Float64(loss_value)) || error("non-finite loss")
    r2_metrics = r2_summary(yhat, traj.x, loss_value)
    return loss_value, r2_metrics
end

function _evaluation_failure(err)
    message = sprint(showerror, err)
    return Dict{String, Any}(
        "loss" => nothing,
        "r2" => nothing,
        "r2_by_dim" => nothing,
        "diverged_or_nonfinite" => true,
        "error" => message,
    )
end

function _evaluate_regime(structure, basis, params, traj)
    try
        loss_value, r2_metrics = _simulate_fixed_model(structure, basis, params, traj)
        return Dict{String, Any}(
            "loss" => loss_value,
            "r2" => r2_metrics.r2,
            "r2_by_dim" => r2_metrics.r2_by_dim,
            "diverged_or_nonfinite" => false,
            "error" => nothing,
        )
    catch err
        return _evaluation_failure(err)
    end
end

function _reconstruction_ok(stored_loss, reconstructed_loss)
    reconstructed_loss === nothing && return false
    stored = Float64(stored_loss)
    got = Float64(reconstructed_loss)
    return abs(got - stored) <= WP_N5_RECONSTRUCTION_ATOL + WP_N5_RECONSTRUCTION_RTOL * abs(stored)
end

function _run_record(record, systems_by_id)
    system_id = Int(_json_require(record, :system_id, "trajectory selection"))
    haskey(systems_by_id, system_id) || error("Unknown system_id=$(system_id)")
    system = systems_by_id[system_id]
    dim = Int(system[:dim])
    source_ic_set = Int(_json_require(record, :initial_condition_set, "trajectory selection"))
    target_ic_set = _target_ic_set(source_ic_set)
    basis_name = String(_json_require(record, :basis_name, "basis reconstruction"))
    basis = _basis_from_name(basis_name, dim)
    structure, params, term_names = _model_from_record(record, basis, dim)

    source_traj = build_trajectory(system, source_ic_set)
    target_traj = build_trajectory(system, target_ic_set)
    reconstruction = _evaluate_regime(structure, basis, params, source_traj)
    generalization = _evaluate_regime(structure, basis, params, target_traj)

    expected_terms = _terms_from_expected(record, basis, dim)
    structure_hit = if _json_get(record, :pruned_match) !== nothing
        Bool(_json_get(record, :pruned_match))
    else
        _same_terms(_pruned_terms(structure, params), expected_terms)
    end
    stored_loss = Float64(_json_require(record, :loss, "reconstruction probe"))
    reconstruction_ok = _reconstruction_ok(stored_loss, reconstruction["loss"])

    return Dict{String, Any}(
        "cell_key" => _record_key(record),
        "condition" => String(_json_require(record, :condition, "output row")),
        "variant" => String(_json_require(record, :variant, "output row")),
        "basis_name" => basis_name,
        "system_id" => system_id,
        "system_name" => String(_json_require(record, :system_name, "output row")),
        "dimension" => dim,
        "source_initial_condition_set" => source_ic_set,
        "target_initial_condition_set" => target_ic_set,
        "direction" => _direction(source_ic_set),
        "seed" => Int(_json_require(record, :seed, "output row")),
        "structure_hit" => structure_hit,
        "model_terms" => term_names,
        "stored_reconstruction_loss" => stored_loss,
        "reconstruction_loss" => reconstruction["loss"],
        "reconstruction_r2" => reconstruction["r2"],
        "reconstruction_r2_by_dim" => reconstruction["r2_by_dim"],
        "reconstruction_diverged_or_nonfinite" => reconstruction["diverged_or_nonfinite"],
        "reconstruction_error" => reconstruction["error"],
        "reconstruction_probe_ok" => reconstruction_ok,
        "reconstruction_abs_loss_delta" => reconstruction["loss"] === nothing ? nothing : abs(Float64(reconstruction["loss"]) - stored_loss),
        "generalization_loss" => generalization["loss"],
        "generalization_r2" => generalization["r2"],
        "generalization_r2_by_dim" => generalization["r2_by_dim"],
        "generalization_diverged_or_nonfinite" => generalization["diverged_or_nonfinite"],
        "generalization_error" => generalization["error"],
    )
end

function _csv_escape(value)
    value === nothing && return ""
    text = value isa AbstractString ? String(value) : string(value)
    return "\"" * replace(text, "\"" => "\"\"") * "\""
end

function _write_csv(path::AbstractString, header::Vector{String}, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(header, ","))
        for row in rows
            println(io, join((_csv_escape(get(row, key, nothing)) for key in header), ","))
        end
    end
end

function _append_jsonl!(path::AbstractString, record)
    mkpath(dirname(path))
    open(path, "a") do io
        JSON3.write(io, json_safe(record))
        write(io, '\n')
    end
end

function _numeric_value(row, key::AbstractString)
    value = get(row, key, nothing)
    value === nothing && return nothing
    return Float64(value)
end

function _r2_hit(value)
    value === nothing && return false
    return Float64(value) > WP_N5_R2_THRESHOLD
end

function _ratio(num, den)
    den == 0 && return nothing
    return Float64(num) / Float64(den)
end

function _group_key(row)
    return (
        basis_name = String(row["basis_name"]),
        dimension = Int(row["dimension"]),
        direction = String(row["direction"]),
    )
end

function _group_rows(results)
    groups = Dict{NamedTuple, Vector{Dict{String, Any}}}()
    for row in results
        key = _group_key(row)
        if !haskey(groups, key)
            groups[key] = Dict{String, Any}[]
        end
        push!(groups[key], row)
    end
    return sort(collect(groups); by = pair -> (pair.first.basis_name, pair.first.dimension, pair.first.direction))
end

function _write_cells(path::AbstractString, results)
    header = [
        "cell_key", "condition", "variant", "basis_name", "system_id", "system_name",
        "dimension", "source_initial_condition_set", "target_initial_condition_set",
        "direction", "seed", "structure_hit", "stored_reconstruction_loss",
        "reconstruction_loss", "reconstruction_r2", "reconstruction_diverged_or_nonfinite",
        "reconstruction_probe_ok", "reconstruction_abs_loss_delta",
        "generalization_loss", "generalization_r2", "generalization_diverged_or_nonfinite",
        "generalization_error",
    ]
    _write_csv(path, header, results)
end

function _write_reconstruction_probe(path::AbstractString, results)
    header = [
        "cell_key", "basis_name", "dimension", "direction", "system_id", "seed",
        "stored_reconstruction_loss", "reconstruction_loss", "reconstruction_abs_loss_delta",
        "reconstruction_probe_ok", "reconstruction_error",
    ]
    _write_csv(path, header, results)
end

function _write_metric_summary(path::AbstractString, results)
    header = [
        "basis_name", "dimension", "direction", "regime", "n_cells",
        "structure_hit_count", "structure_hit_rate", "diverged_or_nonfinite_count",
        "r2_valid_count", "r2_gt_0_9_count", "r2_gt_0_9_rate_over_cells",
        "r2_gt_0_9_rate_over_valid",
    ]
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(header, ","))
        for (key, rows) in _group_rows(results)
            for regime in ("reconstruction", "generalization")
                r2_key = regime * "_r2"
                diverged_key = regime * "_diverged_or_nonfinite"
                n_cells = length(rows)
                structure_hits = count(row -> row["structure_hit"] === true, rows)
                diverged = count(row -> row[diverged_key] === true, rows)
                r2_values = [_numeric_value(row, r2_key) for row in rows]
                r2_valid = count(value -> value !== nothing && isfinite(value), r2_values)
                r2_hits = count(_r2_hit, r2_values)
                fields = Any[
                    key.basis_name,
                    key.dimension,
                    key.direction,
                    regime,
                    n_cells,
                    structure_hits,
                    _ratio(structure_hits, n_cells),
                    diverged,
                    r2_valid,
                    r2_hits,
                    _ratio(r2_hits, n_cells),
                    _ratio(r2_hits, r2_valid),
                ]
                println(io, join(_csv_escape.(fields), ","))
            end
        end
    end
end

function _quantile_value(values::Vector{Float64}, p::Float64)
    isempty(values) && return nothing
    return quantile(values, p)
end

function _write_loss_quantiles(path::AbstractString, results)
    header = ["basis_name", "dimension", "direction", "regime", "n", "q05", "q10", "q25", "q50", "q75", "q90", "q95"]
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(header, ","))
        for (key, rows) in _group_rows(results)
            for regime in ("reconstruction", "generalization")
                loss_key = regime * "_loss"
                values = Float64[
                    _numeric_value(row, loss_key) for row in rows
                    if _numeric_value(row, loss_key) !== nothing && isfinite(_numeric_value(row, loss_key))
                ]
                fields = Any[key.basis_name, key.dimension, key.direction, regime, length(values)]
                append!(fields, [_quantile_value(values, p) for p in WP_N5_QUANTILES])
                println(io, join(_csv_escape.(fields), ","))
            end
        end
    end
end

function _campaign_coefficients_probe(path::AbstractString)
    if !isfile(path)
        return Dict{String, Any}(
            "path" => path,
            "exists" => false,
            "rows_checked" => 0,
            "has_model_terms_column" => false,
            "has_coefficient_column" => false,
            "evaluable" => false,
        )
    end
    header = split(readline(path), ',')
    return Dict{String, Any}(
        "path" => path,
        "exists" => true,
        "rows_checked" => max(0, countlines(path) - 1),
        "has_model_terms_column" => "model_terms" in header,
        "has_coefficient_column" => "coefficient" in header || "coefficients" in header,
        "evaluable" => "model_terms" in header && ("coefficient" in header || "coefficients" in header),
        "columns" => header,
    )
end

function _wp_n5_fingerprint(input_path::AbstractString)
    campaign_path = joinpath(@__DIR__, "..", "..", "experiments", "paper1_phaseB_v1", "run_registry.csv")
    payload = (
        task = "WP-N5",
        input_path = replace(abspath(input_path), Char(0x5c) => '/'),
        input_sha256 = bytes2hex(sha256(read(input_path))),
        target_ic = "1->2 and 2->1",
        parameter_policy = "record coefficients only; no refit",
        reconstruction_probe_atol = WP_N5_RECONSTRUCTION_ATOL,
        reconstruction_probe_rtol = WP_N5_RECONSTRUCTION_RTOL,
        r2_threshold = WP_N5_R2_THRESHOLD,
        quantiles = WP_N5_QUANTILES,
        campaign_registry = replace(abspath(campaign_path), Char(0x5c) => '/'),
    )
    return bytes2hex(sha256(codeunits(canonical_value(payload))))[1:16]
end

function _wp_n5_phase_c_fingerprint(input_path::AbstractString)
    payload = (
        task = "WP-N5",
        campaign = WP_N25_PHASE_C_CAMPAIGN,
        input_path = replace(abspath(input_path), Char(0x5c) => '/'),
        input_sha256 = bytes2hex(sha256(read(input_path))),
        selected_arm = (variant = WP_N25_C1_VARIANT, use_pretuning = false),
        trajectory_source = "phase_c_systems/build_trajectory",
        parameter_policy = "record coefficients only; no refit",
        bfgs_max_loss_evals = BFGS_MAX_LOSS_EVALS,
        reconstruction_probe_atol = WP_N5_RECONSTRUCTION_ATOL,
        reconstruction_probe_rtol = WP_N5_RECONSTRUCTION_RTOL,
        r2_threshold = WP_N5_R2_THRESHOLD,
        quantiles = WP_N5_QUANTILES,
    )
    return bytes2hex(sha256(codeunits(canonical_value(payload))))[1:16]
end

function _run_record_phase_c(record, systems_by_id)
    system_id = Int(_json_require(record, :system_id, "Phase-C trajectory selection"))
    haskey(systems_by_id, system_id) || error("Unknown Phase-C system_id=$(system_id)")
    system = systems_by_id[system_id]
    dim = Int(system[:dim])
    source_ic_set = Int(_json_require(record, :initial_condition_set, "Phase-C trajectory selection"))
    target_ic_set = _target_ic_set(source_ic_set)
    basis_name = String(_json_require(record, :basis_name, "Phase-C basis reconstruction"))
    basis_name == PHASE_C_BASIS_NAME || error("Record $(wp_n25_record_key(record)) basis_name=$(basis_name), expected $(PHASE_C_BASIS_NAME)")
    basis = phase_c_basis(dim)
    structure, params, term_names = _model_from_record(record, basis, dim)

    source_traj = build_trajectory(system, source_ic_set)
    target_traj = build_trajectory(system, target_ic_set)
    reconstruction = _evaluate_regime(structure, basis, params, source_traj)
    generalization = _evaluate_regime(structure, basis, params, target_traj)

    structure_hit = if _json_get(record, :pruned_match) !== nothing
        Bool(_json_get(record, :pruned_match))
    else
        false
    end
    stored_loss = Float64(_json_require(record, :loss, "reconstruction probe"))
    reconstruction_ok = _reconstruction_ok(stored_loss, reconstruction["loss"])

    return Dict{String, Any}(
        "cell_key" => wp_n25_record_key(record),
        "condition" => String(_json_require(record, :condition, "output row")),
        "variant" => String(_json_require(record, :variant, "output row")),
        "basis_name" => basis_name,
        "system_id" => system_id,
        "system_name" => String(_json_require(record, :system_name, "output row")),
        "dimension" => dim,
        "source_initial_condition_set" => source_ic_set,
        "target_initial_condition_set" => target_ic_set,
        "direction" => _direction(source_ic_set),
        "seed" => Int(_json_require(record, :seed, "output row")),
        "representability" => String(_json_require(record, :representability, "output row")),
        "source_trajectory_hash" => wp_n25_trajectory_hash(system, source_ic_set, source_traj),
        "target_trajectory_hash" => wp_n25_trajectory_hash(system, target_ic_set, target_traj),
        "structure_hit" => structure_hit,
        "model_terms" => term_names,
        "stored_reconstruction_loss" => stored_loss,
        "reconstruction_loss" => reconstruction["loss"],
        "reconstruction_r2" => reconstruction["r2"],
        "reconstruction_r2_by_dim" => reconstruction["r2_by_dim"],
        "reconstruction_diverged_or_nonfinite" => reconstruction["diverged_or_nonfinite"],
        "reconstruction_error" => reconstruction["error"],
        "reconstruction_probe_ok" => reconstruction_ok,
        "reconstruction_abs_loss_delta" => reconstruction["loss"] === nothing ? nothing : abs(Float64(reconstruction["loss"]) - stored_loss),
        "generalization_loss" => generalization["loss"],
        "generalization_r2" => generalization["r2"],
        "generalization_r2_by_dim" => generalization["r2_by_dim"],
        "generalization_diverged_or_nonfinite" => generalization["diverged_or_nonfinite"],
        "generalization_error" => generalization["error"],
    )
end

function _wp_n5_write_phase_c_cost_estimate(records)
    println("Planning cost estimate only; not runtime evidence.")
    println("cell_key,dimension,fits_per_cell,integrations_per_cell,campaign_simulation_time_per_ode_solve_s,planning_upper_bound_s")
    total = 0.0
    by_dim = Dict{Int, Vector{Float64}}()
    rows = Dict{String, Any}[]
    for record in records
        system = phase_c_system(Int(_json_require(record, :system_id, "cost estimate")))
        dim = Int(system[:dim])
        sim_time = Float64(_json_require(record, :total_simulation_time_s, "cost estimate"))
        ode_solves = Int(_json_require(record, :total_ode_solves, "cost estimate"))
        ode_solves > 0 || error("Record $(wp_n25_record_key(record)) has non-positive total_ode_solves")
        per_solve = sim_time / ode_solves
        bound = 2 * per_solve
        total += bound
        if !haskey(by_dim, dim)
            by_dim[dim] = Float64[]
        end
        push!(by_dim[dim], bound)
        row = Dict{String, Any}("cell_key" => wp_n25_record_key(record), "dimension" => dim, "planning_upper_bound_s" => bound)
        push!(rows, row)
        println(join([wp_n25_record_key(record), dim, 0, 2, per_solve, bound], ","))
    end
    println("dimension,n_cells,sum_planning_upper_bound_s,max_planning_upper_bound_s")
    for dim in sort(collect(keys(by_dim)))
        println(join([dim, length(by_dim[dim]), sum(by_dim[dim]), maximum(by_dim[dim])], ","))
    end
    if isempty(rows)
        println("total_planning_upper_bound_s=0")
        println("most_expensive_cell=")
    else
        expensive = rows[argmax(Float64[row["planning_upper_bound_s"] for row in rows])]
        println("total_planning_upper_bound_s=$(total)")
        println("most_expensive_cell=$(expensive["cell_key"]) planning_upper_bound_s=$(expensive["planning_upper_bound_s"])")
    end
    return nothing
end

function _write_manifest(path::AbstractString, input_path::AbstractString, output_dir::AbstractString, run_count::Int, fingerprint::AbstractString)
    campaign_path = joinpath(@__DIR__, "..", "..", "experiments", "paper1_phaseB_v1", "run_registry.csv")
    open(path, "w") do io
        JSON3.write(io, json_safe(Dict{String, Any}(
            "task" => "WP-N5",
            "input" => input_path,
            "output_dir" => output_dir,
            "run_count" => run_count,
            "config_fingerprint" => fingerprint,
            "source" => "outputs/wp_n1_dim1_probe/history.jsonl",
            "campaign_probe" => _campaign_coefficients_probe(campaign_path),
            "parameter_policy" => "record coefficients are reused without refitting",
            "reconstruction_probe" => Dict(
                "atol" => WP_N5_RECONSTRUCTION_ATOL,
                "rtol" => WP_N5_RECONSTRUCTION_RTOL,
                "criterion" => "abs(reconstructed_loss - stored_loss) <= atol + rtol * abs(stored_loss)",
            ),
        )))
        write(io, '\n')
    end
end

function _wp_n5_write_phase_c_manifest(path, input_path, output_dir, fingerprint, filter_counts, run_count, shards, shard_index, results = nothing; collect_mode = false)
    payload = Dict{String, Any}(
        "task" => "WP-N5",
        "campaign" => WP_N25_PHASE_C_CAMPAIGN,
        "input" => input_path,
        "output_dir" => output_dir,
        "run_count" => run_count,
        "config_fingerprint" => fingerprint,
        "filter_counts" => filter_counts,
        "shards" => shards,
        "shard_index" => shard_index,
        "collect_mode" => collect_mode,
        "parameter_policy" => "record coefficients are reused without refitting",
        "trajectory_hash_format" => HASH_FORMAT,
        "reconstruction_probe" => Dict(
            "atol" => WP_N5_RECONSTRUCTION_ATOL,
            "rtol" => WP_N5_RECONSTRUCTION_RTOL,
            "criterion" => "abs(reconstructed_loss - stored_loss) <= atol + rtol * abs(stored_loss)",
        ),
    )
    if results !== nothing
        payload["reconstruction_probe_ok_count"] = count(row -> row["reconstruction_probe_ok"] === true, results)
        payload["reconstruction_probe_deviation_count"] = count(row -> row["reconstruction_probe_ok"] !== true, results)
        payload["reconstruction_deviations"] = [
            Dict(
                "cell_key" => row["cell_key"],
                "stored_reconstruction_loss" => row["stored_reconstruction_loss"],
                "reconstruction_loss" => row["reconstruction_loss"],
                "reconstruction_abs_loss_delta" => row["reconstruction_abs_loss_delta"],
            )
            for row in results if row["reconstruction_probe_ok"] !== true
        ]
    end
    wp_n25_write_manifest(path, payload)
end

function main_phase_c(args)
    input_path = _arg_value(args, "--input", PHASE_C_HISTORY_PATH)
    output_dir = _arg_value(args, "--output-dir", joinpath(@__DIR__, "..", "..", "outputs", "wp_n5_ic_generalization_phase_c"))
    shards, shard_index = wp_n25_shard_options(args)
    collect_mode = _arg_flag(args, "--collect")
    estimate_cost = _arg_flag(args, "--estimate-cost")
    records_all = _read_history(input_path)
    records, filter_counts = wp_n25_phase_c_filter(records_all; require_exact_support = false)
    limit = wp_n25_parse_limit(args, length(records))
    records = records[1:limit]
    fingerprint = _wp_n5_phase_c_fingerprint(input_path)

    if estimate_cost
        _wp_n5_write_phase_c_cost_estimate(records)
        return nothing
    end

    result_basename = "results.jsonl"
    if collect_mode
        expected_keys = [wp_n25_record_key(record) for record in records]
        results = wp_n25_collect_jsonl(output_dir, result_basename, shards, expected_keys)
        _write_cells(joinpath(output_dir, "cells.csv"), results)
        _write_reconstruction_probe(joinpath(output_dir, "reconstruction_probe.csv"), results)
        _write_metric_summary(joinpath(output_dir, "metric_summary.csv"), results)
        _write_loss_quantiles(joinpath(output_dir, "loss_quantiles.csv"), results)
        _wp_n5_write_phase_c_manifest(joinpath(output_dir, "manifest.json"), input_path, output_dir, fingerprint, filter_counts, length(records), shards, shard_index, results; collect_mode = true)
        open(joinpath(output_dir, "fingerprint.txt"), "w") do io
            println(io, fingerprint)
        end
        println("Collected $(length(results)) Phase-C WP-N5 cells")
        println("Reconstruction probe failures: $(count(row -> row["reconstruction_probe_ok"] !== true, results))")
        return nothing
    end

    shard_records = wp_n25_shard_records(records, shards, shard_index)
    result_path = wp_n25_shard_path(output_dir, result_basename, shards, shard_index)
    fresh = _arg_flag(args, "--fresh")
    if fresh && isfile(result_path)
        rm(result_path)
    end
    done = wp_n25_done_keys(result_path)
    systems_by_id = wp_n25_phase_c_systems_by_id()
    println("WP-N5 Phase-C fingerprint: $(fingerprint)")
    println("Cells requested in shard: $(length(shard_records))")
    println("Parameter policy: reuse record coefficients without refitting")
    for (idx, record) in enumerate(shard_records)
        key = wp_n25_record_key(record)
        key in done && (println("[$(idx)/$(length(shard_records))] $(key) skipped existing"); continue)
        result = _run_record_phase_c(record, systems_by_id)
        result["config_fingerprint"] = fingerprint
        _append_jsonl!(result_path, result)
        println(@sprintf(
            "[%d/%d] %s recon=%s gen=%s probe_ok=%s",
            idx,
            length(shard_records),
            key,
            result["reconstruction_loss"] === nothing ? "null" : @sprintf("%.3e", result["reconstruction_loss"]),
            result["generalization_loss"] === nothing ? "null" : @sprintf("%.3e", result["generalization_loss"]),
            result["reconstruction_probe_ok"],
        ))
    end
    _wp_n5_write_phase_c_manifest(wp_n25_shard_path(output_dir, "manifest.json", shards, shard_index), input_path, output_dir, fingerprint, filter_counts, length(shard_records), shards, shard_index)
    return nothing
end

function main(args = ARGS)
    if wp_n25_phase_c_requested(args)
        return main_phase_c(args)
    end
    input_path = _arg_value(args, "--input", WP_N5_DEFAULT_INPUT)
    output_dir = _arg_value(args, "--output-dir", WP_N5_DEFAULT_OUTPUT_DIR)
    limit_value = _arg_value(args, "--limit", nothing)
    fresh = _arg_flag(args, "--fresh")
    result_path = joinpath(output_dir, "results.jsonl")
    cells_path = joinpath(output_dir, "cells.csv")
    probe_path = joinpath(output_dir, "reconstruction_probe.csv")
    metric_summary_path = joinpath(output_dir, "metric_summary.csv")
    loss_quantiles_path = joinpath(output_dir, "loss_quantiles.csv")
    manifest_path = joinpath(output_dir, "manifest.json")
    fingerprint_path = joinpath(output_dir, "fingerprint.txt")

    fingerprint = _wp_n5_fingerprint(input_path)
    mkpath(output_dir)
    if fresh && isfile(result_path)
        rm(result_path)
    end

    records = _read_history(input_path)
    limit = limit_value === nothing ? length(records) : parse(Int, limit_value)
    limit >= 0 || error("--limit must be non-negative, got $(limit)")
    run_count = min(limit, length(records))
    systems_by_id = Dict(Int(system[:system_id]) => system for system in PHASE_B_SYSTEMS)
    results = Dict{String, Any}[]

    println("WP-N5 fingerprint: $(fingerprint)")
    println("Input: $(input_path)")
    println("Output: $(output_dir)")
    println("Cells requested: $(run_count)")
    println("Parameter policy: reuse record coefficients without refitting")

    for (idx, record) in enumerate(Iterators.take(records, run_count))
        result = _run_record(record, systems_by_id)
        result["config_fingerprint"] = fingerprint
        push!(results, result)
        _append_jsonl!(result_path, result)
        println(@sprintf(
            "[%d/%d] %s recon=%s gen=%s probe_ok=%s gen_diverged=%s",
            idx,
            run_count,
            result["cell_key"],
            result["reconstruction_loss"] === nothing ? "null" : @sprintf("%.3e", result["reconstruction_loss"]),
            result["generalization_loss"] === nothing ? "null" : @sprintf("%.3e", result["generalization_loss"]),
            result["reconstruction_probe_ok"],
            result["generalization_diverged_or_nonfinite"],
        ))
    end

    _write_cells(cells_path, results)
    _write_reconstruction_probe(probe_path, results)
    _write_metric_summary(metric_summary_path, results)
    _write_loss_quantiles(loss_quantiles_path, results)
    _write_manifest(manifest_path, input_path, output_dir, run_count, fingerprint)
    open(fingerprint_path, "w") do io
        println(io, fingerprint)
    end

    failed_probe_count = count(row -> row["reconstruction_probe_ok"] !== true, results)
    gen_diverged_count = count(row -> row["generalization_diverged_or_nonfinite"] === true, results)
    println("Results: $(result_path)")
    println("Cells CSV: $(cells_path)")
    println("Reconstruction probe: $(probe_path)")
    println("Metric summary: $(metric_summary_path)")
    println("Loss quantiles: $(loss_quantiles_path)")
    println("Manifest: $(manifest_path)")
    println("Reconstruction probe failures: $(failed_probe_count)")
    println("Generalization diverged/non-finite: $(gen_diverged_count)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
