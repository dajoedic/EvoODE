import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd

from baselines import harness


DEFAULT_CONFIGS = [
    "baselines/configs/odeformer_beam10_noopt.json",
    "baselines/configs/odeformer_beam10_opt.json",
    "baselines/configs/odeformer_beam50_noopt.json",
    "baselines/configs/odeformer_beam50_opt.json",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def complete_record(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(record.get("status")) and bool(record.get("odeformer_config_id"))


def atomic_write_json(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def record_name(system_id: int, fit_ic: int, target_ic: int, config_id: str) -> str:
    return f"system_{system_id:03d}_fit{fit_ic}_gen{target_ic}_{config_id}.json"


def timeout_record(record: dict[str, Any], elapsed: float, budget: float) -> dict[str, Any]:
    updated = dict(record)
    updated.update(
        {
            "status": "timeout",
            "error_type": "Timeout",
            "error_message": f"cell exceeded timeout_seconds_per_cell={budget:g} after {elapsed:.6f} s",
            "reconstruction_status": "timeout",
            "generalization_status": "timeout",
            "elapsed_s_non_evidence": elapsed,
        }
    )
    return updated


def selected_config_paths(config: dict[str, Any]) -> list[Path]:
    values = config.get("odeformer_configs", DEFAULT_CONFIGS)
    return [harness.resolve_path(value) for value in values]


def selected_config_objects(config: dict[str, Any], config_ids: set[str] | None) -> list[dict[str, Any]]:
    configs = []
    for path in selected_config_paths(config):
        item = load_json(path)
        if config_ids is not None and str(item["config_id"]) not in config_ids:
            continue
        merged = dict(item)
        merged["environment_id"] = config.get("environment_id", item.get("environment_id", "candidate"))
        configs.append(merged)
    return configs


def parse_int_set(text: str) -> set[int] | None:
    if not text:
        return None
    return {int(part) for part in text.split(",") if part.strip()}


def parse_str_set(text: str) -> set[str] | None:
    if not text:
        return None
    return {part.strip() for part in text.split(",") if part.strip()}


def shard_cells(cells: list[tuple[dict[str, Any], int, int]], shard_index: int | None, shard_count: int | None) -> list[tuple[dict[str, Any], int, int]]:
    if shard_index is None and shard_count is None:
        return cells
    if shard_index is None or shard_count is None:
        raise ValueError("--shard-index and --shard-count must be provided together")
    if shard_count < 1 or shard_index < 0 or shard_index >= shard_count:
        raise ValueError("invalid shard arguments")
    return [cell for idx, cell in enumerate(cells) if idx % shard_count == shard_index]


def collect_records(records_dir: Path, output_dir: Path) -> Path:
    records = []
    for path in sorted(records_dir.glob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    jsonl_path = output_dir / "records.jsonl"
    jsonl_path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + ("\n" if records else ""), encoding="utf-8")
    pd.DataFrame(records).to_csv(output_dir / "records.csv", index=False)
    return jsonl_path


def run(
    config_path: Path,
    output_dir: str | None = None,
    environment_id: str | None = None,
    system_ids: set[int] | None = None,
    config_ids: set[str] | None = None,
    limit: int | None = None,
    shard_index: int | None = None,
    shard_count: int | None = None,
) -> Path:
    config = load_json(config_path)
    if environment_id is not None:
        config = dict(config)
        config["environment_id"] = environment_id
    benchmark = harness.load_benchmark(harness.resolve_path(config["benchmark_path"]))
    if system_ids is not None:
        config = dict(config)
        config["system_ids"] = sorted(system_ids)
    systems = harness.selected_systems(benchmark, config)
    export_dir = harness.resolve_path(config["trajectory_export_dir"])
    cells, trajectory_check = harness.load_exported_cells(export_dir, benchmark)
    out_dir = harness.resolve_path(output_dir or config["output_dir"])
    records_dir = out_dir / "records"
    out_dir.mkdir(parents=True, exist_ok=True)
    configs = selected_config_objects(config, config_ids)
    work_cells = shard_cells([(system, 1, 2) for system in systems] + [(system, 2, 1) for system in systems], shard_index, shard_count)
    work_items = [(system, fit_ic, target_ic, ode_config) for system, fit_ic, target_ic in work_cells for ode_config in configs]
    if limit is not None:
        work_items = work_items[: int(limit)]

    selected_ids = {int(system["id"]) for system in systems}
    manifest = pd.read_csv(export_dir / "trajectory_manifest.csv")
    selection_rows = harness.selected_manifest_rows(manifest, selected_ids)
    (out_dir / "selected_systems.json").write_text(
        json.dumps(
            {
                "selection": {
                    "system_ids": sorted(system_ids) if system_ids is not None else config.get("system_ids"),
                    "config_ids": sorted(config_ids) if config_ids is not None else [item["config_id"] for item in configs],
                    "limit": limit,
                    "shard_index": shard_index,
                    "shard_count": shard_count,
                },
                "system_count": len(systems),
                "trajectory_manifest_row_count": int(len(selection_rows)),
                "systems": [{"system_id": int(system["id"]), "dimension": int(system["dim"])} for system in systems],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    adapters: dict[str, harness.ODEFormerAdapter | Exception] = {}
    budget = float(config.get("timeout_seconds_per_cell", 900))
    for system, fit_ic, target_ic, ode_config in work_items:
        system_id = int(system["id"])
        config_id = str(ode_config["config_id"])
        path = records_dir / record_name(system_id, fit_ic, target_ic, config_id)
        if complete_record(path):
            continue
        if config_id not in adapters:
            try:
                adapters[config_id] = harness.build_odeformer_adapter(ode_config)
            except Exception as exc:
                adapters[config_id] = RuntimeError(f"ODEFormer is not importable in this environment: {exc}")
        adapter_or_exc = adapters[config_id]
        fit_cell = cells[(system_id, fit_ic)]
        target_cell = cells[(system_id, target_ic)]
        start = time.perf_counter()
        if isinstance(adapter_or_exc, Exception):
            base = harness.base_record("odeformer", ode_config, fit_cell, target_cell)
            base.update(harness.odeformer_schema_defaults(ode_config))
            record = harness.odeformer_failure(base, ode_config, adapter_or_exc)
        else:
            record = harness.run_odeformer_record_with_adapter(system, fit_cell, target_cell, ode_config, adapter_or_exc)
        elapsed = time.perf_counter() - start
        if elapsed > budget:
            record = timeout_record(record, elapsed, budget)
        atomic_write_json(path, record)

    trajectory_check.to_csv(out_dir / "trajectory_check.csv", index=False)
    return collect_records(records_dir, out_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the four-configuration ODEFormer Phase-C grid.")
    parser.add_argument("--config", default="baselines/configs/odeformer_grid.json")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--environment-id", choices=["reference", "candidate"], default="")
    parser.add_argument("--system-ids", default="")
    parser.add_argument("--config-ids", default="")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--shard-index", type=int, default=None)
    parser.add_argument("--shard-count", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = run(
        harness.resolve_path(args.config),
        args.output_dir or None,
        environment_id=args.environment_id or None,
        system_ids=parse_int_set(args.system_ids),
        config_ids=parse_str_set(args.config_ids),
        limit=args.limit,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
