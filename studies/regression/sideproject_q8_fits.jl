# Q8 reuses all Q5 readers, evaluation, selection and publication machinery.
include(joinpath(@__DIR__, "sideproject_q5_noise_fits.jl"))

function q8_settings(cell; fixed_ic=false)
    settings = q4_settings()
    settings["clamp_val"] = Float64(cell["coefficient_bound"])
    for key in ("arm", "ic_mode", "coefficient_bound", "start", "refit")
        settings[key] = cell[key]
    end
    settings["fixed_initial_state_control"] = fixed_ic
    return settings
end

function q8_fit(cell, candidate, system, observed, clean, test; fixed_ic=false)
    active = [Int.(collect(eq)) for eq in candidate["active_idxs"]]
    structure, basis = StructureSpec(active), phase_c_basis(Int(cell["dim"]))
    _term_names(active, basis) == [[String(n) for n in eq["term_names"]] for eq in candidate["equations"]] || error("Basis mismatch")
    f!, nparams, _ = build_rhs(structure, basis)
    p0 = Float64.(collect(candidate["p0"]))
    length(p0) == nparams || error("Parameter count")
    p0 == [Float64(v) for eq in candidate["equations"] for v in eq["coefficients"]] || error("Parameter order")
    bound = Float64(cell["coefficient_bound"])
    bound in (10.0, 1000.0) || error("Coefficient bound")
    String(cell["ic_mode"]) in ("first_sample", "estimated") || error("IC mode")
    String(cell["start"]) in ("weak", "random") || error("Start mode")
    optimizer = build_reference_optimizer(max_fit_attempts=1, clamp_val=bound)
    options = build_options(Q3_SEED)
    estimated = cell["ic_mode"] == "estimated" && Bool(cell["refit"])
    # The seed does not depend on shard order, process RNG or arm scheduling.
    seed = parse(Int, bytes2hex(sha256("Q8:start:$(cell["cell_id"]):$(candidate["candidate_id"])"))[1:15]; base=16)
    start = cell["start"] == "random" ? 0.1 .* randn(Random.MersenneTwister(seed), nparams) : p0
    Random.seed!(Q3_SEED)
    initial = collect(observed.x[1, :])
    if Bool(cell["refit"])
        params, loss, meta = fit_parameters(optimizer, f!, observed, nparams, MSELoss(), options;
            p0=start, estimate_initial_state=estimated, fixed_initial_state=fixed_ic)
        estimated && !fixed_ic && (initial = meta.fitted_initial_state)
    else
        params = clamp.(p0, -bound, bound)
        loss = q4_evaluate(f!, params, observed, optimizer, options)["loss"]
        meta = (method="no_refit", loss_evals=0, ode_solves=0, solve_time_s=0.0, fit_time_s=0.0,
            fit_attempts=0, fit_failed=false)
    end
    training = q4_evaluate(f!, params, observed, optimizer, options)
    evaluation_solves = Bool(cell["refit"]) ? 4 : 5
    if estimated && !fixed_ic
        prediction = EvoODE._predict_traj(f!, observed, vcat(params, initial), optimizer; coefficient_count=nparams)
        train_loss = evaluate_loss(MSELoss(), prediction, observed.x)
        metrics = r2_summary(prediction, observed.x, train_loss)
        weights = vec(var(observed.x; dims=1, corrected=false))
        weighted = metrics.r2 === nothing ? nothing : sum(Float64.(metrics.r2_by_dim) .* weights) / sum(weights)
        training = Dict("loss"=>train_loss, "r2_arithmetic"=>metrics.r2, "r2_by_dim"=>metrics.r2_by_dim,
            "r2_variance_weighted"=>weighted, "n_samples"=>length(observed.x),
            "sentinel"=>train_loss >= WP_N4_SENTINEL_LOSS,
            "diverged"=>!all(isfinite, prediction) || metrics.r2 === nothing)
        evaluation_solves += 1
    end
    return Dict{String,Any}("unit_id"=>String(cell["unit_id"]), "cell_id"=>String(cell["cell_id"]),
        "candidate_id"=>String(candidate["candidate_id"]), "arm"=>String(cell["arm"]),
        "ic_mode"=>String(cell["ic_mode"]), "coefficient_bound"=>bound, "start"=>String(cell["start"]),
        "refit"=>Bool(cell["refit"]), "sigma"=>Float64(cell["sigma"]), "rho"=>Float64(cell["rho"]),
        "realization"=>Int(cell["realization"]), "observed_data_sha256"=>String(cell["observed_data_sha256"]),
        "params"=>params, "pruned_active_idxs"=>pruned_support_idxs(structure, params),
        "optimizer_loss"=>loss, "fit_meta"=>meta, "training"=>training,
        "fitted_initial_state"=>initial, "estimated_ic_training_mse"=>training["loss"],
        "estimated_clean_ic_distance"=>sqrt(sum(abs2, initial .- clean.x[1, :])),
        "reconstruction"=>q4_evaluate(f!, params, clean, optimizer, options),
        "generalization"=>q4_evaluate(f!, params, test, optimizer, options),
        "clean_ic_observed_mse"=>q5_clean_start_loss(f!, params, observed, clean, optimizer, options),
        "evaluation_ode_solves"=>evaluation_solves)
end

function q8_read_cell(directory, fallback, row)
    # Each binary pair is staged together. Readers still verify both raw hashes.
    rel = joinpath(replace(row["cell_dir"], Char(0x5c)=>'/'), replace(row["state_path"], Char(0x5c)=>'/'))
    return q5_read_cell(isfile(joinpath(directory, rel)) ? directory : fallback, row)
end

function q8_main(args=ARGS)
    VERSION == v"1.12.6" || error("Q8 requires Julia 1.12.6")
    path = _arg_value(args, "--paths", joinpath(Q3_ROOT, "outputs/sideproject_q8_inputs/grid/q8_fit_paths.json"))
    directory = _arg_value(args, "--export-dir", joinpath(Q3_ROOT, "outputs/phase_c_c6_data_conditions_5dd1df8"))
    fallback = _arg_value(args, "--fallback-export-dir", directory)
    index_path = _arg_value(args, "--export-index", joinpath(directory, "index.csv"))
    payload = JSON3.read(read(path, String))
    payload["protocol"] == "Q8" || error("Wrong Q8 protocol")
    q3_hash(index_path) == payload["input_sha256"]["outputs/phase_c_c6_data_conditions_5dd1df8/index.csv"] || error("Export index changed")
    q3_hash(joinpath(Q3_ROOT, "docs/sideproject_residual_growth_protocol_q8.md")) == payload["q8_protocol_sha256"] || error("Q8 protocol changed")
    allcells = collect(payload["cells"])
    views = [Dict("unit_id"=>String(c["shard_id"])) for c in allcells]
    selected = Set(String(v["unit_id"]) for v in q4_selected_units(args, views))
    cells = [c for c in allcells if String(c["shard_id"]) in selected]
    fixed = _arg_flag(args, "--fixed-initial-state")
    sources = q3_sources()
    for name in ("sideproject_q3_weak_start.jl", "sideproject_q4_path_fits.jl", "sideproject_q5_noise_fits.jl", "sideproject_q8_fits.jl")
        sources["studies/regression/"*name] = q3_hash(joinpath(@__DIR__, name))
    end
    provenance(c) = Dict("paths_sha256"=>q3_hash(path), "index_sha256"=>q3_hash(index_path),
        "runner_sha256"=>q3_hash(@__FILE__), "source_sha256"=>sources, "protocol"=>"Q8",
        "settings_fingerprint"=>bytes2hex(sha256(codeunits(canonical_value(q8_settings(c; fixed_ic=fixed))))))
    output = abspath(_arg_value(args, "--output", joinpath(Q3_ROOT, "outputs/sideproject_q8_fits/results.jsonl")))
    expected = Dict((String(c["cell_id"]), String(c["arm"]), String(k["candidate_id"]))=>c for c in allcells for k in c["candidates"])
    finished = Set{Tuple{String,String,String}}()
    if isfile(output)
        filesize(output) == 0 || last(read(output)) == UInt8('\n') || error("Torn JSONL")
        for row in _read_history(output)
            key = (String(row["cell_id"]), String(row["arm"]), String(row["candidate_id"]))
            haskey(expected, key) && !(key in finished) || error("Unknown/duplicate resumed candidate")
            canonical_value(row["provenance"]) == canonical_value(provenance(expected[key])) || error("Resume provenance mismatch")
            # Compare in record form: JSON stores e.g. 1000.0 as 1000, which reads back as an integer.
            canonical_value(row["optimizer_settings"]) == canonical_value(JSON3.read(JSON3.write(json_safe(q8_settings(expected[key]; fixed_ic=fixed))))) || error("Resume settings mismatch")
            push!(finished, key)
        end
    end
    index, systems = q5_index(index_path), wp_n25_phase_c_systems_by_id()
    for cell in cells
        sid, ic = Int(cell["system_id"]), Int(cell["initial_condition_set"])
        observed, digest = q8_read_cell(directory, fallback, index[(sid, ic, Float64(cell["sigma"]), Float64(cell["rho"]), Int(cell["realization"]))])
        digest == cell["observed_data_sha256"] || error("Path/data hash mismatch")
        clean, _ = q8_read_cell(directory, fallback, index[(sid, ic, 0.0, 0.0, 1)])
        test, _ = q8_read_cell(directory, fallback, index[(sid, 3-ic, 0.0, 0.0, 1)])
        for (target, j) in ((clean, ic), (test, 3-ic))
            integrated = build_trajectory(systems[sid], j)
            integrated.t == target.t && integrated.x == target.x || error("Clean export differs from Q4 integration")
        end
        for candidate in cell["candidates"]
            key = (String(cell["cell_id"]), String(cell["arm"]), String(candidate["candidate_id"]))
            key in finished && continue
            result = q8_fit(cell, candidate, systems[sid], observed, clean, test; fixed_ic=fixed)
            result["provenance"], result["optimizer_settings"] = provenance(cell), q8_settings(cell; fixed_ic=fixed)
            result["trajectory_control"] = Dict("passed"=>true, "hash_identical"=>true)
            q5_atomic_append(output, result)
            push!(finished, key)
            println("Q8 completed $(key)")
        end
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    q8_main()
end
