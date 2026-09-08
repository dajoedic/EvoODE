import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REL_GRID = [1e-4, 1e-3, 1e-2, 1e-1]
ABS_GRID = [1e-8, 1e-6, 1e-4, 1e-2]
CURRENT_REL = 1e-3
CURRENT_ABS = 1e-6
R2_THRESHOLD = 0.9
CATEGORY_ORDER = [
    "hit",
    "extra_term_survives",
    "true_term_deleted",
    "true_term_never_found",
]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    rule_family: str
    rel: float | None
    abs: float | None
    is_current: bool = False

    def threshold(self, max_abs: float) -> float:
        if self.rule_family == "relative":
            if self.rel is None:
                raise ValueError("relative rule missing rel")
            return self.rel * max_abs
        if self.rule_family == "absolute":
            if self.abs is None:
                raise ValueError("absolute rule missing abs")
            return self.abs
        if self.rule_family == "mixed":
            if self.rel is None or self.abs is None:
                raise ValueError("mixed rule missing rel or abs")
            return max(self.abs, self.rel * max_abs)
        raise ValueError(f"unknown rule family: {self.rule_family}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure WP-N2 pruning-rule sensitivity on WP-N1 JSONL records."
    )
    parser.add_argument("--config", help="Path to config JSON.")
    parser.add_argument("--input", help="JSONL input override.")
    return parser.parse_args()


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(path_value: str, config_path: Path | None = None) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    candidates = [Path.cwd() / path, ANALYSIS_ROOT / path]
    if config_path is not None:
        candidates.append(config_path.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def fail(message: str) -> None:
    raise ValueError(message)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                fail(f"{path} line {line_number} is not valid JSON: {exc}")
            if not isinstance(record, dict):
                fail(f"{path} line {line_number} is not a JSON object")
            record["_line_number"] = line_number
            rows.append(record)
    if not rows:
        fail(f"{path} contains no records")
    return rows


def require(record: dict[str, Any], key: str) -> Any:
    if key not in record:
        fail(f"record line {record.get('_line_number', '?')} is missing {key}")
    return record[key]


def require_list(value: Any, name: str, line_number: int) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{name} at line {line_number} must be a list")
    return value


def term_set(values: Iterable[Any], name: str, line_number: int) -> set[str]:
    terms = set()
    for value in values:
        if not isinstance(value, str) or not value:
            fail(f"{name} at line {line_number} contains an invalid term")
        terms.add(value)
    return terms


def parse_equations(record: dict[str, Any]) -> list[dict[str, Any]]:
    line_number = int(record.get("_line_number", -1))
    expected_rows = require_list(
        require(record, "wp_n1_expected_support_terms"),
        "wp_n1_expected_support_terms",
        line_number,
    )
    model_rows = require_list(require(record, "model_terms"), "model_terms", line_number)
    if len(expected_rows) != len(model_rows):
        fail(
            f"record line {line_number} has {len(expected_rows)} expected equations "
            f"but {len(model_rows)} model equations"
        )

    equations = []
    for equation_index, (expected, model_terms) in enumerate(
        zip(expected_rows, model_rows), start=1
    ):
        expected_terms = term_set(
            require_list(expected, "expected equation terms", line_number),
            "expected equation terms",
            line_number,
        )
        model_items = require_list(model_terms, "model equation terms", line_number)
        coefficients: dict[str, float] = {}
        for item in model_items:
            if not isinstance(item, dict):
                fail(f"model term at line {line_number} equation {equation_index} is not an object")
            if "term" not in item or "coefficient" not in item:
                fail(
                    f"model term at line {line_number} equation {equation_index} "
                    "is missing term or coefficient"
                )
            term = item["term"]
            if not isinstance(term, str) or not term:
                fail(f"model term at line {line_number} equation {equation_index} has invalid term")
            try:
                coefficient = float(item["coefficient"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"model term at line {line_number} equation {equation_index} "
                    "has non-numeric coefficient"
                ) from exc
            coefficients[term] = coefficient

        equations.append(
            {
                "equation": equation_index,
                "expected_terms": expected_terms,
                "coefficients": coefficients,
            }
        )
    return equations


def build_rules() -> list[Rule]:
    rules = []
    for rel in REL_GRID:
        rules.append(Rule(f"relative_rel_{rel:.0e}", "relative", rel, None))
    for abs_threshold in ABS_GRID:
        rules.append(Rule(f"absolute_abs_{abs_threshold:.0e}", "absolute", None, abs_threshold))
    for rel in REL_GRID:
        for abs_threshold in ABS_GRID:
            rules.append(
                Rule(
                    f"mixed_abs_{abs_threshold:.0e}_rel_{rel:.0e}",
                    "mixed",
                    rel,
                    abs_threshold,
                    rel == CURRENT_REL and abs_threshold == CURRENT_ABS,
                )
            )
    return rules


def classify(expected: set[str], coefficients: dict[str, float], rule: Rule) -> dict[str, Any]:
    raw_terms = set(coefficients)
    max_abs = max((abs(value) for value in coefficients.values()), default=0.0)
    threshold = rule.threshold(max_abs)
    pruned_terms = {
        term for term, coefficient in coefficients.items() if abs(coefficient) >= threshold
    }
    raw_contains_truth = expected.issubset(raw_terms)
    pruned_contains_truth = expected.issubset(pruned_terms)
    extra_survives = bool(pruned_terms - expected)
    true_deleted = bool((expected & raw_terms) - pruned_terms)

    if pruned_terms == expected:
        category = "hit"
    elif pruned_contains_truth and extra_survives:
        category = "extra_term_survives"
    elif true_deleted:
        category = "true_term_deleted"
    elif not raw_contains_truth:
        category = "true_term_never_found"
    else:
        fail(
            "unclassifiable pruning state: "
            f"expected={sorted(expected)}, raw={sorted(raw_terms)}, pruned={sorted(pruned_terms)}"
        )

    return {
        "threshold": threshold,
        "max_abs": max_abs,
        "raw_terms": raw_terms,
        "pruned_terms": pruned_terms,
        "category": category,
        "raw_match": raw_terms == expected,
        "raw_contains_truth": raw_contains_truth,
        "extra_survives": extra_survives,
        "true_deleted": true_deleted,
        "both_pruning_errors": extra_survives and true_deleted,
    }


def base_cell_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        if str(require(record, "representability")) != "exact":
            continue
        r2 = float(require(record, "r2"))
        for equation in parse_equations(record):
            coefficients = equation["coefficients"]
            expected = equation["expected_terms"]
            rows.append(
                {
                    "cell_id": (
                        f"{record['condition']}|system={record['system_id']}|"
                        f"seed={record['seed']}|ic={record['initial_condition_set']}|"
                        f"eq={equation['equation']}"
                    ),
                    "basis": str(require(record, "condition")),
                    "equation": int(equation["equation"]),
                    "system_id": int(require(record, "system_id")),
                    "system_name": str(require(record, "system_name")),
                    "seed": int(require(record, "seed")),
                    "initial_condition_set": int(require(record, "initial_condition_set")),
                    "r2": r2,
                    "r2_gt_0_9": r2 > R2_THRESHOLD,
                    "expected_terms": expected,
                    "coefficients": coefficients,
                }
            )
    if not rows:
        fail("no exact records found")
    return rows


def evaluation_rows(cells: list[dict[str, Any]], rules: list[Rule]) -> pd.DataFrame:
    rows = []
    for cell in cells:
        for rule in rules:
            result = classify(cell["expected_terms"], cell["coefficients"], rule)
            rows.append(
                {
                    "rule_id": rule.rule_id,
                    "rule_family": rule.rule_family,
                    "rel": rule.rel,
                    "abs": rule.abs,
                    "is_current_rule": rule.is_current,
                    "basis": cell["basis"],
                    "equation": cell["equation"],
                    "cell_id": cell["cell_id"],
                    "system_id": cell["system_id"],
                    "seed": cell["seed"],
                    "initial_condition_set": cell["initial_condition_set"],
                    "r2": cell["r2"],
                    "r2_gt_0_9": cell["r2_gt_0_9"],
                    "max_abs": result["max_abs"],
                    "threshold": result["threshold"],
                    "category": result["category"],
                    "raw_match": result["raw_match"],
                    "raw_contains_truth": result["raw_contains_truth"],
                    "extra_survives": result["extra_survives"],
                    "true_deleted": result["true_deleted"],
                    "both_pruning_errors": result["both_pruning_errors"],
                    "expected_terms": ";".join(sorted(cell["expected_terms"])),
                    "raw_terms": ";".join(sorted(result["raw_terms"])),
                    "pruned_terms": ";".join(sorted(result["pruned_terms"])),
                }
            )
    return pd.DataFrame(rows)


def summarize_categories(group: pd.DataFrame, extra: dict[str, Any]) -> dict[str, Any]:
    n = int(len(group))
    row = {
        **extra,
        "n_cells": n,
        "structure_hits": int(group["category"].eq("hit").sum()),
        "r2_gt_0_9_count": int(group["r2_gt_0_9"].sum()),
        "r2_gt_0_9_rate": float(group["r2_gt_0_9"].mean()),
        "both_pruning_error_cells": int(group["both_pruning_errors"].sum()),
    }
    for category in CATEGORY_ORDER:
        row[f"{category}_cells"] = int(group["category"].eq(category).sum())
    return row


def current_decomposition(evaluations: pd.DataFrame) -> pd.DataFrame:
    subset = evaluations.loc[evaluations["is_current_rule"]].copy()
    rows = []
    for keys, group in subset.groupby(["basis", "equation"], sort=True):
        basis, equation = keys
        rows.append(summarize_categories(group, {"basis": basis, "equation": int(equation)}))
    return pd.DataFrame(rows)


def grid_summary(evaluations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in evaluations.groupby(
        ["rule_family", "rel", "abs", "rule_id", "basis", "equation"],
        sort=True,
        dropna=False,
    ):
        rule_family, rel, abs_threshold, rule_id, basis, equation = keys
        rows.append(
            summarize_categories(
                group,
                {
                    "rule_family": rule_family,
                    "rel": rel,
                    "abs": abs_threshold,
                    "rule_id": rule_id,
                    "basis": basis,
                    "equation": int(equation),
                },
            )
        )
    return pd.DataFrame(rows)


def raw_counterprobe(cells: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    raw_rows = []
    for cell in cells:
        raw_terms = set(cell["coefficients"])
        expected = cell["expected_terms"]
        raw_rows.append(
            {
                "basis": cell["basis"],
                "equation": cell["equation"],
                "r2_gt_0_9": cell["r2_gt_0_9"],
                "raw_match": raw_terms == expected,
                "raw_contains_truth": expected.issubset(raw_terms),
            }
        )
    raw = pd.DataFrame(raw_rows)
    for keys, group in raw.groupby(["basis", "equation"], sort=True):
        basis, equation = keys
        n = int(len(group))
        rows.append(
            {
                "basis": basis,
                "equation": int(equation),
                "n_cells": n,
                "raw_match_count": int(group["raw_match"].sum()),
                "raw_match_rate": float(group["raw_match"].mean()),
                "truth_subset_count": int(group["raw_contains_truth"].sum()),
                "truth_subset_rate": float(group["raw_contains_truth"].mean()),
                "r2_gt_0_9_count": int(group["r2_gt_0_9"].sum()),
                "r2_gt_0_9_rate": float(group["r2_gt_0_9"].mean()),
            }
        )
    return pd.DataFrame(rows)


def switching_summary(evaluations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in evaluations.groupby(["basis", "equation", "cell_id"], sort=True):
        basis, equation, cell_id = keys
        categories = set(group["category"])
        hit_values = set(group["category"].eq("hit"))
        rows.append(
            {
                "basis": basis,
                "equation": int(equation),
                "cell_id": cell_id,
                "n_categories_seen": len(categories),
                "category_switches": len(categories) > 1,
                "hit_status_switches": len(hit_values) > 1,
                "categories_seen": ";".join(sorted(categories)),
            }
        )
    per_cell = pd.DataFrame(rows)
    summary_rows = []
    for keys, group in per_cell.groupby(["basis", "equation"], sort=True):
        basis, equation = keys
        n = int(len(group))
        summary_rows.append(
            {
                "basis": basis,
                "equation": int(equation),
                "n_cells": n,
                "category_switch_cells": int(group["category_switches"].sum()),
                "hit_status_switch_cells": int(group["hit_status_switches"].sum()),
                "category_stable_cells": int((~group["category_switches"]).sum()),
                "hit_status_stable_cells": int((~group["hit_status_switches"]).sum()),
            }
        )
    return pd.DataFrame(summary_rows), per_cell


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.12g")


def write_tex(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(df.to_latex(index=False, escape=True, float_format="%.6g"), encoding="utf-8")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve() if args.config else None
    try:
        config = load_config(config_path)
        input_value = args.input or config.get("input_path")
        if not input_value:
            fail("provide --input or a config with input_path")
        input_path = resolve_path(str(input_value), config_path)
        data_dir = (ANALYSIS_ROOT / config.get("data_output_dir", "data/wp_n2_pruning_sensitivity")).resolve()
        table_dir = (
            ANALYSIS_ROOT / config.get("table_output_dir", "tables/wp_n2_pruning_sensitivity")
        ).resolve()

        records = load_jsonl(input_path)
        cells = base_cell_rows(records)
        rules = build_rules()
        evaluations = evaluation_rows(cells, rules)
        decomposition = current_decomposition(evaluations)
        grid = grid_summary(evaluations)
        raw = raw_counterprobe(cells)
        switch_summary, switch_cells = switching_summary(evaluations)

        data_outputs = {
            "wp_n2_pruning_evaluations.csv": evaluations,
            "wp_n2_pruning_switching_cells.csv": switch_cells,
        }
        table_outputs = {
            "wp_n2_current_decomposition": decomposition,
            "wp_n2_rule_grid": grid,
            "wp_n2_raw_counterprobe": raw,
            "wp_n2_switching_summary": switch_summary,
        }

        for filename, frame in data_outputs.items():
            write_csv(frame, data_dir / filename)
        for stem, frame in table_outputs.items():
            write_csv(frame, table_dir / f"{stem}.csv")
            write_tex(frame, table_dir / f"{stem}.tex")

        print("Aggregated WP-N2 pruning sensitivity")
        print(f"  Input: {input_path}")
        print(f"  Exact cell-equations: {len(cells)}")
        print(f"  Rules: {len(rules)}")
        print(f"  Data output: {data_dir}")
        print(f"  Table output: {table_dir}")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
