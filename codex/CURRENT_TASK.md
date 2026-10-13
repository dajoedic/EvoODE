# WP-T2a-impl-c — make the T2a manifest portable to Orion (prior paths)
**Language: Julia**

## Why

Claude's controls of WP-T2a-impl / -b all passed (bit-identity 3/3, tests, Phase C manifest identical in all 13 frozen
columns — the 4 extra columns are WP-N32's clean defaults —, T2a manifest 252/126/126/20, oracle smoke loads and
records the prior). Before the image build Claude found a blocking portability defect:

- `experiments/paper2_t2a_pilot_v1/manifest.csv` stores `candidate_prior_path` as an **absolute Windows path**
  (`C:\Users\...\experiments\paper2_t2a_pilot_v1\priors\...json`), and `t2a_variant_from_row` /
  `t2a_fingerprint_from_row` load the prior from exactly that path. On Orion every S1 cell would fail.
- `experiments/` is **not in the image** (`.dockerignore` admits only `src/`, `studies/`, `benchmarks/`), so even a
  repository-relative path would not resolve inside the pod.

Decision (Claude): do **not** change the Dockerfile or `.dockerignore` (pipeline compliance, `CHANGELOG.md`). Instead
the priors travel with the manifest to the NFS, exactly like the C-5 input history: the pod reads
`/outputs/paper2_t2a_pilot_v1_<SHA>/manifest.csv` and finds the priors next to it.

## Deliverables

1. The manifest builder writes `candidate_prior_path` **relative to the manifest's directory**, with forward slashes
   (e.g. `priors/oracle_prior_system_0024_ic1.json`). No absolute path may appear anywhere in the T2a manifest or the
   index files.
2. Loading resolves a relative `candidate_prior_path` against the directory of the manifest actually being read
   (`EVO_BATCH_MANIFEST` in the pod, `--manifest` locally). An absolute path in the column is refused with a clear
   error (it can only be a stale manifest). Thread the manifest directory through whatever call chain needs it; do
   not rely on the current working directory.
3. The config fingerprint must stay a function of the prior **content** only (it already is — keep it so; the path
   must not enter it). The oracle smoke fingerprint for system 24 seed 42 IC 1 was `52edf2893b9d9e70`; it must not
   change.
4. Test: a manifest in a temporary directory with a relative prior path resolves and loads; an absolute path is
   refused; the fingerprint is identical whether the manifest+priors are read from the repository or from a copied
   directory.
5. `SCRIPTS.md`: the S1 sequence — regenerate the manifest; copy `manifest.csv`, `indices_s1_oracle_dim2_seed42.txt`
   and the whole `priors/` folder to `/s/BigDataOrion/data-science/joedicke/paper2_t2a_pilot_v1_<SHA>/` (mounted NFS);
   `oc apply` of `k8s/paper2_t2a_s1_job.yaml` with the SHA; collection from `/paper2_t2a_s1_<SHA>/tasks`.
6. Report `codex/reports/REPORT_WP_T2A_IMPL_C.md` with Claude's control commands: the test; regenerate the manifest
   and grep it for `:\\` / absolute paths (must find none); the oracle smoke run **from a copied directory**
   (manifest + indices + priors copied to e.g. `tmp/t2a_portable/`) giving fingerprint `52edf2893b9d9e70` and the same
   `loss`, `support_terms`, `total_loss_evals` as the earlier smoke (`outputs/t2a_controls/oracle_smoke/cell_000067.jsonl`).

## Verboten

- Changing the Dockerfile, `.dockerignore`, CI, search behaviour, the sampler, the prior files' content, the C-1 path or
  any Phase C identity. Running Julia. Committing. Editing this file.

## Abnahme

- Code, test, docs, report; `STATUS.md` `done` (Julia not executed) or `blocked`.
