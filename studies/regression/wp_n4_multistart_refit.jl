import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf
using Random
using SHA
using Statistics

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_b_config.jl"))

const WP_N4_DEFAULT_INPUT = joinpath(@__DIR__, "..", "..", "outputs", "wp_n1_dim1_probe", "history.jsonl")
const WP_N4_DEFAULT_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "wp_n4_multistart_refit")
const WP_N4_R2_THRESHOLD = 0.9
const WP_N4_SENTINEL_LOSS = 1e6
const WP_N4_CURVE_K = [1, 2, 3, 5, 10]

function _arg_value(args::Vector{String}, name::String, default)
    idx = findfirst(==(name), args)
    idx === nothing && return default
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

function _arg_flag(args::Vector{String}, name::String)
    return name in args
end

function _wp_n4_fingerprint(input_path::AbstractString, n_starts::Int)
    payload = (
        task = "WP-N4",
        input_path = replace(abspath(input_path), Char(0x5c) => '/'),
        input_sha256 = bytes2hex(sha256(read(input_path))),
        n_starts = n_starts,
        curve_k = WP_N4_CURVE_K,
        first_start_seed = "cell seed exactly, matching WP-N3",
        later_start_seed = "parse(Int, sha256(\"WP-N4:start:<cell_seed>:<start_index>\")[1:15], base=16)",
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
        r2_threshold = WP_N4_R2_THRESHOLD,
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

function _terms_from_model(record, dim::Int)
    model_terms = _json_require(record, :model_terms, "original structure")
    length(model_terms) == dim ||
        error("model_terms has $(length(model_terms)) equations, expected $(dim)")
    out = Vector{Vector{Int}}()
    for eq in 1:dim
        model_terms[eq] === nothing && error("model_terms[$(eq)] is null")
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
        model_terms[eq] === nothing && error("model_terms[$(eq)] is null")
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

function _start_seed(cell_seed::Int, start_index::Int)
    start_index >= 1 || error("start_index must be positive")
    start_index == 1 && return cell_seed
    digest = bytes2hex(sha256(codeunits("WP-N4:start:$(cell_seed):$(start_index)")))
    return parse(Int, digest[1:15]; base = 16)
end

function _fit_fixed_structure_once(structure_terms, basis, traj, cell_seed::Int, start_index::Int)
    structure = StructureSpec([sort(unique(Int[x for x in eq])) for eq in structure_terms])
    f!, n_params, _ = build_rhs(structure, basis)
    optimizer = build_reference_optimizer()
    seed = _start_seed(cell_seed, start_index)
    options = build_options(seed)

    params = Float64[]
    fit_loss = nothing
    fit_meta = nothing
    Random.seed!(seed)
    if n_params != 0
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
        "start_index" => start_index,
        "start_seed" => seed,
        "loss" => loss_value,
        "r2" => r2_metrics.r2,
        "r2_by_dim" => r2_metrics.r2_by_dim,
        "coefficients" => active_model_terms(structure, basis, params),
        "optimizer_loss" => fit_loss,
        "fit_meta" => fit_meta,
    )
end

function _best_result(results, k::Int)
    usable = [row for row in results if Int(row["start_index"]) <= k]
    isempty(usable) && return nothing
    return usable[argmin(Float64[row["loss"] for row in usable])]
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

function _base_record(record, systems_by_id)
    system_id = Int(_json_require(record, :system_id, "trajectory selection"))
    haskey(systems_by_id, system_id) || error("Unknown system_id=$(system_id)")
    system = systems_by_id[system_id]
    dim = Int(system[:dim])
    basis_name = String(_json_require(record, :basis_name, "basis reconstruction"))
    basis = _basis_from_name(basis_name, dim)
    seed = Int(_json_require(record, :seed, "refit seed"))
    ic_set = Int(_json_require(record, :initial_condition_set, "trajectory selection"))

    original_terms = _terms_from_model(record, dim)
    original_pruned_terms = _pruned_terms_from_model(record, dim)
    true_terms = _terms_from_expected(record, basis, dim)
    oracle_terms = _intersect_terms(original_terms, true_terms)
    flags = _category_flags(original_terms, original_pruned_terms, true_terms)

    return (
        row = Dict{String, Any}(
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
            "original_r2" => _json_get(record, :r2),
            "original_structure_hit" => Bool(flags["structure_hit"]),
            "oracle_structure_hit" => true_terms !== nothing && _same_terms(oracle_terms, true_terms),
            "reference_structure_hit" => true_terms !== nothing,
            "oracle_is_true_subset" => true_terms !== nothing && !_same_terms(oracle_terms, true_terms),
            "wp_n2_category" => flags["category"],
            "extra_term_survives" => flags["extra_term_survives"],
            "true_term_deleted" => flags["true_term_deleted"],
            "true_term_never_found" => flags["true_term_never_found"],
            "both_pruning_error" => flags["both_pruning_error"],
            "error" => true_terms === nothing ? "true support is unavailable for this basis" : nothing,
        ),
        basis = basis,
        traj = build_trajectory(system, ic_set),
        true_terms = true_terms,
        oracle_terms = oracle_terms,
    )
end

function _run_record(record, systems_by_id, n_starts::Int)
    base = _base_record(record, systems_by_id)
    row = base.row
    if base.true_terms === nothing
        row["oracle_starts"] = nothing
        row["reference_starts"] = nothing
        return row
    end

    oracle_starts = Dict{String, Any}[]
    reference_starts = Dict{String, Any}[]
    cell_seed = Int(row["seed"])
    for start_index in 1:n_starts
        push!(oracle_starts, _fit_fixed_structure_once(base.oracle_terms, base.basis, base.traj, cell_seed, start_index))
        push!(reference_starts, _fit_fixed_structure_once(base.true_terms, base.basis, base.traj, cell_seed, start_index))
    end
    row["oracle_starts"] = oracle_starts
    row["reference_starts"] = reference_starts
    return row
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

function _numeric_value(row, key::AbstractString)
    value = get(row, key, nothing)
    value === nothing && return nothing
    return Float64(value)
end

function _r2_hit(value)
    value === nothing && return false
    return Float64(value) > WP_N4_R2_THRESHOLD
end

function _is_sentinel(value)
    value === nothing && return false
    return Float64(value) >= WP_N4_SENTINEL_LOSS
end

function _quantile_value(values::Vector{Float64}, p::Float64)
    isempty(values) && return nothing
    return quantile(values, p)
end

function _write_cells_by_k(path::AbstractString, results, curve_k)
    mkpath(dirname(path))
    header = [
        "k", "structure", "cell_key", "condition", "basis_name", "system_id",
        "system_name", "initial_condition_set", "seed", "wp_n2_category",
        "support_status", "original_loss", "best_loss", "best_start_index",
        "best_start_seed", "r2", "structure_hit", "r2_gt_0_9",
        "reaches_or_beats_original", "sentinel_loss", "error",
    ]
    open(path, "w") do io
        println(io, join(header, ","))
        for row in results
            for k in curve_k
                for (structure_name, starts_key, hit_key) in (
                    ("oracle", "oracle_starts", "oracle_structure_hit"),
                    ("reference", "reference_starts", "reference_structure_hit"),
                )
                    starts = get(row, starts_key, nothing)
                    best = starts === nothing ? nothing : _best_result(starts, k)
                    best_loss = best === nothing ? nothing : best["loss"]
                    fields = Dict{String, Any}(
                        "k" => k,
                        "structure" => structure_name,
                        "cell_key" => row["cell_key"],
                        "condition" => row["condition"],
                        "basis_name" => row["basis_name"],
                        "system_id" => row["system_id"],
                        "system_name" => row["system_name"],
                        "initial_condition_set" => row["initial_condition_set"],
                        "seed" => row["seed"],
                        "wp_n2_category" => row["wp_n2_category"],
                        "support_status" => row["support_status"],
                        "original_loss" => row["original_loss"],
                        "best_loss" => best_loss,
                        "best_start_index" => best === nothing ? nothing : best["start_index"],
                        "best_start_seed" => best === nothing ? nothing : best["start_seed"],
                        "r2" => best === nothing ? nothing : best["r2"],
                        "structure_hit" => row[hit_key],
                        "r2_gt_0_9" => best === nothing ? false : _r2_hit(best["r2"]),
                        "reaches_or_beats_original" => best_loss === nothing ? false : Float64(best_loss) <= Float64(row["original_loss"]),
                        "sentinel_loss" => _is_sentinel(best_loss),
                        "error" => row["error"],
                    )
                    println(io, join((_csv_escape(get(fields, key, nothing)) for key in header), ","))
                end
            end
        end
    end
end

function _basis_groups(results)
    groups = Dict{String, Vector{Dict{String, Any}}}()
    supported = Dict{String, Any}[row for row in results if row["error"] === nothing]
    groups["all"] = supported
    for row in supported
        key = String(row["basis_name"])
        if !haskey(groups, key)
            groups[key] = Dict{String, Any}[]
        end
        push!(groups[key], row)
    end
    return groups
end

function _write_curve_summary(path::AbstractString, results, curve_k)
    mkpath(dirname(path))
    header = [
        "k", "basis", "structure", "n_cells", "sentinel_loss_cells",
        "structure_hit_cells", "structure_hit_rate", "r2_gt_0_9_cells",
        "r2_gt_0_9_rate", "reaches_or_beats_original_cells",
        "reaches_or_beats_original_rate",
    ]
    open(path, "w") do io
        println(io, join(header, ","))
        for (basis_key, rows) in sort(collect(_basis_groups(results)); by = first)
            for k in curve_k
                for (structure_name, starts_key, hit_key) in (
                    ("oracle", "oracle_starts", "oracle_structure_hit"),
                    ("reference", "reference_starts", "reference_structure_hit"),
                )
                    best = [_best_result(row[starts_key], k) for row in rows]
                    losses = [item === nothing ? nothing : item["loss"] for item in best]
                    r2_values = [item === nothing ? nothing : item["r2"] for item in best]
                    n_cells = length(rows)
                    r2_hits = count(_r2_hit, r2_values)
                    reaches = count(idx -> losses[idx] !== nothing && Float64(losses[idx]) <= Float64(rows[idx]["original_loss"]), eachindex(rows))
                    structure_hits = count(row -> row[hit_key] === true, rows)
                    fields = Dict{String, Any}(
                        "k" => k,
                        "basis" => basis_key,
                        "structure" => structure_name,
                        "n_cells" => n_cells,
                        "sentinel_loss_cells" => count(_is_sentinel, losses),
                        "structure_hit_cells" => structure_hits,
                        "structure_hit_rate" => _ratio(structure_hits, n_cells),
                        "r2_gt_0_9_cells" => r2_hits,
                        "r2_gt_0_9_rate" => _ratio(r2_hits, n_cells),
                        "reaches_or_beats_original_cells" => reaches,
                        "reaches_or_beats_original_rate" => _ratio(reaches, n_cells),
                    )
                    println(io, join((_csv_escape(get(fields, key, nothing)) for key in header), ","))
                end
            end
        end
    end
end

function _write_curve_loss_quantiles(path::AbstractString, results, curve_k)
    mkpath(dirname(path))
    probs = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    header = ["k", "basis", "structure", "n", "q05", "q10", "q25", "q50", "q75", "q90", "q95"]
    open(path, "w") do io
        println(io, join(header, ","))
        for (basis_key, rows) in sort(collect(_basis_groups(results)); by = first)
            for k in curve_k
                for (structure_name, starts_key) in (("oracle", "oracle_starts"), ("reference", "reference_starts"))
                    values = Float64[]
                    for row in rows
                        best = _best_result(row[starts_key], k)
                        best === nothing && continue
                        value = Float64(best["loss"])
                        isfinite(value) && push!(values, value)
                    end
                    fields = Any[k, basis_key, structure_name, length(values)]
                    append!(fields, [_quantile_value(values, p) for p in probs])
                    println(io, join(_csv_escape.(fields), ","))
                end
            end
        end
    end
end

function _write_nonadaptable_cells(path::AbstractString, results, max_k::Int)
    mkpath(dirname(path))
    header = [
        "structure", "cell_key", "condition", "basis_name", "system_id",
        "system_name", "initial_condition_set", "seed", "wp_n2_category",
        "best_loss", "best_start_index", "best_start_seed", "r2",
    ]
    open(path, "w") do io
        println(io, join(header, ","))
        for row in results
            row["error"] === nothing || continue
            for (structure_name, starts_key) in (("oracle", "oracle_starts"), ("reference", "reference_starts"))
                best = _best_result(row[starts_key], max_k)
                best !== nothing && _is_sentinel(best["loss"]) || continue
                fields = Dict{String, Any}(
                    "structure" => structure_name,
                    "cell_key" => row["cell_key"],
                    "condition" => row["condition"],
                    "basis_name" => row["basis_name"],
                    "system_id" => row["system_id"],
                    "system_name" => row["system_name"],
                    "initial_condition_set" => row["initial_condition_set"],
                    "seed" => row["seed"],
                    "wp_n2_category" => row["wp_n2_category"],
                    "best_loss" => best["loss"],
                    "best_start_index" => best["start_index"],
                    "best_start_seed" => best["start_seed"],
                    "r2" => best["r2"],
                )
                println(io, join((_csv_escape(get(fields, key, nothing)) for key in header), ","))
            end
        end
    end
end

function _write_manifest(path::AbstractString, input_path::AbstractString, output_dir::AbstractString, n_starts::Int, curve_k, fingerprint::AbstractString, run_count::Int)
    open(path, "w") do io
        JSON3.write(io, json_safe(Dict{String, Any}(
            "task" => "WP-N4",
            "input" => input_path,
            "output_dir" => output_dir,
            "n_starts" => n_starts,
            "curve_k" => curve_k,
            "config_fingerprint" => fingerprint,
            "run_count" => run_count,
            "seed_derivation" => Dict(
                "start_1" => "cell seed exactly; this preserves WP-N3 k=1 initialization",
                "starts_2_to_n" => "parse(Int, bytes2hex(sha256(codeunits(\"WP-N4:start:<cell_seed>:<start_index>\")))[1:15]; base=16)",
            ),
        )))
        write(io, '\n')
    end
end

function main(args = ARGS)
    input_path = _arg_value(args, "--input", WP_N4_DEFAULT_INPUT)
    output_dir = _arg_value(args, "--output-dir", WP_N4_DEFAULT_OUTPUT_DIR)
    limit_value = _arg_value(args, "--limit", nothing)
    n_starts = parse(Int, _arg_value(args, "--starts", "10"))
    n_starts >= 1 || error("--starts must be positive, got $(n_starts)")
    maximum(WP_N4_CURVE_K) <= n_starts ||
        error("--starts must be at least $(maximum(WP_N4_CURVE_K)) for the WP-N4 curve, got $(n_starts)")
    fresh = _arg_flag(args, "--fresh")

    result_path = joinpath(output_dir, "starts.jsonl")
    cells_by_k_path = joinpath(output_dir, "cells_by_k.csv")
    curve_summary_path = joinpath(output_dir, "curve_summary.csv")
    curve_loss_quantiles_path = joinpath(output_dir, "curve_loss_quantiles.csv")
    nonadaptable_path = joinpath(output_dir, "nonadaptable_cells_at_k10.csv")
    fingerprint_path = joinpath(output_dir, "fingerprint.txt")
    manifest_path = joinpath(output_dir, "manifest.json")

    fingerprint = _wp_n4_fingerprint(input_path, n_starts)
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

    println("WP-N4 fingerprint: $(fingerprint)")
    println("Input: $(input_path)")
    println("Output: $(output_dir)")
    println("Cells requested: $(run_count)")
    println("Starts per fitted structure: $(n_starts)")

    for (idx, record) in enumerate(Iterators.take(records, run_count))
        result = _run_record(record, systems_by_id, n_starts)
        result["config_fingerprint"] = fingerprint
        push!(results, result)
        _append_jsonl!(result_path, result)
        if result["error"] === nothing
            oracle_best = _best_result(result["oracle_starts"], n_starts)
            reference_best = _best_result(result["reference_starts"], n_starts)
            println(@sprintf(
                "[%d/%d] %s original=%.3e oracle_best=%.3e reference_best=%.3e",
                idx,
                run_count,
                result["cell_key"],
                result["original_loss"],
                oracle_best["loss"],
                reference_best["loss"],
            ))
        else
            println(@sprintf("[%d/%d] %s skipped error=%s", idx, run_count, result["cell_key"], result["error"]))
        end
    end

    _write_cells_by_k(cells_by_k_path, results, WP_N4_CURVE_K)
    _write_curve_summary(curve_summary_path, results, WP_N4_CURVE_K)
    _write_curve_loss_quantiles(curve_loss_quantiles_path, results, WP_N4_CURVE_K)
    _write_nonadaptable_cells(nonadaptable_path, results, min(n_starts, maximum(WP_N4_CURVE_K)))
    _write_manifest(manifest_path, input_path, output_dir, n_starts, WP_N4_CURVE_K, fingerprint, run_count)
    open(fingerprint_path, "w") do io
        println(io, fingerprint)
    end

    println("Starts JSONL: $(result_path)")
    println("Cells by k: $(cells_by_k_path)")
    println("Curve summary: $(curve_summary_path)")
    println("Curve loss quantiles: $(curve_loss_quantiles_path)")
    println("Nonadaptable cells at k=10: $(nonadaptable_path)")
    println("Manifest: $(manifest_path)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
