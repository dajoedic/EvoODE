include(joinpath(@__DIR__, "stage_potential_probe.jl"))

using Statistics

"""
WP-L2 derivative-estimator diagnostic.

Pre-registered predictions:
1. With an adequate estimator, System 3 keeps its correct verdict: stop at stage 2.
2. System 11 shows a large, split-stable holdout gain at stage 4.
3. System 26 equation 2 shows its stage-3 holdout residual dropping toward the analytic
   floor, with no relevant gain at stages 4 and 5.
4. The derivative residual floor r_k on System 26 is of the same order as the observed
   r_k plateau, meaning v3 promotion can be contaminated by derivative error.

All estimator variants live in this study script. Nothing under src/ is modified.
"""

const L2_SCRIPT_SLUG = "derivative_estimator_probe"
const L2_OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "lookahead", L2_SCRIPT_SLUG), ARGS)
const ESTIMATOR_ERROR_CSV = joinpath(L2_OUTPUT_DIR, "estimator_errors.csv")
const L2_STAGE_CSV = joinpath(L2_OUTPUT_DIR, "stage_capacity_by_estimator.csv")
const RK_JSON = joinpath(L2_OUTPUT_DIR, "rk_contamination.json")
const L2_SUMMARY_JSON = joinpath(L2_OUTPUT_DIR, "summary.json")
const L2_REPORT_MD = joinpath(L2_OUTPUT_DIR, "report.md")

const ESTIMATORS = ("central", "fd4", "local_poly")
const WEIGHTING_MODES = ("unweighted", "richardson_wls")
const L2_SPLIT_LABELS = ("A", "B", "C", "D")
const SPLIT_COND_CAP = 1e10
const SPLIT_EXCITATION_FLOOR = 1e-10

function uniform_step(t::AbstractVector)
    length(t) < 2 && return 1.0
    return mean(diff(t))
end

function finite_difference4(traj::Trajectory)
    t = traj.t
    X = traj.x
    n, dim = size(X)
    dX = zeros(Float64, n, dim)
    n < 5 && return EvoODE.estimate_derivatives(traj)
    h = uniform_step(t)
    for k in 1:dim
        dX[1, k] = (X[2, k] - X[1, k]) / (t[2] - t[1])
        dX[2, k] = (X[3, k] - X[1, k]) / (t[3] - t[1])
        for i in 3:(n - 2)
            dX[i, k] = (-X[i + 2, k] + 8X[i + 1, k] - 8X[i - 1, k] + X[i - 2, k]) / (12h)
        end
        dX[n - 1, k] = (X[n, k] - X[n - 2, k]) / (t[n] - t[n - 2])
        dX[n, k] = (X[n, k] - X[n - 1, k]) / (t[n] - t[n - 1])
    end
    return dX
end

function local_poly_derivatives(traj::Trajectory; halfwidth::Int = 4, degree::Int = 3)
    t = traj.t
    X = traj.x
    n, dim = size(X)
    dX = zeros(Float64, n, dim)
    for i in 1:n
        lo = max(1, i - halfwidth)
        hi = min(n, i + halfwidth)
        if hi - lo + 1 < degree + 1
            lo = max(1, min(lo, n - degree))
            hi = min(n, max(hi, degree + 1))
        end
        z = t[lo:hi] .- t[i]
        A = hcat([z .^ p for p in 0:degree]...)
        for k in 1:dim
            coeffs = A \ X[lo:hi, k]
            dX[i, k] = coeffs[2]
        end
    end
    return dX
end

function estimate_with(name::AbstractString, traj::Trajectory)
    name == "central" && return EvoODE.estimate_derivatives(traj)
    name == "fd4" && return finite_difference4(traj)
    name == "local_poly" && return local_poly_derivatives(traj)
    error("unknown estimator $(name)")
end

function coarsened_trajectory(traj::Trajectory)
    idxs = collect(1:2:length(traj.t))
    return Trajectory(traj.t[idxs], traj.x[idxs, :])
end

function interpolate_to_full(t_full, t_coarse, values_coarse)
    n = length(t_full)
    dim = size(values_coarse, 2)
    out = zeros(Float64, n, dim)
    for k in 1:dim
        j = 1
        for i in 1:n
            while j < length(t_coarse) && t_coarse[j + 1] < t_full[i]
                j += 1
            end
            if t_full[i] <= t_coarse[1]
                out[i, k] = values_coarse[1, k]
            elseif t_full[i] >= t_coarse[end]
                out[i, k] = values_coarse[end, k]
            else
                a = (t_full[i] - t_coarse[j]) / (t_coarse[j + 1] - t_coarse[j])
                out[i, k] = (1 - a) * values_coarse[j, k] + a * values_coarse[j + 1, k]
            end
        end
    end
    return out
end

function richardson_error_estimate(estimator::AbstractString, traj::Trajectory)
    full = estimate_with(estimator, traj)
    coarse_traj = coarsened_trajectory(traj)
    coarse = estimate_with(estimator, coarse_traj)
    coarse_full = interpolate_to_full(traj.t, coarse_traj.t, coarse)
    return abs.(full .- coarse_full)
end

function block_indices(n::Int)
    splits = make_l2_splits(n)
    blocks = Dict{String,Vector{Int}}(
        "all" => collect(1:n),
        "first30" => splits["B"].holdout,
        "middle30" => splits["C"].holdout,
        "last30" => splits["A"].holdout,
        "fitA" => splits["A"].fit,
        "fitB" => splits["B"].fit,
        "fitC" => splits["C"].fit,
    )
    return blocks
end

function make_l2_splits(n::Int)
    splits = copy(make_splits(n))
    q1 = floor(Int, 0.25 * n)
    q2 = floor(Int, 0.50 * n)
    q3 = floor(Int, 0.75 * n)
    splits["D"] = (
        fit = vcat(collect(1:q1), collect((q2 + 1):q3)),
        holdout = vcat(collect((q1 + 1):q2), collect((q3 + 1):n)),
    )
    return splits
end

function corr_safe(x::AbstractVector, y::AbstractVector)
    length(x) < 2 && return NaN
    std(x) == 0.0 && return NaN
    std(y) == 0.0 && return NaN
    return cor(x, y)
end

function estimator_error_rows(sys::ProbeSystem, traj::Trajectory, analytic_dX::Matrix{Float64})
    rows = Dict{String,Any}[]
    blocks = block_indices(length(traj.t))
    for estimator in ESTIMATORS
        dX = estimate_with(estimator, traj)
        rich = richardson_error_estimate(estimator, traj)
        for eq in 1:sys.dim
            true_err = abs.(dX[:, eq] .- analytic_dX[:, eq])
            rich_eq = rich[:, eq]
            corr_value = corr_safe(true_err, rich_eq)
            upper_frac = mean(rich_eq .>= true_err)
            for (block, idxs) in sort(collect(blocks), by = x -> x[1])
                rms_error = sqrt(mean(abs2, true_err[idxs]))
                rms_rich = sqrt(mean(abs2, rich_eq[idxs]))
                max_error = maximum(true_err[idxs])
                ratio = rms_error == 0.0 ? Inf : rms_rich / rms_error
                push!(rows, Dict{String,Any}(
                    "system_id" => sys.id,
                    "system_name" => sys.name,
                    "equation" => eq,
                    "estimator" => estimator,
                    "block" => block,
                    "rms_error" => rms_error,
                    "max_error" => max_error,
                    "richardson_rms" => rms_rich,
                    "richardson_to_true_rms_ratio" => ratio,
                    "pointwise_correlation" => corr_value,
                    "richardson_upper_bound_fraction" => upper_frac,
                ))
            end
        end
    end
    return rows
end

function weighted_ls_fit_eval(Phi::AbstractMatrix, y::AbstractVector, fit_idxs::Vector{Int},
                              holdout_idxs::Vector{Int}, weights::AbstractVector)
    sqrtw = sqrt.(max.(weights[fit_idxs], 0.0))
    Phi_fit = Matrix(Phi[fit_idxs, :])
    y_fit = Vector(y[fit_idxs])
    Phi_hold = Matrix(Phi[holdout_idxs, :])
    y_hold = Vector(y[holdout_idxs])
    ncols = size(Phi_fit, 2)
    try
        coeffs = ncols == 0 ? Float64[] : (Phi_fit .* sqrtw) \ (y_fit .* sqrtw)
        fit_resid = ncols == 0 ? -y_fit : Phi_fit * coeffs - y_fit
        hold_resid = ncols == 0 ? -y_hold : Phi_hold * coeffs - y_hold
        valid = all(isfinite, coeffs) && all(isfinite, fit_resid) && all(isfinite, hold_resid)
        return (
            coeffs = coeffs,
            train_residual = mean(abs2, fit_resid),
            holdout_residual = mean(abs2, hold_resid),
            normalised_holdout_residual = normalised_mse(hold_resid, y_hold),
            rank = ncols == 0 ? 0 : rank(Phi_fit),
            condition_number = ncols == 0 ? Inf : cond(Phi_fit),
            valid = valid,
            reason = valid ? "" : "nonfinite_ls_result",
        )
    catch err
        return (
            coeffs = zeros(ncols),
            train_residual = Inf,
            holdout_residual = Inf,
            normalised_holdout_residual = Inf,
            rank = 0,
            condition_number = Inf,
            valid = false,
            reason = "wls_failed:$(typeof(err))",
        )
    end
end

function weights_from_richardson(rich_eq::AbstractVector)
    scale = median(rich_eq .^ 2) + eps(Float64)
    return 1.0 ./ (rich_eq .^ 2 .+ scale)
end

function split_validity(Phi::AbstractMatrix, y::AbstractVector, fit_idxs::Vector{Int})
    Phi_fit = Matrix(Phi[fit_idxs, :])
    cond_value = size(Phi_fit, 2) == 0 ? Inf : cond(Phi_fit)
    excitation = mean(abs2, y[fit_idxs] .- mean(y[fit_idxs]))
    valid = isfinite(cond_value) && cond_value <= SPLIT_COND_CAP && excitation >= SPLIT_EXCITATION_FLOOR
    reasons = String[]
    isfinite(cond_value) || push!(reasons, "nonfinite_condition")
    cond_value <= SPLIT_COND_CAP || push!(reasons, "condition_gt_$(SPLIT_COND_CAP)")
    excitation >= SPLIT_EXCITATION_FLOOR || push!(reasons, "low_excitation")
    return valid, join(reasons, ";"), cond_value, excitation
end

function l2_stage_rows_for_equation(sys::ProbeSystem, basis::StagedPolynomialBasis, traj::Trajectory,
                                    dX::Matrix{Float64}, rich::Matrix{Float64},
                                    estimator::String, weighting_mode::String,
                                    eq::Int, expected_eq_stage::Int)
    splits = make_l2_splits(length(traj.t))
    y = dX[:, eq]
    weights = weighting_mode == "richardson_wls" ? weights_from_richardson(rich[:, eq]) : ones(length(y))
    rows = Dict{String,Any}[]
    metrics = Dict{Tuple{String,Int},Any}()
    split_meta = Dict{Tuple{String,Int},Any}()
    new_counts = [length(basis.term_groups[s]) for s in 1:MAX_STAGE]

    for split_label in sort(collect(keys(splits)))
        split = splits[split_label]
        for stage in 1:MAX_STAGE
            idxs = cumulative_stage_idxs(basis, stage)
            Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
            valid_split, split_reason, split_cond, excitation = split_validity(Phi, y, split.fit)
            result = weighting_mode == "richardson_wls" ?
                     weighted_ls_fit_eval(Phi, y, split.fit, split.holdout, weights) :
                     ls_fit_eval(Phi, y, split.fit, split.holdout)
            metrics[(split_label, stage)] = result
            split_meta[(split_label, stage)] = (valid = valid_split, reason = split_reason,
                                                condition_number = split_cond, excitation = excitation)
        end
        for stage in 1:MAX_STAGE
            result = metrics[(split_label, stage)]
            idxs = cumulative_stage_idxs(basis, stage)
            next_stage = findfirst(s -> s > stage && new_counts[s] > 0, 1:MAX_STAGE)
            gain_abs = NaN
            gain_rel = NaN
            verdict = "invalid_or_inconclusive"
            valid_for_verdict = result.valid && split_meta[(split_label, stage)].valid
            if valid_for_verdict && next_stage !== nothing &&
               metrics[(split_label, next_stage)].valid && split_meta[(split_label, next_stage)].valid
                next_residual = metrics[(split_label, next_stage)].holdout_residual
                gain_abs = result.holdout_residual - next_residual
                gain_rel = result.holdout_residual == 0.0 ? Inf : gain_abs / result.holdout_residual
                verdict = gain_abs > 0.0 ? "potential_detected" : "no_potential"
            elseif valid_for_verdict && next_stage === nothing
                verdict = "no_potential"
            end
            hold = split.holdout
            push!(rows, Dict{String,Any}(
                "row_type" => "stage_capacity",
                "system_id" => sys.id,
                "system_name" => sys.name,
                "dim" => sys.dim,
                "representability" => string(sys.representability),
                "equation" => eq,
                "expected_eq_stage" => expected_eq_stage,
                "tested_stage" => stage,
                "new_terms" => new_counts[stage],
                "empty_stage" => new_counts[stage] == 0,
                "split" => split_label,
                "estimator" => estimator,
                "weighting" => weighting_mode,
                "train_residual" => result.train_residual,
                "holdout_residual" => result.holdout_residual,
                "normalised_holdout_residual" => result.normalised_holdout_residual,
                "absolute_gain" => gain_abs,
                "relative_gain" => gain_rel,
                "rank" => result.rank,
                "condition_number" => result.condition_number,
                "valid" => result.valid,
                "split_valid" => split_meta[(split_label, stage)].valid,
                "split_invalid_reason" => split_meta[(split_label, stage)].reason,
                "fit_excitation" => split_meta[(split_label, stage)].excitation,
                "noise_floor_richardson_holdout" => mean(abs2, rich[hold, eq]),
                "invalid_reason" => result.reason,
                "fitted_coefficients" => join(result.coeffs, "|"),
                "terms" => join(term_names(basis, idxs), "|"),
                "verdict" => verdict,
            ))
        end
    end
    return rows
end

function l2_grid_rows(stage_rows)
    rows = Dict{String,Any}[]
    grouped = Dict{Tuple{Int,String,String,Int,String,String},Vector{Dict{String,Any}}}()
    for row in stage_rows
        row["row_type"] == "stage_capacity" || continue
        key = (row["system_id"], row["system_name"], row["representability"], row["equation"],
               row["estimator"], row["weighting"])
        push!(get!(grouped, key, Dict{String,Any}[]), row)
    end
    for (key, group) in grouped
        sid, sname, repr, eq, estimator, weighting = key
        expected = group[1]["expected_eq_stage"]
        for tau_rel in TAU_REL_GRID, tau_abs in TAU_ABS_GRID, split in L2_SPLIT_LABELS
            by_stage = Dict(row["tested_stage"] => row for row in group if row["split"] == split)
            max_stage = 1
            excluded = false
            for stage in 1:(MAX_STAGE - 1)
                haskey(by_stage, stage) || continue
                current = by_stage[stage]
                current["empty_stage"] && continue
                next_stage = findfirst(s -> s > stage && haskey(by_stage, s) && !by_stage[s]["empty_stage"], 1:MAX_STAGE)
                next_stage === nothing && continue
                future = by_stage[next_stage]
                if !current["split_valid"] || !future["split_valid"] || !current["valid"] || !future["valid"]
                    excluded = true
                    continue
                end
                delta = current["holdout_residual"] - future["holdout_residual"]
                rel = current["holdout_residual"] == 0.0 ? Inf : delta / current["holdout_residual"]
                if delta > tau_abs && rel > tau_rel
                    max_stage = max(max_stage, next_stage)
                end
            end
            push!(rows, Dict{String,Any}(
                "system_id" => sid,
                "system_name" => sname,
                "representability" => repr,
                "equation" => eq,
                "expected_eq_stage" => expected,
                "split" => split,
                "estimator" => estimator,
                "weighting" => weighting,
                "tau_rel" => tau_rel,
                "tau_abs" => tau_abs,
                "max_useful_stage" => max_stage,
                "stage_error" => max_stage - expected,
                "excluded" => excluded,
            ))
        end
    end
    return rows
end

function rk_residual(Phi::AbstractMatrix, coeffs::AbstractVector, target::AbstractVector)
    return mean(abs2, Phi * coeffs - target)
end

function coeff_vector(names::Vector{String}, coeffs_by_name::Dict{String,Float64})
    return [coeffs_by_name[name] for name in names]
end

function system26_true_coeffs(eq::Int)
    eq == 1 && return Dict("u1" => 3.0, "u1^2" => -1.0, "u1*u2" => -2.0)
    eq == 2 && return Dict("u2" => 2.0, "u1*u2" => -1.0, "u2^2" => -1.0)
    error("system 26 has no equation $(eq)")
end

function rk_contamination_records(best_estimator::String)
    sys = only([s for s in PROBE_SYSTEMS if s.id == 26])
    traj = generate_trajectory(sys)
    basis = default_staged_polynomial_basis(sys.dim)
    records = Any[]
    for estimator in ("central", best_estimator)
        dX = estimate_with(estimator, traj)
        for eq in 1:sys.dim
            true_names = sys.expected_terms[eq]
            true_idxs = [basis_name_to_idx(basis)[name] for name in true_names]
            Phi_true = EvoODE.build_design_matrix(basis, true_idxs, traj.x, traj.t)
            true_coeffs = coeff_vector(true_names, system26_true_coeffs(eq))
            push!(records, Dict(
                "estimator" => estimator,
                "equation" => eq,
                "structure" => "true_support_true_params_floor",
                "stage" => 3,
                "terms" => true_names,
                "r_k" => rk_residual(Phi_true, true_coeffs, dX[:, eq]),
            ))
            ls = ls_fit_eval(Phi_true, dX[:, eq], collect(1:length(traj.t)), collect(1:length(traj.t)))
            push!(records, Dict(
                "estimator" => estimator,
                "equation" => eq,
                "structure" => "true_support_ls",
                "stage" => 3,
                "terms" => true_names,
                "r_k" => ls.holdout_residual,
            ))
            if eq == 2
                # WP-T2 reported du2 support {u1, u1^2}; hardcoded for contamination check.
                bad_names = ["u1", "u1^2"]
                bad_idxs = [basis_name_to_idx(basis)[name] for name in bad_names]
                Phi_bad = EvoODE.build_design_matrix(basis, bad_idxs, traj.x, traj.t)
                bad_ls = ls_fit_eval(Phi_bad, dX[:, eq], collect(1:length(traj.t)), collect(1:length(traj.t)))
                push!(records, Dict(
                    "estimator" => estimator,
                    "equation" => eq,
                    "structure" => "wp_t2_discovered_support_ls",
                    "stage" => 3,
                    "terms" => bad_names,
                    "r_k" => bad_ls.holdout_residual,
                ))
            end
            for stage in 1:MAX_STAGE
                idxs = cumulative_stage_idxs(basis, stage)
                Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
                fit = ls_fit_eval(Phi, dX[:, eq], collect(1:length(traj.t)), collect(1:length(traj.t)))
                push!(records, Dict(
                    "estimator" => estimator,
                    "equation" => eq,
                    "structure" => "full_stage_ls",
                    "stage" => stage,
                    "terms" => term_names(basis, idxs),
                    "r_k" => fit.holdout_residual,
                ))
            end
        end
    end
    return records
end

function choose_best_estimator(error_rows)
    candidates = Dict{String,Float64}()
    for estimator in ESTIMATORS
        vals = [row["rms_error"] for row in error_rows if row["estimator"] == estimator && row["block"] == "all"]
        candidates[estimator] = median(vals)
    end
    return sort(collect(candidates), by = x -> x[2])[1][1]
end

function summarise_l2_grid(grid_rows, estimator::String, weighting::String)
    filtered = [r for r in grid_rows if r["estimator"] == estimator && r["weighting"] == weighting &&
                r["representability"] == "exact" && !r["excluded"]]
    grouped = Dict{Tuple{Float64,Float64,Int,Int},Vector{Int}}()
    meta = Dict{Tuple{Float64,Float64,Int,Int},Any}()
    for row in filtered
        key = (row["tau_rel"], row["tau_abs"], row["system_id"], row["equation"])
        push!(get!(grouped, key, Int[]), row["max_useful_stage"])
        meta[key] = row
    end
    by_grid = Dict{Tuple{Float64,Float64},Dict{String,Any}}()
    for (key, stages) in grouped
        tau_rel, tau_abs, sid, eq = key
        gkey = (tau_rel, tau_abs)
        if !haskey(by_grid, gkey)
            by_grid[gkey] = Dict("under" => Any[], "exact" => Any[], "over" => Any[])
        end
        predicted = median_stage(stages)
        expected = meta[key]["expected_eq_stage"]
        bucket = predicted < expected ? "under" : predicted > expected ? "over" : "exact"
        push!(by_grid[gkey][bucket], Dict("system_id" => sid, "equation" => eq,
                                          "expected" => expected, "predicted" => predicted))
    end
    records = Any[]
    for ((tau_rel, tau_abs), buckets) in sort(collect(by_grid), by = x -> (x[1][1], x[1][2]))
        push!(records, Dict("tau_rel" => tau_rel, "tau_abs" => tau_abs,
                            "under" => length(buckets["under"]),
                            "exact" => length(buckets["exact"]),
                            "over" => length(buckets["over"]),
                            "under_equations" => buckets["under"],
                            "over_equations" => buckets["over"]))
    end
    return records
end

function split_exclusions(stage_rows)
    grouped = Dict{Tuple{String,String,String},Int}()
    for row in stage_rows
        row["row_type"] == "stage_capacity" || continue
        row["split_valid"] && continue
        key = (row["split"], row["estimator"], row["split_invalid_reason"])
        grouped[key] = get(grouped, key, 0) + 1
    end
    return [Dict("split" => k[1], "estimator" => k[2], "reason" => k[3], "count" => v)
            for (k, v) in sort(collect(grouped), by = x -> (x[1][1], x[1][2], x[1][3]))]
end

function write_l2_report(summary)
    best_grid = isempty(summary["best_grid_summary"]) ? nothing :
                sort(summary["best_grid_summary"], by = g -> (g["under"] + g["over"], -g["exact"]))[1]
    open(L2_REPORT_MD, "w") do io
        println(io, "# Derivative Estimator Probe")
        println(io)
        println(io, "Best estimator by median all-block RMS derivative error: $(summary["best_estimator"]).")
        println(io, "Median all-block RMS errors by estimator: $(summary["estimator_median_rms"]).")
        println(io)
        println(io, "## Predictions")
        for item in summary["predictions"]
            println(io, "- $(item)")
        end
        println(io)
        println(io, "## Calibration")
        if best_grid === nothing
            println(io, "No valid exact-system grid rows after split exclusion.")
        else
            println(io, "Best grid for $(summary["best_estimator"]) + richardson_wls: tau_rel=$(best_grid["tau_rel"]), tau_abs=$(best_grid["tau_abs"]).")
            println(io, "Confusion: under=$(best_grid["under"]), exact=$(best_grid["exact"]), over=$(best_grid["over"]).")
            println(io, "Under-shoot equations: $(format_equation_list(best_grid["under_equations"])).")
            println(io, "Over-shoot equations: $(format_equation_list(best_grid["over_equations"])).")
        end
        println(io)
        println(io, "## Split Exclusions")
        println(io, "$(summary["split_exclusions"])")
        println(io)
        println(io, "## r_k Contamination")
        println(io, "$(summary["rk_verdict"])")
        println(io, "System 26 r_k records are in $(RK_JSON).")
    end
end

function prediction_readout(stage_rows, best_estimator)
    rows = [r for r in stage_rows if r["estimator"] == best_estimator && r["weighting"] == "richardson_wls"]
    s3 = [r for r in rows if r["system_id"] == 3 && r["tested_stage"] == 2 && r["split_valid"]]
    s11 = [r for r in rows if r["system_id"] == 11 && r["tested_stage"] == 3 && r["split_valid"]]
    s26 = [r for r in rows if r["system_id"] == 26 && r["equation"] == 2 && r["tested_stage"] == 3 && r["split_valid"]]
    return [
        "System 3 stage-2 valid holdout residuals: $([r["holdout_residual"] for r in s3]).",
        "System 11 stage-3 to stage-4 gains on valid splits: $([r["absolute_gain"] for r in s11]).",
        "System 26 equation 2 stage-3 to next-stage gains on valid splits: $([r["absolute_gain"] for r in s26]).",
    ]
end

function rk_verdict(records)
    central_floor = [r["r_k"] for r in records if r["estimator"] == "central" && r["structure"] == "true_support_true_params_floor"]
    best_floor = [r["r_k"] for r in records if r["estimator"] != "central" && r["structure"] == "true_support_true_params_floor"]
    central_stage3 = [r["r_k"] for r in records if r["estimator"] == "central" && r["structure"] == "full_stage_ls" && r["stage"] == 3]
    return "Central true-parameter floor=$(central_floor), central full-stage-3 r_k=$(central_stage3), best-estimator true-parameter floor=$(best_floor). If floor and plateau-scale r_k are close, promotion is derivative-error contaminated."
end

const ERROR_COLUMNS = [
    "system_id", "system_name", "equation", "estimator", "block", "rms_error",
    "max_error", "richardson_rms", "richardson_to_true_rms_ratio",
    "pointwise_correlation", "richardson_upper_bound_fraction",
]

const L2_STAGE_COLUMNS = [
    "row_type", "system_id", "system_name", "dim", "representability", "equation",
    "expected_eq_stage", "tested_stage", "new_terms", "empty_stage", "split",
    "estimator", "weighting", "train_residual", "holdout_residual",
    "normalised_holdout_residual", "absolute_gain", "relative_gain", "rank",
    "condition_number", "valid", "split_valid", "split_invalid_reason",
    "fit_excitation", "noise_floor_richardson_holdout", "invalid_reason",
    "fitted_coefficients", "terms", "verdict",
]

function main_l2()
    mkpath(L2_OUTPUT_DIR)
    for path in (ESTIMATOR_ERROR_CSV, L2_STAGE_CSV)
        isfile(path) && rm(path)
    end
    error_rows = Dict{String,Any}[]
    stage_rows = Dict{String,Any}[]
    started = time()
    for sys in PROBE_SYSTEMS
        println(@sprintf("L2 SYSTEM id=%d name=%s dim=%d", sys.id, sys.name, sys.dim))
        traj = generate_trajectory(sys)
        analytic_dX = analytic_derivatives(sys, traj)
        basis = default_staged_polynomial_basis(sys.dim)
        expected_eq_stages = expected_stage_by_equation(sys, basis)

        sys_error_rows = estimator_error_rows(sys, traj, analytic_dX)
        append_csv_rows(ESTIMATOR_ERROR_CSV, sys_error_rows, ERROR_COLUMNS)
        append!(error_rows, sys_error_rows)

        sys_stage_rows = Dict{String,Any}[]
        for estimator in ESTIMATORS
            dX = estimate_with(estimator, traj)
            rich = richardson_error_estimate(estimator, traj)
            for weighting in WEIGHTING_MODES, eq in 1:sys.dim
                append!(sys_stage_rows, l2_stage_rows_for_equation(
                    sys, basis, traj, dX, rich, estimator, weighting, eq, expected_eq_stages[eq]))
            end
        end
        append_csv_rows(L2_STAGE_CSV, sys_stage_rows, L2_STAGE_COLUMNS)
        append!(stage_rows, sys_stage_rows)
        if time() - started > 20 * 60
            println("STOP: exceeded 20 minute diagnostic budget after system $(sys.id)")
            break
        end
    end

    best_estimator = choose_best_estimator(error_rows)
    grid_rows = l2_grid_rows(stage_rows)
    best_grid_summary = summarise_l2_grid(grid_rows, best_estimator, "richardson_wls")
    rk_records = rk_contamination_records(best_estimator)
    write_json(RK_JSON, rk_records)
    med = Dict(est => median([r["rms_error"] for r in error_rows if r["estimator"] == est && r["block"] == "all"])
               for est in ESTIMATORS)
    summary = Dict{String,Any}(
        "script" => L2_SCRIPT_SLUG,
        "timestamp" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "elapsed_s" => time() - started,
        "best_estimator" => best_estimator,
        "estimator_median_rms" => med,
        "best_grid_summary" => best_grid_summary,
        "split_exclusions" => split_exclusions(stage_rows),
        "predictions" => prediction_readout(stage_rows, best_estimator),
        "rk_verdict" => rk_verdict(rk_records),
        "outputs" => Dict("estimator_errors" => ESTIMATOR_ERROR_CSV,
                          "stage_capacity" => L2_STAGE_CSV,
                          "rk" => RK_JSON),
    )
    write_json(L2_SUMMARY_JSON, summary)
    write_l2_report(summary)
    println("Wrote $(ESTIMATOR_ERROR_CSV)")
    println("Wrote $(L2_STAGE_CSV)")
    println("Wrote $(RK_JSON)")
    println("Wrote $(L2_SUMMARY_JSON)")
    println("Wrote $(L2_REPORT_MD)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main_l2()
end
