# WP-G2A3-c - Appendix B diagnostic

## Summary

Implemented `experiments/annihilator_gate2a_v3/acceptance/appendix_b.py` and factored the shared ex-ante identifiability logic into `stage_k_calibration.ex_ante_cell`.

Appendix B was not executed in this Codex session because the runtime estimate exceeds the 15 minute session limit. The required full command is:

```powershell
python -m experiments.annihilator_gate2a_v3.acceptance.appendix_b --n 2000 --workers 4
```

`--workers` accepts 1 through 6; the command above uses 4 workers as specified for the runtime decision.

## Stage K Parameters

The Appendix B loader reads all present non-limit files matching:

```text
experiments/annihilator_gate2a_v3/results/calibration/appendix_A_part_*_of_8.json
```

Present sources: 7 files.

Values read from every present file:

| Parameter | JSON field | Value |
|---|---|---:|
| ell_max | `K_a.ell_max` | 4 |
| tau | `K_b.tau` | 3.386508022297224e-07 |

The script aborts if any present part file disagrees on either value.

## Runtime Estimate

Measured command:

```powershell
python -c "import time; from experiments.annihilator_gate2a_v3.acceptance.appendix_b import load_stage_k_parameters; from experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration import ex_ante_cell; from experiments.annihilator_gate2a_v3.config import FUNCTIONS; params=load_stage_k_parameters(); print(params['ell_max'], params['tau'], len(params['sources'])); start=time.perf_counter(); record=ex_ante_cell('F1', FUNCTIONS['F1'], 'wide', 0.01, params['ell_max'], params['tau'], 2000); elapsed=time.perf_counter()-start; print(elapsed); print(record['class'], record['theta_hat_c'], len(record['earlier']))"
```

Output:

```text
4 3.386508022297224e-07 7
67.74629350000032
I 0.002777804616306632 2
```

F1/wide/eta=0.01 uses 2 earlier classes plus the reference class, i.e. 3 AML evaluations. Appendix B uses 236 AML evaluations across F1-F10, both domains, and eta in {0.01, 0.05}. A linear lower-bound projection from this measured cell gives about 21.6 minutes at 4 workers, before accounting for heavier cells such as F10.

## Class Table

Not produced in this Codex session because Appendix B was not executed under the 15 minute rule. The script writes the table to:

```text
experiments/annihilator_gate2a_v3/results/appendix_B/appendix_B.md
```

and the structured data to:

```text
experiments/annihilator_gate2a_v3/results/appendix_B/appendix_B.json
```

## K6 Diagnostic

Not produced in this Codex session because Appendix B was not executed under the 15 minute rule. The implemented diagnostic counts wide F1-F8 cells with `r_ref <= 3` at `eta = 0.01` classified as N1 or N2, and reports `would_trigger = true` iff the count is greater than 1.

## Verification

Passed:

```powershell
python -m pytest experiments/annihilator_gate2a_v3/tests -q
```

Result:

```text
28 passed in 122.76s (0:02:02)
```

Passed:

```powershell
python -m pytest experiments/annihilator_gate2a_v3/tests/test_stage_k_and_caching.py -q
```

Result:

```text
9 passed in 53.50s
```

Passed:

```powershell
python -m py_compile experiments/annihilator_gate2a_v3/acceptance/appendix_b.py experiments/annihilator_gate2a_v3/acceptance/stage_k_calibration.py
```

Passed:

```powershell
python -m experiments.annihilator_gate2a_v3.acceptance.appendix_b --help
```
