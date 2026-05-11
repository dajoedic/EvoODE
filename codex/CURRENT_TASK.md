# CURRENT TASK: Step 2 — Primary Metric Analysis + Freeze Memo

## Context

All 300 runs of `paper1_phaseA_v1` are complete. Aggregation is done.
This task evaluates hypotheses H1–H4 against the frozen study protocol
and writes the formal Freeze Memo to `docs/paper1_freeze_memo_phaseA.md`.

Reference documents (read before implementing):
- `docs/paper1_study_protocol.md` — metric definitions, hypothesis specifications, exclusion rules
- `PAPER_1.md` — freeze memo structure (three-block format), exact_match=0 collapse scenario
- `analysis/CONVENTIONS.md` — script architecture, naming, anti-patterns

**No figures. No paper tables. Claim evaluation and memo only.**

---

## Deliverables

| File | Description |
|------|-------------|
| `analysis/scripts/aggregate/evaluate_hypotheses.py` | Main analysis script |
| `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` | Machine-readable hypothesis diagnostics |
| `docs/paper1_freeze_memo_phaseA.md` | Human-readable Freeze Memo (three-block format) |

---

## Input Files

| File | Role |
|------|------|
| `analysis/data/paper1_phaseA_v1/aggregate_by_variant_system.csv` | Primary input: per-(variant, system) aggregated metrics |
| `experiments/paper1_phaseA_v1/run_registry.csv` | Secondary input: per-run detail if per-seed breakdowns needed |
| `outputs/studies/generalization/generalization_summary.csv` | Auxiliary: generalization study (Block 3 only) |
| `outputs/studies/generalization/generalization_detail.csv` | Auxiliary: per-test-set detail (Block 3 only) |
| `analysis/configs/paper1_phaseA_v1.json` | Config: paths and experiment metadata |

---

## Script: `evaluate_hypotheses.py`

### CLI

```
python analysis/scripts/aggregate/evaluate_hypotheses.py --config analysis/configs/paper1_phaseA_v1.json
```

### Structure

The script has four independent sections executed in order:

1. Load and validate inputs
2. Evaluate H1, H2, H3 (primary claims)
3. Evaluate H4 (secondary claim)
4. Evaluate auxiliary evidence (generalization_study, profile_init context)
5. Write machine-readable diagnostics JSON
6. Write Freeze Memo markdown

No section may influence a prior section's verdict.

---

## Section 1 — Input Validation

Load `aggregate_by_variant_system.csv`.

Verify:
- Expected variants present: `evogrow_v1`, `evogrow_v2_1`, `evogrow_v2_2_stage_local`, `evogrow_v2_2_passive`, `evogrow_v2_2_soft`, `gp_baseline`
- Expected system IDs present: 2, 3, 11, 23, 24, 26, 31, 37, 54, 63
- All (variant, system) cells have `n_valid` > 0 (report any with n_valid = 0 as a warning)

If any critical input is missing: print error and exit with code 1.

---

## Section 2 — H1, H2, H3 Evaluation

### H1 — Stage Overshoot Reduction

**Metric:** `mean_stage_overshoot`

**Filter:**
- Systems: exact systems with expected_stage ≥ 2 → IDs: 3, 11, 26, 31, 54, 63
- Variants: `evogrow_v1`, `evogrow_v2_1`, `evogrow_v2_2_stage_local` only
- GP excluded (no stage structure)

**Computation per system:**
- Compare `mean_stage_overshoot` of `evogrow_v2_2_stage_local` vs `evogrow_v2_1` and vs `evogrow_v1`
- Record: direction correct (v2.2 < v2.1 AND v2.2 < v1), direction partial, or direction wrong

**Verdict:**
- SUPPORTED: correct direction on majority (≥ 4 of 6) systems
- PARTIAL: correct direction on ≥ 1 but < 4 systems
- FALSIFIED: correct direction on 0 systems

---

### H2 — Competitive Recovery Quality

**Metric:** `exact_match_rate` (primary); `mean_loss` (fallback for collapsed systems)

**Filter:** all 8 exact systems (IDs: 2, 3, 11, 24, 26, 31, 54, 63)

**Computation per system:**

Step A — detect exact_match=0 collapse:
A system is collapsed if `exact_match_rate = 0` for ALL variants (including GP).

Step B — for non-collapsed systems:
Compare `exact_match_rate` of `evogrow_v2_2_stage_local` vs `gp_baseline`.
Record: v2.2 ≥ GP (competitive), v2.2 < GP (degraded).

Step C — for collapsed systems:
Compare `mean_loss` of best EvoGrow variant vs `gp_baseline`.
Record: EvoGrow loss ≤ GP loss (competitive on loss), EvoGrow loss > GP loss (degraded).
Flag these systems with: `"recovery_metric_used": "mean_loss (exact_match_rate collapsed)"`.

**Verdict:**
- SUPPORTED: v2.2 competitive (exact_match or loss) on majority (≥ 5 of 8) exact systems
- PARTIAL: competitive on ≥ 2 but < 5 systems
- FALSIFIED: competitive on < 2 systems

---

### H3 — Wasted Levels Reduction

**Metric:** `mean_wasted_levels`

**Filter:**
- Systems: exact systems with expected_stage ≥ 2 → IDs: 3, 11, 26, 31, 54, 63
- Variants: `evogrow_v1`, `evogrow_v2_1`, `evogrow_v2_2_stage_local` only
- GP excluded

**Computation per system:**
- Compare `mean_wasted_levels` of `evogrow_v2_2_stage_local` vs `evogrow_v2_1` and vs `evogrow_v1`
- Record: direction correct (v2.2 ≤ v2.1 AND v2.2 ≤ v1), direction partial, or direction wrong

Note: ties (equal wasted_levels) count as non-degraded, not as improvement.
Record ties separately from directional wins.

**Verdict:**
- SUPPORTED: correct direction on majority (≥ 4 of 6) systems
- PARTIAL: correct direction on ≥ 1 but < 4 systems
- FALSIFIED: correct direction on 0 systems

---

## Section 3 — H4 Evaluation (Secondary)

**Metric:** `exact_match_rate`

**Filter:**
- Systems: exact systems with expected_stage ≥ 3 → IDs: 11, 26, 31, 54, 63
- Variants: `evogrow_v2_2_stage_local` (hard), `evogrow_v2_2_passive`, `evogrow_v2_2_soft`

**Computation per system:**
- Compare exact_match_rate across the three usage-policy variants
- Record: hard ≥ soft ≥ passive (expected order), any other ordering

**Verdict:**
- SUPPORTED: expected ordering holds on majority (≥ 3 of 5) systems
- AMBIGUOUS: mixed results, no clear pattern
- FALSIFIED: reverse ordering on majority of systems

H4 verdict does not affect H1–H3. State this explicitly in the diagnostics JSON.

---

## Section 4 — Auxiliary Evidence

### Generalization Study

Load `outputs/studies/generalization/generalization_summary.csv`.

Print the column names first (they may differ from assumptions).

From the data, for each (system, variant) cell with `exact_support_match = true`
on the training run:
- Extract `mean_refit_loss` (loss after refitting structure to test trajectories)
- Extract `mean_fresh_loss` (loss of fresh discovery on same test trajectories)
- Count `n_exact_runs` per (system, variant) cell

Only include cells with `n_exact_runs ≥ 3` in the verdict.

**Verdict:**
- INCLUDE IN SUPPLEMENTARY: consistent tendency for refit_loss ≤ fresh_loss across systems with n_exact_runs ≥ 3
- INCLUDE WITH CAUTION: mixed results
- OMIT: insufficient data (all cells have n_exact_runs < 3)

### profile_init

Do not load any data. Record only:
> "profile_init.jl results are available (docs/profile_init_results.md). Role: Methods section or short Discussion paragraph only. Not used as evidence for H1–H4."

---

## Section 5 — Machine-Readable Output

Write `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`.

Structure:

```json
{
  "experiment_id": "paper1_phaseA_v1",
  "generated_at": "<ISO timestamp>",
  "h1": {
    "metric": "mean_stage_overshoot",
    "systems_evaluated": [...],
    "per_system": {
      "<system_id>": {
        "v2_2_vs_v2_1": "<lower|equal|higher>",
        "v2_2_vs_v1": "<lower|equal|higher>",
        "direction_correct": true/false
      }
    },
    "n_correct": <int>,
    "n_systems": <int>,
    "verdict": "<SUPPORTED|PARTIAL|FALSIFIED>"
  },
  "h2": {
    "metric": "exact_match_rate (with mean_loss fallback for collapsed systems)",
    "systems_evaluated": [...],
    "per_system": {
      "<system_id>": {
        "recovery_metric_used": "<exact_match_rate|mean_loss>",
        "exact_match_collapsed": true/false,
        "v2_2_competitive": true/false
      }
    },
    "n_competitive": <int>,
    "n_systems": <int>,
    "verdict": "<SUPPORTED|PARTIAL|FALSIFIED>"
  },
  "h3": {
    "metric": "mean_wasted_levels",
    "systems_evaluated": [...],
    "per_system": { ... },
    "n_correct": <int>,
    "n_systems": <int>,
    "verdict": "<SUPPORTED|PARTIAL|FALSIFIED>"
  },
  "h4": {
    "secondary": true,
    "metric": "exact_match_rate by usage policy",
    "systems_evaluated": [...],
    "per_system": { ... },
    "verdict": "<SUPPORTED|AMBIGUOUS|FALSIFIED>",
    "note": "H4 verdict does not affect H1-H3."
  },
  "auxiliary": {
    "generalization_study": {
      "verdict": "<INCLUDE_SUPPLEMENTARY|INCLUDE_WITH_CAUTION|OMIT>",
      "n_cells_with_sufficient_data": <int>,
      "summary": "<one sentence>"
    },
    "profile_init": {
      "verdict": "METHODS_ONLY",
      "note": "Not used as evidence for H1-H4."
    }
  }
}
```

---

## Section 6 — Freeze Memo

Write `docs/paper1_freeze_memo_phaseA.md`.

### Required structure

```markdown
# Paper 1 — Freeze Memo: Phase A Results
Generated: <ISO timestamp>
Experiment: paper1_phaseA_v1 (300/300 runs, all success=true)

This memo defines what Paper 1 is allowed to claim.
Nothing beyond this memo may appear in the paper.

---

## Block 1 — Primary Claims (H1, H2, H3)

### H1 — Stage Overshoot Reduction
Verdict: <SUPPORTED | PARTIAL | FALSIFIED>
Evidence: [per-system table: system | v1 overshoot | v2.1 overshoot | v2.2 overshoot | direction]
Boundary conditions: [which systems support, which do not]
Allowed paper claim: [exact wording, or "claim removed" if FALSIFIED]

### H2 — Competitive Recovery Quality
Verdict: <SUPPORTED | PARTIAL | FALSIFIED>
Evidence: [per-system table: system | GP exact_match | v2.2 exact_match | metric used | competitive?]
Collapse note: [list of systems where exact_match=0 for all methods and mean_loss was used instead]
Allowed paper claim: [exact wording]

### H3 — Wasted Levels Reduction
Verdict: <SUPPORTED | PARTIAL | FALSIFIED>
Evidence: [per-system table: system | v1 wasted | v2.1 wasted | v2.2 wasted | direction]
Boundary conditions: [which systems support, which do not]
Allowed paper claim: [exact wording, or "claim removed" if FALSIFIED]

---

## Block 2 — Secondary Claim (H4)

H4 is secondary. Its verdict does not affect H1–H3.

### H4 — Usage Policy Effect
Verdict: <SUPPORTED | AMBIGUOUS | FALSIFIED>
Evidence: [per-system table: system | hard exact_match | soft exact_match | passive exact_match | ordering]
Allowed paper claim: [exact wording, or "C3 weakened, not reportable as positive result" if AMBIGUOUS/FALSIFIED]

---

## Block 3 — Auxiliary Evidence

### Generalization Study
Verdict: <INCLUDE_SUPPLEMENTARY | INCLUDE_WITH_CAUTION | OMIT>
Evidence: [table: system | n_exact_runs | mean_refit_loss | mean_fresh_loss]
Allowed use: supplementary material only, one interpretive sentence in discussion.

### profile_init
Role: Methods section or short Discussion paragraph.
Not used as evidence for H1–H4. No figures or tables generated.

---

## Known Limitations

- System 11: EvoGrow achieves loss ~4e-15 but exact_match=0 due to growth-without-pruning
  accumulating zero-coefficient terms. This is a genuine algorithmic limitation, not a
  metric error. Must be stated explicitly in the paper.
- [any other limitations identified during analysis]

---

## Freeze Status

Evidence scope is frozen after this memo.
No new experiments may be added to Paper 1.
```

---

## Constraints

- No figures generated
- No paper tables generated
- Script exits with error if aggregate CSV is missing
- Script prints a summary to stdout on completion
- All paths come from config, none hardcoded
- The freeze memo is the authoritative output; the diagnostics JSON is machine-readable support

---

## Verification

After running the script, verify:
1. `h1_h4_diagnostics.json` exists and is valid JSON
2. `docs/paper1_freeze_memo_phaseA.md` exists and contains all three blocks
3. Every verdict is one of the defined values (not free text)
4. Per-system tables in the memo match the aggregate CSV values exactly
