# WP-N33b Report

Implemented the Orion preparation artifacts for R-05 Stage 2 / System 18 and B-02 bound oracle runs.

## Files

- `analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py`
- `k8s/phase_c_robustness_stage2_system18_job.yaml`
- `k8s/phase_c_c8_oracle_b02_job.yaml`
- `SCRIPTS.md`
- `outputs/phase_c_c8_oracle_b02_input/history.jsonl`

## Design Notes

Stage 2 uses an Orion bootstrap job rather than a local manifest copied to NFS. The bootstrap runs `generate_phase_c_manifest.jl` once per robustness condition and filters the generated Phase-C rows inside the same image that later runs `run_batch_cell.jl`. That keeps the WP-N32 columns, config fingerprint, and parser behavior coupled to the runtime image.

B-02 uses `analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py` to filter the real Phase-C C-1 history to the 21 exact dim-1/2 systems from `phase_c_support.json`, 3 seeds, and 2 IC sets. The output has 126 records.

The B-02 manifests use 18 shards per bound. This is based on the existing C-5 estimate line in `SCRIPTS.md`: 180 C-1 exact cells cost 101 core-hours with at most 5.9 h per shard at 36 shards. B-02 has 126 records per bound, so 18 shards gives 7 records per shard and stays below the 24 h job deadline under that inherited upper bound. Claude should confirm with `--estimate-cost` before apply.

## B-02 Input

Command run:

```powershell
python analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py --input outputs/phase_c_campaign_221a3a7/history.jsonl --output outputs/phase_c_c8_oracle_b02_input/history.jsonl
```

Output:

```text
records=126
systems=21
sha256=029b7b71abeba35074d22b66d91f3115d93f0fc40e61caef36994792d6ba768a
```

Negative-count check:

```powershell
python analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py --expected-records 127 --output outputs/phase_c_c8_oracle_b02_input/should_not_pass.jsonl
```

Result: exits non-zero with `Expected 127 B-02 records, got 126`.

## YAML Validation

Command run:

```powershell
python - <<'PY'
from pathlib import Path
import yaml

for path in [
    Path("k8s/phase_c_robustness_stage2_system18_job.yaml"),
    Path("k8s/phase_c_c8_oracle_b02_job.yaml"),
]:
    docs = list(yaml.safe_load_all(path.read_text()))
    deadlines = [doc["spec"].get("activeDeadlineSeconds") for doc in docs]
    assert all(value is not None and value <= 86400 for value in deadlines), (path, deadlines)
    print(path, len(docs), deadlines)
PY
```

Result:

```text
k8s\phase_c_robustness_stage2_system18_job.yaml 3 [3600, 3600, 86400]
k8s\phase_c_c8_oracle_b02_job.yaml 3 [86400, 86400, 86400]
```

## Commands for Claude

B-02 cost estimate:

```powershell
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl `
  --campaign paper1_phaseC_v1 `
  --input outputs/phase_c_c8_oracle_b02_input/history.jsonl `
  --output-dir outputs/phase_c_c8_oracle_b02_bound10 `
  --clamp-val 10 `
  --estimate-cost
```

Smoke-record comparison after collecting the smoke output:

```bash
python - <<'PY'
import json
from pathlib import Path

candidate = json.loads(Path("outputs/phase_c_robustness_stage2_<SHA>/smoke/tasks/cell_000001.jsonl").read_text())
reference = json.loads(Path("outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl").read_text())
fields = ["loss", "support_terms", "total_loss_evals", "stage_caps", "observed_data_sha256"]
for field in fields:
    if candidate.get(field) != reference.get(field):
        raise SystemExit(f"{field} differs")
if candidate.get("model_terms") != reference.get("model_terms"):
    raise SystemExit("coefficients differ")
print("smoke record matches reference fields")
PY
```

## Notes

No `oc` command, cluster job, campaign, regression run, method-code edit, runner edit, fingerprint edit, Git operation, `docs/` edit, C-6 full-grid manifest, or Stage-3 manifest was performed.
