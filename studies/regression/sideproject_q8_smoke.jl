# Run explicitly on Julia 1.12.6; no campaign or cluster work.
include(joinpath(@__DIR__, "sideproject_q8_fits.jl"))

function q8_bit_equal(a, b)
    # Compare as written to a record: the runner serializes with JSON3.write(json_safe(row)),
    # so e.g. the sentinel 1.0e6 is stored as 1000000 and NaN as null.
    as_record(x) = canonical_value(JSON3.read(JSON3.write(json_safe(x))))
    return as_record(a) == as_record(b)
end

function q8_smoke(args=ARGS)
    VERSION == v"1.12.6" || error("Julia 1.12.6 required")
    smoke = JSON3.read(read(joinpath(Q3_ROOT, "outputs/sideproject_q8_inputs/smoke.json"), String))
    export_dir = joinpath(Q3_ROOT, "outputs/phase_c_c6_data_conditions_5dd1df8")
    index, systems = q5_index(joinpath(export_dir, "index.csv")), wp_n25_phase_c_systems_by_id()
    count = 0
    for cell in smoke["cells"]
        sid, ic = Int(cell["system_id"]), Int(cell["initial_condition_set"])
        observed, _ = q5_read_cell(export_dir, index[(sid,ic,Float64(cell["sigma"]),Float64(cell["rho"]),1)])
        clean, _ = q5_read_cell(export_dir, index[(sid,ic,0.0,0.0,1)])
        test, _ = q5_read_cell(export_dir, index[(sid,3-ic,0.0,0.0,1)])
        originals = Dict(String(r["candidate_id"])=>r for r in _read_history(joinpath(Q3_ROOT, String(cell["record_path"]))))
        for k in vcat(collect(cell["candidates"]),collect(cell["upper_candidates"]))
            old = originals[String(k["candidate_id"])]
            current = q5_fit(cell,k,systems[sid],observed,clean,test)
            for field in ("params","optimizer_loss","pruned_active_idxs","training","reconstruction","generalization","clean_ic_observed_mse")
                q8_bit_equal(current[field],old[field]) || error("Default bit control failed: $(cell["cell_id"]) $(k["candidate_id"]) $field")
            end
            c = Dict{String,Any}(String(key)=>value for (key,value) in pairs(cell))
            merge!(c,Dict("arm"=>"C10","ic_mode"=>"estimated","coefficient_bound"=>10,"start"=>"weak","refit"=>true))
            fixed = q8_fit(c,k,systems[sid],observed,clean,test; fixed_ic=true)
            for field in ("params","optimizer_loss","pruned_active_idxs","training","reconstruction","generalization","clean_ic_observed_mse")
                q8_bit_equal(fixed[field],current[field]) || error("Fixed IC bit control failed: $field")
            end
            # Optimizer metadata must match apart from measured wall-clock times.
            for field in keys(current["fit_meta"])
                field in (:solve_time_s,:fit_time_s) && continue
                q8_bit_equal(getproperty(current["fit_meta"],field),getproperty(fixed["fit_meta"],field)) || error("Fit meta differs: $field")
            end
            count += 1
        end
    end
    folder = joinpath(Q3_ROOT,"outputs/sideproject_q8_smoke")
    mkpath(folder)
    result = Dict("passed"=>true,"cells"=>length(smoke["cells"]),"candidates"=>count,
        "default_bit_control"=>true,"fixed_ic_bit_control"=>true,
        "source_sha256"=>Dict(name=>q3_hash(joinpath(Q3_ROOT,name)) for name in (
            "src/optimize/bfgs.jl", "studies/regression/sideproject_q8_fits.jl", "studies/regression/sideproject_q8_smoke.jl")))
    open(joinpath(folder,"controls.json"),"w") do io; JSON3.write(io,result); end
    println("Q8 smoke controls passed: $count candidates")
end

if abspath(PROGRAM_FILE) == @__FILE__
    q8_smoke()
end
