# Idea #1: Annihilator-Guided ODE Discovery (closed, failed)

> **Archive of a closed research track.** This branch (`annihilator-discovery` in the EvoODE repository) holds
> only this idea: its plan, the code, the results and how it developed. It is unrelated to EvoGrow, which lives on
> `main`.
>
> **Status:** closed on 2026-10-08, the idea failed.
>
> **Tags:** `idea01-annihilator-closed` marks the state at the closing decision; `idea01-annihilator-archive`
> marks this cleaned-up archive.
>
> The documents are in German; code, comments and this README are in English.

## The idea

For a 1D ODE $\dot x = f(x)$, do not guess symbolic formulas for $f$. Instead, first identify from data the
simplest linear differential operator with polynomial coefficients that annihilates $f$:

$$
L = \sum_{k=0}^{r} p_k(x)\,D^k, \qquad p_k(x) = \sum_{j=0}^{d} c_{kj}\,x^j, \qquad L f = 0 .
$$

Many function families have such annihilators: exponentials ($D - a$), powers ($xD - p$), $\log x$
($xD^2 + D$), $x\log x$, Gaussians and rational functions. The solution space of $L$ then becomes a data-driven
hypothesis space for $f$, and a least-squares fit inside it gives $\hat f$.

The method had four building blocks:

1. **Weak form:** derivatives of $f$ are moved onto smooth test functions by integration by parts, so the
   operator matrix is linear in the observed values $f_i$.
2. **Statistical test:** because of that linearity the residual covariance is analytic. Accepting an operator
   class $(r, d)$ becomes a $\chi^2$ test instead of a hand-set threshold.
3. **Minimality:** the search takes the first class that is not rejected, in the order $C = (r+1)(d+1)$.
4. **Abstention:** an explicit `AMBIGUOUS` result when the data do not identify the operator.

The hoped-for advantages: structure before parameters, function families beyond a fixed library (Gompertz was
the motivating case), linear algebra instead of expression search, and a principled "the data are not enough".

## What was tested

Seven checks. Each decision rule was frozen before the first run, and a change after that needed a new version.
A sealed test set (ODEBench 4/49/59/62) was never looked at.

| # | Check | Input | Outcome | Documents (`docs/`) |
|---|---|---|---|---|
| 1 | Gate 2A v1 | noisy $(x, f)$ samples | blocked at acceptance, never run: inaccurate matrix, biased estimator | `GATE_2A.md` |
| 2 | Gate 2A v2 | noisy $(x, f)$ samples | calibration stage failed: the estimator converged to saddle points | `GATE_2A_v2*.md` |
| 3 | Gate 2A v3 | noisy $(x, f)$ samples | not passed: uncertainty underestimated 2–7× from order 3; kill criterion K6 triggered | `GATE_2A_v3*.md` |
| 4 | Diagnostic of `AMBIGUOUS` | noisy $(x, f)$ samples | negative: 118 of 118 confident answers in the non-identifiable cases were wrong | `DIAGNOSTIC_AMBIGUITY*.md` |
| 5 | Reality check | same samples | direct sparse regression recovers the hard cases in 60 of 60 | `REALITY_CHECK_DIRECT_REGRESSION*.md` |
| 6 | ODEBench smoke test | oracle $f$, ODEBench systems 3/7/19/21 | true structure 2/4 without noise, 0/4 at 1 % | `ODEBENCH_SMOKE_TEST*.md` |
| 7 | End-to-end comparison | only noisy trajectories, identical for all methods | see below | `ODEBENCH_END2END*.md` |

**End-to-end comparison, at 1 % noise:** SINDy, Weak SINDy and the annihilator were run on the logistic
equation, Gompertz, logistic with harvesting and SIR. The table shows the share with $R^2 \ge 0.9$; v2 is the
annihilator with a smoothing spline, v1 used an interpolating spline (a setup error).

| | Logistic | Gompertz | Harvesting | SIR |
|---|---|---|---|---|
| Reconstruction, annihilator v1 → v2 (of 20) | 4 → 17 | 0 → 14 | 5 → 20 | 4 → 19 |
| Reconstruction, SINDy / Weak SINDy (of 20) | 20 / 14 | 17 / 20 | 16 / 18 | 20 / 20 |
| Generalisation to the other ODEBench initial condition, annihilator v2 / best baseline (of 10) | 8 / 5 | 0 / 0 | 10 / 6 | 8 / 5 |
| Extrapolation to new initial conditions, annihilator v2 / best baseline (of 15) | 10 / 12 | 0 / 5 | 13 / 13 | 5 / 5 |
| Exact structure, annihilator v2 (of 15) | 4 | 0 | 0 | 0 |

## Why it failed

The core promise was not met in any of the seven checks:

- **Structure first:** at 1 % noise the true structure was recovered only for the logistic equation. The
  complexity ordering prefers classes with constant coefficients. These are exponential polynomials with free
  rates, flexible enough to mimic $\log x$, $x\log x$ or $x/(K+x)$ within the noise, and they come before the
  true classes with $x$-dependent coefficients.
- **Gompertz,** the motivating case, was missed even without noise and was the weakest system end to end.
- **The abstention** measures stability, not identifiability. A systematically wrong class is stable, so
  `AMBIGUOUS` did not catch it.
- **Noise:** the weak form shifts derivatives onto test functions, but the noise amplification of higher
  orders remains. From order 3 the uncertainty calculation is wrong; from order 4 the information is not in the
  data.
- **Trajectories:** the weak form integrates in $x$. It removes derivatives of $f$ but not the time derivative
  $\dot x$, so end to end the method needs a derivative estimate like SINDy, unlike Weak SINDy.

**What did work:** the method finds first- and second-order operators with simple coefficients, and the
statistical test is calibrated there. With careful smoothing, end-to-end function accuracy was competitive with
the baselines. Whether that comes from the operator or from the smoothing is unresolved, and function accuracy
was never the goal.

The full account, including the lessons and what a restart would need, is in `docs/IDEA_01_RETROSPECTIVE.md`.

## Where to read

| What | Where |
|---|---|
| Plan of the idea, and closure with an evidence table (§12) | `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` |
| Retrospective: motivation, development, reasons for failure, lessons | `docs/IDEA_01_RETROSPECTIVE.md` |
| Specification and result of each check | `docs/` (table above) |
| Origin of the idea (superseded note) | `docs/idea_structural_diagnostics.md` |
| Discarded draft of a practical benchmark | `docs/PRACTICAL_ANNIHILATOR_BENCHMARK.md` |
| Chronology, 2026-10-04 to 2026-10-08 | `DIARY.md` |
| Work packages and the implementer's reports (code was written by Codex to written specifications) | `codex/` |

## Repository layout

```
docs/                              specifications, results, plan, retrospective
experiments/
  annihilator_gate2a/              Gate 2A v1 (frozen)
  annihilator_gate2a_v2/           Gate 2A v2 (frozen)
  annihilator_gate2a_v3/           Gate 2A v3; diagnostics/ holds the AMBIGUOUS diagnostic and the reality check,
                                   orion/ the cluster runbook
  annihilator_odebench_smoke/      ODEBench smoke test (run.py) and end-to-end comparison (end2end.py)
benchmarks/data/strogatz_extended.json   ODEBench system definitions (used by the smoke and end-to-end tests)
codex/                             work-package protocol, reports
DIARY.md, READ_THIS_FIRST.md, CLAUDE.md  chronology, final handover, working rules
requirements.txt                   pinned Python environment
```

The three Gate 2A folders are self-contained and behaviourally frozen: later versions copy rather than modify
earlier code. `annihilator_odebench_smoke` builds on `annihilator_gate2a_v3`. Results and records sit next to the
code under `results*/`.

## Reproducing

```
pip install -r requirements.txt
```

**Tests:** run them per folder. Several versions contain test files with the same name, so a single pytest run
over all folders fails at collection.

```
python -m pytest experiments/annihilator_gate2a
python -m pytest experiments/annihilator_gate2a_v2
python -m pytest experiments/annihilator_gate2a_v3
python -m pytest experiments/annihilator_odebench_smoke
```

Status at archiving: 8 + 16 + 54 + 34 tests passed.

**Entry points**, run from the repository root:

| Check | Command |
|---|---|
| Gate 2A v1–v3 | `python -m experiments.annihilator_gate2a_v3.run_gate2a --help`, then `evaluate_gate2a`; likewise for `_v2` and v1 |
| Calibration stage (stage K) | `python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --help` |
| `AMBIGUOUS` diagnostic | `python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --help` |
| Reality check | `python -m experiments.annihilator_gate2a_v3.diagnostics.direct_regression_check --help` |
| ODEBench smoke test | `python -m experiments.annihilator_odebench_smoke.run --help` |
| End-to-end v1 / v2 | `python -m experiments.annihilator_odebench_smoke.end2end --spec end2end_v2 --run --workers 7` |

**Caveats:**

- **Cost:** the end-to-end run takes about 10 hours on a laptop with 7 workers.
- **Weak SINDy is not bit-reproducible:** pysindy 2.1.0 draws its test-function centres from the global
  `np.random` without a seed.
- **Raw end-to-end records** (2 × 910 MB) are not in git. The committed `records_compact.jsonl` files keep all
  metrics and coefficients. The raw files are archived on the institute's Orion NFS, with checksums in
  `experiments/annihilator_odebench_smoke/RAW_RECORDS_SHA256.txt`.
