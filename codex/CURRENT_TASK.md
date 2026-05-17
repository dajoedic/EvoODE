# CURRENT TASK: WP-1.1 — Coefficient-Threshold Pruning for exact_support_match

**Language: Julia**

## Context

EvoGrow grows structures incrementally but never prunes terms with near-zero coefficients.
As a result, a discovered model like:

```
dx/dt = 0.000001*u1 + 1.000043*u1^2
```

fails `exact_support_match` against the true structure `dx/dt = u1^2`, even though the
extra term is effectively zero. This makes the raw metric too strict and masks genuine
structural recovery.

The fix: for evaluation only, prune terms whose coefficient magnitude is negligible before
comparing against the expected support. This pruning must NEVER affect the search process,
parameter optimization, or population state — only the evaluation step.

## What to implement

All changes go in `experiments/run_experiment.jl`.

---

### Step 1 — Add `support_match_pruned`

Add a new function directly below the existing `support_match` (line ~192):

```julia
function support_match_pruned(
    structure::StructureSpec,
    params::Vector{Float64},
    expected_idxs::Vector{Vector{Int}}
)
    if length(structure.active_idxs) != length(expected_idxs)
        return false
    end

    offset = 0
    for (got_idxs, exp_idxs) in zip(structure.active_idxs, expected_idxs)
        n_terms = length(got_idxs)
        eq_params = params[offset+1 : offset+n_terms]
        offset += n_terms

        max_abs = isempty(eq_params) ? 0.0 : maximum(abs, eq_params)
        threshold = max(1e-6, 1e-3 * max_abs)

        pruned_idxs = sort([got_idxs[i] for i in 1:n_terms if abs(eq_params[i]) >= threshold])

        if pruned_idxs != sort(unique(exp_idxs))
            return false
        end
    end
    return true
end
```

**Important:** The parameter layout is sequential — equation k uses params at positions
`(offset+1):(offset+n_terms_k)` where offset is the sum of term counts for all prior equations.
This matches how `build_rhs` lays out the parameter vector.

---

### Step 2 — Update `compute_metrics`

In `compute_metrics` (line ~311), replace the current single `exact_support_match` computation:

**Current code (lines ~318–324):**
```julia
exact_support_match = nothing
...
if representability == "exact"
    expected_idxs = expected_active_idxs(Int(cfg.system_id), basis)
    exact_support_match = expected_idxs === nothing ? false : support_match(result.structure, expected_idxs)
    ...
end
```

**New code:**
```julia
exact_support_match_raw = nothing
exact_support_match_pruned = nothing
...
if representability == "exact"
    expected_idxs = expected_active_idxs(Int(cfg.system_id), basis)
    if expected_idxs !== nothing
        exact_support_match_raw = support_match(result.structure, expected_idxs)
        exact_support_match_pruned = support_match_pruned(
            result.structure, result.params, expected_idxs
        )
    else
        exact_support_match_raw = false
        exact_support_match_pruned = false
    end
    ...
end
```

---

### Step 3 — Update the metrics Dict in `compute_metrics`

Replace:
```julia
"exact_support_match" => exact_support_match,
```

With:
```julia
"exact_support_match" => exact_support_match_raw,
"exact_support_match_raw" => exact_support_match_raw,
"exact_support_match_pruned" => exact_support_match_pruned,
```

Keep `"exact_support_match"` (equal to raw) for backward compatibility with existing
aggregation scripts that reference this field.

---

### Step 4 — Update `partial_metrics`

Add the two new fields with `nothing` values alongside the existing `"exact_support_match"`:

```julia
"exact_support_match_raw" => nothing,
"exact_support_match_pruned" => nothing,
```

---

### Step 5 — Update `build_result_payload`

Add both new fields to the result payload dict alongside the existing `"exact_support_match"`:

```julia
"exact_support_match_raw" => metrics["exact_support_match_raw"],
"exact_support_match_pruned" => metrics["exact_support_match_pruned"],
```

---

### Step 6 — Update `write_summary`

Add one line to the summary text output, after the existing `exact_support_match` line:

```julia
println(io, "exact_support_match_pruned: $(metrics["exact_support_match_pruned"])")
```

---

## Verification

Run the existing experiment runner on one small test (e.g. System 3, logistic growth,
`evogrow_v2_2_stage_local`, seed 42) from `paper1_phaseA_v1` or a fresh minimal run.

Verify:
1. `metrics.json` contains all three fields: `exact_support_match`, `exact_support_match_raw`,
   `exact_support_match_pruned`.
2. For a system where the algorithm finds the correct structure with no spurious terms:
   raw == pruned == true.
3. For System 11 (`du = -u^3`, expected only cubic term): if the discovered structure has
   near-zero linear or quadratic coefficients, pruned should be true while raw may be false.
4. `result.json` contains `exact_support_match_raw` and `exact_support_match_pruned`.
5. The search behavior is unchanged (no modification to EvoGrow or GPStructureSearch).

## Constraints

- Do not modify any search logic in `src/`.
- Do not modify `experiments/aggregate.jl` — it reads whatever fields are present in
  `metrics.json` and will pick up the new fields automatically.
- Do not modify `experiments/generate_manifest.jl`.
- Only `experiments/run_experiment.jl` changes.
- The pruning threshold `max(1e-6, 1e-3 * max_abs_coeff_in_equation)` is frozen for Paper 1
  and must not be made configurable in this WP.
