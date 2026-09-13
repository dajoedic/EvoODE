import csv
import json
import sys
from pathlib import Path

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_wp_n1_dim2_probe import (  # noqa: E402
    EXPECTED_RECORDS,
    VARIANT_CONSTANT,
    VARIANT_OLD,
    main,
)


BOTH_EXACT = {24, 25, 26, 27, 28, 29, 31, 32, 38}
CONSTANT_ONLY = {43}
SYSTEMS = list(range(24, 52))
SEEDS = [7, 42, 123]
ICS = ["ic_a", "ic_b"]


def base_record(system_id: int, seed: int, ic_set: str, variant: str, manifest_index: int) -> dict:
    exact_systems = BOTH_EXACT | (CONSTANT_ONLY if variant == VARIANT_CONSTANT else set())
    representability = "exact" if system_id in exact_systems else "surrogate"
    support_terms = [["u1"], ["u2"]]
    pruned_match = True
    if system_id == 24 and seed == 7 and ic_set == "ic_a" and variant == VARIANT_OLD:
        support_terms = [["u1", "u1^2"], ["u2"]]
        pruned_match = True
    if system_id == 25 and seed == 7 and ic_set == "ic_a" and variant == VARIANT_OLD:
        pruned_match = False
    return {
        "system_id": system_id,
        "system_name": f"system_{system_id}",
        "seed": seed,
        "initial_condition_set": ic_set,
        "variant": variant,
        "basis_name": variant,
        "representability": representability,
        "support_terms": support_terms,
        "wp_n1_expected_support_terms": [["u1"], ["u2"]]
        if representability == "exact"
        else None,
        "wp_n1_support_status": "fixture",
        "pruned_match": pruned_match,
        "r2": 0.95 if system_id % 2 == 0 else 0.75,
        "loss": 0.01,
        "final_stage": 2,
        "eq_final_stages": [2, 2],
        "model_terms": [],
        "total_parameter_fits": manifest_index * 10,
        "total_loss_evals": manifest_index * 20,
        "total_ode_solves": manifest_index * 30,
        "error": "",
        "git_hash": "ec3b6bd",
        "config_fingerprint": "cfg",
        "stage_cap_behavior_fingerprint": "stage",
        "manifest_index": manifest_index,
        "elapsed_s": float(manifest_index),
    }


def all_records() -> list[dict]:
    records = []
    manifest_index = 1
    for variant in [VARIANT_OLD, VARIANT_CONSTANT]:
        for system_id in SYSTEMS:
            for seed in SEEDS:
                for ic_set in ICS:
                    records.append(base_record(system_id, seed, ic_set, variant, manifest_index))
                    manifest_index += 1
    assert manifest_index == EXPECTED_RECORDS + 1
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def write_cell_files(path: Path, records: list[dict]) -> None:
    path.mkdir()
    for record in records:
        cell_path = path / f"cell_{record['manifest_index']:06d}.jsonl"
        write_jsonl(cell_path, [record])
    write_jsonl(path / "cell_000001.heartbeat.jsonl", [{"manifest_index": 1, "error": "ignore me"}])


def write_classification(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["system_id", "dim", "description"])
        writer.writeheader()
        for system_id in SYSTEMS:
            writer.writerow({"system_id": system_id, "dim": 2, "description": f"system {system_id}"})


def run_main(tmp_path: Path, records: list[dict], extra_args: list[str] | None = None) -> int:
    input_path = tmp_path / "records.jsonl"
    classification_path = tmp_path / "classification.csv"
    output_dir = tmp_path / "out"
    write_jsonl(input_path, records)
    write_classification(classification_path)
    args = [
        "--input",
        str(input_path),
        "--classification",
        str(classification_path),
        "--output-dir",
        str(output_dir),
    ]
    if extra_args:
        args.extend(extra_args)
    return main(args)


def test_output_directory_outside_repo_success_path_runs_through(tmp_path: Path) -> None:
    records = all_records()
    input_path = tmp_path / "records.jsonl"
    classification_path = tmp_path / "classification.csv"
    output_dir = tmp_path / "external-output"
    write_jsonl(input_path, records)
    write_classification(classification_path)

    result = main(
        [
            "--input",
            str(input_path),
            "--classification",
            str(classification_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert result == 0
    assert (output_dir / "wp_n1_dim2_probe_cells.csv").exists()
    assert (output_dir / "wp_n1_dim2_probe_decision_table.csv").exists()


def test_surrogate_without_expected_support_terms_is_not_applicable(tmp_path: Path) -> None:
    assert run_main(tmp_path, all_records()) == 0
    cells = pd.read_csv(tmp_path / "out" / "wp_n1_dim2_probe_cells.csv")
    decisions = pd.read_csv(tmp_path / "out" / "wp_n1_dim2_probe_decision_table.csv")

    surrogate_cells = cells[cells["representability"] == "surrogate"]
    surrogate_summary = decisions[
        (decisions["row_type"] == "literature_r2_summary")
        & (decisions["representability"] == "surrogate")
    ]

    assert not surrogate_cells.empty
    assert surrogate_cells["raw_support_match"].isna().all()
    assert surrogate_cells["pruned_support_match"].isna().all()
    assert surrogate_summary["raw_support_denominator"].eq(0).all()
    assert surrogate_summary["pruned_support_denominator"].eq(0).all()
    assert surrogate_summary["raw_support_rate"].isna().all()
    assert surrogate_summary["pruned_support_rate"].isna().all()


def test_exact_without_expected_support_terms_returns_nonzero(tmp_path: Path) -> None:
    records = all_records()
    exact_index = next(
        index for index, record in enumerate(records) if record["representability"] == "exact"
    )
    records[exact_index]["wp_n1_expected_support_terms"] = None

    assert run_main(tmp_path, records) == 1


def test_layer_logic_keeps_constant_only_system_out_of_layer_a(tmp_path: Path) -> None:
    assert run_main(tmp_path, all_records()) == 0
    cells = pd.read_csv(tmp_path / "out" / "wp_n1_dim2_probe_cells.csv")
    layer_a = cells[cells["decision_layer"] == "A_paired_both_exact"]

    assert set(layer_a["system_id"]) == BOTH_EXACT
    assert len(layer_a[layer_a["variant"] == VARIANT_OLD]) == 54
    assert len(layer_a[layer_a["variant"] == VARIANT_CONSTANT]) == 54
    assert cells[(cells["system_id"] == 43) & (cells["variant"] == VARIANT_OLD)]["decision_layer"].eq(
        "C_literature_all_cells"
    ).all()
    assert cells[(cells["system_id"] == 43) & (cells["variant"] == VARIANT_CONSTANT)][
        "decision_layer"
    ].eq("B_constant_only_exact").all()


def test_raw_and_pruned_matches_are_separate_and_containment_is_counted(tmp_path: Path) -> None:
    assert run_main(tmp_path, all_records()) == 0
    cells = pd.read_csv(tmp_path / "out" / "wp_n1_dim2_probe_cells.csv")
    decisions = pd.read_csv(tmp_path / "out" / "wp_n1_dim2_probe_decision_table.csv")

    differing = cells[
        (cells["manifest_index"] == 1)
        & (cells["raw_support_match"].eq(False))
        & (cells["pruned_support_match"].eq(True))
    ]
    violating = cells[
        (cells["system_id"] == 25)
        & (cells["seed"] == 7)
        & (cells["initial_condition_set"] == "ic_a")
        & (cells["variant"] == VARIANT_OLD)
        & (cells["raw_implies_pruned_violation"])
    ]
    assert len(differing) == 1
    assert len(violating) == 1
    assert decisions["raw_implies_pruned_violations_total"].max() == 1
    assert "support_match" not in cells.columns


def test_heartbeat_files_are_not_read(tmp_path: Path) -> None:
    input_dir = tmp_path / "cells"
    classification_path = tmp_path / "classification.csv"
    output_dir = tmp_path / "out"
    write_cell_files(input_dir, all_records())
    write_classification(classification_path)

    result = main(
        [
            "--input",
            str(input_dir),
            "--classification",
            str(classification_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert result == 0
    cells = pd.read_csv(output_dir / "wp_n1_dim2_probe_cells.csv")
    assert len(cells) == EXPECTED_RECORDS


def test_missing_records_fail_without_flag_by_exit_code(tmp_path: Path) -> None:
    records = [record for record in all_records() if record["manifest_index"] != 293]

    assert run_main(tmp_path, records) == 1


def test_allowed_incomplete_run_writes_missing_index_to_outputs(tmp_path: Path) -> None:
    records = [record for record in all_records() if record["manifest_index"] != 293]

    assert run_main(tmp_path, records, ["--allow-incomplete"]) == 0
    cells = pd.read_csv(tmp_path / "out" / "wp_n1_dim2_probe_cells.csv")
    decisions = pd.read_csv(tmp_path / "out" / "wp_n1_dim2_probe_decision_table.csv")

    assert cells["missing_manifest_indices"].astype(str).eq("293").all()
    assert decisions["missing_manifest_indices"].astype(str).eq("293").all()
    assert cells["observed_manifest_records"].eq(335).all()


def test_identity_and_error_abort_paths_return_nonzero(tmp_path: Path) -> None:
    mutators = [
        lambda records: records[0].update({"config_fingerprint": "other"}),
        lambda records: records[0].update({"error": "failed"}),
        lambda records: records[0].update({"git_hash": "not_collected"}),
        lambda records: records.append({**records[0], "manifest_index": 999}),
    ]
    for index, mutate in enumerate(mutators):
        case_dir = tmp_path / f"case_{index}"
        case_dir.mkdir()
        records = all_records()
        mutate(records)

        assert run_main(case_dir, records) == 1
