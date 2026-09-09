# WP-F1 Report - Line-search cost diagnosis

The sentinel-cliff hypothesis is refuted for the decisive expensive fits measured here. The worst
reproduced fit, Phase B system 2 with pretuning on and structure `u1`, spent 28,618/28,618
evaluations on finite non-sentinel losses and had zero `1e6` sentinel hits. System 17 showed the
same pattern for its expensive `u1` fit: 4,105/4,105 finite non-sentinel evaluations. Some quadratic
fits did touch the sentinel, including long runs, but those hits were a small minority of the
default-line-search evaluations rather than the dominant cost source.

## Scope

Added a standalone measurement study:

- `studies/linesearch/diagnose_linesearch.jl`
- outputs under `outputs/studies/linesearch/wp_f1/`

No `src/` files were modified. The study uses a custom `AbstractLoss` to record every evaluated
parameter vector and returned loss, and uses the existing `EvoODE._BFGS_SOLVE_HOOK` only inside the
study for the offline backtracking comparison.

## Fit Selection

Small 1D-only sample from the Phase B profile:

- pathological: system 2, `Population growth (naive)`
- pathological: system 17
- control: system 11

For each system:

- initial condition set `1`
- seed `42`
- structures `u1` and `u1 + u1^2`
- both Phase B conditions: `pretune_on`, `pretune_off`
- default Optim.jl BFGS line search and offline `BackTracking()` BFGS comparison

Both line-search variants optimize the identical objective from the identical explicit `p0`.

## Evaluation-Sequence Statistics

| system | condition | structure | line search | evals | sentinel | finite | distinct losses | sentinel runs | longest sentinel run | final loss | retcode |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 | pretune_on | `u1` | default | 28618 | 0 | 28618 | 9216 | 0 | 0 | 1.864067e-12 | Failure |
| 2 | pretune_on | `u1` | backtracking | 24 | 0 | 24 | 20 | 0 | 0 | 9.559071e-13 | Success |
| 2 | pretune_off | `u1` | default | 97 | 0 | 97 | 45 | 0 | 0 | 1.955816e-12 | Success |
| 2 | pretune_off | `u1` | backtracking | 38 | 0 | 38 | 25 | 0 | 0 | 1.955814e-12 | Success |
| 2 | pretune_on | `u1 + u1^2` | default | 289 | 0 | 289 | 216 | 0 | 0 | 1.518493e-08 | Success |
| 2 | pretune_on | `u1 + u1^2` | backtracking | 99 | 0 | 99 | 74 | 0 | 0 | 1.510212e-08 | Success |
| 2 | pretune_off | `u1 + u1^2` | default | 51385 | 64 | 51321 | 26108 | 3 | 52 | 8.900239e-10 | Failure |
| 2 | pretune_off | `u1 + u1^2` | backtracking | 231 | 67 | 164 | 122 | 8 | 12 | 1.375132e-08 | Success |
| 17 | pretune_on | `u1` | default | 4105 | 0 | 4105 | 505 | 0 | 0 | 9.586518e+01 | Failure |
| 17 | pretune_on | `u1` | backtracking | 45 | 0 | 45 | 32 | 0 | 0 | 9.586518e+01 | Success |
| 17 | pretune_off | `u1` | default | 145 | 0 | 145 | 70 | 0 | 0 | 9.586518e+01 | Success |
| 17 | pretune_off | `u1` | backtracking | 62 | 0 | 62 | 45 | 0 | 0 | 9.586518e+01 | Success |
| 17 | pretune_on | `u1 + u1^2` | default | 1749 | 0 | 1749 | 1132 | 0 | 0 | 7.966898e-03 | Success |
| 17 | pretune_on | `u1 + u1^2` | backtracking | 74 | 0 | 74 | 60 | 0 | 0 | 7.966898e-03 | Success |
| 17 | pretune_off | `u1 + u1^2` | default | 1937 | 164 | 1773 | 1183 | 5 | 80 | 7.966898e-03 | Failure |
| 17 | pretune_off | `u1 + u1^2` | backtracking | 203 | 57 | 146 | 125 | 5 | 17 | 7.966791e-03 | Success |
| 11 | pretune_on | `u1` | default | 31 | 0 | 31 | 20 | 0 | 0 | 1.159602e-01 | Success |
| 11 | pretune_on | `u1` | backtracking | 25 | 0 | 25 | 16 | 0 | 0 | 1.159602e-01 | Success |
| 11 | pretune_off | `u1` | default | 7 | 0 | 7 | 3 | 0 | 0 | 1.835299e-01 | Success |
| 11 | pretune_off | `u1` | backtracking | 7 | 0 | 7 | 3 | 0 | 0 | 1.835299e-01 | Success |
| 11 | pretune_on | `u1 + u1^2` | default | 105 | 0 | 105 | 78 | 0 | 0 | 3.847572e-03 | Success |
| 11 | pretune_on | `u1 + u1^2` | backtracking | 82 | 0 | 82 | 61 | 0 | 0 | 3.847572e-03 | Success |
| 11 | pretune_off | `u1 + u1^2` | default | 9 | 0 | 9 | 4 | 0 | 0 | 2.195661e-01 | Success |
| 11 | pretune_off | `u1 + u1^2` | backtracking | 9 | 0 | 9 | 4 | 0 | 0 | 2.195661e-01 | Success |

## Sentinel-Run Finding

Default expensive fits do not generally spend their evaluations on sentinel hits:

- system 2, `pretune_on`, `u1`: 0 sentinel hits; all 28,618 evaluations finite.
- system 17, `pretune_on`, `u1`: 0 sentinel hits; all 4,105 evaluations finite.
- system 17, `pretune_on`, `u1 + u1^2`: 0 sentinel hits; all 1,749 evaluations finite.

Sentinel runs appear only in the `pretune_off` quadratic fits:

- system 2, `u1 + u1^2`, default: 64 sentinel hits in 3 runs, longest run 52; only 0.12% of 51,385 evaluations.
- system 17, `u1 + u1^2`, default: 164 sentinel hits in 5 runs, longest run 80; 8.47% of 1,937 evaluations.
- backtracking shortened sentinel runs in those cases, but the default runs were still mostly finite-loss work.

So the cliff signature exists in some fits, but it is not the explanation for the worst measured
cost. The expensive default line search is mostly revisiting finite, highly varied objective values:
9,216 distinct finite losses for the 28,618-evaluation system-2 `u1` fit, and 26,108 distinct losses
for the 51,385-evaluation system-2 quadratic fit.

## Offline Line-Search Comparison

Backtracking saved large amounts of work on every pathological default fit:

- system 2 `pretune_on` `u1`: 28,618 -> 24 evaluations; final loss improved from `1.864067e-12` to `9.559071e-13`.
- system 2 `pretune_off` `u1 + u1^2`: 51,385 -> 231 evaluations; final loss worsened from `8.900239e-10` to `1.375132e-08`.
- system 17 `pretune_on` `u1`: 4,105 -> 45 evaluations; final loss unchanged at `9.586518e+01`.
- system 17 `pretune_on` `u1 + u1^2`: 1,749 -> 74 evaluations; final loss unchanged to shown precision.
- system 17 `pretune_off` `u1 + u1^2`: 1,937 -> 203 evaluations; final loss slightly improved from `7.966898e-03` to `7.966791e-03`.

The control system 11 stayed cheap under both line searches: default fits ranged from 7 to 105
evaluations, and backtracking ranged from 7 to 82.

Backtracking is therefore promising as a cost control, but system 2 `pretune_off` `u1 + u1^2` shows
that it can move the final loss. That is an offline comparison result only; no production optimizer
setting was changed.

## Fingerprints

Measured at the end of the study run:

```text
regression_fingerprint=7acd3ebf3f60b974
phase_b_fingerprint=e577d9d692f3125b
```

## Artifacts

- `outputs/studies/linesearch/wp_f1/fit_summary.csv`
- `outputs/studies/linesearch/wp_f1/fit_records.jsonl`

The JSONL contains the full evaluation sequence for every fit: evaluation index, parameter vector,
and returned loss.

## Commands

Study command:

```powershell
julia --project=. --startup-file=no studies/linesearch/diagnose_linesearch.jl
```

Observed runtime here: 84.2 s wall time after Julia startup/compilation. Expected runtime on the
same machine: about 1-3 minutes.

Pass criterion:

- command exits with status 0
- `regression_fingerprint=7acd3ebf3f60b974`
- `phase_b_fingerprint=e577d9d692f3125b`
- `outputs/studies/linesearch/wp_f1/fit_summary.csv` and `fit_records.jsonl` are produced
- the default system-2 `pretune_on` `u1` row reports 28,618 evaluations, 0 sentinel hits, and
  final loss near `1.864067e-12`
