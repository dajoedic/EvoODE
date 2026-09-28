#!/usr/bin/env python
"""Export true Phase-C coefficients for the WP-T1f warm-start probe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.aggregate.aggregate_phaseb_structure_metrics import (  # noqa: E402
    true_coefficients_for_phasec_terms,
)
from utils.metrics import check_required_columns, normalize_term_name, parse_pipe_terms  # noqa: E402


DEFAULT_CLASSIFICATION = (
    REPO_ROOT / "analysis" / "data" / "paper1_phaseC_v1" / "system_classification.csv"
)
DEFAULT_SUPPORT = REPO_ROOT / "studies" / "regression" / "phase_c_support.json"
DEFAULT_OUTPUT = REPO_ROOT / "studies" / "regression" / "wp_t1f_true_coefficients.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classification", default=str(DEFAULT_CLASSIFICATION))
    parser.add_argument("--support", default=str(DEFAULT_SUPPORT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def load_support(path: Path) -> dict[int, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    systems: dict[int, dict[str, Any]] = {}
    for system in data["systems"]:
        system_id = int(system["system_id"])
        if (
            system.get("representability") == "exact"
            and int(system.get("dim", -1)) in (2, 3)
            and system_id != 63
        ):
            systems[system_id] = system
    return systems


def exact_dim23_rows(classification_path: Path) -> pd.DataFrame:
    frame = pd.read_csv(classification_path)
    check_required_columns(
        frame,
        [
            "system_id",
            "dim",
            "equation_index",
            "equation",
            "representability",
            "matched_basis_terms",
        ],
    )
    mask = (
        (frame["representability"] == "exact")
        & (frame["dim"].isin([2, 3]))
        & (frame["system_id"] != 63)
    )
    return frame.loc[mask].sort_values(["system_id", "equation_index"])


def export_coefficients(classification_path: Path, support_path: Path) -> dict[str, Any]:
    support_by_system = load_support(support_path)
    rows = exact_dim23_rows(classification_path)
    systems: dict[str, Any] = {}

    for system_id, group in rows.groupby("system_id", sort=True):
        system_id_int = int(system_id)
        if system_id_int not in support_by_system:
            raise ValueError(f"Missing exact dim-2/3 support row for system {system_id_int}")
        support = support_by_system[system_id_int]
        expected_terms = support["support_terms"]
        dim = int(support["dim"])
        equations: list[dict[str, Any]] = []
        if len(group) != len(expected_terms):
            raise ValueError(
                f"System {system_id_int} has {len(group)} classification equations, "
                f"expected {len(expected_terms)}"
            )

        for _, row in group.iterrows():
            equation_index = int(row["equation_index"])
            terms = [normalize_term_name(term) for term in expected_terms[equation_index - 1]]
            matched_terms = [
                normalize_term_name(term)
                for term in parse_pipe_terms(str(row["matched_basis_terms"]))
            ]
            if set(matched_terms) != set(terms):
                raise ValueError(
                    f"System {system_id_int} equation {equation_index} support terms "
                    f"{sorted(terms)} do not exactly match classification matched terms "
                    f"{sorted(matched_terms)}"
                )
            coefficients = true_coefficients_for_phasec_terms(
                str(row["equation"]), dim, terms
            )
            coefficient_terms = set(coefficients)
            support_terms = set(terms)
            if coefficient_terms != support_terms:
                raise ValueError(
                    f"System {system_id_int} equation {equation_index} coefficient terms "
                    f"{sorted(coefficient_terms)} do not exactly match support terms "
                    f"{sorted(support_terms)}"
                )
            equations.append(
                {
                    "equation_index": equation_index,
                    "support_terms": terms,
                    "coefficients": {term: coefficients[term] for term in terms},
                }
            )

        systems[str(system_id_int)] = {
            "system_id": system_id_int,
            "dimension": dim,
            "equations": equations,
        }

    if set(systems) != {str(system_id) for system_id in support_by_system}:
        raise ValueError("Classification/support system sets differ for exact dim-2/3 systems")

    return {
        "basis_name": "staged_polynomial_basis_with_constant",
        "coefficient_source": "WP-N26 equation-column extraction with x_i -> u{i+1}",
        "classification_path": str(classification_path.relative_to(REPO_ROOT)),
        "support_path": str(support_path.relative_to(REPO_ROOT)),
        "systems": systems,
    }


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).resolve()
    data = export_coefficients(Path(args.classification).resolve(), Path(args.support).resolve())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
