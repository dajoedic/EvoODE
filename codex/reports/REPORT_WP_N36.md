# REPORT WP-N36

## Status

Blocked: Umgebung, nicht Sache. Julia was not executed in this Codex session, so Pkg resolution,
precompilation, package-extension loading, and numerical equivalence checks remain for Claude.

One content blocker is also recorded: the task text says `OrdinaryDiffEq` version `5.64.0` is
already in the Manifest. In this working tree, `[[deps.OrdinaryDiffEq]]` is version `6.104.0`
with `git-tree-sha1 = "bcb26e15bc7d9add263fc13546625af5d4e2caac"` and uuid
`1dea7af3-3e70-54e6-95c3-0bf5283fa5ed`. The only Manifest entry with version `5.64.0` is
not `OrdinaryDiffEq`. To preserve the "0 changed versions or hashes" criterion, `Project.toml`
was set to `OrdinaryDiffEq = "6.104.0"`.

## Changes Prepared

- Replaced all repo-local `using DifferentialEquations` imports under `src/`, `studies/`,
  `benchmarks/`, `experiments/`, and `test/` with `using OrdinaryDiffEq`.
- Updated `Project.toml`:
  - removed direct deps `DifferentialEquations`, `Plots`, `CairoMakie`;
  - added direct dep `OrdinaryDiffEq`;
  - added weakdeps `Plots`, `CairoMakie`;
  - added extensions `EvoODEPlotsExt`, `EvoODECairoMakieExt`;
  - removed `DifferentialEquations` compat;
  - added `OrdinaryDiffEq = "6.104.0"` compat;
  - kept `Plots` and `CairoMakie` compat.
- Removed plot includes from `src/EvoODE.jl` and declared public generic functions:
  `solve_and_save_plot`, `render_all_frames`, `render_frame`, `structure_to_string`.
- Moved Plots-backed method code to `ext/EvoODEPlotsExt.jl`.
- Moved CairoMakie-backed animation/rendering method code to `ext/EvoODECairoMakieExt.jl`.
- Added `codex/reports/wp_n36_manifest_diff.py` for Manifest before/after comparison.
- Left `Manifest.toml` unresolved/unchanged by Codex because Julia cannot be run here.

## Name Check

Repo usage after replacement:

- `ODEProblem`
- `solve`
- `Tsit5`
- `ReturnCode`

Static local-depot check for the active Manifest version:

- `OrdinaryDiffEq` 6.104.0 source exports `Tsit5` and `solve`.
- `SciMLBase` source exports `ODEProblem`, `solve`, and `ReturnCode`.
- `OrdinaryDiffEq` depends on/reexports SciMLBase in the local package source, so no missing
  replacement name was found statically.

No callbacks were found in the changed search set.

## Static Checks Run

```text
rg 'DifferentialEquations|using Plots|include\("plotting|plot_solution|search_animation' src studies benchmarks experiments test Project.toml ext codex/reports/wp_n36_manifest_diff.py
```

Result: no matches.

```text
python -m py_compile codex/reports/wp_n36_manifest_diff.py
```

Result: exit code 0.

```text
python -c "import tomllib, pathlib; tomllib.loads(pathlib.Path('Project.toml').read_text()); print('Project.toml OK')"
```

Result: `Project.toml OK`.

```text
python codex/reports/wp_n36_manifest_diff.py Manifest.toml Manifest.toml
```

Result:

```text
removed_count: 0
remaining_count: 443
added_count: 0
changed_version_or_hash_count: 0
```

## Claude Commands

Run from repo root. Expected duration: Pkg resolution under 1 minute; instantiate/precompile
depends on cache state and may take 5-15 minutes on the laptop.

```bash
cp Manifest.toml codex/reports/Manifest_WP_N36_before.toml
julia --project=. -e 'import Pkg; Pkg.resolve(); Pkg.instantiate(); Pkg.precompile()'
python codex/reports/wp_n36_manifest_diff.py codex/reports/Manifest_WP_N36_before.toml Manifest.toml
```

Acceptance for this step: `added_count: 0` and `changed_version_or_hash_count: 0`.
If either value is nonzero, WP-N36 remains blocked.

Expected duration: 1-3 minutes.

```bash
julia --project=. test/test_wp_n32_data_condition.jl
```

Acceptance includes `phase_c_fingerprint() == "0c9672de35c75a9d"`.

Expected duration: short Stage 0 cell batch, likely minutes; compare step under 1 minute.

```bash
julia --project=. studies/regression/run_batch_cell.jl 1 --manifest outputs/wp_n32_stage0/manifest.csv --output-dir outputs/wp_n36_stage0/tasks
julia --project=. studies/regression/run_batch_cell.jl 2 --manifest outputs/wp_n32_stage0/manifest.csv --output-dir outputs/wp_n36_stage0/tasks
julia --project=. studies/regression/run_batch_cell.jl 7 --manifest outputs/wp_n32_stage0/manifest.csv --output-dir outputs/wp_n36_stage0/tasks
julia --project=. studies/regression/run_batch_cell.jl 8 --manifest outputs/wp_n32_stage0/manifest.csv --output-dir outputs/wp_n36_stage0/tasks
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/wp_n36_stage0
```

Expected duration: system 1 boundary-10 oracle, likely minutes.

```bash
julia --project=. studies/regression/wp_n3_oracle_refit.jl --input outputs/wp_n32_b01/history_sys1.jsonl --output-dir outputs/wp_n36_b01 --fresh
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/phase_c_campaign_221a3a7 --candidate-oracle outputs/wp_n36_b01
```

Compare against C-5 with the existing Phase C comparison tooling used for prior WP-N32/C-5 checks.

Expected duration: dimension 2 single C-1 cell, likely minutes.

```bash
julia --project=. studies/regression/run_batch_cell.jl 277 --manifest outputs/studies/regression/phase_c/manifest.csv --output-dir outputs/wp_n36_dim2/tasks
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/wp_n36_dim2
```

Expected duration: dimension 3 oracle, cheaper than a full search; likely minutes.

```bash
python -c 'import json, pathlib; src=pathlib.Path("outputs/phase_c_campaign_221a3a7/history.jsonl"); out=pathlib.Path("outputs/wp_n36_dim3_input/history.jsonl"); out.parent.mkdir(parents=True, exist_ok=True); rows=[json.loads(line) for line in src.read_text().splitlines() if line.strip()]; rows=[r for r in rows if int(r.get("system_id")) == 52 and int(r.get("seed")) == 42 and int(r.get("initial_condition_set")) == 1 and r.get("condition") == "capped"]; out.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)); print(len(rows))'
julia --project=. studies/regression/wp_n3_oracle_refit.jl --input outputs/wp_n36_dim3_input/history.jsonl --output-dir outputs/wp_n36_dim3 --fresh
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/phase_c_campaign_221a3a7 --candidate-oracle outputs/wp_n36_dim3
```

Expected duration: seconds after precompile.

```bash
julia --project=. -e 'using EvoODE; @assert !haskey(Base.loaded_modules, Base.PkgId(Base.UUID("91a5bcdd-55d7-5caf-9e0b-520d859cae80"), "Plots")); @assert !haskey(Base.loaded_modules, Base.PkgId(Base.UUID("13f3f980-e62b-5c42-98c6-ff1f3baf88f0"), "CairoMakie")); println("EvoODE loaded without plot stacks")'
julia --project=. -e 'using EvoODE, Plots; @assert hasmethod(EvoODE.solve_and_save_plot, Tuple{Function, Vector{Float64}, EvoODE.Trajectory}); println("Plots extension loaded")'
```

## Open Acceptance Items

- Pkg resolution not run.
- Manifest removed-package list not produced from a resolved Manifest.
- Julia tests not run.
- Numerical bit-equality checks not run.
- Package-extension runtime loading not run.
