# Frozen WP-FA3 Q3: true-support weak warm starts, no campaign work.
# This include loads run_regression.jl and wp_n25_phase_c_c5_common.jl once,
# at top level, through the existing P-04 machinery (avoids world-age errors).
include(joinpath(@__DIR__, "wp_n4_multistart_refit.jl"))

const Q3_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const Q3_WEAK = joinpath(Q3_ROOT, "analysis", "data", "sideproject_residual_growth", "q3_weak_starts.json")
const Q3_P04 = joinpath(Q3_ROOT, "outputs", "phase_c_c5_restart_curve_5dd1df8", "out")
const Q3_EXPORT = joinpath(Q3_ROOT, "outputs", "phase_c_trajectory_hashes", "wp_c4c", "trajectory_export")
const Q3_OUTPUT = joinpath(Q3_ROOT, "outputs", "sideproject_q3_weak_start", "results.jsonl")
const Q3_CONTROLS = Set(["sys0001_ic1", "sys0024_ic1", "sys0052_ic1"])
const Q3_SEED = 7

q3_hash(path) = bytes2hex(sha256(read(path)))
q3_id(row) = @sprintf("sys%04d_ic%d", Int(row["system_id"]), Int(row["initial_condition_set"]))

function q3_sources()
    paths = String[]
    for (directory, _, files) in walkdir(joinpath(Q3_ROOT, "src"))
        append!(paths, [joinpath(directory, f) for f in files if endswith(f, ".jl")])
    end
    for name in ("wp_n4_multistart_refit.jl", "run_regression.jl", "wp_n25_phase_c_c5_common.jl",
                 "phase_b_config.jl", "phase_c_config.jl", "diagnostic_systems.jl",
                 "phase_c_trajectory_hash_lib.jl", "clamp_val.jl")
        push!(paths, joinpath(@__DIR__, name))
    end
    append!(paths, [joinpath(Q3_ROOT, "Project.toml"), joinpath(Q3_ROOT, "Manifest.toml"), REGRESSION_DATA_PATH])
    return Dict(replace(relpath(p, Q3_ROOT), Char(0x5c) => '/') => q3_hash(p) for p in paths)
end

function q3_reference_records()
    records = Dict{Tuple{String, Int}, Any}()
    hashes = Dict{String, String}()
    for (directory, _, files) in walkdir(Q3_P04)
        for name in sort(files)
            endswith(name, ".jsonl") || continue
            path = joinpath(directory, name)
            hashes[replace(relpath(path, Q3_ROOT), Char(0x5c) => '/')] = q3_hash(path)
            for row in _read_history(path)
                key = (q3_id(row), Int(row["seed"]))
                haskey(records, key) && error("Duplicate P-04 cell $(key)")
                records[key] = row
            end
        end
    end
    length(records) == 180 || error("Expected 180 P-04 records")
    return records, hashes
end

function q3_read_float64(path)
    bytes = read(path)
    length(bytes) % 8 == 0 || error("Malformed float64 export $(path)")
    return collect(reinterpret(Float64, ltoh.(reinterpret(UInt64, bytes))))
end

function q3_trajectory_control(unit, traj)
    export_info = unit["export"]
    time_path = joinpath(Q3_EXPORT, String(export_info["time_path"]))
    state_path = joinpath(Q3_EXPORT, String(export_info["state_path"]))
    q3_hash(time_path) == String(export_info["time_sha256"]) || error("Export time hash changed")
    q3_hash(state_path) == String(export_info["state_sha256"]) || error("Export state hash changed")
    time = q3_read_float64(time_path)
    shape = Int[Int(v) for v in JSON3.read(String(export_info["state_shape"]))]
    length(shape) == 2 || error("Expected time-by-dimension export")
    state = Matrix(reshape(q3_read_float64(state_path), shape[2], shape[1])')
    size(traj.x) == size(state) || error("Trajectory shape mismatch")
    traj.t == time || error("Trajectory time grid differs from export")
    all(isfinite, traj.x) || error("Nonfinite training trajectory")
    relative = maximum(abs.(traj.x .- state) ./ max.(abs.(state), eps(Float64)))
    state_hash = sha256_matrix_float64_le_c_order(traj.x)
    passed = state_hash == String(export_info["state_sha256"]) || relative < 1e-8
    passed || error("Trajectory agreement failed: max relative difference=$(relative)")
    return Dict("passed" => passed, "time_grid_identical" => true,
                "time_sha256" => sha256_vector_float64_le(traj.t),
                "state_sha256" => state_hash, "export_state_sha256" => String(export_info["state_sha256"]),
                "hash_identical" => state_hash == String(export_info["state_sha256"]),
                "max_relative_difference" => relative)
end

function q3_evaluate(f!, params, structure, basis, traj, optimizer, options)
    yhat = simulate(f!, params, traj;
        abstol = optimizer.abstol, reltol = optimizer.reltol,
        maxiters = optimizer.maxiters_solve, clamp_val = optimizer.clamp_val,
        reject_nonfinite = optimizer.reject_nonfinite,
        divergence_limit = optimizer.divergence_limit, options = options)
    loss = evaluate_loss(MSELoss(), yhat, traj.x)
    metrics = r2_summary(yhat, traj.x, loss)
    return Dict{String, Any}("loss" => loss, "r2" => metrics.r2,
        "r2_by_dim" => metrics.r2_by_dim, "params" => params,
        "coefficients" => active_model_terms(structure, basis, params),
        "sentinel" => loss >= WP_N4_SENTINEL_LOSS)
end

function q3_run_unit(unit, system, references)
    sid, ic, dim = Int(unit["system_id"]), Int(unit["initial_condition_set"]), Int(unit["dim"])
    id = String(unit["unit_id"])
    traj = build_trajectory(system, ic)  # Identical call to _base_record_phase_c.
    trajectory_control = q3_trajectory_control(unit, traj)
    basis = phase_c_basis(dim)
    active = [Int[Int(i) for i in eq] for eq in unit["active_idxs"]]
    structure = StructureSpec(active)
    support = load_phase_c_support()[sid]
    support.representability == "exact" && support.status == "ok" || error("Nonexact support")
    active == support.support || error("Weak support differs from true StructureSpec")
    expected_names = [[String(n) for n in eq["term_names"]] for eq in unit["equations"]]
    _term_names(active, basis) == expected_names || error("Basis order mismatch")
    for seed in (7, 42, 123)
        ref = references[(id, seed)]
        [[String(n) for n in eq] for eq in ref["true_structure"]] == expected_names ||
            error("P-04 true support mismatch")
    end
    f!, n_params, _ = build_rhs(structure, basis)
    p0 = Float64[Float64(v) for v in unit["p0"]]
    length(p0) == n_params || error("Warm-start parameter length mismatch")
    coefficient_order = Float64[Float64(c) for eq in unit["equations"] for c in eq["coefficients"]]
    p0 == coefficient_order || error("Warm-start coefficient order mismatch")
    optimizer = build_reference_optimizer(max_fit_attempts = 1)
    options = build_options(Q3_SEED)
    w0 = q3_evaluate(f!, p0, structure, basis, traj, optimizer, options)
    w0["effective_params"] = clamp.(p0, -optimizer.clamp_val, optimizer.clamp_val)
    Random.seed!(Q3_SEED)
    params, optimizer_loss, meta = fit_parameters(optimizer, f!, traj, n_params, MSELoss(), options; p0 = p0)
    w1 = q3_evaluate(f!, params, structure, basis, traj, optimizer, options)
    w1["optimizer_loss"] = optimizer_loss
    w1["fit_meta"] = meta
    control = nothing
    if id in Q3_CONTROLS
        # Same p0=nothing path and start seed as P-04, no replacement optimizer.
        reproduced = _fit_fixed_structure_once(active, basis, traj, Q3_SEED, 1)
        candidates = [s for s in references[(id, Q3_SEED)]["reference_starts"] if Int(s["start_index"]) == 1]
        length(candidates) == 1 || error("P-04 start 1 missing or duplicated")
        expected_loss = Float64(only(candidates)["loss"])
        actual_loss = Float64(reproduced["loss"])
        passed = reinterpret(UInt64, actual_loss) == reinterpret(UInt64, expected_loss)
        control = Dict("seed" => Q3_SEED, "start_index" => 1,
                       "expected_loss" => expected_loss, "actual_loss" => actual_loss,
                       "passed" => passed, "result" => reproduced)
        passed || error("P-04 start-1 is not bit-identical for $(id): $(actual_loss) vs $(expected_loss)")
    end
    return Dict{String, Any}("unit_id" => id, "system_id" => sid,
        "initial_condition_set" => ic, "dim" => dim, "stratum" => String(unit["stratum"]),
        "trajectory_sha256" => String(unit["trajectory_sha256"]),
        "trajectory_control" => trajectory_control, "random_start_control" => control,
        "weak_abs_gt_10_count" => count(x -> abs(x) > 10, p0),
        "W0" => w0, "W1" => w1, "seed" => Q3_SEED, "protocol_commit" => "c81e7c6")
end

function q3_main(args = ARGS)
    VERSION == v"1.12.6" || error("Q3 requires Julia 1.12.6; found $(VERSION)")
    output = abspath(_arg_value(args, "--output", Q3_OUTPUT))
    weak = JSON3.read(read(Q3_WEAK, String))
    String(weak["protocol_commit"]) == "c81e7c6" || error("Wrong Q3 protocol")
    for (name, digest) in pairs(weak["input_sha256"])
        q3_hash(joinpath(Q3_ROOT, String(name))) == String(digest) || error("Weak input changed: $(name)")
    end
    units = collect(weak["units"])
    ids = Set(String(u["unit_id"]) for u in units)
    length(units) == length(ids) == 60 || error("Expected 60 unique weak-start units")
    requested = _arg_value(args, "--units", nothing)
    if requested !== nothing
        selected = Set(String.(split(requested, ',')))
        isempty(setdiff(selected, ids)) || error("Unknown --units entries")
        units = [u for u in units if String(u["unit_id"]) in selected]
    end
    units = units[1:wp_n25_parse_limit(args, length(units))]
    references, reference_hashes = q3_reference_records()
    sources = q3_sources()
    weak_hash, runner_hash = q3_hash(Q3_WEAK), q3_hash(@__FILE__)
    finished = Set{String}()
    if isfile(output)
        # A torn final JSON line fails explicitly; never truncate append-only data.
        for row in _read_history(output)
            id = String(row["unit_id"])
            id in ids || error("Unknown resumed unit $(id)")
            id in finished && error("Duplicate resumed unit $(id)")
            String(row["weak_starts_sha256"]) == weak_hash || error("Resume weak-start hash mismatch")
            String(row["runner_sha256"]) == runner_hash || error("Resume runner hash mismatch")
            Dict(String(k) => String(v) for (k, v) in pairs(row["source_sha256"])) == sources || error("Resume source mismatch")
            Dict(String(k) => String(v) for (k, v) in pairs(row["p04_sha256"])) == reference_hashes || error("Resume P-04 mismatch")
            Bool(row["trajectory_control"]["passed"]) || error("Invalid resumed trajectory control")
            if id in Q3_CONTROLS
                row["random_start_control"] !== nothing && Bool(row["random_start_control"]["passed"]) || error("Invalid resumed random-start control")
            end
            push!(finished, id)
        end
        filesize(output) == 0 || last(read(output)) == UInt8('\n') || error("JSONL must end with newline before append")
    end
    systems = wp_n25_phase_c_systems_by_id()
    for unit in units
        id = String(unit["unit_id"])
        id in finished && continue
        row = q3_run_unit(unit, systems[Int(unit["system_id"])], references)
        row["weak_starts_sha256"], row["runner_sha256"] = weak_hash, runner_hash
        row["source_sha256"], row["p04_sha256"] = sources, reference_hashes
        _append_jsonl!(output, row)
        println("Q3 completed $(id)")
    end
    return nothing
end

if abspath(PROGRAM_FILE) == @__FILE__
    q3_main()
end
