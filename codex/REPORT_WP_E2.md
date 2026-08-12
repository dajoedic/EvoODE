# REPORT WP-E2 — The structure metric for all 63 campaign systems

Implemented directly rather than through Codex, by exception.

## Outcome

`pruned_match` was `nothing` for every Phase B system. It is now computed wherever a true support
exists: **20 of 63 systems**, with the other 43 correctly reporting `nothing`.

## Derivation method

`studies/regression/derive_phase_b_support.jl` derives the support per equation and writes
`studies/regression/phase_b_support.json`, which is committed.

The RHS is evaluated analytically from the dataset's substituted expressions and compared against the
staged polynomial basis by least squares. Two properties are required of the result:

- **Exact**: the support reproduces the RHS to `atol = rtol = 1e-9`.
- **Minimal**: no term can be dropped without breaking that. This is enforced by iteratively removing
  the smallest coefficient and refitting.

Minimality is not cosmetic. A plain threshold on least-squares coefficients returned supports of 18
and 26 terms for systems 52 and 62 — a representable RHS smeared across the basis on an
ill-conditioned design, not a true support.

**Evaluation points**: both IC trajectories plus 400 scattered points inside the visited box. A
single trajectory leaves basis columns collinear, which makes the least-squares support non-unique;
under that condition system 63 could not be derived at all. The scatter stays strictly inside the box
because leaving it exits the domain of some right-hand sides (`log`, `sqrt`), and points where the
RHS or the basis is undefined are dropped.

Precomputed rather than derived at run time: the derivation takes about 21 s for all 63 systems, and
each of the 756 campaign jobs would otherwise repeat it. `--check` re-derives and compares against the
committed file without rewriting it.

## Cross-check against the hand-encoded systems

All five diagnostic systems with a hand-encoded support are reproduced **exactly**, including system
63 in 4D:

| system | hand-encoded | derived |
|---|---|---|
| 2 | `[u1]` | `[u1]` |
| 3 | `[u1, u1^2]` | `[u1, u1^2]` |
| 11 | `[u1^3]` | `[u1^3]` |
| 26 | `[u1, u1*u2, u1^2] [u1*u2, u2, u2^2]` | identical |
| 31 | `[u1*u2] [u1*u2, u2]` | identical |
| 63 | `[u1*u3] [u1*u3, u2] [u2, u3] [u3]` | identical |

The generator fails hard on any disagreement rather than writing the table.

## Finding: representability was too permissive

Three systems — **30, 52 and 62** — were classified `exact` but have no true support in the basis.

The previous check fitted the basis along a **single trajectory**. A function can agree with a basis
representation on one curve without being that function on the state space. Scattering over the
visited box is the stricter and correct test.

The campaign therefore rests on **20 exact systems, not 23**. `representability` now comes from the
same computation as the support, so "exact" and "a true support exists" are one statement instead of
two that can drift apart. The old trajectory-only check was removed.

## Decoupling from `expected_stage`

`pruned_match` was gated on `expected_stage`, which the dataset does not provide. Support recovery
does not depend on which stage was expected, so the gate is gone. The stage-derived metrics
(`stage_overshoot`, `wasted_levels`, `eq_overshoot`, `eq_wasted_levels`) legitimately require an
expected stage and remain `nothing` without one; no expected stage was invented.

Campaign systems supply their derived support; the diagnostic systems keep the hand-encoded table
unchanged.

## Budget-stop attribution

No schema change required. Records carry `system_id`, and the manifest carries `system_dim`, so
budget stops are attributable to dimension by joining at analysis time.

**Limitation to state**: the parameter count per fit is *not* recoverable, because the counters are
aggregated per cell. Attribution by parameter count would need per-fit telemetry, which does not
exist. Dimension answers the question that motivated the requirement.

## Fingerprints

| | before | after |
|---|---|---|
| regression | `45cb2c4507007366` | `45cb2c4507007366` (unchanged) |
| Phase B | `c0a236edf030e03a` | `c71c85ac2ec580ff` |

Phase B changes because three systems are reclassified and because the derived support is now part of
the payload — it defines what `pruned_match` means, so it belongs to the campaign identity. The
regression fingerprint is untouched, as required.

## Verification

| check | result |
|---|---|
| exact cell (sys 11, `pretune_off`) | `pruned=true`, loss 4.670e-15 |
| surrogate cell (sys 1, `pretune_off`) | `pruned=nothing`, loss 6.630e-05 |
| regression cell (sys 11, seed 42) vs `arm20k.jsonl` | **62 fields compared, 0 differences** |
| `derive_phase_b_support.jl --check` | committed table matches fresh derivation |
| manifest | 756 rows, exact 20 / surrogate 43 |

Loss, `total_loss_evals`, `total_parameter_fits`, `support_terms` and `final_stage` are unchanged in
the regression cell: this work package measures, it does not search differently.

## Commands

```powershell
julia --project=. --startup-file=no studies\regression\derive_phase_b_support.jl --check
julia --project=. --startup-file=no studies\regression\generate_phase_b_manifest.jl --output outputs\studies\regression\phase_b\wp_e2_manifest.csv
```

First: about 25 s, prints the per-system table and must end with "committed table matches a fresh
derivation". Second: about 30 s, must report `rows=756`, `phase_b_fingerprint=c71c85ac2ec580ff`,
`regression_fingerprint=45cb2c4507007366`.

## Backlog recorded, not fixed

`support_match_pruned` exists three times in near-identical form under `experiments/`,
`studies/regression/` and `studies/phase1_diag/`.
