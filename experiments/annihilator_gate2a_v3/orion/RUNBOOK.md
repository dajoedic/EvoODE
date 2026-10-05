# Orion runbook: ambiguity diagnostic main run

Spec: `docs/DIAGNOSTIC_AMBIGUITY.md` §6 (N = 100, 11 pods × 1 core, about 32 h). Code is bundled from git with
`git archive` at the commit recorded in `COMMIT`. Nothing is built into an image: the pods use `python:3.12-slim`
and install pinned wheels offline from NFS.

NFS layout (`/bigdata/data-science/joedicke`, mounted at `/outputs`):

```
annihilator_diag_amb/
  COMMIT                  code commit of the bundle
  code/experiments/...    v3 code + oracle_reference_v3.json + calibration/appendix_A.json
  wheels/                 numpy 2.2.6, scipy 1.13.1, sympy 1.13.1, mpmath 1.3.0 (manylinux, cp312)
  results/records.jsonl   the 12 pilot records (excluded from the parts)
  results/parts/part_<i>_of_11/{records.jsonl,run.log,nullspace_cache.json,DONE}
```

## 1. Build the staging tarball (local)

`stage.tar` contains `code/` (git archive of `experiments/annihilator_gate2a_v3` without `results/` and `tests/`,
plus the two result files above), `wheels/`, `results/records.jsonl` and `COMMIT`.

## 2. Stage onto NFS (from the directory that contains `stage.tar`; relative paths, since `oc cp` misreads `C:`)

```
oc apply -f <repo>/experiments/annihilator_gate2a_v3/orion/helper.yaml
oc wait --for=condition=Ready pod/annihilator-diag-amb-helper --timeout=300s
oc exec annihilator-diag-amb-helper -- sh -c "test ! -e /outputs/annihilator_diag_amb && mkdir -p /outputs/annihilator_diag_amb"
oc cp stage.tar annihilator-diag-amb-helper:/outputs/annihilator_diag_amb/stage.tar
oc exec annihilator-diag-amb-helper -- sh -c "cd /outputs/annihilator_diag_amb && tar -xf stage.tar && rm stage.tar && cat COMMIT && wc -l results/records.jsonl"
```

The `test ! -e` guard refuses to overwrite an existing directory.

## 3. Smoke test inside the helper (offline install, imports, references, partition)

```
oc exec annihilator-diag-amb-helper -- sh -c "pip install --quiet --no-index --target /tmp/pylib --find-links /outputs/annihilator_diag_amb/wheels numpy==2.2.6 scipy==1.13.1 sympy==1.13.1 mpmath==1.3.0 && cd /outputs/annihilator_diag_amb/code && PYTHONPATH=/tmp/pylib PYTHONDONTWRITEBYTECODE=1 python -c \"from pathlib import Path; from experiments.annihilator_gate2a_v3.diagnostics import ambiguity_diagnostic as d; s=d.diagnostic_settings(); d.validate_references(d.load_oracle_cache()); print(s.ell_max, s.sigma_floor_factor, [len(d.tasks_for_part(100,(i,11),Path('/outputs/annihilator_diag_amb/results/records.jsonl'))) for i in range(11)])\""
```

Pass: `4 3.386508022297224e-07 [54, 54, 54, 54, 54, 53, 53, 53, 53, 53, 53]`.

## 4. Start

```
oc apply -f <repo>/experiments/annihilator_gate2a_v3/orion/job.yaml
oc get pods -l app=annihilator-diag-amb
```

## 5. Monitor (state-free progress lines only)

```
oc exec annihilator-diag-amb-helper -- sh -c "cd /outputs/annihilator_diag_amb/results/parts && for p in part_*; do printf '%s %s %s\n' $p $(cat $p/run.log 2>/dev/null | grep -vc WARNING) $(test -f $p/DONE && echo DONE); done"
```

Expected: 53–54 lines per part at the end, each about 36 min apart on average.

## 6. Collect and merge

```
oc exec annihilator-diag-amb-helper -- sh -c "cd /outputs/annihilator_diag_amb && tar -cf /tmp/results.tar results"
oc cp annihilator-diag-amb-helper:/tmp/results.tar results.tar
```

Then, locally, unpack into `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/orion/` and run
`--merge --reps 100 --outdir <that dir>` and `--summarize --records <that dir>/records_merged.jsonl --outdir <that dir>`.
Delete the helper pod afterwards: `oc delete pod annihilator-diag-amb-helper`.
