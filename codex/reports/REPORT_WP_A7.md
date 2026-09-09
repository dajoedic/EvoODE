# WP-A7 Report - Distribution-Aware Effect Size and Seed Collapse

## Commands

```powershell
python -m py_compile analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py
python analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py --config analysis/configs/paper1_phaseB_v1.json --input analysis/fixtures/wp_a7_bad_support_terms.csv --expected-total-pairs 0 --expected-exact-pairs 0 --expected-surrogate-pairs 0 --expected-collapse-groups-per-condition 0 --output outputs/wp_a7_bad_support_terms/should_not_exist.json
python analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py --input experiments/paper1_phaseB_v1/history.jsonl --output experiments/paper1_phaseB_v1/run_registry.csv --experiment-id paper1_phaseB_v1
python analysis/scripts/aggregate/verify_campaign_registry.py --input experiments/paper1_phaseB_v1/run_registry.csv
python analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py --config analysis/configs/paper1_phaseB_v1.json
```

The fixture command exited non-zero with:

```text
Error: support_terms is not valid JSON: not-json
```

The converter command wrote:

```text
Converted 756 campaign records
  Input:  experiments\paper1_phaseB_v1\history.jsonl
  Output: experiments\paper1_phaseB_v1\run_registry.csv
```

The unchanged registry invariant check wrote:

```text
Verified campaign registry: 756 rows
  Unique identities: 756
  Condition column: condition
  Rows per condition: {'pretune_off': 378, 'pretune_on': 378}
  Representability: exact=240, surrogate=516
  git_hash: 91f88c4
  config_fingerprint: 604e79733b22d64d
  stage_cap_behavior_fingerprint: ffb0266c7913352c
  Numeric surrogate r2 rows: 516
```

Machine-readable result:

```text
analysis/data/paper1_phaseB_v1/pretuning_distribution_collapse.json
```

The new analysis is a second script rather than an edit of the A6 script because it produces a different result family: distribution quantiles, full threshold grids, and seed-collapse tables. Keeping it separate avoids changing the already completed A6 paired contrast output.

## Registry Columns

The regenerated registry carries exactly these seven additional columns after the previous columns:

```text
support_terms, condition, use_pretuning, n_levels, eq_overshoot, eq_final_stages, stage_caps
```

`support_terms`, `eq_overshoot`, `eq_final_stages`, and `stage_caps` are written as JSON cells. Example first data row:

```text
"[[""u1"",""u1^2"",""u1^3"",""cos(u1)""]]",pretune_on,True,30,null,[5],[5]
```

## Randomization

| quantity | value |
|---|---:|
| permutation count | 100000 |
| bootstrap replicates | 10000 |
| seed | 20260907 |
| permutation unit | system_id |
| bootstrap unit | system_id |

Pairing checks passed:

| group | pairs | systems |
|---|---:|---:|
| exact | 120 | 20 |
| surrogate | 258 | 43 |
| total | 378 | 63 |

Seed-collapse grouping checks passed:

| condition | groups |
|---|---:|
| pretune_off | 126 |
| pretune_on | 126 |

The script also checks and passed: complete pretuning pairs, expected pair counts, no sentinel loss `1e6`, numeric and non-missing `r2`, positive loss for `log10`, non-empty targets, exactly three rows and three distinct seeds per seed-collapse group, and parseable JSON in every `support_terms` cell.

## R2 Distribution

Target: `r2` on surrogate systems only. Difference is `pretune_on - pretune_off`; positive favors pretuning.

| quantile | value |
|---:|---:|
| 0.05 | -0.0807121354 |
| 0.10 | -0.0198207051 |
| 0.25 | -9.920151286e-06 |
| 0.50 | -8.187339695e-13 |
| 0.75 | 5.858985377e-08 |
| 0.90 | 0.0199583202 |
| 0.95 | 0.1110536404 |

Full threshold grid:

| threshold | on count | on share | on CI95 | off count | off share | off CI95 |
|---:|---:|---:|---:|---:|---:|---:|
| 1e-04 | 46 | 0.178294574 | [0.096899225, 0.271317829] | 63 | 0.244186047 | [0.151162791, 0.348837209] |
| 1e-03 | 36 | 0.139534884 | [0.069767442, 0.220930233] | 56 | 0.217054264 | [0.124031008, 0.317829457] |
| 1e-02 | 30 | 0.116279070 | [0.046511628, 0.193895349] | 36 | 0.139534884 | [0.065891473, 0.228682171] |
| 1e-01 | 16 | 0.062015504 | [0.015503876, 0.120155039] | 13 | 0.050387597 | [0.015503876, 0.093023256] |

Sign asymmetry:

| favors pretune_on | favors pretune_off | exact zero | cluster permutation p |
|---:|---:|---:|---:|
| 81 | 174 | 3 | 0.0005399946 |

## Loss Distribution

Loss is analyzed as `log10(loss_on) - log10(loss_off)`. Negative values favor pretuning.

Exact systems:

| quantile | value |
|---:|---:|
| 0.05 | -1.182011271 |
| 0.10 | -0.5548805906 |
| 0.25 | -0.0674075243 |
| 0.50 | 4.666489417e-12 |
| 0.75 | 0.1261450270 |
| 0.90 | 2.497231358 |
| 0.95 | 7.304433566 |

| fold threshold | on count | on share | on CI95 | off count | off share | off CI95 |
|---:|---:|---:|---:|---:|---:|---:|
| 1.1 | 35 | 0.291666667 | [0.133333333, 0.466666667] | 35 | 0.291666667 | [0.141666667, 0.450000000] |
| 2 | 13 | 0.108333333 | [0.016666667, 0.233333333] | 26 | 0.216666667 | [0.108333333, 0.333333333] |
| 10 | 7 | 0.058333333 | [0.000000000, 0.141666667] | 21 | 0.175000000 | [0.075000000, 0.283333333] |
| 100 | 4 | 0.033333333 | [0.000000000, 0.100000000] | 14 | 0.116666667 | [0.033333333, 0.208333333] |

| favors pretune_on | favors pretune_off | exact zero | cluster permutation p |
|---:|---:|---:|---:|
| 52 | 62 | 6 | 0.6681633184 |

Surrogate systems:

| quantile | value |
|---:|---:|
| 0.05 | -0.8579539433 |
| 0.10 | -0.5779865895 |
| 0.25 | -5.551033233e-08 |
| 0.50 | 3.487521383e-11 |
| 0.75 | 0.0339994070 |
| 0.90 | 0.2445619649 |
| 0.95 | 0.9507566555 |

| fold threshold | on count | on share | on CI95 | off count | off share | off CI95 |
|---:|---:|---:|---:|---:|---:|---:|
| 1.1 | 52 | 0.201550388 | [0.120155039, 0.290697674] | 56 | 0.217054264 | [0.131782946, 0.313953488] |
| 2 | 32 | 0.124031008 | [0.062015504, 0.197674419] | 24 | 0.093023256 | [0.034883721, 0.162790698] |
| 10 | 12 | 0.046511628 | [0.011627907, 0.085271318] | 12 | 0.046511628 | [0.015503876, 0.085271318] |
| 100 | 1 | 0.003875969 | [0.000000000, 0.011627907] | 0 | 0.000000000 | [0.000000000, 0.000000000] |

| favors pretune_on | favors pretune_off | exact zero | cluster permutation p |
|---:|---:|---:|---:|
| 74 | 176 | 8 | 0.0000899991 |

## Collapse Tolerance and Support Normalization

Numeric collapse uses `abs(value - first) <= absolute + relative * abs(first)`, with default relative tolerance `1e-12` and absolute tolerance `0.0`. This keeps the default purely relative; loss values near zero do not get a tolerance floor that would collapse small absolute differences by construction. Loss values are still required to be positive, and the reported loss spread is the range of `log10(loss)` within the three-seed group.

Support collapse parses the JSON cell, preserves equation order, sorts terms within each equation, serializes the normalized structure back to canonical JSON, and then compares exactly. Equation order is preserved because equations map to state dimensions; term order inside one equation is normalized because it is a support set, not a coefficient vector.

## Seed Collapse

Target: `r2`.

| group | off collapsed | on collapsed | off share | on share | pairs | systems | off no/on no | off no/on yes | off yes/on no | off yes/on yes | McNemar p | cluster p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| exact | 14/40 | 29/40 | 0.350000000 | 0.725000000 | 40 | 20 | 11 | 15 | 0 | 14 | 0.0000610352 | 0.0008999910 |
| surrogate | 21/86 | 67/86 | 0.244186047 | 0.779069767 | 86 | 43 | 19 | 46 | 0 | 21 | 2.842170943e-14 | 0.0000099999 |
| all | 35/126 | 96/126 | 0.277777778 | 0.761904762 | 126 | 63 | 30 | 61 | 0 | 35 | 8.673617380e-19 | 0.0000099999 |

Target: `loss`.

| group | off collapsed | on collapsed | off share | on share | pairs | systems | off no/on no | off no/on yes | off yes/on no | off yes/on yes | McNemar p | cluster p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| exact | 1/40 | 29/40 | 0.025000000 | 0.725000000 | 40 | 20 | 11 | 28 | 0 | 1 | 7.450580597e-09 | 0.0000599994 |
| surrogate | 13/86 | 67/86 | 0.151162791 | 0.779069767 | 86 | 43 | 19 | 54 | 0 | 13 | 1.110223025e-16 | 0.0000099999 |
| all | 14/126 | 96/126 | 0.111111111 | 0.761904762 | 126 | 63 | 30 | 82 | 0 | 14 | 4.135903063e-25 | 0.0000099999 |

Target: `support_terms`.

| group | off collapsed | on collapsed | off share | on share | pairs | systems | off no/on no | off no/on yes | off yes/on no | off yes/on yes | McNemar p | cluster p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| exact | 16/40 | 29/40 | 0.400000000 | 0.725000000 | 40 | 20 | 11 | 13 | 0 | 16 | 0.0002441406 | 0.0036899631 |
| surrogate | 45/86 | 67/86 | 0.523255814 | 0.779069767 | 86 | 43 | 19 | 22 | 0 | 45 | 0.0000004768 | 0.0001899981 |
| all | 61/126 | 96/126 | 0.484126984 | 0.761904762 | 126 | 63 | 30 | 35 | 0 | 61 | 5.820766091e-11 | 0.0000099999 |

R2 spread per group is stored in the JSON as seven quantiles and the maximum range. For all systems, the off-condition R2 range quantiles are `[2.775557562e-16, 4.524158825e-15, 6.452061108e-13, 1.163557429e-07, 0.0088025539, 0.1304719514, 0.2121596315]` with max `0.3558688932`; the on-condition quantiles are `[0, 0, 0, 0, 0, 0.0421474702, 0.0802696075]` with max `0.3558689011`.

Loss spread per group is stored in the JSON as seven quantiles of the `log10(loss)` range and the maximum range. For all systems, the off-condition quantiles are `[1.861011345e-14, 3.614886168e-13, 7.869026653e-09, 0.0356266476, 0.3381360141, 0.7561472866, 1.2103736993]` with max `6.8473146496`; the on-condition quantiles are `[0, 0, 0, 0, 0, 0.1155821026, 0.4197676201]` with max `2.6683660160`.

The support-pattern collapse shows the same directional pattern as R2: across all 126 paired system/IC groups, `pretune_on` has 96 collapsed groups, while `pretune_off` has 61 for support and 35 for R2. The support comparison is less extreme in raw off-condition counts than R2, but all discordant support pairs go in the same direction: 35 off-no/on-yes and 0 off-yes/on-no.
