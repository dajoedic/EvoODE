import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf
using Statistics

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
include(joinpath(REPO_ROOT, "studies", "output_path_guard.jl"))

const SCRIPT_SLUG = "wp_v1_stage_cap_reliability"
const OUTPUT_DIR = study_resolve_output_dir(joinpath(REPO_ROOT, "outputs", "studies", "lookahead", SCRIPT_SLUG), ARGS)
const ROW_CSV_PATH = joinpath(OUTPUT_DIR, "row_decisions.csv")
const LOSO_CSV_PATH = joinpath(OUTPUT_DIR, "loso_decisions.csv")
const SUMMARY_JSON_PATH = joinpath(OUTPUT_DIR, "summary.json")
const REPORT_PATH = study_resolve_output_path(joinpath(REPO_ROOT, "docs", "WP-V1.md"), ARGS; flag = "--report")

const EXPECTED_CONFIG_FINGERPRINT = "1d0ccf8d53c6576d"
const EXPECTED_PHASE_B_FINGERPRINT = "e361a2af49366670"
const EXPECTED_STAGE_CAP_BEHAVIOR_FINGERPRINT = "61b6548ef0014593"

include(joinpath(REPO_ROOT, "studies", "regression", "run_regression.jl"))
include(joinpath(REPO_ROOT, "studies", "regression", "phase_b_config.jl"))

const DEFAULT_POLICY = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...)

function csv_escape(value)
    text = string(value)
    if occursin('"', text) || occursin(',', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_csv(path::String, headers, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(headers, ","))
        for row in rows
            println(io, join([csv_escape(getfield(row, Symbol(header))) for header in headers], ","))
        end
    end
end

function markdown_table(headers, rows)
    lines = String[
        "| " * join(headers, " | ") * " |",
        "| " * join(fill("---", length(headers)), " | ") * " |",
    ]
    for row in rows
        push!(lines, "| " * join(string.(row), " | ") * " |")
    end
    return join(lines, "\n")
end

function format_cap(cap)
    cap === nothing && return "nothing"
    return string(cap)
end

function cap_value(text::AbstractString)
    text == "nothing" && return nothing
    return parse(Int, text)
end

function exact_phase_b_systems()
    systems = [system for system in PHASE_B_SYSTEMS if String(system[:representability]) == "exact"]
    return sort(systems; by = system -> Int(system[:system_id]))
end

function equation_required_stages(dim::Int, support)
    support === nothing && error("Cannot derive equation stages for surrogate support")
    basis = default_staged_polynomial_basis(dim)
    stages = Int[]
    for eq_support in support
        isempty(eq_support) && error("Cannot derive required stage from empty equation support")
        push!(stages, maximum(stage_for_term_idx.(Ref(basis), eq_support)))
    end
    return stages
end

function self_integrated_trajectory(system, ic_set::Int)
    dim = Int(system[:dim])
    u0 = Float64[x for x in system[:init_sets][ic_set]]
    length(u0) == dim || error("System $(system[:system_id]) IC$(ic_set) dimension mismatch")
    t_grid = collect(range(0.0, 10.0; length = 512))
    prob = ODEProblem(system[:rhs!], copy(u0), (0.0, 10.0), nothing)
    sol = solve(prob, Tsit5(); saveat = t_grid, abstol = 1e-9, reltol = 1e-9)
    sol.retcode == ReturnCode.Success ||
        error("Self-integration failed for system $(system[:system_id]), IC$(ic_set): $(sol.retcode)")
    return Trajectory(t_grid, Array(sol)')
end

function split_state(traj::Trajectory, basis::StagedPolynomialBasis, eq::Int,
                     policy::LookAheadStageCapPolicy)
    dX = EvoODE._cap_estimate_derivatives(traj, policy.estimator)
    rich = EvoODE._cap_richardson_error_estimate(traj, policy.estimator)
    y = dX[:, eq]
    weights = policy.weighting == :richardson_wls ? EvoODE._cap_weights_from_richardson(rich[:, eq]) : ones(length(y))
    max_basis_stage = EvoODE._max_stage(basis)
    applicable_stages = [s for s in 1:max_basis_stage if !isempty(basis.term_groups[s])]
    states = NamedTuple[]
    for (split_index, split) in enumerate(EvoODE._cap_splits(length(traj.t)))
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
        push!(states, (split_index = split_index, residuals = residuals, floors = floors, usable = usable, applicable_stages = applicable_stages))
    end
    return states
end

function binary_post_floor_branch(residuals::AbstractVector{Float64},
                                  floors::AbstractVector{Float64},
                                  applicable_stages::Vector{Int},
                                  stage_pos::Int,
                                  policy::LookAheadStageCapPolicy)
    stage = applicable_stages[stage_pos]
    current_residual = residuals[stage]
    floor = floors[stage]
    isfinite(current_residual) && isfinite(floor) || return :undecidable
    current_residual <= floor || return :not_applicable
    current_residual > 0.0 || return :no_clear_drop
    floor > 0.0 || return :no_clear_drop
    floor_ratio = current_residual / floor
    floor_ratio < policy.post_floor_min_floor_ratio && return :no_clear_drop
    stage_pos == length(applicable_stages) && return :no_clear_drop
    later_residuals = [
        residuals[next_stage]
        for next_stage in applicable_stages[(stage_pos + 1):end]
        if isfinite(residuals[next_stage])
    ]
    isempty(later_residuals) && return :undecidable
    later_ratio = minimum(later_residuals) / current_residual
    later_ratio <= policy.post_floor_clear_drop_ratio && return :clear_drop
    return :no_clear_drop
end

function traced_split_decision(state, policy::LookAheadStageCapPolicy; binary::Bool = false)
    residuals = state.residuals
    usable = state.usable
    floors = state.floors
    applicable_stages = state.applicable_stages
    isempty(applicable_stages) && return ((kind = :invalid, cap = nothing, stage = 1), "empty_applicable_stages", "none")

    pos = 1
    observed_gain = false
    while pos <= length(applicable_stages)
        stage = applicable_stages[pos]
        usable[stage] || return ((kind = :invalid, cap = nothing, stage = stage), "usability", "stage=$(stage)")

        if residuals[stage] <= floors[stage]
            branch = binary ?
                binary_post_floor_branch(residuals, floors, applicable_stages, pos, policy) :
                EvoODE._cap_post_floor_significant_drop(residuals, floors, applicable_stages, pos, policy)
            trigger = post_floor_trigger(residuals, floors, applicable_stages, pos, branch, binary)
            if branch == :clear_drop && observed_gain
                observed_gain = true
                pos += 1
                continue
            end
            if branch == :no_clear_drop && observed_gain &&
               EvoODE._cap_successor_evaluable(applicable_stages, pos, usable)
                return ((kind = :positive, cap = stage, stage = stage), "floor_after_gain", trigger)
            end
            return ((kind = :undecidable, cap = nothing, stage = stage), "floor_doubt_band", trigger)
        end

        horizon_end = min(length(applicable_stages), pos + policy.lookahead_horizon)
        horizon_end == pos && return (
            (kind = observed_gain ? :positive : :undecidable, cap = observed_gain ? stage : nothing, stage = stage),
            "horizon_exhausted",
            "stage=$(stage)",
        )

        jumped = false
        for next_pos in (pos + 1):horizon_end
            next_stage = applicable_stages[next_pos]
            usable[next_stage] || return ((kind = :invalid, cap = nothing, stage = next_stage), "usability", "stage=$(next_stage)")
            if EvoODE._cap_rule_counts_gain(residuals[stage], residuals[next_stage], floors[stage], policy)
                observed_gain = true
                pos = next_pos
                jumped = true
                break
            end
        end
        jumped && continue

        if !observed_gain &&
           EvoODE._cap_residuals_uninformative_without_gain(residuals, applicable_stages, pos, policy)
            return ((kind = :undecidable, cap = nothing, stage = stage), "uninformative_without_gain", uninformative_trigger(residuals, applicable_stages, policy, pos))
        end

        if EvoODE._cap_successor_evaluable(applicable_stages, pos, usable)
            return ((kind = :positive, cap = stage, stage = stage), "gain_search_exhausted", "stage=$(stage)")
        end
        return ((kind = :invalid, cap = nothing, stage = applicable_stages[pos + 1]), "successor_usability", "stage=$(applicable_stages[pos + 1])")
    end

    return ((kind = :positive, cap = applicable_stages[end], stage = applicable_stages[end]), "loop_exhausted", "stage=$(applicable_stages[end])")
end

function post_floor_trigger(residuals, floors, applicable_stages, pos::Int, branch::Symbol, binary::Bool)
    stage = applicable_stages[pos]
    current_residual = residuals[stage]
    floor = floors[stage]
    later = pos < length(applicable_stages) ?
        [residuals[next_stage] for next_stage in applicable_stages[(pos + 1):end] if isfinite(residuals[next_stage])] :
        Float64[]
    ratio = isempty(later) || current_residual == 0.0 ? NaN : minimum(later) / current_residual
    floor_ratio = floor > 0.0 ? current_residual / floor : NaN
    mode = binary ? "binary" : "band"
    return @sprintf("%s post-floor %s at stage=%d later_ratio=%.12g floor_ratio=%.12g", mode, String(branch), stage, ratio, floor_ratio)
end

function uninformative_trigger(residuals, applicable_stages, policy::LookAheadStageCapPolicy, pos::Int)
    values = [residuals[stage] for stage in applicable_stages[pos:end] if isfinite(residuals[stage])]
    ratio = isempty(values) ? NaN : maximum(abs.(values)) / policy.tau_abs
    return @sprintf("uninformative_without_gain at stage=%d max_abs_over_tau_abs=%.12g", applicable_stages[pos], ratio)
end

function decisions_from_states(states, policy::LookAheadStageCapPolicy; binary::Bool = false)
    traced = [traced_split_decision(state, policy; binary = binary) for state in states]
    cap = EvoODE._cap_aggregate_split_decisions([item[1] for item in traced], policy)
    return (
        cap = cap,
        branches = join(["split$(states[i].split_index):$(traced[i][2])/$(String(traced[i][1].kind))/$(format_cap(traced[i][1].cap))" for i in eachindex(states)], "; "),
        triggers = join(["split$(states[i].split_index):$(traced[i][3])" for i in eachindex(states)], "; "),
    )
end

function row_class(cap, required_stage::Int)
    cap === nothing && return "abstain"
    cap < required_stage && return "wrong_commit"
    return "correct_commit"
end

function confusion(rows)
    return (
        correct_commit = count(row -> row.classification == "correct_commit", rows),
        wrong_commit = count(row -> row.classification == "wrong_commit", rows),
        unnecessary_abstain = count(row -> row.classification == "unnecessary_abstain", rows),
        correct_abstain = count(row -> row.classification == "correct_abstain", rows),
    )
end

function collect_cases(policy::LookAheadStageCapPolicy)
    cases = NamedTuple[]
    systems = exact_phase_b_systems()
    length(systems) == 20 || error("Expected 20 exact Phase-B systems, got $(length(systems))")
    for system in systems
        system_id = Int(system[:system_id])
        dim = Int(system[:dim])
        basis = default_staged_polynomial_basis(dim)
        required_stages = equation_required_stages(dim, system[:expected_support])
        for ic_set in PHASE_B_IC_SETS
            traj = self_integrated_trajectory(system, ic_set)
            for eq in 1:dim
                states = split_state(traj, basis, eq, policy)
                push!(
                    cases,
                    (
                        system_id = system_id,
                        system_name = String(system[:system_name]),
                        ic_set = ic_set,
                        equation_index = eq,
                        dim = dim,
                        required_stage = required_stages[eq],
                        states = states,
                    ),
                )
            end
        end
    end
    return cases
end

function derive_rows(cases, policy::LookAheadStageCapPolicy)
    rows = NamedTuple[]
    for case in cases
        current = decisions_from_states(case.states, policy; binary = false)
        binary_decision = decisions_from_states(case.states, policy; binary = true)
        current_class = row_class(current.cap, case.required_stage)
        binary_class = row_class(binary_decision.cap, case.required_stage)
        classification = if current.cap !== nothing
            current.cap < case.required_stage ? "wrong_commit" : "correct_commit"
        else
            binary_decision.cap === nothing || binary_decision.cap >= case.required_stage ? "unnecessary_abstain" : "correct_abstain"
        end
        push!(
            rows,
            (
                system_id = case.system_id,
                system_name = case.system_name,
                ic_set = case.ic_set,
                equation_index = case.equation_index,
                dim = case.dim,
                required_stage = case.required_stage,
                current_cap = format_cap(current.cap),
                binary_cap = format_cap(binary_decision.cap),
                current_class = current_class,
                binary_class = binary_class,
                classification = classification,
                current_branches = current.branches,
                current_triggers = current.triggers,
                binary_branches = binary_decision.branches,
                binary_triggers = binary_decision.triggers,
            ),
        )
    end
    return rows
end

function candidate_values(rows, field::Symbol)
    values = Float64[]
    for row in rows
        text = getfield(row, field)
        for m in eachmatch(r"later_ratio=([0-9.eE+-]+)", text)
            value = parse(Float64, m.captures[1])
            isfinite(value) && push!(values, value)
        end
    end
    return sort(unique(vcat(values, [0.35, 0.62])))
end

function evaluate_rows_with_policy(cases, drop::Float64, no_drop::Float64, min_floor::Float64)
    policy = LookAheadStageCapPolicy(;
        LOOKAHEAD_CAP_POLICY...,
        post_floor_clear_drop_ratio = drop,
        post_floor_clear_no_drop_ratio = no_drop,
        post_floor_min_floor_ratio = min_floor,
    )
    return derive_rows(cases, policy)
end

function choose_bounds(cases, training_system_ids::Vector{Int})
    all_rows = derive_rows(cases, DEFAULT_POLICY)
    drop_values = candidate_values(all_rows, :current_triggers)
    no_drop_values = candidate_values(all_rows, :current_triggers)
    min_floor = DEFAULT_POLICY.post_floor_min_floor_ratio
    best = nothing
    for drop in drop_values
        for no_drop in no_drop_values
            drop <= no_drop || continue
            rows = evaluate_rows_with_policy(cases, drop, no_drop, min_floor)
            training = [row for row in rows if row.system_id in training_system_ids]
            cm = confusion(training)
            cm.wrong_commit == 0 || continue
            score = (cm.unnecessary_abstain + cm.correct_abstain, -cm.correct_commit, drop, no_drop)
            if best === nothing || score < best.score
                best = (drop = drop, no_drop = no_drop, min_floor = min_floor, score = score, rows = rows, cm = cm)
            end
        end
    end
    best === nothing && error("No leave-one-system-out bounds found without wrong commitments")
    return best
end

function loso_rows(cases)
    systems = exact_phase_b_systems()
    ids = [Int(system[:system_id]) for system in systems]
    rows = NamedTuple[]
    bounds = NamedTuple[]
    for holdout in ids
        training_ids = [id for id in ids if id != holdout]
        selected = choose_bounds(cases, training_ids)
        append!(rows, [merge((holdout_system_id = holdout, drop = selected.drop, no_drop = selected.no_drop, min_floor = selected.min_floor), row) for row in selected.rows if row.system_id == holdout])
        push!(bounds, (holdout_system_id = holdout, drop = selected.drop, no_drop = selected.no_drop, min_floor = selected.min_floor))
    end
    return (rows = rows, bounds = bounds)
end

function write_report(path::String, rows, loso, fingerprints)
    cm = confusion(rows)
    loso_cm = confusion(loso.rows)
    wrong_rows = [row for row in rows if row.classification == "wrong_commit"]
    abstains = [row for row in rows if row.current_cap == "nothing"]
    loso_wrong = [row for row in loso.rows if row.classification == "wrong_commit"]
    drops = [row.drop for row in loso.bounds]
    nodrops = [row.no_drop for row in loso.bounds]
    minfloors = [row.min_floor for row in loso.bounds]

    lines = String[
        "# WP-V1 Stage-Cap Reliability",
        "",
        "Generated by `studies/lookahead/wp_v1_stage_cap_reliability.jl` at $(Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")).",
        "",
    ]
    if isempty(wrong_rows)
        push!(lines, "No wrong current commitments were observed in the 80 in-sample rows.")
    else
        push!(lines, "Wrong current commitments were observed and are listed first.")
        push!(lines, "")
        push!(lines, markdown_table(
            ["system", "ic_set", "equation", "required_stage", "current_cap", "binary_cap"],
            [[row.system_id, row.ic_set, row.equation_index, row.required_stage, row.current_cap, row.binary_cap] for row in wrong_rows],
        ))
    end

    append!(
        lines,
        [
            "",
            "## In-Sample Matrix",
            "",
            markdown_table(
                ["cell", "rows"],
                [
                    ["correct commit", cm.correct_commit],
                    ["wrong commit", cm.wrong_commit],
                    ["unnecessary abstain", cm.unnecessary_abstain],
                    ["correct abstain", cm.correct_abstain],
                ],
            ),
            "",
            "## Abstentions",
            "",
        ],
    )
    if isempty(abstains)
        push!(lines, "No current abstentions were observed.")
    else
        push!(lines, markdown_table(
            ["system", "ic_set", "equation", "required_stage", "binary_cap", "classification", "trigger"],
            [[row.system_id, row.ic_set, row.equation_index, row.required_stage, row.binary_cap, row.classification, row.current_triggers] for row in abstains],
        ))
    end

    append!(
        lines,
        [
            "",
            "## Fingerprints",
            "",
            markdown_table(
                ["fingerprint", "expected", "observed", "unchanged"],
                [
                    ["config_fingerprint()", "`$(EXPECTED_CONFIG_FINGERPRINT)`", "`$(fingerprints.config)`", fingerprints.config == EXPECTED_CONFIG_FINGERPRINT],
                    ["phase_b_fingerprint()", "`$(EXPECTED_PHASE_B_FINGERPRINT)`", "`$(fingerprints.phase_b)`", fingerprints.phase_b == EXPECTED_PHASE_B_FINGERPRINT],
                    ["stage_cap_behavior_fingerprint()", "`$(EXPECTED_STAGE_CAP_BEHAVIOR_FINGERPRINT)`", "`$(fingerprints.stage_cap)`", fingerprints.stage_cap == EXPECTED_STAGE_CAP_BEHAVIOR_FINGERPRINT],
                ],
            ),
            "",
            "## Leave-One-System-Out",
            "",
        ],
    )
    if isempty(loso_wrong)
        push!(lines, "No wrong current commitments were observed in the 80 out-of-sample rows.")
    else
        push!(lines, "Wrong out-of-sample current commitments:")
        push!(lines, markdown_table(
            ["holdout", "system", "ic_set", "equation", "required_stage", "current_cap", "binary_cap"],
            [[row.holdout_system_id, row.system_id, row.ic_set, row.equation_index, row.required_stage, row.current_cap, row.binary_cap] for row in loso_wrong],
        ))
    end
    append!(
        lines,
        [
            "",
            markdown_table(
                ["cell", "rows"],
                [
                    ["correct commit", loso_cm.correct_commit],
                    ["wrong commit", loso_cm.wrong_commit],
                    ["unnecessary abstain", loso_cm.unnecessary_abstain],
                    ["correct abstain", loso_cm.correct_abstain],
                ],
            ),
            "",
            "LOSO bound selection used only the 19 training systems for each holdout and selected bounds with zero training wrong commitments, minimizing total abstentions and then maximizing correct commitments.",
            "",
            markdown_table(
                ["bound", "min", "max"],
                [
                    ["post_floor_clear_drop_ratio", @sprintf("%.12g", minimum(drops)), @sprintf("%.12g", maximum(drops))],
                    ["post_floor_clear_no_drop_ratio", @sprintf("%.12g", minimum(nodrops)), @sprintf("%.12g", maximum(nodrops))],
                    ["post_floor_min_floor_ratio", @sprintf("%.12g", minimum(minfloors)), @sprintf("%.12g", maximum(minfloors))],
                ],
            ),
            "",
            "## Outputs",
            "",
            "- Row CSV: `$(relpath(ROW_CSV_PATH, REPO_ROOT))`",
            "- LOSO CSV: `$(relpath(LOSO_CSV_PATH, REPO_ROOT))`",
            "- Summary JSON: `$(relpath(SUMMARY_JSON_PATH, REPO_ROOT))`",
        ],
    )

    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(lines, "\n"))
    end
end

function main()
    fingerprints = (
        config = config_fingerprint(),
        phase_b = phase_b_fingerprint(),
        stage_cap = stage_cap_behavior_fingerprint(),
    )
    cases = collect_cases(DEFAULT_POLICY)
    rows = derive_rows(cases, DEFAULT_POLICY)
    if fingerprints.config != EXPECTED_CONFIG_FINGERPRINT ||
       fingerprints.phase_b != EXPECTED_PHASE_B_FINGERPRINT ||
       fingerprints.stage_cap != EXPECTED_STAGE_CAP_BEHAVIOR_FINGERPRINT
        loso = (rows = NamedTuple[], bounds = NamedTuple[])
    else
        loso = loso_rows(cases)
    end

    write_csv(
        ROW_CSV_PATH,
        [
            "system_id", "system_name", "ic_set", "equation_index", "dim",
            "required_stage", "current_cap", "binary_cap", "current_class",
            "binary_class", "classification", "current_branches", "current_triggers",
            "binary_branches", "binary_triggers",
        ],
        rows,
    )
    if !isempty(loso.rows)
        write_csv(
            LOSO_CSV_PATH,
            [
                "holdout_system_id", "drop", "no_drop", "min_floor",
                "system_id", "system_name", "ic_set", "equation_index", "dim",
                "required_stage", "current_cap", "binary_cap", "current_class",
                "binary_class", "classification", "current_branches", "current_triggers",
                "binary_branches", "binary_triggers",
            ],
            loso.rows,
        )
    end
    summary = Dict(
        "fingerprints" => Dict("config" => fingerprints.config, "phase_b" => fingerprints.phase_b, "stage_cap" => fingerprints.stage_cap),
        "in_sample" => confusion(rows),
        "loso" => isempty(loso.rows) ? nothing : confusion(loso.rows),
        "loso_bounds" => loso.bounds,
    )
    open(SUMMARY_JSON_PATH, "w") do io
        JSON3.pretty(io, summary)
    end
    write_report(REPORT_PATH, rows, loso, fingerprints)
    println("Wrote $(ROW_CSV_PATH)")
    !isempty(loso.rows) && println("Wrote $(LOSO_CSV_PATH)")
    println("Wrote $(SUMMARY_JSON_PATH)")
    println("Wrote $(REPORT_PATH)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
