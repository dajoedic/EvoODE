# Frozen WP-FA4: Q3 machinery is included at top level, without invoking q3_main.
include(joinpath(@__DIR__, "sideproject_q3_weak_start.jl"))
const Q4_PATHS = joinpath(Q3_ROOT, "analysis/data/sideproject_residual_growth/q4_paths.json")
const Q4_OUTPUT = joinpath(Q3_ROOT, "outputs/sideproject_q4_path_fits/results.jsonl")
const Q4_CONTROL = "sys0001_ic1"

function q4_settings()
    optimizer = build_reference_optimizer(max_fit_attempts = 1)
    return Dict(string(k) => (getfield(optimizer, k) isa AbstractFloat && !isfinite(getfield(optimizer, k)) ? string(getfield(optimizer, k)) : getfield(optimizer, k)) for k in fieldnames(typeof(optimizer)))
end

function q4_evaluate(f!, params, traj, optimizer, options)
    predicted = simulate(f!, params, traj; abstol=optimizer.abstol, reltol=optimizer.reltol,
        maxiters=optimizer.maxiters_solve, clamp_val=optimizer.clamp_val,
        reject_nonfinite=optimizer.reject_nonfinite, divergence_limit=optimizer.divergence_limit,
        options=options)
    loss = evaluate_loss(MSELoss(), predicted, traj.x)
    metrics = r2_summary(predicted, traj.x, loss)
    weights = vec(var(traj.x; dims=1, corrected=false))
    weighted = metrics.r2 === nothing ? nothing :
        sum(Float64.(metrics.r2_by_dim) .* weights) / sum(weights)
    return Dict("loss"=>loss, "r2_arithmetic"=>metrics.r2, "r2_by_dim"=>metrics.r2_by_dim,
        "r2_variance_weighted"=>weighted, "n_samples"=>length(traj.x),
        "sentinel"=>loss >= WP_N4_SENTINEL_LOSS,
        "diverged"=>!all(isfinite, predicted) || metrics.r2 === nothing)
end

# Export paths in the frozen JSON were produced on Windows. Make them absolute
# before calling the unchanged Q3 loader (joinpath preserves an absolute tail).
function q4_export_path(directory, name)
    return abspath(joinpath(directory, split(replace(String(name), Char(0x5c) => '/'), '/')...))
end

function q4_selected_units(args, units)
    requested = _arg_value(args, "--units", nothing)
    unit_list = _arg_value(args, "--unit-list", nothing)
    index_text = _arg_value(args, "--index", nothing)
    (unit_list === nothing) == (index_text === nothing) || error("--unit-list and --index must be used together")
    requested !== nothing && unit_list !== nothing && error("--units and --unit-list are alternatives")
    if unit_list !== nothing
        entries = strip.(readlines(unit_list))
        all(!isempty(entry) for entry in entries) || error("Empty unit-list entry")
        length(Set(entries)) == length(entries) || error("Duplicate unit-list entry")
        index = tryparse(Int, index_text)
        index !== nothing && 0 <= index < length(entries) || error("--index is outside the 0-based unit list")
        requested = entries[index + 1]
    end
    if requested !== nothing
        selected = Set(String.(split(requested, ',')))
        ids = Set(String(u["unit_id"]) for u in units)
        isempty(setdiff(selected, ids)) || error("Unknown unit")
        units = [u for u in units if String(u["unit_id"]) in selected]
    end
    return units[1:wp_n25_parse_limit(args, length(units))]
end

function q4_verify_inputs(paths, units, input_root, export_dir)
    export_prefix = "outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/"
    needed = Set(replace(String(u["export"][field]), Char(0x5c) => '/')
                 for u in units for field in ("time_path", "state_path"))
    for (name, digest) in pairs(paths["input_sha256"])
        relative = replace(String(name), Char(0x5c) => '/')
        if startswith(relative, export_prefix)
            tail = relative[length(export_prefix)+1:end]
            # The full frozen manifest stays hashed; only selected binaries are needed.
            tail == "trajectory_manifest.csv" || tail in needed || continue
            source = q4_export_path(export_dir, tail)
        else
            source = joinpath(Q3_ROOT, split(relative, '/')...)
            isfile(source) || (source = joinpath(input_root, split(relative, '/')...))
        end
        q3_hash(source) == String(digest) || error("Input changed: $(name)")
    end
end

function q4_fit(unit, candidate, system; export_dir=Q3_EXPORT)
    ic = Int(unit["initial_condition_set"])
    train, test = build_trajectory(system, ic), build_trajectory(system, 3-ic)
    control_unit = unit
    if export_dir != Q3_EXPORT
        export_info = Dict{String,Any}(String(k) => v for (k, v) in pairs(unit["export"]))
        for field in ("time_path", "state_path")
            export_info[field] = q4_export_path(export_dir, export_info[field])
        end
        control_unit = Dict("export" => export_info)
    end
    agreement = q3_trajectory_control(control_unit, train)
    basis = phase_c_basis(Int(unit["dim"]))
    active = [Int.(collect(eq)) for eq in candidate["active_idxs"]]
    structure = StructureSpec(active)
    _term_names(active, basis) == [[String(n) for n in eq["term_names"]] for eq in candidate["equations"]] ||
        error("Candidate basis mismatch")
    f!, nparams, _ = build_rhs(structure, basis)
    p0 = Float64.(collect(candidate["p0"]))
    length(p0) == nparams || error("Parameter count mismatch")
    p0 == [Float64(c) for eq in candidate["equations"] for c in eq["coefficients"]] ||
        error("Parameter order mismatch")
    optimizer, options = build_reference_optimizer(max_fit_attempts=1), build_options(Q3_SEED)
    Random.seed!(Q3_SEED)
    params, fit_loss, meta = fit_parameters(optimizer, f!, train, nparams, MSELoss(), options; p0=p0)
    return Dict{String,Any}("unit_id"=>String(unit["unit_id"]),
        "candidate_id"=>String(candidate["candidate_id"]), "params"=>params,
        "pruned_active_idxs"=>pruned_support_idxs(structure, params),
        "optimizer_loss"=>fit_loss, "fit_meta"=>meta, "trajectory_control"=>agreement,
        "training"=>q4_evaluate(f!, params, train, optimizer, options),
        "generalization"=>q4_evaluate(f!, params, test, optimizer, options))
end

function q4_main(args=ARGS)
    VERSION == v"1.12.6" || error("Q4 requires Julia 1.12.6")
    paths_path = _arg_value(args, "--paths", Q4_PATHS)
    q3_results = _arg_value(args, "--q3-results", Q3_OUTPUT)
    q3_weak = _arg_value(args, "--q3-weak-starts", Q3_WEAK)
    export_dir = _arg_value(args, "--export-dir", Q3_EXPORT)
    input_root = _arg_value(args, "--input-root", Q3_ROOT)
    paths = JSON3.read(read(paths_path, String))
    String(paths["protocol_commit"]) == "24ede2d" || error("Wrong protocol")
    units = collect(paths["units"])
    ids = Set(String(u["unit_id"]) for u in units)
    length(units) == length(ids) == 60 || error("Expected 60 units")
    units = q4_selected_units(args, units)
    if paths_path == Q4_PATHS && export_dir == Q3_EXPORT && input_root == Q3_ROOT
        # Preserve the original full-input audit for the default laptop invocation.
        for (name, digest) in pairs(paths["input_sha256"])
            q3_hash(joinpath(Q3_ROOT, String(name))) == String(digest) || error("Input changed: $(name)")
        end
    else
        q4_verify_inputs(paths, units, input_root, export_dir)
    end
    systems = wp_n25_phase_c_systems_by_id()
    output = abspath(_arg_value(args, "--output", Q4_OUTPUT))
    sources = q3_sources()
    sources["studies/regression/sideproject_q3_weak_start.jl"] = q3_hash(joinpath(@__DIR__, "sideproject_q3_weak_start.jl"))
    settings = q4_settings()
    fingerprint = bytes2hex(sha256(codeunits(canonical_value(settings))))
    provenance = Dict("paths_sha256"=>q3_hash(paths_path), "runner_sha256"=>q3_hash(@__FILE__),
        "source_sha256"=>sources, "settings_fingerprint"=>fingerprint,
        "protocol_commit"=>"24ede2d", "q3_results_sha256"=>q3_hash(q3_results), "q3_weak_sha256"=>q3_hash(q3_weak))
    overrides = Dict(flag => abspath(_arg_value(args, flag, default))
        for (flag, default) in (("--paths", Q4_PATHS), ("--q3-results", Q3_OUTPUT),
            ("--q3-weak-starts", Q3_WEAK), ("--export-dir", Q3_EXPORT),
            ("--input-root", Q3_ROOT), ("--output", Q4_OUTPUT)) if flag in args)
    isempty(overrides) || (provenance["input_paths"] = overrides)
    finished = Set{Tuple{String,String}}()
    expected = Set((String(u["unit_id"]), String(c["candidate_id"])) for u in paths["units"]
                   for c in vcat(collect(u["candidates"]), collect(u["upper_candidates"])))
    push!(expected, (Q4_CONTROL, "control_true"))
    if isfile(output)
        for row in _read_history(output)
            key = (String(row["unit_id"]), String(row["candidate_id"]))
            key in expected || error("Unknown resumed candidate")
            key in finished && error("Duplicate resumed candidate")
            canonical_value(row["provenance"]) == canonical_value(provenance) || error("Resume provenance mismatch")
            Bool(row["trajectory_control"]["passed"]) || error("Resume trajectory mismatch")
            key[2] == "control_true" && !Bool(row["control_passed"]) && error("Failed resumed control")
            push!(finished, key)
        end
        filesize(output) == 0 || last(read(output)) == UInt8('\n') || error("Torn JSONL")
    end
    for unit in units
        uid = String(unit["unit_id"])
        candidates = Any[c for c in vcat(collect(unit["candidates"]), collect(unit["upper_candidates"]))]
        if uid == Q4_CONTROL
            # Forced true support is a separate control, never a size-choice candidate.
            q3payload = JSON3.read(read(q3_weak, String))
            truth = only([u for u in q3payload["units"] if String(u["unit_id"]) == uid])
            control_candidate = Dict("candidate_id"=>"control_true", "active_idxs"=>truth["active_idxs"],
                "equations"=>truth["equations"], "p0"=>truth["p0"])
            pushfirst!(candidates, control_candidate)
        end
        for candidate in candidates
            cid = String(candidate["candidate_id"])
            (uid, cid) in finished && continue
            row = q4_fit(unit, candidate, systems[Int(unit["system_id"])]; export_dir=export_dir)
            if cid == "control_true"
                reference = only([r for r in _read_history(q3_results) if String(r["unit_id"]) == uid])
                actual, expected_loss = Float64(row["training"]["loss"]), Float64(reference["W1"]["loss"])
                row["control_passed"] = reinterpret(UInt64, actual) == reinterpret(UInt64, expected_loss)
                row["expected_loss"] = expected_loss
                row["control_passed"] || error("Q3 W1 control is not bit-identical")
            end
            row["provenance"], row["optimizer_settings"] = provenance, settings
            _append_jsonl!(output, row)
            println("Q4 completed $(uid) $(cid)")
        end
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    q4_main()
end
