"""Inventory frozen C-1 supports on exact systems, without refitting or pruning."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "analysis"))
from utils.metrics import check_required_columns, parse_support_terms_json

REGISTRY = Path("analysis/data/paper1_phaseC_v1/final_2026-10-05/phasec_analysis_registry_c1.csv")
SUPPORT = Path("studies/regression/phase_c_support.json")
DEFAULT_OUTPUT = Path("analysis/data/paper1_phaseC_v1/c1_structure_inventory")
# CLAUDE.md, Known Gaps: bound feasibility decision of 2026-10-01.
# No per-system table carrying these exact stratum labels is used as an input.
DIM3_FEASIBLE = frozenset({52, 61})
DIM3_BOUND_INFEASIBLE = frozenset({54, 55, 56, 57, 58, 59})
STRATA = ("dim1", "dim2", "dim3_feasible", "dim3_bound_infeasible", "dim4")
CLASSES = ("exact", "disjoint", "subset", "superset", "mixed")
KINDS = ("raw", "pruned")
CLASS_DEFINITION = (
    "missing=|T\\F|; extra=|F\\T|; tp=|T intersection F|. "
    "In order: exact if missing=0 and extra=0; disjoint if tp=0; "
    "subset if extra=0; superset if missing=0; mixed otherwise. "
    "needs_add=missing>0; needs_remove=extra>0. "
    "Cell supports are (1-based equation index, term) pairs."
)
IDS = ["run_id", "system_id", "system_dim", "stratum", "seed", "initial_condition_set"]


def classify(truth: set, found: set) -> dict:
    """Classify sets in the specified order, including empty-set cases."""
    missing, extra, tp = len(truth - found), len(found - truth), len(truth & found)
    if missing == 0 and extra == 0:
        label = "exact"
    elif tp == 0:
        label = "disjoint"
    elif extra == 0:
        label = "subset"
    elif missing == 0:
        label = "superset"
    else:
        label = "mixed"
    return {"class": label, "n_true": len(truth), "missing": missing, "extra": extra,
            "needs_add": missing > 0, "needs_remove": extra > 0}


def cell_support_pairs(equations: list[list[str]]) -> set[tuple[int, str]]:
    return {(index, term) for index, terms in enumerate(equations, 1) for term in terms}


def support_equations(value, label: str) -> list[list[str]]:
    data = json.loads(value) if isinstance(value, str) else value
    if not isinstance(data, list) or any(
        not isinstance(terms, list) or any(not isinstance(term, str) for term in terms)
        for terms in data
    ):
        raise ValueError(f"{label}: expected a list of term-name lists")
    # Reuse the pipeline parser, but require canonical input: do not change frozen supports.
    parsed = parse_support_terms_json(data)
    if parsed != data:
        raise ValueError(f"{label}: noncanonical term spelling")
    return parsed


def stratum_for(system_id: int, dim: int) -> str:
    if dim in (1, 2):
        return f"dim{dim}"
    if dim == 3 and system_id in DIM3_FEASIBLE:
        return "dim3_feasible"
    if dim == 3 and system_id in DIM3_BOUND_INFEASIBLE:
        return "dim3_bound_infeasible"
    if dim == 4 and system_id == 63:
        return "dim4"
    raise ValueError(f"Unexpected exact system/dimension: {system_id}/{dim}")


def strict_bool(value, label: str) -> bool:
    text = str(value).strip().lower()
    if text not in {"true", "false"}:
        raise ValueError(f"{label}: invalid boolean {value!r}")
    return text == "true"


def build_inventory(registry: pd.DataFrame, support: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    check_required_columns(registry, [c for c in IDS if c != "stratum"] + [
        "r2", "support_terms", "pruned_support_terms", "exact_support_match_raw",
        "exact_support_match_pruned", "variant"])
    truth = {int(s["system_id"]): s for s in support["systems"] if s["representability"] == "exact"}
    if len(truth) != 30:
        raise ValueError(f"Expected 30 exact systems, found {len(truth)}")
    selected = registry.loc[registry.system_id.isin(truth)].copy()
    if len(registry) != 378 or len(selected) != 180:
        raise ValueError(f"Expected 378 C-1 rows / 180 exact rows, found {len(registry)} / {len(selected)}")
    if set(registry.variant) != {"evogrow_v2_2_stage_capped"}:
        raise ValueError("Registry must contain only the C-1 capped variant")
    if selected.run_id.duplicated().any() or selected.duplicated(["system_id", "seed", "initial_condition_set"]).any():
        raise ValueError("Duplicate C-1 cell identity")
    equations, cells, mismatches = [], [], []
    for row in selected.sort_values(["system_id", "seed", "initial_condition_set"]).to_dict("records"):
        sid, dim = int(row["system_id"]), int(row["system_dim"])
        true = support_equations(truth[sid]["support_terms"], f"system {sid} truth")
        if len(true) != dim or int(truth[sid]["dim"]) != dim:
            raise ValueError(f"{row['run_id']}: true equation count/dimension mismatch")
        base = {key: row[key] for key in IDS if key != "stratum"}
        base["stratum"] = stratum_for(sid, dim)
        base["r2"] = row["r2"]
        cell = dict(base)
        for kind, column in (("raw", "support_terms"), ("pruned", "pruned_support_terms")):
            found = support_equations(row[column], f"{row['run_id']} {kind}")
            if len(found) != len(true):
                raise ValueError(f"{row['run_id']} {kind}: expected {len(true)} equations, found {len(found)}")
            result = classify(cell_support_pairs(true), cell_support_pairs(found))
            for field in ("class", "missing", "extra"):
                cell[f"{kind}_{field}"] = result[field]
            expected = strict_bool(row[f"exact_support_match_{kind}"], f"{row['run_id']} {kind}")
            if (result["class"] == "exact") != expected:
                mismatches.append({"run_id": row["run_id"], "kind": kind,
                                   "class": result["class"], "registry_exact": expected})
            for index, (t, f) in enumerate(zip(true, found), 1):
                t, f = set(t), set(f)
                equations.append({**base, "equation_index": index, "kind": kind, **classify(t, f),
                                  "missing_terms": json.dumps(sorted(t - f)),
                                  "extra_terms": json.dumps(sorted(f - t))})
        cells.append(cell)
    if mismatches:
        raise ValueError("Exact-match control diverging rows: " + json.dumps(mismatches))
    return pd.DataFrame(equations), pd.DataFrame(cells)


def git_head(repo: Path) -> str:
    """Read HEAD without running any Git command (protocol forbids Git operations)."""
    git_dir = repo / ".git"
    if git_dir.is_file():
        git_dir = (repo / git_dir.read_text().strip().split(": ", 1)[1]).resolve()
    common = git_dir
    if (git_dir / "commondir").exists():
        common = (git_dir / (git_dir / "commondir").read_text().strip()).resolve()
    head = (git_dir / "HEAD").read_text().strip()
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    for directory in (git_dir, common):
        if (directory / ref).is_file():
            return (directory / ref).read_text().strip()
    packed = common / "packed-refs"
    if packed.exists():
        for line in packed.read_text().splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", 1)
                if name == ref:
                    return commit
    raise ValueError(f"Cannot resolve HEAD reference: {ref}")


def summaries(equations: pd.DataFrame, cells: pd.DataFrame) -> dict[str, pd.DataFrame]:
    eq_summary, cell_summary, system_summary, transitions, r2_summary = [], [], [], [], []
    for stratum in STRATA:
        eq = equations.loc[equations.stratum == stratum]
        ce = cells.loc[cells.stratum == stratum]
        for kind in KINDS:
            ek = eq.loc[eq.kind == kind]
            for label in CLASSES:
                eq_summary.append(dict(stratum=stratum, kind=kind, summary_type="class", **{
                    "class": label, "needs_add": None, "needs_remove": None, "count": int((ek['class'] == label).sum())}))
                cell_summary.append(dict(stratum=stratum, kind=kind, **{
                    "class": label, "count": int((ce[f'{kind}_class'] == label).sum())}))
            for add, remove in ((False, False), (False, True), (True, False), (True, True)):
                eq_summary.append(dict(stratum=stratum, kind=kind, summary_type="two_axis", **{
                    "class": None, "needs_add": add, "needs_remove": remove,
                    "count": int(((ek.needs_add == add) & (ek.needs_remove == remove)).sum())}))
        for raw in CLASSES:
            for pruned in CLASSES:
                transitions.append(dict(stratum=stratum, raw_class=raw, pruned_class=pruned,
                                        count=int(((ce.raw_class == raw) & (ce.pruned_class == pruned)).sum())))
        for label in CLASSES:
            group = ce.loc[ce.pruned_class == label]
            r2_summary.append(dict(stratum=stratum, kind="pruned", **{
                "class": label, "r2_gt_0_9": int((group.r2 > 0.9).sum()), "total": len(group)}))
    for sid, group in cells.groupby("system_id", sort=True):
        for kind in KINDS:
            for level, labels in (("cell", group[f"{kind}_class"]),
                                  ("equation", equations.loc[(equations.system_id == sid) & (equations.kind == kind), "class"])):
                counts = Counter(labels)
                for label in CLASSES:
                    system_summary.append(dict(system_id=int(sid), system_dim=int(group.system_dim.iloc[0]),
                                               stratum=group.stratum.iloc[0], kind=kind, level=level,
                                               **{"class": label, "count": counts[label]}))
    return {"summary_equations_by_stratum.csv": pd.DataFrame(eq_summary),
            "summary_cells_by_stratum.csv": pd.DataFrame(cell_summary),
            "summary_by_system.csv": pd.DataFrame(system_summary),
            "transition_raw_to_pruned_cells.csv": pd.DataFrame(transitions),
            "r2_by_class_cells.csv": pd.DataFrame(r2_summary)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="Absolute path or path relative to --repo-root; existing files are never overwritten.")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    output = output.resolve()
    registry_path, support_path = repo / REGISTRY, repo / SUPPORT
    registry = pd.read_csv(registry_path)
    equations, cells = build_inventory(registry, json.loads(support_path.read_text(encoding="utf-8")))
    tables = {"equations.csv": equations, "cells.csv": cells, **summaries(equations, cells)}
    metadata = {
        "inputs": [{"path": str(p.relative_to(repo)).replace(chr(92), "/"),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                   for p in (registry_path, support_path)],
        "git_hash": git_head(repo), "git_hash_source": "read-only HEAD/ref files; no Git command",
        "class_definition": CLASS_DEFINITION,
        "row_counts": {"input_registry": len(registry), "exact_systems": cells.system_id.nunique(),
                       **{name: len(frame) for name, frame in tables.items()}},
        "controls": {"exact_rows": len(cells), "raw_exact_flag_agreements": len(cells),
                     "pruned_exact_flag_agreements": len(cells), "equation_counts_match": True},
        "equation_index_base": 1,
        "summary_layout": "Long format, zero counts included. Transition and r2 tables are stratified; sum strata for pooled counts.",
        "stratum_source": "CLAUDE.md Known Gaps, 2026-10-01 bound feasibility decision",
    }
    targets = [output / name for name in (*tables, "run_metadata.json")]
    existing = [str(p) for p in targets if p.exists()]
    if existing:
        raise FileExistsError("Refusing to overwrite existing artifacts: " + ", ".join(existing))
    output.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output / name, index=False, lineterminator="\n")
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata["row_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
