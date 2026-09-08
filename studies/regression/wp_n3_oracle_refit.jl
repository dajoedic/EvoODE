import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf
using Random
using SHA
using Statistics

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_b_config.jl"))

const WP_N3_DEFAULT_INPUT = joinpath(@__DIR__, "..", "..", "outputs", "wp_n1_dim1_probe", "history.jsonl")
const WP_N3_DEFAULT_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "wp_n3_oracle_refit")
const WP_N3_R2_THRESHOLD = 0.9

function _arg_value(args::Vector{String}, name::String, default)
    idx = findfirst(==(name), args)
    idx === nothing && return default
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _arg_flag(args::Vector{String}, name::String)
    return name in args
end

function _wp_n3_fingerprint(input_path::AbstractString)
    payload = (
        task = "WP-N3",
        input_path = replace(abspath(input_path), Char(0x5c) => '/'),
        input_sha256 = bytes2hex(sha256(read(input_path))),
        refit_optimizer = (
            maxiters = BFGS_MAXITERS,
            abstol = BFGS_ABSTOL,
            reltol = BFGS_RELTOL,
            maxiters_solve = BFGS_MAXITERS_SOLVE,
            max_loss_evals = BFGS_MAX_LOSS_EVALS,
            clamp_val = BFGS_CLAMP_VAL,
            reject_nonfinite = BFGS_REJECT_NONFINITE,
            divergence_limit = BFGS_DIVERGENCE_LIMIT,
        ),
        r2_threshold = WP_N3_R2_THRESHOLD,
    )
    return bytes2hex(sha256(codeunits(canonical_value(payload))))[1:16]
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
        names === nothing &&
            error("wp_n1_expected_support_terms[$(eq)] is null")
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

function _terms_from_model(record, dim::Int)
    model_terms = _json_require(record, :model_terms, "original structure")
    length(model_terms) == dim ||
        error("model_terms has $(length(model_terms)) equations, expected $(dim)")
    out = Vector{Vector{Int}}()
    for eq in 1:dim
        model_terms[eq] === nothing &&
            error("model_terms[$(eq)] is null")
        push!(out, sort(unique(Int[Int(_json_require(term, :term_index, "model_terms[$(eq)]")) for term in model_terms[eq]])))
    end
    return out
end

function _pruned_terms_from_model(record, dim::Int)
    model_terms = _json_require(record, :model_terms, "pruned original structure")
    length(model_terms) == dim ||
        error("model_terms has $(length(model_terms)) equations, expected $(dim)")
    out = Vector{Vector{Int}}()
    for eq in 1:dim
        model_terms[eq] === nothing &&
            error("model_terms[$(eq)] is null")
        coeffs = Float64[Float64(_json_require(term, :coefficient, "model_terms[$(eq)]")) for term in model_terms[eq]]
        max_abs = isempty(coeffs) ? 0.0 : maximum(abs, coeffs)
        threshold = max(1e-6, 1e-3 * max_abs)
        kept = Int[]
        for (idx, term) in enumerate(model_terms[eq])
            abs(coeffs[idx]) >= threshold &&
                push!(kept, Int(_json_require(term, :term_index, "model_terms[$(eq)]")))
        end
        push!(out, sort(unique(kept)))
    end
    return out
end

function _term_names(terms_by_eq, basis)
    terms_by_eq === nothing && return nothing
    return [[basis_term_name(basis, idx) for idx in eq_terms] for eq_terms in terms_by_eq]
end

function _same_terms(lhs, rhs)
    (lhs === nothing || rhs === nothing) && return false
    length(lhs) == length(rhs) || return false
    return all(sort(unique(l)) == sort(unique(r)) for (l, r) in zip(lhs, rhs))
end

function _intersect_terms(found, truth)
    (found === nothing || truth === nothing) && return nothing
    return [sort(collect(intersect(Set(found_eq), Set(true_eq)))) for (found_eq, true_eq) in zip(found, truth)]
end

function _category_flags(found, pruned, truth)
    if truth === nothing
        return Dict(
            "structure_hit" => false,
            "extra_term_survives" => false,
            "true_term_deleted" => false,
            "true_term_never_found" => false,
            "both_pruning_error" => false,
            "category" => "not_representable",
        )
    end
    extra = false
    deleted = false
    never = false
    for (found_eq, pruned_eq, true_eq) in zip(found, pruned, truth)
        found_set = Set(found_eq)
        pruned_set = Set(pruned_eq)
        true_set = Set(true_eq)
        !isempty(setdiff(pruned_set, true_set)) && (extra = true)
        !isempty(intersect(setdiff(found_set, pruned_set), true_set)) && (deleted = true)
        !isempty(setdiff(true_set, found_set)) && (never = true)
    end
    hit = _same_terms(pruned, truth)
    category = hit ? "hit" :
        never ? "true_term_never_found" :
        (extra && deleted) ? "extra_survives_and_true_deleted" :
        extra ? "extra_term_survives" :
        deleted ? "true_term_deleted" :
        "other_miss"
    return Dict(
        "structure_hit" => hit,
        "extra_term_survives" => extra,
        "true_term_deleted" => deleted,
        "true_term_never_found" => never,
        "both_pruning_error" => extra && deleted,
        "category" => category,
    )
end

function _fit_fixed_structure(structure_terms, system, basis, traj, seed::Int)
    structure = StructureSpec([sort(unique(Int[x for x in eq])) for eq in structure_terms])
    f!, n_params, _ = build_rhs(structure, basis)
    optimizer = build_reference_optimizer()
    options = build_options(seed)

    params = Float64[]
    fit_loss = nothing
    fit_meta = nothing
    Random.seed!(seed)
    if n_params == 0
        params = Float64[]
    else
        params, fit_loss, fit_meta = fit_parameters(optimizer, f!, traj, n_params, MSELoss(), options)
    end

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
    loss_value = evaluate_loss(MSELoss(), yhat, traj.x)
    r2_metrics = r2_summary(yhat, traj.x, loss_value)

    return Dict{String, Any}(
        "loss" => loss_value,
        "r2" => r2_metrics.r2,
        "r2_by_dim" => r2_metrics.r2_by_dim,
        "coefficients" => active_model_terms(structure, basis, params),
        "optimizer_loss" => fit_loss,
        "fit_meta" => fit_meta,
    )
end

function _ratio(numerator, denominator)
    (numerator === nothing || denominator === nothing) && return nothing
    den = Float64(denominator)
    den == 0.0 && return nothing
    return Float64(numerator) / den
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

function _run_record(record, systems_by_id)
    system_id = Int(_json_require(record, :system_id, "trajectory selection"))
    haskey(systems_by_id, system_id) || error("Unknown system_id=$(system_id)")
    system = systems_by_id[system_id]
    dim = Int(system[:dim])
    basis_name = String(_json_require(record, :basis_name, "basis reconstruction"))
    basis = _basis_from_name(basis_name, dim)
    seed = Int(_json_require(record, :seed, "refit seed"))
    ic_set = Int(_json_require(record, :initial_condition_set, "trajectory selection"))
    traj = build_trajectory(system, ic_set)

    original_terms = _terms_from_model(record, dim)
    original_pruned_terms = _pruned_terms_from_model(record, dim)
    true_terms = _terms_from_expected(record, basis, dim)
    oracle_terms = _intersect_terms(original_terms, true_terms)
    flags = _category_flags(original_terms, original_pruned_terms, true_terms)

    oracle_result = nothing
    reference_result = nothing
    error_text = nothing
    if true_terms === nothing
        error_text = "true support is unavailable for this basis"
    else
        oracle_result = _fit_fixed_structure(oracle_terms, system, basis, traj, seed)
        reference_result = _fit_fixed_structure(true_terms, system, basis, traj, seed)
    end

    exact_original = true_terms !== nothing && _same_terms(original_pruned_terms, true_terms)
    exact_structure_deviation = exact_original && !_same_terms(oracle_terms, true_terms)

    return Dict{String, Any}(
        "cell_key" => _record_key(record),
        "system_id" => system_id,
        "system_name" => String(_json_require(record, :system_name, "output row")),
        "initial_condition_set" => ic_set,
        "seed" => seed,
        "condition" => String(_json_require(record, :condition, "output row")),
        "basis_name" => basis_name,
        "support_status" => String(_json_get(record, :wp_n1_support_status, "unknown")),
        "original_structure" => _term_names(original_terms, basis),
        "original_pruned_structure" => _term_names(original_pruned_terms, basis),
        "oracle_structure" => _term_names(oracle_terms, basis),
        "true_structure" => _term_names(true_terms, basis),
        "original_loss" => Float64(_json_require(record, :loss, "loss ratios")),
        "oracle_loss" => oracle_result === nothing ? nothing : oracle_result["loss"],
        "reference_loss" => reference_result === nothing ? nothing : reference_result["loss"],
        "original_r2" => _json_get(record, :r2),
        "oracle_r2" => oracle_result === nothing ? nothing : oracle_result["r2"],
        "reference_r2" => reference_result === nothing ? nothing : reference_result["r2"],
        "original_structure_hit" => Bool(flags["structure_hit"]),
        "oracle_structure_hit" => true_terms !== nothing && _same_terms(oracle_terms, true_terms),
        "reference_structure_hit" => true_terms !== nothing,
        "oracle_is_true_subset" => true_terms !== nothing && !_same_terms(oracle_terms, true_terms),
        "wp_n2_category" => flags["category"],
        "extra_term_survives" => flags["extra_term_survives"],
        "true_term_deleted" => flags["true_term_deleted"],
        "true_term_never_found" => flags["true_term_never_found"],
        "both_pruning_error" => flags["both_pruning_error"],
        "original_to_oracle_loss_ratio" => oracle_result === nothing ? nothing : _ratio(oracle_result["loss"], _json_require(record, :loss, "loss ratios")),
        "original_to_reference_loss_ratio" => reference_result === nothing ? nothing : _ratio(reference_result["loss"], _json_require(record, :loss, "loss ratios")),
        "oracle_to_reference_loss_ratio" => oracle_result === nothing || reference_result === nothing ? nothing : _ratio(oracle_result["loss"], reference_result["loss"]),
        "oracle_coefficients" => oracle_result === nothing ? nothing : oracle_result["coefficients"],
        "reference_coefficients" => reference_result === nothing ? nothing : reference_result["coefficients"],
        "oracle_fit_meta" => oracle_result === nothing ? nothing : oracle_result["fit_meta"],
        "reference_fit_meta" => reference_result === nothing ? nothing : reference_result["fit_meta"],
        "exact_original_structure_deviation" => exact_structure_deviation,
        "error" => error_text,
    )
end

function _append_jsonl!(path::AbstractString, record)
    mkpath(dirname(path))
    open(path, "a") do io
        JSON3.write(io, json_safe(record))
        write(io, '\n')
    end
end

function _csv_escape(value)
    value === nothing && return ""
    text = value isa AbstractString ? String(value) : string(value)
    return "\"" * replace(text, "\"" => "\"\"") * "\""
end

function _write_cell_csv(path::AbstractString, results)
    mkpath(dirname(path))
    header = [
        "cell_key", "condition", "system_id", "initial_condition_set", "seed",
        "wp_n2_category", "support_status", "original_structure_hit",
        "oracle_structure_hit", "reference_structure_hit", "oracle_is_true_subset",
        "original_loss", "oracle_loss", "reference_loss",
        "original_r2", "oracle_r2", "reference_r2",
        "original_to_oracle_loss_ratio", "original_to_reference_loss_ratio",
        "oracle_to_reference_loss_ratio", "error",
    ]
    open(path, "w") do io
        println(io, join(header, ","))
        for row in results
            println(io, join((_csv_escape(get(row, key, nothing)) for key in header), ","))
        end
    end
end

function _numeric_value(row, key::AbstractString)
    value = get(row, key, nothing)
    value === nothing && return nothing
    return Float64(value)
end

function _r2_hit(row, key::AbstractString)
    value = _numeric_value(row, key)
    return value !== nothing && value > WP_N3_R2_THRESHOLD
end

function _finite_metric_rows(results, key::AbstractString)
    return [row for row in results if _numeric_value(row, key) !== nothing && isfinite(_numeric_value(row, key))]
end

function _metric_groups(results)
    groups = Dict{String, Vector{Dict{String, Any}}}()
    groups["all"] = results
    for row in results
        for key in (
            "basis=" * String(row["condition"]),
            "category=" * String(row["wp_n2_category"]),
            "basis=" * String(row["condition"]) * ";category=" * String(row["wp_n2_category"]),
        )
            if !haskey(groups, key)
                groups[key] = Dict{String, Any}[]
            end
            push!(groups[key], row)
        end
    end
    return groups
end

function _write_metric_summary(path::AbstractString, results)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "group,n_cells,n_refit_cells,original_structure_hits,oracle_structure_hits,reference_structure_hits,original_r2_gt_0_9,oracle_r2_gt_0_9,reference_r2_gt_0_9")
        for (group, rows) in sort(collect(_metric_groups(results)); by = first)
            n_refit = count(row -> row["error"] === nothing, rows)
            fields = [
                group,
                length(rows),
                n_refit,
                count(row -> row["original_structure_hit"] === true, rows),
                count(row -> row["oracle_structure_hit"] === true, rows),
                count(row -> row["reference_structure_hit"] === true, rows),
                count(row -> _r2_hit(row, "original_r2"), rows),
                count(row -> _r2_hit(row, "oracle_r2"), rows),
                count(row -> _r2_hit(row, "reference_r2"), rows),
            ]
            println(io, join(_csv_escape.(fields), ","))
        end
    end
end

function _quantile_value(values::Vector{Float64}, p::Float64)
    isempty(values) && return nothing
    return quantile(values, p)
end

function _write_loss_quantiles(path::AbstractString, results)
    mkpath(dirname(path))
    loss_keys = ["original_loss", "oracle_loss", "reference_loss"]
    probs = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    open(path, "w") do io
        println(io, "group,metric,n,q05,q10,q25,q50,q75,q90,q95")
        for (group, rows) in sort(collect(_metric_groups(results)); by = first)
            for key in loss_keys
                values = Float64[_numeric_value(row, key) for row in rows if _numeric_value(row, key) !== nothing && isfinite(_numeric_value(row, key))]
                fields = Any[group, key, length(values)]
                append!(fields, [_quantile_value(values, p) for p in probs])
                println(io, join(_csv_escape.(fields), ","))
            end
        end
    end
end

function _write_loss_ratios(path::AbstractString, results)
    mkpath(dirname(path))
    ratio_keys = ["original_to_oracle_loss_ratio", "original_to_reference_loss_ratio", "oracle_to_reference_loss_ratio"]
    probs = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    open(path, "w") do io
        println(io, "group,metric,n,q05,q10,q25,q50,q75,q90,q95")
        for (group, rows) in sort(collect(_metric_groups(results)); by = first)
            for key in ratio_keys
                values = Float64[_numeric_value(row, key) for row in rows if _numeric_value(row, key) !== nothing && isfinite(_numeric_value(row, key))]
                fields = Any[group, key, length(values)]
                append!(fields, [_quantile_value(values, p) for p in probs])
                println(io, join(_csv_escape.(fields), ","))
            end
        end
    end
end

function _write_deviations(path::AbstractString, results)
    mkpath(dirname(path))
    rows = [row for row in results if row["exact_original_structure_deviation"] === true]
    open(path, "w") do io
        println(io, "cell_key,condition,system_id,initial_condition_set,seed,original_pruned_structure,oracle_structure,true_structure")
        for row in rows
            fields = [
                row["cell_key"],
                row["condition"],
                row["system_id"],
                row["initial_condition_set"],
                row["seed"],
                JSON3.write(row["original_pruned_structure"]),
                JSON3.write(row["oracle_structure"]),
                JSON3.write(row["true_structure"]),
            ]
            println(io, join(_csv_escape.(fields), ","))
        end
    end
end

function main(args = ARGS)
    input_path = _arg_value(args, "--input", WP_N3_DEFAULT_INPUT)
    output_dir = _arg_value(args, "--output-dir", WP_N3_DEFAULT_OUTPUT_DIR)
    limit_value = _arg_value(args, "--limit", nothing)
    fresh = _arg_flag(args, "--fresh")
    result_path = joinpath(output_dir, "results.jsonl")
    cell_csv_path = joinpath(output_dir, "cells.csv")
    metric_summary_path = joinpath(output_dir, "metric_summary.csv")
    loss_quantiles_path = joinpath(output_dir, "loss_quantiles.csv")
    loss_ratios_path = joinpath(output_dir, "loss_ratios.csv")
    deviations_path = joinpath(output_dir, "exact_structure_deviations.csv")
    fingerprint_path = joinpath(output_dir, "fingerprint.txt")
    fingerprint = _wp_n3_fingerprint(input_path)

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

    println("WP-N3 fingerprint: $(fingerprint)")
    println("Input: $(input_path)")
    println("Output: $(output_dir)")
    println("Cells requested: $(run_count)")

    for (idx, record) in enumerate(Iterators.take(records, run_count))
        result = _run_record(record, systems_by_id)
        result["config_fingerprint"] = fingerprint
        push!(results, result)
        _append_jsonl!(result_path, result)
        println(@sprintf(
            "[%d/%d] %s original=%.3e oracle=%s reference=%s error=%s",
            idx,
            run_count,
            result["cell_key"],
            result["original_loss"],
            result["oracle_loss"] === nothing ? "null" : @sprintf("%.3e", result["oracle_loss"]),
            result["reference_loss"] === nothing ? "null" : @sprintf("%.3e", result["reference_loss"]),
            result["error"] === nothing ? "none" : result["error"],
        ))
    end

    _write_cell_csv(cell_csv_path, results)
    _write_metric_summary(metric_summary_path, results)
    _write_loss_quantiles(loss_quantiles_path, results)
    _write_loss_ratios(loss_ratios_path, results)
    _write_deviations(deviations_path, results)
    open(fingerprint_path, "w") do io
        println(io, fingerprint)
    end
    println("Results: $(result_path)")
    println("Cell CSV: $(cell_csv_path)")
    println("Metric summary: $(metric_summary_path)")
    println("Loss quantiles: $(loss_quantiles_path)")
    println("Loss ratios: $(loss_ratios_path)")
    println("Exact-structure deviations: $(deviations_path)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
