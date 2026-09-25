import argparse
import json
import multiprocessing as mp
import os
import queue
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from baselines import harness


DEFAULT_CONFIGS = [
    "baselines/configs/odeformer_beam10_noopt.json",
    "baselines/configs/odeformer_beam10_opt.json",
    "baselines/configs/odeformer_beam50_noopt.json",
    "baselines/configs/odeformer_beam50_opt.json",
]

CELL_KEYS = ["system_id", "fit_initial_condition_set", "generalization_initial_condition_set", "odeformer_config_id"]
R2_FIELDS = ["reconstruction_r2_variance_weighted", "generalization_r2_variance_weighted"]
MODEL_FIELD = "odeformer_model_raw"
REPETITION_DIR_RE = re.compile(r"^rep_([0-9]{3})$")
QUEUE_POLL_SECONDS = 0.05
PROCESS_JOIN_GRACE_SECONDS = 5.0


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def complete_record(path: Path, rerun_timeouts: bool = False) -> bool:
    if not path.is_file():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if rerun_timeouts and record.get("status") == "timeout":
        return False
    return bool(record.get("status")) and bool(record.get("odeformer_config_id"))


def atomic_write_json(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def record_name(system_id: int, fit_ic: int, target_ic: int, config_id: str) -> str:
    return f"system_{system_id:03d}_fit{fit_ic}_gen{target_ic}_{config_id}.json"


def timeout_record(record: dict[str, Any], elapsed: float, budget: float, timeout_enforced: bool) -> dict[str, Any]:
    updated = dict(record)
    updated.update(
        {
            "status": "timeout",
            "error_type": "Timeout",
            "error_message": f"cell exceeded timeout_seconds_per_cell={budget:g} after {elapsed:.6f} s",
            "reconstruction_status": "timeout",
            "generalization_status": "timeout",
            "elapsed_s_non_evidence": elapsed,
            "timeout_enforced": bool(timeout_enforced),
        }
    )
    return updated


def timeout_enforcement_available() -> bool:
    return os.name == "posix"


def timeout_base_record(
    system: dict[str, Any],
    fit_cell: harness.TrajectoryCell,
    target_cell: harness.TrajectoryCell,
    ode_config: dict[str, Any],
    elapsed: float,
    budget: float,
    timeout_enforced: bool,
) -> dict[str, Any]:
    base = harness.base_record("odeformer", ode_config, fit_cell, target_cell)
    base.update(harness.odeformer_schema_defaults(ode_config))
    failed = harness.odeformer_failure(base, ode_config, TimeoutError(f"cell exceeded timeout_seconds_per_cell={budget:g}"))
    failed["system_id"] = int(system["id"])
    return timeout_record(failed, elapsed, budget, timeout_enforced)


def run_odeformer_cell_direct(
    system: dict[str, Any],
    fit_cell: harness.TrajectoryCell,
    target_cell: harness.TrajectoryCell,
    ode_config: dict[str, Any],
    adapter_or_exc: harness.ODEFormerAdapter | Exception,
    timeout_enforced: bool,
) -> dict[str, Any]:
    if isinstance(adapter_or_exc, Exception):
        base = harness.base_record("odeformer", ode_config, fit_cell, target_cell)
        base.update(harness.odeformer_schema_defaults(ode_config))
        record = harness.odeformer_failure(base, ode_config, adapter_or_exc)
    else:
        record = harness.run_odeformer_record_with_adapter(system, fit_cell, target_cell, ode_config, adapter_or_exc)
    record["timeout_enforced"] = bool(timeout_enforced)
    return record


def _run_cell_child(
    result_queue: Any,
    system: dict[str, Any],
    fit_cell: harness.TrajectoryCell,
    target_cell: harness.TrajectoryCell,
    ode_config: dict[str, Any],
) -> None:
    try:
        try:
            adapter_or_exc: harness.ODEFormerAdapter | Exception = harness.build_odeformer_adapter(ode_config)
        except Exception as exc:
            adapter_or_exc = RuntimeError(f"ODEFormer is not importable in this environment: {exc}")
        result_queue.put(("record", run_odeformer_cell_direct(system, fit_cell, target_cell, ode_config, adapter_or_exc, True)))
    except BaseException as exc:
        result_queue.put(("exception", (type(exc).__name__, str(exc))))


def run_cell_with_hard_timeout(
    system: dict[str, Any],
    fit_cell: harness.TrajectoryCell,
    target_cell: harness.TrajectoryCell,
    ode_config: dict[str, Any],
    budget: float | None,
    runner: Callable[[Any, dict[str, Any], harness.TrajectoryCell, harness.TrajectoryCell, dict[str, Any]], None] = _run_cell_child,
) -> dict[str, Any]:
    ctx = mp.get_context("fork")
    result_queue = ctx.Queue(maxsize=1)
    start = time.perf_counter()
    process = ctx.Process(target=runner, args=(result_queue, system, fit_cell, target_cell, ode_config))
    process.start()
    deadline = None if budget is None else start + max(0.0, float(budget))
    result: tuple[str, Any] | None = None
    timed_out = False
    while result is None:
        now = time.perf_counter()
        if deadline is None:
            wait_seconds = QUEUE_POLL_SECONDS
        else:
            remaining = deadline - now
            if remaining <= 0.0:
                wait_seconds = 0.0
            else:
                wait_seconds = min(QUEUE_POLL_SECONDS, remaining)
        try:
            result = result_queue.get(timeout=wait_seconds)
            break
        except queue.Empty:
            if deadline is not None and time.perf_counter() >= deadline and process.is_alive():
                timed_out = True
                break
            if not process.is_alive():
                break
    elapsed = time.perf_counter() - start
    if result is None:
        if timed_out or process.is_alive():
            process.terminate()
            process.join(PROCESS_JOIN_GRACE_SECONDS)
            if process.is_alive():
                process.kill()
                process.join(PROCESS_JOIN_GRACE_SECONDS)
            return timeout_base_record(system, fit_cell, target_cell, ode_config, elapsed, budget, True)
        process.join(PROCESS_JOIN_GRACE_SECONDS)
        try:
            result = result_queue.get_nowait()
        except queue.Empty:
            base = harness.base_record("odeformer", ode_config, fit_cell, target_cell)
            base.update(harness.odeformer_schema_defaults(ode_config))
            record = harness.odeformer_failure(base, ode_config, RuntimeError(f"cell worker exited with code {process.exitcode} before returning a record"))
            record["timeout_enforced"] = True
            return record
    else:
        process.join(PROCESS_JOIN_GRACE_SECONDS)
        if process.is_alive():
            process.terminate()
            process.join(PROCESS_JOIN_GRACE_SECONDS)
            if process.is_alive():
                process.kill()
                process.join(PROCESS_JOIN_GRACE_SECONDS)
    kind, payload = result
    if kind == "record":
        payload["timeout_enforced"] = True
        return payload
    error_type, error_message = payload
    if error_type == "ODEFormerInfrastructureError":
        raise harness.ODEFormerInfrastructureError(error_message)
    base = harness.base_record("odeformer", ode_config, fit_cell, target_cell)
    base.update(harness.odeformer_schema_defaults(ode_config))
    record = harness.odeformer_failure(base, ode_config, RuntimeError(f"{error_type}: {error_message}"))
    record["timeout_enforced"] = True
    return record


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


def preflight_odeformer_constant_optimization(configs: list[dict[str, Any]]) -> None:
    if any(bool(config.get("constant_optimization_enabled", False)) for config in configs):
        try:
            harness.preflight_odeformer_constant_optimization()
        except harness.ODEFormerInfrastructureError:
            raise
        except ImportError as exc:
            raise harness.ODEFormerInfrastructureError(
                f"ODEFormer constant optimization preflight failed: {type(exc).__name__}: {exc}"
            ) from exc


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


def output_root(base_output_dir: Path, repetition: int | None) -> Path:
    if repetition is None:
        return base_output_dir
    if repetition < 1:
        raise ValueError("--repetition must be 1-based")
    return base_output_dir / f"rep_{int(repetition):03d}"


def configure_torch_threads_from_env(env_var: str = "ODEFORMER_TORCH_THREADS") -> tuple[int | None, str]:
    requested = os.environ.get(env_var)
    if requested is None or requested == "":
        return None, "not_requested"
    try:
        requested_threads = int(requested)
    except ValueError as exc:
        raise ValueError(f"{env_var} must be an integer") from exc
    if requested_threads < 1:
        raise ValueError(f"{env_var} must be >= 1")
    try:
        import torch
    except Exception as exc:
        return None, f"torch_unavailable:{type(exc).__name__}"
    torch.set_num_threads(requested_threads)
    return int(torch.get_num_threads()), "set_from_env"


def observed_torch_threads() -> int | None:
    try:
        import torch
    except Exception:
        return None
    try:
        return int(torch.get_num_threads())
    except Exception:
        return None


def assert_faithful_mode(config: dict[str, Any]) -> None:
    if config.get("timeout_seconds_per_cell") is not None:
        raise ValueError("ODEFormer reference grid must run in faithful mode: timeout_seconds_per_cell must be null")
    for path in selected_config_paths(config):
        ode_config = load_json(path)
        if ode_config.get("integration_timeout_seconds") is not None:
            raise ValueError(f"ODEFormer reference grid must run in faithful mode: {path} sets integration_timeout_seconds")


def collect_records(records_dir: Path, output_dir: Path) -> Path:
    records = []
    for path in sorted(records_dir.glob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    jsonl_path = output_dir / "records.jsonl"
    jsonl_path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + ("\n" if records else ""), encoding="utf-8")
    pd.DataFrame(records).to_csv(output_dir / "records.csv", index=False)
    return jsonl_path


def discover_repetition_dirs(output_dir: Path) -> list[tuple[int, Path]]:
    reps: list[tuple[int, Path]] = []
    for path in sorted(output_dir.iterdir() if output_dir.is_dir() else []):
        match = REPETITION_DIR_RE.match(path.name)
        if match and (path / "records").is_dir():
            reps.append((int(match.group(1)), path))
    return reps


def read_record_dir(records_dir: Path) -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(records_dir.glob("*.json"))]


def summarize_repetition_groups(records: list[dict[str, Any]], group_keys: list[str]) -> pd.DataFrame:
    rows = []
    frame = pd.DataFrame(records)
    if not frame.empty:
        for key, group in frame.groupby(group_keys, dropna=False):
            key_tuple = key if isinstance(key, tuple) else (key,)
            values = dict(zip(group_keys, key_tuple))
            raw_models = group[MODEL_FIELD].astype(str).tolist() if MODEL_FIELD in group.columns else []
            r2_columns = [field for field in R2_FIELDS if field in group.columns]
            timeout_values = pd.to_numeric(group.get("odeformer_integration_timeout_count_total", pd.Series([0] * len(group))), errors="coerce").fillna(0)
            rows.append(
                {
                    **values,
                    "repetition_count": int(len(group)),
                    "all_bitwise_identical": bool(len(set(raw_models)) <= 1 and all(group[field].astype(str).nunique(dropna=False) <= 1 for field in r2_columns)),
                    "handler_timeout_count_min": int(timeout_values.min()) if len(timeout_values) else 0,
                    "handler_timeout_count_max": int(timeout_values.max()) if len(timeout_values) else 0,
                    "r2_gt_0_9_flip": bool(any(pd.to_numeric(group[field], errors="coerce").gt(harness.R2_THRESHOLD).nunique(dropna=False) > 1 for field in r2_columns)),
                }
            )
    return pd.DataFrame(rows)


def summarize_cell_repetitions(records: list[dict[str, Any]], output_dir: Path) -> Path:
    path = output_dir / "cell_repetition_summary.csv"
    summarize_repetition_groups(records, CELL_KEYS).to_csv(path, index=False)
    return path


def expected_record_count(config_path: Path, system_ids: set[int] | None = None, config_ids: set[str] | None = None) -> int:
    config = load_json(config_path)
    if system_ids is not None:
        config = dict(config)
        config["system_ids"] = sorted(system_ids)
    benchmark = harness.load_benchmark(harness.resolve_path(config["benchmark_path"]))
    systems = harness.selected_systems(benchmark, config)
    configs = selected_config_objects(config, config_ids)
    return len(systems) * 2 * len(configs)


def collect_repetitions(output_dir: Path, expected_per_repetition: int, repetitions: int = 3) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rep_dirs = dict(discover_repetition_dirs(output_dir))
    missing_reps = [rep for rep in range(1, int(repetitions) + 1) if rep not in rep_dirs]
    if missing_reps:
        raise ValueError(f"missing repetition directories: {missing_reps}")
    records: list[dict[str, Any]] = []
    summary_rows = []
    for rep in range(1, int(repetitions) + 1):
        rep_records = read_record_dir(rep_dirs[rep] / "records")
        if len(rep_records) != int(expected_per_repetition):
            raise ValueError(f"repetition {rep} incomplete: expected {expected_per_repetition} records, found {len(rep_records)}")
        for record in rep_records:
            record = dict(record)
            record.setdefault("odeformer_grid_repetition", rep)
            records.append(record)
        summary_rows.append({"repetition": rep, "record_count": len(rep_records)})
    jsonl_path = output_dir / "records.jsonl"
    jsonl_path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + ("\n" if records else ""), encoding="utf-8")
    pd.DataFrame(records).to_csv(output_dir / "records.csv", index=False)
    pd.DataFrame(summary_rows).to_csv(output_dir / "repetition_counts.csv", index=False)
    summarize_cell_repetitions(records, output_dir)
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
    rerun_timeouts: bool = False,
    repetition: int | None = None,
    trajectory_export_dir: str | None = None,
) -> Path:
    config = load_json(config_path)
    if environment_id is not None:
        config = dict(config)
        config["environment_id"] = environment_id
    if trajectory_export_dir is not None:
        config = dict(config)
        config["trajectory_export_dir"] = trajectory_export_dir
    assert_faithful_mode(config)
    torch_threads, torch_thread_source = configure_torch_threads_from_env()
    benchmark = harness.load_benchmark(harness.resolve_path(config["benchmark_path"]))
    if system_ids is not None:
        config = dict(config)
        config["system_ids"] = sorted(system_ids)
    systems = harness.selected_systems(benchmark, config)
    export_dir = harness.resolve_path(config["trajectory_export_dir"])
    cells, trajectory_check = harness.load_exported_cells(export_dir, benchmark)
    out_dir = output_root(harness.resolve_path(output_dir or config["output_dir"]), repetition)
    records_dir = out_dir / "records"
    out_dir.mkdir(parents=True, exist_ok=True)
    configs = selected_config_objects(config, config_ids)
    preflight_odeformer_constant_optimization(configs)
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
                    "repetition": repetition,
                    "trajectory_export_dir": str(export_dir),
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
    budget = None
    hard_timeout = timeout_enforcement_available()
    if not hard_timeout:
        print("timeout_enforced=false: hard per-cell timeout is only enforced on POSIX runners", file=sys.stderr)
    for system, fit_ic, target_ic, ode_config in work_items:
        system_id = int(system["id"])
        config_id = str(ode_config["config_id"])
        path = records_dir / record_name(system_id, fit_ic, target_ic, config_id)
        if complete_record(path, rerun_timeouts=rerun_timeouts):
            continue
        fit_cell = cells[(system_id, fit_ic)]
        target_cell = cells[(system_id, target_ic)]
        start = time.perf_counter()
        if hard_timeout:
            record = run_cell_with_hard_timeout(system, fit_cell, target_cell, ode_config, budget)
        else:
            if config_id not in adapters:
                try:
                    adapters[config_id] = harness.build_odeformer_adapter(ode_config)
                except Exception as exc:
                    adapters[config_id] = RuntimeError(f"ODEFormer is not importable in this environment: {exc}")
            adapter_or_exc = adapters[config_id]
            record = run_odeformer_cell_direct(system, fit_cell, target_cell, ode_config, adapter_or_exc, False)
        elapsed = time.perf_counter() - start
        record["timeout_seconds_per_cell"] = budget
        record["odeformer_grid_mode"] = "faithful"
        record["odeformer_grid_repetition"] = repetition
        record["trajectory_export_dir"] = str(export_dir)
        record["torch_num_threads"] = observed_torch_threads() if torch_threads is None else torch_threads
        record["torch_num_threads_source"] = torch_thread_source
        if budget is None:
            record["timeout_enforced"] = False
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
    parser.add_argument("--rerun-timeouts", action="store_true")
    parser.add_argument("--repetition", type=int, default=None)
    parser.add_argument("--trajectory-export-dir", default="")
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.collect:
        output_dir = harness.resolve_path(args.output_dir)
        expected = expected_record_count(
            harness.resolve_path(args.config),
            system_ids=parse_int_set(args.system_ids),
            config_ids=parse_str_set(args.config_ids),
        )
        path = collect_repetitions(output_dir, expected, args.repetitions)
        print(path)
        return 0
    path = run(
        harness.resolve_path(args.config),
        args.output_dir or None,
        environment_id=args.environment_id or None,
        system_ids=parse_int_set(args.system_ids),
        config_ids=parse_str_set(args.config_ids),
        limit=args.limit,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        rerun_timeouts=args.rerun_timeouts,
        repetition=args.repetition,
        trajectory_export_dir=args.trajectory_export_dir or None,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
