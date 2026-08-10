# REPORT WP-D1

## Base Image

- Container definition: `containers/evoode_regression.apptainer`
- Exact upstream tag used: `julia:1.12.6-bookworm`
- Verification source: Docker Hub's official `julia` image page lists `1.12.6-bookworm`, and the
  tag page lists Linux architectures for that tag. Docker Hub also documents `bookworm` tags as
  Debian suite variants.
- Thread pinning, depot path and runscript were left unchanged.

## Project Compat

Added:

- `julia = "1.12"`

Verified existing compat entries against `Manifest.toml`:

| Compat entry | Manifest version | Result |
|---|---:|---|
| `CairoMakie = "0.15.10"` | `0.15.10` | satisfied |
| `DifferentialEquations = "7.17.0"` | `7.17.0` | satisfied |
| `JSON3 = "1.14.3"` | `1.14.3` | satisfied |
| `LinearAlgebra = "1.12.0"` | `1.12.0` | satisfied under Julia 1.12.6 |
| `Logging = "1.11.0"` | `1.11.0` | satisfied |
| `Optimization = "5.2.0"` | `5.2.0` | satisfied |
| `OptimizationOptimJL = "0.4.8"` | `0.4.8` | satisfied |
| `Plots = "1.41.2"` | `1.41.2` | satisfied |
| `Printf = "1.11.0"` | `1.11.0` | satisfied |
| `ProgressMeter = "1.11.0"` | `1.11.0` | satisfied |
| `Random = "1.11.0"` | `1.11.0` | satisfied |
| `SciMLBase = "2.128.0"` | `2.128.0` | satisfied |
| `SpecialFunctions = "2.5.1"` | `2.6.1` | satisfied by Julia compat semantics for the `2.x` series |
| `Statistics = "1.11.1"` | `1.11.1` | satisfied |

No manifest contradiction was found.

## Clean Instantiate Check

Local Julia version:

```text
julia version 1.12.6
```

Command shape used for the clean-depot instantiate:

```powershell
$depot = Join-Path (Get-Location) '.codex_tmp_wp_d1_depot_4'
New-Item -ItemType Directory -Force -Path $depot | Out-Null
$env:JULIA_DEPOT_PATH = $depot
$env:JULIA_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:JULIA_PKG_PRECOMPILE_AUTO = '0'
$before = (Get-FileHash Manifest.toml -Algorithm SHA256).Hash.ToLowerInvariant()
julia --project=. -e 'import Pkg; Pkg.instantiate(; verbose=true)'
$after = (Get-FileHash Manifest.toml -Algorithm SHA256).Hash.ToLowerInvariant()
if ($before -ne $after) { throw "Manifest hash changed" }
```

Result:

- `manifest_before = 2a2f5dcc0b5555178cdb76935f9f7d22b8e75bbed3ef387d5243941bcf552f6c`
- `manifest_after  = 2a2f5dcc0b5555178cdb76935f9f7d22b8e75bbed3ef387d5243941bcf552f6c`
- The verbose output installed the manifest's pinned versions, for example
  `DifferentialEquations v7.17.0`, `Optimization v5.2.0`, `OptimizationOptimJL v0.4.8`,
  `CairoMakie v0.15.10`, `Plots v1.41.2`, `SciMLBase v2.128.0`, and
  `SpecialFunctions v2.6.1`.
- The output contained no `Resolving` step.
- `git diff -- Manifest.toml` was empty after the run.

The requested package-load smoke check was attempted separately:

```powershell
$env:JULIA_DEPOT_PATH = (Join-Path (Get-Location) '.codex_tmp_wp_d1_depot_4')
julia --project=. -e 'using EvoODE; b = default_polynomial_basis(1, 2); println(basis_num_terms(b)); println(basis_term_name(b, 1))'
```

This did not complete in this Windows/VS Code execution environment: two `using EvoODE` attempts
timed out, including one with a 15 minute limit. I am not reporting the load smoke as passed. The
instantiate acceptance passed; the load-smoke acceptance should be rerun in a normal terminal or in
the Apptainer image with the command above. A pass is: exit code 0, output containing `2` and `u1`,
and an unchanged `Manifest.toml` hash.

## Build Provenance

The image now writes a small JSON file at build time:

- Location: `/opt/EvoODE/build_provenance.json`
- Format:

```json
{"julia_version":"1.12.6","project_toml_sha256":"<sha256>","manifest_toml_sha256":"<sha256>"}
```

Current source-file hashes:

- `Project.toml`: `2153e124df036ec434d3e4313a63193f595c334d54baa4781c28f320ca6ad04e`
- `Manifest.toml`: `2a2f5dcc0b5555178cdb76935f9f7d22b8e75bbed3ef387d5243941bcf552f6c`

This provenance is not used by `config_fingerprint()`, is not a runtime gate, and is not a new
identity mechanism.

## Version Claims Corrected

Files corrected:

- `CLAUDE.md`
- `docs/hpc_requirements.md`
- `docs/hpc_briefing_2026-08-06.md`
- `containers/evoode_regression.apptainer`
- `codex/REPORT_WP_B2.md`
- `DIARY.md`

The correction states that the existing Phase A and regression results were produced on Julia
1.12.6, and that the earlier Julia 1.11.5 claim was incorrect.

## Manifest Status

`Manifest.toml` is unchanged. It was not regenerated, updated, resolved, or edited.
