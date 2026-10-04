# REPORT WP-G2A-b

## Status

Blocked.

The implementation was extended under `experiments/annihilator_gate2a/`, but the literal Gate 2A acceptance was not completed in this Codex session. The full mpmath oracle build started through `pytest` did not finish before the per-command 15 minute limit became imminent and was interrupted after about 12.5 minutes. No oracle results from that interrupted run are reported as accepted.

## Changes

- Replaced the stale double-precision oracle cache with a required metadata contract:
  - method: `sympy_derivatives_mpmath_svd`
  - precision: 60 decimal digits
  - points: 120
  - relative threshold: `1e-35`
- `build_reference()` now refuses stale oracle caches without the required metadata and verifies reference classes against `docs/GATE_2A.md`.
- Deleted the previous `experiments/annihilator_gate2a/results/oracle_reference.json` double-precision cache.
- Added a reusable `WeightContext` that builds the largest `(6,6)` fit/validation tensors once per grid and selects class columns from it.
- Reused the same tensor support across bootstrap replicas by rebuilding only the value-dependent matrices.
- Added non-smoke `GIT_COMMIT` enforcement in `run_gate2a.py`.
- Added narrow-domain transfer evaluation and fills `transfer_passed`.
- Replaced the K2/K3 verdict stubs with per-criterion JSON entries containing value, threshold, and pass flag. `TRUE_NOT_REF` is not counted as K2.
- Added six acceptance scripts under `experiments/annihilator_gate2a/acceptance/`, each writing JSON under `results/acceptance/`.

## Files Changed

- `experiments/annihilator_gate2a/config.py`
- `experiments/annihilator_gate2a/oracle.py`
- `experiments/annihilator_gate2a/weak_operator.py`
- `experiments/annihilator_gate2a/operator_search.py`
- `experiments/annihilator_gate2a/run_gate2a.py`
- `experiments/annihilator_gate2a/evaluate_gate2a.py`
- `experiments/annihilator_gate2a/acceptance/__init__.py`
- `experiments/annihilator_gate2a/acceptance/common.py`
- `experiments/annihilator_gate2a/acceptance/accept_01_oracle.py`
- `experiments/annihilator_gate2a/acceptance/accept_02_weak_strong.py`
- `experiments/annihilator_gate2a/acceptance/accept_03_covariance_mc.py`
- `experiments/annihilator_gate2a/acceptance/accept_04_transfer.py`
- `experiments/annihilator_gate2a/acceptance/accept_05_determinism.py`
- `experiments/annihilator_gate2a/acceptance/accept_06_smoke.py`
- deleted `experiments/annihilator_gate2a/results/oracle_reference.json`

## Checks Run

Command:

```powershell
python -m pytest experiments/annihilator_gate2a/tests -q
```

Result:

```text
One test dot was printed. The run was interrupted after about 12.5 minutes because the full mpmath oracle build had not finished and the 15 minute command limit was approaching.
```

Command:

```powershell
$files = @(rg --files experiments/annihilator_gate2a | Where-Object { $_ -like '*.py' }); python -m py_compile @files
```

Result:

```text
passed
```

Command:

```powershell
python -c "from experiments.annihilator_gate2a.config import FUNCTIONS, Settings, domain_for; from experiments.annihilator_gate2a.functions import noisy_sample; from experiments.annihilator_gate2a.operator_search import search_once; s=Settings(n=300,modes=6,boot_reps=2); d=domain_for(FUNCTIONS['F2'],'wide'); _,z,v,_=noisy_sample('F2',d,s.n,0.0,0); sel=search_once(z,v,0.0,s); print(sel.selected_class, sel.tested_classes)"
```

Result:

```text
(3, 0) 4
```

This command checked that the optimized tensor/search path executes; it is not an acceptance-strength class result.

Command:

```powershell
python -c "from experiments.annihilator_gate2a.evaluate_gate2a import summarize, verdict_for; rows=[{'function':'F2','domain':'wide','eta':'0.01','seed':'0','state':'WRONG','selected_r':'2','selected_d':'0','coeff_angle':'','transfer_passed':''} for _ in range(10)]; rows += [{'function':'F2','domain':'wide','eta':'0.01','seed':'10','state':'CORRECT','selected_r':'1','selected_d':'0','coeff_angle':'','transfer_passed':''}]; cells=summarize(rows); print(cells); print(verdict_for(rows,cells)['criteria']['k2'])"
```

Result:

```text
[{'function': 'F2', 'domain': 'wide', 'eta': '0.01', 'n': 11, 'CORRECT': 1, 'AMBIGUOUS': 0, 'TRUE_NOT_REF': 0, 'WRONG': 10, 'NONE': 0, 'transfer_passed': 0, 'transfer_total': 0}]
{'value': {'cell': ('F2', 'wide', '0.01'), 'class': '2,0', 'count': 10}, 'threshold': 'kill if a WRONG class reaches >= 10 of 20 in any 1% cell', 'passed': False}
```

## Acceptance Status

1. Oracle: implemented with mpmath/SymPy metadata and stale-cache refusal, but not completed in this session. The full build was interrupted near the command limit.
2. Weak matrix vs strong form: script added, not accepted. No full 200,000 point result was produced.
3. Covariance Monte Carlo: script added, not accepted. No 1,000 realization result was produced.
4. Transfer angle: script added and transfer column wired, not accepted. No full angle table was produced.
5. Determinism: script added, not accepted. No 1-worker vs 4-worker acceptance run was produced.
6. Smoke: script added, not accepted. No smoke runtime or extrapolation was produced.
7. `pytest experiments/annihilator_gate2a/tests`: not green in this session because the mpmath oracle build did not finish before interruption.

## Commands for Claude

Short path:

```powershell
python -m pytest experiments/annihilator_gate2a/tests -q
python -m experiments.annihilator_gate2a.acceptance.accept_01_oracle --limit
python -m experiments.annihilator_gate2a.acceptance.accept_02_weak_strong --limit
python -m experiments.annihilator_gate2a.acceptance.accept_03_covariance_mc --limit
python -m experiments.annihilator_gate2a.acceptance.accept_04_transfer --limit
python -m experiments.annihilator_gate2a.acceptance.accept_05_determinism --limit
python -m experiments.annihilator_gate2a.acceptance.accept_06_smoke --limit
```

Full acceptance:

```powershell
python -m experiments.annihilator_gate2a.acceptance.accept_01_oracle
python -m experiments.annihilator_gate2a.acceptance.accept_02_weak_strong
python -m experiments.annihilator_gate2a.acceptance.accept_03_covariance_mc
python -m experiments.annihilator_gate2a.acceptance.accept_04_transfer
python -m experiments.annihilator_gate2a.acceptance.accept_05_determinism
python -m experiments.annihilator_gate2a.acceptance.accept_06_smoke
```

Smoke and run commands:

```powershell
python -m experiments.annihilator_gate2a.run_gate2a --smoke --workers 1
$env:GIT_COMMIT = "<commit>"
python -m experiments.annihilator_gate2a.run_gate2a --variant standard --workers 8
python -m experiments.annihilator_gate2a.evaluate_gate2a --variant standard
```

## Blocker

The blocker is the session command limit: the full mpmath oracle construction did not complete before the 15 minute limit became imminent. Therefore the required acceptance numbers cannot be reported from this session.
