# WP-H7 Report

## Implementation

- `studies/regression/generate_phase_b_manifest.jl` now writes `indices_cost_desc.txt` together
  with the existing `indices_all.txt` and `indices_dim1.txt` through `indices_dim4.txt` when called
  with `--all-dimensions`.
- The cost sort uses named constants from `docs/hpc_requirements.md` Section 2:
  dim 1 = 250.0 s, dim 2 = 10,440.0 s, dim 3 = 63,800.0 s, dim 4 = 2,300.0 s.
- Derived descending class order: dim 3, dim 2, dim 4, dim 1.
- Sorting is stable (`MergeSort`), so rows keep manifest order inside each dimension class.
- No individual system is preferred inside a class. This ignores known expensive systems within a
  dimension class by design; the index list is a dimension-class scheduling heuristic only.
- `k8s/phase_b_indexed_campaign_job.yaml` was added for the full campaign.
- `SCRIPTS.md` now records the campaign start order and points to
  `docs/hpc_deployment_guide.md` Section 7 for the maintained command sequence.

## Kubernetes manifest

`k8s/phase_b_indexed_campaign_job.yaml` parses as YAML.

- `kind`: `Job`
- `metadata.name`: `evoode-phase-b-campaign`
- `completions`: 756
- `parallelism`: 16
- `backoffLimit`: 1
- `EVO_BATCH_MANIFEST`: `/outputs/phase_b_campaign_<COMMIT_SHA>/manifest.csv`
- `EVO_BATCH_INDEX_LIST`: `/outputs/phase_b_campaign_<COMMIT_SHA>/indices_cost_desc.txt`
- `EVO_BATCH_OUTPUT_DIR`: `/outputs/phase_b_campaign_<COMMIT_SHA>/tasks`

`backoffLimit: 1` was chosen because a cell then gets one retry after its first failed pod attempt;
after two failed attempts it is not retried indefinitely.

## Acceptance

1. Manifest regeneration: blocked locally. The default `julia.exe` resolves to the WindowsApps stub
   and fails before running code:
   `A specified logon session does not exist. It may already have been terminated`.
   The explicit Julia 1.11.5 binary starts, but `import Pkg` fails before project code runs:
   `SystemError: longpath: Access is denied`.
   Therefore I could not regenerate the manifest in this session and could not re-confirm
   `phase_b_fingerprint=604e79733b22d64d`, `rows=756`, and `unique_identities=756` from the
   generator output.
2. Permutation check: not completed on a newly generated `indices_cost_desc.txt` because item 1 is
   blocked. Static verification against the existing `outputs/wp_h4_mapping/manifest.csv` gives
   756 rows and 756 unique sorted indices.
3. Order check from the same existing manifest and the implemented sort key:
   first five indices `307, 308, 309, 310, 311`; last five indices
   `512, 513, 514, 515, 516`; class starts `1:dim3`, `121:dim2`, `457:dim4`, `481:dim1`.
   Class counts are dim 3 = 120, dim 2 = 336, dim 4 = 24, dim 1 = 276.
4. Byte-identical double generation: blocked by the same Julia `Pkg` load failure as item 1.
5. YAML parse: passed. `completions=756` and `parallelism=16`.

No cluster job was started.
