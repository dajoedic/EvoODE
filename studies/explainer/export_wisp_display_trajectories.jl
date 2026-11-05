# Display evaluation only. Including the frozen runner defines its functions;
# its PROGRAM_FILE guard prevents fitting. Never call q5_main or q5_fit here.
include(joinpath(@__DIR__, "..", "regression", "sideproject_q5_noise_fits.jl"))

function display_csv(path)
    lines = readlines(path)
    header = q5_csv_record(first(lines))
    return [Dict(zip(header, q5_csv_record(line))) for line in lines[2:end]]
end

function display_target(f!, params, target, optimizer, options)
    scores = q4_evaluate(f!, params, target, optimizer, options)
    # q4_evaluate does not return its prediction. Repeat exactly its simulate call.
    predicted = simulate(f!, params, target; abstol=optimizer.abstol, reltol=optimizer.reltol,
        maxiters=optimizer.maxiters_solve, clamp_val=optimizer.clamp_val,
        reject_nonfinite=optimizer.reject_nonfinite, divergence_limit=optimizer.divergence_limit,
        options=options)
    return Dict("t"=>target.t, "truth"=>[collect(r) for r in eachrow(target.x)],
        "model"=>[collect(r) for r in eachrow(predicted)],
        "scores"=>Dict("arithmetic"=>scores["r2_arithmetic"],
                       "variance_weighted"=>scores["r2_variance_weighted"]))
end

# The regression logger encodes nonfinite numbers as strings. This display format
# uses JSON null so readers can withhold failed curves without parsing sentinels.
function display_safe(value)
    value isa AbstractFloat && return isfinite(value) ? value : nothing
    value isa AbstractDict && return Dict(k=>display_safe(v) for (k,v) in value)
    value isa AbstractVector && return [display_safe(v) for v in value]
    return value
end

function display_main(args=ARGS)
    VERSION == v"1.12.6" || error("Display evaluation requires Julia 1.12.6")
    root = Q3_ROOT
    q7 = "--q7-examples" in args
    prefix = q7 ? "q7" : "q5"
    grid = joinpath(root,"analysis/data/sideproject_residual_growth/"*prefix*"_grid")
    directory = joinpath(root,"outputs/phase_c_c6_data_conditions_5dd1df8")
    payload = JSON3.read(read(joinpath(root,"outputs/sideproject_q5_inputs/q5_grid_paths.json"),String))
    index_path = joinpath(directory,"index.csv")
    q3_hash(index_path) == String(payload["input_sha256"]["outputs/phase_c_c6_data_conditions_5dd1df8/index.csv"]) || error("Export index changed")
    index = q5_index(index_path)
    units = filter(r->r["size_rule"]=="c",display_csv(joinpath(grid,prefix*"_units.csv")))
    candidates = display_csv(joinpath(grid,prefix*"_candidates.csv"))
    if q7
        requested = split(_arg_value(args,"--cells","sys0027_ic1_s0.03_r0_n1,sys0003_ic2_s0.03_r0_n1"),',')
        length(Set(requested)) == length(requested) || error("Duplicate named cell")
        available = Set(r["cell_id"] for r in units)
        all(cid->cid in available,requested) || error("Unknown named Q7 cell")
        units = [only(filter(r->r["cell_id"]==cid,units)) for cid in requested]
    end
    manifest = JSON3.read(read(joinpath(root,"explainer/wisp/data/manifest.json"),String))
    featured = Set(String(v) for v in values(manifest["featured_selection"]["cells"]))
    cells = Dict(String(c["cell_id"])=>c for c in payload["cells"])
    systems = wp_n25_phase_c_systems_by_id()
    limit = wp_n25_parse_limit(args,length(units))
    output = abspath(_arg_value(args,"--output",joinpath(root,"outputs/wisp_explainer_julia/"*(q7 ? "q7_examples.jsonl" : "trajectories.jsonl"))))
    allowed = abspath(joinpath(root,"outputs/wisp_explainer_julia"))
    relative = relpath(output,allowed)
    (relative == ".." || startswith(relative,"../") || startswith(relative,"..\\") || isabspath(relative)) && error("Output outside display directory")
    mkpath(dirname(output))
    optimizer, options = build_reference_optimizer(max_fit_attempts=1), build_options(Q3_SEED)
    source_units_hash = q3_hash(joinpath(grid,prefix*"_units.csv"))
    source_candidates_hash = q3_hash(joinpath(grid,prefix*"_candidates.csv"))
    target_cache = Dict{Tuple{Int,Int},Trajectory}()
    function clean_target(sid, ic)
        return get!(target_cache, (sid, ic)) do
            target, _ = q5_read_cell(directory,index[(sid,ic,0.0,0.0,1)])
            integrated = build_trajectory(systems[sid],ic)
            integrated.t == target.t && integrated.x == target.x || error("Clean target mismatch")
            target
        end
    end
    open(output*".tmp","w") do io
        for chosen in units[1:limit]
            cid = chosen["cell_id"]
            cell = cells[cid]
            sid, ic = Int(cell["system_id"]), Int(cell["initial_condition_set"])
            path_ids = Set(String(k["candidate_id"]) for k in cell["candidates"])
            pool = q7 ? sort(filter(r->r["cell_id"]==cid && startswith(r["candidate_id"],"q7_"),candidates),by=r->parse(Int,r["step"])) :
                cid in featured ? filter(r->r["cell_id"]==cid && r["candidate_id"] in path_ids,candidates) : [chosen]
            # Stored Q5 clean reconstruction and opposite-IC targets, verified as in q5_main.
            clean, test = clean_target(sid,ic), clean_target(sid,3-ic)
            for row in pool
                record = Dict{String,Any}("cell_id"=>cid,"candidate_id"=>row["candidate_id"],
                    "source_units_sha256"=>source_units_hash,
                    "source_candidates_sha256"=>source_candidates_hash)
                try
                    active = [Int.(collect(eq)) for eq in JSON3.read(row["active_idxs"])]
                    params = Float64.(collect(JSON3.read(row["params"])))
                    f!, count, _ = build_rhs(StructureSpec(active),phase_c_basis(Int(cell["dim"])))
                    length(params) == count || error("Stored parameter count mismatch")
                    errors = Float64[]
                    for (kind,target) in (("reconstruction",clean),("generalization",test))
                        bundle = display_target(f!,params,target,optimizer,options)
                        record[kind] = bundle
                        for weight in ("arithmetic","variance_weighted")
                            stored = tryparse(Float64,row[kind*"_r2_"*weight])
                            value = bundle["scores"][weight]
                            stored !== nothing && value !== nothing && isfinite(value) || error("Missing/nonfinite score")
                            push!(errors,abs(value-stored))
                        end
                    end
                    if q7
                        # Q5/Q7 reconstruction uses the clean start. Training uses
                        # the noisy first observation; preserve both meanings.
                        observed, _ = q5_read_cell(directory,index[(sid,ic,Float64(cell["sigma"]),Float64(cell["rho"]),Int(cell["realization"]))])
                        record["training"] = display_target(f!,params,observed,optimizer,options)
                        record["true_initial"] = record["reconstruction"]
                    end
                    record["max_r2_error"] = maximum(errors)
                    record["passed"] = maximum(errors) <= 1e-12
                    record["reason"] = record["passed"] ? nothing : "R2 mismatch above 1e-12"
                catch exc
                    record["passed"] = false
                    record["reason"] = sprint(showerror,exc)
                end
                JSON3.write(io,display_safe(record)); write(io,'\n'); flush(io)
                println("Display evaluation: ",cid," / ",row["candidate_id"]," passed=",record["passed"])
            end
        end
    end
    Base.Filesystem.rename(output*".tmp",output)
end

if abspath(PROGRAM_FILE) == @__FILE__
    display_main()
end
