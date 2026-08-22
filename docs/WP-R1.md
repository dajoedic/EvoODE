# WP-R1 - Full-basis least-squares representation reference

This reference is the best fit obtained by unregularized least squares on the derivative problem over the full current staged basis. It is a deterministic, reproducible reference for this fitting procedure, not a proven optimum over all possible trajectory-space fits of the model class.

CSV: `outputs\studies\representation\wp_r1_full_basis_reference\full_basis_reference.csv`

## Acceptance

- Completeness: 126 rows, 126 unique `(system_id, ic_set)` pairs, 0 duplicates, 0 missing pairs.
- Exact systems: 20 system ids: `2, 3, 6, 8, 11, 12, 24, 25, 26, 27, 28, 29, 31, 32, 38, 54, 55, 56, 61, 63`.
- Stability: 13 of 126 fitted models diverged during integration.
- Diverged cells: `[[24, 1], [26, 2], [31, 2], [37, 1], [48, 1], [51, 1], [51, 2], [52, 2], [53, 1], [62, 1], [62, 2], [63, 1], [63, 2]]`.

Trajectory R2 distribution:

| group | n | min | q25 | median | mean | q75 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| exact | 35 | -120.2192232 | 0.3019211292 | 0.999907652 | -2.835507946 | 0.9999999377 | 1 |
| surrogate | 78 | -12.18198307 | 0.9990843988 | 0.9999976764 | 0.5309354553 | 0.9999999706 | 1 |

Derivative-space R2 distribution:

| group | n | min | q25 | median | mean | q75 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| exact | 40 | 0.9962371961 | 0.9999629046 | 0.9999977895 | 0.9998023723 | 0.9999996402 | 0.9999999639 |
| surrogate | 86 | 0.4656309256 | 0.9994287991 | 0.9999927362 | 0.9850374179 | 0.9999990987 | 0.999999991 |

Trajectory MSE distribution:

| group | n | min | q25 | median | mean | q75 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| exact | 40 | 2.819603347e-13 | 7.692459503e-08 | 0.0007319997159 | 1111087.959 | 133.5766195 | 40441028.61 |
| surrogate | 86 | 8.24346713e-14 | 2.432278977e-08 | 1.99181248e-05 | 93025.10527 | 0.06538949709 | 1000000 |

## Exact systems below trajectory R2 0.99

| system | ic_set | trajectory_r2 | trajectory_mse | derivative_r2 |
|---:|---:|---:|---:|---:|
| 24 | 1 | null | 1000000 | 0.9999992237 |
| 24 | 2 | -0.7300232266 | 0.0296132395 | 0.9999992228 |
| 26 | 2 | null | 1000000 | 0.9999800868 |
| 27 | 1 | 0.9658865267 | 0.2103104919 | 0.9998241752 |
| 29 | 1 | 0.5865084435 | 0.1581029291 | 0.9999937998 |
| 29 | 2 | 0.01733381488 | 0.07966228881 | 0.999997973 |
| 31 | 1 | -120.2192232 | 294.1727179 | 0.9999982346 |
| 31 | 2 | null | 40441028.61 | 0.9999899159 |
| 32 | 2 | 0.9892583004 | 0.7168898935 | 0.9999739316 |
| 55 | 1 | -0.7374978821 | 744.7202603 | 0.9984043326 |
| 55 | 2 | -0.8669490596 | 789.304138 | 0.999300429 |
| 56 | 1 | -0.2996418691 | 89.88378625 | 0.9999635732 |
| 56 | 2 | -0.4656227452 | 108.6361358 | 0.999791275 |
| 61 | 1 | -0.9375420807 | 253.4183627 | 0.9995758235 |
| 61 | 2 | -0.5336201547 | 208.3980707 | 0.9997586397 |
| 63 | 1 | null | 1000000 | 0.9999993709 |
| 63 | 2 | null | 1000000 | 0.999999639 |

## Determinism

The script writes deterministic CSV and summary content with no timestamps. Determinism was checked by running the script twice and comparing the CSV byte-for-byte.
