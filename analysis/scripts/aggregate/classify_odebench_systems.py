import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = REPO_ROOT / "benchmarks" / "data" / "strogatz_extended.json"
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "analysis"
    / "data"
    / "paper1_phaseB_v1"
    / "system_classification.csv"
)
DEFAULT_REPORT = REPO_ROOT / "docs" / "paper1_phaseB_system_classification.md"

HAND_ENTERED_TRUTH = {
    2: {
        "representability": "exact",
        "expected_stage": 1,
        "expected_terms": [["u1"]],
    },
    3: {
        "representability": "exact",
        "expected_stage": 2,
        "expected_terms": [["u1", "u1^2"]],
    },
    11: {
        "representability": "exact",
        "expected_stage": 4,
        "expected_terms": [["u1^3"]],
    },
    23: {
        "representability": "surrogate",
        "expected_stage": 5,
        "expected_terms": None,
        "expected_gap_reasons": {"constant_offset"},
    },
    24: {
        "representability": "exact",
        "expected_stage": 1,
        "expected_terms": [["u2"], ["u1"]],
    },
    26: {
        "representability": "exact",
        "expected_stage": 3,
        "expected_terms": [["u1", "u1^2", "u1*u2"], ["u2", "u1*u2", "u2^2"]],
    },
    31: {
        "representability": "exact",
        "expected_stage": 3,
        "expected_terms": [["u1*u2"], ["u1*u2", "u2"]],
    },
    37: {
        "representability": "surrogate",
        "expected_stage": 4,
        "expected_terms": None,
        "expected_gap_reasons": {"mixed_higher_order_term"},
    },
    54: {
        "representability": "exact",
        "expected_stage": 3,
        "expected_terms": [
            ["u1", "u2"],
            ["u1", "u2", "u1*u3"],
            ["u1*u2", "u3"],
        ],
    },
    63: {
        "representability": "exact",
        "expected_stage": 3,
        "expected_terms": [["u1*u3"], ["u1*u3", "u2"], ["u2", "u3"], ["u3"]],
    },
}

FIELDNAMES = [
    "system_id",
    "dim",
    "description",
    "equation_index",
    "equation",
    "representability",
    "expected_stage",
    "expected_eq_stage",
    "matched_basis_terms",
    "unmatched_terms",
    "gap_reason",
    "source",
    "substituted_sets_identical",
    "n_substituted_sets",
    "variable_mapping",
]


@dataclass(frozen=True)
class TermClassification:
    term: str
    basis_term: str | None
    stage: int | None
    reason: str | None


@dataclass(frozen=True)
class EquationClassification:
    equation_index: int
    equation: str
    matched_terms: tuple[str, ...]
    unmatched_terms: tuple[str, ...]
    gap_reasons: tuple[str, ...]
    expected_eq_stage: int | None


@dataclass(frozen=True)
class SystemClassification:
    system_id: int
    dim: int
    description: str
    source: str
    representability: str
    expected_stage: int | None
    equations: tuple[EquationClassification, ...]
    substituted_sets_identical: bool
    n_substituted_sets: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify ODEBench systems against the staged EvoODE basis."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="ODEBench JSON path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Output Markdown report.")
    return parser.parse_args()


def u_name(symbol: sp.Symbol) -> str:
    return f"u{int(str(symbol).split('_', 1)[1]) + 1}"


def make_local_dict(dim: int) -> dict[str, Any]:
    local_dict: dict[str, Any] = {
        "sin": sp.sin,
        "cos": sp.cos,
        "exp": sp.exp,
        "log": sp.log,
        "cot": sp.cot,
        "Abs": sp.Abs,
    }
    for idx in range(dim):
        local_dict[f"x_{idx}"] = sp.Symbol(f"x_{idx}")
    return local_dict


def expression_terms(expr: sp.Expr) -> list[sp.Expr]:
    expanded = sp.expand(expr)
    if expanded == 0:
        return []
    return list(expanded.as_ordered_terms())


def strip_numeric_coefficient(term: sp.Expr) -> sp.Expr:
    coefficient, core = term.as_coeff_Mul()
    if coefficient != 1:
        return core
    return term


def format_sympy_term(term: sp.Expr, symbols: list[sp.Symbol]) -> str:
    substitutions = {
        symbol: sp.Symbol(f"u{idx + 1}") for idx, symbol in enumerate(symbols)
    }
    return str(term.xreplace(substitutions)).replace("**", "^")


def unsupported_function_names(term: sp.Expr) -> set[str]:
    return {func.func.__name__ for func in term.atoms(sp.Function)}


def classify_polynomial_core(core: sp.Expr, symbols: list[sp.Symbol]) -> TermClassification:
    poly = sp.Poly(core, *symbols)
    if len(poly.terms()) != 1:
        return TermClassification(
            format_sympy_term(core, symbols), None, None, "unsupported_product"
        )

    powers, coefficient = poly.terms()[0]
    if coefficient != 1:
        return TermClassification(
            format_sympy_term(core, symbols), None, None, "unsupported_product"
        )

    active = [(idx, power) for idx, power in enumerate(powers) if power != 0]
    total_degree = sum(powers)
    if len(active) == 1:
        idx, power = active[0]
        name = f"u{idx + 1}"
        if power == 1:
            return TermClassification(format_sympy_term(core, symbols), name, 1, None)
        if power == 2:
            return TermClassification(format_sympy_term(core, symbols), f"{name}^2", 2, None)
        if power == 3:
            return TermClassification(format_sympy_term(core, symbols), f"{name}^3", 4, None)
        return TermClassification(
            format_sympy_term(core, symbols), None, None, "unsupported_power"
        )

    if len(active) == 2 and total_degree == 2 and all(power == 1 for _, power in active):
        lhs, rhs = sorted(idx for idx, _ in active)
        return TermClassification(
            format_sympy_term(core, symbols), f"u{lhs + 1}*u{rhs + 1}", 3, None
        )

    if len(active) >= 2 and total_degree >= 3:
        return TermClassification(
            format_sympy_term(core, symbols), None, None, "mixed_higher_order_term"
        )

    return TermClassification(
        format_sympy_term(core, symbols), None, None, "unsupported_power"
    )


def classify_term(term: sp.Expr, symbols: list[sp.Symbol]) -> TermClassification:
    core = strip_numeric_coefficient(term)
    display_term = format_sympy_term(term, symbols)

    if not core.free_symbols:
        return TermClassification(display_term, None, None, "constant_offset")

    function_names = unsupported_function_names(core)
    if core.func in (sp.sin, sp.cos):
        arg = core.args[0]
        if arg in symbols:
            name = f"{core.func.__name__}({u_name(arg)})"
            return TermClassification(display_term, name, 5, None)
        return TermClassification(
            display_term, None, None, "unsupported_trigonometric_argument"
        )

    if function_names:
        trig_atoms = [
            atom
            for atom in core.atoms(sp.Function)
            if atom.func in (sp.sin, sp.cos) and atom.args and atom.args[0] not in symbols
        ]
        if trig_atoms:
            return TermClassification(
                display_term, None, None, "unsupported_trigonometric_argument"
            )
        return TermClassification(display_term, None, None, "unsupported_function")

    try:
        return classify_polynomial_core(core, symbols)
    except sp.PolynomialError:
        return TermClassification(display_term, None, None, "unsupported_power")


def classify_equation(equation: str, equation_index: int, dim: int) -> EquationClassification:
    symbols = [sp.Symbol(f"x_{idx}") for idx in range(dim)]
    expr = parse_expr(equation, local_dict=make_local_dict(dim), evaluate=True)
    term_results = [classify_term(term, symbols) for term in expression_terms(expr)]

    matched = sorted({result.basis_term for result in term_results if result.basis_term})
    unmatched = [
        f"{result.term} [{result.reason}]"
        for result in term_results
        if result.reason is not None
    ]
    gap_reasons = sorted({result.reason for result in term_results if result.reason})

    if gap_reasons:
        expected_stage = None
    else:
        stages = [result.stage for result in term_results if result.stage is not None]
        expected_stage = max(stages) if stages else 0

    return EquationClassification(
        equation_index=equation_index,
        equation=equation,
        matched_terms=tuple(matched),
        unmatched_terms=tuple(unmatched),
        gap_reasons=tuple(gap_reasons),
        expected_eq_stage=expected_stage,
    )


def substituted_sets_identical(entry: dict[str, Any]) -> bool:
    substituted = entry["substituted"]
    first = substituted[0]
    return all(candidate == first for candidate in substituted[1:])


def classify_system(entry: dict[str, Any]) -> SystemClassification:
    equations = tuple(
        classify_equation(equation, idx + 1, int(entry["dim"]))
        for idx, equation in enumerate(entry["substituted"][0])
    )
    representability = (
        "exact" if all(not equation.gap_reasons for equation in equations) else "surrogate"
    )
    exact_stages = [
        equation.expected_eq_stage
        for equation in equations
        if equation.expected_eq_stage is not None
    ]
    expected_stage = max(exact_stages) if representability == "exact" and exact_stages else None

    return SystemClassification(
        system_id=int(entry["id"]),
        dim=int(entry["dim"]),
        description=str(entry["eq_description"]),
        source=str(entry.get("source", "")),
        representability=representability,
        expected_stage=expected_stage,
        equations=equations,
        substituted_sets_identical=substituted_sets_identical(entry),
        n_substituted_sets=len(entry["substituted"]),
    )


def basis_sort_key(term: str) -> tuple[int, str]:
    stages = {}
    for dim in range(1, 10):
        stages[f"u{dim}"] = 1
        stages[f"u{dim}^2"] = 2
        stages[f"u{dim}^3"] = 4
        stages[f"sin(u{dim})"] = 5
        stages[f"cos(u{dim})"] = 5
    for lhs in range(1, 10):
        for rhs in range(lhs + 1, 10):
            stages[f"u{lhs}*u{rhs}"] = 3
    return stages.get(term, 99), term


def join_values(values: tuple[str, ...] | list[str]) -> str:
    return "|".join(values)


def variable_mapping(dim: int) -> str:
    return "; ".join(f"x_{idx}->u{idx + 1}" for idx in range(dim))


def write_csv(path: Path, systems: list[SystemClassification]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for system in systems:
            for equation in system.equations:
                writer.writerow(
                    {
                        "system_id": system.system_id,
                        "dim": system.dim,
                        "description": system.description,
                        "equation_index": equation.equation_index,
                        "equation": equation.equation,
                        "representability": system.representability,
                        "expected_stage": "" if system.expected_stage is None else system.expected_stage,
                        "expected_eq_stage": ""
                        if equation.expected_eq_stage is None
                        else equation.expected_eq_stage,
                        "matched_basis_terms": join_values(
                            sorted(equation.matched_terms, key=basis_sort_key)
                        ),
                        "unmatched_terms": join_values(list(equation.unmatched_terms)),
                        "gap_reason": join_values(list(equation.gap_reasons)),
                        "source": system.source,
                        "substituted_sets_identical": str(
                            system.substituted_sets_identical
                        ).lower(),
                        "n_substituted_sets": system.n_substituted_sets,
                        "variable_mapping": variable_mapping(system.dim),
                    }
                )


def stage_distribution(systems: list[SystemClassification]) -> Counter[int]:
    return Counter(
        system.expected_stage
        for system in systems
        if system.representability == "exact" and system.expected_stage is not None
    )


def gap_reason_counts(systems: list[SystemClassification]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for system in systems:
        for equation in system.equations:
            for unmatched_term in equation.unmatched_terms:
                if "[" in unmatched_term and unmatched_term.endswith("]"):
                    reason = unmatched_term.rsplit("[", 1)[1].rstrip("]")
                    counts[reason] += 1
    return counts


def dimension_breakdown(systems: list[SystemClassification]) -> dict[int, Counter[str]]:
    breakdown: dict[int, Counter[str]] = defaultdict(Counter)
    for system in systems:
        breakdown[system.dim][system.representability] += 1
    return breakdown


def system_terms(system: SystemClassification) -> list[list[str]]:
    return [
        sorted(list(equation.matched_terms), key=basis_sort_key)
        for equation in system.equations
    ]


def validation_rows(systems: list[SystemClassification]) -> list[list[str]]:
    by_id = {system.system_id: system for system in systems}
    rows = []
    for system_id, truth in sorted(HAND_ENTERED_TRUTH.items()):
        system = by_id[system_id]
        derived_terms = system_terms(system) if system.representability == "exact" else None
        derived_gap_reasons = {
            reason for equation in system.equations for reason in equation.gap_reasons
        }
        representability_ok = system.representability == truth["representability"]
        if truth["representability"] == "exact":
            stage_ok = system.expected_stage == truth["expected_stage"]
            expected_term_sets = [set(terms) for terms in truth["expected_terms"]]
            derived_term_sets = [set(terms) for terms in derived_terms or []]
            terms_ok = derived_term_sets == expected_term_sets
            gap_ok = True
        else:
            stage_ok = True
            terms_ok = True
            gap_ok = truth.get("expected_gap_reasons", set()).issubset(
                derived_gap_reasons
            )
        status = (
            "agree"
            if representability_ok and stage_ok and terms_ok and gap_ok
            else "disagree"
        )
        rows.append(
            [
                str(system_id),
                truth["representability"],
                system.representability,
                str(truth["expected_stage"]),
                "" if system.expected_stage is None else str(system.expected_stage),
                "" if truth["expected_terms"] is None else repr(truth["expected_terms"]),
                "" if derived_terms is None else repr(derived_terms),
                ", ".join(sorted(derived_gap_reasons)),
                status,
            ]
        )
    return rows


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, systems: list[SystemClassification], csv_path: Path) -> None:
    exact_count = sum(1 for system in systems if system.representability == "exact")
    surrogate_count = len(systems) - exact_count
    stage_counts = stage_distribution(systems)
    gap_counts = gap_reason_counts(systems)
    dim_counts = dimension_breakdown(systems)
    validation = validation_rows(systems)
    non_identical = [
        system.system_id for system in systems if not system.substituted_sets_identical
    ]

    stage_rows = [[stage, stage_counts[stage]] for stage in sorted(stage_counts)]
    gap_rows = [[reason, gap_counts[reason]] for reason in sorted(gap_counts)]
    dim_rows = [
        [
            dim,
            dim_counts[dim]["exact"],
            dim_counts[dim]["surrogate"],
            dim_counts[dim]["exact"] + dim_counts[dim]["surrogate"],
        ]
        for dim in sorted(dim_counts)
    ]

    lines = [
        "# ODEBench System Classification",
        "",
        "Generated by `analysis/scripts/aggregate/classify_odebench_systems.py` from `benchmarks/data/strogatz_extended.json`.",
        "",
        "Variables in the input are `x_0 ... x_{dim-1}` and are mapped to EvoODE basis variables `u1 ... u_dim` by the explicit shift `x_i -> u{i+1}`.",
        "",
        "`sympy==1.13.1` was added to `analysis/requirements.txt` because the classifier parses equations symbolically.",
        "",
        f"CSV output: `{csv_path.relative_to(REPO_ROOT).as_posix()}`",
        "",
        "## Exact vs Surrogate",
        "",
        markdown_table(
            ["category", "systems"],
            [["exact", exact_count], ["surrogate", surrogate_count]],
        ),
        "",
        "## Expected Stage Distribution",
        "",
        markdown_table(["expected_stage", "exact_systems"], stage_rows),
        "",
        "## Gap Reason Frequencies",
        "",
        markdown_table(["gap_reason", "unmatched_terms"], gap_rows),
        "",
        "## Dimension Breakdown",
        "",
        markdown_table(["dim", "exact", "surrogate", "total"], dim_rows),
        "",
        "## Substituted Equation Sets",
        "",
        "All substituted equation sets are identical across initial-condition sets."
        if not non_identical
        else "Non-identical substituted equation sets found for systems: "
        + ", ".join(str(system_id) for system_id in non_identical),
        "",
        "## Validation Against Hand-Entered Benchmark Truth",
        "",
        markdown_table(
            [
                "system",
                "truth_repr",
                "derived_repr",
                "truth_stage",
                "derived_stage",
                "truth_terms",
                "derived_terms",
                "derived_gap_reasons",
                "status",
            ],
            validation,
        ),
        "",
    ]

    disagreements = [row for row in validation if row[-1] != "agree"]
    if disagreements:
        lines.extend(
            [
                "## Findings",
                "",
                "Validation disagreements were found and should be investigated before using the classification.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Findings",
                "",
                "All ten hand-entered benchmark classifications agree with the symbolic classifier.",
                "",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def load_systems(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if len(data) != 63:
        raise ValueError(f"Expected 63 systems, found {len(data)}")
    return data


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    report_path = Path(args.report)

    entries = load_systems(input_path)
    systems = [classify_system(entry) for entry in entries]

    equation_count = sum(len(system.equations) for system in systems)
    if equation_count != 117:
        raise ValueError(f"Expected 117 equations, found {equation_count}")

    write_csv(output_path, systems)
    write_report(report_path, systems, output_path)

    exact_count = sum(1 for system in systems if system.representability == "exact")
    surrogate_count = len(systems) - exact_count
    disagreements = [row for row in validation_rows(systems) if row[-1] != "agree"]

    print(f"Wrote {output_path.relative_to(REPO_ROOT)} ({equation_count} rows)")
    print(f"Wrote {report_path.relative_to(REPO_ROOT)}")
    print(f"Exact systems: {exact_count}")
    print(f"Surrogate systems: {surrogate_count}")
    print(f"Validation disagreements: {len(disagreements)}")
    return 0 if not disagreements else 1


if __name__ == "__main__":
    sys.exit(main())
