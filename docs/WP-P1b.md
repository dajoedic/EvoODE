# WP-P1b Report

## Changes

- Added `SHA = "ea8e919c-243c-51af-8825-aaa63cd721ce"` to `[deps]` in `Project.toml`.
- Added `SHA = "0.7.0"` to `[compat]`, consistent with the existing stdlib compat entries.
- Resolved `Manifest.toml`; the existing `[[deps.SHA]]` stdlib entry remains at version `0.7.0`, and `project_hash` changed to `9b27a50c1c329db6162aa628d28f6eb002243932`.
- Added a package-load test at the start of `test/test_stage_cap.jl`. It starts a fresh Julia process with `--project=<repo>` and runs `using EvoODE`, so a missing direct dependency now fails before the include-based tests run.
- Updated `test/test_regression_runner_gate2.jl` expectations to the current values without changing the constants under test.

## SHA use

`SHA` is used directly by `src/structure/stage_cap_fingerprint.jl` for `stage_cap_behavior_fingerprint()`.
It is also used directly by `studies/regression/run_regression.jl` for `config_fingerprint()`.
`studies/regression/phase_b_config.jl` calls `sha256` through the regression runner include context.

The existing `config_fingerprint()` implementation already uses Julia's `SHA.sha256` path, so declaring the same stdlib dependency in `Project.toml` is the consistent fix. No local replacement hash function was introduced.

## Gate-2 test update

The historical Gate-2 freeze test now checks the current values:

| Check | Current expected value |
|---|---|
| `VARIANTS` | `["evogrow_v2_2_stage_local", "evogrow_v3", "evogrow_v2_2_stage_capped", "evogrow_v3_stage_capped"]` |
| `BFGS_TIME_LIMIT_S` | `Inf` |
| `LOOKAHEAD_CAP_POLICY.lookahead_horizon` | `5` |

The test contains an inline comment noting that WP-P1, WP-B3/D2, and WP-C2 moved these values.

## Why WP-P1 tests were green while package loading failed

`test/test_stage_cap.jl` loaded the code with:

```julia
include(joinpath(@__DIR__, "..", "src", "EvoODE.jl"))
using .EvoODE
```

That path evaluates the source file as a local module and does not validate the package's declared direct dependencies in the same way as `using EvoODE` through Julia's package loader. Therefore `using SHA` inside `src/structure/stage_cap_fingerprint.jl` could be reached in include-based tests while `julia --project=. -e 'using EvoODE'` failed because `SHA` was missing from `[deps]`.

The new first test in `test/test_stage_cap.jl` starts a separate Julia process and runs `using EvoODE` through the project environment. That makes a missing `[deps]` entry red in this test file.

## Verification

### Manifest resolve

Command:

```powershell
julia --project=. -e "using Pkg; Pkg.resolve()"
```

Output:

```text
Project No packages added to or removed from `C:\Users\joedicke\Documents\reps\EvoODE\Project.toml`
Manifest No packages added to or removed from `C:\Users\joedicke\Documents\reps\EvoODE\Manifest.toml`
```

### Package load

PowerShell command used to preserve Julia string quoting:

```powershell
julia --project=. --% -e "using EvoODE; println(\"ok\")"
```

Output:

```text
ok
```

### Stage-cap behavior fingerprint

Command:

```powershell
julia --project=. -e "using EvoODE; println(EvoODE.stage_cap_behavior_fingerprint())"
```

Output:

```text
61b6548ef0014593
Precompiling packages...
  48871.6 ms  ✓ EvoODE
  1 dependency successfully precompiled in 70 seconds. 579 already precompiled.
```

The emitted fingerprint is exactly `61b6548ef0014593`.

### Stage-cap tests

Command:

```powershell
julia --project=. test/test_stage_cap.jl
```

Output:

```text
Test Summary:                              | Pass  Total   Time
package loads through project dependencies |    1      1  22.3s
Test Summary:                     | Pass  Total  Time
look-ahead stage cap is data-only |    3      3  4.1s
Test Summary:                         | Pass  Total  Time
default look-ahead spans staged basis |    4      4  0.0s
Test Summary:                       | Pass  Total  Time
look-ahead split decision semantics |    8      8  0.3s
Test Summary:                                         | Pass  Total  Time
post-floor split decision has three relative outcomes |    6      6  0.0s
Test Summary:                                                 | Pass  Total  Time
stage cap behavior fingerprint is stable and behavior-derived |    6      6  1.0s
Test Summary:                        | Pass  Total  Time
look-ahead cap limits promotion only |    4      4  0.2s
Test Summary:                     | Pass  Total   Time
capped search smoke path executes |    4      4  13.6s
Test Summary:                           | Pass  Total  Time
EvoGrowV3 cap disabled is bit-identical |    4      4  0.3s
```

Totals from the summaries: 40 passes, 0 failures.

### Gate-2 regression runner test

Command:

```powershell
julia --project=. test/test_regression_runner_gate2.jl
```

Output:

```text
Test Summary:                      | Pass  Total  Time
Gate 2 regression runner selection |    9      9  5.5s
  Activating project at `C:\Users\joedicke\Documents\reps\EvoODE`
```

Totals from the summary: 9 passes, 0 failures.
