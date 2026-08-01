include(joinpath(@__DIR__, "derivative_estimator_probe.jl"))

"""
WP-L3 floor-gated firing, identifiability, and sampling-limit diagnostic.

Pre-registered predictions:
1. The floor-gated rule removes all three System-54 overshoots and introduces at most
   two undershoots, both on System 54.
2. Systems 3, 11, and 26 keep their correct verdicts under the floor-gated rule.
3. On System 54, increased sampling density lowers derivative error enough for a
   stage-3 cliff to appear.
4. On System 63, rank deficiency persists at every sampling density.

This study reuses WP-L2's local polynomial estimator, Richardson floor, split machinery,
and benchmark definitions. It remains diagnostic only: no src/ changes, no search, no
BFGS, and no ODE simulation beyond generating each trajectory.
"""

const L3_SCRIPT_SLUG = "floor_gated_probe"
const L3_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "lookahead", L3_SCRIPT_SLUG)
const L3_STAGE_CSV = joinpath(L3_OUTPUT_DIR, "stage_profiles_by_rule.csv")
const IDENTIFIABILITY_CSV = joinpath(L3_OUTPUT_DIR, "identifiability.csv")
const DENSITY_CSV = joinpath(L3_OUTPUT_DIR, "density_sweep.csv")
const L3_SUMMARY_JSON = joinpath(L3_OUTPUT_DIR, "summary.json")
const L3_REPORT_MD = joinpath(L3_OUTPUT_DIR, "report.md")

const L3_ESTIMATORS = ("central", "local_poly")
const FIT_METHODS = ("ols", "ridge")
const RIDGE_ALPHA = 1e-8
const DENSITY_MULTIPLIERS = (1, 2, 4, 8)

function ridge_fit_eval(Phi::AbstractMatrix, y::AbstractVector, fit_idxs::Vector{Int},
                        holdout_idxs::Vector{Int}, weights::AbstractVector;
                        alpha::Float64 = RIDGE_ALPHA)
    sqrtw = sqrt.(max.(weights[fit_idxs], 0.0))
    A = Matrix(Phi[fit_idxs, :]) .* sqrtw
    b = Vector(y[fit_idxs]) .* sqrtw
    Ah = Matrix(Phi[holdout_idxs, :])
    yh = Vector(y[holdout_idxs])
    ncols = size(A, 2)
    try
        coeffs = ncols == 0 ? Float64[] : (A' * A + alpha * I(ncols)) \ (A' * b)
        fit_resid = ncols == 0 ? -b : Matrix(Phi[fit_idxs, :]) * coeffs - Vector(y[fit_idxs])
        hold_resid = ncols == 0 ? -yh : Ah * coeffs - yh
        valid = all(isfinite, coeffs) && all(isfinite, fit_resid) && all(isfinite, hold_resid)
        return (
            coeffs = coeffs,
            train_residual = mean(abs2, fit_resid),
            holdout_residual = mean(abs2, hold_resid),
            normalised_holdout_residual = normalised_mse(hold_resid, yh),
            rank = ncols == 0 ? 0 : rank(Matrix(Phi[fit_idxs, :])),
            condition_number = ncols == 0 ? Inf : cond(Matrix(Phi[fit_idxs, :])),
            valid = valid,
            reason = valid ? "" : "nonfinite_ridge_result",
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
            reason = "ridge_failed:$(typeof(err))",
        )
    end
end

function is_rank_deficient(Phi::AbstractMatrix; cond_cap::Float64 = SPLIT_COND_CAP)
    ncols = size(Phi, 2)
    ncols == 0 && return true, "empty_design", 0, Inf
    r = rank(Matrix(Phi))
    c = cond(Matrix(Phi))
    deficient = r < ncols || !isfinite(c) || c > cond_cap
    reason = r < ncols ? "rank_deficient" : (!isfinite(c) ? "nonfinite_condition" :
             (c > cond_cap ? "condition_gt_$(cond_cap)" : ""))
    return deficient, reason, r, c
end

function rule_counts_gain(rule::String, current_residual::Float64, next_residual::Float64,
                          floor::Float64, tau_rel::Float64, tau_abs::Float64)
    isfinite(current_residual) && isfinite(next_residual) || return false
    delta = current_residual - next_residual
    rel = current_residual == 0.0 ? Inf : delta / current_residual
    if rule == "threshold_only"
        return delta > tau_abs && rel > tau_rel
    elseif rule == "floor_gated"
        current_residual <= floor && return false
        return delta > tau_abs && rel > tau_rel && delta > floor
    end
    error("unknown rule $(rule)")
end

function l3_stage_rows_for_equation(sys::ProbeSystem, basis::StagedPolynomialBasis, traj::Trajectory,
                                    dX::Matrix{Float64}, rich::Matrix{Float64}, estimator::String,
                                    weighting_mode::String, fit_method::String,
                                    eq::Int, expected_eq_stage::Int)
    splits = make_l2_splits(length(traj.t))
    y = dX[:, eq]
    weights = weighting_mode == "richardson_wls" ? weights_from_richardson(rich[:, eq]) : ones(length(y))
    rows = Dict{String,Any}[]
    new_counts = [length(basis.term_groups[s]) for s in 1:MAX_STAGE]
    metrics = Dict{Tuple{String,Int},Any}()
    ident = Dict{Tuple{String,Int},Any}()

    for split_label in L2_SPLIT_LABELS
        split = splits[split_label]
        for stage in 1:MAX_STAGE
            idxs = cumulative_stage_idxs(basis, stage)
            Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
            deficient, ident_reason, design_rank, design_cond = is_rank_deficient(Phi[split.fit, :])
            result = if fit_method == "ridge"
                ridge_fit_eval(Phi, y, split.fit, split.holdout, weights)
            elseif weighting_mode == "richardson_wls"
                weighted_ls_fit_eval(Phi, y, split.fit, split.holdout, weights)
            else
                ls_fit_eval(Phi, y, split.fit, split.holdout)
            end
            metrics[(split_label, stage)] = result
            ident[(split_label, stage)] = (
                rank_deficient_at_tested_stage = deficient,
                reason = ident_reason,
                rank = design_rank,
                condition_number = design_cond,
            )
        end
        for stage in 1:MAX_STAGE
            current = metrics[(split_label, stage)]
            idxs = cumulative_stage_idxs(basis, stage)
            next_stage = findfirst(s -> s > stage && new_counts[s] > 0, 1:MAX_STAGE)
            floor = mean(abs2, rich[split.holdout, eq])
            for rule in ("threshold_only", "floor_gated")
                gain_abs = NaN
                gain_rel = NaN
                verdict = ident[(split_label, stage)].rank_deficient_at_tested_stage ? "rank_deficient_at_tested_stage" : "invalid_or_inconclusive"
                if current.valid && !ident[(split_label, stage)].rank_deficient_at_tested_stage
                    if next_stage === nothing
                        verdict = "no_potential"
                    else
                        future = metrics[(split_label, next_stage)]
                        future_ident = ident[(split_label, next_stage)]
                        if future.valid && !future_ident.rank_deficient_at_tested_stage
                            gain_abs = current.holdout_residual - future.holdout_residual
                            gain_rel = current.holdout_residual == 0.0 ? Inf : gain_abs / current.holdout_residual
                            verdict = rule_counts_gain(rule, current.holdout_residual,
                                                       future.holdout_residual, floor,
                                                       1e-4, 1e-8) ? "potential_detected" : "no_potential"
                        end
                    end
                end
                push!(rows, Dict{String,Any}(
                    "row_type" => "stage_profile",
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
                    "fit_method" => fit_method,
                    "rule" => rule,
                    "train_residual" => current.train_residual,
                    "holdout_residual" => current.holdout_residual,
                    "normalised_holdout_residual" => current.normalised_holdout_residual,
                    "noise_floor_richardson_holdout" => floor,
                    "absolute_gain" => gain_abs,
                    "relative_gain" => gain_rel,
                    "rank" => ident[(split_label, stage)].rank,
                    "condition_number" => ident[(split_label, stage)].condition_number,
                    "valid" => current.valid,
                    "rank_deficient_at_tested_stage" => ident[(split_label, stage)].rank_deficient_at_tested_stage,
                    "identifiability_reason" => ident[(split_label, stage)].reason,
                    "invalid_reason" => current.reason,
                    "fitted_coefficients" => join(current.coeffs, "|"),
                    "terms" => join(term_names(basis, idxs), "|"),
                    "verdict" => verdict,
                ))
            end
        end
    end
    return rows
end

function derived_stage_from_rows(group, tau_rel::Float64, tau_abs::Float64, rule::String)
    by_split = Dict(split => [r for r in group if r["split"] == split && r["rule"] == rule] for split in L2_SPLIT_LABELS)
    split_stages = Int[]
    any_stage1_rank_deficient = false
    for split in L2_SPLIT_LABELS
        rows = by_split[split]
        isempty(rows) && continue
        by_stage = Dict(r["tested_stage"] => r for r in rows)
        if !haskey(by_stage, 1) || by_stage[1]["rank_deficient_at_tested_stage"] || !by_stage[1]["valid"]
            any_stage1_rank_deficient |= haskey(by_stage, 1) && by_stage[1]["rank_deficient_at_tested_stage"]
            continue
        end
        max_stage = 1
        for stage in 1:(MAX_STAGE - 1)
            haskey(by_stage, stage) || continue
            current = by_stage[stage]
            current["empty_stage"] && continue
            (current["rank_deficient_at_tested_stage"] || !current["valid"]) && break
            next_stage = findfirst(s -> s > stage && haskey(by_stage, s) && !by_stage[s]["empty_stage"], 1:MAX_STAGE)
            next_stage === nothing && continue
            future = by_stage[next_stage]
            (future["rank_deficient_at_tested_stage"] || !future["valid"]) && break
            floor = current["noise_floor_richardson_holdout"]
            if rule_counts_gain(rule, current["holdout_residual"], future["holdout_residual"],
                                floor, tau_rel, tau_abs)
                max_stage = max(max_stage, next_stage)
            end
        end
        push!(split_stages, max_stage)
    end
    isempty(split_stages) && any_stage1_rank_deficient && return "rank_deficient"
    isempty(split_stages) && return "invalid_or_inconclusive"
    return median_stage(split_stages)
end

function confusion_for(stage_rows; estimator::String, weighting::String, fit_method::String,
                       rule::String, tau_rel::Float64 = 1e-4, tau_abs::Float64 = 1e-8)
    filtered = [r for r in stage_rows if r["representability"] == "exact" &&
                r["estimator"] == estimator && r["weighting"] == weighting &&
                r["fit_method"] == fit_method && r["rule"] == rule]
    grouped = Dict{Tuple{Int,Int},Vector{Dict{String,Any}}}()
    for row in filtered
        push!(get!(grouped, (row["system_id"], row["equation"]), Dict{String,Any}[]), row)
    end
    counts = Dict("under" => 0, "exact" => 0, "over" => 0,
                  "rank_deficient" => 0, "invalid_or_inconclusive" => 0)
    details = Any[]
    for (key, group) in sort(collect(grouped), by = x -> (x[1][1], x[1][2]))
        expected = group[1]["expected_eq_stage"]
        predicted = derived_stage_from_rows(group, tau_rel, tau_abs, rule)
        category = if predicted == "rank_deficient"
            "rank_deficient"
        elseif predicted == "invalid_or_inconclusive"
            "invalid_or_inconclusive"
        elseif predicted < expected
            "under"
        elseif predicted > expected
            "over"
        else
            "exact"
        end
        counts[category] += 1
        push!(details, Dict("system_id" => key[1], "equation" => key[2],
                            "expected" => expected, "predicted" => predicted,
                            "category" => category))
    end
    return Dict("counts" => counts, "details" => details)
end

function lower_stage_reaches_floor(sys::ProbeSystem, basis, traj, dX, rich, eq, expected_stage)
    splits = make_l2_splits(length(traj.t))
    for stage in 1:(expected_stage - 1)
        idxs = cumulative_stage_idxs(basis, stage)
        Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
        for split in L2_SPLIT_LABELS
            fit = splits[split].fit
            hold = splits[split].holdout
            result = ls_fit_eval(Phi, dX[:, eq], fit, hold)
            floor = mean(abs2, rich[hold, eq])
            if result.valid && result.holdout_residual <= floor
                return true, stage, split, result.holdout_residual, floor
            end
        end
    end
    return false, 0, "", NaN, NaN
end

function identifiability_rows_for_system(sys::ProbeSystem)
    traj = generate_trajectory(sys)
    basis = default_staged_polynomial_basis(sys.dim)
    dX = estimate_with("local_poly", traj)
    rich = richardson_error_estimate("local_poly", traj)
    expected = expected_stage_by_equation(sys, basis)
    rows = Dict{String,Any}[]
    for eq in 1:sys.dim
        identifiable_floor, floor_stage, floor_split, residual, floor =
            lower_stage_reaches_floor(sys, basis, traj, dX, rich, eq, expected[eq])
        true_idxs = cumulative_stage_idxs(basis, expected[eq])
        Phi = EvoODE.build_design_matrix(basis, true_idxs, traj.x, traj.t)
        deficient, reason, r, c = is_rank_deficient(Phi)
        push!(rows, Dict{String,Any}(
            "system_id" => sys.id,
            "system_name" => sys.name,
            "representability" => string(sys.representability),
            "equation" => eq,
            "expected_eq_stage" => expected[eq],
            "true_stage_rank_deficient" => deficient,
            "true_stage_identifiability_reason" => reason,
            "true_stage_rank" => r,
            "true_stage_condition_number" => c,
            "lower_stage_reaches_floor" => identifiable_floor,
            "lower_stage" => floor_stage,
            "split" => floor_split,
            "lower_stage_holdout_residual" => residual,
            "noise_floor" => floor,
            "rank_deficient_at_expected_stage" => deficient,
            "lower_stage_indistinguishable" => identifiable_floor,
        ))
    end
    return rows
end

function trajectory_at_multiplier(sys::ProbeSystem, multiplier::Int)
    dense = ProbeSystem(id = sys.id, name = sys.name, dim = sys.dim, true_rhs! = sys.true_rhs!,
                        u0 = sys.u0, tspan = sys.tspan, T = sys.T * multiplier,
                        representability = sys.representability,
                        expected_stage = sys.expected_stage,
                        expected_terms = sys.expected_terms)
    return generate_trajectory(dense)
end

function density_sweep_rows()
    rows = Dict{String,Any}[]
    for sid in (54, 63)
        sys = only([s for s in PROBE_SYSTEMS if s.id == sid])
        for multiplier in DENSITY_MULTIPLIERS
            traj = trajectory_at_multiplier(sys, multiplier)
            basis = default_staged_polynomial_basis(sys.dim)
            dX = estimate_with("local_poly", traj)
            rich = richardson_error_estimate("local_poly", traj)
            analytic = analytic_derivatives(sys, traj)
            expected = expected_stage_by_equation(sys, basis)
            for eq in 1:sys.dim
                rms_err = sqrt(mean(abs2, dX[:, eq] .- analytic[:, eq]))
                true_stage = expected[eq]
                stage_residuals = Float64[]
                floors = Float64[]
                deficient_flags = Bool[]
                for stage in 1:MAX_STAGE
                    idxs = cumulative_stage_idxs(basis, stage)
                    Phi = EvoODE.build_design_matrix(basis, idxs, traj.x, traj.t)
                    split = make_l2_splits(length(traj.t))["D"]
                    fit = weighted_ls_fit_eval(Phi, dX[:, eq], split.fit, split.holdout,
                                               weights_from_richardson(rich[:, eq]))
                    push!(stage_residuals, fit.holdout_residual)
                    push!(floors, mean(abs2, rich[split.holdout, eq]))
                    deficient, _, _, _ = is_rank_deficient(Phi[split.fit, :])
                    push!(deficient_flags, deficient)
                end
                prev_stage = max(1, true_stage - 1)
                cliff = stage_residuals[prev_stage] - stage_residuals[true_stage]
                push!(rows, Dict{String,Any}(
                    "system_id" => sid,
                    "system_name" => sys.name,
                    "equation" => eq,
                    "multiplier" => multiplier,
                    "T" => length(traj.t),
                    "expected_eq_stage" => true_stage,
                    "rms_derivative_error" => rms_err,
                    "stage_residuals" => join(stage_residuals, "|"),
                    "noise_floors" => join(floors, "|"),
                    "true_stage_cliff" => cliff,
                    "true_stage_residual" => stage_residuals[true_stage],
                    "true_stage_floor" => floors[true_stage],
                    "rank_deficient_flags" => join(deficient_flags, "|"),
                    "stage3_rank_deficient" => deficient_flags[3],
                    "true_stage_rank_deficient" => deficient_flags[true_stage],
                    "stage3_cliff_visible" => true_stage == 3 && cliff > floors[true_stage],
                ))
            end
        end
    end
    return rows
end

function split_contribution_summary(stage_rows)
    rows = Any[]
    for split in L2_SPLIT_LABELS
        split_rows = [r for r in stage_rows if r["split"] == split && r["rule"] == "threshold_only" &&
                      r["fit_method"] == "ols" && r["estimator"] == "local_poly" &&
                      r["weighting"] == "richardson_wls"]
        lost = count(r -> r["rank_deficient_at_tested_stage"], split_rows)
        push!(rows, Dict("split" => split, "cells" => length(split_rows), "lost_to_validity" => lost))
    end
    return rows
end

function write_l3_report(summary)
    open(L3_REPORT_MD, "w") do io
        println(io, "# Floor-Gated Probe")
        println(io)
        println(io, "Main configuration: local_poly + richardson_wls + ols at tau_rel=1e-4, tau_abs=1e-8.")
        println(io)
        println(io, "## Confusion")
        println(io, "Threshold-only: $(summary["threshold_confusion"]["counts"]).")
        println(io, "Floor-gated: $(summary["floor_confusion"]["counts"]).")
        println(io, "All rule/estimator/weighting/fit-method confusion counts: $(summary["confusion_grid"]).")
        println(io, "Floor-gated System-54 details: $(filter(d -> d["system_id"] == 54, summary["floor_confusion"]["details"])).")
        println(io, "Floor-gated Systems 3/11/26 details: $(filter(d -> d["system_id"] in (3, 11, 26), summary["floor_confusion"]["details"])).")
        println(io)
        println(io, "## Identifiability")
        println(io, "Lower-stage indistinguishable: $(summary["lower_stage_indistinguishable_count"]) of $(summary["exact_equation_count"]) exact equations.")
        println(io, "Rank-deficient at expected stage: $(summary["rank_deficient_at_expected_stage_count"]) of $(summary["exact_equation_count"]) exact equations.")
        println(io, "Both properties: $(summary["both_identifiability_properties_count"]) of $(summary["exact_equation_count"]) exact equations.")
        println(io, "Rows are in $(IDENTIFIABILITY_CSV).")
        println(io)
        println(io, "## Sampling Sensitivity")
        println(io, "System 54 stage-3 cliff visible rows: $(summary["system54_visible_rows"]).")
        println(io, "System 63 stage-3 library rank deficient at all densities: $(summary["system63_rank_deficient_all_densities"]).")
        println(io)
        println(io, "## Splits")
        println(io, "A: fit first 70%, hold out last 30%.")
        println(io, "B: fit last 70%, hold out first 30%; retained diagnostically because it exposes tail-only degeneracy.")
        println(io, "C: fit outer 35%+35%, hold out middle 30%.")
        println(io, "D: replacement split; fit first 25% plus third quartile, hold out second and fourth quartiles.")
        println(io, "Validity criterion: rank full, finite condition number <= $(SPLIT_COND_CAP), and fit-block excitation >= $(SPLIT_EXCITATION_FLOOR).")
        println(io, "Contribution summary: $(summary["split_contribution_summary"]).")
        println(io)
        println(io, "## Predictions")
        for p in summary["predictions"]
            println(io, "- $(p)")
        end
    end
end

function confusion_grid(stage_rows)
    rows = Any[]
    for estimator in L3_ESTIMATORS, weighting in WEIGHTING_MODES, fit_method in FIT_METHODS,
        rule in ("threshold_only", "floor_gated")
        conf = confusion_for(stage_rows; estimator = estimator, weighting = weighting,
                             fit_method = fit_method, rule = rule)
        push!(rows, Dict("estimator" => estimator, "weighting" => weighting,
                         "fit_method" => fit_method, "rule" => rule,
                         "counts" => conf["counts"]))
    end
    return rows
end

const L3_STAGE_COLUMNS = [
    "row_type", "system_id", "system_name", "dim", "representability", "equation",
    "expected_eq_stage", "tested_stage", "new_terms", "empty_stage", "split",
    "estimator", "weighting", "fit_method", "rule", "train_residual",
    "holdout_residual", "normalised_holdout_residual", "noise_floor_richardson_holdout",
    "absolute_gain", "relative_gain", "rank", "condition_number", "valid",
    "rank_deficient_at_tested_stage", "identifiability_reason", "invalid_reason",
    "fitted_coefficients", "terms", "verdict",
]

const IDENT_COLUMNS = [
    "system_id", "system_name", "representability", "equation", "expected_eq_stage",
    "true_stage_rank_deficient", "true_stage_identifiability_reason", "true_stage_rank",
    "true_stage_condition_number", "lower_stage_reaches_floor", "lower_stage", "split",
    "lower_stage_holdout_residual", "noise_floor", "rank_deficient_at_expected_stage",
    "lower_stage_indistinguishable",
]

const DENSITY_COLUMNS = [
    "system_id", "system_name", "equation", "multiplier", "T", "expected_eq_stage",
    "rms_derivative_error", "stage_residuals", "noise_floors", "true_stage_cliff",
    "true_stage_residual", "true_stage_floor", "rank_deficient_flags",
    "stage3_rank_deficient", "true_stage_rank_deficient", "stage3_cliff_visible",
]

function main_l3()
    mkpath(L3_OUTPUT_DIR)
    for path in (L3_STAGE_CSV, IDENTIFIABILITY_CSV, DENSITY_CSV)
        isfile(path) && rm(path)
    end
    stage_rows = Dict{String,Any}[]
    ident_rows = Dict{String,Any}[]
    started = time()
    for sys in PROBE_SYSTEMS
        println(@sprintf("L3 SYSTEM id=%d name=%s dim=%d", sys.id, sys.name, sys.dim))
        traj = generate_trajectory(sys)
        basis = default_staged_polynomial_basis(sys.dim)
        expected = expected_stage_by_equation(sys, basis)
        sys_rows = Dict{String,Any}[]
        for estimator in L3_ESTIMATORS
            dX = estimate_with(estimator, traj)
            rich = richardson_error_estimate(estimator, traj)
            for weighting in WEIGHTING_MODES, fit_method in FIT_METHODS, eq in 1:sys.dim
                append!(sys_rows, l3_stage_rows_for_equation(sys, basis, traj, dX, rich,
                                                             estimator, weighting, fit_method,
                                                             eq, expected[eq]))
            end
        end
        append_csv_rows(L3_STAGE_CSV, sys_rows, L3_STAGE_COLUMNS)
        append!(stage_rows, sys_rows)
        sys_ident = identifiability_rows_for_system(sys)
        append_csv_rows(IDENTIFIABILITY_CSV, sys_ident, IDENT_COLUMNS)
        append!(ident_rows, sys_ident)
        time() - started > 30 * 60 && (println("STOP: exceeded 30 minute budget after system $(sys.id)"); break)
    end
    density_rows = density_sweep_rows()
    write_csv(DENSITY_CSV, density_rows, DENSITY_COLUMNS)

    threshold_conf = confusion_for(stage_rows; estimator = "local_poly",
                                   weighting = "richardson_wls", fit_method = "ols",
                                   rule = "threshold_only")
    floor_conf = confusion_for(stage_rows; estimator = "local_poly",
                               weighting = "richardson_wls", fit_method = "ols",
                               rule = "floor_gated")
    exact_ident = [r for r in ident_rows if r["representability"] == "exact"]
    lower_stage_count = count(r -> r["lower_stage_indistinguishable"], exact_ident)
    rank_def_count = count(r -> r["rank_deficient_at_expected_stage"], exact_ident)
    both_count = count(r -> r["lower_stage_indistinguishable"] && r["rank_deficient_at_expected_stage"], exact_ident)
    s54_visible = [r for r in density_rows if r["system_id"] == 54 && r["stage3_cliff_visible"]]
    s63_rows = [r for r in density_rows if r["system_id"] == 63]
    s63_all_rank_def = all(r -> r["stage3_rank_deficient"], s63_rows)
    predictions = [
        "Prediction 1 floor-gated System-54 effect: threshold over details=$(filter(d -> d["system_id"] == 54, threshold_conf["details"])); floor details=$(filter(d -> d["system_id"] == 54, floor_conf["details"])).",
        "Prediction 2 Systems 3/11/26 floor-gated details=$(filter(d -> d["system_id"] in (3, 11, 26), floor_conf["details"])).",
        "Prediction 3 System 54 visible density rows=$(s54_visible).",
        "Prediction 4 System 63 rank deficiency persists=$(s63_all_rank_def).",
    ]
    summary = Dict{String,Any}(
        "script" => L3_SCRIPT_SLUG,
        "timestamp" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "elapsed_s" => time() - started,
        "threshold_confusion" => threshold_conf,
        "floor_confusion" => floor_conf,
        "confusion_grid" => confusion_grid(stage_rows),
        "lower_stage_indistinguishable_count" => lower_stage_count,
        "rank_deficient_at_expected_stage_count" => rank_def_count,
        "both_identifiability_properties_count" => both_count,
        "exact_equation_count" => length(exact_ident),
        "system54_visible_rows" => s54_visible,
        "system63_rank_deficient_all_densities" => s63_all_rank_def,
        "split_contribution_summary" => split_contribution_summary(stage_rows),
        "predictions" => predictions,
        "outputs" => Dict("stage_profiles" => L3_STAGE_CSV,
                          "identifiability" => IDENTIFIABILITY_CSV,
                          "density_sweep" => DENSITY_CSV),
    )
    write_json(L3_SUMMARY_JSON, summary)
    write_l3_report(summary)
    println("Wrote $(L3_STAGE_CSV)")
    println("Wrote $(IDENTIFIABILITY_CSV)")
    println("Wrote $(DENSITY_CSV)")
    println("Wrote $(L3_SUMMARY_JSON)")
    println("Wrote $(L3_REPORT_MD)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main_l3()
end
