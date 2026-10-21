"""Merge atomic C-6 symbolic-baseline units; never read EvoGrow outputs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for path in (ROOT, ROOT / "analysis"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from baselines.c6_shards import CONFIGS, N_SHARDS, expected_units, context_id, smoke_index, assign_shards
from baselines.noise_execution import cell_key, unit_key, load_unit, encoded, atomic_write
from scripts.aggregate.run_phasec_noise_sindy_baselines import read_export_index, data_sha


def aggregate(input_dir, export_index, output_dir, method, git_commit, image_id,
              n_shards=None, config_path=None, smoke=False, allow_incomplete=False):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite output directory: {output_dir}")
    frame = read_export_index(Path(export_index))
    if smoke:
        frame = smoke_index(frame, method)
    n_shards = n_shards or (len(frame) if smoke else N_SHARDS[method])
    config_path = config_path or CONFIGS[method]
    expected = expected_units(frame, method, config_path, smoke)
    context = context_id(frame, method, n_shards, git_commit, image_id, config_path, smoke)
    assignment = assign_shards(frame, n_shards)
    owners = {cell_key(row): int(row.shard_index) for _, row in assignment.iterrows()}
    records, checks = {}, {}
    for directory in sorted(input_dir.glob("shard_*")):
        plan_path = directory / "plan.json"
        if not plan_path.is_file():
            if list(directory.glob("units/*.json")):
                raise ValueError(f"Missing plan: {directory}")
            continue
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if (plan["context"] != context or plan["method"] != method or plan["n_shards"] != n_shards
                or plan["smoke"] != smoke or plan["git_commit"] != git_commit or plan["image_id"] != image_id):
            raise ValueError(f"Shard plan/provenance mismatch: {directory}")
        for path in sorted(directory.glob("units/*.json")):
            body = load_unit(path)
            record, check = body["record"], body["export_check"]
            key = unit_key(record)
            if body["context"] != context or key not in expected:
                raise ValueError(f"Unexpected unit/context: {path}")
            if owners[cell_key(record)] != int(plan["shard_index"]):
                raise ValueError(f"Wrong shard assignment: {path}")
            row = expected[key]
            if (record["git_hash"] != git_commit or record["code_origin_git_hash"] != git_commit
                    or record["image_id"] != image_id or record["observed_data_sha256"] != data_sha(row)
                    or check["time_sha256"] != str(row.time_sha256) or check["state_sha256"] != str(row.state_sha256)):
                raise ValueError(f"Record provenance/hash mismatch: {path}")
            if not check["hash_verified"] and (record["status"] != "error" or not record.get("export_validation_error")):
                raise ValueError(f"Hash error lacks failure record: {path}")
            if method == "pysr" and record["status"] == "success" and record.get("pysr_api") != "legacy_0x":
                raise ValueError(f"Wrong PySR API: {path}")
            if key in records and encoded(records[key]) != encoded(record):
                raise ValueError(f"Non-identical duplicate unit: {key}")
            records[key] = record
            ckey = cell_key(check)
            if ckey in checks and encoded(checks[ckey]) != encoded(check):
                raise ValueError(f"Non-identical export checks: {ckey}")
            checks[ckey] = check
    missing = set(expected) - records.keys()
    if missing and not allow_incomplete:
        raise ValueError(f"Missing {len(missing)} of {len(expected)} units")
    if not records:
        raise ValueError("No complete units found")
    # Reuse the local runner's exact summary/schema; do not join comparison sources.
    if method == "odeformer":
        from baselines.run_odeformer_noise import build_summary
    else:
        from baselines.run_pysr_noise import build_summary
    ordered = [records[key] for key in expected if key in records]
    details = pd.DataFrame(ordered)
    summary = build_summary(details)
    output_dir.mkdir(parents=True, exist_ok=False)
    atomic_write(output_dir / "records.jsonl", b"".join(encoded(record) + b"\n" for record in ordered))
    atomic_write(output_dir / "details.csv", details.to_csv(index=False).encode())
    atomic_write(output_dir / "summary.csv", summary.to_csv(index=False).encode())
    atomic_write(output_dir / "export_checks.csv", pd.DataFrame(list(checks.values())).to_csv(index=False).encode())
    result = dict(expected=len(expected), present=len(records), missing=len(missing), allow_incomplete=allow_incomplete)
    atomic_write(output_dir / "merge_audit.json", encoded(result) + b"\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True, choices=CONFIGS)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--export-index", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--n-shards", type=int)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    print(json.dumps(aggregate(args.input_dir, args.export_index, args.output_dir, args.method, args.git_sha,
                              args.image_id, args.n_shards, args.config, args.smoke, args.allow_incomplete), indent=2))


if __name__ == "__main__":
    main()
