# WP-P1 Report - Behavior Fingerprint for Stage-Cap Logic

## Design comparison

### Source hash over decision-bearing files

Scope: hash files such as `src/structure/stage_cap.jl` and include the digest in records.

Recognizes: any textual change to the hashed files, including logic changes in `_cap_split_decision`.

Does not recognize: behavioral changes outside the selected file set, unless the boundary is kept
complete. It also does not say which behavior changed.

False alarms: high. Comments, whitespace, import ordering, and mechanical refactors change the hash
even when all decisions stay identical.

Operational cost: low at runtime, but high in maintenance. The file boundary must be curated, and
benign edits create new record groups.

Existing 42 pilot records: they do not carry a source hash. They would remain legacy records and
could not be made comparable to records produced after introducing this field without either
backfilling from their git hashes or marking them as pre-source-fingerprint records.

Verdict: precise for text provenance, too sensitive for the campaign comparability question.

### Behavior hash over a frozen probe

Scope: run a fixed, versioned set of synthetic decision inputs through `_cap_split_decision` and
hash the canonicalized outputs.

Recognizes: changes that affect the probed decision behavior. The WP-C4 floor-crossing logic is in
scope because the probe includes the three post-floor outcomes: reopen, cap, and abstain.

Does not recognize: behavior changes outside the probe boundary, and changes to `estimate_stage_caps`
that do not pass through `_cap_split_decision`.

False alarms: low for comments and formatting because source text is not hashed. A false alarm
occurs only if the probe definition or observed outputs change.

Operational cost: very low. The current probe evaluates five small vectors and performs no ODE
solve, no structure search, no campaign run, and no manifest generation.

Probe freezing and versioning: the probe payload contains
`STAGE_CAP_BEHAVIOR_FINGERPRINT_VERSION = 1`, the target name `_cap_split_decision`, the policy
values used for the probe, all synthetic inputs, and all decisions. If the probe is extended, the
version must be incremented and the new value intentionally starts a new behavior-fingerprint era.

Existing 42 pilot records: they have no behavior fingerprint. They should be treated as legacy
records with `stage_cap_behavior_fingerprint` missing. They can still be audited by git hash and
the old config fingerprint, but they must not be claimed to share the new behavior fingerprint.

Verdict: best match for the defect. It is insensitive to formatting and sensitive to the specific
logic behavior that the old config fingerprints missed.

### Separate second fingerprint

Scope: keep `config_fingerprint` and `phase_b_fingerprint` unchanged and add a second behavior
fingerprint field to each record.

Recognizes: configuration changes and behavior changes as separate axes.

Does not recognize: a single scalar identity unless downstream checks explicitly require both
fingerprints.

False alarms: lower than folding behavior into the config fingerprint. A behavior-only change does
not rewrite the configuration identity, and a configuration-only change does not imply a behavior
change.

Operational cost: low. Record checks must compare `(config_fingerprint,
stage_cap_behavior_fingerprint)` for capped campaign comparability.

Existing 42 pilot records: legacy records have the config fingerprint only. They are distinguishable
from new records because the behavior field is absent. They should not be merged into a
post-WP-P1 campaign block.

Verdict: this is the recommended structure, implemented with the behavior-probe hash above.

## Recommendation

Use a separate behavior fingerprint derived from a frozen probe. The campaign identity should be
read as two fields: the existing configuration fingerprint plus
`stage_cap_behavior_fingerprint`. This preserves the existing published config values, avoids
source-hash false alarms, and detects the WP-C4 class of decision change.

## Implementation

Added `src/structure/stage_cap_fingerprint.jl` and exported
`stage_cap_behavior_fingerprint()` from `src/EvoODE.jl`.

The function hashes a canonical payload containing:

- `version = 1`
- `target = "_cap_split_decision"`
- the fixed `LookAheadStageCapPolicy` values used for the probe
- five synthetic split-decision probes and their returned decisions

`studies/regression/run_regression.jl` now writes
`"stage_cap_behavior_fingerprint"` into every `run_one` record and heartbeat context. Because
`run_batch_cell.jl` and `run_k8s_indexed_cell.jl` both call `run_one`, Phase B task records receive
the same field without changing manifests.

The existing config fingerprints are unchanged:

| Function | Value after WP-P1 |
|---|---|
| `config_fingerprint()` | `1d0ccf8d53c6576d` |
| `phase_b_fingerprint()` | `e361a2af49366670` |
| `stage_cap_behavior_fingerprint()` | `61b6548ef0014593` |

## Acceptance evidence

Reproducibility on the same code state:

| Calculation | Value |
|---|---|
| first `stage_cap_behavior_fingerprint()` | `61b6548ef0014593` |
| second `stage_cap_behavior_fingerprint()` | `61b6548ef0014593` |

Behavior change against `5d2f4f2`:

| State | Value |
|---|---|
| temporary `src/structure/stage_cap.jl` from `5d2f4f2` | `b0968d0661a11a29` |
| restored current `src/structure/stage_cap.jl` | `61b6548ef0014593` |

Restoration check for the temporary checkout:

| Check | Value |
|---|---|
| current file SHA-256 before temporary old-file swap | `440DBF6BFB0A597F5F3F35E148CD55A3AA07BB4A9637A1FA6F397F6CFA912110` |
| temporary old-file SHA-256 | `DB35931CD705120EDD9CE0AF62BA8CBC2AE26DC3443A6F201593EDDC0F60402E` |
| current file SHA-256 after restore | `440DBF6BFB0A597F5F3F35E148CD55A3AA07BB4A9637A1FA6F397F6CFA912110` |
| restored | `true` |

Comment-only change:

| Check | Value |
|---|---|
| current file SHA-256 before comment probe | `440DBF6BFB0A597F5F3F35E148CD55A3AA07BB4A9637A1FA6F397F6CFA912110` |
| comment-probe file SHA-256 | `CB9677A953A336FA11758B4CAD0D0F9CD3A67187C06403E16D8B5B4D3E765DF7` |
| fingerprint before comment probe | `61b6548ef0014593` |
| fingerprint after comment probe | `61b6548ef0014593` |
| current file SHA-256 after restore | `440DBF6BFB0A597F5F3F35E148CD55A3AA07BB4A9637A1FA6F397F6CFA912110` |
| restored | `true` |

Focused test run:

| Command | Result |
|---|---|
| `julia --project=. test/test_stage_cap.jl` | pass, 38 tests |
| `julia --project=. test/test_regression_runner_gate2.jl` | fail, 6 passed / 3 failed |

The regression-runner failures are stale expectations unrelated to WP-P1:
`VARIANTS` now contains `evogrow_v2_2_stage_capped`, `BFGS_TIME_LIMIT_S` is `Inf`, and
`LOOKAHEAD_CAP_POLICY.lookahead_horizon` is `5` while the test still expects the old Gate-2 values.

## Documentation follow-up for Claude

Do not edit these in WP-P1; update them after review:

- `docs/hpc_requirements.md` section 7: replace "git commit hash and a configuration fingerprint"
  with a statement that each job records git hash, configuration fingerprint, and
  `stage_cap_behavior_fingerprint`.
- `docs/hpc_requirements.md` section 7: replace "mixed hashes" with the explicit publishability
  rule that a campaign must share one git hash, one configuration fingerprint, and one behavior
  fingerprint.
- `CLAUDE.md` codex convention / provenance wording: mention that `STATUS.md` reports WP results
  only; campaign provenance is now in records as config plus behavior fingerprints.
- `CLAUDE.md` Current Priorities, "Fingerprint boundary": add the current behavior fingerprint
  `61b6548ef0014593` and state that the 42 pilot records predate it.
- `CLAUDE.md` Paper 1 final paragraph: change "one git commit hash and one config_fingerprint" to
  "one git commit hash, one config_fingerprint or phase_b_fingerprint as applicable, and one
  stage_cap_behavior_fingerprint".

