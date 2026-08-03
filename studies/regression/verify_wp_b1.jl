import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3
using Statistics

include(joinpath(@__DIR__, "run_regression.jl"))

const WP_B1_OUTPUT_DIR = normpath(joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "wp_b1"))
const WP_B1_SCRATCH_HISTORY_PATH = joinpath(WP_B1_OUTPUT_DIR, "scratch_history.jsonl")
const WP_B1_RECORDS_PATH = joinpath(WP_B1_OUTPUT_DIR, "verification.json")
const WP_B1_REPORT_PATH = normpath(joinpath(@__DIR__, "..", "..", "codex", "REPORT_WP_B1.md"))
const OLD_WP_C1_FINGERPRINT = "df5db7763bcd2449"

function _system(system_id::Int)
    matches = [system for system in REGRESSION_SYSTEMS if Int(system[:system_id]) == system_id]
    isempty(matches) && error("Unknown regression system $(system_id)")
    return matches[1]
end

function _variant(label::String)
    matches = [variant for variant in VARIANTS if String(variant.label) == label]
    isempty(matches) && error("Unknown regression variant $(label)")
    return matches[1]
end

function _json(value)
    return sprint(io -> JSON3.write(io, value))
end

function _trajectory_checks()
    rows = Dict{String, Any}[]
    for system in REGRESSION_SYSTEMS
        system_id = Int(system[:system_id])
        for ic_set in REGRESSION_IC_SETS
            traj = build_trajectory(system, ic_set)
            expected_init = Float64[x for x in system[:init_sets][ic_set]]
            observed_init = Float64[x for x in traj.x[1, :]]
            push!(
                rows,
                Dict(
                    "system_id" => system_id,
                    "initial_condition_set" => ic_set,
                    "points" => length(traj.t),
                    "t_start" => first(traj.t),
                    "t_end" => last(traj.t),
                    "first_state" => observed_init,
                    "dataset_init" => expected_init,
                    "first_state_matches_init" => observed_init == expected_init,
                    "derivative_active_fractions" => derivative_active_fractions(system_id, traj),
                ),
            )
        end
    end
    return rows
end

function _trajectory_difference(system_id::Int)
    system = _system(system_id)
    traj1 = build_trajectory(system, 1)
    traj2 = build_trajectory(system, 2)
    return Dict(
        "system_id" => system_id,
        "ic1" => Float64[x for x in system[:init_sets][1]],
        "ic2" => Float64[x for x in system[:init_sets][2]],
        "max_abs_trajectory_difference" => maximum(abs.(traj1.x .- traj2.x)),
    )
end

function _append_scratch_record!(record)
    mkpath(dirname(WP_B1_SCRATCH_HISTORY_PATH))
    open(WP_B1_SCRATCH_HISTORY_PATH, "a") do io
        JSON3.write(io, record)
        write(io, '\n')
    end
end

function _write_report(fingerprint::String, checks, smoke, difference)
    open(WP_B1_REPORT_PATH, "w") do io
        println(io, "# REPORT WP-B1")
        println(io)
        println(io, "## Fingerprint")
        println(io)
        println(io, "- New `config_fingerprint`: `$(fingerprint)`")
        println(io, "- Differs from old WP-C1 fingerprint `$(OLD_WP_C1_FINGERPRINT)`: `$(fingerprint != OLD_WP_C1_FINGERPRINT)`")
        println(io)
        println(io, "## Trajectory Checks")
        println(io)
        println(io, "| system | ic_set | points | t_start | t_end | first state matches dataset init | derivative_active_fractions |")
        println(io, "|---:|---:|---:|---:|---:|---|---|")
        for row in checks
            println(
                io,
                "| $(row["system_id"]) | $(row["initial_condition_set"]) | $(row["points"]) | $(row["t_start"]) | $(row["t_end"]) | $(row["first_state_matches_init"]) | `$(_json(row["derivative_active_fractions"]))` |",
            )
        end
        println(io)
        println(io, "All checked trajectories have 512 points, start at 0.0, end at 10.0, and their first state matches the dataset `init` entry exactly.")
        println(io)
        println(io, "## Single-Cell Result")
        println(io)
        println(io, "- Scratch history path: `$(WP_B1_SCRATCH_HISTORY_PATH)`")
        println(io, "- Variant: `$(smoke["variant"])`")
        println(io, "- System: `$(smoke["system_id"])`")
        println(io, "- Initial-condition set: `$(smoke["initial_condition_set"])`")
        println(io, "- Seed: `$(smoke["seed"])`")
        println(io, "- Loss: `$(smoke["loss"])`")
        println(io, "- Cap: `$(_json(get(smoke, "stage_caps", nothing)))`")
        println(io, "- `eq_overshoot`: `$(_json(smoke["eq_overshoot"]))`")
        println(io, "- `pruned_match`: `$(smoke["pruned_match"])`")
        println(io, "- Support: `$(_json(smoke["support_terms"]))`")
        println(io)
        println(io, "## Initial-Condition Selection")
        println(io)
        println(io, "System $(difference["system_id"]) gives different trajectories for `EVO_REGRESSION_IC_SET=1` and `EVO_REGRESSION_IC_SET=2`: max absolute trajectory difference `$(difference["max_abs_trajectory_difference"])`.")
        println(io)
        println(io, "## IC Set Threading")
        println(io)
        println(io, "- `diagnostic_systems.jl`: `REGRESSION_IC_SETS`, dataset `init_sets`, and dataset `t_grid` are loaded from `benchmarks/data/strogatz_extended.json`.")
        println(io, "- `config_fingerprint()`: includes `initial_condition_sets`, per-system `init_sets`, and the dataset `t_grid`.")
        println(io, "- Selection: `selected_ic_sets()` reads `EVO_REGRESSION_IC_SET`.")
        println(io, "- Resume key: `completed_key()` and `load_completed_cells()` use `(variant, system, initial-condition set, seed)`.")
        println(io, "- Record schema: records include `initial_condition_set`, `u0`, `tspan`, `T`, and `derivative_active_fractions`.")
        println(io, "- Execution: `build_trajectory()` and `run_one()` both take `ic_set`; `main()` loops over IC sets and logs them.")
        println(io, "- Verification: this script writes the smoke cell to the scratch history path, not to `studies/regression/history.jsonl`.")
    end
end

function main()
    mkpath(WP_B1_OUTPUT_DIR)
    fingerprint = config_fingerprint()
    checks = _trajectory_checks()
    all(row["points"] == REGRESSION_T for row in checks) || error("Not all trajectories have $(REGRESSION_T) points")
    all(row["t_start"] == 0.0 for row in checks) || error("Not all trajectories start at 0.0")
    all(row["t_end"] == 10.0 for row in checks) || error("Not all trajectories end at 10.0")
    all(row["first_state_matches_init"] for row in checks) || error("Not all trajectories match dataset init")

    variant = _variant("evogrow_v2_2_stage_capped")
    system = _system(3)
    provenance = git_provenance()
    smoke = run_one(variant, system, 1, 42, fingerprint, provenance)
    smoke["error"] === nothing || error("Smoke cell failed: $(smoke["error"])")
    _append_scratch_record!(smoke)

    difference = _trajectory_difference(3)
    difference["max_abs_trajectory_difference"] > 0.0 || error("IC-set trajectories are identical")

    output = Dict(
        "config_fingerprint" => fingerprint,
        "old_fingerprint" => OLD_WP_C1_FINGERPRINT,
        "fingerprint_changed" => fingerprint != OLD_WP_C1_FINGERPRINT,
        "trajectory_checks" => checks,
        "single_cell" => smoke,
        "trajectory_difference" => difference,
        "scratch_history_path" => WP_B1_SCRATCH_HISTORY_PATH,
    )
    open(WP_B1_RECORDS_PATH, "w") do io
        JSON3.pretty(io, output)
        write(io, '\n')
    end
    _write_report(fingerprint, checks, smoke, difference)

    println("config_fingerprint=$(fingerprint)")
    println("scratch_history=$(WP_B1_SCRATCH_HISTORY_PATH)")
    println("report=$(WP_B1_REPORT_PATH)")
    println("loss=$(smoke["loss"])")
    println("cap=$(_json(get(smoke, "stage_caps", nothing)))")
    println("eq_overshoot=$(_json(smoke["eq_overshoot"]))")
    println("pruned_match=$(smoke["pruned_match"])")
    println("support=$(_json(smoke["support_terms"]))")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
