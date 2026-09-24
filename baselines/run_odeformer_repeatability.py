import argparse
import csv
import importlib.metadata
import json
import math
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baselines import harness
from baselines import run_odeformer_grid


BASE_DIR = harness.REPO_ROOT / "analysis" / "data" / "paper1_phaseC_v1" / "odeformer_baseline"
OUTPUT_ROOT = harness.REPO_ROOT / "outputs" / "odeformer_repeatability"
R2_FIELDS = ["reconstruction_r2_variance_weighted", "generalization_r2_variance_weighted"]
MODEL_FIELD = "odeformer_model_raw"
CELL_KEYS = ["environment_id", "system_id", "fit_initial_condition_set", "generalization_initial_condition_set", "odeformer_config_id"]
ENVIRONMENT_EXPECTED_CHANGED = {"reference": 18, "candidate": 12}
ENVIRONMENT_CONTROL_COUNT = {"reference": 4, "candidate": 4}
RUN_DIR_RE = re.compile(r"^(reference|candidate)_(faithful|lifted)_([1-9][0-9]*)$")


def records_path(name: str) -> Path:
    return BASE_DIR / name / "records"


def read_record_dir(name: str) -> pd.DataFrame:
    rows = []
    for path in sorted(records_path(name).glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["record_path"] = str(path)
        rows.append(record)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError(f"no records found in {records_path(name)}")
    if "odeformer_environment_id" in frame.columns:
        frame["environment_id"] = frame["odeformer_environment_id"].astype(str)
    return frame


def cell_id(record: pd.Series | dict[str, Any]) -> tuple[Any, ...]:
    return tuple(record[key] for key in CELL_KEYS)


def differs(left: pd.Series, right: pd.Series) -> bool:
    for field in [*R2_FIELDS, MODEL_FIELD]:
        if str(left.get(field)) != str(right.get(field)):
            return True
    return False


def environment_from_record(record: dict[str, Any], fallback: str) -> str:
    return str(record.get("odeformer_environment_id") or record.get("environment_id") or fallback)


def parse_environment(record: dict[str, Any]) -> dict[str, str]:
    value = record.get("environment")
    if not value:
        return {}
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): str(item) for key, item in parsed.items()}


def expected_environment_signature(environment_id: str) -> dict[str, str]:
    records = sorted(records_path(environment_id).glob("*.json"))
    if not records:
        raise ValueError(f"no baseline records found for environment {environment_id!r}")
    for path in records:
        record = json.loads(path.read_text(encoding="utf-8"))
        env = parse_environment(record)
        if "torch" in env:
            return {"torch": env["torch"]}
    raise ValueError(f"no torch version found in baseline records for environment {environment_id!r}")


def installed_environment_signature() -> dict[str, str]:
    try:
        torch_version = importlib.metadata.version("torch")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError("torch is not installed; cannot verify ODEFormer environment") from exc
    return {"torch": torch_version}


def assert_environment_matches(environment_id: str) -> None:
    expected = expected_environment_signature(environment_id)
    actual = installed_environment_signature()
    mismatches = {key: (expected[key], actual.get(key)) for key in expected if actual.get(key) != expected[key]}
    if mismatches:
        details = ", ".join(f"{key}: expected {left}, installed {right}" for key, (left, right) in sorted(mismatches.items()))
        raise RuntimeError(f"installed environment does not match {environment_id}: {details}")


def derive_cells(
    expected_changed: int = 30,
    expected_changed_by_environment: dict[str, int] | None = None,
    control_count_by_environment: dict[str, int] | None = None,
    seed: int = 20260924,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs = [
        ("reference", "reference_wp_n23"),
        ("candidate", "candidate_wp_n23"),
    ]
    changed: dict[tuple[Any, ...], dict[str, Any]] = {}
    stable: dict[tuple[Any, ...], dict[str, Any]] = {}
    for baseline_name, repeat_name in pairs:
        left = read_record_dir(baseline_name)
        right = read_record_dir(repeat_name)
        merged = left.merge(
            right,
            on=["system_id", "fit_initial_condition_set", "generalization_initial_condition_set", "odeformer_config_id"],
            suffixes=("_baseline", "_repeat"),
        )
        for _, row in merged.iterrows():
            environment_id = str(row.get("environment_id_baseline", baseline_name))
            item = {
                "environment_id": environment_id,
                "system_id": int(row["system_id"]),
                "fit_initial_condition_set": int(row["fit_initial_condition_set"]),
                "generalization_initial_condition_set": int(row["generalization_initial_condition_set"]),
                "odeformer_config_id": str(row["odeformer_config_id"]),
                "dimension": int(row["dimension_baseline"]),
            }
            key = cell_id(item)
            left_record = pd.Series({field: row.get(f"{field}_baseline") for field in [*R2_FIELDS, MODEL_FIELD]})
            right_record = pd.Series({field: row.get(f"{field}_repeat") for field in [*R2_FIELDS, MODEL_FIELD]})
            if differs(left_record, right_record):
                changed[key] = {**item, "selection_reason": "changed"}
            else:
                stable[key] = {**item, "selection_reason": "control"}
    if len(changed) != expected_changed:
        raise ValueError(f"expected {expected_changed} changed cells, found {len(changed)}; difference={len(changed) - expected_changed}")
    expected_changed_by_environment = expected_changed_by_environment or ENVIRONMENT_EXPECTED_CHANGED
    observed_changed = {environment_id: 0 for environment_id in expected_changed_by_environment}
    for item in changed.values():
        observed_changed[item["environment_id"]] = observed_changed.get(item["environment_id"], 0) + 1
    if observed_changed != expected_changed_by_environment:
        raise ValueError(f"expected changed cells by environment {expected_changed_by_environment}, found {observed_changed}")
    candidates = [item for key, item in stable.items() if key not in changed]
    rng = random.Random(seed)
    by_bucket: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for item in candidates:
        bucket = (item["environment_id"], item["dimension"], item["odeformer_config_id"])
        by_bucket.setdefault(bucket, []).append(item)
    selected_by_environment: dict[str, list[dict[str, Any]]] = {key: [] for key in (control_count_by_environment or ENVIRONMENT_CONTROL_COUNT)}
    for bucket in sorted(by_bucket):
        environment_id = str(bucket[0])
        if environment_id not in selected_by_environment:
            continue
        options = sorted(by_bucket[bucket], key=lambda item: cell_id(item))
        rng.shuffle(options)
        if options and len(selected_by_environment[environment_id]) < (control_count_by_environment or ENVIRONMENT_CONTROL_COUNT)[environment_id]:
            selected_by_environment[environment_id].append(options[0])
    already_selected = {cell_id(item) for items in selected_by_environment.values() for item in items}
    for environment_id, needed in (control_count_by_environment or ENVIRONMENT_CONTROL_COUNT).items():
        remaining = [item for item in candidates if item["environment_id"] == environment_id and cell_id(item) not in already_selected]
        rng.shuffle(remaining)
        selected_by_environment[environment_id].extend(
            sorted(remaining, key=lambda item: cell_id(item))[: max(0, needed - len(selected_by_environment[environment_id]))]
        )
        if len(selected_by_environment[environment_id]) != needed:
            raise ValueError(f"expected {needed} control cells for {environment_id}, found {len(selected_by_environment[environment_id])}")
    selected = sorted([item for items in selected_by_environment.values() for item in items], key=lambda item: cell_id(item))
    return sorted(changed.values(), key=lambda item: cell_id(item)), selected


def write_cell_list(path: Path, cells: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cells, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def filter_environment(cells: list[dict[str, Any]], environment_id: str, limit: int | None = None) -> list[dict[str, Any]]:
    filtered = [cell for cell in cells if str(cell["environment_id"]) == environment_id]
    if limit is not None:
        filtered = filtered[: int(limit)]
    return filtered


def mode_config(config: dict[str, Any], mode: str) -> dict[str, Any]:
    updated = dict(config)
    if mode == "faithful":
        updated["integration_timeout_seconds"] = None
    elif mode == "lifted":
        updated["integration_timeout_seconds"] = 10.0
    else:
        raise ValueError(f"unknown mode: {mode}")
    return updated


def repeatability_record_name(cell: dict[str, Any], repetition: int, mode: str) -> str:
    return (
        f"{cell['environment_id']}_{mode}_system_{int(cell['system_id']):03d}_"
        f"fit{cell['fit_initial_condition_set']}_gen{cell['generalization_initial_condition_set']}_"
        f"{cell['odeformer_config_id']}_rep{int(repetition):03d}.json"
    )


def expected_record_count(cells: list[dict[str, Any]], repetitions: int) -> int:
    return len(cells) * int(repetitions)


def grid_config_differences() -> list[dict[str, Any]]:
    grid_config = run_odeformer_grid.load_json(harness.resolve_path("baselines/configs/odeformer_grid.json"))
    reference = {str(item["config_id"]): item for item in run_odeformer_grid.selected_config_objects({**grid_config, "environment_id": "reference"}, None)}
    candidate = {str(item["config_id"]): item for item in run_odeformer_grid.selected_config_objects({**grid_config, "environment_id": "candidate"}, None)}
    rows: list[dict[str, Any]] = []
    for config_id in sorted(set(reference) | set(candidate)):
        left = reference.get(config_id, {})
        right = candidate.get(config_id, {})
        for key in sorted(set(left) | set(right)):
            if left.get(key) != right.get(key):
                rows.append({"config_id": config_id, "field": key, "reference": left.get(key), "candidate": right.get(key)})
    return rows


def run_one_cell(
    cell: dict[str, Any],
    repetition: int,
    mode: str,
    output_dir: Path,
    benchmark: list[dict[str, Any]],
    cells_by_key: dict[tuple[int, int], harness.TrajectoryCell],
    config_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    system_id = int(cell["system_id"])
    system = next(item for item in benchmark if int(item["id"]) == system_id)
    fit_cell = cells_by_key[(system_id, int(cell["fit_initial_condition_set"]))]
    target_cell = cells_by_key[(system_id, int(cell["generalization_initial_condition_set"]))]
    config = mode_config(config_by_id[str(cell["odeformer_config_id"])], mode)
    config["environment_id"] = str(cell["environment_id"])
    record = run_odeformer_grid.run_cell_with_hard_timeout(system, fit_cell, target_cell, config, 900.0)
    record.update(
        {
            "environment_id": str(cell["environment_id"]),
            "repeatability_mode": mode,
            "repeatability_repetition": int(repetition),
            "repeatability_selection_reason": str(cell["selection_reason"]),
        }
    )
    path = output_dir / "records" / repeatability_record_name(cell, repetition, mode)
    run_odeformer_grid.atomic_write_json(path, record)
    return record


def not_run_record(cell: dict[str, Any], repetition: int, mode: str) -> dict[str, Any]:
    return {
        **cell,
        "status": "not_run_global_time_limit",
        "repeatability_mode": mode,
        "repeatability_repetition": int(repetition),
        "repeatability_selection_reason": str(cell["selection_reason"]),
    }


def read_record_files(output_dir: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted((output_dir / "records").glob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def summarize_records(records: list[dict[str, Any]], output_dir: Path) -> Path:
    rows = []
    frame = pd.DataFrame(records)
    if not frame.empty:
        if "environment_id" not in frame.columns and "odeformer_environment_id" in frame.columns:
            frame["environment_id"] = frame["odeformer_environment_id"]
        if "odeformer_config_id" not in frame.columns:
            frame["odeformer_config_id"] = ""
        for key, group in frame.groupby(CELL_KEYS + ["repeatability_mode", "repeatability_selection_reason"], dropna=False):
            values = dict(zip([*CELL_KEYS, "mode", "selection_reason"], key))
            raw_models = group[MODEL_FIELD].astype(str).tolist() if MODEL_FIELD in group.columns else []
            r2_columns = [field for field in R2_FIELDS if field in group.columns]
            timeout_values = pd.to_numeric(group.get("odeformer_integration_timeout_count_total", pd.Series([0] * len(group))), errors="coerce").fillna(0)
            rows.append(
                {
                    **values,
                    "repetition_count": int(len(group)),
                    "all_bitwise_identical": bool(len(set(raw_models)) <= 1 and all(group[field].astype(str).nunique(dropna=False) <= 1 for field in r2_columns)),
                    "timeout_count_min": int(timeout_values.min()) if len(timeout_values) else 0,
                    "timeout_count_max": int(timeout_values.max()) if len(timeout_values) else 0,
                    "handler_timeout_count_min": int(timeout_values.min()) if len(timeout_values) else 0,
                    "handler_timeout_count_max": int(timeout_values.max()) if len(timeout_values) else 0,
                    "r2_gt_0_9_flip": bool(any(pd.to_numeric(group[field], errors="coerce").gt(harness.R2_THRESHOLD).nunique(dropna=False) > 1 for field in r2_columns)),
                }
            )
    path = output_dir / "cell_summary.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def write_records_tables(records: list[dict[str, Any]], output_dir: Path) -> tuple[Path, Path, Path]:
    jsonl_path = output_dir / "records.jsonl"
    jsonl_path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + ("\n" if records else ""), encoding="utf-8")
    csv_path = output_dir / "records.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    summary_path = summarize_records(records, output_dir)
    return jsonl_path, csv_path, summary_path


def collect(output_dir: Path, repetitions: int | None = None) -> Path:
    output_dir = harness.resolve_path(output_dir)
    records = read_record_files(output_dir)
    write_records_tables(records, output_dir)
    selected_path = output_dir / "selected_cells.json"
    selected = json.loads(selected_path.read_text(encoding="utf-8")) if selected_path.is_file() else []
    if repetitions is None:
        repetitions = max([int(record.get("repeatability_repetition", 0)) for record in records] or [0])
    expected = expected_record_count(selected, int(repetitions)) if selected else len(records)
    not_run = sum(1 for record in records if record.get("status") == "not_run_global_time_limit")
    summary = {
        "expected_cell_repetitions": int(expected),
        "record_count": int(len(records)),
        "not_run_global_time_limit_count": int(not_run),
        "missing_count": int(max(0, expected - len(records))),
    }
    (output_dir / "collection_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "collect: expected={expected_cell_repetitions} present={record_count} not_run_global_time_limit={not_run_global_time_limit_count}".format(
            **summary
        )
    )
    return output_dir / "records.jsonl"


def compare_modes(output_root: Path) -> Path:
    rows = []
    for path in sorted(output_root.glob("*/cell_summary.csv")):
        match = RUN_DIR_RE.match(path.parent.name)
        if not match:
            continue
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        environment_id, mode, shard_text = match.groups()
        rows.append(
            {
                "run": path.parent.name,
                "environment_id": environment_id,
                "mode": mode,
                "shards": shard_text,
                "cell_count": int(len(frame)),
                "all_cells_bitwise_identical_count": int(frame["all_bitwise_identical"].sum()),
                "timeout_count_min": int(frame["timeout_count_min"].min()),
                "timeout_count_max": int(frame["timeout_count_max"].max()),
                "handler_timeout_count_min": int(frame.get("handler_timeout_count_min", frame["timeout_count_min"]).min()),
                "handler_timeout_count_max": int(frame.get("handler_timeout_count_max", frame["timeout_count_max"]).max()),
                "r2_gt_0_9_flip_count": int(frame["r2_gt_0_9_flip"].sum()),
            }
        )
    out = output_root / "mode_comparison.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def run(args: argparse.Namespace) -> Path:
    if not args.environment_id:
        raise ValueError("--environment-id is required when computing cells")
    changed, controls = derive_cells(expected_changed=args.expected_changed, seed=args.control_seed)
    all_cells = filter_environment(changed + controls, args.environment_id, args.limit_cells)
    output_dir = harness.resolve_path(args.output_dir or (OUTPUT_ROOT / f"{args.environment_id}_{args.mode}_{args.shards}"))
    write_cell_list(output_dir / "changed_cells.json", changed)
    write_cell_list(output_dir / "control_cells.json", controls)
    write_cell_list(output_dir / "selected_cells.json", all_cells)
    (output_dir / "grid_config_differences.json").write_text(json.dumps(grid_config_differences(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.derive_only:
        return output_dir / "selected_cells.json"
    assert_environment_matches(args.environment_id)

    benchmark = harness.load_benchmark(harness.resolve_path("benchmarks/data/strogatz_extended.json"))
    export_dir = harness.resolve_path("outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export")
    cells_by_key, _ = harness.load_exported_cells(export_dir, benchmark)
    grid_config = run_odeformer_grid.load_json(harness.resolve_path("baselines/configs/odeformer_grid.json"))
    config_by_id = {str(config["config_id"]): config for config in run_odeformer_grid.selected_config_objects(grid_config, None)}
    deadline = time.monotonic() + float(args.max_hours) * 3600.0
    for repetition in range(1, int(args.repetitions) + 1):
        for index, cell in enumerate(all_cells):
            if args.shard_index is not None and index % int(args.shards) != int(args.shard_index):
                continue
            record_path = output_dir / "records" / repeatability_record_name(cell, repetition, args.mode)
            if record_path.is_file():
                continue
            if time.monotonic() >= deadline:
                run_odeformer_grid.atomic_write_json(record_path, not_run_record(cell, repetition, args.mode))
                continue
            run_one_cell(cell, repetition, args.mode, output_dir, benchmark, cells_by_key, config_by_id)
    return output_dir / "records"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or summarize ODEFormer repeatability cells.")
    parser.add_argument("--mode", choices=["faithful", "lifted"], default="faithful")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=None)
    parser.add_argument("--max-hours", type=float, default=24.0)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--environment-id", choices=["reference", "candidate"], default="")
    parser.add_argument("--expected-changed", type=int, default=30)
    parser.add_argument("--control-seed", type=int, default=20260924)
    parser.add_argument("--limit-cells", type=int, default=None)
    parser.add_argument("--derive-only", action="store_true")
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--compare-modes", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.compare_modes:
        print(compare_modes(harness.resolve_path(args.output_dir or OUTPUT_ROOT)))
        return 0
    if args.collect:
        print(collect(harness.resolve_path(args.output_dir or (OUTPUT_ROOT / f"{args.environment_id}_{args.mode}_{args.shards}")), args.repetitions))
        return 0
    print(run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
