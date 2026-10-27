# Q5 deliberately includes the frozen Q4 runner without invoking its main.
include(joinpath(@__DIR__, "sideproject_q4_path_fits.jl"))

# Strict RFC4180 records for the export's quoted CSV (no extra dependency).
function q5_csv_record(line)
    fields, buffer, quoted = String[], IOBuffer(), false
    chars, i = collect(chomp(line)), 1
    while i <= length(chars)
        c = chars[i]
        if c == '"'
            if quoted && i < length(chars) && chars[i+1] == '"'
                write(buffer, '"'); i += 1
            else
                quoted = !quoted
            end
        elseif c == ',' && !quoted
            push!(fields, String(take!(buffer)))
        else
            write(buffer, c)
        end
        i += 1
    end
    quoted && error("Unterminated CSV quote")
    push!(fields, String(take!(buffer)))
    return fields
end

q5_key(r) = (parse(Int, r["system_id"]), parse(Int, r["initial_condition_set"]),
    parse(Float64, r["noise_sigma"]), parse(Float64, r["subsample_rho"]), parse(Int, r["noise_realization"]))

function q5_index(path)
    lines = readlines(path)
    isempty(lines) && error("Empty export index")
    header = q5_csv_record(first(lines))
    rows = Dict{Tuple{Int,Int,Float64,Float64,Int},Dict{String,String}}()
    for line in lines[2:end]
        values = q5_csv_record(line)
        length(values) == length(header) || error("CSV width mismatch")
        row = Dict(zip(header, values))
        key = q5_key(row)
        haskey(rows, key) && error("Duplicate export cell")
        rows[key] = row
    end
    return rows
end

function q5_read_cell(directory, row)
    row["hash_format"] == "sha256_raw_little_endian_float64" || error("Hash format")
    row["dtype"] == "float64" && row["byte_order"] == "little_endian" || error("Dtype/order")
    row["time_axis_order"] == "time" && row["state_axis_order"] == "time_by_dimension_c_order" || error("Axes")
    tshape = Int.(collect(JSON3.read(row["time_shape"])))
    shape = Int.(collect(JSON3.read(row["state_shape"])))
    dim = parse(Int, row["dimension"])
    length(tshape) == 1 && shape == [only(tshape), dim] || error("Shape mismatch")
    only(tshape) == parse(Int, row["n_observed_points"]) || error("Point count")
    paths = [q4_export_path(directory, joinpath(replace(row["cell_dir"], Char(0x5c)=>'/'),
             replace(row[field], Char(0x5c)=>'/'))) for field in ("time_path", "state_path")]
    for (path, field, n) in zip(paths, ("time_sha256", "state_sha256"), (only(tshape), prod(shape)))
        q3_hash(path) == row[field] || error("Binary hash mismatch: $(path)")
        filesize(path) == 8*n || error("Binary size mismatch")
    end
    t, flat = q3_read_float64(paths[1]), q3_read_float64(paths[2])
    x = Matrix(reshape(flat, dim, only(tshape))')
    all(isfinite, t) && all(isfinite, x) && all(diff(t) .> 0) || error("Invalid observations")
    digest = "{\"state_sha256\":\"$(row["state_sha256"])\",\"time_sha256\":\"$(row["time_sha256"])\"}"
    return Trajectory(t, x), digest
end

function q5_clean_start_loss(f!, params, observed, clean, optimizer, options)
    # Evaluation only. Include the clean t0 even when thinning removed it.
    prepend = observed.t[1] != clean.t[1]
    times = prepend ? vcat(clean.t[1], observed.t) : copy(observed.t)
    states = prepend ? vcat(clean.x[1:1, :], observed.x) : copy(observed.x)
    states[1, :] = clean.x[1, :]
    grid = Trajectory(times, states)
    prediction = simulate(f!, params, grid; abstol=optimizer.abstol, reltol=optimizer.reltol,
        maxiters=optimizer.maxiters_solve, clamp_val=optimizer.clamp_val,
        reject_nonfinite=optimizer.reject_nonfinite, divergence_limit=optimizer.divergence_limit, options=options)
    return evaluate_loss(MSELoss(), prepend ? prediction[2:end, :] : prediction, observed.x)
end

function q5_fit(cell, candidate, system, observed, clean, test)
    basis = phase_c_basis(Int(cell["dim"]))
    active = [Int.(collect(eq)) for eq in candidate["active_idxs"]]
    structure = StructureSpec(active)
    _term_names(active, basis) == [[String(n) for n in eq["term_names"]] for eq in candidate["equations"]] || error("Basis mismatch")
    f!, nparams, _ = build_rhs(structure, basis)
    p0 = Float64.(collect(candidate["p0"]))
    length(p0) == nparams || error("Parameter count")
    p0 == [Float64(c) for eq in candidate["equations"] for c in eq["coefficients"]] || error("Parameter order")
    optimizer, options = build_reference_optimizer(max_fit_attempts=1), build_options(Q3_SEED)
    Random.seed!(Q3_SEED)
    params, loss, meta = fit_parameters(optimizer, f!, observed, nparams, MSELoss(), options; p0=p0)
    return Dict{String,Any}("unit_id"=>String(cell["unit_id"]), "cell_id"=>String(cell["cell_id"]),
        "candidate_id"=>String(candidate["candidate_id"]), "sigma"=>Float64(cell["sigma"]),
        "rho"=>Float64(cell["rho"]), "realization"=>Int(cell["realization"]),
        "observed_data_sha256"=>String(cell["observed_data_sha256"]),
        "params"=>params, "pruned_active_idxs"=>pruned_support_idxs(structure, params),
        "optimizer_loss"=>loss, "fit_meta"=>meta,
        "training"=>q4_evaluate(f!, params, observed, optimizer, options),
        "reconstruction"=>q4_evaluate(f!, params, clean, optimizer, options),
        "generalization"=>q4_evaluate(f!, params, test, optimizer, options),
        "clean_ic_observed_mse"=>q5_clean_start_loss(f!, params, observed, clean, optimizer, options),
        "evaluation_ode_solves"=>4)
end

function q5_atomic_append(output, row)
    mkpath(dirname(output))
    temporary = output * ".candidate.tmp"
    open(temporary, "w") do io
        isfile(output) && write(io, read(output))
        JSON3.write(io, json_safe(row)); write(io, '\n'); flush(io)
    end
    # Same-directory rename publishes the complete candidate or the old file.
    Base.Filesystem.rename(temporary, output)
end

function q5_main(args=ARGS)
    VERSION == v"1.12.6" || error("Q5 requires Julia 1.12.6")
    paths_path = _arg_value(args, "--paths", joinpath(Q3_ROOT, "outputs/sideproject_q5_inputs/q5_probe_paths.json"))
    directory = _arg_value(args, "--export-dir", joinpath(Q3_ROOT, "outputs/phase_c_c6_data_conditions_5dd1df8"))
    index_path = _arg_value(args, "--export-index", joinpath(directory, "index.csv"))
    payload = JSON3.read(read(paths_path, String))
    String(payload["protocol_commit"]) == "f737939" || error("Wrong Q5 protocol")
    q3_hash(index_path) == String(payload["input_sha256"]["outputs/phase_c_c6_data_conditions_5dd1df8/index.csv"]) || error("Export index changed")
    cells = collect(payload["cells"])
    allcells = copy(cells)
    # Q4 selector accepts unit_id; expose cell_id only in this selection view.
    views = [Dict("unit_id"=>String(c["cell_id"])) for c in cells]
    selected = Set(String(v["unit_id"]) for v in q4_selected_units(args, views))
    cells = [c for c in cells if String(c["cell_id"]) in selected]
    index = q5_index(index_path)
    settings = q4_settings()
    sources = q3_sources()
    for name in ("sideproject_q3_weak_start.jl", "sideproject_q4_path_fits.jl", "sideproject_q5_noise_fits.jl")
        sources["studies/regression/"*name] = q3_hash(joinpath(@__DIR__, name))
    end
    provenance = Dict("paths_sha256"=>q3_hash(paths_path), "index_sha256"=>q3_hash(index_path),
        "runner_sha256"=>q3_hash(@__FILE__), "source_sha256"=>sources,
        "protocol_commit"=>"f737939", "settings_fingerprint"=>bytes2hex(sha256(codeunits(canonical_value(settings)))))
    output = abspath(_arg_value(args, "--output", joinpath(Q3_ROOT, "outputs/sideproject_q5_fits/results.jsonl")))
    expected = Set((String(c["cell_id"]), String(k["candidate_id"])) for c in allcells
                   for k in vcat(collect(c["candidates"]), collect(c["upper_candidates"])))
    finished = Set{Tuple{String,String}}()
    if isfile(output)
        filesize(output) == 0 || last(read(output)) == UInt8('\n') || error("Torn JSONL")
        for row in _read_history(output)
            key = (String(row["cell_id"]), String(row["candidate_id"]))
            key in expected && !(key in finished) || error("Unknown/duplicate resumed candidate")
            canonical_value(row["provenance"]) == canonical_value(provenance) || error("Resume provenance mismatch")
            push!(finished, key)
        end
    end
    systems = wp_n25_phase_c_systems_by_id()
    for cell in cells
        sid, ic = Int(cell["system_id"]), Int(cell["initial_condition_set"])
        row = index[(sid, ic, Float64(cell["sigma"]), Float64(cell["rho"]), Int(cell["realization"]))]
        observed, digest = q5_read_cell(directory, row)
        digest == String(cell["observed_data_sha256"]) || error("Path/data hash mismatch")
        clean, _ = q5_read_cell(directory, index[(sid, ic, 0.0, 0.0, 1)])
        test, _ = q5_read_cell(directory, index[(sid, 3-ic, 0.0, 0.0, 1)])
        # Check export clean targets against the same integration used in Q4.
        integrated = build_trajectory(systems[sid], ic)
        integrated.t == clean.t && integrated.x == clean.x || error("Clean export differs from Q4 integration")
        integrated_test = build_trajectory(systems[sid], 3-ic)
        integrated_test.t == test.t && integrated_test.x == test.x || error("Clean test export differs from Q4 integration")
        for candidate in vcat(collect(cell["candidates"]), collect(cell["upper_candidates"]))
            key = (String(cell["cell_id"]), String(candidate["candidate_id"]))
            key in finished && continue
            result = q5_fit(cell, candidate, systems[sid], observed, clean, test)
            result["provenance"], result["optimizer_settings"] = provenance, settings
            result["trajectory_control"] = Dict("passed"=>true, "hash_identical"=>true)
            q5_atomic_append(output, result)
            push!(finished, key)
            println("Q5 completed $(key)")
        end
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    q5_main()
end
