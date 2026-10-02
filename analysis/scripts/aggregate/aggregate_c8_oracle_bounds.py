"""Aggregate Phase-C C-8 oracle clamp-bound results."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_SUPPORT = Path("studies/regression/phase_c_support.json")
DEFAULT_REFERENCE_C5 = Path("outputs/wp_n3_oracle_refit_phase_c")
DEFAULT_OUTPUT_DIR = Path("outputs/phase_c_c8_oracle_bounds")
BOUNDS = ("10", "1000", "Inf")
GATE_EXCLUDED_SYSTEMS = set(range(54, 60))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("error") is not None:
                raise SystemExit(f"{path}:{line_no}: result has error={record.get('error')!r}")
            records.append(record)
    return records


def result_files(directories: list[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in directories:
        if not directory.exists():
            raise SystemExit(f"Input directory not found: {directory}")
        direct = directory / "results.jsonl"
        if direct.is_file():
            files.append(direct)
        files.extend(sorted(directory.glob("shard_*/results.jsonl")))
    return sorted(set(files))


def load_results(directories: list[Path], label: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in result_files(directories):
        for record in read_jsonl(path):
            key = str(record["cell_key"])
            if key in records:
                raise SystemExit(f"Duplicate {label} cell_key {key} in {path}")
            records[key] = record
    if not records:
        raise SystemExit(f"No {label} results found under {', '.join(str(path) for path in directories)}")
    return records


def load_support(path: Path) -> dict[int, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return {int(system["system_id"]): system for system in raw["systems"]}


def cell_sort_key(key: str) -> tuple[int, int, int]:
    parts = key.replace("sys", "").replace("seed", "").replace("ic", "").split("_")
    return (int(parts[0]), int(parts[2]), int(parts[1]))


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
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


def get_loss_evals(record: dict[str, Any]) -> int | None:
    meta = record.get("reference_fit_meta") or {}
    value = meta.get("loss_evals")
    return None if value is None else int(value)


def result_valid(record: dict[str, Any]) -> bool:
    meta = record.get("reference_fit_meta") or {}
    return bool(meta.get("result_valid", False))


def is_hard_error(record: dict[str, Any]) -> bool:
    return not result_valid(record) or finite_float(record.get("reference_loss")) is None


def is_penalty(record: dict[str, Any]) -> bool:
    loss = finite_float(record.get("reference_loss"))
    return loss is not None and loss >= 1e6


def r2_hit(record: dict[str, Any]) -> bool:
    r2 = finite_float(record.get("reference_r2"))
    return r2 is not None and r2 > 0.9


def meta_count(record: dict[str, Any], field: str) -> int | None:
    meta = record.get("reference_fit_meta") or {}
    if field not in meta:
        return None
    return int(meta[field])


def records_equal_for_control(lhs: dict[str, Any], rhs: dict[str, Any]) -> list[str]:
    diffs: list[str] = []
    for field in ("reference_loss", "reference_coefficients", "reference_r2"):
        if lhs.get(field) != rhs.get(field):
            diffs.append(field)
    lhs_evals = (lhs.get("reference_fit_meta") or {}).get("loss_evals")
    rhs_evals = (rhs.get("reference_fit_meta") or {}).get("loss_evals")
    if lhs_evals != rhs_evals:
        diffs.append("reference_fit_meta.loss_evals")
    return diffs


def run_control(bound10: dict[str, dict[str, Any]], reference: dict[str, dict[str, Any]]) -> None:
    missing = sorted(set(bound10) - set(reference), key=cell_sort_key)
    if missing:
        raise SystemExit(f"C-5 reference missing {len(missing)} bound-10 keys; first={missing[0]}")
    mismatches: list[str] = []
    for key in sorted(bound10, key=cell_sort_key):
        diffs = records_equal_for_control(bound10[key], reference[key])
        if diffs:
            mismatches.append(f"{key}: {', '.join(diffs)}")
    if mismatches:
        detail = "\n".join(mismatches[:20])
        raise SystemExit(f"Bound-10/C-5 control failed for {len(mismatches)} cells:\n{detail}")


def summarize_bound(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    loss_evals = [value for record in records if (value := get_loss_evals(record)) is not None]
    diverged_present = any(meta_count(record, "diverged_solves") is not None for record in records)
    nonfinite_present = any(meta_count(record, "nonfinite_solves") is not None for record in records)
    diverged_count = sum(1 for record in records if (meta_count(record, "diverged_solves") or 0) > 0)
    nonfinite_count = sum(1 for record in records if (meta_count(record, "nonfinite_solves") or 0) > 0)
    return {
        "n": n,
        "hard_errors": sum(1 for record in records if is_hard_error(record)),
        "penalties": sum(1 for record in records if is_penalty(record)),
        "loss_evals_median": statistics.median(loss_evals) if loss_evals else None,
        "loss_evals_q95": q_value([float(value) for value in loss_evals], 0.95),
        "r2_gt_0_9": sum(1 for record in records if r2_hit(record)),
        "reference_structure_hits": sum(1 for record in records if record.get("reference_structure_hit") is True),
        "retry_rate": sum(1 for record in records if (record.get("reference_fit_meta") or {}).get("retry_triggered") is True) / n if n else None,
        "diverged_or_nonfinite": sum(
            1
            for record in records
            if (meta_count(record, "diverged_solves") or 0) > 0
            or (meta_count(record, "nonfinite_solves") or 0) > 0
        ),
        "diverged_present": diverged_present,
        "nonfinite_present": nonfinite_present,
        "diverged_count": diverged_count,
        "nonfinite_count": nonfinite_count,
    }


def comparable(bound: dict[str, Any], baseline: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    n = int(bound["n"])
    base_n = int(baseline["n"])
    hard_pp = 100.0 * (bound["hard_errors"] / n - baseline["hard_errors"] / base_n)
    penalty_pp = 100.0 * (bound["penalties"] / n - baseline["penalties"] / base_n)
    effort_ratio = float(bound["loss_evals_median"]) / float(baseline["loss_evals_median"])
    ok = abs(hard_pp) <= 2.0 and abs(penalty_pp) <= 5.0 and effort_ratio <= 1.5
    return ok, {
        "hard_error_delta_pp": hard_pp,
        "penalty_delta_pp": penalty_pp,
        "median_loss_evals_ratio": effort_ratio,
    }


def same_fit(lhs: dict[str, Any], rhs: dict[str, Any]) -> bool:
    return (
        lhs.get("reference_loss") == rhs.get("reference_loss")
        and lhs.get("reference_coefficients") == rhs.get("reference_coefficients")
        and lhs.get("reference_r2") == rhs.get("reference_r2")
    )


def build_change_rows(records_by_bound: dict[str, dict[str, dict[str, Any]]], gate_keys: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = records_by_bound["10"]
    for bound in ("1000", "Inf"):
        for key in gate_keys:
            lhs = base[key]
            rhs = records_by_bound[bound][key]
            base_loss = finite_float(lhs.get("reference_loss"))
            loss = finite_float(rhs.get("reference_loss"))
            base_r2 = r2_hit(lhs)
            this_r2 = r2_hit(rhs)
            rows.append(
                {
                    "bound": bound,
                    "cell_key": key,
                    "system_id": rhs["system_id"],
                    "initial_condition_set": rhs["initial_condition_set"],
                    "seed": rhs["seed"],
                    "changed_fit": not same_fit(lhs, rhs),
                    "loss_better": loss is not None and base_loss is not None and loss < base_loss,
                    "loss_worse": loss is not None and base_loss is not None and loss > base_loss,
                    "r2_flip": base_r2 != this_r2,
                    "reference_loss_delta": None if loss is None or base_loss is None else loss - base_loss,
                    "reference_r2_delta": None
                    if finite_float(rhs.get("reference_r2")) is None or finite_float(lhs.get("reference_r2")) is None
                    else float(rhs["reference_r2"]) - float(lhs["reference_r2"]),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def write_markdown(
    path: Path,
    summary_rows: list[dict[str, Any]],
    change_rows: list[dict[str, Any]],
    gate_note: str,
    control_n: int,
    excluded_rows: dict[str, int],
) -> None:
    change_by_bound: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in change_rows:
        change_by_bound[str(row["bound"])].append(row)
    lines = [
        "# C-8 Oracle Bound Aggregation",
        "",
        f"Control: bound 10 equals C-5 on {control_n}/{control_n} cells.",
        f"Gate set: {gate_note}.",
        "",
        "## Stability Summary",
        "",
        "| bound | n | hard_errors | penalties | median_loss_evals | q95_loss_evals | R2_gt_0_9 | comparable_stable |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary_rows:
        lines.append(
            "| {bound} | {n} | {hard_errors} | {penalties} | {loss_evals_median} | {loss_evals_q95} | {r2_gt_0_9} | {comparable_stable} |".format(
                **{key: format_value(value) for key, value in row.items()}
            )
        )
    lines.extend(["", "## Changes Against Bound 10", ""])
    lines.append("| bound | changed_fits | loss_better | loss_worse | r2_flips |")
    lines.append("|---|---:|---:|---:|---:|")
    for bound in ("1000", "Inf"):
        rows = change_by_bound[bound]
        lines.append(
            f"| {bound} | {sum(row['changed_fit'] for row in rows)} | "
            f"{sum(row['loss_better'] for row in rows)} | {sum(row['loss_worse'] for row in rows)} | "
            f"{sum(row['r2_flip'] for row in rows)} |"
        )
    lines.extend(["", "## Excluded Exact Systems 54-59", ""])
    for bound in BOUNDS:
        lines.append(f"- {bound}: {excluded_rows.get(bound, 0)} records")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def aggregate(args: argparse.Namespace) -> None:
    records_by_bound = {
        "10": load_results(args.bound10, "bound 10"),
        "1000": load_results(args.bound1000, "bound 1000"),
        "Inf": load_results(args.bound_inf, "bound Inf"),
    }
    reference = load_results([args.reference_c5], "C-5 reference")
    run_control(records_by_bound["10"], reference)

    support = load_support(args.support)
    gate_systems = {
        system_id
        for system_id, system in support.items()
        if system.get("representability") == "exact" and system_id not in GATE_EXCLUDED_SYSTEMS
    }
    expected_gate_n = len(gate_systems) * 3 * 2
    common_keys = set.intersection(*(set(records) for records in records_by_bound.values()))
    gate_keys = sorted(
        [key for key in common_keys if int(records_by_bound["10"][key]["system_id"]) in gate_systems],
        key=cell_sort_key,
    )
    if not gate_keys:
        raise SystemExit("Gate set is empty")
    gate_note = (
        f"complete, n = {len(gate_keys)}"
        if len(gate_keys) == expected_gate_n
        else f"preliminary, n = {len(gate_keys)} of {expected_gate_n}"
    )

    summaries = {bound: summarize_bound([records_by_bound[bound][key] for key in gate_keys]) for bound in BOUNDS}
    summary_rows: list[dict[str, Any]] = []
    for bound in BOUNDS:
        row = {"bound": bound, **summaries[bound]}
        if bound == "10":
            row.update(
                {
                    "hard_error_delta_pp": 0.0,
                    "penalty_delta_pp": 0.0,
                    "median_loss_evals_ratio": 1.0,
                    "comparable_stable": "baseline",
                }
            )
        else:
            ok, deltas = comparable(summaries[bound], summaries["10"])
            row.update(deltas)
            row["comparable_stable"] = "yes" if ok else "no"
        summary_rows.append(row)

    change_rows = build_change_rows(records_by_bound, gate_keys)
    excluded_rows = {
        bound: sum(1 for record in records.values() if int(record["system_id"]) in GATE_EXCLUDED_SYSTEMS)
        for bound, records in records_by_bound.items()
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        args.output_dir / "bound_summary.csv",
        summary_rows,
        [
            "bound",
            "n",
            "hard_errors",
            "penalties",
            "loss_evals_median",
            "loss_evals_q95",
            "hard_error_delta_pp",
            "penalty_delta_pp",
            "median_loss_evals_ratio",
            "comparable_stable",
            "r2_gt_0_9",
            "reference_structure_hits",
            "retry_rate",
            "diverged_or_nonfinite",
            "diverged_present",
            "nonfinite_present",
            "diverged_count",
            "nonfinite_count",
        ],
    )
    write_csv(
        args.output_dir / "changes_by_cell.csv",
        change_rows,
        [
            "bound",
            "cell_key",
            "system_id",
            "initial_condition_set",
            "seed",
            "changed_fit",
            "loss_better",
            "loss_worse",
            "r2_flip",
            "reference_loss_delta",
            "reference_r2_delta",
        ],
    )
    write_markdown(args.output_dir / "summary.md", summary_rows, change_rows, gate_note, len(records_by_bound["10"]), excluded_rows)
    print(f"control={len(records_by_bound['10'])}/{len(records_by_bound['10'])}")
    print(f"gate={gate_note}")
    for row in summary_rows:
        print(
            f"bound={row['bound']} n={row['n']} hard_errors={row['hard_errors']} "
            f"penalties={row['penalties']} median_loss_evals={format_value(row['loss_evals_median'])} "
            f"r2_gt_0_9={row['r2_gt_0_9']} comparable_stable={row['comparable_stable']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bound10", nargs="+", required=True, type=Path)
    parser.add_argument("--bound1000", nargs="+", required=True, type=Path)
    parser.add_argument("--bound-inf", dest="bound_inf", nargs="+", required=True, type=Path)
    parser.add_argument("--reference-c5", default=DEFAULT_REFERENCE_C5, type=Path)
    parser.add_argument("--support", default=DEFAULT_SUPPORT, type=Path)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    aggregate(parser.parse_args())


if __name__ == "__main__":
    main()
