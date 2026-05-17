# CURRENT TASK: WP-0.1 — Correct H4 Claim in Freeze Memo

**Language: Python**

## Context

Phase A of `paper1_phaseA_v1` produced an H4 verdict of SUPPORTED — but this verdict is
vacuous: all three usage-policy variants (`hard`, `soft`, `passive`) achieve
`exact_match_rate = 0` on every high-stage system. The expected ordering
`hard >= soft >= passive` holds only because all values are equal (0 = 0 = 0).
This is not a meaningful result. The current freeze memo and diagnostics JSON
incorrectly present this as a positive finding.

## What Needs to Change

### 1. `analysis/scripts/aggregate/evaluate_hypotheses.py`

**Line ~521** — the H4 "Allowed paper claim" block currently reads:

```python
Allowed paper claim: {"Hard usage policy follows the expected hard >= soft >= passive ordering on the majority of high-stage systems." if h4["verdict"] == "SUPPORTED" else "C3 weakened, not reportable as positive result"}
```

Replace the entire conditional with the fixed string (no conditional needed):

```python
Allowed paper claim: C3 cannot be evaluated — all usage-policy variants achieve exact_match_rate = 0 on all high-stage systems. The expected ordering holds vacuously through ties only.
```

**Line ~521 vicinity** — also change the H4 verdict output in the memo from `SUPPORTED`
to `VACUOUS`. The verdict string in the diagnostics JSON must be updated to match.

To do this, change the `evaluate_h4` function so that:
- If all `exact_match_rate` values across all systems and all three usage-policy variants
  are 0, override the verdict to `"VACUOUS"` instead of `"SUPPORTED"`.
- Add a `"vacuous": true` field to the H4 diagnostics dict in this case.
- The existing note field in the H4 diagnostics JSON must read:
  `"H4 verdict is vacuous. All usage-policy variants achieve exact_match_rate = 0 on all high-stage systems. Ordering holds through ties only. H4 does not affect H1-H3."`

### 2. Regenerate outputs

After the code fix, run:

```
python analysis/scripts/aggregate/evaluate_hypotheses.py --config analysis/configs/paper1_phaseA_v1.json
```

This regenerates both output files:
- `docs/paper1_freeze_memo_phaseA.md`
- `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`

## Verification

After running the script, verify:

1. `docs/paper1_freeze_memo_phaseA.md` contains:
   - H4 Verdict: `VACUOUS`
   - H4 Allowed paper claim: the vacuous-result text (not the positive ordering claim)

2. `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` contains:
   - `"verdict": "VACUOUS"` under `h4`
   - `"vacuous": true` under `h4`
   - The corrected note text

3. H1, H2, H3 verdicts and tables are **unchanged**.

4. The generalization verdict is **OMIT** (path fix from WP-0.2 is already in place).

## Constraints

- Do not change any Phase A run data.
- Do not change H1, H2, H3 evaluation logic.
- Do not change the generalization evaluation logic.
- Only `evaluate_hypotheses.py` and the two regenerated output files may change.
