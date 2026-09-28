import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf
using Random
using SHA
using Statistics

include(joinpath(@__DIR__, "wp_t1d_neighbourhood_loss.jl"))

const WP_T1F_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "wp_t1f_warm_neighbourhood")
const WP_T1F_ANALYSIS_ROOT = joinpath(@__DIR__, "..", "..", "analysis", "data", "wp_t1d_neighbourhood")
const WP_T1F_TRUE_COEFFICIENTS_PATH = joinpath(@__DIR__, "wp_t1f_true_coefficients.json")
const WP_T1F_CONTROL_LOSS_ABORT = 1e-4
# Phase-C trajectories are generated in run_regression.jl / phase_c_config.jl with 1e-9 solver tolerances.
const WP_T1F_TRAJECTORY_DATA_TOLERANCE = 1e-9
const WP_T1F_TRUTH_COLD_STARTS = 10
const WP_T1F_TRUTH_COLD_SMOKE_STARTS = 2
const WP_T1F_SMOKE_NEIGHBOURS_PER_CLASS = 5
const WP_T1F_INDEX_LIST_ENV = "EVO_T1F_INDEX_LIST"
const WP_T1F_OUTPUT_DIR_ENV = "EVO_T1F_OUTPUT_DIR"
const WP_T1F_OPTIMIZER_VARIANT = "phase_c_reference_unclamped"

function plain_json(value)
    if value isa JSON3.Object
        return Dict(String(k) => plain_json(value[k]) for k in keys(value))
    elseif value isa JSON3.Array
        return [plain_json(item) for item in value]
    else
        return value
    end
end

function json_get(row, key::String, default = nothing)
    haskey(row, key) && return row[key]
    sym = Symbol(key)
    haskey(row, sym) && return row[sym]
    return default
end

function read_json_file(path::AbstractString)
    isfile(path) || error("Missing JSON file: $(path)")
    return plain_json(JSON3.read(read(path, String)))
end

function load_t1f_true_coefficients(path::AbstractString = WP_T1F_TRUE_COEFFICIENTS_PATH)
    data = read_json_file(path)
    String(data["basis_name"]) == "staged_polynomial_basis_with_constant" ||
        error("Unexpected coefficient basis: $(data["basis_name"])")
    return data["systems"]
end

function coefficients_for_system(coefficients, system_id::Int)
    key = string(system_id)
    haskey(coefficients, key) || error("Missing true coefficients for system $(system_id)")
    return coefficients[key]
end

function coefficient_lookup(system_coefficients)
    lookup = Dict{Tuple{Int, String}, Float64}()
    for equation in system_coefficients["equations"]
        eq_idx = Int(equation["equation_index"])
        for (term, coefficient) in equation["coefficients"]
            lookup[(eq_idx, String(term))] = Float64(coefficient)
        end
    end
    return lookup
end

function parameter_terms(structure_terms, basis)
    structure = StructureSpec([sort(unique(Int[x for x in eq])) for eq in structure_terms])
    _, n_params, _ = build_rhs(structure, basis)
    terms = Tuple{Int, Int, String}[]
    for (eq_idx, eq_terms) in enumerate(structure.active_idxs)
        for term_idx in eq_terms
            push!(terms, (eq_idx, Int(term_idx), basis_term_name(basis, Int(term_idx))))
        end
    end
    length(terms) == n_params || error("Parameter order length mismatch")
    return terms
end

function true_parameter_vector(structure_terms, basis, system_coefficients; default_new::Float64 = 0.0)
    lookup = coefficient_lookup(system_coefficients)
    params = Float64[]
    for (eq_idx, _, term_name) in parameter_terms(structure_terms, basis)
        push!(params, get(lookup, (eq_idx, term_name), default_new))
    end
    return params
end

function validate_true_coefficients_against_support(system, basis, system_coefficients)
    support_names = term_names(canonical_support_terms(system[:expected_support]), basis)
    for equation in system_coefficients["equations"]
        eq_idx = Int(equation["equation_index"])
        coeff_terms = sort(String.(collect(keys(equation["coefficients"]))))
        expected = sort(String.(support_names[eq_idx]))
        coeff_terms == expected ||
            error("True coefficient term mismatch for system $(Int(system[:system_id])) equation $(eq_idx): $(coeff_terms) vs $(expected)")
    end
    return true
end

function build_t1f_unclamped_optimizer(; max_fit_attempts::Int = PHASE_C_MAX_FIT_ATTEMPTS)
    reference = build_reference_optimizer(max_fit_attempts = max_fit_attempts)
    return BFGSOptimizer(
        maxiters = reference.maxiters,
        abstol = reference.abstol,
        reltol = reference.reltol,
        maxiters_solve = reference.maxiters_solve,
        clamp_val = Inf,
        max_loss_evals = reference.max_loss_evals,
        time_limit_s = reference.time_limit_s,
        reject_nonfinite = reference.reject_nonfinite,
        divergence_limit = reference.divergence_limit,
        max_fit_attempts = reference.max_fit_attempts,
    )
end

function serialise_clamp_val(value::Float64)
    return isinf(value) ? "Inf" : value
end

function wp_t1f_config_fingerprint(phase_c_config_fingerprint::AbstractString, optimizer)
    payload = JSON3.write((
        phase_c_config_fingerprint = String(phase_c_config_fingerprint),
        optimizer_variant = WP_T1F_OPTIMIZER_VARIANT,
        clamp_val = serialise_clamp_val(Float64(optimizer.clamp_val)),
        truth_cold_starts = WP_T1F_TRUTH_COLD_STARTS,
        margin_factors = WP_T1D_MARGIN_FACTORS,
        margin_quantiles = WP_T1D_QUANTILES,
        control_loss_abort = WP_T1F_CONTROL_LOSS_ABORT,
        sentinel_loss = WP_T1D_SENTINEL_LOSS,
    ))
    return bytes2hex(sha256(codeunits(payload)))[1:16]
end

function t1f_optimizer_identity_fields(optimizer, phase_c_config_fingerprint::AbstractString)
    return Dict{String, Any}(
        "phase_c_config_fingerprint" => String(phase_c_config_fingerprint),
        "wp_t1f_config_fingerprint" => wp_t1f_config_fingerprint(phase_c_config_fingerprint, optimizer),
        "optimizer_variant" => WP_T1F_OPTIMIZER_VARIANT,
        "clamp_val" => serialise_clamp_val(Float64(optimizer.clamp_val)),
    )
end

function add_t1f_optimizer_identity!(row, optimizer, phase_c_config_fingerprint::AbstractString)
    for (key, value) in t1f_optimizer_identity_fields(optimizer, phase_c_config_fingerprint)
        row[key] = value
    end
    return row
end

function optimizer_value_for_csv(value)
    if value isa AbstractFloat && isinf(value)
        return "Inf"
    end
    return string(value)
end

function t1f_optimizer_comparison_rows(; max_fit_attempts::Int = PHASE_C_MAX_FIT_ATTEMPTS)
    reference = build_reference_optimizer(max_fit_attempts = max_fit_attempts)
    unclamped = build_t1f_unclamped_optimizer(max_fit_attempts = max_fit_attempts)
    rows = Dict{String, Any}[]
    for field in fieldnames(BFGSOptimizer)
        ref_value = getfield(reference, field)
        got_value = getfield(unclamped, field)
        push!(rows, Dict{String, Any}(
            "field" => String(field),
            "reference_value" => optimizer_value_for_csv(ref_value),
            "wp_t1f_value" => optimizer_value_for_csv(got_value),
            "matches_reference" => field == :clamp_val ? false : got_value == ref_value,
        ))
    end
    return rows
end

function assert_t1f_optimizer_matches_reference_except_clamp(; max_fit_attempts::Int = PHASE_C_MAX_FIT_ATTEMPTS)
    reference = build_reference_optimizer(max_fit_attempts = max_fit_attempts)
    unclamped = build_t1f_unclamped_optimizer(max_fit_attempts = max_fit_attempts)
    unclamped.clamp_val == Inf || error("WP-T1f optimizer clamp_val is $(unclamped.clamp_val), expected Inf")
    for field in fieldnames(BFGSOptimizer)
        field == :clamp_val && continue
        getfield(unclamped, field) == getfield(reference, field) ||
            error("WP-T1f optimizer field $(field) differs from Phase-C reference")
    end
    return true
end

function evaluate_structure_loss(
    structure_terms,
    basis,
    traj,
    params::Vector{Float64};
    seed::Int = WP_T1D_SEED,
    optimizer = build_reference_optimizer(max_fit_attempts = 1),
    abstol::Union{Nothing, Float64} = nothing,
    reltol::Union{Nothing, Float64} = nothing,
)
    structure = StructureSpec([sort(unique(Int[x for x in eq])) for eq in structure_terms])
    f!, n_params, _ = build_rhs(structure, basis)
    length(params) == n_params ||
        error("Parameter vector length $(length(params)) does not match structure parameter count $(n_params)")
    options = build_options(seed)
    yhat = simulate(
        f!,
        params,
        traj;
        abstol = abstol === nothing ? optimizer.abstol : abstol,
        reltol = reltol === nothing ? optimizer.reltol : reltol,
        maxiters = optimizer.maxiters_solve,
        clamp_val = optimizer.clamp_val,
        reject_nonfinite = optimizer.reject_nonfinite,
        divergence_limit = optimizer.divergence_limit,
        options = options,
    )
    return evaluate_loss(MSELoss(), yhat, traj.x)
end

function fit_winning_attempt(fit_result)
    meta = fit_result["fit_meta"]
    meta === nothing && return 1
    haskey(meta, :accepted_attempt) && return Int(meta.accepted_attempt)
    haskey(meta, :fit_attempts) && return Int(meta.fit_attempts)
    return 1
end

function fit_loss_evals(fit_result)
    meta = fit_result["fit_meta"]
    meta === nothing && return 0
    haskey(meta, :loss_evals) && return Int(meta.loss_evals)
    return 0
end

function fit_attempt_count(fit_result)
    meta = fit_result["fit_meta"]
    meta === nothing && return 1
    haskey(meta, :fit_attempts) && return Int(meta.fit_attempts)
    return 1
end

function assert_t1f_control_loss_ok(control_loss_data_tolerance, system_id::Int, ic_set::Int; control_loss_optimizer_tolerance = nothing)
    Float64(control_loss_data_tolerance) <= WP_T1F_CONTROL_LOSS_ABORT ||
        error(
            "Control loss at data tolerance $(control_loss_data_tolerance) exceeds " *
            "$(WP_T1F_CONTROL_LOSS_ABORT) for system $(system_id) IC $(ic_set)",
        )
    return true
end

function t1f_floor_to_control_optimizer_ratio(floor_loss, control_loss_optimizer_tolerance)
    floor_loss === nothing && return nothing
    control_loss_optimizer_tolerance === nothing && return nothing
    control = Float64(control_loss_optimizer_tolerance)
    (!isfinite(control) || control <= 0.0) && return nothing
    return Float64(floor_loss) / control
end

function t1f_comparison_budget_stratum(neighbor_budget_exhausted::Bool, floor_budget_exhausted::Bool)
    if neighbor_budget_exhausted && floor_budget_exhausted
        return "both_exhausted"
    elseif neighbor_budget_exhausted
        return "neighbour_exhausted"
    elseif floor_budget_exhausted
        return "floor_exhausted"
    end
    return "neither_exhausted"
end

function t1f_loss_comparison(neighbor_loss, floor_loss; neighbor_budget_exhausted::Bool = false, floor_budget_exhausted::Bool = false)
    stratum = t1f_comparison_budget_stratum(neighbor_budget_exhausted, floor_budget_exhausted)
    out = Dict{String, Any}(
        "log10_loss_ratio" => nothing,
        "beats_floor" => false,
        "comparison_budget_stratum" => stratum,
    )
    (is_sentinel_loss(neighbor_loss) || is_sentinel_loss(floor_loss)) && return out
    floor_value = Float64(floor_loss)
    neighbor_value = Float64(neighbor_loss)
    (!isfinite(neighbor_value) || !isfinite(floor_value)) && return out
    floor_value <= 0.0 && return out
    out["log10_loss_ratio"] = neighbor_value <= 0.0 ? -Inf : log10(neighbor_value / floor_value)
    out["beats_floor"] = neighbor_value < floor_value
    return out
end

function add_t1f_loss_comparison!(row, neighbor_loss, floor_loss; neighbor_budget_exhausted::Bool = false, floor_budget_exhausted::Bool = false)
    comparison = t1f_loss_comparison(
        neighbor_loss,
        floor_loss;
        neighbor_budget_exhausted = neighbor_budget_exhausted,
        floor_budget_exhausted = floor_budget_exhausted,
    )
    for (key, value) in comparison
        row[key] = value
    end
    return row
end

function base_raw_row(system, ic_set::Int, trajectory_sha, trajectory_source, git, phase_c_fingerprint_value, optimizer)
    row = Dict{String, Any}(
        "git_hash" => git.git_hash,
        "system_id" => Int(system[:system_id]),
        "dimension" => Int(system[:dim]),
        "initial_condition_set" => ic_set,
        "trajectory_sha256" => trajectory_sha,
        "trajectory_source" => trajectory_source,
        "bfgs_max_loss_evals" => BFGS_MAX_LOSS_EVALS,
        "elapsed_s_non_evidence" => nothing,
    )
    return add_t1f_optimizer_identity!(row, optimizer, phase_c_fingerprint_value)
end

function add_fit_fields!(row, fit_result)
    row["loss"] = fit_result["loss"]
    row["budget_exhausted"] = fit_budget_exhausted(fit_result)
    row["sentinel_loss"] = is_sentinel_loss(fit_result["loss"])
    row["winning_attempt"] = fit_winning_attempt(fit_result)
    row["total_parameter_fits"] = fit_attempt_count(fit_result)
    row["loss_evaluations"] = fit_loss_evals(fit_result)
    row["fitted_coefficients"] = JSON3.write(fit_result["coefficients"])
    return row
end

function cold_truth_seed(system, ic_set::Int, start_index::Int)
    payload = "wp-t1f:$(Int(system[:system_id])):$(ic_set):$(start_index)"
    digest = sha256(codeunits(payload))
    value = 0
    for idx in 1:4
        value = (value << 8) + Int(digest[idx])
    end
    return value
end

function smoke_limited_neighbours(neighbours)
    by_class = Dict("add_one" => 0, "remove_one" => 0, "swap_one" => 0)
    out = Dict{String, Any}[]
    for neighbour in neighbours
        klass = String(neighbour["neighbor_class"])
        by_class[klass] < WP_T1F_SMOKE_NEIGHBOURS_PER_CLASS || continue
        by_class[klass] += 1
        push!(out, neighbour)
    end
    return out
end

function run_t1f_cell(
    system,
    ic_set::Int,
    export_dir::AbstractString,
    raw_jsonl_path::AbstractString,
    true_coefficients;
    smoke::Bool = false,
)
    system_id = Int(system[:system_id])
    dim = Int(system[:dim])
    basis = phase_c_basis(dim)
    true_terms = canonical_support_terms(system[:expected_support])
    assert_neighbourhood_counts(true_terms, basis)
    system_coefficients = coefficients_for_system(true_coefficients, system_id)
    validate_true_coefficients_against_support(system, basis, system_coefficients)
    truth_p0 = true_parameter_vector(true_terms, basis, system_coefficients)
    traj, trajectory_sha, trajectory_source = trajectory_for_cell(export_dir, system, ic_set)
    git = git_provenance()
    fingerprint = phase_c_fingerprint()
    reference_optimizer = build_t1f_unclamped_optimizer(max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS)
    control_optimizer = build_t1f_unclamped_optimizer(max_fit_attempts = 1)
    truth_cold_optimizer = build_t1f_unclamped_optimizer(max_fit_attempts = 1)

    rows = Dict{String, Any}[]
    control_start = time()
    control_loss_data_tolerance = evaluate_structure_loss(
        true_terms,
        basis,
        traj,
        truth_p0;
        optimizer = control_optimizer,
        abstol = WP_T1F_TRAJECTORY_DATA_TOLERANCE,
        reltol = WP_T1F_TRAJECTORY_DATA_TOLERANCE,
    )
    control_loss_optimizer_tolerance = evaluate_structure_loss(true_terms, basis, traj, truth_p0; optimizer = control_optimizer)
    control_row = base_raw_row(system, ic_set, trajectory_sha, trajectory_source, git, fingerprint, control_optimizer)
    control_row["fit_role"] = "control"
    control_row["loss"] = control_loss_data_tolerance
    control_row["control_loss_data_tolerance"] = control_loss_data_tolerance
    control_row["control_loss_optimizer_tolerance"] = control_loss_optimizer_tolerance
    control_row["budget_exhausted"] = false
    control_row["sentinel_loss"] = is_sentinel_loss(control_loss_data_tolerance)
    control_row["winning_attempt"] = 0
    control_row["total_parameter_fits"] = 0
    control_row["loss_evaluations"] = 2
    control_row["fitted_coefficients"] = JSON3.write(active_model_terms(StructureSpec(true_terms), basis, truth_p0))
    control_row["elapsed_s_non_evidence"] = time() - control_start
    push!(rows, control_row)
    append_jsonl!(raw_jsonl_path, control_row)
    assert_t1f_control_loss_ok(
        control_loss_data_tolerance,
        system_id,
        ic_set;
        control_loss_optimizer_tolerance = control_loss_optimizer_tolerance,
    )

    floor_start = time()
    floor_result = fit_fixed_structure_phase_c(
        true_terms,
        system,
        basis,
        traj,
        WP_T1D_SEED;
        p0 = truth_p0,
        max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
        optimizer = reference_optimizer,
    )
    floor_row = base_raw_row(system, ic_set, trajectory_sha, trajectory_source, git, fingerprint, reference_optimizer)
    floor_row["fit_role"] = "floor"
    floor_row["control_loss_data_tolerance"] = control_loss_data_tolerance
    floor_row["control_loss_optimizer_tolerance"] = control_loss_optimizer_tolerance
    add_fit_fields!(floor_row, floor_result)
    floor_row["elapsed_s_non_evidence"] = time() - floor_start
    push!(rows, floor_row)
    append_jsonl!(raw_jsonl_path, floor_row)
    floor_loss = floor_result["loss"]
    floor_budget_exhausted = fit_budget_exhausted(floor_result)

    neighbours = neighbourhood(true_terms, basis)
    smoke && (neighbours = smoke_limited_neighbours(neighbours))
    for (idx, neighbour) in enumerate(neighbours)
        neighbour_terms = neighbour["neighbor_terms"]
        p0 = true_parameter_vector(neighbour_terms, basis, system_coefficients; default_new = 0.0)
        fit_start = time()
        fit_result = fit_fixed_structure_phase_c(
            neighbour_terms,
            system,
            basis,
            traj,
            WP_T1D_SEED;
            p0 = p0,
            max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS,
            optimizer = reference_optimizer,
        )
        row = base_raw_row(system, ic_set, trajectory_sha, trajectory_source, git, fingerprint, reference_optimizer)
        row["fit_role"] = "neighbour_warm"
        row["neighbor_index"] = idx
        row["neighbor_class"] = String(neighbour["neighbor_class"])
        row["equation_idx"] = Int(neighbour["equation_idx"])
        row["neighbor_terms"] = JSON3.write(term_names(neighbour_terms, basis))
        row["true_terms"] = JSON3.write(term_names(true_terms, basis))
        row["added_term"] = neighbour["added_term"] === nothing ? nothing : basis_term_name(basis, Int(neighbour["added_term"]))
        row["removed_term"] = neighbour["removed_term"] === nothing ? nothing : basis_term_name(basis, Int(neighbour["removed_term"]))
        row["control_loss_data_tolerance"] = control_loss_data_tolerance
        row["control_loss_optimizer_tolerance"] = control_loss_optimizer_tolerance
        row["floor_loss"] = floor_loss
        add_fit_fields!(row, fit_result)
        row["floor_budget_exhausted"] = floor_budget_exhausted
        add_t1f_loss_comparison!(
            row,
            row["loss"],
            floor_loss;
            neighbor_budget_exhausted = Bool(row["budget_exhausted"]),
            floor_budget_exhausted = floor_budget_exhausted,
        )
        row["warm_start_from_attempt_1"] = Int(row["winning_attempt"]) == 1
        row["elapsed_s_non_evidence"] = time() - fit_start
        push!(rows, row)
        append_jsonl!(raw_jsonl_path, row)
    end

    n_cold = smoke ? WP_T1F_TRUTH_COLD_SMOKE_STARTS : WP_T1F_TRUTH_COLD_STARTS
    for start_index in 1:n_cold
        seed = cold_truth_seed(system, ic_set, start_index)
        fit_start = time()
        fit_result = fit_fixed_structure_phase_c(
            true_terms,
            system,
            basis,
            traj,
            seed;
            p0 = nothing,
            max_fit_attempts = 1,
            optimizer = truth_cold_optimizer,
        )
        row = base_raw_row(system, ic_set, trajectory_sha, trajectory_source, git, fingerprint, truth_cold_optimizer)
        row["fit_role"] = "truth_cold"
        row["truth_cold_start_index"] = start_index
        row["truth_cold_seed"] = seed
        row["control_loss_data_tolerance"] = control_loss_data_tolerance
        row["control_loss_optimizer_tolerance"] = control_loss_optimizer_tolerance
        row["floor_loss"] = floor_loss
        add_fit_fields!(row, fit_result)
        row["elapsed_s_non_evidence"] = time() - fit_start
        push!(rows, row)
        append_jsonl!(raw_jsonl_path, row)
    end
    return rows
end

function t1f_fit_count_for_cell(system; smoke::Bool = false)
    basis = phase_c_basis(Int(system[:dim]))
    true_terms = canonical_support_terms(system[:expected_support])
    neighbours = neighbourhood(true_terms, basis)
    smoke && (neighbours = smoke_limited_neighbours(neighbours))
    cold_starts = smoke ? WP_T1F_TRUTH_COLD_SMOKE_STARTS : WP_T1F_TRUTH_COLD_STARTS
    return 1 + length(neighbours) + cold_starts
end

function write_t1f_projection(output_dir::AbstractString, cells; measured_elapsed_s = nothing, measured_loss_evals = nothing, smoke::Bool = false)
    rows = Dict{String, Any}[]
    total_fits = 0
    for (system, ic_set) in cells
        fits = t1f_fit_count_for_cell(system; smoke = smoke)
        total_fits += fits
        push!(rows, Dict{String, Any}(
            "system_id" => Int(system[:system_id]),
            "dimension" => Int(system[:dim]),
            "initial_condition_set" => Int(ic_set),
            "planned_parameter_fits" => fits,
        ))
    end
    seconds = measured_elapsed_s
    seconds_per_eval = measured_loss_evals === nothing || measured_loss_evals <= 0 || seconds === nothing ? nothing : Float64(seconds) / Float64(measured_loss_evals)
    projection = Dict{String, Any}(
        "projection_basis" => seconds_per_eval === nothing ? "fit_count_only" : "smoke_elapsed_seconds_per_loss_eval",
        "elapsed_s_non_evidence" => measured_elapsed_s,
        "measured_loss_evaluations" => measured_loss_evals,
        "measured_seconds_per_loss_eval_non_evidence" => seconds_per_eval,
        "planned_parameter_fits" => total_fits,
        "planned_loss_eval_budget" => total_fits * BFGS_MAX_LOSS_EVALS,
        "projected_runtime_s_non_evidence" => seconds_per_eval === nothing ? nothing : seconds_per_eval * total_fits * BFGS_MAX_LOSS_EVALS,
        "rows" => rows,
    )
    open(joinpath(output_dir, "projection.json"), "w") do io
        JSON3.write(io, json_safe(projection))
        write(io, '\n')
    end
    write_csv(joinpath(output_dir, "projection_cells.csv"), ["system_id", "dimension", "initial_condition_set", "planned_parameter_fits"], rows)
    return projection
end

function read_jsonl_rows(path::AbstractString)
    rows = Dict{String, Any}[]
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            push!(rows, plain_json(JSON3.read(line)))
        end
    end
    return rows
end

function collect_jsonl_rows(input_dir::AbstractString)
    paths = String[]
    for (root, _, files) in walkdir(input_dir)
        for file in files
            endswith(file, ".jsonl") || continue
            push!(paths, joinpath(root, file))
        end
    end
    sort!(paths)
    rows = Dict{String, Any}[]
    for path in paths
        append!(rows, read_jsonl_rows(path))
    end
    return rows
end

function finite_margin(row)
    comparison = t1f_loss_comparison(
        json_get(row, "loss", nothing),
        json_get(row, "floor_loss", nothing);
        neighbor_budget_exhausted = Bool(json_get(row, "budget_exhausted", false)),
        floor_budget_exhausted = Bool(json_get(row, "floor_budget_exhausted", json_get(row, "budget_exhausted_true", false))),
    )
    row["comparison_budget_stratum"] = comparison["comparison_budget_stratum"]
    row["log10_loss_ratio"] = comparison["log10_loss_ratio"]
    row["beats_floor"] = comparison["beats_floor"]
    value = comparison["log10_loss_ratio"]
    value === nothing && return nothing
    margin = Float64(value)
    isfinite(margin) || return nothing
    return margin
end

function normalised_neighbour_rows(raw_rows)
    rows = Dict{String, Any}[]
    for row in raw_rows
        role = String(json_get(row, "fit_role", ""))
        if role == "neighbour_warm"
            push!(rows, row)
        elseif haskey(row, "loss_true") && haskey(row, "loss_neighbor")
            out = copy(row)
            out["fit_role"] = "neighbour_warm"
            out["variant"] = "cold_reference"
            out["loss"] = row["loss_neighbor"]
            out["floor_loss"] = row["loss_true"]
            out["budget_exhausted"] = json_get(row, "budget_exhausted_neighbor", false)
            out["floor_budget_exhausted"] = json_get(row, "budget_exhausted_true", false)
            out["warm_start_from_attempt_1"] = false
            out["phase_c_config_fingerprint"] = json_get(row, "phase_c_config_fingerprint", json_get(row, "config_fingerprint", nothing))
            push!(rows, out)
        end
    end
    for row in rows
        if !haskey(row, "variant")
            row["variant"] = "warm_reference"
        end
        if !haskey(row, "phase_c_config_fingerprint")
            row["phase_c_config_fingerprint"] = json_get(row, "config_fingerprint", nothing)
        end
    end
    return rows
end

function aggregate_t1f_rows(raw_rows)
    neighbours = normalised_neighbour_rows(raw_rows)
    by_key = Dict{Tuple{String, Int, String}, Vector{Dict{String, Any}}}()
    for row in neighbours
        key = (String(row["variant"]), Int(row["dimension"]), String(row["neighbor_class"]))
        get!(by_key, key, Dict{String, Any}[])
        push!(by_key[key], row)
    end

    summary = Dict{String, Any}[]
    thresholds = Dict{String, Any}[]
    quantiles = Dict{String, Any}[]
    retry = Dict{String, Any}[]
    budget_strata = Dict{String, Any}[]
    for (key, rows) in sort(collect(by_key); by = x -> x[1])
        variant, dim, klass = key
        margins_by_scope = Dict("all_comparable" => Float64[], "neither_exhausted" => Float64[])
        beats_by_scope = Dict("all_comparable" => 0, "neither_exhausted" => 0)
        stratum_counts = Dict(
            "neither_exhausted" => 0,
            "neighbour_exhausted" => 0,
            "floor_exhausted" => 0,
            "both_exhausted" => 0,
        )
        for row in rows
            margin = finite_margin(row)
            stratum = String(row["comparison_budget_stratum"])
            haskey(stratum_counts, stratum) || (stratum_counts[stratum] = 0)
            stratum_counts[stratum] += 1
            margin === nothing && continue
            push!(margins_by_scope["all_comparable"], margin)
            margin < 0.0 && (beats_by_scope["all_comparable"] += 1)
            if stratum == "neither_exhausted"
                push!(margins_by_scope["neither_exhausted"], margin)
                margin < 0.0 && (beats_by_scope["neither_exhausted"] += 1)
            end
        end
        for scope in ("all_comparable", "neither_exhausted")
            margins = margins_by_scope[scope]
            beats = beats_by_scope[scope]
            push!(summary, Dict{String, Any}(
                "variant" => variant,
                "dimension" => dim,
                "neighbor_class" => klass,
                "comparison_scope" => scope,
                "n_neighbor_rows" => length(rows),
                "n_valid_margins" => length(margins),
                "n_neighbors_below_floor" => beats,
                "share_neighbors_below_floor" => isempty(margins) ? nothing : beats / length(margins),
            ))
            for factor in WP_T1D_MARGIN_FACTORS
                threshold = -log10(factor)
                n_better = count(value -> value < threshold, margins)
                push!(thresholds, Dict{String, Any}(
                    "variant" => variant,
                    "dimension" => dim,
                    "neighbor_class" => klass,
                    "comparison_scope" => scope,
                    "margin_factor" => factor,
                    "log10_threshold" => threshold,
                    "n_neighbors_better_by_factor" => n_better,
                    "share_neighbors_better_by_factor" => isempty(margins) ? nothing : n_better / length(margins),
                    "n_margins" => length(margins),
                ))
            end
            for q in WP_T1D_QUANTILES
                push!(quantiles, Dict{String, Any}(
                    "variant" => variant,
                    "dimension" => dim,
                    "neighbor_class" => klass,
                    "comparison_scope" => scope,
                    "quantile" => q,
                    "log10_loss_ratio" => quantile_or_nothing(margins, q),
                    "n_margins" => length(margins),
                ))
            end
        end
        for stratum in ("neither_exhausted", "neighbour_exhausted", "floor_exhausted", "both_exhausted")
            push!(budget_strata, Dict{String, Any}(
                "variant" => variant,
                "dimension" => dim,
                "neighbor_class" => klass,
                "comparison_budget_stratum" => stratum,
                "n_rows" => get(stratum_counts, stratum, 0),
            ))
        end
        retry_rows = [row for row in rows if String(row["variant"]) == "warm_reference"]
        non_warm = count(row -> json_get(row, "warm_start_from_attempt_1", false) !== true, retry_rows)
        push!(retry, Dict{String, Any}(
            "variant" => variant,
            "dimension" => dim,
            "neighbor_class" => klass,
            "n_warm_neighbour_rows" => length(retry_rows),
            "n_not_from_warm_attempt" => non_warm,
            "share_not_from_warm_attempt" => isempty(retry_rows) ? nothing : non_warm / length(retry_rows),
        ))
    end

    cell_loss_by_key = Dict{Tuple{Int, Int, Int}, Dict{String, Any}}()
    for row in raw_rows
        role = String(json_get(row, "fit_role", ""))
        role in ("control", "floor") || continue
        key = (Int(row["dimension"]), Int(row["system_id"]), Int(row["initial_condition_set"]))
        out = get!(cell_loss_by_key, key) do
            Dict{String, Any}(
                "system_id" => row["system_id"],
                "dimension" => row["dimension"],
                "initial_condition_set" => row["initial_condition_set"],
                "control_loss_data_tolerance" => nothing,
                "control_loss_optimizer_tolerance" => nothing,
                "floor_loss" => nothing,
                "floor_to_control_optimizer_tolerance_ratio" => nothing,
            )
        end
        data_loss = json_get(row, "control_loss_data_tolerance", json_get(row, "control_loss", role == "control" ? row["loss"] : nothing))
        optimizer_loss = json_get(row, "control_loss_optimizer_tolerance", json_get(row, "control_loss", role == "control" ? row["loss"] : nothing))
        data_loss !== nothing && (out["control_loss_data_tolerance"] = data_loss)
        optimizer_loss !== nothing && (out["control_loss_optimizer_tolerance"] = optimizer_loss)
        if role == "floor"
            out["floor_loss"] = row["loss"]
        end
    end
    cell_losses = Dict{String, Any}[]
    for (_, row) in sort(collect(cell_loss_by_key); by = x -> x[1])
        row["floor_to_control_optimizer_tolerance_ratio"] = t1f_floor_to_control_optimizer_ratio(
            row["floor_loss"],
            row["control_loss_optimizer_tolerance"],
        )
        push!(cell_losses, row)
    end

    cold_rows = [row for row in raw_rows if String(json_get(row, "fit_role", "")) == "truth_cold"]
    by_cell = Dict{Tuple{Int, Int, Int}, Vector{Dict{String, Any}}}()
    for row in cold_rows
        key = (Int(row["dimension"]), Int(row["system_id"]), Int(row["initial_condition_set"]))
        get!(by_cell, key, Dict{String, Any}[])
        push!(by_cell[key], row)
    end
    cold_summary = Dict{String, Any}[]
    for (key, rows) in sort(collect(by_cell); by = x -> x[1])
        dim, system_id, ic_set = key
        push!(cold_summary, Dict{String, Any}(
            "dimension" => dim,
            "system_id" => system_id,
            "initial_condition_set" => ic_set,
            "n_starts" => length(rows),
            "n_loss_lt_1e_8" => count(row -> Float64(row["loss"]) < 1e-8, rows),
            "n_loss_1e_8_to_1e_3" => count(row -> 1e-8 <= Float64(row["loss"]) < 1e-3, rows),
            "n_loss_ge_1e_3" => count(row -> Float64(row["loss"]) >= 1e-3, rows),
            "n_sentinel" => count(row -> json_get(row, "sentinel_loss", false) === true, rows),
        ))
    end
    by_dim = Dict{Int, Vector{Dict{String, Any}}}()
    for row in cold_rows
        get!(by_dim, Int(row["dimension"]), Dict{String, Any}[])
        push!(by_dim[Int(row["dimension"])], row)
    end
    cold_rates = Dict{String, Any}[]
    for (dim, rows) in sort(collect(by_dim); by = x -> x[1])
        hits = count(row -> Float64(row["loss"]) < 1e-8, rows)
        push!(cold_rates, Dict{String, Any}(
            "dimension" => dim,
            "n_starts" => length(rows),
            "n_loss_lt_1e_8" => hits,
            "single_start_hit_rate" => isempty(rows) ? nothing : hits / length(rows),
        ))
    end
    return summary, thresholds, quantiles, cell_losses, cold_summary, cold_rates, retry, budget_strata
end

function write_t1f_aggregates(raw_rows, analysis_dir::AbstractString)
    mkpath(analysis_dir)
    summary, thresholds, quantiles, cell_losses, cold_summary, cold_rates, retry, budget_strata = aggregate_t1f_rows(raw_rows)
    write_csv(joinpath(analysis_dir, "neighbour_summary_by_dimension_class.csv"), ["variant", "dimension", "neighbor_class", "comparison_scope", "n_neighbor_rows", "n_valid_margins", "n_neighbors_below_floor", "share_neighbors_below_floor"], summary)
    write_csv(joinpath(analysis_dir, "margin_threshold_grid_by_dimension_class.csv"), ["variant", "dimension", "neighbor_class", "comparison_scope", "margin_factor", "log10_threshold", "n_neighbors_better_by_factor", "share_neighbors_better_by_factor", "n_margins"], thresholds)
    write_csv(joinpath(analysis_dir, "margin_quantiles_by_dimension_class.csv"), ["variant", "dimension", "neighbor_class", "comparison_scope", "quantile", "log10_loss_ratio", "n_margins"], quantiles)
    write_csv(joinpath(analysis_dir, "comparison_budget_strata_by_dimension_class.csv"), ["variant", "dimension", "neighbor_class", "comparison_budget_stratum", "n_rows"], budget_strata)
    write_csv(
        joinpath(analysis_dir, "control_and_floor_loss_by_cell.csv"),
        [
            "system_id", "dimension", "initial_condition_set",
            "control_loss_data_tolerance", "control_loss_optimizer_tolerance",
            "floor_loss", "floor_to_control_optimizer_tolerance_ratio",
        ],
        cell_losses,
    )
    write_csv(joinpath(analysis_dir, "truth_cold_by_cell.csv"), ["dimension", "system_id", "initial_condition_set", "n_starts", "n_loss_lt_1e_8", "n_loss_1e_8_to_1e_3", "n_loss_ge_1e_3", "n_sentinel"], cold_summary)
    write_csv(joinpath(analysis_dir, "truth_cold_hit_rate_by_dimension.csv"), ["dimension", "n_starts", "n_loss_lt_1e_8", "single_start_hit_rate"], cold_rates)
    write_csv(joinpath(analysis_dir, "warm_retry_share_by_dimension_class.csv"), ["variant", "dimension", "neighbor_class", "n_warm_neighbour_rows", "n_not_from_warm_attempt", "share_not_from_warm_attempt"], retry)
    return nothing
end

function t1f_raw_output_columns()
    return [
        "git_hash", "phase_c_config_fingerprint", "wp_t1f_config_fingerprint",
        "optimizer_variant", "clamp_val", "system_id", "dimension", "initial_condition_set",
        "trajectory_sha256", "trajectory_source", "fit_role", "neighbor_index",
        "neighbor_class", "equation_idx", "neighbor_terms", "true_terms", "added_term",
        "removed_term", "truth_cold_start_index", "truth_cold_seed", "loss",
        "control_loss_data_tolerance", "control_loss_optimizer_tolerance",
        "floor_loss", "log10_loss_ratio", "beats_floor",
        "budget_exhausted", "floor_budget_exhausted", "sentinel_loss",
        "comparison_budget_stratum", "warm_start_from_attempt_1",
        "winning_attempt", "total_parameter_fits", "loss_evaluations",
        "bfgs_max_loss_evals", "fitted_coefficients", "elapsed_s_non_evidence",
    ]
end

function run_t1f_control_only(output_dir::AbstractString, export_dir::AbstractString, true_coefficients)
    rows = Dict{String, Any}[]
    failures = String[]
    for (idx, (system, ic_set)) in enumerate(selected_cells())
        system_id = Int(system[:system_id])
        dim = Int(system[:dim])
        @printf("[%d/36] control system_id=%d dim=%d ic=%d\n", idx, system_id, dim, Int(ic_set))
        basis = phase_c_basis(dim)
        true_terms = canonical_support_terms(system[:expected_support])
        system_coefficients = coefficients_for_system(true_coefficients, system_id)
        validate_true_coefficients_against_support(system, basis, system_coefficients)
        truth_p0 = true_parameter_vector(true_terms, basis, system_coefficients)
        traj, _, _ = trajectory_for_cell(export_dir, system, Int(ic_set))
        optimizer = build_t1f_unclamped_optimizer(max_fit_attempts = 1)
        control_loss_data_tolerance = evaluate_structure_loss(
            true_terms,
            basis,
            traj,
            truth_p0;
            optimizer = optimizer,
            abstol = WP_T1F_TRAJECTORY_DATA_TOLERANCE,
            reltol = WP_T1F_TRAJECTORY_DATA_TOLERANCE,
        )
        control_loss_optimizer_tolerance = evaluate_structure_loss(true_terms, basis, traj, truth_p0; optimizer = optimizer)
        push!(rows, Dict{String, Any}(
            "system_id" => system_id,
            "initial_condition_set" => Int(ic_set),
            "dimension" => dim,
            "control_loss_data_tolerance" => control_loss_data_tolerance,
            "control_loss_optimizer_tolerance" => control_loss_optimizer_tolerance,
        ))
        if Float64(control_loss_data_tolerance) > WP_T1F_CONTROL_LOSS_ABORT
            push!(
                failures,
                "system_id=$(system_id) ic=$(Int(ic_set)) dimension=$(dim) " *
                "control_loss_data_tolerance=$(control_loss_data_tolerance) " *
                "control_loss_optimizer_tolerance=$(control_loss_optimizer_tolerance)",
            )
        end
    end
    write_csv(
        joinpath(output_dir, "control_only.csv"),
        ["system_id", "initial_condition_set", "dimension", "control_loss_data_tolerance", "control_loss_optimizer_tolerance"],
        rows,
    )
    if !isempty(failures)
        println("Control losses above $(WP_T1F_CONTROL_LOSS_ABORT):")
        for failure in failures
            println(failure)
        end
        error("Control-only check found $(length(failures)) cells above threshold")
    end
    println("Control-only rows: $(length(rows)); all data-tolerance control losses <= $(WP_T1F_CONTROL_LOSS_ABORT)")
    return rows
end

function run_t1f_self_test(output_dir::AbstractString, true_coefficients)
    rows = run_self_test()
    assert_t1f_optimizer_matches_reference_except_clamp()
    for system in phase_c_exact_dim23_systems()
        basis = phase_c_basis(Int(system[:dim]))
        system_coefficients = coefficients_for_system(true_coefficients, Int(system[:system_id]))
        validate_true_coefficients_against_support(system, basis, system_coefficients)
        true_terms = canonical_support_terms(system[:expected_support])
        true_parameter_vector(true_terms, basis, system_coefficients)
    end
    system = first(phase_c_exact_dim23_systems())
    basis = phase_c_basis(Int(system[:dim]))
    system_coefficients = coefficients_for_system(true_coefficients, Int(system[:system_id]))
    true_terms = canonical_support_terms(system[:expected_support])
    neighbours = neighbourhood(true_terms, basis)
    checks = Dict{String, Any}[]
    for klass in ("add_one", "remove_one", "swap_one")
        neighbour = first(row for row in neighbours if String(row["neighbor_class"]) == klass)
        params = true_parameter_vector(neighbour["neighbor_terms"], basis, system_coefficients; default_new = 0.0)
        term_rows = parameter_terms(neighbour["neighbor_terms"], basis)
        push!(checks, Dict{String, Any}(
            "neighbor_class" => klass,
            "parameter_terms" => JSON3.write([term for term in term_rows]),
            "warm_start" => JSON3.write(params),
        ))
    end
    write_csv(joinpath(output_dir, "neighbourhood_self_test.csv"), ["system_id", "dimension", "equation_idx", "library_size", "support_size", "add_one", "remove_one", "swap_one"], rows)
    write_csv(joinpath(output_dir, "warm_start_self_test.csv"), ["neighbor_class", "parameter_terms", "warm_start"], checks)
    optimizer_rows = t1f_optimizer_comparison_rows()
    write_csv(joinpath(output_dir, "optimizer_self_test.csv"), ["field", "reference_value", "wp_t1f_value", "matches_reference"], optimizer_rows)
    println("WP-T1f self-test rows: $(length(rows)); warm-start checks: $(length(checks)); optimizer fields: $(length(optimizer_rows))")
    return rows, checks
end

function t1f_analysis_dir_for(input_dir::AbstractString, analysis_root::AbstractString)
    clean = replace(String(input_dir), r"[\\/]+$" => "")
    label = isempty(clean) ? "aggregate" : basename(normpath(clean))
    isempty(label) && (label = "aggregate")
    return joinpath(analysis_root, label)
end

function run_t1f_k8s_indexed_cell(args, export_dir::AbstractString, true_coefficients)
    output_dir = env_path(WP_T1F_OUTPUT_DIR_ENV, WP_T1F_OUTPUT_DIR)
    index_list_path = env_path(WP_T1F_INDEX_LIST_ENV, joinpath(output_dir, "indices_all.txt"))
    mapping = resolve_k8s_cell_index(completion_index(), index_list_path)
    system, ic_set = cell_by_index(mapping.cell_index)
    cell_dir = joinpath(output_dir, @sprintf("cell_%03d_system_%04d_ic%d", mapping.cell_index, Int(system[:system_id]), Int(ic_set)))
    raw_jsonl_path = joinpath(cell_dir, "neighbour_rows.jsonl")
    fresh = arg_flag(args, "--fresh")
    fresh && isfile(raw_jsonl_path) && rm(raw_jsonl_path)
    rows = run_t1f_cell(system, Int(ic_set), export_dir, raw_jsonl_path, true_coefficients; smoke = false)
    write_csv(joinpath(cell_dir, "neighbour_rows.csv"), t1f_raw_output_columns(), rows)
    println("Raw rows: $(length(rows))")
    println("output_dir=$(cell_dir)")
    return nothing
end

function main(args = ARGS)
    output_dir = env_path(WP_T1F_OUTPUT_DIR_ENV, arg_value(args, "--output-dir", WP_T1F_OUTPUT_DIR))
    export_dir = arg_value(args, "--trajectory-export-dir", WP_T1D_TRAJECTORY_EXPORT_DIR)
    coeff_path = arg_value(args, "--true-coefficients", WP_T1F_TRUE_COEFFICIENTS_PATH)
    analysis_root = arg_value(args, "--analysis-root", WP_T1F_ANALYSIS_ROOT)
    input_dir = arg_value(args, "--input-dir", nothing)
    aggregate_only = arg_flag(args, "--aggregate-only")
    control_only = arg_flag(args, "--control-only")
    self_test = arg_flag(args, "--self-test")
    smoke = arg_flag(args, "--smoke")
    write_indices = arg_flag(args, "--write-index-lists")
    fresh = arg_flag(args, "--fresh")
    limit_value = arg_value(args, "--limit-cells", nothing)
    limit = limit_value === nothing ? nothing : parse(Int, limit_value)
    true_coefficients = load_t1f_true_coefficients(coeff_path)

    mkpath(output_dir)
    if write_indices
        paths = write_index_lists(output_dir)
        println("Wrote all indices: $(paths.all)")
        println("Wrote smoke indices: $(paths.smoke)")
        println("Wrote cell index map: $(paths.map)")
        return nothing
    end
    if aggregate_only
        input_dir === nothing && error("--aggregate-only requires --input-dir")
        raw_rows = collect_jsonl_rows(input_dir)
        analysis_dir = t1f_analysis_dir_for(input_dir, analysis_root)
        write_t1f_aggregates(raw_rows, analysis_dir)
        println("Aggregated raw rows: $(length(raw_rows))")
        println("analysis_dir=$(analysis_dir)")
        return nothing
    end
    if control_only
        run_t1f_control_only(output_dir, export_dir, true_coefficients)
        return nothing
    end
    if haskey(ENV, "JOB_COMPLETION_INDEX")
        return run_t1f_k8s_indexed_cell(args, export_dir, true_coefficients)
    end
    if self_test
        run_t1f_self_test(output_dir, true_coefficients)
        return nothing
    end

    cells = selected_cells(; smoke = smoke, limit = limit)
    raw_jsonl_path = joinpath(output_dir, "neighbour_rows.jsonl")
    fresh && isfile(raw_jsonl_path) && rm(raw_jsonl_path)
    raw_rows = Dict{String, Any}[]
    elapsed = @elapsed begin
        for (idx, (system, ic_set)) in enumerate(cells)
            @printf("[%d/%d] system_id=%d dim=%d ic=%d\n", idx, length(cells), Int(system[:system_id]), Int(system[:dim]), Int(ic_set))
            append!(raw_rows, run_t1f_cell(system, Int(ic_set), export_dir, raw_jsonl_path, true_coefficients; smoke = smoke))
        end
    end
    measured_loss_evals = sum(Int(json_get(row, "loss_evaluations", 0)) for row in raw_rows)
    if smoke || limit !== nothing
        write_t1f_projection(output_dir, selected_cells(); measured_elapsed_s = elapsed, measured_loss_evals = measured_loss_evals, smoke = false)
    else
        write_t1f_projection(output_dir, selected_cells(); smoke = false)
    end
    write_csv(joinpath(output_dir, "neighbour_rows.csv"), t1f_raw_output_columns(), raw_rows)
    write_t1f_aggregates(raw_rows, t1f_analysis_dir_for(output_dir, analysis_root))
    println("Raw rows: $(length(raw_rows))")
    println("Elapsed seconds (non-evidence): $(elapsed)")
    return nothing
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
