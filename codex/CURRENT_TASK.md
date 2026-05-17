# CURRENT TASK: WP-1.2 — Phase A Diagnostic: Metric Artifact vs. Structural Failure

**Language: Python**

## Context

Phase A showed `exact_support_match=0` for several systems. The question is:
was this a metric artifact (near-zero spurious terms that pruning would remove) or a
genuine structural failure (wrong terms discovered)?

Manual inspection of result.json already reveals:

- **System 11** (`du=-u1^3`): structure_pretty shows
  `du_1 = (-0.0000)*u1 + (0.0000)*u1^2 + (-1.0000)*u1^3`
  → correct cubic term found, two near-zero extras → **metric artifact**

- **System 26**: discovered `u1, u2, u2^2, u1*u2` in eq1 (missing `u1^2`), wrong eq2
  → wrong term set → **genuine structural failure**

- **System 31**: discovered linear + self-quadratic terms, no cross-term `u1*u2`
  → wrong term set → **genuine structural failure**

- **System 63**: discovered only linear terms, no cross-terms like `u1*u3`
  → wrong term set → **genuine structural failure**

WP-1.2 systematizes this analysis over all Phase A EvoGrow runs for all exact systems
and writes a diagnostic report that feeds into the Gate 1 decision.

## Script

**Path:** `analysis/scripts/aggregate/phase1_diagnostic.py`

**CLI:**
```
python analysis/scripts/aggregate/phase1_diagnostic.py \
    --runs_dir experiments/paper1_phaseA_v1/runs \
    --output docs/phase1_diagnostic.md
```

All paths must be passed as CLI arguments. No hardcoded paths.

---

## Expected Terms (hardcoded lookup table in script)

Use the following ground-truth term sets for the exact systems.
Term names must match the notation used in structure_pretty.

```python
EXPECTED_TERMS = {
    2:  {1: {"u1"}},
    3:  {1: {"u1", "u1^2"}},
    11: {1: {"u1^3"}},
    24: {1: {"u2"}, 2: {"u1"}},
    26: {1: {"u1", "u1^2", "u1*u2"}, 2: {"u2", "u1*u2", "u2^2"}},
    31: {1: {"u1*u2"},               2: {"u1*u2", "u2"}},
    54: {1: {"u1", "u2"},            2: {"u1", "u2", "u1*u3"}, 3: {"u1*u2", "u3"}},
    63: {1: {"u1*u3"},               2: {"u1*u3", "u2"},
         3: {"u2", "u3"},            4: {"u3"}},
}
```

---

## Implementation

### Step 1 — Parse structure_pretty

Write a helper `parse_structure_pretty(s: str) -> dict[int, dict[str, float]]`
that parses strings of the form:

```
du_1 = (-0.0000)*u1 + (0.0000)*u1^2 + (-1.0000)*u1^3
du_2 = (2.7894)*u1 + (-0.3317)*u2 + (-0.3294)*u1^2
```

Returns: `{eq_idx: {term_name: coefficient}}` where eq_idx starts at 1.

The regex pattern for one term is: `\((-?\d+\.\d+)\)\*(\S+)`

Handle the case where structure_pretty is empty or None — return `{}`.

### Step 2 — Apply pruning

Write `prune_terms(eq_terms: dict[str, float]) -> set[str]`
that returns the set of term names surviving pruning:

```python
def prune_terms(eq_terms):
    if not eq_terms:
        return set()
    max_abs = max(abs(v) for v in eq_terms.values())
    threshold = max(1e-6, 1e-3 * max_abs)
    return {name for name, coeff in eq_terms.items() if abs(coeff) >= threshold}
```

Note: structure_pretty coefficients are rounded to 4 decimal places. This is sufficient
to detect near-zero terms (printed as `0.0000`) vs. meaningful terms.

### Step 3 — Evaluate per run

For each result.json file under `runs_dir`:
1. Load `result.json`
2. Read `system_id` from `config.json` in the same folder (or infer from run_id)
3. Skip if system_id not in EXPECTED_TERMS (surrogate or GP baseline)
4. Skip GP baseline runs (variant contains "gp")
5. Parse structure_pretty → per-equation terms with coefficients
6. Apply pruning → pruned term set per equation
7. Compare pruned term set against EXPECTED_TERMS[system_id]
8. Record:
   - `run_id`
   - `system_id`
   - `variant`
   - `seed`
   - `final_loss`
   - `exact_support_match_raw` (from result.json field `exact_support_match`)
   - `exact_support_match_pruned` (computed here)
   - `structure_pretty`
   - `pruned_terms_per_eq` (as string)
   - `expected_terms_per_eq` (as string)
   - `diagnosis`: `"metric_artifact"` if raw=False and pruned=True,
                   `"genuine_failure"` if raw=False and pruned=False,
                   `"correct"` if raw=True (pruned should also be True),
                   `"unexpected"` otherwise

### Step 4 — Aggregate per (system_id, variant)

Group by (system_id, variant). Compute:
- `n_runs`: total seed count
- `n_correct_raw`: exact_support_match_raw=True count
- `n_correct_pruned`: exact_support_match_pruned=True count
- `n_metric_artifact`: diagnosis=metric_artifact count
- `n_genuine_failure`: diagnosis=genuine_failure count
- `mean_loss`: mean final_loss

### Step 5 — Write diagnostic report

Write to the path given by `--output` (default: `docs/phase1_diagnostic.md`).

Structure:

```markdown
# Phase 1 Diagnostic: Metric Artifact vs. Structural Failure
Generated: <ISO timestamp>
Source: experiments/paper1_phaseA_v1/runs/

## Summary

| system | variant | n_runs | raw_match | pruned_match | metric_artifacts | genuine_failures | mean_loss |
| ------ | ------- | ------ | --------- | ------------ | ---------------- | ---------------- | --------- |
...

## Per-System Findings

### System 11 (Critical slowing down — du=-u1^3)
...one paragraph describing what was found...

### System 26 (Lotka-Volterra competition)
...

[etc. for all systems with any exact_support_match=False]

## Gate 1 Input

- Systems where pruning fixes the metric: [list]
- Systems with genuine structural failure: [list]
- Diagnosis: [one sentence]
```

---

## Verification

After running the script:

1. `docs/phase1_diagnostic.md` exists and contains all exact system IDs.
2. System 11 is classified as `metric_artifact` for all EvoGrow variants across all seeds.
3. Systems 26, 31, 63 show `genuine_failure` in the majority of seeds.
4. System 2, 3, 24 show `correct` where expected (high exact_match_rate in Phase A).
5. The summary table is complete with no missing rows.

## Constraints

- Read-only access to `experiments/paper1_phaseA_v1/runs/` — do not write or modify any run files.
- The script must run without errors even if some result.json files are missing or malformed
  (skip with a warning).
- Use only the standard library + pandas. No new dependencies.
- The output file `docs/phase1_diagnostic.md` must be committed (it is not gitignored).
