import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using JSON3
using LinearAlgebra
using Printf
using Statistics

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
include(joinpath(REPO_ROOT, "studies", "output_path_guard.jl"))
include(joinpath(REPO_ROOT, "studies", "regression", "run_regression.jl"))
include(joinpath(REPO_ROOT, "studies", "regression", "phase_c_config.jl"))

const SCRIPT_SLUG = "wp_s04_stage_cap_noise_thinning"
const OUTPUT_DIR = study_resolve_output_dir(joinpath(REPO_ROOT, "outputs", "studies", "lookahead", SCRIPT_SLUG), ARGS)
const DETAIL_CSV = joinpath(OUTPUT_DIR, "stage_cap_noise_thinning_detail.csv")
const METADATA_JSON = joinpath(OUTPUT_DIR, "metadata.json")
const REFERENCE_HISTORY = joinpath(REPO_ROOT, "outputs", "phase_c_campaign_221a3a7", "history.jsonl")

const SIGMAS = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05]
const RHOS = [0.0, 0.5]
const NONCLEAN_REALIZATIONS = [1, 2, 3]
const CLEAN_REALIZATION = 0
const DEFAULT_LIMIT = 0

function arg_value(name::String, default::Union{Nothing,String} = nothing)
    idx = findfirst(==(name), ARGS)
    idx === nothing && return default
    idx == length(ARGS) && error("Missing value after $(name)")
    return ARGS[idx + 1]
end

function parse_int_csv(value::Union{Nothing,String})
    value === nothing && return nothing
    stripped = strip(value)
    isempty(stripped) && return Int[]
    return [parse(Int, strip(part)) for part in split(stripped, ",")]
end

function selected_exact_systems()
    requested = parse_int_csv(arg_value("--systems"))
    limit = parse(Int, arg_value("--limit", string(DEFAULT_LIMIT)))
    systems = [
        system for system in phase_c_exact_systems()
        if Int(system[:dim]) <= 2 && (requested === nothing || Int(system[:system_id]) in requested)
    ]
    systems = sort(systems; by = system -> Int(system[:system_id]))
    if requested === nothing && limit > 0
        systems = systems[1:min(limit, length(systems))]
    end
    if requested === nothing && limit == 0 && length(systems) != 21
        error("Expected 21 exact Phase-C systems with dim <= 2, got $(length(systems))")
    end
    return systems
end

function csv_escape(value)
    text = string(value)
    if occursin('"', text) || occursin(',', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

format_cap(cap) = cap === nothing ? "nothing" : string(Int(cap))

function cap_sort_value(cap)
    cap === nothing && return typemax(Int)
    return Int(cap)
end

function classify_cap_change(cap, clean_cap)
    cap === clean_cap && return "same"
    cap === nothing && return "to_nothing"
    clean_cap === nothing && return "from_nothing"
    cap_sort_value(cap) < cap_sort_value(clean_cap) && return "tighter"
    return "wider"
end

function equation_required_stages(basis::StagedPolynomialBasis, support)
    support === nothing && error("Cannot derive required stages for surrogate support")
    stages = Int[]
    for eq_support in support
        isempty(eq_support) && error("Cannot derive required stage from empty equation support")
        push!(stages, maximum(phase_c_stage_for_term_idx.(Ref(basis), eq_support)))
    end
    return stages
end

function finite_median_or_inf(values)
    finite_values = [value for value in values if isfinite(value)]
    isempty(finite_values) && return Inf
    return median(finite_values)
end

function cap_truncates_truth(cap, required_stage::Int)
    cap === nothing && return false
    return Int(cap) < required_stage
end

function true_rhs_matrix(system, traj::Trajectory)
    rhs! = system_rhs(system)
    n = length(traj.t)
    dim = Int(system[:dim])
    out = zeros(Float64, n, dim)
    du = zeros(Float64, dim)
    for i in 1:n
        rhs!(du, view(traj.x, i, :), nothing, traj.t[i])
        out[i, :] .= du
    end
    return out
end

function trajectory_on_times(source::Trajectory, target_t::AbstractVector)
    index_by_time = Dict{Float64, Int}(Float64(t) => i for (i, t) in pairs(source.t))
    idxs = Int[]
    for t in target_t
        key = Float64(t)
        haskey(index_by_time, key) || error("Target time $(t) is not present in the source trajectory")
        push!(idxs, index_by_time[key])
    end
    return Trajectory(collect(target_t), source.x[idxs, :])
end

function cap_diagnostics_for_equation(traj::Trajectory, basis::StagedPolynomialBasis,
                                      dX::Matrix{Float64}, rich::Matrix{Float64},
                                      eq::Int, policy::LookAheadStageCapPolicy)
    y = dX[:, eq]
    weights = policy.weighting == :richardson_wls ? EvoODE._cap_weights_from_richardson(rich[:, eq]) : ones(length(y))
    max_basis_stage = EvoODE._max_stage(basis)
    new_counts = [length(basis.term_groups[s]) for s in 1:max_basis_stage]
    applicable_stages = [s for s in 1:max_basis_stage if new_counts[s] > 0]
    split_decisions = NamedTuple[]
    residual_by_split = Vector{Vector{Float64}}()
    floor_by_split = Vector{Vector{Float64}}()
    usable_by_split = Vector{Vector{Bool}}()

    for split in EvoODE._cap_splits(length(traj.t))
        residuals = fill(Inf, max_basis_stage)
        floors = fill(Inf, max_basis_stage)
        usable = falses(max_basis_stage)
        for stage in 1:max_basis_stage
            idxs = EvoODE._cap_cumulative_stage_idxs(basis, stage)
            Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
            usable[stage] = EvoODE._cap_stage_condition(Phi, y, split.fit, policy)
            fit = EvoODE._cap_fit_eval(Phi, y, split.fit, split.holdout, weights)
            residuals[stage] = fit.residual
            floors[stage] = mean(abs2, rich[split.holdout, eq])
            usable[stage] &= fit.valid
        end
        push!(residual_by_split, residuals)
        push!(floor_by_split, floors)
        push!(usable_by_split, usable)
        push!(split_decisions, EvoODE._cap_split_decision(residuals, usable, floors, applicable_stages, policy))
    end

    cap = EvoODE._cap_aggregate_split_decisions(split_decisions, policy)
    median_residuals = [finite_median_or_inf(residuals[stage] for residuals in residual_by_split) for stage in 1:max_basis_stage]
    median_floors = [finite_median_or_inf(floors[stage] for floors in floor_by_split) for stage in 1:max_basis_stage]
    usable_counts = [
        count(usable -> usable[stage], usable_by_split)
        for stage in 1:max_basis_stage
    ]
    return (
        cap = cap,
        residuals_median = median_residuals,
        floors_median = median_floors,
        usable_split_counts = usable_counts,
        split_decisions = split_decisions,
    )
end

function cap_diagnostics(traj::Trajectory, basis::StagedPolynomialBasis, policy::LookAheadStageCapPolicy)
    dX = EvoODE._cap_estimate_derivatives(traj, policy.estimator)
    rich = EvoODE._cap_richardson_error_estimate(traj, policy.estimator)
    _, dim = size(traj.x)
    return [
        cap_diagnostics_for_equation(traj, basis, dX, rich, eq, policy)
        for eq in 1:dim
    ]
end

function local_poly_window(n::Int, i::Int; halfwidth::Int = 4, degree::Int = 3)
    lo = max(1, i - halfwidth)
    hi = min(n, i + halfwidth)
    if hi - lo + 1 < degree + 1
        lo = max(1, min(lo, n - degree))
        hi = min(n, max(hi, degree + 1))
    end
    return lo:hi
end

function derivative_weights(t::AbstractVector, i::Int; halfwidth::Int = 4, degree::Int = 3)
    idxs = collect(local_poly_window(length(t), i; halfwidth = halfwidth, degree = degree))
    z = t[idxs] .- t[i]
    A = hcat([z .^ p for p in 0:degree]...)
    weights = (A \ Matrix{Float64}(I, length(idxs), length(idxs)))[2, :]
    return idxs, vec(weights)
end

function local_cubic_residual_variance(t::AbstractVector, x::AbstractVector, i::Int;
                                       halfwidth::Int = 4, degree::Int = 3)
    idxs = collect(local_poly_window(length(t), i; halfwidth = halfwidth, degree = degree))
    z = t[idxs] .- t[i]
    A = hcat([z .^ p for p in 0:degree]...)
    coeffs = A \ x[idxs]
    residuals = A * coeffs - x[idxs]
    return (length(idxs) / max(length(idxs) - (degree + 1), 1)) * mean(abs2, residuals)
end

function derivative_noise_diagnostics(clean_on_observed_traj::Trajectory, observed_traj::Trajectory,
                                      estimated_dX::Matrix{Float64}, true_rhs_clean::Matrix{Float64},
                                      sigma::Float64, eq::Int, true_stage_residual::Float64)
    n = length(observed_traj.t)
    true_pred = zeros(Float64, n)
    estimated_pred = zeros(Float64, n)
    for i in 1:n
        idxs, weights = derivative_weights(observed_traj.t, i)
        true_pred[i] = sigma^2 * sum((weights .^ 2) .* (clean_on_observed_traj.x[idxs, eq] .^ 2))
        sigmahat2 = local_cubic_residual_variance(observed_traj.t, view(observed_traj.x, :, eq), i)
        estimated_pred[i] = sigmahat2 * sum(weights .^ 2)
    end
    measured_error = mean(abs2, estimated_dX[:, eq] .- true_rhs_clean[:, eq])
    return (
        f4_true_sigma_prediction = mean(true_pred),
        f4_estimated_sigma_prediction = mean(estimated_pred),
        f4_measured_derivative_error = measured_error,
        f4_true_stage_residual = true_stage_residual,
        f4_true_pred_to_measured_deriv = measured_error > 0 ? mean(true_pred) / measured_error : NaN,
        f4_est_pred_to_measured_deriv = measured_error > 0 ? mean(estimated_pred) / measured_error : NaN,
        f4_true_pred_to_true_stage_residual = true_stage_residual > 0 ? mean(true_pred) / true_stage_residual : NaN,
        f4_est_pred_to_true_stage_residual = true_stage_residual > 0 ? mean(estimated_pred) / true_stage_residual : NaN,
    )
end

function serializable_split_decisions(decisions)
    return [
        (
            kind = String(decision.kind),
            cap = decision.cap === nothing ? nothing : Int(decision.cap),
            stage = Int(decision.stage),
        )
        for decision in decisions
    ]
end

function json_get(record, key::Symbol, default = nothing)
    haskey(record, key) && return getproperty(record, key)
    text_key = String(key)
    haskey(record, text_key) && return record[text_key]
    return default
end

function normalize_caps(value, dim::Int)
    value === nothing && return Union{Nothing,Int}[nothing for _ in 1:dim]
    return Union{Nothing,Int}[item === nothing ? nothing : Int(item) for item in value]
end

function load_reference_clean_caps(path::String)
    caps = Dict{Tuple{Int,Int}, Vector{Union{Nothing,Int}}}()
    isfile(path) || error("Missing C-1 reference history at $(path)")
    open(path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            record = JSON3.read(line)
            json_get(record, :error) === nothing || continue
            String(json_get(record, :condition, "")) == "capped" || continue
            Int(json_get(record, :seed, -1)) == 42 || continue
            Bool(json_get(record, :stage_cap_policy_active, false)) || continue
            system_id = Int(json_get(record, :system_id))
            ic_set = Int(json_get(record, :initial_condition_set))
            dim = Int(json_get(record, :system_dim, json_get(record, :T, 0))) # overwritten below when caps exist
            raw_caps = json_get(record, :stage_caps)
            raw_caps === nothing && continue
            dim = length(raw_caps)
            caps[(system_id, ic_set)] = normalize_caps(raw_caps, dim)
        end
    end
    return caps
end

function maybe_reference_caps(reference_map, system_id::Int, ic_set::Int, dim::Int)
    key = (system_id, ic_set)
    haskey(reference_map, key) || error("Missing clean C-1 reference caps for system $(system_id), IC$(ic_set), seed 42")
    caps = reference_map[key]
    length(caps) == dim || error("Reference cap length mismatch for system $(system_id), IC$(ic_set)")
    return caps
end

function realization_values(sigma::Float64, rho::Float64)
    sigma == 0.0 && rho == 0.0 && return [CLEAN_REALIZATION]
    return NONCLEAN_REALIZATIONS
end

function write_csv(path::String, rows)
    headers = [
        "system_id", "system_name", "dimension", "equation_index", "initial_condition_set",
        "sigma", "rho", "realization", "n_observed_points", "cap", "clean_cap",
        "reference_clean_cap", "cap_change_class", "required_stage", "truncates_true_terms",
        "rebuild_cap_matches_estimate", "clean_reference_matches_c1",
        "residual_stage_1", "residual_stage_2", "residual_stage_3", "residual_stage_4", "residual_stage_5",
        "floor_stage_1", "floor_stage_2", "floor_stage_3", "floor_stage_4", "floor_stage_5",
        "usable_splits_stage_1", "usable_splits_stage_2", "usable_splits_stage_3", "usable_splits_stage_4", "usable_splits_stage_5",
        "split_decisions_json",
        "f4_true_sigma_prediction", "f4_estimated_sigma_prediction",
        "f4_measured_derivative_error", "f4_true_stage_residual",
        "f4_true_pred_to_measured_deriv", "f4_est_pred_to_measured_deriv",
        "f4_true_pred_to_true_stage_residual", "f4_est_pred_to_true_stage_residual",
    ]
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(headers, ","))
        for row in rows
            println(io, join([csv_escape(getfield(row, Symbol(header))) for header in headers], ","))
        end
    end
end

function diagnostic_rows()
    systems = selected_exact_systems()
    reference_map = load_reference_clean_caps(REFERENCE_HISTORY)
    policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...)
    rows = NamedTuple[]

    for system in systems
        system_id = Int(system[:system_id])
        dim = Int(system[:dim])
        basis = phase_c_basis(dim)
        required_stages = equation_required_stages(basis, system[:expected_support])
        for ic_set in PHASE_C_IC_SETS
            clean_traj = build_trajectory(phase_c_system(system_id), ic_set)
            clean_caps = estimate_stage_caps(clean_traj, basis; policy = policy)
            reference_caps = maybe_reference_caps(reference_map, system_id, ic_set, dim)
            reference_matches = clean_caps == reference_caps
            reference_matches || error("Clean cap mismatch against C-1 record for system $(system_id), IC$(ic_set): computed=$(clean_caps), reference=$(reference_caps)")

            for sigma in SIGMAS, rho in RHOS, realization in realization_values(sigma, rho)
                observed_traj = apply_phase_c_data_condition(clean_traj, system_id, ic_set, sigma, rho, realization)
                clean_on_observed_traj = trajectory_on_times(clean_traj, observed_traj.t)
                estimated_caps = estimate_stage_caps(observed_traj, basis; policy = policy)
                diagnostics = cap_diagnostics(observed_traj, basis, policy)
                rebuilt_caps = [diag.cap for diag in diagnostics]
                rebuilt_caps == estimated_caps || error(
                    "Rebuilt cap mismatch for system $(system_id), IC$(ic_set), sigma=$(sigma), rho=$(rho), realization=$(realization): estimate=$(estimated_caps), rebuilt=$(rebuilt_caps)"
                )
                dX = EvoODE._cap_estimate_derivatives(observed_traj, policy.estimator)
                true_rhs_clean = true_rhs_matrix(system, clean_on_observed_traj)

                for eq in 1:dim
                    diag = diagnostics[eq]
                    true_stage = required_stages[eq]
                    true_stage_residual = diag.residuals_median[true_stage]
                    f4 = derivative_noise_diagnostics(clean_on_observed_traj, observed_traj, dX, true_rhs_clean, Float64(sigma), eq, true_stage_residual)
                    push!(
                        rows,
                        (
                            system_id = system_id,
                            system_name = String(system[:system_name]),
                            dimension = dim,
                            equation_index = eq,
                            initial_condition_set = ic_set,
                            sigma = Float64(sigma),
                            rho = Float64(rho),
                            realization = realization,
                            n_observed_points = length(observed_traj.t),
                            cap = format_cap(estimated_caps[eq]),
                            clean_cap = format_cap(clean_caps[eq]),
                            reference_clean_cap = format_cap(reference_caps[eq]),
                            cap_change_class = classify_cap_change(estimated_caps[eq], clean_caps[eq]),
                            required_stage = true_stage,
                            truncates_true_terms = cap_truncates_truth(estimated_caps[eq], true_stage),
                            rebuild_cap_matches_estimate = rebuilt_caps[eq] === estimated_caps[eq],
                            clean_reference_matches_c1 = reference_matches,
                            residual_stage_1 = diag.residuals_median[1],
                            residual_stage_2 = diag.residuals_median[2],
                            residual_stage_3 = diag.residuals_median[3],
                            residual_stage_4 = diag.residuals_median[4],
                            residual_stage_5 = diag.residuals_median[5],
                            floor_stage_1 = diag.floors_median[1],
                            floor_stage_2 = diag.floors_median[2],
                            floor_stage_3 = diag.floors_median[3],
                            floor_stage_4 = diag.floors_median[4],
                            floor_stage_5 = diag.floors_median[5],
                            usable_splits_stage_1 = diag.usable_split_counts[1],
                            usable_splits_stage_2 = diag.usable_split_counts[2],
                            usable_splits_stage_3 = diag.usable_split_counts[3],
                            usable_splits_stage_4 = diag.usable_split_counts[4],
                            usable_splits_stage_5 = diag.usable_split_counts[5],
                            split_decisions_json = JSON3.write(serializable_split_decisions(diag.split_decisions)),
                            f4_true_sigma_prediction = f4.f4_true_sigma_prediction,
                            f4_estimated_sigma_prediction = f4.f4_estimated_sigma_prediction,
                            f4_measured_derivative_error = f4.f4_measured_derivative_error,
                            f4_true_stage_residual = f4.f4_true_stage_residual,
                            f4_true_pred_to_measured_deriv = f4.f4_true_pred_to_measured_deriv,
                            f4_est_pred_to_measured_deriv = f4.f4_est_pred_to_measured_deriv,
                            f4_true_pred_to_true_stage_residual = f4.f4_true_pred_to_true_stage_residual,
                            f4_est_pred_to_true_stage_residual = f4.f4_est_pred_to_true_stage_residual,
                        ),
                    )
                end
            end
        end
    end
    return rows, systems
end

function json_metadata_value(value)
    value isa Symbol && return String(value)
    return value
end

function write_metadata(path::String, rows, systems)
    metadata = Dict(
        "script" => SCRIPT_SLUG,
        "timestamp" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "detail_csv" => DETAIL_CSV,
        "reference_history" => REFERENCE_HISTORY,
        "systems" => [Int(system[:system_id]) for system in systems],
        "system_count" => length(systems),
        "row_count" => length(rows),
        "sigmas" => SIGMAS,
        "rhos" => RHOS,
        "nonclean_realizations" => NONCLEAN_REALIZATIONS,
        "clean_realization" => CLEAN_REALIZATION,
        "policy" => Dict(String(key) => json_metadata_value(getfield(LOOKAHEAD_CAP_POLICY, key)) for key in keys(LOOKAHEAD_CAP_POLICY)),
    )
    mkpath(dirname(path))
    open(path, "w") do io
        JSON3.write(io, metadata)
        write(io, '\n')
    end
end

function main()
    rows, systems = diagnostic_rows()
    write_csv(DETAIL_CSV, rows)
    write_metadata(METADATA_JSON, rows, systems)
    println("Wrote $(DETAIL_CSV)")
    println("Wrote $(METADATA_JSON)")
    println("Rows: $(length(rows))")
    println("Systems: $(length(systems))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
