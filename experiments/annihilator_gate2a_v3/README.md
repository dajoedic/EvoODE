# Gate 2A: Annihilator Discovery

This directory implements the frozen Gate 2A specification in `docs/GATE_2A.md`.

The main modules are:

- `config.py`: frozen constants, test functions, domains, class ordering, sensitivity variants.
- `functions.py`: numeric and symbolic function definitions.
- `oracle.py`: independent symbolic/collocation reference side.
- `weak_operator.py`: test functions, analytic derivatives, and the linear weight tensor `K`.
- `operator_search.py`: candidate selection, validation test, A1 and A2.
- `transfer.py`: narrow-to-wide affine coefficient transfer.
- `run_gate2a.py`: run CLI writing `results/<variant>/runs.csv`.
- `evaluate_gate2a.py`: cell summaries and gate verdict JSON.

Commands for Claude:

```powershell
python -m experiments.annihilator_gate2a.run_gate2a --variant standard --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S1 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S2 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S3 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S4 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S5 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S6 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S7 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S8 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S9 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S10 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S11 --workers 8
python -m experiments.annihilator_gate2a.evaluate_gate2a --variant standard
```

Smoke only:

```powershell
python -m experiments.annihilator_gate2a.run_gate2a --smoke --workers 1
```

