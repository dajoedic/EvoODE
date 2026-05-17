import argparse
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPECTED_TERMS = {
    2: {1: {"u1"}},
    3: {1: {"u1", "u1^2"}},
    11: {1: {"u1^3"}},
    24: {1: {"u2"}, 2: {"u1"}},
    26: {1: {"u1", "u1^2", "u1*u2"}, 2: {"u2", "u1*u2", "u2^2"}},
    31: {1: {"u1*u2"}, 2: {"u1*u2", "u2"}},
    54: {1: {"u1", "u2"}, 2: {"u1", "u2", "u1*u3"}, 3: {"u1*u2", "u3"}},
    63: {
        1: {"u1*u3"},
        2: {"u1*u3", "u2"},
        3: {"u2", "u3"},
        4: {"u3"},
    },
}

SYSTEM_NAMES = {
    2: "Exponential growth",
    3: "Logistic growth",
    11: "Critical slowing down - du=-u1^3",
    24: "Simple harmonic oscillator",
    26: "Lotka-Volterra competition",
    31: "SIR infection model",
    54: "Lorenz system",
    63: "SEIR-style epidemic system",
}

TERM_RE = re.compile(r"\((-?\d+\.\d+)\)\*(\S+)")
EQ_RE = re.compile(r"du_(\d+)\s*=")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose whether Phase A exact-support failures are metric artifacts."
    )
    parser.add_argument("--runs_dir", required=True, help="Path to experiment runs directory.")
    parser.add_argument(
        "--output",
        default="docs/phase1_diagnostic.md",
        help="Path to write the diagnostic Markdown report.",
    )
    return parser.parse_args()


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{path}: {exc}"


def parse_structure_pretty(s: str | None) -> dict[int, dict[str, float]]:
    if not s:
        return {}

    parsed: dict[int, dict[str, float]] = {}
    for line in str(s).splitlines():
        eq_match = EQ_RE.search(line)
        if eq_match is None:
            continue
        eq_idx = int(eq_match.group(1))
        parsed[eq_idx] = {
            term: float(coeff)
            for coeff, term in TERM_RE.findall(line)
        }
    return parsed


def prune_terms(eq_terms: dict[str, float]) -> set[str]:
    if not eq_terms:
        return set()
    max_abs = max(abs(v) for v in eq_terms.values())
    threshold = max(1e-6, 1e-3 * max_abs)
    return {name for name, coeff in eq_terms.items() if abs(coeff) >= threshold}


def infer_system_id(run_id: str) -> int | None:
    try:
        return int(run_id.split("_", 1)[0])
    except (ValueError, IndexError):
        return None


def fmt_bool(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "-"


def fmt_float(value: Any) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if math.isnan(number):
        return "-"
    if number == 0:
        return "0"
    if abs(number) < 0.001 or abs(number) >= 10000:
        return f"{number:.3e}"
    return f"{number:.6g}"


def format_terms_by_eq(terms_by_eq: dict[int, set[str]]) -> str:
    parts = []
    for eq_idx in sorted(terms_by_eq):
        terms = sorted(terms_by_eq[eq_idx])
        parts.append(f"eq{eq_idx}: {{{', '.join(terms)}}}")
    return "; ".join(parts)


def expected_terms_string(system_id: int) -> str:
    return format_terms_by_eq(EXPECTED_TERMS[system_id])


def pruned_terms_for(parsed: dict[int, dict[str, float]], system_id: int) -> dict[int, set[str]]:
    eq_ids = set(EXPECTED_TERMS[system_id]) | set(parsed)
    return {eq_idx: prune_terms(parsed.get(eq_idx, {})) for eq_idx in sorted(eq_ids)}


def pruned_match(system_id: int, pruned_terms: dict[int, set[str]]) -> bool:
    expected = EXPECTED_TERMS[system_id]
    if set(pruned_terms) != set(expected):
        return False
    return all(pruned_terms[eq_idx] == expected[eq_idx] for eq_idx in expected)


def diagnose(raw_match: bool, pruned_match_value: bool) -> str:
    if raw_match and pruned_match_value:
        return "correct"
    if not raw_match and pruned_match_value:
        return "metric_artifact"
    if not raw_match and not pruned_match_value:
        return "genuine_failure"
    return "unexpected"


def iter_run_records(runs_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    warnings: list[str] = []

    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
        result_path = run_dir / "result.json"
        if not result_path.exists():
            warnings.append(f"Skipping {run_dir.name}: missing result.json")
            continue

        result, error = load_json(result_path)
        if error is not None:
            warnings.append(f"Skipping malformed result: {error}")
            continue

        config_path = run_dir / "config.json"
        config, error = load_json(config_path)
        if error is not None:
            warnings.append(f"Skipping run with malformed config: {error}")
            continue

        assert result is not None
        assert config is not None
        run_id = str(config.get("run_id") or result.get("run_id") or run_dir.name)
        system_id = config.get("system_id")
        if system_id is None:
            system_id = infer_system_id(run_id)
        if system_id is None:
            warnings.append(f"Skipping {run_dir.name}: could not determine system_id")
            continue
        system_id = int(system_id)

        variant = str(config.get("variant", ""))
        if system_id not in EXPECTED_TERMS or "gp" in variant.lower():
            continue

        parsed = parse_structure_pretty(result.get("structure_pretty"))
        pruned_terms = pruned_terms_for(parsed, system_id)
        pruned_ok = pruned_match(system_id, pruned_terms)
        raw_match = bool(result.get("exact_support_match", False))

        records.append(
            {
                "run_id": run_id,
                "system_id": system_id,
                "variant": variant,
                "seed": config.get("seed"),
                "final_loss": result.get("final_loss"),
                "exact_support_match_raw": raw_match,
                "exact_support_match_pruned": pruned_ok,
                "structure_pretty": result.get("structure_pretty", ""),
                "pruned_terms_per_eq": format_terms_by_eq(pruned_terms),
                "expected_terms_per_eq": expected_terms_string(system_id),
                "diagnosis": diagnose(raw_match, pruned_ok),
            }
        )

    return records, warnings


def build_summary(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=[
                "system_id",
                "variant",
                "n_runs",
                "n_correct_raw",
                "n_correct_pruned",
                "n_metric_artifact",
                "n_genuine_failure",
                "mean_loss",
            ]
        )

    df = pd.DataFrame(records)
    summary = (
        df.groupby(["system_id", "variant"], sort=True)
        .agg(
            n_runs=("run_id", "count"),
            n_correct_raw=("exact_support_match_raw", "sum"),
            n_correct_pruned=("exact_support_match_pruned", "sum"),
            n_metric_artifact=("diagnosis", lambda s: int((s == "metric_artifact").sum())),
            n_genuine_failure=("diagnosis", lambda s: int((s == "genuine_failure").sum())),
            mean_loss=("final_loss", "mean"),
        )
        .reset_index()
    )
    return summary


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def system_findings(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    findings: dict[int, dict[str, Any]] = {}
    by_system: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_system[int(record["system_id"])].append(record)

    for system_id, system_records in by_system.items():
        total = len(system_records)
        raw = sum(1 for r in system_records if r["exact_support_match_raw"])
        pruned = sum(1 for r in system_records if r["exact_support_match_pruned"])
        artifacts = sum(1 for r in system_records if r["diagnosis"] == "metric_artifact")
        failures = sum(1 for r in system_records if r["diagnosis"] == "genuine_failure")
        correct = sum(1 for r in system_records if r["diagnosis"] == "correct")
        findings[system_id] = {
            "total": total,
            "raw": raw,
            "pruned": pruned,
            "artifacts": artifacts,
            "failures": failures,
            "correct": correct,
        }
    return findings


def write_report(
    output: Path,
    runs_dir: Path,
    records: list[dict[str, Any]],
    summary: pd.DataFrame,
    warnings: list[str],
) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    findings = system_findings(records)

    summary_rows = []
    for _, row in summary.iterrows():
        summary_rows.append(
            [
                int(row["system_id"]),
                row["variant"],
                int(row["n_runs"]),
                int(row["n_correct_raw"]),
                int(row["n_correct_pruned"]),
                int(row["n_metric_artifact"]),
                int(row["n_genuine_failure"]),
                fmt_float(row["mean_loss"]),
            ]
        )

    systems_where_pruning_fixes = sorted(
        sid for sid, item in findings.items() if item["artifacts"] > 0
    )
    systems_with_genuine_failure = sorted(
        sid for sid, item in findings.items() if item["failures"] > 0
    )

    lines = [
        "# Phase 1 Diagnostic: Metric Artifact vs. Structural Failure",
        f"Generated: {generated_at}",
        f"Source: {runs_dir.as_posix()}/",
        "",
        "## Summary",
        "",
        markdown_table(
            [
                "system",
                "variant",
                "n_runs",
                "raw_match",
                "pruned_match",
                "metric_artifacts",
                "genuine_failures",
                "mean_loss",
            ],
            summary_rows,
        ),
        "",
        "## Per-System Findings",
        "",
    ]

    for system_id in sorted(EXPECTED_TERMS):
        item = findings.get(
            system_id,
            {"total": 0, "raw": 0, "pruned": 0, "artifacts": 0, "failures": 0, "correct": 0},
        )
        lines.extend(
            [
                f"### System {system_id} ({SYSTEM_NAMES.get(system_id, 'exact system')})",
                (
                    f"Across {item['total']} EvoGrow Phase A runs, raw support matched in "
                    f"{item['raw']} runs and pruned support matched in {item['pruned']} runs. "
                    f"The diagnosis counts are {item['artifacts']} metric artifacts, "
                    f"{item['failures']} genuine structural failures, and {item['correct']} "
                    "runs already correct under the raw metric."
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Gate 1 Input",
            "",
            "- Systems where pruning fixes the metric: "
            + (", ".join(str(sid) for sid in systems_where_pruning_fixes) or "none"),
            "- Systems with genuine structural failure: "
            + (", ".join(str(sid) for sid in systems_with_genuine_failure) or "none"),
            "- Diagnosis: Pruning resolves near-zero-term artifacts where the expected support is otherwise present, but systems with missing or wrong terms remain genuine structural failures.",
        ]
    )

    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    runs_dir = Path(args.runs_dir)
    output = Path(args.output)

    records, warnings = iter_run_records(runs_dir)
    summary = build_summary(records)
    write_report(output, runs_dir, records, summary, warnings)

    for warning in warnings:
        print(f"Warning: {warning}")
    print(f"Wrote {output}")
    print(f"Evaluated {len(records)} EvoGrow exact-system runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
