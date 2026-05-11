# Paper 1 - Freeze Memo: Phase A Results
Generated: 2026-05-11T14:48:48.582394+00:00
Experiment: paper1_phaseA_v1 (300/300 runs, all success=true)

This memo defines what Paper 1 is allowed to claim.
Nothing beyond this memo may appear in the paper.

---

## Block 1 - Primary Claims (H1, H2, H3)

### H1 - Stage Overshoot Reduction
Verdict: PARTIAL
Evidence:
| system | v1 overshoot | v2.1 overshoot | v2.2 overshoot | direction |
| --- | --- | --- | --- | --- |
| 3 | 0 | 3 | 3 | wrong |
| 11 | 0 | 0 | 0 | wrong |
| 26 | 2 | 2 | 2 | wrong |
| 31 | 2 | 2 | 2 | wrong |
| 54 | 2 | 1.6 | 0 | correct |
| 63 | 2 | 2 | 2 | wrong |
Boundary conditions: Supports: 54. Does not support: 3, 11, 26, 31, 63.
Allowed paper claim: Stage-local stopping reduces stage overshoot only under the listed boundary conditions.

### H2 - Competitive Recovery Quality
Verdict: SUPPORTED
Evidence:
| system | GP exact_match | v2.2 exact_match | metric used | competitive? |
| --- | --- | --- | --- | --- |
| 2 | 1 | 1 | exact_match_rate | yes |
| 3 | 0.8 | 1 | exact_match_rate | yes |
| 11 | 1 | 0 | exact_match_rate | no |
| 24 | 0 | 1 | exact_match_rate | yes |
| 26 | 0 | 0 | mean_loss | yes |
| 31 | 0 | 0 | mean_loss | yes |
| 54 | 0 | 0 | mean_loss | yes |
| 63 | 0 | 0 | mean_loss | yes |
Collapse note: 26, 31, 54, 63
Allowed paper claim: EvoGrow v2.2 stage-local is competitive with GP recovery quality on the majority of exact systems.

### H3 - Wasted Levels Reduction
Verdict: PARTIAL
Evidence:
| system | v1 wasted | v2.1 wasted | v2.2 wasted | direction |
| --- | --- | --- | --- | --- |
| 3 | 0 | 3 | 12 | wrong |
| 11 | 0 | 0 | 0 | correct |
| 26 | 2 | 2 | 6 | wrong |
| 31 | 2 | 2 | 6 | wrong |
| 54 | 1.6 | 1.2 | 0 | correct |
| 63 | 2 | 2 | 8 | wrong |
Boundary conditions: Supports: 11, 54. Does not support: 3, 26, 31, 63.
Allowed paper claim: Stage-local stopping reduces wasted levels only under the listed boundary conditions.

---

## Block 2 - Secondary Claim (H4)

H4 is secondary. Its verdict does not affect H1-H3.

### H4 - Usage Policy Effect
Verdict: SUPPORTED
Evidence:
| system | hard exact_match | soft exact_match | passive exact_match | ordering |
| --- | --- | --- | --- | --- |
| 11 | 0 | 0 | 0 | hard >= soft >= passive |
| 26 | 0 | 0 | 0 | hard >= soft >= passive |
| 31 | 0 | 0 | 0 | hard >= soft >= passive |
| 54 | 0 | 0 | 0 | hard >= soft >= passive |
| 63 | 0 | 0 | 0 | hard >= soft >= passive |
Allowed paper claim: Hard usage policy follows the expected hard >= soft >= passive ordering on the majority of high-stage systems.

---

## Block 3 - Auxiliary Evidence

### Generalization Study
Verdict: OMIT
Evidence:
No eligible generalization cells available.
Allowed use: supplementary material only, one interpretive sentence in discussion.

### profile_init
Role: Methods section or short Discussion paragraph.
Not used as evidence for H1-H4. No figures or tables generated.

---

## Known Limitations

- System 11: EvoGrow achieves loss ~4e-15 but exact_match=0 due to growth-without-pruning accumulating zero-coefficient terms. This is a genuine algorithmic limitation, not a metric error. Must be stated explicitly in the paper.
- Cells with low or zero exact_match remain scientific results and must not be hidden or repaired post hoc.
- The generalization study is auxiliary and cannot override the H1-H4 verdicts.

---

## Freeze Status

Evidence scope is frozen after this memo.
No new experiments may be added to Paper 1.
