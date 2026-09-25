import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import check_required_columns, normalize_term_name  # noqa: E402


PHASE_C_CAMPAIGN_ID = "paper1_phaseC_v1"
PHASE_C_BASIS_NAME = "staged_polynomial_basis_with_constant"
DEFAULT_PHASE_B_CLASSIFICATION = (
    ANALYSIS_ROOT / "data" / "paper1_phaseB_v1" / "system_classification.csv"
)
DEFAULT_SUPPORT = REPO_ROOT / "studies" / "regression" / "phase_c_support.json"
DEFAULT_OUTPUT = (
    ANALYSIS_ROOT / "data" / PHASE_C_CAMPAIGN_ID / "system_classification.csv"
)
EXPECTED_EXACT_SYSTEMS = 30


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Phase-C system classification from phase_c_support.json."
    )
    parser.add_argument("--phase-b-classification", default=str(DEFAULT_PHASE_B_CLASSIFICATION))
    parser.add_argument("--support", default=str(DEFAULT_SUPPORT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def staged_polynomial_basis_with_constant(dim: int) -> tuple[list[str], list[list[int]]]:
    term_names: list[str] = []
    term_groups: list[list[int]] = []

    def add_term(name: str, group: list[int]) -> None:
        term_names.append(name)
        group.append(len(term_names))

    group1: list[int] = []
    add_term("1", group1)
    for index in range(1, dim + 1):
        add_term(f"u{index}", group1)
    term_groups.append(group1)

    group2: list[int] = []
    for index in range(1, dim + 1):
        add_term(f"u{index}^2", group2)
    term_groups.append(group2)

    group3: list[int] = []
    for left in range(1, dim + 1):
        for right in range(left + 1, dim + 1):
            add_term(f"u{left}*u{right}", group3)
    term_groups.append(group3)

    group4: list[int] = []
    for index in range(1, dim + 1):
        add_term(f"u{index}^3", group4)
    term_groups.append(group4)

    group5: list[int] = []
    for index in range(1, dim + 1):
        add_term(f"sin(u{index})", group5)
        add_term(f"cos(u{index})", group5)
    term_groups.append(group5)

    return term_names, term_groups


def stage_for_term_idx(term_groups: list[list[int]], term_idx: int) -> int:
    for stage, term_group in enumerate(term_groups, start=1):
        if term_idx in term_group:
            return stage
    raise ValueError(f"Term index {term_idx} is not present in staged basis")


def expected_eq_stage(dim: int, support: list[int]) -> int:
    _, term_groups = staged_polynomial_basis_with_constant(dim)
    if not support:
        raise ValueError("Cannot derive expected stage from empty support")
    return max(stage_for_term_idx(term_groups, int(term_idx)) for term_idx in support)


def expected_stage(dim: int, support: list[list[int]] | None) -> int | None:
    if support is None:
        return None
    return max(expected_eq_stage(dim, equation_support) for equation_support in support)


def basis_terms_from_indexes(dim: int, support: list[int]) -> list[str]:
    term_names, _ = staged_polynomial_basis_with_constant(dim)
    terms: list[str] = []
    for term_idx in support:
        if term_idx < 1 or term_idx > len(term_names):
            raise ValueError(f"Term index {term_idx} is not present for dim={dim}")
        terms.append(term_names[term_idx - 1])
    return terms


def load_support(path: Path) -> tuple[str, dict[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    basis_name = str(payload.get("basis_name", ""))
    if basis_name != PHASE_C_BASIS_NAME:
        raise ValueError(
            f"Phase-C support basis_name={basis_name!r}, expected {PHASE_C_BASIS_NAME!r}"
        )
    systems = payload.get("systems")
    if not isinstance(systems, list):
        raise ValueError("phase_c_support.json must contain a systems list")
    by_system: dict[int, dict[str, Any]] = {}
    for entry in systems:
        system_id = int(entry["system_id"])
        by_system[system_id] = entry
    return basis_name, by_system


def pipe_terms(terms: list[str]) -> str:
    return "|".join(normalize_term_name(term) for term in terms)


def build_rows(phase_b: pd.DataFrame, support_by_system: dict[int, dict[str, Any]]) -> pd.DataFrame:
    check_required_columns(
        phase_b,
        [
            "system_id",
            "dim",
            "equation_index",
            "representability",
            "expected_stage",
            "expected_eq_stage",
            "matched_basis_terms",
            "unmatched_terms",
            "gap_reason",
        ],
    )
    exact_systems = {
        system_id
        for system_id, entry in support_by_system.items()
        if str(entry["representability"]) == "exact"
    }
    if len(exact_systems) != EXPECTED_EXACT_SYSTEMS:
        raise ValueError(
            f"Phase-C support has {len(exact_systems)} exact systems; "
            f"expected {EXPECTED_EXACT_SYSTEMS}"
        )

    rows: list[dict[str, Any]] = []
    for _, source_row in phase_b.iterrows():
        row = dict(source_row)
        system_id = int(row["system_id"])
        equation_index = int(row["equation_index"])
        if system_id not in support_by_system:
            raise ValueError(f"System {system_id} missing from Phase-C support table")
        support_entry = support_by_system[system_id]
        dim = int(support_entry["dim"])
        if int(row["dim"]) != dim:
            raise ValueError(f"System {system_id} dim mismatch between Phase-B and support")

        support_idxs = support_entry.get("support_idxs")
        support_terms = support_entry.get("support_terms")
        representability = str(support_entry["representability"])
        row["representability"] = representability
        row["basis_name"] = PHASE_C_BASIS_NAME
        row["unmatched_terms"] = ""

        if representability == "exact":
            if support_idxs is None or support_terms is None:
                raise ValueError(f"Exact system {system_id} has no support")
            eq_support_idxs = support_idxs[equation_index - 1]
            eq_support_terms = [normalize_term_name(term) for term in support_terms[equation_index - 1]]
            generated_terms = basis_terms_from_indexes(dim, eq_support_idxs)
            if eq_support_terms != generated_terms:
                raise ValueError(
                    f"System {system_id} equation {equation_index} support term mismatch: "
                    f"support_terms={eq_support_terms}, basis_indexes={generated_terms}"
                )
            row["matched_basis_terms"] = pipe_terms(eq_support_terms)
            row["gap_reason"] = ""
            row["expected_stage"] = expected_stage(dim, support_idxs)
            row["expected_eq_stage"] = expected_eq_stage(dim, eq_support_idxs)
        else:
            row["matched_basis_terms"] = ""
            row["gap_reason"] = str(support_entry.get("status", ""))
            row["expected_stage"] = ""
            row["expected_eq_stage"] = ""
        rows.append(row)

    output = pd.DataFrame(rows)
    exact_rows = output[output["representability"] == "exact"]
    observed_exact_systems = set(int(value) for value in exact_rows["system_id"].unique())
    if observed_exact_systems != exact_systems:
        raise ValueError("Generated exact-system set does not match Phase-C support")
    return output


def run(
    phase_b_classification_path: Path,
    support_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    if output_path != DEFAULT_OUTPUT:
        raise ValueError(f"Phase-C classification output must be {DEFAULT_OUTPUT}")
    phase_b = pd.read_csv(phase_b_classification_path)
    _, support_by_system = load_support(support_path)
    output = build_rows(phase_b, support_by_system)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False)
    return {
        "output_path": output_path,
        "n_rows": len(output),
        "n_exact_systems": output.loc[
            output["representability"] == "exact", "system_id"
        ].nunique(),
    }


def main() -> int:
    args = parse_args()
    try:
        result = run(
            Path(args.phase_b_classification),
            Path(args.support),
            Path(args.output).resolve(),
        )
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {result['output_path'].relative_to(REPO_ROOT)}")
    print(f"Rows: {result['n_rows']}")
    print(f"Exact systems: {result['n_exact_systems']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
