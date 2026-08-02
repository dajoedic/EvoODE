import Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

using JSON3

include(joinpath(@__DIR__, "run_regression.jl"))

const WP_C1_OUTPUT_DIR = joinpath(@__DIR__, "..", "..", "outputs", "studies", "regression", "wp_c1")
const WP_C1_RECORDS_PATH = joinpath(WP_C1_OUTPUT_DIR, "verification_records.json")
const WP_C1_REPORT_PATH = joinpath(@__DIR__, "..", "..", "codex", "REPORT_WP_C1b.md")

const EXPECTED_FINGERPRINT = "df5db7763bcd2449"
const EXPECTED_CAPS = Dict(
    "3" => Union{Nothing,Int}[2],
    "11" => Union{Nothing,Int}[4],
    "26" => Union{Nothing,Int}[3, 3],
    "31" => Union{Nothing,Int}[3, 3],
    "63" => Union{Nothing,Int}[nothing, nothing, nothing, nothing],
)

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

function _expected_smoke_ok(smoke)
    return get(smoke, "stage_caps", nothing) == EXPECTED_CAPS["3"] &&
           smoke["final_stage"] == 2 &&
           smoke["stage_overshoot"] == 0 &&
           smoke["loss"] == 1.3476451847014113e-08 &&
           smoke["support_terms"] == [["u1", "u1^2"]] &&
           smoke["pruned_match"] == true
end

function _expected_disabled_ok(baseline, disabled)
    return _same_values(baseline, disabled) &&
           disabled["loss"] == 4.402192340718147e-15 &&
           disabled["support_terms"] == [["u1", "u1^2", "u1^3"]]
end

function _cap_comparisons(caps)
    rows = []
    for key in sort(collect(keys(EXPECTED_CAPS)); by = x -> parse(Int, x))
        observed = caps[key]
        expected = EXPECTED_CAPS[key]
        push!(rows, (system = key, expected = expected, observed = observed, match = observed == expected))
    end
    return rows
end

function _term_names_by_eq(terms_by_eq, basis)
    return [[basis_term_name(basis, idx) for idx in terms] for terms in terms_by_eq]
end

function _coupling_inert_rows(caps)
    rows = []
    for key in sort(collect(keys(caps)); by = x -> parse(Int, x))
        system_id = parse(Int, key)
        system = _system(system_id)
        dim = Int(system[:dim])
        basis = default_staged_polynomial_basis(dim)
        basis_max_stage = EvoODE._max_stage(basis)
        system_caps = caps[key]
        effective_max = maximum(cap === nothing ? basis_max_stage : Int(cap) for cap in system_caps)

        identical = true
        details = String[]
        for stage in 1:effective_max
            eq_stages = [
                min(stage, cap === nothing ? basis_max_stage : Int(cap))
                for cap in system_caps
            ]
            allowed_with, current_with = EvoODE._evogrow_v3_equation_terms(
                basis,
                eq_stages;
                stage_caps = system_caps,
                coupling_coherence = true,
            )
            allowed_without, current_without = EvoODE._evogrow_v3_equation_terms(
                basis,
                eq_stages;
                stage_caps = system_caps,
                coupling_coherence = false,
            )
            stage_same = allowed_with == allowed_without && current_with == current_without
            identical &= stage_same
            push!(
                details,
                "stage $(stage): eq_stages=$(eq_stages), same=$(stage_same), allowed=$(_term_names_by_eq(allowed_without, basis))",
            )
        end
        push!(rows, (system = key, caps = system_caps, identical = identical, details = details))
    end
    return rows
end

function _write_report(path::String, fingerprint::String, baseline, disabled, smoke, caps, coupling_rows)
    cap_rows = _cap_comparisons(caps)
    fingerprint_ok = fingerprint == EXPECTED_FINGERPRINT
    disabled_ok = _expected_disabled_ok(baseline, disabled)
    smoke_ok = _expected_smoke_ok(smoke)
    caps_ok = all(row.match for row in cap_rows)
    coupling_ok = all(row.identical for row in coupling_rows)

    lines = String[
        "# WP-C1b Report",
        "",
        "## What Changed",
        "",
        "- Replaced the duplicated v2.2 stage-cap child-generation copy with the shared `_expand_equation_aware_with_usage_policy` implementation.",
        "- Added explicit child-generation semantics for cap-derived limits: cap-limited referenced variables do not block coupling terms in another equation.",
        "- Kept v3's default promotion-driven coupling coherence for uncapped/non-cap-derived stage differences.",
        "- `estimate_stage_caps`, `FINGERPRINT_VARIANT_LABELS`, and the `lookahead_stage_cap` fingerprint payload were not changed.",
        "",
        "## Fingerprint",
        "",
        "- `config_fingerprint()` = `$(fingerprint)`.",
        "- Expected fingerprint = `$(EXPECTED_FINGERPRINT)`.",
        "- Match: `$(fingerprint_ok)`.",
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
        "Expected-value check: `$(disabled_ok)`.",
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
        "Expected-value check: `$(smoke_ok)`.",
        "",
        "## Confirmed Cap Values",
        "",
        "| system | expected | observed | match |",
        "| --- | --- | --- | --- |",
    ]

    for row in cap_rows
        push!(lines, "| $(row.system) | $(row.expected) | $(row.observed) | $(row.match) |")
    end

    append!(
        lines,
        [
            "",
            "Cap comparison check: `$(caps_ok)`.",
            "",
            "## Coupling-Term Rule Inertness",
            "",
            "| system | caps | coherent vs cap-derived availability identical |",
            "| --- | --- | --- |",
        ],
    )

    for row in coupling_rows
        push!(lines, "| $(row.system) | $(row.caps) | $(row.identical) |")
    end

    append!(
        lines,
        [
            "",
            "Coupling-inertness check: `$(coupling_ok)`.",
            "",
            "### Coupling Details",
            "",
        ],
    )

    for row in coupling_rows
        push!(lines, "System $(row.system):")
        for detail in row.details
            push!(lines, "- $(detail)")
        end
        push!(lines, "")
    end

    append!(
        lines,
        [
            "## Overall",
            "",
            "- All checks passed: `$(fingerprint_ok && disabled_ok && smoke_ok && caps_ok && coupling_ok)`.",
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
    coupling_rows = _coupling_inert_rows(caps)

    payload = Dict(
        "fingerprint" => fingerprint,
        "cap_disabled_baseline" => _record_summary(baseline),
        "cap_disabled_variant" => _record_summary(disabled),
        "cap_enabled_smoke" => _record_summary(smoke),
        "confirmed_caps" => caps,
        "coupling_inertness" => coupling_rows,
    )

    open(WP_C1_RECORDS_PATH, "w") do io
        JSON3.pretty(io, payload)
    end

    _write_report(WP_C1_REPORT_PATH, fingerprint, baseline, disabled, smoke, caps, coupling_rows)
    println("Wrote $(WP_C1_RECORDS_PATH)")
    println("Wrote $(WP_C1_REPORT_PATH)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
