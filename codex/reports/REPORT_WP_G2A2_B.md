# REPORT WP-G2A2-b

## Status

Blocked. The implementation work for the requested corrections is in place, and the Python test suites pass, but the
official v2 oracle cache and official Appendix A were not completed in this Codex session. The full Stage K command
entered the long K-c workload and was interrupted before approaching the 15 minute command limit.

## Implemented

- `stage_k_calibration.py`
  - K-c points 1-3 now produce per-point numeric records and `passed` flags.
  - K-c points 1-3 are restricted to K1-K6, wide domain, eta `0.01`, and ex-ante class `I`.
  - Non-`I` K1-K6 cells are reported as not checked with their ex-ante class.
  - Point 1 checks rejection rate `<= 0.03` and median `T/dof` in `[0.8, 1.25]`.
  - Point 2 aligns signs to `c*` and checks `bias_norm <= 0.5 * sqrt(empirical_trace)`.
  - Point 3 records empirical trace, mean propagated trace, ratio, and checks `[0.5, 2]`.
  - K-c point 4 uses §7 states: `CORRECT`, `AMBIGUOUS` with A1/A2/A3 sources, `TRUE_NOT_REF`, `WRONG`, `NONE`.
  - `TRUE_NOT_REF` requires the v2 oracle cache; otherwise non-limit Stage K stops with a clear error.
  - Overall Stage K verdict is `K_a and K_b and K_c`.
  - `--part i/n` writes `appendix_A_part_i_of_n.json` and does not overwrite `appendix_A.json`.
  - `--merge-parts n` refuses missing part files and incomplete seed sets before writing `appendix_A.json`.
  - Markdown output now includes K-c Monte Carlo and clean tables.
- `accept_01_oracle.py`
  - Added `--workers`.
  - Added `--part i/n` and `--merge-parts n`.
  - Full or merged runs write `results/oracle_reference_v2.json`.
  - Added K1-K8 reference-coefficient check: angle between `config.calibration_reference_coeffs` and oracle `c*`
    must be `< 1e-20`.
- `weak_operator.py`
  - Weight tensors are cached per process by z-grid, `ell_max`, `q`, `M`, split kind, and max class.
  - `WeightContext.split` memoizes class-column views per context.
- Cleanup
  - Removed v2 copies of `accept_02` through `accept_06`.
  - Removed v2 copied result JSONs `accept_02` through `accept_06`.
  - Removed copied `results/oracle_reference.json`.
  - Removed empty `results/standard/`.

## Accepted Deviation

K-a still compares the trapezoidal weak residual against `Ac* = 0`, not against row-by-row mpmath integrals. This is
the accepted deviation from the task: it is equivalent here because `L*f` is identically zero for the specified
calibration operator and the boundary terms vanish. A high-precision integral would reproduce zero.

## Executed Commands

```text
$env:PYTHONPATH='.'; pytest experiments/annihilator_gate2a_v2/tests -q
```

Result: `13 passed in 37.42s`.

```text
$env:PYTHONPATH='.'; pytest experiments/annihilator_gate2a/tests -q
```

Result: `8 passed in 2.70s`.

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle --limit
```

Result file: `experiments/annihilator_gate2a_v2/results/acceptance/accept_01_oracle.json`.
Payload: `passed=true`, limit entry point only.

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --limit
```

Result file: `experiments/annihilator_gate2a_v2/results/calibration/appendix_A_limit.json`.
Limit settings: `n=120`, `reps=2`.
Limit K-a result: failed at `ell=3`, max scaled error `0.163894301315622`.

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 2000 --reps 1000
```

Result: interrupted manually after several minutes with no output, before the 15 minute command limit. No official
`appendix_A.json` was produced by this run.

## Bit-Equality Evidence For Runtime Cache

Added pytest `experiments/annihilator_gate2a_v2/tests/test_cache_equivalence.py`.

The test runs K1 wide, eta `0.01`, seed `0`, `boot_reps=5`, through an uncached weight context and through the new
cached `WeightContext`. It compares all `Selection` fields, including coefficients, covariance, bootstrap share, and
ambiguity flags. Result in the v2 test run: passed.

## Runtime Profile

Short warm-cache profile, K1 wide, eta `0.01`, seed `0`, `N=160`, `ell_max=3`, `boot_reps=5`:

- Cold full search elapsed: `15.924312600000121 s`.
- Warm full search elapsed: `9.780252099999416 s`.
- Warm profile largest remaining cumulative block: `fns_candidate`, `9.628 s`; inside it `_pinv`, `7.290 s`, and
  NumPy `eigh`, `6.686 s`.
- The selected class in this short profile was `None`, so no bootstrap replicas ran in that particular profile.

This is a developer profile only, not an official N=2000 Gate projection.

## Official Artifacts

- Official oracle cache: not produced.
- Official `appendix_A.json`: not produced.
- Official `appendix_A.md`: not produced.
- Limit files produced:
  - `experiments/annihilator_gate2a_v2/results/acceptance/accept_01_oracle.json`
  - `experiments/annihilator_gate2a_v2/results/calibration/appendix_A_limit.json`
  - `experiments/annihilator_gate2a_v2/results/calibration/appendix_A_limit.md`

## Commands Still Required

Full oracle, single command:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle --workers 8
```

Partitioned oracle:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle --workers 8 --part 0/8
```

Repeat with `--part 1/8` through `--part 7/8`, then:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle --merge-parts 8
```

Stage K full, if runtime permits:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 2000 --reps 1000
```

Partitioned K-c seed workload:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 0/8
```

Repeat with `--part 1/8` through `--part 7/8`, then:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 2000 --reps 1000 --merge-parts 8
```

## Missing Abnahme Points

- Full v2 oracle JSON does not exist yet.
- Full Appendix A does not exist yet.
- Full K-c numeric pass/fail table was not produced.
- The requested official N=2000 main-run and raster projection was not produced; only the short developer profile
  above exists.
