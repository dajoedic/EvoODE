using Dates
using JSON3

include(joinpath(@__DIR__, "..", "output_path_guard.jl"))

const OUTPUT_DIR = study_resolve_output_dir(joinpath(@__DIR__, "..", "..", "outputs", "studies", "gate2_do_or_die"), ARGS)
const DEFAULT_HISTORY_PATH = joinpath(@__DIR__, "..", "regression", "history.jsonl")

const GATE2_ANCHOR = (
    variant = "evogrow_v2_2_stage_local",
    config_fingerprint = "0c739d4e36ee6498",
    system_id = 26,
    seed = 42,
    loss = 0.001391623174905009,
    final_stage = 5,
    stage_overshoot = 2,
    wasted_levels = 8,
    du1_support = ["u1", "u1^2", "u1*u2"],
    du2_support = ["u1", "u1^2"],
)

const GATE2_V3_RESULT = (
    variant = "evogrow_v3",
    loss = 2.5195575964774715e-4,
    eq_final_stages = [5, 5],
    eq_overshoot = [2, 2],
)

const SYSTEM26_EXPECTED_STAGE = 3
const SYSTEM26_EXPECTED_CAP = [3, 3]
const SYSTEM26_DU1_TRUTH = ["u1", "u1^2", "u1*u2"]
const SYSTEM26_DU2_TRUTH = ["u2", "u1*u2", "u2^2"]

function _record_get(record, key::String, default = nothing)
    if record isa AbstractDict
        return get(record, key, default)
    end

    sym = Symbol(key)
    return hasproperty(record, sym) ? getproperty(record, sym) : default
end

function _support_set(values)
    values === nothing && return Set{String}()
    return Set(String.(collect(values)))
end

function _eq_support(record, eq_idx::Int)
    supports = _record_get(record, "support_terms")
    supports === nothing && error("Record is missing support_terms")
    return collect(supports[eq_idx])
end

function evaluate_gate2_record(record)
    eq_final_stages = collect(_record_get(record, "eq_final_stages", Int[]))
    eq_overs = _record_get(record, "eq_overshoot")
    if eq_overs === nothing && !isempty(eq_final_stages)
        eq_overs = [max(0, Int(stage) - SYSTEM26_EXPECTED_STAGE) for stage in eq_final_stages]
    else
        eq_overs = eq_overs === nothing ? nothing : collect(eq_overs)
    end

    eq_wasted = _record_get(record, "eq_wasted_levels")
    eq_wasted = eq_wasted === nothing ? nothing : collect(eq_wasted)

    du1_support = _eq_support(record, 1)
    du2_support = _eq_support(record, 2)
    loss = Float64(_record_get(record, "loss", Inf))

    construction_check = collect(Int.(eq_final_stages)) == SYSTEM26_EXPECTED_CAP
    du1_exact = _support_set(du1_support) == _support_set(SYSTEM26_DU1_TRUTH)
    du2_exact = _support_set(du2_support) == _support_set(SYSTEM26_DU2_TRUTH)
    loss_vs_anchor = loss < GATE2_ANCHOR.loss ? "better" : (loss == GATE2_ANCHOR.loss ? "equal" : "worse")
    loss_vs_v3 = loss < GATE2_V3_RESULT.loss ? "better" : (loss == GATE2_V3_RESULT.loss ? "equal" : "worse")

    verdict = construction_check ? "REPORTABLE" : "IMPLEMENTATION_CHECK_FAILED"

    du2_anchor_support = _support_set(GATE2_ANCHOR.du2_support)
    du2_truth_support = _support_set(SYSTEM26_DU2_TRUTH)
    du2_support_set = _support_set(du2_support)

    return Dict{String, Any}(
        "verdict" => verdict,
        "checks" => Dict(
            "construction_eq_final_stages_match_cap" => construction_check,
            "du1_support_exact" => du1_exact,
            "du2_support_exact" => du2_exact,
            "loss_vs_v2_2_anchor" => loss_vs_anchor,
            "loss_vs_v3_gate2" => loss_vs_v3,
        ),
        "anchor" => Dict(
            "variant" => GATE2_ANCHOR.variant,
            "config_fingerprint" => GATE2_ANCHOR.config_fingerprint,
            "system_id" => GATE2_ANCHOR.system_id,
            "seed" => GATE2_ANCHOR.seed,
            "loss" => GATE2_ANCHOR.loss,
            "final_stage" => GATE2_ANCHOR.final_stage,
            "stage_overshoot" => GATE2_ANCHOR.stage_overshoot,
            "wasted_levels" => GATE2_ANCHOR.wasted_levels,
            "du1_support" => GATE2_ANCHOR.du1_support,
            "du2_support" => GATE2_ANCHOR.du2_support,
        ),
        "v3" => Dict(
            "variant" => _record_get(record, "variant"),
            "config_fingerprint" => _record_get(record, "config_fingerprint"),
            "system_id" => _record_get(record, "system_id"),
            "seed" => _record_get(record, "seed"),
            "loss" => loss,
            "final_stage" => _record_get(record, "final_stage"),
            "eq_final_stages" => eq_final_stages,
            "eq_overshoot" => eq_overs,
            "eq_wasted_levels" => eq_wasted,
            "du1_support" => du1_support,
            "du2_support" => du2_support,
        ),
        "v3_gate2" => Dict(
            "variant" => GATE2_V3_RESULT.variant,
            "loss" => GATE2_V3_RESULT.loss,
            "eq_final_stages" => GATE2_V3_RESULT.eq_final_stages,
            "eq_overshoot" => GATE2_V3_RESULT.eq_overshoot,
        ),
        "diagnostics" => Dict(
            "du2_support_changed_from_anchor" => du2_support_set != du2_anchor_support,
            "du2_support_exact_truth" => du2_support_set == du2_truth_support,
            "stage_caps" => _record_get(record, "stage_caps"),
            "total_ode_solves" => _record_get(record, "total_ode_solves"),
            "total_parameter_fits" => _record_get(record, "total_parameter_fits"),
        ),
    )
end

function _matching_gate2_record(record)
    return _record_get(record, "variant") == "evogrow_v3_stage_capped" &&
           Int(_record_get(record, "system_id", -1)) == 26 &&
           Int(_record_get(record, "seed", -1)) == 42 &&
           _record_get(record, "error") === nothing &&
           _record_get(record, "support_terms") !== nothing
end

function load_latest_gate2_record(history_path::String)
    latest = nothing
    open(history_path, "r") do io
        for line in eachline(io)
            isempty(strip(line)) && continue
            record = JSON3.read(line)
            if _matching_gate2_record(record)
                latest = record
            end
        end
    end
    latest === nothing && error("No evogrow_v3_stage_capped System 26 Seed 42 record with support_terms found in $(history_path)")
    return latest
end

function write_gate2_outputs(result; output_dir::String = OUTPUT_DIR)
    mkpath(output_dir)
    json_path = joinpath(output_dir, "gate2_do_or_die.json")
    md_path = joinpath(output_dir, "gate2_do_or_die.md")

    open(json_path, "w") do io
        JSON3.write(io, result)
        write(io, '\n')
    end

    checks = result["checks"]
    anchor = result["anchor"]
    v3_gate2 = result["v3_gate2"]
    v3 = result["v3"]
    diagnostics = result["diagnostics"]

    open(md_path, "w") do io
        println(io, "# Gate 2 Do-or-Die Readout")
        println(io)
        println(io, "- Verdict: **$(result["verdict"])**")
        println(io, "- Generated: $(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"))")
        println(io)
        println(io, "## Anchor v2.2")
        println(io, "- loss: $(anchor["loss"])")
        println(io, "- final_stage: $(anchor["final_stage"])")
        println(io, "- stage_overshoot: $(anchor["stage_overshoot"])")
        println(io, "- wasted_levels: $(anchor["wasted_levels"])")
        println(io, "- du1_support: $(anchor["du1_support"])")
        println(io, "- du2_support: $(anchor["du2_support"])")
        println(io)
        println(io, "## Frozen EvoGrowV3 Gate-2")
        println(io, "- loss: $(v3_gate2["loss"])")
        println(io, "- eq_final_stages: $(v3_gate2["eq_final_stages"])")
        println(io, "- eq_overshoot: $(v3_gate2["eq_overshoot"])")
        println(io)
        println(io, "## Capped Variant")
        println(io, "- loss: $(v3["loss"])")
        println(io, "- final_stage: $(v3["final_stage"])")
        println(io, "- eq_final_stages: $(v3["eq_final_stages"])")
        println(io, "- eq_overshoot: $(v3["eq_overshoot"])")
        println(io, "- eq_wasted_levels: $(v3["eq_wasted_levels"])")
        println(io, "- du1_support: $(v3["du1_support"])")
        println(io, "- du2_support: $(v3["du2_support"])")
        println(io)
        println(io, "## Checks")
        println(io, "- Construction eq_final_stages == $(SYSTEM26_EXPECTED_CAP): $(checks["construction_eq_final_stages_match_cap"] ? "PASS" : "FAIL")")
        println(io, "- du1 support exact: $(checks["du1_support_exact"])")
        println(io, "- du2 support exact: $(checks["du2_support_exact"])")
        println(io, "- loss vs v2.2 anchor: $(checks["loss_vs_v2_2_anchor"])")
        println(io, "- loss vs v3 Gate-2: $(checks["loss_vs_v3_gate2"])")
        println(io, "The forced stage cap is a construction check only, not a success criterion.")
        println(io)
        println(io, "## Diagnostics")
        println(io, "- du2_support_changed_from_anchor: $(diagnostics["du2_support_changed_from_anchor"])")
        println(io, "- du2_support_exact_truth: $(diagnostics["du2_support_exact_truth"])")
        println(io, "- stage_caps: $(diagnostics["stage_caps"])")
        println(io, "- total_ode_solves: $(diagnostics["total_ode_solves"])")
        println(io, "- total_parameter_fits: $(diagnostics["total_parameter_fits"])")
    end

    return (json_path = json_path, md_path = md_path)
end

function main()
    history_path = get(ENV, "GATE2_HISTORY_PATH", DEFAULT_HISTORY_PATH)
    record = load_latest_gate2_record(history_path)
    result = evaluate_gate2_record(record)
    paths = write_gate2_outputs(result)
    println("Gate 2 verdict: $(result["verdict"])")
    println("Wrote $(paths.json_path)")
    println("Wrote $(paths.md_path)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
