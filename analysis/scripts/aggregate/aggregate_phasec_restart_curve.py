"""Aggregate Phase-C P-04 restart-curve shard outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_VERSION = "WP-N44.restart_curve.v1"
K_VALUES = (1, 2, 3, 5, 10)
THRESHOLDS = (1e-12, 1e-10, 1e-8, 1e-6, 1e-4)
R2_THRESHOLD = 0.9
SENTINEL_LOSS = 1e6
INFEASIBLE_SYSTEMS = {54, 55, 56, 57, 58, 59}
DEFAULT_INPUT_DIR = Path("outputs/wp_n4_multistart_refit_phase_c")
DEFAULT_OUTPUT_DIR = Path("analysis/data/paper1_phaseC_v1/restart_curve")
DEFAULT_C5_DIR = Path("outputs/wp_n3_oracle_refit_phase_c")
DEFAULT_REGISTRY = Path("experiments/paper1_phaseC_v1/run_registry.csv")
DEFAULT_SUPPORT = Path("studies/regression/phase_c_support.json")
DEFAULT_DUPLICATE_SOURCE = Path("outputs/phase_c_campaign_221a3a7/history.jsonl")
DEFAULT_COLD_STARTS = Path(
    "analysis/data/wp_t1d_neighbourhood/"
    "wp_t1f_campaign_1db11932c4335e480d374c7de1be35593b62b447/truth_cold_by_cell.csv"
)


class AggregationError(RuntimeError):
    """Expected input or control failure."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else repo_root() / path


def fail(message: str) -> None:
    raise AggregationError(message)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                rows.append(json.loads(text))
            except json.JSONDecodeError as exc:
                fail(f"{path}:{line_no}: invalid JSON: {exc}")
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def q_value(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def cell_key(system_id: int, seed: int, ic: int) -> str:
    return f"sys{system_id:04d}_seed{seed}_ic{ic}"


def cell_sort_key(key: str) -> tuple[int, int, int, str]:
    try:
        sys_part, seed_part, ic_part = key.split("_")
        return (int(sys_part.removeprefix("sys")), int(seed_part.removeprefix("seed")), int(ic_part.removeprefix("ic")), key)
    except Exception:
        return (10**9, 10**9, 10**9, key)


def load_support(path: Path) -> dict[int, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {int(row["system_id"]): row for row in raw["systems"]}


def load_expected_cells(registry_path: Path, support: dict[int, dict[str, Any]]) -> set[str]:
    rows = read_csv(registry_path)
    expected: set[str] = set()
    for row in rows:
        if row.get("variant_slug") != "evogrow_v2_2_stage_capped":
            continue
        if str(row.get("condition")) != "capped" or boolish(row.get("use_pretuning")):
            continue
        system_id = int(row["system_id"])
        support_row = support.get(system_id, {})
        if row.get("system_representability") != "exact" and support_row.get("representability") != "exact":
            continue
        expected.add(cell_key(system_id, int(row["seed"]), int(row["initial_condition_set"])))
    return expected


def starts_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    direct = input_dir / "starts.jsonl"
    files = [direct] if direct.is_file() else []
    files.extend(sorted(input_dir.glob("shard_*_of_*/starts.jsonl")))
    return sorted(set(files))


def c5_files(c5_dir: Path) -> list[Path]:
    if not c5_dir.exists():
        return []
    direct = c5_dir / "results.jsonl"
    files = [direct] if direct.is_file() else []
    files.extend(sorted(c5_dir.glob("shard_*_of_*/results.jsonl")))
    return sorted(set(files))


def load_restart_records(input_dir: Path) -> tuple[dict[str, dict[str, Any]], list[Path]]:
    records: dict[str, dict[str, Any]] = {}
    paths = starts_files(input_dir)
    for path in paths:
        for row in read_jsonl(path):
            key = str(row.get("cell_key", ""))
            if not key:
                fail(f"{path}: row without cell_key")
            if key in records:
                fail(f"duplicate restart cell_key {key}")
            records[key] = row
    return records, paths


def load_c5_records(c5_dir: Path) -> tuple[dict[str, dict[str, Any]], list[Path]]:
    records: dict[str, dict[str, Any]] = {}
    paths = c5_files(c5_dir)
    for path in paths:
        for row in read_jsonl(path):
            key = str(row.get("cell_key", ""))
            if not key:
                fail(f"{path}: C-5 row without cell_key")
            if key in records:
                fail(f"duplicate C-5 cell_key {key}")
            records[key] = row
    return records, paths


def validate_complete(records: dict[str, dict[str, Any]], expected: set[str], allow_incomplete: bool) -> None:
    errors = sorted(key for key, row in records.items() if row.get("error") is not None)
    missing = sorted(expected - set(records), key=cell_sort_key)
    extra = sorted(set(records) - expected, key=cell_sort_key)
    if errors and not allow_incomplete:
        fail(f"restart input contains {len(errors)} rows with non-null error; first={errors[0]}")
    if (missing or extra or len(records) != len(expected)) and not allow_incomplete:
        fail(
            "restart input cell set is incomplete: "
            f"expected={len(expected)} actual={len(records)} missing={len(missing)} extra={len(extra)}"
        )


def checked_starts(record: dict[str, Any], structure: str, k: int) -> list[dict[str, Any]]:
    key = f"{structure}_starts"
    starts = record.get(key)
    if not isinstance(starts, list):
        fail(f"{record.get('cell_key')}: {key} is not a list")
    usable = [row for row in starts if int(row.get("start_index", 0)) <= k]
    present = {int(row.get("start_index", 0)) for row in usable}
    missing = sorted(set(range(1, k + 1)) - present)
    if missing:
        fail(f"{record.get('cell_key')}: missing {structure} starts for k={k}: {missing}")
    if not usable:
        fail(f"{record.get('cell_key')}: no {structure} starts for k={k}")
    return usable


def best_start(record: dict[str, Any], structure: str, k: int) -> dict[str, Any]:
    usable = checked_starts(record, structure, k)
    return min(usable, key=lambda row: float(row["loss"]))


def cumulative_evals(record: dict[str, Any], structure: str, k: int) -> int:
    total = 0
    for row in checked_starts(record, structure, k):
        meta = row.get("fit_meta") or {}
        if "loss_evals" not in meta:
            fail(f"{record.get('cell_key')}: missing {structure} fit_meta.loss_evals")
        total += int(meta["loss_evals"])
    return total


def strata_for(record: dict[str, Any], support: dict[int, dict[str, Any]]) -> list[str]:
    system_id = int(record["system_id"])
    dim = int(support[system_id]["dim"])
    strata = [f"dimension_{dim}"]
    if system_id in INFEASIBLE_SYSTEMS:
        strata.append("infeasible_bound_10")
    else:
        strata.extend(["feasible_bound_10", "all_feasible"])
    if dim == 3:
        strata.append("dim3_systems_52_57" if system_id in {52, 57} else "dim3_other_systems")
    return strata


def run_control(records: dict[str, dict[str, Any]], c5: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for key in sorted(records, key=cell_sort_key):
        c5_row = c5.get(key)
        if c5_row is None:
            fail(f"C-5 control missing cell {key}")
        accepted = (c5_row.get("reference_fit_meta") or {}).get("accepted_attempt")
        restart_start = best_start(records[key], "reference", 1)
        restart_loss = restart_start.get("loss")
        c5_loss = c5_row.get("reference_loss")
        comparable = accepted == 1
        passed = (restart_loss == c5_loss) if comparable else None
        row = {
            "cell_key": key,
            "system_id": records[key].get("system_id"),
            "initial_condition_set": records[key].get("initial_condition_set"),
            "seed": records[key].get("seed"),
            "c5_accepted_attempt": accepted,
            "comparable": comparable,
            "restart_reference_start1_loss": restart_loss,
            "c5_reference_loss": c5_loss,
            "passed": passed,
            "note": "" if comparable else "not comparable: C-5 accepted a later attempt",
        }
        rows.append(row)
        if comparable and not passed:
            failures.append(row)
    return rows, failures


def curve_rows(records: dict[str, dict[str, Any]], support: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records.values():
        for stratum in strata_for(record, support):
            for structure in ("reference", "oracle"):
                for k in K_VALUES:
                    best = best_start(record, structure, k)
                    grouped[(k, structure, stratum)].append(
                        {
                            "loss": float(best["loss"]),
                            "r2": finite_float(best.get("r2")),
                            "cost": cumulative_evals(record, structure, k),
                            "original_loss": finite_float(record.get("original_loss")),
                        }
                    )
    rows: list[dict[str, Any]] = []
    for (k, structure, stratum), group in sorted(grouped.items()):
        costs = [float(item["cost"]) for item in group]
        row: dict[str, Any] = {
            "k": k,
            "structure": structure,
            "stratum": stratum,
            "n_cells": len(group),
            "loss_evals_sum": int(sum(costs)),
            "loss_evals_q10_per_cell": q_value(costs, 0.10),
            "loss_evals_q50_per_cell": q_value(costs, 0.50),
            "loss_evals_q90_per_cell": q_value(costs, 0.90),
            "r2_gt_0_9_count": sum(1 for item in group if item["r2"] is not None and item["r2"] > R2_THRESHOLD),
            "sentinel_count": sum(1 for item in group if item["loss"] >= SENTINEL_LOSS),
            "reaches_or_beats_original_count": sum(
                1 for item in group if item["original_loss"] is not None and item["loss"] <= item["original_loss"]
            ),
        }
        row["r2_gt_0_9_rate"] = row["r2_gt_0_9_count"] / len(group) if group else None
        for threshold in THRESHOLDS:
            count = sum(1 for item in group if item["loss"] < threshold)
            label = f"loss_lt_{threshold:.0e}".replace("+", "")
            row[f"{label}_count"] = count
            row[f"{label}_share"] = count / len(group) if group else None
        rows.append(row)
    return rows


def first_hit_rows(records: dict[str, dict[str, Any]], support: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(records, key=cell_sort_key):
        record = records[key]
        first: int | None = None
        for k in K_VALUES:
            r2 = finite_float(best_start(record, "reference", k).get("r2"))
            if r2 is not None and r2 > R2_THRESHOLD:
                first = k
                break
        system_id = int(record["system_id"])
        rows.append(
            {
                "cell_key": key,
                "system_id": system_id,
                "dimension": int(support[system_id]["dim"]),
                "initial_condition_set": record["initial_condition_set"],
                "seed": record["seed"],
                "first_reference_r2_gt_0_9_k": first if first is not None else "not within 10",
            }
        )
    return rows


def k3_reading_rows(records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    feasible = [row for row in records.values() if int(row["system_id"]) not in INFEASIBLE_SYSTEMS]
    k3_hits = sum(1 for row in feasible if (finite_float(best_start(row, "reference", 3).get("r2")) or -math.inf) > R2_THRESHOLD)
    k10_hits = sum(1 for row in feasible if (finite_float(best_start(row, "reference", 10).get("r2")) or -math.inf) > R2_THRESHOLD)
    n = len(feasible)
    k3_rate = k3_hits / n if n else None
    k10_rate = k10_hits / n if n else None
    diff_pp = None if k3_rate is None or k10_rate is None else (k10_rate - k3_rate) * 100.0
    return [
        {
            "stratum": "all_feasible_reference",
            "n_cells": n,
            "k3_r2_gt_0_9_count": k3_hits,
            "k3_r2_gt_0_9_rate": k3_rate,
            "k10_r2_gt_0_9_count": k10_hits,
            "k10_r2_gt_0_9_rate": k10_rate,
            "k10_minus_k3_pp": diff_pp,
            "within_5_pp": None if diff_pp is None else diff_pp <= 5.0,
            "extra_loss_evals_k3_to_k10": sum(
                cumulative_evals(row, "reference", 10) - cumulative_evals(row, "reference", 3) for row in feasible
            ),
        }
    ]


def load_duplicate_rows(path: Path, support: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = read_jsonl(path) if path.suffix == ".jsonl" else []
    by_dimension: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row.get("variant") != "evogrow_v2_2_stage_capped" or str(row.get("condition")) != "capped" or boolish(row.get("use_pretuning")):
            continue
        system_id = int(row["system_id"])
        if support.get(system_id, {}).get("representability") != "exact":
            continue
        quantiles = row.get("structure_repeat_quantiles") or {}
        dim = int(support[system_id]["dim"])
        for name, value in quantiles.items():
            number = finite_float(value)
            if number is not None:
                by_dimension[dim][str(name)].append(number)
    out: list[dict[str, Any]] = []
    for dim, quantile_values in sorted(by_dimension.items()):
        for name, values in sorted(quantile_values.items()):
            out.append(
                {
                    "dimension": dim,
                    "source_field": "structure_repeat_quantiles",
                    "quantile_name": name,
                    "n_cells": len(values),
                    "across_cell_q10": q_value(values, 0.10),
                    "across_cell_q50": q_value(values, 0.50),
                    "across_cell_q90": q_value(values, 0.90),
                }
            )
    return out


def cold_start_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    grouped: dict[int, dict[str, int]] = defaultdict(lambda: {"hits": 0, "starts": 0, "cells": 0, "dimension": 0})
    for row in read_csv(path):
        system_id = int(row["system_id"])
        grouped[system_id]["dimension"] = int(row["dimension"])
        grouped[system_id]["hits"] += int(row["n_loss_lt_1e_8"])
        grouped[system_id]["starts"] += int(row["n_starts"])
        grouped[system_id]["cells"] += 1
    return [
        {
            "bound": "Inf",
            "m": 10,
            "threshold": "loss_lt_1e-8",
            "system_id": system_id,
            "dimension": data["dimension"],
            "n_cells": data["cells"],
            "n_starts": data["starts"],
            "n_hits": data["hits"],
            "hit_rate": data["hits"] / data["starts"] if data["starts"] else None,
        }
        for system_id, data in sorted(grouped.items())
    ]


def sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
    else:
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(str(child.relative_to(path)).replace("\\", "/").encode("utf-8"))
            digest.update(b"\0")
            digest.update(child.read_bytes())
    return digest.hexdigest()


def manifest_entry(path: Path, row_count: int | None = None) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_path(path), "row_count": row_count}


def write_manifest(
    path: Path,
    args: argparse.Namespace,
    restart_paths: list[Path],
    c5_paths: list[Path],
    counts: dict[str, int],
) -> None:
    data = {
        "script_version": SCRIPT_VERSION,
        "curve_k": list(K_VALUES),
        "thresholds": list(THRESHOLDS),
        "r2_threshold": R2_THRESHOLD,
        "inputs": {
            "restart_input_dir": manifest_entry(resolve(args.input_dir), counts["restart_rows"]),
            "restart_files": [manifest_entry(item) for item in restart_paths],
            "c5_oracle_dir": manifest_entry(resolve(args.c5_oracle_dir), counts["c5_rows"]),
            "c5_files": [manifest_entry(item) for item in c5_paths],
            "registry": manifest_entry(resolve(args.registry), counts["registry_rows"]),
            "support": manifest_entry(resolve(args.support), counts["support_rows"]),
            "duplicate_source": manifest_entry(resolve(args.duplicate_source), counts["duplicate_rows"]),
            "cold_starts": manifest_entry(resolve(args.cold_starts), counts["cold_start_rows"]),
            "script": manifest_entry(Path(__file__).resolve()),
        },
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def aggregate(args: argparse.Namespace) -> dict[str, Path]:
    input_dir = resolve(args.input_dir)
    output_dir = resolve(args.output_dir)
    c5_dir = resolve(args.c5_oracle_dir)
    registry_path = resolve(args.registry)
    support_path = resolve(args.support)
    duplicate_source = resolve(args.duplicate_source)
    cold_starts = resolve(args.cold_starts)

    support = load_support(support_path)
    expected = load_expected_cells(registry_path, support)
    if not expected:
        fail(f"expected cell set is empty from registry {registry_path}")
    records, restart_paths = load_restart_records(input_dir)
    c5, c5_paths = load_c5_records(c5_dir)
    validate_complete(records, expected, args.allow_incomplete)
    if not records:
        fail(f"no restart starts.jsonl files found under {input_dir}")
    if not c5:
        fail(f"no C-5 results.jsonl files found under {c5_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    control, failures = run_control(records, c5)
    outputs = {
        "control": output_dir / "control_reference_start1_vs_c5.csv",
        "curve": output_dir / "restart_curve.csv",
        "first_hit": output_dir / "reference_first_hit_by_cell.csv",
        "k3_reading": output_dir / "k3_reading.csv",
        "duplicate_quantiles": output_dir / "c1_duplicate_rate_quantiles_by_dimension.csv",
        "cold_starts": output_dir / "wp_t1f_cold_start_hit_rates_by_system.csv",
        "manifest": output_dir / "manifest.json",
    }
    write_csv(
        outputs["control"],
        control,
        [
            "cell_key",
            "system_id",
            "initial_condition_set",
            "seed",
            "c5_accepted_attempt",
            "comparable",
            "restart_reference_start1_loss",
            "c5_reference_loss",
            "passed",
            "note",
        ],
    )
    if failures:
        fail(f"C-5 control failed for {len(failures)} comparable cells; first={failures[0]['cell_key']}")

    duplicate_rows = load_duplicate_rows(duplicate_source, support)
    cold_rows = cold_start_rows(cold_starts)
    write_csv(outputs["curve"], curve_rows(records, support), curve_fieldnames())
    write_csv(
        outputs["first_hit"],
        first_hit_rows(records, support),
        ["cell_key", "system_id", "dimension", "initial_condition_set", "seed", "first_reference_r2_gt_0_9_k"],
    )
    write_csv(outputs["k3_reading"], k3_reading_rows(records), list(k3_reading_rows(records)[0]))
    write_csv(
        outputs["duplicate_quantiles"],
        duplicate_rows,
        ["dimension", "source_field", "quantile_name", "n_cells", "across_cell_q10", "across_cell_q50", "across_cell_q90"],
    )
    write_csv(
        outputs["cold_starts"],
        cold_rows,
        ["bound", "m", "threshold", "system_id", "dimension", "n_cells", "n_starts", "n_hits", "hit_rate"],
    )
    write_manifest(
        outputs["manifest"],
        args,
        restart_paths,
        c5_paths,
        {
            "restart_rows": len(records),
            "c5_rows": len(c5),
            "registry_rows": len(read_csv(registry_path)),
            "support_rows": len(support),
            "duplicate_rows": len(duplicate_rows),
            "cold_start_rows": len(cold_rows),
        },
    )
    return outputs


def curve_fieldnames() -> list[str]:
    fields = [
        "k",
        "structure",
        "stratum",
        "n_cells",
        "loss_evals_sum",
        "loss_evals_q10_per_cell",
        "loss_evals_q50_per_cell",
        "loss_evals_q90_per_cell",
        "r2_gt_0_9_count",
        "r2_gt_0_9_rate",
        "sentinel_count",
        "reaches_or_beats_original_count",
    ]
    for threshold in THRESHOLDS:
        label = f"loss_lt_{threshold:.0e}".replace("+", "")
        fields.extend([f"{label}_count", f"{label}_share"])
    return fields


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--c5-oracle-dir", default=DEFAULT_C5_DIR)
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--support", default=DEFAULT_SUPPORT)
    parser.add_argument("--duplicate-source", default=DEFAULT_DUPLICATE_SOURCE)
    parser.add_argument("--cold-starts", default=DEFAULT_COLD_STARTS)
    parser.add_argument("--allow-incomplete", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        outputs = aggregate(parse_args(argv))
    except (AggregationError, OSError, KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
