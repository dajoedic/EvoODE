# WP-N41 Report

## Result

Implemented the WP-N41 manifest package, but local Julia validation is blocked by the Codex
environment, not by the change itself.

Files changed:

- `k8s/phase_c_c8_search_b05_job.yaml`
- `studies/regression/select_phase_c_stage2_manifest.jl`
- `test/test_wp_n33c_stage2_manifest_selection.jl`
- `SCRIPTS.md`

## Implementation

`k8s/phase_c_c8_search_b05_job.yaml` defines 3 Kubernetes Jobs:

- `evoode-phase-c-c8-search-b05-bootstrap`
- `evoode-phase-c-c8-search-b05-smoke`
- `evoode-phase-c-c8-search-b05-orion`

The bootstrap writes under `/outputs/phase_c_c8_search_b05_<COMMIT_SHA>`, creates clean-data
manifests for `clamp_val=1000` and `clamp_val=Inf`, then selects and renumbers these 10 search
cells:

```text
24, IC 1, Inf
24, IC 2, Inf
52, IC 1, 1000
52, IC 2, 1000
52, IC 1, Inf
52, IC 2, Inf
57, IC 1, 1000
57, IC 2, 1000
57, IC 1, Inf
57, IC 2, Inf
```

The smoke manifest selects System 1, IC 1, `clamp_val=1000` from the first source manifest. The
indexed search Job has `completions: 10` and `parallelism: 10`. The smoke Job has `completions: 1`
and `parallelism: 1`. There is no `activeDeadlineSeconds`.

`select_phase_c_stage2_manifest.jl` now accepts optional explicit cells:

```text
--stage2-cells system:initial_condition_set:clamp_val,...
```

Existing Stage-2/Stage-3 calls that use `--stage2-systems` keep the old selection loop and defaults.

## Local Bootstrap Dry Run for Claude

Run this outside the Codex sandbox:

```powershell
$TMP = "outputs\wp_n41_bootstrap_dryrun"
New-Item -ItemType Directory -Force "$TMP\bound_1000", "$TMP\bound_Inf" | Out-Null

julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl `
  --output "$TMP\bound_1000\manifest.csv" `
  --noise-sigma 0 --subsample-rho 0 --noise-realization 0 --clamp-val 1000 --all-dimensions

julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl `
  --output "$TMP\bound_Inf\manifest.csv" `
  --noise-sigma 0 --subsample-rho 0 --noise-realization 0 --clamp-val Inf --all-dimensions

julia --project=. --startup-file=no studies/regression/select_phase_c_stage2_manifest.jl `
  --source "$TMP\bound_1000\manifest.csv" `
  --source "$TMP\bound_Inf\manifest.csv" `
  --stage2-output "$TMP\manifest.csv" `
  --stage2-indices "$TMP\indices_c8_search_b05.txt" `
  --smoke-output "$TMP\smoke_manifest.csv" `
  --smoke-indices "$TMP\indices_smoke.txt" `
  --stage2-cells 24:1:Inf,24:2:Inf,52:1:1000,52:2:1000,52:1:Inf,52:2:Inf,57:1:1000,57:2:1000,57:1:Inf,57:2:Inf `
  --smoke-system 1 `
  --initial-condition-set 1 `
  --seed 42

Import-Csv "$TMP\manifest.csv" |
  Select-Object index,system_id,initial_condition_set,clamp_val |
  Format-Table -AutoSize
```

Pass criterion: the table has exactly 10 rows, with `index` 1 through 10 and this ordered
`system_id, initial_condition_set, clamp_val` sequence:

```text
24,1,Inf
24,2,Inf
52,1,1000
52,2,1000
52,1,Inf
52,2,Inf
57,1,1000
57,2,1000
57,1,Inf
57,2,Inf
```

## Smoke Comparison

After the Orion smoke has been collected, compare it with the completed local B-04 bound-1000 cell:

```bash
python - <<'PY'
import json
from pathlib import Path

candidate = json.loads(Path("outputs/phase_c_c8_search_b05_<SHA>/smoke/tasks/cell_000001.jsonl").read_text())
reference = json.loads(Path("outputs/b04_search_bounds/bound_1000/tasks/cell_000001.jsonl").read_text())
fields = ["loss", "support_terms", "total_loss_evals", "model_terms", "config_fingerprint"]
for field in fields:
    if candidate.get(field) != reference.get(field):
        raise SystemExit(f"{field} differs")
print("WP-N41 smoke record matches B-04 bound-1000 reference fields")
PY
```

## Checks Performed

Successful checks:

```text
python -c "import yaml, pathlib; docs=list(yaml.safe_load_all(pathlib.Path('k8s/phase_c_c8_search_b05_job.yaml').read_text())); print(len(docs)); print([d['metadata']['name'] for d in docs]); print([d['spec'].get('activeDeadlineSeconds') for d in docs])"
```

Output:

```text
3
['evoode-phase-c-c8-search-b05-bootstrap', 'evoode-phase-c-c8-search-b05-smoke', 'evoode-phase-c-c8-search-b05-orion']
[None, None, None]
```

```text
rg -n "activeDeadlineSeconds|timeout" k8s/phase_c_c8_search_b05_job.yaml studies/regression/select_phase_c_stage2_manifest.jl test/test_wp_n33c_stage2_manifest_selection.jl
```

Output: no matches.

```text
python -c "from pathlib import Path; text=Path('k8s/phase_c_c8_search_b05_job.yaml').read_text(); s='24:1:Inf,24:2:Inf,52:1:1000,52:2:1000,52:1:Inf,52:2:Inf,57:1:1000,57:2:1000,57:1:Inf,57:2:Inf'; print(text.count(s)); print(len(s.split(',')))"
```

Output:

```text
1
10
```

Blocked check:

```text
julia --project=. --startup-file=no test/test_wp_n33c_stage2_manifest_selection.jl
```

Output:

```text
Program 'julia.exe' failed to run: The file cannot be accessed by the system
```

Per `codex/CODEX_PROTOCOL.md`, this is an environment blocker for Julia execution in Codex.
