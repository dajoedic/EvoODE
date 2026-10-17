# WP-FA4b — Run the Q4 dim-3/dim-4 candidate fits on Orion
**Language: Julia** (plus k8s YAML)

## Why

WP-FA4's runner `studies/regression/sideproject_q4_path_fits.jl` runs dim 1/2 on the laptop (in progress, do not
touch its output). The 18 units of dim 3 and dim 4 (459 fits; system 61 fits take ~15 min each) go to Orion. The image
contains only `Project.toml`, `Manifest.toml`, `src/`, `studies/`, `benchmarks/`, `containers/` (`.dockerignore`), so
the runner's inputs outside `studies/` must come from the NFS share, and parallel pods must not append to one file.

## Changes

1. **Runner CLI, defaults unchanged.** Add options overriding the input paths the runner (and the included Q3 machinery
   it uses) reads: the Q4 paths JSON, the Q3 results JSONL, the Q3 weak-starts JSON, the WP-C4c trajectory export
   directory, and the output JSONL. Without the options, behaviour, paths and outputs stay exactly as now. Add
   `--unit-list <file> --index <i>` (0-based) as an alternative to `--units`: pick the i-th unit id from a one-id-per-line
   file. **No change to fits, settings, controls, record format or provenance fields beyond recording the override
   paths.** If a source-file hash enters provenance, the changed runner hash is expected: the aggregation must accept
   records from exactly the two runner versions (pre- and post-WP-FA4b, both hashes listed as constants) and must still
   require one identical optimizer-settings fingerprint across all records; record both hashes in the run metadata.
   Respect the WP-FA3 lessons: no time limits, no reserved words as identifiers.
2. **Aggregation:** accept several result files (glob or list) in addition to the default file; duplicates of the same
   (unit, candidate) must be bit-identical in loss, else abort; report how many duplicates were compared.
3. **Unit list** `studies/regression/sideproject_q4_orion_units.txt`: the 18 dim-3/dim-4 unit ids plus `sys0024_ic1`
   (platform control: already run on the laptop, must come out bit-identical), ordered by expected cost descending —
   use the Q3 W1 `fit_meta.fit_time_s` in `outputs/sideproject_q3_weak_start/results.jsonl` times the unit's candidate
   count from `q4_paths.json`; put the order and the numbers in the report.
4. **Manifest** `k8s/sideproject_q4_job.yaml`, modelled on `k8s/phase_c_c5_restart_curve_job.yaml`: indexed Job,
   `completions` = 19, `parallelism: 8` (project core limit: 40 in total, 32 in use), 1 CPU / 2 Gi per pod (state why
   2 Gi suffices or raise it), `JULIA_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, **no `activeDeadlineSeconds`**,
   `backoffLimit` as in the model, image `registry.gitlab.scch.at:443/joedicke/evoode:<COMMIT_SHA>`. Inputs under
   `/outputs/sideproject_q4_<COMMIT_SHA>/input/` (paths JSON, Q3 results, Q3 weak starts, the export subset for the
   needed systems with its manifest), one output file per index under `/outputs/sideproject_q4_<COMMIT_SHA>/out/`.
   Header comment with the expected runtime (~5–8 h wall, longest unit ~5 h, ~15–20 core-h, uncertainty up to ×2).
5. **Input staging list** in the report: exactly which local files must be copied to which NFS path (including the
   export binaries of systems 24, 52, 54–59, 61, 63 and a manifest restricted to them, or the full manifest if the
   loader requires it — check), with SHA256 of each.

## Forbidden

No change to fit behaviour or to `src/`; do not touch `outputs/sideproject_q4_path_fits/` (a run is writing there).
No commit, no push, no cluster command.

## Verification

Python tests for the aggregation change (multi-file, duplicate check, two runner hashes); the full analysis suite (two
known failures). Julia cannot be run by you — Claude parses and smoke-tests the CLI locally after the laptop run
finishes. Report: append "WP-FA4b" to `codex/reports/REPORT_WP_FA4.md`.
