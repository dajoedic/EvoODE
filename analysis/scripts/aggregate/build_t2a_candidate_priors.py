from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from exploratory.term_relevance import term_relevance as tr  # noqa: E402


STUDY_ID = "paper2_t2a_pilot_v1"
SOURCE_TAG = "wp_t1_term_relevance_weak_forward_clean_training_ic"
DEFAULT_RECORDS = REPO_ROOT / "analysis" / "data" / "wp_t1_term_relevance" / "records.csv"
DEFAULT_SUPPORT = REPO_ROOT / "studies" / "regression" / "phase_c_support.json"
DEFAULT_TRAJECTORY_MANIFEST = (
    REPO_ROOT
    / "outputs"
    / "phase_c_trajectory_hashes"
    / "wp_c4c"
    / "trajectory_export"
    / "trajectory_manifest.csv"
)
DEFAULT_OUTPUT = REPO_ROOT / "experiments" / STUDY_ID / "priors"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_json_field(row: dict[str, str], name: str) -> Any:
    try:
        return json.loads(row[name])
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {name} for row {row_id(row)}") from exc


def row_id(row: dict[str, str]) -> str:
    return (
        f"system={row['system_id']} ic={row['ic_strategy']} eq={row['equation_idx']} "
        f"signal={row['signal']} method={row['ranking_method']} sigma={row['sigma_rel']}"
    )


def load_phase_c_state_hashes(path: Path) -> dict[tuple[int, int], str]:
    if not path.exists():
        raise ValueError(f"missing Phase-C trajectory manifest: {path}")
    hashes: dict[tuple[int, int], str] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            hashes[(int(row["system_id"]), int(row["initial_condition_set"]))] = row["state_sha256"]
    return hashes


def load_rows(records_path: Path, trajectory_hashes: dict[tuple[int, int], str]) -> dict[tuple[int, int, int], dict[str, Any]]:
    selected: dict[tuple[int, int, int], dict[str, Any]] = {}
    with records_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["signal"] != "weak":
                continue
            if row["ranking_method"] != "forward":
                continue
            if float(row["sigma_rel"]) != 0.0:
                continue
            if row["basis_name"] != tr.BASIS_NAME:
                continue
            if row["ic_strategy"] not in {"ic1", "ic2"}:
                continue
            ic_set = 1 if row["ic_strategy"] == "ic1" else 2
            system_id = int(row["system_id"])
            expected_hash = trajectory_hashes.get((system_id, ic_set))
            if expected_hash is None:
                raise ValueError(f"missing Phase-C trajectory hash for system {system_id} ic{ic_set}")
            if row["trajectory_sha256"] != expected_hash:
                raise ValueError(
                    f"trajectory hash mismatch for {row_id(row)}: "
                    f"record={row['trajectory_sha256']} phase_c={expected_hash}"
                )
            equation_idx = int(row["equation_idx"])
            key = (system_id, ic_set, equation_idx)
            if key in selected:
                raise ValueError(f"duplicate selected ranking row for {key}")
            selected[key] = {
                "row_id": row_id(row),
                "candidate_names": parse_json_field(row, "candidate_names"),
                "candidate_ranks": [int(x) for x in parse_json_field(row, "candidate_ranks")],
                "trajectory_sha256": row["trajectory_sha256"],
            }
    return selected


def name_to_index(candidate_names: list[str], dim: int) -> dict[str, int]:
    expected = [term.name for term in tr.phasec_basis(dim)]
    if candidate_names != expected:
        missing = sorted(set(candidate_names).symmetric_difference(expected))
        raise ValueError(f"candidate name mapping mismatch for dim {dim}: {missing[:8]}")
    return {name: idx for idx, name in enumerate(expected, start=1)}


def guided_ranking(row: dict[str, Any], dim: int) -> list[int]:
    names = list(row["candidate_names"])
    mapping = name_to_index(names, dim)
    ranks = list(row["candidate_ranks"])
    if len(ranks) != len(names):
        raise ValueError(f"candidate_ranks length mismatch for {row['row_id']}")
    ordered_names = [name for _rank, name in sorted(zip(ranks, names), key=lambda item: (item[0], item[1]))]
    return [mapping[name] for name in ordered_names]


def oracle_ranking(guided: list[int], true_support: list[int]) -> list[int]:
    true = set(int(x) for x in true_support)
    true_first = [idx for idx in guided if idx in true]
    rest = [idx for idx in guided if idx not in true]
    if set(true_first) != true:
        raise ValueError(f"true support terms missing from guided ranking: {sorted(true - set(true_first))}")
    return true_first + rest


def prior_payload(
    arm: str,
    system: dict[str, Any],
    ic_set: int,
    rankings: list[list[int]],
    row_meta: list[dict[str, Any]],
    source_sha: str,
    records_path: Path,
    trajectory_manifest_path: Path,
) -> dict[str, Any]:
    return {
        "study_id": STUDY_ID,
        "arm": arm,
        "system_id": int(system["system_id"]),
        "dimension": int(system["dim"]),
        "initial_condition_set": ic_set,
        "basis_name": tr.BASIS_NAME,
        "epsilon": 0.2,
        "mapping": "harmonic",
        "rankings": rankings,
        "source_tag": SOURCE_TAG,
        "source_sha256": source_sha,
        "source_records_path": str(records_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "trajectory_manifest_path": str(trajectory_manifest_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "rows": row_meta,
    }


def build_priors(
    records_path: Path = DEFAULT_RECORDS,
    support_path: Path = DEFAULT_SUPPORT,
    trajectory_manifest_path: Path = DEFAULT_TRAJECTORY_MANIFEST,
) -> dict[tuple[str, int, int], dict[str, Any]]:
    source_sha = sha256(records_path)
    trajectory_hashes = load_phase_c_state_hashes(trajectory_manifest_path)
    rows = load_rows(records_path, trajectory_hashes)
    basis_name, systems = tr.load_exact_supports(support_path)
    if basis_name != tr.BASIS_NAME:
        raise ValueError(f"support basis mismatch: {basis_name} != {tr.BASIS_NAME}")

    priors: dict[tuple[str, int, int], dict[str, Any]] = {}
    systems = [system for system in systems if int(system["dim"]) <= 2]
    if len(systems) != 21:
        raise ValueError(f"expected 21 exact dim 1/2 systems, got {len(systems)}")
    for system in systems:
        system_id = int(system["system_id"])
        dim = int(system["dim"])
        support_idxs = [[int(x) for x in eq] for eq in system["support_idxs"]]
        for ic_set in (1, 2):
            guided_rankings: list[list[int]] = []
            oracle_rankings: list[list[int]] = []
            row_meta: list[dict[str, Any]] = []
            for eq_idx in range(1, dim + 1):
                key = (system_id, ic_set, eq_idx)
                if key not in rows:
                    raise ValueError(f"missing selected ranking row for {key}")
                guided = guided_ranking(rows[key], dim)
                oracle = oracle_ranking(guided, support_idxs[eq_idx - 1])
                guided_rankings.append(guided)
                oracle_rankings.append(oracle)
                row_meta.append(
                    {
                        "equation_idx": eq_idx,
                        "row_id": rows[key]["row_id"],
                        "trajectory_sha256": rows[key]["trajectory_sha256"],
                    }
                )
            priors[("guided_prior", system_id, ic_set)] = prior_payload(
                "guided_prior",
                system,
                ic_set,
                guided_rankings,
                row_meta,
                source_sha,
                records_path,
                trajectory_manifest_path,
            )
            priors[("oracle_prior", system_id, ic_set)] = prior_payload(
                "oracle_prior",
                system,
                ic_set,
                oracle_rankings,
                row_meta,
                source_sha,
                records_path,
                trajectory_manifest_path,
            )
    return priors


def write_priors(priors: dict[tuple[str, int, int], dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for (arm, system_id, ic_set), payload in sorted(priors.items()):
        path = output_dir / f"{arm}_system_{system_id:04d}_ic{ic_set}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Paper 2 T2a EvoGrow candidate-prior JSON files.")
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--trajectory-manifest", type=Path, default=DEFAULT_TRAJECTORY_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    priors = build_priors(args.records, args.support, args.trajectory_manifest)
    write_priors(priors, args.output_dir)
    print(f"priors={len(priors)}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()

