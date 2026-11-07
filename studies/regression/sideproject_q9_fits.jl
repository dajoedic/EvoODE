# Q9 (final WISP run): the Q8 fit function unchanged, arm C1000 only.
# Differences to Q8: protocol label and hash, source inventory, one export directory.
include(joinpath(@__DIR__, "sideproject_q8_fits.jl"))

function q9_main(args=ARGS)
    VERSION == v"1.12.6" || error("Q9 requires Julia 1.12.6")
    path = _arg_value(args, "--paths", joinpath(Q3_ROOT, "outputs/sideproject_q9_inputs/grid/q9_paths.json"))
    directory = _arg_value(args, "--export-dir", joinpath(Q3_ROOT, "outputs/phase_c_c6_data_conditions_5dd1df8"))
    index_path = _arg_value(args, "--export-index", joinpath(directory, "index.csv"))
    payload = JSON3.read(read(path, String))
    payload["protocol"] == "Q9" || error("Wrong Q9 protocol")
    payload["arm"] == "C1000" || error("Q9 runs arm C1000 only")
    q3_hash(index_path) == payload["input_sha256"]["outputs/phase_c_c6_data_conditions_5dd1df8/index.csv"] || error("Export index changed")
    q3_hash(joinpath(Q3_ROOT, "docs/sideproject_residual_growth_protocol_q9.md")) == payload["q9_protocol_sha256"] || error("Q9 protocol changed")
    allcells = collect(payload["cells"])
    all(c -> c["arm"] == "C1000" && c["ic_mode"] == "estimated" && c["coefficient_bound"] == 1000 &&
        c["start"] == "weak" && c["refit"] == true, allcells) || error("Q9 cell settings differ from C1000")
    views = [Dict("unit_id"=>String(c["shard_id"])) for c in allcells]
    selected = Set(String(v["unit_id"]) for v in q4_selected_units(args, views))
    cells = [c for c in allcells if String(c["shard_id"]) in selected]
    sources = q3_sources()
    for name in ("sideproject_q3_weak_start.jl", "sideproject_q4_path_fits.jl", "sideproject_q5_noise_fits.jl",
                 "sideproject_q8_fits.jl", "sideproject_q9_fits.jl")
        sources["studies/regression/"*name] = q3_hash(joinpath(@__DIR__, name))
    end
    provenance(c) = Dict("paths_sha256"=>q3_hash(path), "index_sha256"=>q3_hash(index_path),
        "runner_sha256"=>q3_hash(@__FILE__), "source_sha256"=>sources, "protocol"=>"Q9",
        "settings_fingerprint"=>bytes2hex(sha256(codeunits(canonical_value(q8_settings(c))))))
    output = abspath(_arg_value(args, "--output", joinpath(Q3_ROOT, "outputs/sideproject_q9_fits/results.jsonl")))
    expected = Dict((String(c["cell_id"]), String(c["arm"]), String(k["candidate_id"]))=>c for c in allcells for k in c["candidates"])
    finished = Set{Tuple{String,String,String}}()
    if isfile(output)
        filesize(output) == 0 || last(read(output)) == UInt8('\n') || error("Torn JSONL")
        for row in _read_history(output)
            key = (String(row["cell_id"]), String(row["arm"]), String(row["candidate_id"]))
            haskey(expected, key) && !(key in finished) || error("Unknown/duplicate resumed candidate")
            canonical_value(row["provenance"]) == canonical_value(provenance(expected[key])) || error("Resume provenance mismatch")
            canonical_value(row["optimizer_settings"]) == canonical_value(JSON3.read(JSON3.write(json_safe(q8_settings(expected[key]))))) || error("Resume settings mismatch")
            push!(finished, key)
        end
    end
    index, systems = q5_index(index_path), wp_n25_phase_c_systems_by_id()
    for cell in cells
        sid, ic = Int(cell["system_id"]), Int(cell["initial_condition_set"])
        observed, digest = q8_read_cell(directory, directory, index[(sid, ic, Float64(cell["sigma"]), Float64(cell["rho"]), Int(cell["realization"]))])
        digest == cell["observed_data_sha256"] || error("Path/data hash mismatch")
        clean, _ = q8_read_cell(directory, directory, index[(sid, ic, 0.0, 0.0, 1)])
        test, _ = q8_read_cell(directory, directory, index[(sid, 3-ic, 0.0, 0.0, 1)])
        for (target, j) in ((clean, ic), (test, 3-ic))
            integrated = build_trajectory(systems[sid], j)
            integrated.t == target.t && integrated.x == target.x || error("Clean export differs from Q4 integration")
        end
        for candidate in cell["candidates"]
            key = (String(cell["cell_id"]), String(cell["arm"]), String(candidate["candidate_id"]))
            key in finished && continue
            result = q8_fit(cell, candidate, systems[sid], observed, clean, test)
            result["provenance"], result["optimizer_settings"] = provenance(cell), q8_settings(cell)
            result["trajectory_control"] = Dict("passed"=>true, "hash_identical"=>true)
            q5_atomic_append(output, result)
            push!(finished, key)
            println("Q9 completed $(key)")
        end
        # A cell with an empty path writes no record; mark it so completion is checkable from the log.
        isempty(cell["candidates"]) && println("Q9 empty path $(cell["cell_id"])")
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    q9_main()
end
