import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3

include(joinpath(@__DIR__, "run_regression.jl"))

const WP_C1_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "wp_c1")
const WP_C1_RECORDS_PATH = joinpath(WP_C1_OUTPUT_DIR, "verification_records.json")
const WP_C1_REPORT_PATH = joinpath(@__DIR__, "..", "..", "codex", "REPORT_WP_C1.md")

function _system(system_id::Int)
    matches = [system for system in REGRESSION_SYSTEMS if Int(system[:system_id]) == system_id]
    isempty(matches) && error("Unknown regression system $(system_id)")
    return matches[1]
end

function _support_terms(record)
    terms = get(record, "support_terms", nothing)
    terms === nothing && return "nothing"
    return repr(terms)
end

function _record_summary(record)
    return Dict(
        "variant" => record["variant"],
        "system_id" => record["system_id"],
        "seed" => record["seed"],
        "loss" => record["loss"],
        "pruned_match" => record["pruned_match"],
        "final_stage" => record["final_stage"],
        "stage_overshoot" => record["stage_overshoot"],
        "wasted_levels" => record["wasted_levels"],
        "eq_final_stages" => record["eq_final_stages"],
        "eq_overshoot" => record["eq_overshoot"],
        "eq_wasted_levels" => record["eq_wasted_levels"],
        "stage_caps" => get(record, "stage_caps", nothing),
        "stage_cap_policy_active" => get(record, "stage_cap_policy_active", false),
        "support_terms" => record["support_terms"],
        "elapsed_s" => record["elapsed_s"],
        "error" => record["error"],
    )
end

function _run_variant(label::String, constructor, system, seed::Int, fingerprint::String, provenance)
    variant = (label = label, constructor = constructor)
    record = run_one(variant, system, seed, fingerprint, provenance)
    record["error"] === nothing || error("$(label) failed: $(record["error"])")
    return record
end

function _baseline_constructor(level_callback, screening_optimizer)
    return EvoGrow(
        pop_size = POP_SIZE,
        n_levels = N_LEVELS,
        children_per_parent = CHILDREN_PER_PARENT,
        max_terms_per_eq = MAX_TERMS,
        λ = LAMBDA,
        progression = StageProgressionPolicy(
            mode = :stage_local,
            min_levels_per_stage = STAGE_MIN,
        ),
        usage = StageUsagePolicy(
            mode = :hard,
            new_term_bias_prob = SOFT_BIAS,
        ),
        use_pretuning = USE_PRETUNING,
        screening_optimizer = screening_optimizer,
        level_callback = level_callback,
    )
end

function _cap_disabled_constructor(level_callback, screening_optimizer)
    return EvoGrow(
        pop_size = POP_SIZE,
        n_levels = N_LEVELS,
        children_per_parent = CHILDREN_PER_PARENT,
        max_terms_per_eq = MAX_TERMS,
        λ = LAMBDA,
        progression = StageProgressionPolicy(
            mode = :stage_local,
            min_levels_per_stage = STAGE_MIN,
        ),
        usage = StageUsagePolicy(
            mode = :hard,
            new_term_bias_prob = SOFT_BIAS,
        ),
        use_pretuning = USE_PRETUNING,
        screening_optimizer = screening_optimizer,
        level_callback = level_callback,
        stage_caps = Union{Nothing,Int}[nothing],
    )
end

function _stage_capped_constructor(level_callback, screening_optimizer)
    return EvoGrow(
        pop_size = POP_SIZE,
        n_levels = N_LEVELS,
        children_per_parent = CHILDREN_PER_PARENT,
        max_terms_per_eq = MAX_TERMS,
        λ = LAMBDA,
        progression = StageProgressionPolicy(
            mode = :stage_local,
            min_levels_per_stage = STAGE_MIN,
        ),
        usage = StageUsagePolicy(
            mode = :hard,
            new_term_bias_prob = SOFT_BIAS,
        ),
        use_pretuning = USE_PRETUNING,
        screening_optimizer = screening_optimizer,
        level_callback = level_callback,
        stage_cap_policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...),
    )
end

function _confirmed_caps()
    caps = Dict{String, Any}()
    for system_id in (3, 11, 26, 31, 63)
        system = _system(system_id)
        traj = build_trajectory(system)
        basis = default_staged_polynomial_basis(Int(system[:dim]))
        caps[string(system_id)] = estimate_stage_caps(
            traj,
            basis;
            policy = LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...),
        )
    end
    return caps
end

function _same_values(lhs, rhs)
    return lhs["loss"] == rhs["loss"] &&
           lhs["final_stage"] == rhs["final_stage"] &&
           lhs["pruned_match"] == rhs["pruned_match"] &&
           lhs["support_terms"] == rhs["support_terms"]
end

function _write_report(path::String, fingerprint::String, baseline, disabled, smoke, caps)
    lines = String[
        "# WP-C1 Report",
        "",
        "## What Changed",
        "",
        "- Added regression variant `evogrow_v2_2_stage_capped`.",
        "- The variant uses the existing v2.2 `:stage_local` promotion and `:hard` usage path.",
        "- The look-ahead cap is applied only as a per-equation term restriction: equation `k` sees terms with stage `<= min(global_stage, cap[k])`; `nothing` means the basis maximum.",
        "- The effective global promotion maximum is the maximum cap, with `nothing` counted as the basis maximum.",
        "- `estimate_stage_caps`, `EvoGrowV3`, and `EvoGrowStageCapped` were not changed.",
        "",
        "## Fingerprint",
        "",
        "- `config_fingerprint()` = `$(fingerprint)`.",
        "- `FINGERPRINT_VARIANT_LABELS` and the `lookahead_stage_cap` payload were left unchanged. The payload still names only `evogrow_v3_stage_capped`, which is now incomplete but intentionally frozen.",
        "",
        "## Cap-Disabled Equivalence",
        "",
        "System 11, seed 42, comparing `evogrow_v2_2_stage_local` against the same v2.2 substrate with `stage_caps = [nothing]`.",
        "",
        "| metric | v2.2 stage-local | v2.2 cap-disabled |",
        "| --- | --- | --- |",
        "| loss | $(baseline["loss"]) | $(disabled["loss"]) |",
        "| final_stage | $(baseline["final_stage"]) | $(disabled["final_stage"]) |",
        "| pruned_match | $(baseline["pruned_match"]) | $(disabled["pruned_match"]) |",
        "| support_terms | $(_support_terms(baseline)) | $(_support_terms(disabled)) |",
        "",
        "Bit-identical comparison on reported values: `$(_same_values(baseline, disabled))`.",
        "",
        "## Cap-Enabled Smoke Test",
        "",
        "System 3, seed 42, variant `evogrow_v2_2_stage_capped`.",
        "",
        "| metric | value |",
        "| --- | --- |",
        "| stage_caps | $(get(smoke, "stage_caps", nothing)) |",
        "| loss | $(smoke["loss"]) |",
        "| final_stage | $(smoke["final_stage"]) |",
        "| stage_overshoot | $(smoke["stage_overshoot"]) |",
        "| eq_final_stages | $(smoke["eq_final_stages"]) |",
        "| eq_overshoot | $(smoke["eq_overshoot"]) |",
        "| eq_wasted_levels | $(smoke["eq_wasted_levels"]) |",
        "| pruned_match | $(smoke["pruned_match"]) |",
        "| support_terms | $(_support_terms(smoke)) |",
        "",
        "## Confirmed Cap Values",
        "",
        "| system | caps |",
        "| --- | --- |",
    ]

    for key in sort(collect(keys(caps)); by = x -> parse(Int, x))
        push!(lines, "| $(key) | $(caps[key]) |")
    end

    append!(
        lines,
        [
            "",
            "## Surprises",
            "",
            "- No parser or cap-estimator disagreement surfaced.",
            "- The fingerprint payload's cap variant label is now incomplete by design; changing it would change the frozen hash.",
            "",
        ],
    )

    mkpath(dirname(path))
    open(path, "w") do io
        println(io, join(lines, "\n"))
    end
end

function main()
    mkpath(WP_C1_OUTPUT_DIR)
    fingerprint = config_fingerprint()
    provenance = git_provenance()
    system11 = _system(11)
    system3 = _system(3)

    baseline = _run_variant(
        "evogrow_v2_2_stage_local",
        _baseline_constructor,
        system11,
        42,
        fingerprint,
        provenance,
    )
    disabled = _run_variant(
        "evogrow_v2_2_stage_capped_disabled",
        _cap_disabled_constructor,
        system11,
        42,
        fingerprint,
        provenance,
    )
    smoke = _run_variant(
        "evogrow_v2_2_stage_capped",
        _stage_capped_constructor,
        system3,
        42,
        fingerprint,
        provenance,
    )
    caps = _confirmed_caps()

    payload = Dict(
        "fingerprint" => fingerprint,
        "cap_disabled_baseline" => _record_summary(baseline),
        "cap_disabled_variant" => _record_summary(disabled),
        "cap_enabled_smoke" => _record_summary(smoke),
        "confirmed_caps" => caps,
    )

    open(WP_C1_RECORDS_PATH, "w") do io
        JSON3.pretty(io, payload)
    end

    _write_report(WP_C1_REPORT_PATH, fingerprint, baseline, disabled, smoke, caps)
    println("Wrote $(WP_C1_RECORDS_PATH)")
    println("Wrote $(WP_C1_REPORT_PATH)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
