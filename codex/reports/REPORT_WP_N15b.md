# WP-N15b Report

## Changes

- Added safe CLI path display for `aggregate_wp_n1_dim2_probe.py`: output paths are printed relative to the repository when possible and as absolute paths otherwise, so success paths with `--output-dir` outside the repository no longer fail.
- Changed WP-N1 dim-2 support matching so `wp_n1_expected_support_terms == null` is accepted for surrogate cells and remains invalid for exact cells.
- Marked `raw_support_match` and `pruned_support_match` as not applicable for surrogate cells by writing empty CSV values, not `False`.
- Changed structure hit denominators in the decision table to count only exact cells via `raw_support_denominator` and `pruned_support_denominator`; surrogate-only rows have denominator `0` and blank support rates.

## New Tests

- `test_output_directory_outside_repo_success_path_runs_through`
- `test_surrogate_without_expected_support_terms_is_not_applicable`
- `test_exact_without_expected_support_terms_returns_nonzero`

The existing fixture factory now mirrors the real data relationship: exact cells carry `wp_n1_expected_support_terms`, surrogate cells carry `null`.

## Test Result

```text
....................................                                     [100%]
36 passed in 12.42s
```

Command:

```text
python -m pytest analysis/tests -q --basetemp outputs/pytest-wp-n15b-full
```

The real-record run was not executed because the `S:\` share is not visible from the Codex session.
