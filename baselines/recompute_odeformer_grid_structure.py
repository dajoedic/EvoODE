from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baselines.run_odeformer_noise import (
    phase_c_support_terms,
    read_jsonl,
    recompute_record_structure_fields,
    resolve_repo_path,
)


DEFAULT_INPUTS = [
    Path("analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.jsonl"),
    Path("analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_orion_8e0e699/records.jsonl"),
]
DEFAULT_SUPPORT = Path("studies/regression/phase_c_support.json")
R2_FIELDS = [
    "reconstruction_r2_arithmetic_mean",
    "reconstruction_r2_variance_weighted",
    "generalization_r2_arithmetic_mean",
    "generalization_r2_variance_weighted",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recompute ODEFormer grid structure fields without running ODEFormer.")
    parser.add_argument(
        "--records",
        action="append",
        default=[],
        help="Input records.jsonl or records.csv. May be passed multiple times; defaults to the Orion reference and candidate grids.",
    )
    parser.add_argument("--support", default=str(DEFAULT_SUPPORT), help="Phase-C support JSON.")
    parser.add_argument("--output-stem", default="records_structure_recomputed", help="Output basename without suffix.")
    parser.add_argument("--manifest-name", default="structure_recompute_manifest.json", help="Manifest filename in each input directory.")
    return parser.parse_args()


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path).to_dict("records")
    raise ValueError(f"unsupported records input suffix: {path}")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def code_hash() -> str:
    digest = hashlib.sha256()
    for relative in [
        "baselines/recompute_odeformer_grid_structure.py",
        "baselines/run_odeformer_noise.py",
        "baselines/harness.py",
    ]:
        digest.update(relative.encode("utf-8"))
        digest.update((REPO_ROOT / relative).read_bytes())
    return digest.hexdigest()


def r2_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    return {field: record.get(field) for field in R2_FIELDS}


def recompute_records(records: list[dict[str, Any]], support_terms_by_id: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    updated = []
    for record in records:
        item = dict(record)
        before_r2 = r2_snapshot(item)
        item.update(recompute_record_structure_fields(item, support_terms_by_id))
        if r2_snapshot(item) != before_r2:
            raise AssertionError(f"R2 fields changed for system_id={item.get('system_id')}")
        updated.append(item)
    return updated


def write_outputs(
    input_path: Path,
    records: list[dict[str, Any]],
    support_path: Path,
    output_stem: str,
    manifest_name: str,
) -> dict[str, Path]:
    output_jsonl = input_path.parent / f"{output_stem}.jsonl"
    output_csv = input_path.parent / f"{output_stem}.csv"
    manifest_path = input_path.parent / manifest_name

    output_jsonl.write_text(
        "\n".join(stable_json(record) for record in records) + ("\n" if records else ""),
        encoding="utf-8",
    )
    pd.DataFrame(records).to_csv(output_csv, index=False)

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "reason": "WP-N40 recomputed ODEFormer structure fields from canonical expressions; original grid files were not overwritten.",
        "input_records": str(input_path),
        "input_records_sha256": sha256_path(input_path),
        "support_path": str(support_path),
        "support_sha256": sha256_path(support_path),
        "code_hash_sha256": code_hash(),
        "record_count": len(records),
        "output_jsonl": str(output_jsonl),
        "output_csv": str(output_csv),
        "structure_hit_raw_count": int(sum(bool(record.get("structure_hit_raw")) for record in records)),
        "structure_hit_pruned_count": int(sum(bool(record.get("structure_hit_pruned")) for record in records)),
        "outside_basis_record_count": int(
            sum(int(record.get("odeformer_outside_basis_term_count", 0) or 0) > 0 for record in records)
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"jsonl": output_jsonl, "csv": output_csv, "manifest": manifest_path}


def recompute_file(input_path: Path, support_path: Path, output_stem: str, manifest_name: str) -> dict[str, Path]:
    input_path = resolve_repo_path(input_path)
    support_path = resolve_repo_path(support_path)
    support_terms_by_id = phase_c_support_terms(support_path)
    records = recompute_records(load_records(input_path), support_terms_by_id)
    return write_outputs(input_path, records, support_path, output_stem, manifest_name)


def main() -> None:
    args = parse_args()
    inputs = [Path(value) for value in args.records] if args.records else DEFAULT_INPUTS
    for input_path in inputs:
        paths = recompute_file(input_path, Path(args.support), args.output_stem, args.manifest_name)
        print(f"{input_path}: wrote {paths['jsonl']} and {paths['csv']}")


if __name__ == "__main__":
    main()
