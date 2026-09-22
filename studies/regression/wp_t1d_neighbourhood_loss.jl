import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Printf
using Random
using SHA
using Statistics

include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_c_config.jl"))

const WP_T1D_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "wp_t1d_neighbourhood")
const WP_T1D_ANALYSIS_DIR = joinpath(@__DIR__, "..", "..", "analysis", "data", "wp_t1d_neighbourhood")
const WP_T1D_TRAJECTORY_EXPORT_DIR = joinpath(
    @__DIR__,
    "..",
    "..",
    "outputs",
    "phase_c_trajectory_hashes",
    "wp_c4c",
    "trajectory_export",
)
const WP_T1D_SENTINEL_LOSS = 1e6
const WP_T1D_REFERENCE_SECONDS_PER_FIT = 9.48
const WP_T1D_RUNTIME_CUTOFF_HOURS = 25.0
const WP_T1D_SEED = first(PHASE_C_SEEDS)
const WP_T1D_MARGIN_FACTORS = [1.0, 1.5, 2.0, 10.0, 100.0]
const WP_T1D_QUANTILES = [0.0, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 1.0]
const WP_T1D_INDEX_LIST_ENV = "EVO_T1D_INDEX_LIST"
const WP_T1D_OUTPUT_DIR_ENV = "EVO_T1D_OUTPUT_DIR"

function arg_value(args::Vector{String}, name::String, default)
    idx = findfirst(==(name), args)
    idx === nothing && return default
    idx == length(args) && error("Missing value for $(name)")
    return args[idx + 1]
end

arg_flag(args::Vector{String}, name::String) = name in args

function env_path(name::String, default)
    value = strip(get(ENV, name, ""))
    return isempty(value) ? default : value
end

function parse_int_list(text)
    text === nothing && return nothing
    clean = strip(String(text))
    isempty(clean) && return nothing
    return Set(parse(Int, strip(part)) for part in split(clean, ",") if !isempty(strip(part)))
end

function canonical_support_terms(support)
    return [sort(unique(Int[x for x in eq])) for eq in support]
end

function term_names(terms_by_eq, basis)
    return [[basis_term_name(basis, idx) for idx in eq_terms] for eq_terms in terms_by_eq]
end

function one_eq_replaced(terms_by_eq, eq_idx::Int, new_terms::Vector{Int})
    out = [copy(eq_terms) for eq_terms in terms_by_eq]
    out[eq_idx] = sort(unique(new_terms))
    return out
end

function support_key(terms_by_eq)
    return join([join(string.(eq_terms), ";") for eq_terms in terms_by_eq], "|")
end

function neighbour_records_for_equation(true_terms, basis, eq_idx::Int)
    p = basis_num_terms(basis)
    eq_terms = sort(unique(true_terms[eq_idx]))
    eq_set = Set(eq_terms)
    absent = [idx for idx in 1:p if !(idx in eq_set)]
    records = Dict{String, Any}[]

    for add_idx in absent
        neighbor = one_eq_replaced(true_terms, eq_idx, sort([eq_terms; add_idx]))
        push!(
            records,
            Dict{String, Any}(
                "neighbor_class" => "add_one",
                "equation_idx" => eq_idx,
                "neighbor_terms" => neighbor,
                "added_term" => add_idx,
                "removed_term" => nothing,
            ),
        )
    end

    for remove_idx in eq_terms
        new_eq = [idx for idx in eq_terms if idx != remove_idx]
        neighbor = one_eq_replaced(true_terms, eq_idx, new_eq)
        push!(
            records,
            Dict{String, Any}(
                "neighbor_class" => "remove_one",
                "equation_idx" => eq_idx,
                "neighbor_terms" => neighbor,
                "added_term" => nothing,
                "removed_term" => remove_idx,
            ),
        )
    end

    for remove_idx in eq_terms
        for add_idx in absent
            new_eq = sort([Int[idx for idx in eq_terms if idx != remove_idx]; add_idx])
            neighbor = one_eq_replaced(true_terms, eq_idx, new_eq)
            push!(
                records,
                Dict{String, Any}(
                    "neighbor_class" => "swap_one",
                    "equation_idx" => eq_idx,
                    "neighbor_terms" => neighbor,
                    "added_term" => add_idx,
                    "removed_term" => remove_idx,
                ),
            )
        end
    end

    return records
end

function measured_structure_fits(raw_rows)
    isempty(raw_rows) && return 0
    by_cell = Dict{Tuple{Int, Int}, Int}()
    for row in raw_rows
        key = (Int(row["system_id"]), Int(row["initial_condition_set"]))
        by_cell[key] = Int(row["total_parameter_fits"])
    end
    return sum(values(by_cell); init = 0)
end

function neighbourhood(true_terms, basis)
    true_key = support_key(true_terms)
    seen = Set{String}()
    records = Dict{String, Any}[]
    for eq_idx in eachindex(true_terms)
        for record in neighbour_records_for_equation(true_terms, basis, eq_idx)
            key = support_key(record["neighbor_terms"])
            key == true_key && error("True support appeared as its own neighbour for equation $(eq_idx)")
            key in seen && error("Duplicate neighbour support for equation $(eq_idx): $(key)")
            push!(seen, key)
            push!(records, record)
        end
    end
    return records
end

function assert_neighbourhood_counts(true_terms, basis)
    p = basis_num_terms(basis)
    records = neighbourhood(true_terms, basis)
    expected_total = 0
    for eq_idx in eachindex(true_terms)
        s = length(true_terms[eq_idx])
        counts = Dict("add_one" => 0, "remove_one" => 0, "swap_one" => 0)
        for record in records
            Int(record["equation_idx"]) == eq_idx || continue
            counts[String(record["neighbor_class"])] += 1
        end
        expected = Dict(
            "add_one" => p - s,
            "remove_one" => s,
            "swap_one" => s * (p - s),
        )
        for klass in keys(expected)
            counts[klass] == expected[klass] ||
                error("Neighbour count mismatch for eq $(eq_idx) $(klass): got $(counts[klass]), expected $(expected[klass])")
            expected_total += expected[klass]
        end
    end
    length(records) == expected_total ||
        error("Neighbour total mismatch: got $(length(records)), expected $(expected_total)")
    return true
end

function phase_c_exact_dim23_systems()
    systems = [
        system for system in PHASE_C_SYSTEMS
        if String(system[:representability]) == "exact" &&
           Int(system[:dim]) in (2, 3) &&
           Int(system[:system_id]) != 63
    ]
    return sort(systems; by = s -> Int(s[:system_id]))
end

function smoke_cells()
    systems = phase_c_exact_dim23_systems()
    dim2 = first([system for system in systems if Int(system[:dim]) == 2])
    dim3 = first([system for system in systems if Int(system[:dim]) == 3])
    return [(dim2, first(PHASE_C_IC_SETS)), (dim3, first(PHASE_C_IC_SETS))]
end

function selected_cells(; smoke::Bool = false, limit::Union{Nothing, Int} = nothing, only_systems = nothing)
    cells = smoke ? smoke_cells() : Tuple{Dict{Symbol, Any}, Int}[]
    if !smoke
        for system in phase_c_exact_dim23_systems()
            only_systems === nothing || Int(system[:system_id]) in only_systems || continue
            for ic_set in PHASE_C_IC_SETS
                push!(cells, (system, Int(ic_set)))
            end
        end
    end
    limit === nothing && return cells
    limit >= 0 || error("--limit-cells must be non-negative")
    return cells[1:min(limit, length(cells))]
end

function indexed_cells()
    return selected_cells()
end

function cell_index_table()
    rows = Dict{String, Any}[]
    for (one_index, (system, ic_set)) in enumerate(indexed_cells())
        zero_index = one_index - 1
        push!(
            rows,
            Dict{String, Any}(
                "cell_index" => zero_index,
                "system_id" => Int(system[:system_id]),
                "dimension" => Int(system[:dim]),
                "initial_condition_set" => Int(ic_set),
            ),
        )
    end
    return rows
end

function cell_by_index(cell_index::Int)
    cells = indexed_cells()
    0 <= cell_index < length(cells) ||
        error("Cell index $(cell_index) out of range 0:$(length(cells) - 1)")
    return cells[cell_index + 1]
end

function read_index_list(path::AbstractString)
    isfile(path) || error("Index list not found: $(path)")
    values = Int[]
    open(path, "r") do io
        for line in eachline(io)
            clean = strip(line)
            isempty(clean) && continue
            push!(values, parse(Int, clean))
        end
    end
    isempty(values) && error("Index list is empty: $(path)")
    return values
end

function completion_index()
    value = strip(get(ENV, "JOB_COMPLETION_INDEX", ""))
    isempty(value) && error("Set JOB_COMPLETION_INDEX")
    return parse(Int, value)
end

function resolve_k8s_cell_index(completion_index::Int, index_list_path::AbstractString)
    completion_index >= 0 || error("JOB_COMPLETION_INDEX must be >= 0, got $(completion_index)")
    values = read_index_list(index_list_path)
    line_number = completion_index + 1
    line_number <= length(values) ||
        error("JOB_COMPLETION_INDEX=$(completion_index) maps to line $(line_number), but $(index_list_path) has only $(length(values)) rows")
    return (
        completion_index = completion_index,
        index_list_line = line_number,
        cell_index = values[line_number],
        index_list_rows = length(values),
    )
end

function fit_count_for_cell(system)
    basis = phase_c_basis(Int(system[:dim]))
    true_terms = canonical_support_terms(system[:expected_support])
    return 1 + length(neighbourhood(true_terms, basis))
end

function projected_fit_counts(cells)
    rows = Dict{String, Any}[]
    total = 0
    for (system, ic_set) in cells
        count = fit_count_for_cell(system)
        total += count
        push!(
            rows,
            Dict{String, Any}(
                "system_id" => Int(system[:system_id]),
                "dimension" => Int(system[:dim]),
                "initial_condition_set" => Int(ic_set),
                "structure_fits" => count,
            ),
        )
    end
    return rows, total
end

function fit_fixed_structure_phase_c(structure_terms, system, basis, traj, seed::Int)
    structure = StructureSpec([sort(unique(Int[x for x in eq])) for eq in structure_terms])
    f!, n_params, _ = build_rhs(structure, basis)
    optimizer = build_reference_optimizer(max_fit_attempts = PHASE_C_MAX_FIT_ATTEMPTS)
    options = build_options(seed)

    params = Float64[]
    fit_loss = nothing
    fit_meta = nothing
    Random.seed!(seed)
    if n_params > 0
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

function fit_budget_exhausted(fit_result)
    meta = fit_result["fit_meta"]
    meta === nothing && return false
    if haskey(meta, :stop_reason)
        return String(meta.stop_reason) == "loss_eval_budget"
    end
    if haskey(meta, :optimizer_eval_budget_limit_hits)
        return Int(meta.optimizer_eval_budget_limit_hits) > 0
    end
    return false
end

function is_sentinel_loss(value)
    value === nothing && return true
    loss = Float64(value)
    return !isfinite(loss) || loss >= WP_T1D_SENTINEL_LOSS
end

function log10_loss_ratio(neighbor_loss, true_loss; neighbor_budget_exhausted::Bool = false, true_budget_exhausted::Bool = false)
    (neighbor_budget_exhausted || true_budget_exhausted) && return nothing
    (is_sentinel_loss(neighbor_loss) || is_sentinel_loss(true_loss)) && return nothing
    true_loss_value = Float64(true_loss)
    neighbor = Float64(neighbor_loss)
    true_loss_value <= 0.0 && return nothing
    neighbor <= 0.0 && return -Inf
    return log10(neighbor / true_loss_value)
end

function pruned_terms_by_eq(coefficients)
    out = Vector{Vector{Int}}()
    for eq_model in coefficients
        term_idxs = Int[Int(term["term_index"]) for term in eq_model]
        coeffs = Float64[Float64(term["coefficient"]) for term in eq_model]
        push!(out, pruned_support_idxs_for_equation(term_idxs, coeffs))
    end
    return out
end

function extra_term_survives(record, fit_result)
    String(record["neighbor_class"]) == "add_one" || return nothing
    added = record["added_term"]
    added === nothing && return nothing
    eq_idx = Int(record["equation_idx"])
    pruned = pruned_terms_by_eq(fit_result["coefficients"])
    return Int(added) in pruned[eq_idx]
end

function append_jsonl!(path::AbstractString, record)
    mkpath(dirname(path))
    open(path, "a") do io
        JSON3.write(io, json_safe(record))
        write(io, '\n')
    end
end

function csv_escape(value)
    value === nothing && return ""
    value isa Bool && return value ? "true" : "false"
    text = value isa AbstractString ? String(value) : string(value)
    if occursin(",", text) || occursin("\"", text) || occursin("\n", text) || occursin("\r", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::AbstractString, columns::Vector{String}, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(csv_escape.(columns), ","))
        for row in rows
            println(io, join([csv_escape(get(row, col, nothing)) for col in columns], ","))
        end
    end
    return path
end

function parse_csv_line(line::AbstractString)
    fields = String[]
    buf = IOBuffer()
    in_quotes = false
    i = firstindex(line)
    while i <= lastindex(line)
        c = line[i]
        if c == '"'
            if in_quotes && i < lastindex(line) && line[nextind(line, i)] == '"'
                write(buf, UInt8('"'))
                i = nextind(line, i)
            else
                in_quotes = !in_quotes
            end
        elseif c == ',' && !in_quotes
            push!(fields, String(take!(buf)))
        else
            print(buf, c)
        end
        i = nextind(line, i)
    end
    push!(fields, String(take!(buf)))
    return fields
end

function read_csv(path::AbstractString)
    lines = readlines(path)
    isempty(lines) && error("Empty CSV: $(path)")
    columns = parse_csv_line(lines[1])
    rows = Dict{String, String}[]
    for (line_no, line) in enumerate(lines[2:end])
        isempty(strip(line)) && continue
        values = parse_csv_line(line)
        length(values) == length(columns) ||
            error("CSV $(path) line $(line_no + 1) has $(length(values)) fields, expected $(length(columns))")
        push!(rows, Dict(columns[i] => values[i] for i in eachindex(columns)))
    end
    return rows
end

function append_float64_le!(bytes::Vector{UInt8}, value)
    bits = reinterpret(UInt64, Float64[value])[1]
    @inbounds for shift in 0:8:56
        push!(bytes, UInt8((bits >> shift) & 0xff))
    end
    return bytes
end

function sha256_vector_float64_le(values::AbstractVector)
    bytes = UInt8[]
    sizehint!(bytes, 8 * length(values))
    @inbounds for value in values
        append_float64_le!(bytes, value)
    end
    return bytes2hex(sha256(bytes))
end

function sha256_matrix_float64_le_c_order(values::AbstractMatrix)
    rows, cols = size(values)
    bytes = UInt8[]
    sizehint!(bytes, 8 * rows * cols)
    @inbounds for row in 1:rows
        for col in 1:cols
            append_float64_le!(bytes, values[row, col])
        end
    end
    return bytes2hex(sha256(bytes))
end

function parse_shape(text::AbstractString)
    clean = strip(String(text))
    startswith(clean, "[") && endswith(clean, "]") ||
        error("Unsupported shape string: $(text)")
    inner = strip(clean[2:(end - 1)])
    isempty(inner) && return Int[]
    return [parse(Int, strip(part)) for part in split(inner, ",")]
end

function read_float64_le_vector(path::AbstractString, expected_length::Int)
    bytes = read(path)
    length(bytes) == 8 * expected_length ||
        error("$(path) has $(length(bytes)) bytes, expected $(8 * expected_length)")
    values = Vector{Float64}(undef, expected_length)
    @inbounds for idx in 1:expected_length
        offset = 8 * (idx - 1)
        bits = UInt64(0)
        for shift in 0:8:56
            bits |= UInt64(bytes[offset + div(shift, 8) + 1]) << shift
        end
        values[idx] = reinterpret(Float64, bits)
    end
    return values
end

function read_float64_le_matrix_c_order(path::AbstractString, rows::Int, cols::Int)
    values = read_float64_le_vector(path, rows * cols)
    out = Matrix{Float64}(undef, rows, cols)
    pos = 1
    @inbounds for row in 1:rows
        for col in 1:cols
            out[row, col] = values[pos]
            pos += 1
        end
    end
    return out
end

function load_trajectory_manifest(export_dir::AbstractString)
    path = joinpath(export_dir, "trajectory_manifest.csv")
    isfile(path) || error("Missing trajectory manifest: $(path)")
    rows = read_csv(path)
    manifest = Dict{Tuple{Int, Int}, Dict{String, String}}()
    for row in rows
        key = (parse(Int, row["system_id"]), parse(Int, row["initial_condition_set"]))
        haskey(manifest, key) && error("Duplicate trajectory manifest row for $(key)")
        manifest[key] = row
    end
    return manifest
end

function verify_trajectory_hash!(manifest, system, ic_set::Int, traj)
    key = (Int(system[:system_id]), ic_set)
    haskey(manifest, key) || error("Trajectory manifest is missing system_id=$(key[1]) ic=$(key[2])")
    row = manifest[key]
    time_sha = sha256_vector_float64_le(traj.t)
    state_sha = sha256_matrix_float64_le_c_order(traj.x)
    time_sha == row["time_sha256"] ||
        error("Time hash mismatch for system_id=$(key[1]) ic=$(key[2]): got $(time_sha), expected $(row["time_sha256"])")
    state_sha == row["state_sha256"] ||
        error("State hash mismatch for system_id=$(key[1]) ic=$(key[2]): got $(state_sha), expected $(row["state_sha256"])")
    return state_sha
end

function load_exported_trajectory(export_dir::AbstractString, manifest, system, ic_set::Int)
    key = (Int(system[:system_id]), ic_set)
    haskey(manifest, key) || error("Trajectory manifest is missing system_id=$(key[1]) ic=$(key[2])")
    row = manifest[key]
    haskey(row, "time_path") && haskey(row, "state_path") ||
        error("Trajectory manifest row for system_id=$(key[1]) ic=$(key[2]) does not contain export paths")
    time_shape = parse_shape(row["time_shape"])
    state_shape = parse_shape(row["state_shape"])
    length(time_shape) == 1 || error("Unexpected time shape for $(key): $(row["time_shape"])")
    length(state_shape) == 2 || error("Unexpected state shape for $(key): $(row["state_shape"])")
    time_path = joinpath(export_dir, row["time_path"])
    state_path = joinpath(export_dir, row["state_path"])
    isfile(time_path) || error("Missing exported trajectory time file: $(time_path)")
    isfile(state_path) || error("Missing exported trajectory state file: $(state_path)")
    traj = Trajectory(
        read_float64_le_vector(time_path, time_shape[1]),
        read_float64_le_matrix_c_order(state_path, state_shape[1], state_shape[2]),
    )
    sha = verify_trajectory_hash!(manifest, system, ic_set, traj)
    return traj, sha, "export"
end

function trajectory_for_cell(export_dir::AbstractString, system, ic_set::Int)
    manifest_path = joinpath(export_dir, "trajectory_manifest.csv")
    if isfile(manifest_path)
        manifest = load_trajectory_manifest(export_dir)
        return load_exported_trajectory(export_dir, manifest, system, ic_set)
    end
    traj = build_trajectory(system, ic_set)
    return traj, sha256_matrix_float64_le_c_order(traj.x), "generated"
end

function run_cell(system, ic_set::Int, export_dir::AbstractString, raw_jsonl_path::AbstractString)
    system_id = Int(system[:system_id])
    dim = Int(system[:dim])
    basis = phase_c_basis(dim)
    true_terms = canonical_support_terms(system[:expected_support])
    assert_neighbourhood_counts(true_terms, basis)
    traj, trajectory_sha, trajectory_source = trajectory_for_cell(export_dir, system, ic_set)
    git = git_provenance()
    fingerprint = phase_c_fingerprint()

    start_time = time()
    true_result = fit_fixed_structure_phase_c(true_terms, system, basis, traj, WP_T1D_SEED)
    elapsed_true = time() - start_time
    true_loss = true_result["loss"]
    sentinel_true = is_sentinel_loss(true_loss)
    budget_exhausted_true = fit_budget_exhausted(true_result)
    neighbours = neighbourhood(true_terms, basis)
    rows = Dict{String, Any}[]
    total_parameter_fits = 1 + length(neighbours)

    for (idx, neighbor) in enumerate(neighbours)
        fit_start = time()
        fit_result = fit_fixed_structure_phase_c(neighbor["neighbor_terms"], system, basis, traj, WP_T1D_SEED)
        elapsed = time() - fit_start
        neighbor_loss = fit_result["loss"]
        sentinel_neighbor = is_sentinel_loss(neighbor_loss)
        budget_exhausted_neighbor = fit_budget_exhausted(fit_result)
        margin = log10_loss_ratio(
            neighbor_loss,
            true_loss;
            neighbor_budget_exhausted = budget_exhausted_neighbor,
            true_budget_exhausted = budget_exhausted_true,
        )
        beats = !sentinel_true &&
                !sentinel_neighbor &&
                !budget_exhausted_true &&
                !budget_exhausted_neighbor &&
                Float64(neighbor_loss) < Float64(true_loss)
        row = Dict{String, Any}(
            "system_id" => system_id,
            "dimension" => dim,
            "initial_condition_set" => ic_set,
            "equation_idx" => Int(neighbor["equation_idx"]),
            "neighbor_class" => String(neighbor["neighbor_class"]),
            "neighbor_terms" => JSON3.write(term_names(neighbor["neighbor_terms"], basis)),
            "true_terms" => JSON3.write(term_names(true_terms, basis)),
            "support_size_true" => sum(length(eq) for eq in true_terms),
            "support_size_neighbor" => sum(length(eq) for eq in neighbor["neighbor_terms"]),
            "loss_true" => true_loss,
            "loss_neighbor" => neighbor_loss,
            "log10_loss_ratio" => margin,
            "beats_true" => beats,
            "sentinel_true" => sentinel_true,
            "sentinel_neighbor" => sentinel_neighbor,
            "budget_exhausted_true" => budget_exhausted_true,
            "budget_exhausted_neighbor" => budget_exhausted_neighbor,
            "bfgs_max_loss_evals" => BFGS_MAX_LOSS_EVALS,
            "extra_term_survives_pruning" => extra_term_survives(neighbor, fit_result),
            "total_parameter_fits" => total_parameter_fits,
            "elapsed_s_non_evidence" => elapsed,
            "git_hash" => git.git_hash,
            "config_fingerprint" => fingerprint,
            "trajectory_sha256" => trajectory_sha,
            "trajectory_source" => trajectory_source,
            "added_term" => neighbor["added_term"] === nothing ? nothing : basis_term_name(basis, Int(neighbor["added_term"])),
            "removed_term" => neighbor["removed_term"] === nothing ? nothing : basis_term_name(basis, Int(neighbor["removed_term"])),
            "cell_true_fit_elapsed_s_non_evidence" => elapsed_true,
            "neighbor_index" => idx,
        )
        push!(rows, row)
        append_jsonl!(raw_jsonl_path, row)
    end
    return rows
end

function quantile_or_nothing(values::Vector{Float64}, p::Float64)
    isempty(values) && return nothing
    return quantile(values, p)
end

function aggregate_rows(raw_rows)
    by_key = Dict{Tuple{Int, String}, Vector{Dict{String, Any}}}()
    for row in raw_rows
        key = (Int(row["dimension"]), String(row["neighbor_class"]))
        if !haskey(by_key, key)
            by_key[key] = Dict{String, Any}[]
        end
        push!(by_key[key], row)
    end

    summary = Dict{String, Any}[]
    quantiles = Dict{String, Any}[]
    thresholds = Dict{String, Any}[]
    add_pruning = Dict{String, Any}[]
    swap_beaters = Dict{String, Any}[]

    for (key, rows) in sort(collect(by_key); by = x -> x[1])
        dim, klass = key
        cell_keys = Set((Int(row["system_id"]), Int(row["initial_condition_set"])) for row in rows)
        beating_cell_keys = Set((Int(row["system_id"]), Int(row["initial_condition_set"])) for row in rows if row["beats_true"] === true)
        margins = Float64[Float64(row["log10_loss_ratio"]) for row in rows if row["log10_loss_ratio"] !== nothing && isfinite(Float64(row["log10_loss_ratio"]))]
        push!(
            summary,
            Dict{String, Any}(
                "dimension" => dim,
                "neighbor_class" => klass,
                "n_cells" => length(cell_keys),
                "n_cells_with_beating_neighbor" => length(beating_cell_keys),
                "share_cells_with_beating_neighbor" => isempty(cell_keys) ? nothing : length(beating_cell_keys) / length(cell_keys),
                "n_neighbor_rows" => length(rows),
                "sentinel_true_rows" => count(row -> row["sentinel_true"] === true, rows),
                "sentinel_neighbor_rows" => count(row -> row["sentinel_neighbor"] === true, rows),
                "budget_exhausted_true_rows" => count(row -> row["budget_exhausted_true"] === true, rows),
                "budget_exhausted_neighbor_rows" => count(row -> row["budget_exhausted_neighbor"] === true, rows),
            ),
        )
        for q in WP_T1D_QUANTILES
            push!(
                quantiles,
                Dict{String, Any}(
                    "dimension" => dim,
                    "neighbor_class" => klass,
                    "quantile" => q,
                    "log10_loss_ratio" => quantile_or_nothing(margins, q),
                    "n_margins" => length(margins),
                ),
            )
        end
        for factor in WP_T1D_MARGIN_FACTORS
            threshold = -log10(factor)
            count_rows = count(value -> value < threshold, margins)
            push!(
                thresholds,
                Dict{String, Any}(
                    "dimension" => dim,
                    "neighbor_class" => klass,
                    "margin_factor" => factor,
                    "log10_threshold" => threshold,
                    "n_neighbors_better_by_factor" => count_rows,
                    "share_neighbors_better_by_factor" => isempty(margins) ? nothing : count_rows / length(margins),
                    "n_margins" => length(margins),
                ),
            )
        end
        if klass == "add_one"
            applicable = [row for row in rows if row["extra_term_survives_pruning"] !== nothing]
            survives = count(row -> row["extra_term_survives_pruning"] === true, applicable)
            push!(
                add_pruning,
                Dict{String, Any}(
                    "dimension" => dim,
                    "neighbor_class" => klass,
                    "n_add_one_neighbors" => length(applicable),
                    "n_extra_term_survives_pruning" => survives,
                    "share_extra_term_survives_pruning" => isempty(applicable) ? nothing : survives / length(applicable),
                ),
            )
        end
        if klass == "swap_one"
            for row in rows
                row["beats_true"] === true || continue
                push!(
                    swap_beaters,
                    Dict{String, Any}(
                        "dimension" => dim,
                        "system_id" => row["system_id"],
                        "initial_condition_set" => row["initial_condition_set"],
                        "equation_idx" => row["equation_idx"],
                        "neighbor_terms" => row["neighbor_terms"],
                        "true_terms" => row["true_terms"],
                        "loss_true" => row["loss_true"],
                        "loss_neighbor" => row["loss_neighbor"],
                        "log10_loss_ratio" => row["log10_loss_ratio"],
                    ),
                )
            end
        end
    end
    return summary, quantiles, thresholds, add_pruning, swap_beaters
end

function write_projection(output_dir::AbstractString, cells; measured_elapsed_s = nothing, measured_fits = nothing)
    rows, total = projected_fit_counts(cells)
    projected_seconds = if measured_elapsed_s !== nothing && measured_fits !== nothing && measured_fits > 0
        total * Float64(measured_elapsed_s) / Float64(measured_fits)
    else
        total * WP_T1D_REFERENCE_SECONDS_PER_FIT
    end
    projection = Dict{String, Any}(
        "n_cells" => length(cells),
        "projected_structure_fits" => total,
        "projection_basis" => measured_elapsed_s === nothing ? "phase_b_reference_seconds_per_fit" : "smoke_elapsed_seconds_per_fit",
        "reference_seconds_per_fit" => WP_T1D_REFERENCE_SECONDS_PER_FIT,
        "measured_elapsed_s_non_evidence" => measured_elapsed_s,
        "measured_structure_fits" => measured_fits,
        "projected_runtime_hours_non_evidence" => projected_seconds / 3600.0,
        "runtime_cutoff_hours" => WP_T1D_RUNTIME_CUTOFF_HOURS,
        "full_run_allowed_by_projection" => projected_seconds / 3600.0 <= WP_T1D_RUNTIME_CUTOFF_HOURS,
        "rows" => rows,
    )
    path = joinpath(output_dir, "projection.json")
    mkpath(dirname(path))
    open(path, "w") do io
        JSON3.write(io, json_safe(projection))
        write(io, '\n')
    end
    write_csv(
        joinpath(output_dir, "projection_cells.csv"),
        ["system_id", "dimension", "initial_condition_set", "structure_fits"],
        rows,
    )
    return projection
end

function write_index_lists(output_dir::AbstractString)
    rows = cell_index_table()
    write_csv(
        joinpath(output_dir, "cell_index_map.csv"),
        ["cell_index", "system_id", "dimension", "initial_condition_set"],
        rows,
    )
    all_path = joinpath(output_dir, "indices_all.txt")
    smoke_path = joinpath(output_dir, "indices_smoke_sys24_sys25_ic1.txt")
    open(all_path, "w") do io
        for row in rows
            println(io, row["cell_index"])
        end
    end
    smoke_indices = [
        row["cell_index"] for row in rows
        if Int(row["initial_condition_set"]) == 1 && Int(row["system_id"]) in (24, 25)
    ]
    length(smoke_indices) == 2 ||
        error("Expected two smoke indices for system 24 IC 1 and system 25 IC 1, got $(length(smoke_indices))")
    open(smoke_path, "w") do io
        for idx in smoke_indices
            println(io, idx)
        end
    end
    return (all = all_path, smoke = smoke_path, map = joinpath(output_dir, "cell_index_map.csv"))
end

function run_k8s_indexed_cell(args, export_dir::AbstractString)
    output_dir = env_path(WP_T1D_OUTPUT_DIR_ENV, WP_T1D_OUTPUT_DIR)
    index_list_path = env_path(WP_T1D_INDEX_LIST_ENV, joinpath(output_dir, "indices_all.txt"))
    mapping = resolve_k8s_cell_index(completion_index(), index_list_path)
    system, ic_set = cell_by_index(mapping.cell_index)
    cell_dir = joinpath(output_dir, @sprintf("cell_%03d_system_%04d_ic%d", mapping.cell_index, Int(system[:system_id]), Int(ic_set)))
    raw_jsonl_path = joinpath(cell_dir, "neighbour_rows.jsonl")
    fresh = arg_flag(args, "--fresh")
    fresh && isfile(raw_jsonl_path) && rm(raw_jsonl_path)

    println("job_completion_index=$(mapping.completion_index)")
    println("index_list=$(index_list_path)")
    println("index_list_line=$(mapping.index_list_line)")
    println("index_list_rows=$(mapping.index_list_rows)")
    println("cell_index=$(mapping.cell_index)")
    println("system_id=$(Int(system[:system_id]))")
    println("dimension=$(Int(system[:dim]))")
    println("initial_condition_set=$(Int(ic_set))")

    rows = run_cell(system, Int(ic_set), export_dir, raw_jsonl_path)
    write_csv(
        joinpath(cell_dir, "neighbour_rows.csv"),
        raw_output_columns(),
        rows,
    )
    println("Raw rows: $(length(rows))")
    println("output_dir=$(cell_dir)")
    return nothing
end

function run_self_test()
    rows = Dict{String, Any}[]
    for system in phase_c_exact_dim23_systems()
        basis = phase_c_basis(Int(system[:dim]))
        true_terms = canonical_support_terms(system[:expected_support])
        assert_neighbourhood_counts(true_terms, basis)
        p = basis_num_terms(basis)
        for eq_idx in eachindex(true_terms)
            s = length(true_terms[eq_idx])
            push!(
                rows,
                Dict{String, Any}(
                    "system_id" => Int(system[:system_id]),
                    "dimension" => Int(system[:dim]),
                    "equation_idx" => eq_idx,
                    "library_size" => p,
                    "support_size" => s,
                    "add_one" => p - s,
                    "remove_one" => s,
                    "swap_one" => s * (p - s),
                ),
            )
        end
    end
    return rows
end

function raw_output_columns()
    return [
        "system_id", "dimension", "initial_condition_set", "equation_idx",
        "neighbor_class", "neighbor_terms", "true_terms", "support_size_true",
        "support_size_neighbor", "loss_true", "loss_neighbor", "log10_loss_ratio",
        "beats_true", "sentinel_true", "sentinel_neighbor", "budget_exhausted_true",
        "budget_exhausted_neighbor", "bfgs_max_loss_evals", "extra_term_survives_pruning",
        "total_parameter_fits", "elapsed_s_non_evidence", "git_hash",
        "config_fingerprint", "trajectory_sha256", "trajectory_source",
    ]
end

function main(args = ARGS)
    output_dir = env_path(WP_T1D_OUTPUT_DIR_ENV, arg_value(args, "--output-dir", WP_T1D_OUTPUT_DIR))
    analysis_dir = arg_value(args, "--analysis-dir", WP_T1D_ANALYSIS_DIR)
    export_dir = arg_value(args, "--trajectory-export-dir", WP_T1D_TRAJECTORY_EXPORT_DIR)
    limit_value = arg_value(args, "--limit-cells", nothing)
    limit = limit_value === nothing ? nothing : parse(Int, limit_value)
    only_systems = parse_int_list(arg_value(args, "--systems", nothing))
    smoke = arg_flag(args, "--smoke")
    self_test = arg_flag(args, "--self-test")
    projection_only = arg_flag(args, "--projection-only")
    write_indices = arg_flag(args, "--write-index-lists")
    fresh = arg_flag(args, "--fresh")

    mkpath(output_dir)
    mkpath(analysis_dir)

    if write_indices
        paths = write_index_lists(output_dir)
        println("Wrote all indices: $(paths.all)")
        println("Wrote smoke indices: $(paths.smoke)")
        println("Wrote cell index map: $(paths.map)")
        return nothing
    end

    if haskey(ENV, "JOB_COMPLETION_INDEX")
        return run_k8s_indexed_cell(args, export_dir)
    end

    if self_test
        rows = run_self_test()
        write_csv(
            joinpath(output_dir, "neighbourhood_self_test.csv"),
            ["system_id", "dimension", "equation_idx", "library_size", "support_size", "add_one", "remove_one", "swap_one"],
            rows,
        )
        println("Neighbourhood self-test rows: $(length(rows))")
        return nothing
    end

    cells = selected_cells(; smoke = smoke, limit = limit, only_systems = only_systems)
    full_cells = selected_cells()
    projection = write_projection(output_dir, full_cells)
    println("Projected full-run structure fits: $(projection["projected_structure_fits"])")
    println(@sprintf("Projected full-run runtime: %.3f h", projection["projected_runtime_hours_non_evidence"]))
    projection_only && return nothing
    if !smoke && limit === nothing && only_systems === nothing && projection["full_run_allowed_by_projection"] !== true
        error(
            @sprintf(
                "Full run projection %.3f h exceeds cutoff %.3f h; run the smoke path first and report the projection.",
                projection["projected_runtime_hours_non_evidence"],
                WP_T1D_RUNTIME_CUTOFF_HOURS,
            ),
        )
    end

    raw_jsonl_path = joinpath(output_dir, "neighbour_rows.jsonl")
    fresh && isfile(raw_jsonl_path) && rm(raw_jsonl_path)
    raw_rows = Dict{String, Any}[]
    elapsed = @elapsed begin
        for (idx, (system, ic_set)) in enumerate(cells)
            @printf(
                "[%d/%d] system_id=%d dim=%d ic=%d\n",
                idx,
                length(cells),
                Int(system[:system_id]),
                Int(system[:dim]),
                Int(ic_set),
            )
            append!(raw_rows, run_cell(system, ic_set, export_dir, raw_jsonl_path))
        end
    end
    measured_fits = measured_structure_fits(raw_rows)
    if smoke || limit !== nothing || only_systems !== nothing
        write_projection(output_dir, full_cells; measured_elapsed_s = elapsed, measured_fits = measured_fits)
    end

    write_csv(joinpath(output_dir, "neighbour_rows.csv"), raw_output_columns(), raw_rows)
    summary, quantiles, thresholds, add_pruning, swap_beaters = aggregate_rows(raw_rows)
    write_csv(
        joinpath(analysis_dir, "aggregate_by_dimension_class.csv"),
        ["dimension", "neighbor_class", "n_cells", "n_cells_with_beating_neighbor", "share_cells_with_beating_neighbor", "n_neighbor_rows", "sentinel_true_rows", "sentinel_neighbor_rows", "budget_exhausted_true_rows", "budget_exhausted_neighbor_rows"],
        summary,
    )
    write_csv(
        joinpath(analysis_dir, "margin_quantiles_by_dimension_class.csv"),
        ["dimension", "neighbor_class", "quantile", "log10_loss_ratio", "n_margins"],
        quantiles,
    )
    write_csv(
        joinpath(analysis_dir, "margin_threshold_grid_by_dimension_class.csv"),
        ["dimension", "neighbor_class", "margin_factor", "log10_threshold", "n_neighbors_better_by_factor", "share_neighbors_better_by_factor", "n_margins"],
        thresholds,
    )
    write_csv(
        joinpath(analysis_dir, "add_one_pruning_survival_by_dimension.csv"),
        ["dimension", "neighbor_class", "n_add_one_neighbors", "n_extra_term_survives_pruning", "share_extra_term_survives_pruning"],
        add_pruning,
    )
    write_csv(
        joinpath(analysis_dir, "swap_one_beating_neighbours.csv"),
        ["dimension", "system_id", "initial_condition_set", "equation_idx", "neighbor_terms", "true_terms", "loss_true", "loss_neighbor", "log10_loss_ratio"],
        swap_beaters,
    )
    println("Raw rows: $(length(raw_rows))")
    println("Elapsed seconds (non-evidence): $(elapsed)")
    return nothing
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
