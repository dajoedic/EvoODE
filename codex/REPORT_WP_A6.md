# WP-A6 Report - Paired Pretuning Contrast

## Commands

```powershell
python analysis/scripts/aggregate/analyze_pretuning_contrast.py --config analysis/configs/paper1_phaseB_v1.json
python analysis/scripts/aggregate/analyze_pretuning_contrast.py --config analysis/configs/paper1_phaseB_v1.json --input analysis/fixtures/wp_a6_incomplete_pairing.csv --expected-total-pairs 2 --expected-exact-pairs 2 --expected-surrogate-pairs 0 --output outputs/wp_a6_fixture_should_not_exist.json
python -m py_compile analysis/scripts/aggregate/analyze_pretuning_contrast.py
```

The fixture command exited non-zero with:

```text
Error: incomplete or duplicate pair for system_id=3, seed=42, initial_condition_set=1
```

## Output

Machine-readable result:

```text
analysis/data/paper1_phaseB_v1/pretuning_contrast.json
```

Pairing checks passed for the full registry:

| group | pairs | systems |
|---|---:|---:|
| exact | 120 | 20 |
| surrogate | 258 | 43 |
| total | 378 | 63 |

The script also checks and passed: no incomplete pairs, expected pair counts, no loss equal to the sentinel `1e6`, numeric `r2` in all 756 rows, positive loss for `log10`, and non-empty targets for both conditions.

## Randomization

| quantity | value |
|---|---:|
| permutation count | 100000 |
| bootstrap replicates | 10000 |
| seed | 20260907 |
| permutation unit | system_id |
| bootstrap unit | system_id |

## Exact Support Match

Target: `exact_support_match` on exact systems only. Difference is `pretune_on - pretune_off`.

Full paired contingency table:

| pretune_off | pretune_on | pairs |
|---:|---:|---:|
| 0 | 0 | 57 |
| 0 | 1 | 3 |
| 1 | 0 | 13 |
| 1 | 1 | 47 |

| statistic | value |
|---|---:|
| hit count difference on-minus-off | -10 |
| discordant pairs | 16 |
| paired proportion difference | -0.0833333 |
| cluster bootstrap 95% CI | [-0.191667, 0.0166667] |
| naive exact McNemar p | 0.0212708 |
| cluster permutation p | 0.217718 |

Descriptive dimension breakdown, no per-dimension tests:

| dim | pairs | off 0 / on 0 | off 0 / on 1 | off 1 / on 0 | off 1 / on 1 |
|---:|---:|---:|---:|---:|---:|
| 1 | 36 | 6 | 0 | 3 | 27 |
| 2 | 54 | 21 | 3 | 10 | 20 |
| 3 | 24 | 24 | 0 | 0 | 0 |
| 4 | 6 | 6 | 0 | 0 | 0 |

## R2

Target: `r2` on surrogate systems only. Difference is `pretune_on - pretune_off`; positive favors pretuning.

| statistic | value |
|---|---:|
| pairs | 258 |
| systems | 43 |
| median paired difference | -8.18734e-13 |
| cluster bootstrap 95% CI | [-1.47671e-10, -1.33227e-14] |
| naive Wilcoxon statistic | 13153.5 |
| naive Wilcoxon p | 0.00723412 |
| cluster permutation p | 0.0269697 |

## Loss

Loss is analyzed as `log10(loss_on) - log10(loss_off)`. The raw loss spans many orders of magnitude, so the log transform makes multiplicative changes comparable while preserving the paired sign. Negative values favor pretuning; values near zero mean no material multiplicative change.

Exact systems:

| statistic | value |
|---|---:|
| pairs | 120 |
| systems | 20 |
| median log10 difference | 4.66649e-12 |
| cluster bootstrap 95% CI | [-0.0209357, 0.0134891] |
| median fold change on/off | 1.000000000010745 |
| fold change 95% CI | [0.952937, 1.03155] |
| naive Wilcoxon statistic | 2907 |
| naive Wilcoxon p | 0.294846 |
| cluster permutation p | 0.590064 |

Surrogate systems:

| statistic | value |
|---|---:|
| pairs | 258 |
| systems | 43 |
| median log10 difference | 3.48752e-11 |
| cluster bootstrap 95% CI | [6.12205e-13, 1.79774e-08] |
| median fold change on/off | 1.000000000080303 |
| fold change 95% CI | [1.0000000000014098, 1.000000041394406] |
| naive Wilcoxon statistic | 12540 |
| naive Wilcoxon p | 0.00595798 |
| cluster permutation p | 0.0105799 |

## Naive vs Cluster-Robust Tests

The exact-support result changes materially: the naive exact McNemar p-value is 0.0212708, while the system-cluster permutation p-value is 0.217718. The naive test treats 120 pairs as independent; the cluster test uses the 20 systems as the randomization unit and no longer gives small-p evidence.

For surrogate `r2`, both procedures produce small p-values, but the cluster permutation p-value is larger: 0.0269697 versus 0.00723412. The median effect is -8.18734e-13, so the numerical effect is extremely small even though the paired signs are systematic enough to affect p-values.

For loss, exact systems have no small-p result in either procedure: 0.294846 naive and 0.590064 cluster-robust. Surrogate loss has small p-values in both procedures, 0.00595798 naive and 0.0105799 cluster-robust, with a median fold change of 1.000000000080303 on/off.
