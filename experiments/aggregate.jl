import Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using Dates
using JSON3
using Printf

if isempty(ARGS)
    error("Usage: julia experiments/aggregate.jl <experiment_id>")
end

const EXPERIMENT_ID = ARGS[1]
const EXPERIMENT_DIR = joinpath(@__DIR__, EXPERIMENT_ID)
const MANIFEST_PATH = joinpath(EXPERIMENT_DIR, "manifest.json")
const REGISTRY_PATH = joinpath(EXPERIMENT_DIR, "run_registry.csv")

if !isdir(EXPERIMENT_DIR)
    error("Experiment directory does not exist: $(EXPERIMENT_DIR)")
end

if !isfile(MANIFEST_PATH)
    error("Manifest not found: $(MANIFEST_PATH)")
end

const MANIFEST = try
    JSON3.read(read(MANIFEST_PATH, String))
catch err
    error("Failed to read manifest JSON: $(sprint(showerror, err))")
end

const CSV_COLUMNS = [
    "run_id",
    "experiment_id",
    "phase",
    "hypothesis",
    "run_type",
    "include_in_paper",
    "system_id",
    "system_name",
    "system_dim",
    "system_representability",
    "system_expected_stage",
    "variant",
    "seed",
    "status",
    "inferred_status",
    "success",
    "failure_reason",
    "started_at",
    "finished_at",
    "loss",
    "objective",
    "exact_support_match",
    "final_stage",
    "stage_overshoot",
    "wasted_levels",
    "total_loss_evals",
    "total_invalid_evals",
    "elapsed_s",
    "partial",
    "metrics_available",
    "corrupted"
]

function read_json_maybe(path::String)
    if !isfile(path)
        return false, nothing
    end
    try
        return true, JSON3.read(read(path, String))
    catch
        return true, nothing
    end
end

function value_to_csv(value)
    if value === nothing
        return ""
    elseif value isa Bool
        return value ? "true" : "false"
    elseif value isa AbstractFloat
        return string(value)
    elseif value isa Integer
        return string(value)
    else
        s = String(value)
        s = replace(s, "\"" => "\"\"")
        if occursin(',', s) || occursin('"', s) || occursin('\n', s) || occursin('\r', s)
            return "\"" * s * "\""
        end
        return s
    end
end

function get_maybe(obj, field::Symbol)
    if obj === nothing
        return nothing
    end
    return hasproperty(obj, field) ? getproperty(obj, field) : nothing
end

function build_row(run_id::String)
    run_dir = joinpath(EXPERIMENT_DIR, "runs", run_id)
    config_path = joinpath(run_dir, "config.json")
    status_path = joinpath(run_dir, "status.json")
    metrics_path = joinpath(run_dir, "metrics.json")
    result_path = joinpath(run_dir, "result.json")

    corrupted = false

    config_exists, config_obj = read_json_maybe(config_path)
    if !config_exists || config_obj === nothing
        corrupted = true
        row = Dict(col => nothing for col in CSV_COLUMNS)
        row["run_id"] = run_id
        row["status"] = "corrupted"
        row["inferred_status"] = "corrupted"
        row["metrics_available"] = false
        row["corrupted"] = true
        return row
    end

    status_exists, status_obj = read_json_maybe(status_path)
    status = nothing
    success = nothing
    failure_reason = nothing
    started_at = nothing
    finished_at = nothing
    inferred_status = nothing

    if !status_exists
        inferred_status = "never_started"
    elseif status_obj === nothing
        corrupted = true
        status = "corrupted"
        inferred_status = "corrupted"
    else
        status = get_maybe(status_obj, :status)
        success = get_maybe(status_obj, :success)
        failure_reason = get_maybe(status_obj, :failure_reason)
        started_at = get_maybe(status_obj, :started_at)
        finished_at = get_maybe(status_obj, :finished_at)

        if status == "running" && finished_at === nothing
            inferred_status = "interrupted"
        else
            inferred_status = status
        end
    end

    metrics_exists, metrics_obj = read_json_maybe(metrics_path)
    metrics_available = false
    loss = nothing
    objective = nothing
    exact_support_match = nothing
    final_stage = nothing
    stage_overshoot = nothing
    wasted_levels = nothing
    total_loss_evals = nothing
    total_invalid_evals = nothing
    elapsed_s = nothing
    partial = nothing

    if metrics_exists && metrics_obj === nothing
        corrupted = true
    elseif metrics_obj !== nothing
        metrics_available = true
        loss = get_maybe(metrics_obj, :loss)
        objective = get_maybe(metrics_obj, :objective)
        exact_support_match = get_maybe(metrics_obj, :exact_support_match)
        final_stage = get_maybe(metrics_obj, :final_stage)
        stage_overshoot = get_maybe(metrics_obj, :stage_overshoot)
        wasted_levels = get_maybe(metrics_obj, :wasted_levels)
        total_loss_evals = get_maybe(metrics_obj, :total_loss_evals)
        total_invalid_evals = get_maybe(metrics_obj, :total_invalid_evals)
        elapsed_s = get_maybe(metrics_obj, :elapsed_s)
        partial = get_maybe(metrics_obj, :partial)
    end

    result_exists, result_obj = read_json_maybe(result_path)
    if status == "finished" && (!result_exists || result_obj === nothing || !metrics_exists)
        corrupted = true
    end

    row = Dict{String,Any}()
    row["run_id"] = get_maybe(config_obj, :run_id)
    row["experiment_id"] = get_maybe(config_obj, :experiment_id)
    row["phase"] = get_maybe(config_obj, :phase)
    row["hypothesis"] = get_maybe(config_obj, :hypothesis)
    row["run_type"] = get_maybe(config_obj, :run_type)
    row["include_in_paper"] = get_maybe(config_obj, :include_in_paper)
    row["system_id"] = get_maybe(config_obj, :system_id)
    row["system_name"] = get_maybe(config_obj, :system_name)
    row["system_dim"] = get_maybe(config_obj, :system_dim)
    row["system_representability"] = get_maybe(config_obj, :system_representability)
    row["system_expected_stage"] = get_maybe(config_obj, :system_expected_stage)
    row["variant"] = get_maybe(config_obj, :variant)
    row["seed"] = get_maybe(config_obj, :seed)

    row["status"] = status
    row["inferred_status"] = inferred_status
    row["success"] = success
    row["failure_reason"] = failure_reason
    row["started_at"] = started_at
    row["finished_at"] = finished_at

    row["loss"] = loss
    row["objective"] = objective
    row["exact_support_match"] = exact_support_match
    row["final_stage"] = final_stage
    row["stage_overshoot"] = stage_overshoot
    row["wasted_levels"] = wasted_levels
    row["total_loss_evals"] = total_loss_evals
    row["total_invalid_evals"] = total_invalid_evals
    row["elapsed_s"] = elapsed_s
    row["partial"] = partial

    row["metrics_available"] = metrics_available
    row["corrupted"] = corrupted
    return row
end

rows = [build_row(String(run_id)) for run_id in MANIFEST.run_ids]

open(REGISTRY_PATH, "w") do io
    println(io, join(CSV_COLUMNS, ","))
    for row in rows
        println(io, join([value_to_csv(get(row, col, nothing)) for col in CSV_COLUMNS], ","))
    end
end

finished_success = count(r -> get(r, "status", nothing) == "finished" && get(r, "success", nothing) == true, rows)
finished_failure = count(r -> get(r, "status", nothing) == "finished" && get(r, "success", nothing) == false, rows)
failed_count = count(r -> get(r, "inferred_status", nothing) == "failed", rows)
interrupted_count = count(r -> get(r, "inferred_status", nothing) == "interrupted", rows)
queued_count = count(r -> get(r, "inferred_status", nothing) == "queued", rows)
never_started_count = count(r -> get(r, "inferred_status", nothing) == "never_started", rows)
corrupted_count = count(r -> get(r, "corrupted", false) == true, rows)

@printf("Experiment: %s\n", EXPERIMENT_ID)
@printf("Total runs in manifest: %d\n", length(rows))
@printf("  finished (success=true):  %d\n", finished_success)
@printf("  finished (success=false): %d\n", finished_failure)
@printf("  failed:                   %d\n", failed_count)
@printf("  interrupted:              %d\n", interrupted_count)
@printf("  queued:                   %d\n", queued_count)
@printf("  never_started:            %d\n", never_started_count)
@printf("  corrupted:                %d\n", corrupted_count)
@printf("run_registry.csv written to: %s\n", REGISTRY_PATH)
