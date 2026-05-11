import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.io import load_aggregate  # noqa: E402
from utils.metrics import check_required_columns  # noqa: E402


EXPECTED_VARIANTS = [
    "evogrow_v1",
    "evogrow_v2_1",
    "evogrow_v2_2_stage_local",
    "evogrow_v2_2_passive",
    "evogrow_v2_2_soft",
    "gp_baseline",
]
EXPECTED_SYSTEMS = [2, 3, 11, 23, 24, 26, 31, 37, 54, 63]
EXACT_SYSTEMS = [2, 3, 11, 24, 26, 31, 54, 63]
STAGED_SYSTEMS = [3, 11, 26, 31, 54, 63]
HIGH_STAGE_SYSTEMS = [11, 26, 31, 54, 63]

PRIMARY_VARIANTS = ["evogrow_v1", "evogrow_v2_1", "evogrow_v2_2_stage_local"]
H4_VARIANTS = [
    "evogrow_v2_2_stage_local",
    "evogrow_v2_2_soft",
    "evogrow_v2_2_passive",
]

REQUIRED_AGGREGATE_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "n_valid",
    "mean_loss",
    "exact_match_rate",
    "mean_stage_overshoot",
    "mean_wasted_levels",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Paper 1 Phase A hypotheses H1-H4 and write freeze memo."
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(path_value: str, config_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (config_path.parent / path).resolve()


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (pd.NA.__class__,)):
        return None
    if pd.isna(value) if not isinstance(value, (dict, list, tuple, str)) else False:
        return None
    return value


def fmt(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, str):
        return value
    value = float(value)
    if value == 0:
        return "0"
    if abs(value) < 0.001 or abs(value) >= 10000:
        return f"{value:.3e}"
    return f"{value:.6g}"


def compare(a: float, b: float) -> str:
    if pd.isna(a) or pd.isna(b):
        return "missing"
    if math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-12):
        return "equal"
    return "lower" if a < b else "higher"


def validate_inputs(df: pd.DataFrame) -> list[str]:
    check_required_columns(df, REQUIRED_AGGREGATE_COLUMNS)
    warnings: list[str] = []

    variants = set(df["variant_slug"].astype(str))
    missing_variants = [variant for variant in EXPECTED_VARIANTS if variant not in variants]
    if missing_variants:
        raise ValueError(f"Missing expected variants: {', '.join(missing_variants)}")

    systems = set(pd.to_numeric(df["system_id"], errors="coerce").dropna().astype(int))
    missing_systems = [system for system in EXPECTED_SYSTEMS if system not in systems]
    if missing_systems:
        raise ValueError(
            "Missing expected system IDs: "
            + ", ".join(str(system) for system in missing_systems)
        )

    zero_valid = df.loc[pd.to_numeric(df["n_valid"], errors="coerce").fillna(0) <= 0]
    for _, row in zero_valid.iterrows():
        warnings.append(
            f"n_valid=0 for variant={row['variant_slug']}, system={int(row['system_id'])}"
        )
    return warnings


def cell(df: pd.DataFrame, variant: str, system_id: int) -> pd.Series:
    match = df.loc[
        (df["variant_slug"] == variant) & (df["system_id"].astype(int) == system_id)
    ]
    if match.empty:
        raise ValueError(f"Missing aggregate cell: variant={variant}, system={system_id}")
    return match.iloc[0]


def evaluate_h1(df: pd.DataFrame) -> dict[str, Any]:
    per_system: dict[str, Any] = {}
    n_correct = 0
    for system_id in STAGED_SYSTEMS:
        v1 = cell(df, "evogrow_v1", system_id)
        v21 = cell(df, "evogrow_v2_1", system_id)
        v22 = cell(df, "evogrow_v2_2_stage_local", system_id)
        c21 = compare(v22["mean_stage_overshoot"], v21["mean_stage_overshoot"])
        c1 = compare(v22["mean_stage_overshoot"], v1["mean_stage_overshoot"])
        correct = c21 == "lower" and c1 == "lower"
        partial = (c21 == "lower") ^ (c1 == "lower")
        n_correct += int(correct)
        per_system[str(system_id)] = {
            "v1": v1["mean_stage_overshoot"],
            "v2_1": v21["mean_stage_overshoot"],
            "v2_2": v22["mean_stage_overshoot"],
            "v2_2_vs_v2_1": c21,
            "v2_2_vs_v1": c1,
            "direction": "correct" if correct else "partial" if partial else "wrong",
            "direction_correct": correct,
        }
    verdict = "SUPPORTED" if n_correct >= 4 else "PARTIAL" if n_correct >= 1 else "FALSIFIED"
    return {
        "metric": "mean_stage_overshoot",
        "systems_evaluated": STAGED_SYSTEMS,
        "per_system": per_system,
        "n_correct": n_correct,
        "n_systems": len(STAGED_SYSTEMS),
        "verdict": verdict,
    }


def best_evogrow_loss(df: pd.DataFrame, system_id: int) -> tuple[str, float]:
    losses = []
    for variant in EXPECTED_VARIANTS:
        if variant == "gp_baseline":
            continue
        row = cell(df, variant, system_id)
        losses.append((variant, row["mean_loss"]))
    valid = [(variant, loss) for variant, loss in losses if not pd.isna(loss)]
    if not valid:
        return "none", float("nan")
    return min(valid, key=lambda item: item[1])


def evaluate_h2(df: pd.DataFrame) -> dict[str, Any]:
    per_system: dict[str, Any] = {}
    n_competitive = 0
    for system_id in EXACT_SYSTEMS:
        rates = [cell(df, variant, system_id)["exact_match_rate"] for variant in EXPECTED_VARIANTS]
        collapsed = all((not pd.isna(rate)) and float(rate) == 0 for rate in rates)
        gp = cell(df, "gp_baseline", system_id)
        v22 = cell(df, "evogrow_v2_2_stage_local", system_id)
        if collapsed:
            best_variant, best_loss = best_evogrow_loss(df, system_id)
            competitive = (
                not pd.isna(best_loss)
                and not pd.isna(gp["mean_loss"])
                and float(best_loss) <= float(gp["mean_loss"])
            )
            metric_used = "mean_loss"
            detail = {
                "gp_exact_match": gp["exact_match_rate"],
                "v2_2_exact_match": v22["exact_match_rate"],
                "best_evogrow_variant": best_variant,
                "best_evogrow_loss": best_loss,
                "gp_loss": gp["mean_loss"],
            }
        else:
            competitive = (
                not pd.isna(v22["exact_match_rate"])
                and not pd.isna(gp["exact_match_rate"])
                and float(v22["exact_match_rate"]) >= float(gp["exact_match_rate"])
            )
            metric_used = "exact_match_rate"
            detail = {
                "gp_exact_match": gp["exact_match_rate"],
                "v2_2_exact_match": v22["exact_match_rate"],
            }
        n_competitive += int(competitive)
        per_system[str(system_id)] = {
            "recovery_metric_used": metric_used,
            "exact_match_collapsed": collapsed,
            "v2_2_competitive": competitive,
            **detail,
        }
    verdict = (
        "SUPPORTED" if n_competitive >= 5 else "PARTIAL" if n_competitive >= 2 else "FALSIFIED"
    )
    return {
        "metric": "exact_match_rate (with mean_loss fallback for collapsed systems)",
        "systems_evaluated": EXACT_SYSTEMS,
        "per_system": per_system,
        "n_competitive": n_competitive,
        "n_systems": len(EXACT_SYSTEMS),
        "verdict": verdict,
    }


def evaluate_h3(df: pd.DataFrame) -> dict[str, Any]:
    per_system: dict[str, Any] = {}
    n_correct = 0
    n_ties = 0
    for system_id in STAGED_SYSTEMS:
        v1 = cell(df, "evogrow_v1", system_id)
        v21 = cell(df, "evogrow_v2_1", system_id)
        v22 = cell(df, "evogrow_v2_2_stage_local", system_id)
        c21 = compare(v22["mean_wasted_levels"], v21["mean_wasted_levels"])
        c1 = compare(v22["mean_wasted_levels"], v1["mean_wasted_levels"])
        correct = c21 in {"lower", "equal"} and c1 in {"lower", "equal"}
        tied = c21 == "equal" or c1 == "equal"
        partial = (c21 in {"lower", "equal"}) ^ (c1 in {"lower", "equal"})
        n_correct += int(correct)
        n_ties += int(tied)
        per_system[str(system_id)] = {
            "v1": v1["mean_wasted_levels"],
            "v2_1": v21["mean_wasted_levels"],
            "v2_2": v22["mean_wasted_levels"],
            "v2_2_vs_v2_1": c21,
            "v2_2_vs_v1": c1,
            "has_tie": tied,
            "direction": "correct" if correct else "partial" if partial else "wrong",
            "direction_correct": correct,
        }
    verdict = "SUPPORTED" if n_correct >= 4 else "PARTIAL" if n_correct >= 1 else "FALSIFIED"
    return {
        "metric": "mean_wasted_levels",
        "systems_evaluated": STAGED_SYSTEMS,
        "per_system": per_system,
        "n_correct": n_correct,
        "n_ties": n_ties,
        "n_systems": len(STAGED_SYSTEMS),
        "verdict": verdict,
    }


def evaluate_h4(df: pd.DataFrame) -> dict[str, Any]:
    per_system: dict[str, Any] = {}
    n_expected = 0
    n_reverse = 0
    for system_id in HIGH_STAGE_SYSTEMS:
        hard = cell(df, "evogrow_v2_2_stage_local", system_id)["exact_match_rate"]
        soft = cell(df, "evogrow_v2_2_soft", system_id)["exact_match_rate"]
        passive = cell(df, "evogrow_v2_2_passive", system_id)["exact_match_rate"]
        expected = (
            not pd.isna(hard)
            and not pd.isna(soft)
            and not pd.isna(passive)
            and float(hard) >= float(soft) >= float(passive)
        )
        reverse = (
            not pd.isna(hard)
            and not pd.isna(soft)
            and not pd.isna(passive)
            and float(passive) >= float(soft) >= float(hard)
            and (float(passive) > float(hard))
        )
        n_expected += int(expected)
        n_reverse += int(reverse)
        per_system[str(system_id)] = {
            "hard_exact_match": hard,
            "soft_exact_match": soft,
            "passive_exact_match": passive,
            "ordering": "hard >= soft >= passive" if expected else "other",
            "expected_order": expected,
            "reverse_order": reverse,
        }
    verdict = (
        "SUPPORTED"
        if n_expected >= 3
        else "FALSIFIED"
        if n_reverse >= 3
        else "AMBIGUOUS"
    )
    return {
        "secondary": True,
        "metric": "exact_match_rate by usage policy",
        "systems_evaluated": HIGH_STAGE_SYSTEMS,
        "per_system": per_system,
        "n_expected_order": n_expected,
        "n_reverse_order": n_reverse,
        "verdict": verdict,
        "note": "H4 verdict does not affect H1-H3.",
    }


def load_generalization(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    if not path.exists():
        return (
            {
                "verdict": "OMIT",
                "n_cells_with_sufficient_data": 0,
                "summary": f"Generalization summary not found at {path}.",
                "columns": [],
            },
            [],
            [],
        )

    df = pd.read_csv(path)
    columns = list(df.columns)
    required = {"system", "variant", "n_exact_runs", "mean_refit_loss", "mean_fresh_loss"}
    if not required.issubset(columns):
        return (
            {
                "verdict": "OMIT",
                "n_cells_with_sufficient_data": 0,
                "summary": "Generalization summary columns do not match expected schema.",
                "columns": columns,
            },
            [],
            columns,
        )

    eligible = df.loc[pd.to_numeric(df["n_exact_runs"], errors="coerce") >= 3].copy()
    rows = eligible.to_dict(orient="records")
    if eligible.empty:
        verdict = "OMIT"
        summary = "No generalization cells have n_exact_runs >= 3."
    else:
        comparable = eligible["mean_refit_loss"] <= eligible["mean_fresh_loss"]
        n_refit_better = int(comparable.sum())
        verdict = (
            "INCLUDE_SUPPLEMENTARY"
            if n_refit_better >= math.ceil(len(eligible) / 2)
            else "INCLUDE_WITH_CAUTION"
        )
        summary = (
            f"{n_refit_better}/{len(eligible)} eligible cells have refit_loss <= fresh_loss."
        )
    return (
        {
            "verdict": verdict,
            "n_cells_with_sufficient_data": int(len(eligible)),
            "summary": summary,
            "columns": columns,
        },
        rows,
        columns,
    )


def allowed_claim(verdict: str, supported_text: str, partial_text: str) -> str:
    if verdict == "SUPPORTED":
        return supported_text
    if verdict == "PARTIAL":
        return partial_text
    return "claim removed"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return "\n".join(lines)


def summarize_support(per_system: dict[str, Any], key: str) -> str:
    supported = [sid for sid, values in per_system.items() if values[key]]
    unsupported = [sid for sid, values in per_system.items() if not values[key]]
    return (
        f"Supports: {', '.join(supported) if supported else 'none'}. "
        f"Does not support: {', '.join(unsupported) if unsupported else 'none'}."
    )


def write_memo(
    path: Path,
    generated_at: str,
    diagnostics: dict[str, Any],
    generalization_rows: list[dict[str, Any]],
) -> None:
    h1 = diagnostics["h1"]
    h2 = diagnostics["h2"]
    h3 = diagnostics["h3"]
    h4 = diagnostics["h4"]
    aux = diagnostics["auxiliary"]["generalization_study"]

    h1_rows = [
        [
            sid,
            values["v1"],
            values["v2_1"],
            values["v2_2"],
            values["direction"],
        ]
        for sid, values in h1["per_system"].items()
    ]
    h2_rows = []
    collapsed = []
    for sid, values in h2["per_system"].items():
        if values["exact_match_collapsed"]:
            collapsed.append(sid)
        h2_rows.append(
            [
                sid,
                values.get("gp_exact_match"),
                values.get("v2_2_exact_match"),
                values["recovery_metric_used"],
                values["v2_2_competitive"],
            ]
        )
    h3_rows = [
        [
            sid,
            values["v1"],
            values["v2_1"],
            values["v2_2"],
            values["direction"],
        ]
        for sid, values in h3["per_system"].items()
    ]
    h4_rows = [
        [
            sid,
            values["hard_exact_match"],
            values["soft_exact_match"],
            values["passive_exact_match"],
            values["ordering"],
        ]
        for sid, values in h4["per_system"].items()
    ]
    gen_rows = [
        [
            row.get("system", row.get("system_id", "-")),
            row.get("n_exact_runs"),
            row.get("mean_refit_loss"),
            row.get("mean_fresh_loss"),
        ]
        for row in generalization_rows
    ]

    content = f"""# Paper 1 - Freeze Memo: Phase A Results
Generated: {generated_at}
Experiment: paper1_phaseA_v1 (300/300 runs, all success=true)

This memo defines what Paper 1 is allowed to claim.
Nothing beyond this memo may appear in the paper.

---

## Block 1 - Primary Claims (H1, H2, H3)

### H1 - Stage Overshoot Reduction
Verdict: {h1["verdict"]}
Evidence:
{markdown_table(["system", "v1 overshoot", "v2.1 overshoot", "v2.2 overshoot", "direction"], h1_rows)}
Boundary conditions: {summarize_support(h1["per_system"], "direction_correct")}
Allowed paper claim: {allowed_claim(h1["verdict"], "Stage-local stopping reduces stage overshoot on the majority of evaluated staged exact systems.", "Stage-local stopping reduces stage overshoot only under the listed boundary conditions.")}

### H2 - Competitive Recovery Quality
Verdict: {h2["verdict"]}
Evidence:
{markdown_table(["system", "GP exact_match", "v2.2 exact_match", "metric used", "competitive?"], h2_rows)}
Collapse note: {", ".join(collapsed) if collapsed else "No systems used the exact_match=0 collapse fallback."}
Allowed paper claim: {allowed_claim(h2["verdict"], "EvoGrow v2.2 stage-local is competitive with GP recovery quality on the majority of exact systems.", "EvoGrow v2.2 stage-local is competitive only on the listed subset of exact systems.")}

### H3 - Wasted Levels Reduction
Verdict: {h3["verdict"]}
Evidence:
{markdown_table(["system", "v1 wasted", "v2.1 wasted", "v2.2 wasted", "direction"], h3_rows)}
Boundary conditions: {summarize_support(h3["per_system"], "direction_correct")}
Allowed paper claim: {allowed_claim(h3["verdict"], "Stage-local stopping reduces wasted levels on the majority of evaluated staged exact systems.", "Stage-local stopping reduces wasted levels only under the listed boundary conditions.")}

---

## Block 2 - Secondary Claim (H4)

H4 is secondary. Its verdict does not affect H1-H3.

### H4 - Usage Policy Effect
Verdict: {h4["verdict"]}
Evidence:
{markdown_table(["system", "hard exact_match", "soft exact_match", "passive exact_match", "ordering"], h4_rows)}
Allowed paper claim: {"Hard usage policy follows the expected hard >= soft >= passive ordering on the majority of high-stage systems." if h4["verdict"] == "SUPPORTED" else "C3 weakened, not reportable as positive result"}

---

## Block 3 - Auxiliary Evidence

### Generalization Study
Verdict: {aux["verdict"]}
Evidence:
{markdown_table(["system", "n_exact_runs", "mean_refit_loss", "mean_fresh_loss"], gen_rows) if gen_rows else "No eligible generalization cells available."}
Allowed use: supplementary material only, one interpretive sentence in discussion.

### profile_init
Role: Methods section or short Discussion paragraph.
Not used as evidence for H1-H4. No figures or tables generated.

---

## Known Limitations

- System 11: EvoGrow achieves loss ~4e-15 but exact_match=0 due to growth-without-pruning accumulating zero-coefficient terms. This is a genuine algorithmic limitation, not a metric error. Must be stated explicitly in the paper.
- Cells with low or zero exact_match remain scientific results and must not be hidden or repaired post hoc.
- The generalization study is auxiliary and cannot override the H1-H4 verdicts.

---

## Freeze Status

Evidence scope is frozen after this memo.
No new experiments may be added to Paper 1.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()

    try:
        config = load_config(config_path)
        experiment_id = config["experiment_id"]
        aggregate_path = resolve_path(config["aggregate_path"], config_path)
        diagnostics_path = resolve_path(config["diagnostics_path"], config_path)
        freeze_memo_path = resolve_path(config["freeze_memo_path"], config_path)
        generalization_path = resolve_path(config["generalization_summary_path"], config_path)

        aggregate = load_aggregate(aggregate_path)
        aggregate["system_id"] = pd.to_numeric(aggregate["system_id"], errors="raise").astype(int)
        warnings = validate_inputs(aggregate)

        generated_at = datetime.now(timezone.utc).isoformat()
        h1 = evaluate_h1(aggregate)
        h2 = evaluate_h2(aggregate)
        h3 = evaluate_h3(aggregate)
        h4 = evaluate_h4(aggregate)
        generalization, generalization_rows, generalization_columns = load_generalization(
            generalization_path
        )
        print(
            "Generalization summary columns: "
            + (", ".join(generalization_columns) if generalization_columns else "<not available>")
        )

        diagnostics = {
            "experiment_id": experiment_id,
            "generated_at": generated_at,
            "input_warnings": warnings,
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "h4": h4,
            "auxiliary": {
                "generalization_study": generalization,
                "profile_init": {
                    "verdict": "METHODS_ONLY",
                    "note": "profile_init.jl results are available (docs/profile_init_results.md). Role: Methods section or short Discussion paragraph only. Not used as evidence for H1-H4.",
                },
            },
        }

        diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostics_path.write_text(
            json.dumps(json_safe(diagnostics), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        write_memo(freeze_memo_path, generated_at, diagnostics, generalization_rows)

        for warning in warnings:
            print(f"Warning: {warning}")
        print(f"Evaluated {experiment_id}")
        print(f"  H1: {h1['verdict']} ({h1['n_correct']}/{h1['n_systems']})")
        print(f"  H2: {h2['verdict']} ({h2['n_competitive']}/{h2['n_systems']})")
        print(f"  H3: {h3['verdict']} ({h3['n_correct']}/{h3['n_systems']})")
        print(f"  H4: {h4['verdict']}")
        print(f"  Generalization: {generalization['verdict']}")
        print(f"  Diagnostics: {diagnostics_path}")
        print(f"  Freeze memo: {freeze_memo_path}")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
