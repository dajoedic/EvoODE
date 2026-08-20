# src/structure/stage_cap_fingerprint.jl

using SHA

const STAGE_CAP_BEHAVIOR_FINGERPRINT_VERSION = 2

function _cap_probe_decision_payload()
    policy = LookAheadStageCapPolicy(tau_abs = 1e-6, tau_rel = 1e-4, lookahead_horizon = 5)
    probes = (
        (
            name = "late_floor_drop_reopens_walk",
            residuals = [10.0, 1.0, 0.2],
            usable = [true, true, true],
            floors = [0.1, 2.0, 2.0],
            stages = [1, 2, 3],
        ),
        (
            name = "late_floor_no_clear_drop_caps",
            residuals = [10.0, 1.0, 0.8],
            usable = [true, true, true],
            floors = [0.1, 2.0, 2.0],
            stages = [1, 2, 3],
        ),
        (
            name = "late_floor_intermediate_drop_caps",
            residuals = [10.0, 1.0, 0.5],
            usable = [true, true, true],
            floors = [0.1, 2.0, 2.0],
            stages = [1, 2, 3],
        ),
        (
            name = "near_zero_without_gain_abstains",
            residuals = [1e-12, 2e-12, 5e-13],
            usable = [true, true, true],
            floors = [1e-14, 1e-14, 1e-14],
            stages = [1, 2, 3],
        ),
        (
            name = "unusable_successor_invalidates",
            residuals = [10.0, 0.1],
            usable = [true, false],
            floors = [1e-3, 1e-3],
            stages = [1, 2],
        ),
    )
    return (
        version = STAGE_CAP_BEHAVIOR_FINGERPRINT_VERSION,
        target = "_cap_split_decision",
        policy = (
            estimator = String(policy.estimator),
            weighting = String(policy.weighting),
            aggregation = String(policy.aggregation),
            lookahead_horizon = policy.lookahead_horizon,
            tau_rel = policy.tau_rel,
            tau_abs = policy.tau_abs,
            cond_cap = policy.cond_cap,
            excitation_floor = policy.excitation_floor,
            post_floor_significant_drop_ratio = policy.post_floor_significant_drop_ratio,
            post_floor_min_floor_ratio = policy.post_floor_min_floor_ratio,
        ),
        probes = [
            (
                name = probe.name,
                residuals = probe.residuals,
                usable = probe.usable,
                floors = probe.floors,
                stages = probe.stages,
                decision = _cap_split_decision(
                    probe.residuals,
                    probe.usable,
                    probe.floors,
                    probe.stages,
                    policy,
                ),
            )
            for probe in probes
        ],
    )
end

function _cap_fingerprint_canonical_value(x)
    if x isa NamedTuple
        parts = String[]
        for key in sort(collect(keys(x)); by = string)
            push!(parts, string(key, "=", _cap_fingerprint_canonical_value(getfield(x, key))))
        end
        return "{" * join(parts, ",") * "}"
    elseif x isa Tuple
        return "(" * join(_cap_fingerprint_canonical_value.(collect(x)), ",") * ")"
    elseif x isa AbstractVector
        return "[" * join(_cap_fingerprint_canonical_value.(x), ",") * "]"
    else
        return repr(x)
    end
end

function stage_cap_behavior_fingerprint()
    bytes = sha256(codeunits(_cap_fingerprint_canonical_value(_cap_probe_decision_payload())))
    return bytes2hex(bytes)[1:16]
end
