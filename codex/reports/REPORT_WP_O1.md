# WP-O1 Report

## Changes

- Moved the two Python tests from root-level `tests/` to `analysis/tests/`.
- Updated both tests to compute `REPO_ROOT` as `Path(__file__).resolve().parents[2]`.
- Added import-time root guards in both test files:
  - `(REPO_ROOT / "CLAUDE.md").is_file()`
  - `(REPO_ROOT / "benchmarks").is_dir()`
- Updated `test_unknown_variant_is_not_silently_dropped_from_main_table` to call
  `build_csv_table(pd.DataFrame(rows), exact_ids=[2], surrogate_ids=[23])`.
- Added `analysis/tests/` to `analysis/CONVENTIONS.md`, including allowed and forbidden contents.
- Removed the resolved Python-test-location and red-test Known Gaps from `CLAUDE.md`; kept the
  remaining gap that nothing runs the Python tests.

## Path Check

After the move, a test path has this shape:

```text
analysis/tests/test_*.py
```

Therefore:

- `parents[0]` is `analysis/tests`
- `parents[1]` is `analysis`
- `parents[2]` is the repository root

The tests now assert the root by checking that `CLAUDE.md` exists as a file and `benchmarks/` exists
as a directory under `REPO_ROOT`.

## Variant-Visibility Fix

The visibility test uses systems 2 and 23. The repaired call passes:

```python
exact_ids=[2]
surrogate_ids=[23]
```

The invariant is unchanged: `campaign_unknown_variant` must be present in the generated CSV table.

## Counterprobe

I temporarily changed `build_csv_table` locally so that it used only known variants from
`VARIANT_ORDER` and dropped extra observed variants. Then I ran:

```bash
python -m pytest analysis/tests/test_analysis_variant_visibility.py -q -p no:cacheprovider
```

Result:

```text
1 failed
AssertionError: assert 'campaign_unknown_variant' in {'evogrow_v1'}
```

The temporary break was reverted immediately afterward.

## Acceptance

Command:

```bash
python -m pytest analysis/tests -q -p no:cacheprovider
```

Result:

```text
4 passed in 2.20s
```

The root-level `tests/` directory no longer exists:

```text
Test-Path -LiteralPath tests -> False
```

## Notes

The task requested `git mv`, but `codex/CODEX_PROTOCOL.md` explicitly forbids Git operations. I
moved the files through the filesystem instead and left the changes uncommitted and unstaged.
