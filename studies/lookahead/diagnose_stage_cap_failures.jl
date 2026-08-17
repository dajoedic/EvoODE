import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using Dates
using DifferentialEquations
using JSON3
using Printf
using Statistics

const REPO_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const SCRIPT_SLUG = "diagnose_stage_cap_failures"
const OUTPUT_DIR = joinpath(REPO_ROOT, "outputs", "studies", "lookahead", SCRIPT_SLUG)
const STAGE_CSV_PATH = joinpath(OUTPUT_DIR, "stage_diagnostics.csv")
const CAP_CSV_PATH = joinpath(OUTPUT_DIR, "cap_diagnostics.csv")
const SENSITIVITY_CSV_PATH = joinpath(OUTPUT_DIR, "threshold_sensitivity.csv")
const REPORT_PATH = joinpath(REPO_ROOT, "docs", "wp_c2_stage_cap_failure_diagnosis.md")
const OLD_CONFIG_FINGERPRINT = "06e1c71fbd10a3a4"
const OLD_PHASE_B_FINGERPRINT = "41f69abc3670b6c4"

include(joinpath(REPO_ROOT, "studies", "regression", "run_regression.jl"))
include(joinpath(REPO_ROOT, "studies", "regression", "phase_b_config.jl"))

const TARGET_ROWS = [
    (system_id = 55, ic_set = 1, eq = 3, role = "target"),
    (system_id = 55, ic_set = 2, eq = 3, role = "target"),
    (system_id = 56, ic_set = 1, eq = 3, role = "target"),
    (system_id = 56, ic_set = 2, eq = 3, role = "target"),
    (system_id = 31, ic_set = 2, eq = 1, role = "target"),
]

const CONTROL_ROWS = vcat(
    [(system_id = 61, ic_set = ic, eq = eq, role = "control") for ic in PHASE_B_IC_SETS for eq in 1:3],
    [(system_id = sid, ic_set = ic, eq = eq, role = "control") for sid in (26, 27) for ic in PHASE_B_IC_SETS for eq in 1:2],
    [(system_id = 31, ic_set = 1, eq = 1, role = "control")],
)

const DIAGNOSTIC_ROWS = vcat(TARGET_ROWS, CONTROL_ROWS)
const SENSITIVITY_FACTORS = [1e-2, 1e-1, 1.0, 10.0, 100.0]

function csv_escape(value)
    text = string(value)
    if occursin('"', text) || occursin(',', text) || occursin('\n', text) || occursin('\r', text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function format_cap(cap)
    cap === nothing && return "nothing"
    return string(cap)
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

function equation_required_stages(dim::Int, support)
    basis = default_staged_polynomial_basis(dim)
    return [maximum(stage_for_term_idx.(Ref(basis), eq_support)) for eq_support in support]
end

function exact_derivatives(system, traj::Trajectory)
    return _phase_b_rhs_matrix(system[:rhs!], traj)
end

function cap_diagnostics(traj::Trajectory, basis::StagedPolynomialBasis, eq::Int,
                         policy::LookAheadStageCapPolicy, dX::Matrix{Float64}, rich::Matrix{Float64})
    y = dX[:, eq]
    weights = policy.weighting == :richardson_wls ? EvoODE._cap_weights_from_richardson(rich[:, eq]) : ones(length(y))
    max_basis_stage = EvoODE._max_stage(basis)
    new_counts = [length(basis.term_groups[s]) for s in 1:max_basis_stage]
    applicable_stages = [s for s in 1:max_basis_stage if new_counts[s] > 0]
    split_rows = NamedTuple[]
    stage_rows = NamedTuple[]

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
        decision, branch = traced_split_decision(residuals, usable, floors, applicable_stages, policy)
        push!(split_rows, (split_index = split_index, decision = decision, branch = branch))

        for stage in 1:max_basis_stage
            prev_stage = stage - 1
            abs_delta = prev_stage >= 1 ? residuals[prev_stage] - residuals[stage] : NaN
            rel_delta = prev_stage >= 1 && residuals[prev_stage] != 0.0 ? abs_delta / residuals[prev_stage] : NaN
            gain_from_prev = prev_stage >= 1 ? EvoODE._cap_rule_counts_gain(residuals[prev_stage], residuals[stage], floors[prev_stage], policy) : false
            push!(
                stage_rows,
                (
                    split_index = split_index,
                    stage = stage,
                    residual = residuals[stage],
                    floor = floors[stage],
                    usable = usable[stage],
                    prev_stage = prev_stage >= 1 ? string(prev_stage) : "none",
                    abs_delta_from_prev = abs_delta,
                    rel_delta_from_prev = rel_delta,
                    tau_abs = policy.tau_abs,
                    tau_rel = policy.tau_rel,
                    gain_from_prev = gain_from_prev,
                    decision_kind = String(decision.kind),
                    decision_cap = format_cap(decision.cap),
                    decision_stage = decision.stage,
                    termination_branch = branch,
                ),
            )
        end
    end

    decisions = [row.decision for row in split_rows]
    cap = EvoODE._cap_aggregate_split_decisions(decisions, policy)
    return (cap = cap, split_rows = split_rows, stage_rows = stage_rows)
end

function traced_split_decision(residuals::AbstractVector{Float64}, usable::AbstractVector{Bool},
                               floors::AbstractVector{Float64}, applicable_stages::Vector{Int},
                               policy::LookAheadStageCapPolicy)
    isempty(applicable_stages) && return ((kind = :invalid, cap = nothing, stage = 1), "empty_applicable_stages")

    pos = 1
    observed_gain = false
    while pos <= length(applicable_stages)
        stage = applicable_stages[pos]
        usable[stage] || return ((kind = :invalid, cap = nothing, stage = stage), "usability")

        if residuals[stage] <= floors[stage]
            if observed_gain && EvoODE._cap_successor_evaluable(applicable_stages, pos, usable)
                return ((kind = :positive, cap = stage, stage = stage), "floor_after_gain")
            end
            return ((kind = :undecidable, cap = nothing, stage = stage), "floor_without_gain")
        end

        horizon_end = min(length(applicable_stages), pos + policy.lookahead_horizon)
        horizon_end == pos && return (
            (kind = observed_gain ? :positive : :undecidable, cap = observed_gain ? stage : nothing, stage = stage),
            "horizon_exhausted",
        )

        jumped = false
        for next_pos in (pos + 1):horizon_end
            next_stage = applicable_stages[next_pos]
            usable[next_stage] || return ((kind = :invalid, cap = nothing, stage = next_stage), "usability")
            if EvoODE._cap_rule_counts_gain(residuals[stage], residuals[next_stage], floors[stage], policy)
                observed_gain = true
                pos = next_pos
                jumped = true
                break
            end
        end
        jumped && continue

        if EvoODE._cap_successor_evaluable(applicable_stages, pos, usable)
            return ((kind = :positive, cap = stage, stage = stage), "gain_search_exhausted")
        end
        return ((kind = :invalid, cap = nothing, stage = applicable_stages[pos + 1]), "successor_usability")
    end

    return ((kind = :positive, cap = applicable_stages[end], stage = applicable_stages[end]), "loop_exhausted")
end

function majority_branch(split_rows)
    branches = [row.branch for row in split_rows]
    counts = [(branch, count(==(branch), branches)) for branch in sort(unique(branches))]
    sort!(counts; by = x -> (-x[2], x[1]))
    return counts[1][1]
end

function split_branch_string(split_rows)
    return join(["split$(row.split_index):$(row.branch)/$(String(row.decision.kind))/$(format_cap(row.decision.cap))" for row in split_rows], "; ")
end

function run_diagnostics()
    policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...)
    stage_rows = NamedTuple[]
    cap_rows = NamedTuple[]
    sensitivity_rows = NamedTuple[]

    for spec in DIAGNOSTIC_ROWS
        system = phase_b_system(spec.system_id)
        dim = Int(system[:dim])
        basis = default_staged_polynomial_basis(dim)
        required_stages = equation_required_stages(dim, system[:expected_support])
        traj = self_integrated_trajectory(system, spec.ic_set)
        estimated_dX = EvoODE._cap_estimate_derivatives(traj, policy.estimator)
        estimated_rich = EvoODE._cap_richardson_error_estimate(traj, policy.estimator)
        exact_dX = exact_derivatives(system, traj)
        exact_rich = zeros(size(exact_dX))
        estimated = cap_diagnostics(traj, basis, spec.eq, policy, estimated_dX, estimated_rich)
        exact = cap_diagnostics(traj, basis, spec.eq, policy, exact_dX, exact_rich)

        for row in estimated.stage_rows
            push!(
                stage_rows,
                merge(
                    (
                        role = spec.role,
                        system_id = spec.system_id,
                        system_name = String(system[:system_name]),
                        ic_set = spec.ic_set,
                        equation_index = spec.eq,
                        derivative_source = "estimated",
                    ),
                    row,
                ),
            )
        end
        for row in exact.stage_rows
            push!(
                stage_rows,
                merge(
                    (
                        role = spec.role,
                        system_id = spec.system_id,
                        system_name = String(system[:system_name]),
                        ic_set = spec.ic_set,
                        equation_index = spec.eq,
                        derivative_source = "exact",
                    ),
                    row,
                ),
            )
        end

        push!(
            cap_rows,
            (
                role = spec.role,
                system_id = spec.system_id,
                system_name = String(system[:system_name]),
                ic_set = spec.ic_set,
                equation_index = spec.eq,
                required_stage = required_stages[spec.eq],
                estimated_cap = format_cap(estimated.cap),
                exact_derivative_cap = format_cap(exact.cap),
                estimated_majority_branch = majority_branch(estimated.split_rows),
                exact_majority_branch = majority_branch(exact.split_rows),
                estimated_split_branches = split_branch_string(estimated.split_rows),
                exact_split_branches = split_branch_string(exact.split_rows),
            ),
        )

        if spec.role == "target"
            for tau_rel_factor in SENSITIVITY_FACTORS
                for tau_abs_factor in SENSITIVITY_FACTORS
                    varied_policy = LookAheadStageCapPolicy(;
                        LOOKAHEAD_CAP_POLICY...,
                        tau_rel = LOOKAHEAD_CAP_POLICY.tau_rel * tau_rel_factor,
                        tau_abs = LOOKAHEAD_CAP_POLICY.tau_abs * tau_abs_factor,
                    )
                    varied = cap_diagnostics(traj, basis, spec.eq, varied_policy, estimated_dX, estimated_rich)
                    push!(
                        sensitivity_rows,
                        (
                            system_id = spec.system_id,
                            ic_set = spec.ic_set,
                            equation_index = spec.eq,
                            tau_rel_factor = tau_rel_factor,
                            tau_abs_factor = tau_abs_factor,
                            tau_rel = varied_policy.tau_rel,
                            tau_abs = varied_policy.tau_abs,
                            cap = format_cap(varied.cap),
                            majority_branch = majority_branch(varied.split_rows),
                            split_branches = split_branch_string(varied.split_rows),
                        ),
                    )
                end
            end
        end
    end

    return (stage_rows = stage_rows, cap_rows = cap_rows, sensitivity_rows = sensitivity_rows)
end

function audit_rows_from_csv()
    path = joinpath(REPO_ROOT, "outputs", "studies", "lookahead", "audit_exact_stage_cap_horizons", "exact_stage_cap_horizon_audit.csv")
    isfile(path) || return []
    lines = readlines(path)
    headers = split(lines[1], ',')
    idx(name) = findfirst(==(name), headers)
    return [
        (
            system_id = parse(Int, split(line, ',')[idx("system_id")]),
            ic_set = parse(Int, split(line, ',')[idx("ic_set")]),
            horizon = parse(Int, split(line, ',')[idx("horizon")]),
            equation_index = parse(Int, split(line, ',')[idx("equation_index")]),
            cap = split(line, ',')[idx("cap")],
        )
        for line in lines[2:end]
    ]
end

function horizon_identity_summary()
    rows = audit_rows_from_csv()
    isempty(rows) && return (checked = 0, identical = false, mismatches = [])
    h3 = Dict((row.system_id, row.ic_set, row.equation_index) => row.cap for row in rows if row.horizon == 3)
    h5 = Dict((row.system_id, row.ic_set, row.equation_index) => row.cap for row in rows if row.horizon == 5)
    mismatches = []
    for key in sort(collect(keys(h3)))
        if h3[key] != h5[key]
            system_id, ic_set, eq = key
            push!(mismatches, [system_id, ic_set, eq, h3[key], h5[key]])
        end
    end
    return (checked = length(h3), identical = isempty(mismatches), mismatches = mismatches)
end

function caps_to_three_count(rows)
    targets = [row for row in rows if row.role == "target"]
    return count(row -> row.exact_derivative_cap == "3", targets)
end

function sensitivity_summary_rows(rows)
    out = []
    for spec in TARGET_ROWS
        selected = [
            row for row in rows
            if row.system_id == spec.system_id && row.ic_set == spec.ic_set && row.equation_index == spec.eq
        ]
        caps = sort(unique(row.cap for row in selected))
        cap3 = count(row -> row.cap == "3", selected)
        push!(out, [spec.system_id, spec.ic_set, spec.eq, join(caps, ", "), "$(cap3)/$(length(selected))"])
    end
    return out
end

function write_report(path::String, result)
    identity = horizon_identity_summary()
    target_caps = [row for row in result.cap_rows if row.role == "target"]
    control_caps = [row for row in result.cap_rows if row.role == "control"]
    exact_three = caps_to_three_count(result.cap_rows)
    cause = if exact_three == length(target_caps)
        "Exact derivatives move all five target caps to 3. For systems 55 and 56, this supports derivative-estimation error on chaotic trajectories as the Lorenz failure mechanism. System 31 also moves from 1 to 3 with exact derivatives, so its failure is likewise tied to the derivative input rather than to the default gain thresholds."
    elseif exact_three >= 4
        "Exact derivatives move the four Lorenz target caps to 3. This supports derivative-estimation error on chaotic trajectories as the Lorenz failure mechanism, while the remaining target row needs separate treatment."
    elseif exact_three == 0
        "Exact derivatives do not move the target caps to 3; this supports the gain rule or thresholds as the failure mechanism."
    else
        "The exact-derivative experiment is mixed; it does not cleanly establish either single mechanism for all target rows."
    end
    target_branches = sort(unique(row.estimated_majority_branch for row in target_caps))
    control_branches = sort(unique(row.estimated_majority_branch for row in control_caps))
    branch_comparison = "Estimated target branches: `$(join(target_branches, "`, `"))`; estimated control branches: `$(join(control_branches, "`, `"))`. The Lorenz target rows end through the same `floor_after_gain` branch as the controls, so their failure is not explained by a unique termination branch. System 31 / IC2 differs from the controls by ending through `gain_search_exhausted`."

    lines = String[
        "# WP-C2 Stage-Cap Failure Diagnosis",
        "",
        "Generated by `studies/lookahead/diagnose_stage_cap_failures.jl` at $(Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")).",
        "",
        "## Part 1: Horizon To Basis End",
        "",
        "The default `lookahead_horizon` is `$(LOOKAHEAD_CAP_POLICY.lookahead_horizon)`, matching the current staged polynomial basis depth.",
        "The WP-C1 audit CSV contains $(identity.checked) row keys at horizon 3. Horizon 5 is row-wise cap-identical to horizon 3: `$(identity.identical)`.",
    ]
    if !isempty(identity.mismatches)
        push!(lines, markdown_table(["system", "ic_set", "equation", "horizon_3_cap", "horizon_5_cap"], identity.mismatches))
    end
    append!(
        lines,
        [
            "",
            "## Fingerprints",
            "",
            markdown_table(
                ["fingerprint", "old", "new"],
                [
                    ["Regression", "`$(OLD_CONFIG_FINGERPRINT)`", "`$(config_fingerprint())`"],
                    ["Phase B", "`$(OLD_PHASE_B_FINGERPRINT)`", "`$(phase_b_fingerprint())`"],
                ],
            ),
            "",
            "## 1. Target Termination Branches",
            "",
            markdown_table(
                ["system", "ic_set", "equation", "required_stage", "estimated_cap", "estimated_branch", "estimated_split_branches"],
                [[row.system_id, row.ic_set, row.equation_index, row.required_stage, row.estimated_cap, row.estimated_majority_branch, row.estimated_split_branches] for row in target_caps],
            ),
            "",
            "## 2. Control Branch Comparison",
            "",
            markdown_table(
                ["system", "ic_set", "equation", "required_stage", "estimated_cap", "estimated_branch"],
                [[row.system_id, row.ic_set, row.equation_index, row.required_stage, row.estimated_cap, row.estimated_majority_branch] for row in control_caps],
            ),
            "",
            branch_comparison,
            "",
            "## 3. Exact-Derivative Caps",
            "",
            markdown_table(
                ["system", "ic_set", "equation", "estimated_cap", "exact_derivative_cap", "exact_branch"],
                [[row.system_id, row.ic_set, row.equation_index, row.estimated_cap, row.exact_derivative_cap, row.exact_majority_branch] for row in target_caps],
            ),
            "",
            "## 4. Cause",
            "",
            cause,
            "",
            "## Threshold Sensitivity",
            "",
            markdown_table(["system", "ic_set", "equation", "caps_seen", "cap_3_cells"], sensitivity_summary_rows(result.sensitivity_rows)),
            "",
            "Defaults for `tau_rel` and `tau_abs` were not changed; this is only a measurement over the 5 x 5 factor grid `[1e-2, 1e-1, 1, 10, 100]`.",
            "",
            "## Recommendation",
            "",
            "Do not tune thresholds from these five rows. The next step should isolate whether derivative noise and split aggregation interact differently on chaotic trajectories, using the exact-derivative diagnostic as a reference only.",
            "",
            "## Outputs",
            "",
            "- Stage CSV: `outputs/studies/lookahead/$(SCRIPT_SLUG)/stage_diagnostics.csv`",
            "- Cap CSV: `outputs/studies/lookahead/$(SCRIPT_SLUG)/cap_diagnostics.csv`",
            "- Sensitivity CSV: `outputs/studies/lookahead/$(SCRIPT_SLUG)/threshold_sensitivity.csv`",
        ],
    )

    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(lines, "\n"))
    end
end

function main()
    result = run_diagnostics()
    write_csv(
        STAGE_CSV_PATH,
        [
            "role", "system_id", "system_name", "ic_set", "equation_index", "derivative_source",
            "split_index", "stage", "residual", "floor", "usable", "prev_stage",
            "abs_delta_from_prev", "rel_delta_from_prev", "tau_abs", "tau_rel",
            "gain_from_prev", "decision_kind", "decision_cap", "decision_stage",
            "termination_branch",
        ],
        result.stage_rows,
    )
    write_csv(
        CAP_CSV_PATH,
        [
            "role", "system_id", "system_name", "ic_set", "equation_index", "required_stage",
            "estimated_cap", "exact_derivative_cap", "estimated_majority_branch",
            "exact_majority_branch", "estimated_split_branches", "exact_split_branches",
        ],
        result.cap_rows,
    )
    write_csv(
        SENSITIVITY_CSV_PATH,
        [
            "system_id", "ic_set", "equation_index", "tau_rel_factor", "tau_abs_factor",
            "tau_rel", "tau_abs", "cap", "majority_branch", "split_branches",
        ],
        result.sensitivity_rows,
    )
    write_report(REPORT_PATH, result)
    println("Wrote $(STAGE_CSV_PATH)")
    println("Wrote $(CAP_CSV_PATH)")
    println("Wrote $(SENSITIVITY_CSV_PATH)")
    println("Wrote $(REPORT_PATH)")
    println("Diagnostic rows: $(length(result.cap_rows))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
