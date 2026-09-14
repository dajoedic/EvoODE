# WP-C4a Report

## Status

Implemented the Phase-C SINDy baseline, trajectory hashes, and the Python-side pairing machinery.
The work package is blocked only on acceptance criterion 1: rerunning the unchanged WP-N6 script
with the old WP-N6 config did not produce byte-identical outputs because WP-N6 writes runtime
columns.

## Files

- `analysis/scripts/aggregate/run_phasec_sindy_baseline.py`
- `analysis/configs/paper1_phaseC_sindy_baseline.json`
- `analysis/tests/test_phasec_sindy_baseline.py`
- `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/*.csv`
- `analysis/tables/paper1_phaseC_v1/phasec_sindy_baseline/*`
- `analysis/data/paper1_phaseC_v1/phasec_sindy_paired.csv`
- `analysis/tables/paper1_phaseC_v1/phasec_sindy_pairing/phasec_sindy_paired_summary.csv`

## Commands Run

```text
python -m py_compile analysis/scripts/aggregate/run_phasec_sindy_baseline.py analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py
pytest -q analysis/tests/test_phasec_sindy_baseline.py --basetemp .pytest_tmp
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py run-sindy --config analysis/configs/paper1_phaseC_sindy_baseline.json
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py pair --sindy-details analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv --evogrow-records-dir outputs/phase_c_p9_pilot_records
pytest -q analysis/tests --basetemp .pytest_tmp
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py check-wpn6-bitidentical --config analysis/configs/wp_n6_sindy_baseline.json
```

`pytest -q analysis/tests --basetemp .pytest_tmp` passed:

```text
52 passed in 13.06s
```

The focused WP-C4a tests passed:

```text
5 passed
```

## Phase-C SINDy Output Check

The Phase-C run used `studies/regression/phase_c_support.json` as the representability source.
The loader asserts the Phase-C basis name `staged_polynomial_basis_with_constant` and the expected
support counts: 30 exact systems and 33 surrogate systems. It does not read
`analysis/data/paper1_phaseB_v1/representational_adequacy.csv`.

Written SINDy rows:

```text
details rows: 2520
systems: 63
initial_condition_set values: 1, 2
configurations: 10
directions: IC1_to_IC2 1260, IC2_to_IC1 1260
regimes: reconstruction 1260, generalization 1260
trajectory hashes: 126 rows, 63 systems
trajectory checks: 126 success
representability: surrogate 33, exact 30
summary rows: 382
cost rows: 1260
```

Reconstruction control:

```text
reconstruction_control_valid: true 2354, false 166
diverged_or_nonfinite: false 2047, true 473
```

Rows with nonzero/invalid reconstruction control are marked invalid and excluded from pairing and
summaries.

## Trajectory Hash Format

`trajectory_hashes.csv` writes one row per `(system_id, initial_condition_set)`.

Hash format:

- `hash_format = sha256_raw_little_endian_float64`
- time vector and state matrix are hashed separately
- arrays are converted to contiguous little-endian Float64 before hashing
- time hash input order: one-dimensional time axis
- state hash input order: C-order matrix with axes `(time, dimension)`
- row includes `time_shape`, `state_shape`, `time_min`, `time_max`, `state_min`, and `state_max`

This is the format for the later Julia-side reproduction.

## Pairing

The pairer takes EvoGrow records through `--evogrow-records-dir`; it has no default pointing at the
running C-1 campaign. It validates Phase-C identity fields, `basis_name`, complete
seed-condition coverage for the requested input, and uniqueness of:

- `git_hash`
- `config_fingerprint`
- `stage_cap_behavior_fingerprint`

For the 16 local pilot records:

```text
paired rows: 70
systems: 2, 24, 52, 63
directions: IC1_to_IC2 35, IC2_to_IC1 35
configurations: 10
reconstruction_control_valid: true 70
evogrow_seed_policy: mean_rate_over_available_phasec_seeds
```

The paired output carries SINDy raw/pruned structure hits, SINDy `r2_gt_0_9`, EvoGrow raw/pruned
structure-hit seed rates, EvoGrow `r2_gt_0_9` seed rate, dimension, and
`phasec_representability_threeway`. The summary groups by dimension and Phase-C representability;
there is no unlayered headline aggregate.

## WP-N6 Bit-Identity Blocker

The old WP-N6 script was not modified. Its old config was rerun through:

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py check-wpn6-bitidentical --config analysis/configs/wp_n6_sindy_baseline.json
```

The command exited nonzero:

```text
Error: WP-N6 bit-identical check failed for:
analysis\data\wp_n6_sindy_baseline\details.csv
analysis\data\wp_n6_sindy_baseline\costs.csv
analysis\tables\wp_n6_sindy_baseline\wp_n6_costs.csv
analysis\tables\wp_n6_sindy_baseline\wp_n6_costs.tex
```

The mismatching files are the WP-N6 outputs that include runtime fields
`fit_elapsed_s_non_evidence` and `elapsed_s_non_evidence_total`. The deterministic outputs
`trajectory_check.csv`, `summary.csv`, and their table copies matched byte-for-byte in this check.

This means acceptance criterion 1 cannot be honestly marked complete without changing either the
old WP-N6 output contract or the bit-identity criterion. WP-N6 output files under
`analysis/data/wp_n6_sindy_baseline/` and `analysis/tables/wp_n6_sindy_baseline/` were not
overwritten.

## Notes

The full pytest run created `.codex_tmp` test-temp data. An attempted cleanup was blocked by the
environment policy, so the directory was left in place.
