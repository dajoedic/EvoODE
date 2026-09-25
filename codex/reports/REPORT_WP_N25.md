# WP-N25 Report

## Changed files

- `studies/regression/wp_n25_phase_c_c5_common.jl` (new shared Phase-C C-5 helper)
- `studies/regression/wp_n3_oracle_refit.jl`
- `studies/regression/wp_n4_multistart_refit.jl`
- `studies/regression/wp_n5_ic_generalization.jl`
- `test/test_wp_n25_phase_c_c5.jl`
- `SCRIPTS.md`

## Implemented arguments

All three C-5 scripts now accept Phase-C mode only when explicitly requested:

- `--campaign paper1_phaseC_v1`
- `--shards N --shard-index I`
- `--collect`
- `--estimate-cost`

Without `--campaign`, the existing WP-N1 path remains the top-level `main` path.

Phase-C filtering selects only `variant == "evogrow_v2_2_stage_capped"` and
`use_pretuning == false`. Non-C-1 records are counted in the manifest. WP-N3/WP-N4 skip surrogate
systems after counting them. WP-N5 keeps exact and surrogate systems.

## Acceptance commands

Prepare Phase-C history from the dry-run task records:

```bash
julia --project=. --startup-file=no studies/regression/merge_batch_records.jl \
  --input-dir outputs/phase_c_dryrun_2026-09-25/tasks \
  --history outputs/studies/regression/phase_c/history.jsonl
```

WP-N1 bitwise behavior check: run these commands once on the pre-WP-N25 tree and once on this tree,
then compare each pair of `results.jsonl` / `starts.jsonl` files byte-for-byte.

```bash
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl \
  --input outputs/wp_n1_dim1_probe/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n3_wp_n1 \
  --limit 4 --fresh

julia --project=. --startup-file=no studies/regression/wp_n4_multistart_refit.jl \
  --input outputs/wp_n1_dim1_probe/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n4_wp_n1 \
  --starts 10 --limit 4 --fresh

julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl \
  --input outputs/wp_n1_dim1_probe/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n5_wp_n1 \
  --limit 4 --fresh
```

Phase-C hash identity smoke checks:

```bash
julia --project=. --startup-file=no studies/regression/phase_c_trajectory_hashes.jl \
  --limit 6 \
  --output-dir outputs/wp_n25_acceptance/trajectory_hashes \
  --export-dir outputs/wp_n25_acceptance/trajectory_export
```

Phase-C smoke tests, one shard/cell and collect:

```bash
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n3_phase_c \
  --limit 1 --shards 1 --shard-index 1 --fresh
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n3_phase_c \
  --limit 1 --shards 1 --collect

julia --project=. --startup-file=no studies/regression/wp_n4_multistart_refit.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n4_phase_c \
  --starts 10 --limit 1 --shards 1 --shard-index 1 --fresh
julia --project=. --startup-file=no studies/regression/wp_n4_multistart_refit.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n4_phase_c \
  --starts 10 --limit 1 --shards 1 --collect

julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n5_phase_c \
  --limit 1 --shards 1 --shard-index 1 --fresh
julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --output-dir outputs/wp_n25_acceptance/wp_n5_phase_c \
  --limit 1 --shards 1 --collect
```

Cost estimates:

```bash
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --estimate-cost

julia --project=. --startup-file=no studies/regression/wp_n4_multistart_refit.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --starts 10 --estimate-cost

julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/studies/regression/phase_c/history.jsonl \
  --estimate-cost
```

New tests:

```bash
julia --project=. --startup-file=no test/test_wp_n25_phase_c_c5.jl
```

## Not verified

Julia was not executed in this Codex environment, per `codex/CODEX_PROTOCOL.md`. Therefore the
following remain for Claude:

- WP-N1 byte-for-byte result comparison.
- Phase-C smoke runs and `--collect`.
- Hash identity comparison against `phase_c_trajectory_hashes.jl` output.
- `--estimate-cost` output on the merged Phase-C history.
- The new Julia tests.

The local file `outputs/studies/regression/phase_c/history.jsonl` was not present during this
session; `outputs/phase_c_dryrun_2026-09-25/tasks/` was present.

## WP-N25b

### Changed files

- `studies/regression/phase_c_trajectory_hash_lib.jl` (new shared hash helper; no `Pkg.activate`
  and no includes of `run_regression.jl` or `phase_c_config.jl`)
- `studies/regression/phase_c_trajectory_hashes.jl`
- `studies/regression/wp_n25_phase_c_c5_common.jl`
- `test/test_wp_n25_phase_c_c5.jl`

### Include structure

`phase_c_trajectory_hashes.jl` still owns the standalone-script path:

```julia
include(joinpath(@__DIR__, "run_regression.jl"))
include(joinpath(@__DIR__, "phase_c_config.jl"))
include(joinpath(@__DIR__, "phase_c_trajectory_hash_lib.jl"))
```

The three C-5 scripts still include `run_regression.jl`, then `phase_b_config.jl`, then
`wp_n25_phase_c_c5_common.jl`. The common helper no longer includes
`phase_c_trajectory_hashes.jl`; it includes `phase_c_config.jl` only when `PHASE_C_ID` is not
already defined, and includes the hash library only when `HASH_FORMAT` is not already defined.

Static name scan of `phase_b_config.jl` and `phase_c_config.jl`: no same-name top-level
`const` or `function` definitions were found. Phase B uses `PHASE_B_*`, `phase_b_*`, and
`_phase_b_*`; Phase C uses `PHASE_C_*`, `phase_c_*`, and `_phase_c_*`.

### Hash behavior

The moved code is the previous byte serialization and row construction logic:

- `HASH_FORMAT = "sha256_raw_little_endian_float64"`
- little-endian Float64 vector hashing
- time-by-dimension C-order matrix hashing
- `trajectory_hash_row`
- raw byte export helpers used by `phase_c_trajectory_hashes.jl`

No hash constants, byte order, axis order, row columns, or export path suffixes were changed.

### Test coverage change

`test/test_wp_n25_phase_c_c5.jl` now loads:

- `wp_n3_oracle_refit.jl` in the main test module, as before
- `wp_n4_multistart_refit.jl` in an isolated module
- `wp_n5_ic_generalization.jl` in an isolated module
- `phase_c_trajectory_hashes.jl` in an isolated module

This makes a load-time include collision visible before the existing functional assertions run.

### Acceptance commands for Claude

Short load/test path:

```bash
julia --project=. --startup-file=no test/test_wp_n25_phase_c_c5.jl
```

Hash identity check requested for WP-N25b:

```bash
julia --project=. --startup-file=no studies/regression/phase_c_trajectory_hashes.jl \
  --limit 6 \
  --output-dir outputs/wp_n25b_acceptance/trajectory_hashes \
  --export-dir outputs/wp_n25b_acceptance/trajectory_export
```

Then compare the generated `trajectory_hashes_julia.csv` byte-for-byte with the corresponding
pre-WP-N25b file from the same command.

Full hash run:

```bash
julia --project=. --startup-file=no studies/regression/phase_c_trajectory_hashes.jl \
  --output-dir outputs/wp_n25b_acceptance/trajectory_hashes_full \
  --export-dir outputs/wp_n25b_acceptance/trajectory_export_full
```

Full WP-N25 acceptance remains the command set listed above in this report.

### Not verified

Julia was not executed in this Codex environment, per `codex/CODEX_PROTOCOL.md`. Therefore the
load fix, the new test load checks, and the byte-identical `phase_c_trajectory_hashes.jl --limit 6`
hash comparison remain for Claude.
