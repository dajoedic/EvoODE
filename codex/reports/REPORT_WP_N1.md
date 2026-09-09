# WP-N1 Report

## Implementation

Changed files:

- `src/basis/staged_polynomial.jl`
- `src/EvoODE.jl`
- `studies/regression/run_regression.jl`
- `studies/regression/wp_n1_basis_probe.jl`
- `test/test_wp_n1_basis_and_record.jl`
- `docs/architecture.md`

`default_staged_polynomial_basis(dim)` was not edited. The new exported builder is
`staged_polynomial_basis_with_constant(dim)`. It preserves the existing staged layout and adds term
`"1"` to stage 1.

Stage 1 is deliberate: the staged basis is degree ordered, and the constant has degree 0. It is
therefore simpler than the linear terms and must be available from the first stage.

`studies/regression/run_regression.jl` now records:

- `basis_name`: `"default_staged_polynomial_basis"` unless a variant explicitly sets another basis.
- `support_terms`: unchanged term-name list by equation.
- `model_terms`: per equation, a list of `term_index`, `term`, and `coefficient` entries in the same
  order as the flattened fitted parameter vector.

Existing variants do not define `basis_name`, so they continue to use
`default_staged_polynomial_basis`.

## Record Form and Reconstruction Example

Example record fragment:

```json
{
  "basis_name": "staged_polynomial_basis_with_constant",
  "support_terms": [["1", "u1", "u1^3"]],
  "model_terms": [[
    {"term_index": 1, "term": "1", "coefficient": 2.5},
    {"term_index": 2, "term": "u1", "coefficient": -1.0},
    {"term_index": 4, "term": "u1^3", "coefficient": 0.125}
  ]]
}
```

Reconstruction from record plus basis:

```julia
basis = staged_polynomial_basis_with_constant(1)
structure = StructureSpec([[entry["term_index"] for entry in record["model_terms"][1]]])
params = [entry["coefficient"] for entry in record["model_terms"][1]]
f!, n_params, meta = build_rhs(structure, basis)
```

This reconstructs `du1 = 2.5*1 - 1.0*u1 + 0.125*u1^3` without access to the original search run.

## Probe Runner

Added `studies/regression/wp_n1_basis_probe.jl`.

The dim-1 run compares the old and constant staged bases on systems:

```text
2, 3, 6, 8, 11, 12, 1, 5, 9, 17, 23
```

It uses seeds `7, 42, 123`, IC sets `1, 2`, and `pretuning=false` for both basis variants. This
matches one Phase-B condition and avoids mixing the basis question with the pretuning factor.

The dim-1 command is:

```powershell
julia --project=. --startup-file=no studies/regression/wp_n1_basis_probe.jl --dim=1
```

Expected outputs:

- `outputs/wp_n1_dim1_probe/history.jsonl`
- `outputs/wp_n1_dim1_probe/summary.csv`
- `outputs/wp_n1_dim1_probe/heartbeats/*.heartbeat.jsonl`

The startable dim-2 command, not run in this Codex session, is:

```powershell
$env:WP_N1_ALLOW_DIM2='1'; julia --project=. --startup-file=no studies/regression/wp_n1_basis_probe.jl --dim=2
```

It writes to `outputs/wp_n1_dim2_probe/`.

## Commands Attempted

```powershell
julia --project=. --startup-file=no test/test_wp_n1_basis_and_record.jl
```

Result: Julia did not start.

```text
Program 'julia.exe' failed to run: A specified logon session does not exist.
```

```powershell
julia --project=. --startup-file=no -e "include(\"studies/regression/run_regression.jl\"); println(config_fingerprint()); println(stage_cap_behavior_fingerprint())"
```

Result: Julia did not start with the same process-start error.

```powershell
julia --project=. --startup-file=no studies/regression/wp_n1_basis_probe.jl --dim=2
```

Result: Julia did not start with the same process-start error. No dim-2 run was launched.

Static checks performed:

```powershell
rg -n "staged_polynomial_basis_with_constant|basis_name|model_terms|active_model_terms|WP_N1_DIM1_SYSTEM_IDS|dim=2|WP-N1" src studies test docs codex -S
rg -n "[^\x00-\x7F]" src/basis/staged_polynomial.jl studies/regression/wp_n1_basis_probe.jl test/test_wp_n1_basis_and_record.jl
rg -n "basis_name|model_terms|support_terms|build_variant_basis|default_staged_polynomial_basis\(dim\)" studies/regression/run_regression.jl studies/regression/phase_b_config.jl
```

The ASCII scan found no non-ASCII characters in newly edited Julia files.

## Acceptance Status

Blocked by environment, not by the implementation.

Open because Julia could not be started:

- old-basis loss bit-equality could not be executed;
- `config_fingerprint()` could not be printed;
- the dim-1 probe could not be run;
- no dim-1 result table exists under `outputs/`;
- the new test file could not be executed.

Static evidence for campaign identity:

- `default_staged_polynomial_basis(dim)` body was not changed; the new builder was appended.
- `config_fingerprint()` and `phase_b_fingerprint()` still contain the literal
  `"default_staged_polynomial_basis(dim)"`.
- Existing regression variants have no `basis_name` field and therefore resolve to
  `"default_staged_polynomial_basis"`.
