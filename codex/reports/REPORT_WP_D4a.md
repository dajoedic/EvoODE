# WP-D4a Report

## Contract failure

`discover()` now fails immediately when the structure search returns a parameter vector whose length does not match the RHS built from the returned structure.

Error message text:

```text
Structure search parameter contract violated: expected <expected> parameters from returned structure, received <received> from <StructureSearchType>; returned_structure=<repr>
```

Observed example from a minimal bad structure search:

```text
Structure search parameter contract violated: expected 1 parameters from returned structure, received 0 from ContractSearch; returned_structure=StructureSpec([[1]])
```

The old silent refit path was removed from `src/core/discover.jl`. There is no flag or fallback repair path left.

## Runner behavior

No rescue was added in either runner:

- `experiments/run_experiment.jl`
- `studies/regression/run_regression.jl`

The error is allowed to propagate into their existing per-cell failure handling. That means a bad cell is recorded as failed instead of returning internally inconsistent `params`/`loss`/`objective`.

## Docstring

`src/core/types.jl` now documents `DiscoveryResult.objective` as:

```text
objective value reported by the structure search; it may use
search-specific penalties and is not necessarily recomputed from loss
```

No field was renamed, added, or removed.

## Tests added

New file:

```text
test/test_discover_contract.jl
```

It contains two testsets:

- `discover rejects structure-search parameter count mismatch`
  - constructs a bad `ContractSearch` returning `StructureSpec([[1]])` with `Float64[]`
  - asserts `discover()` raises `ErrorException`
  - asserts the message contains `expected 1`, `received 0`, `ContractSearch`, and `StructureSpec`
- `discover accepts consistent structure-search result`
  - constructs a healthy `ContractSearch` returning one parameter for `StructureSpec([[1]])`
  - asserts a normal `DiscoveryResult`
  - asserts params, loss, objective, and `meta.optimize.method` are preserved on the healthy path

Per task instruction, I did not run this test file locally as a suite-style command. The exact command for you to run is below.

## Healthy path argument

The change is entirely behind `if length(params) != n_params`. For matching counts, `discover()` still:

- keeps the structure-search parameter vector
- keeps the structure-search objective
- computes the same final simulation and validated loss
- sets `opt_meta = (method = "from_structure_search",)`
- does not call `fit_parameters`

Since the matching-count branch performs no extra fitting, random draw, parameter mutation, or objective recomputation, healthy runs keep the same parameters, loss, objective, RNG consumption, and evaluation count.

## Fingerprint

Measured after WP-D4a:

```text
7acd3ebf3f60b974
```

This matches WP-D3/D3b; WP-D4a did not change `config_fingerprint()`.

## Verification performed

Smoke only; no regression suite or experiment run was started.

Commands run:

```powershell
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); println(config_fingerprint())"
julia --project=. --startup-file=no --% -e "include(\"src/EvoODE.jl\"); using .EvoODE; println(\"load ok\")"
julia --project=. --startup-file=no --% -e "include(\"src/EvoODE.jl\"); using .EvoODE; struct ContractSearch <: AbstractStructureSearch; end; EvoODE.search_structure(::ContractSearch, traj, basis, loss, optimizer, options) = (structure = StructureSpec([[1]]), params = Float64[], loss = 0.0, objective = 1.0, meta = (;)); try; discover(Trajectory([0.0, 1.0], zeros(2, 1)); structure = ContractSearch(), optimizer = DummyOptimizer(), basis = default_polynomial_basis(1), loss = MSELoss(), options = DiscoveryOptions(verbose = 0)); catch err; println(sprint(showerror, err)); end"
Get-FileHash test/test_bfgs_budget.jl,test/test_bfgs_fallback_order.jl -Algorithm SHA256
```

Pass observations:

- fingerprint printed `7acd3ebf3f60b974`
- `EvoODE` printed `load ok`
- the minimal mismatch printed the contract error shown above
- `test/test_bfgs_budget.jl` hash remained `968FA0BE3ADD7CE9B219BC9904D72572288C21922D797800D89BFB0A022D7671`
- `test/test_bfgs_fallback_order.jl` hash was `FCFDF090EAA9539E6A2568770789BC85D87D400A156DFC01A6AFE8B18EEE5CCC`

## Commands for user-run verification

New contract test. Expected runtime: under 1 minute after Julia is warm, allow 2-3 minutes on a cold start.

```powershell
julia --project=. --startup-file=no test\test_discover_contract.jl
```

Pass looks like two testsets passing with no failures or errors.

Existing WP-D2/WP-D2b tests, unchanged. Expected runtime: about 1-2 minutes each.

```powershell
julia --project=. --startup-file=no test\test_bfgs_budget.jl
julia --project=. --startup-file=no test\test_bfgs_fallback_order.jl
```

Pass looks like all tests passed, with no failures or errors.

Fingerprint check. Expected runtime: under 2 minutes after Julia is warm, allow up to 5 minutes on a cold start.

```powershell
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); println(config_fingerprint())"
```

Pass looks like:

```text
7acd3ebf3f60b974
```

## WP-D4a-fix

The healthy-path assertion in `test/test_discover_contract.jl` now compares the returned structure content:

```julia
@test result.structure.active_idxs == [[1]]
```

It no longer compares `StructureSpec([[1]]) == StructureSpec([[1]])`, because `StructureSpec` has no custom `==`, `isequal`, or `hash` method and therefore uses identity comparison for its vector-backed contents. No equality or hash method was added.

Executed command:

```powershell
julia --project=. --startup-file=no test\test_discover_contract.jl
```

Full output:

```text
Test Summary:                                              | Pass  Total  Time
discover rejects structure-search parameter count mismatch |    5      5  2.5s
Test Summary:                                       | Pass  Total  Time
discover accepts consistent structure-search result |    6      6  3.2s
```
