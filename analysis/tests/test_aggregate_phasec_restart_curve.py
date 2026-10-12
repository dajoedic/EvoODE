import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_phasec_restart_curve import aggregate


def start(index: int, loss: float, r2: float, evals: int) -> dict:
    return {
        "start_index": index,
        "start_seed": 1000 + index,
        "loss": loss,
        "r2": r2,
        "fit_meta": {"loss_evals": evals},
    }


def restart_record(system_id: int, seed: int, ic: int, reference: list[dict], oracle: list[dict], original_loss: float = 1.0) -> dict:
    return {
        "cell_key": f"sys{system_id:04d}_seed{seed}_ic{ic}",
        "system_id": system_id,
        "system_name": f"system {system_id}",
        "initial_condition_set": ic,
        "seed": seed,
        "condition": "capped",
        "basis_name": "staged_polynomial_basis_with_constant",
        "support_status": "exact",
        "original_loss": original_loss,
        "reference_starts": reference,
        "oracle_starts": oracle,
        "error": None,
    }


def flat_starts(loss: float, r2: float, evals: int = 10) -> list[dict]:
    return [start(i, loss, r2, evals) for i in range(1, 11)]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_fixture(tmp_path: Path, rows: list[dict], c5_rows: list[dict] | None = None, duplicate_rows: list[dict] | None = None):
    starts_dir = tmp_path / "starts"
    c5_dir = tmp_path / "c5"
    write_jsonl(starts_dir / "shard_001_of_036" / "starts.jsonl", rows)
    c5_payload = c5_rows or [
        {
            "cell_key": row["cell_key"],
            "system_id": row["system_id"],
            "initial_condition_set": row["initial_condition_set"],
            "seed": row["seed"],
            "reference_loss": row["reference_starts"][0]["loss"],
            "reference_fit_meta": {"accepted_attempt": 1, "loss_evals": row["reference_starts"][0]["fit_meta"]["loss_evals"]},
            "error": None,
        }
        for row in rows
    ]
    write_jsonl(c5_dir / "shard_001_of_036" / "results.jsonl", c5_payload)
    support = tmp_path / "support.json"
    support.write_text(
        json.dumps(
            {
                "systems": [
                    {"system_id": 1, "dim": 1, "representability": "exact"},
                    {"system_id": 52, "dim": 3, "representability": "exact"},
                    {"system_id": 54, "dim": 3, "representability": "exact"},
                ]
            }
        ),
        encoding="utf-8",
    )
    registry = tmp_path / "registry.csv"
    with registry.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "variant_slug",
                "condition",
                "use_pretuning",
                "system_id",
                "system_representability",
                "seed",
                "initial_condition_set",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "variant_slug": "evogrow_v2_2_stage_capped",
                    "condition": "capped",
                    "use_pretuning": "False",
                    "system_id": row["system_id"],
                    "system_representability": "exact",
                    "seed": row["seed"],
                    "initial_condition_set": row["initial_condition_set"],
                }
            )
    duplicate = tmp_path / "duplicates.jsonl"
    write_jsonl(
        duplicate,
        duplicate_rows
        or [
            {
                "variant": "evogrow_v2_2_stage_capped",
                "condition": "capped",
                "use_pretuning": False,
                "system_id": row["system_id"],
                "structure_repeat_quantiles": {"q50": 2, "q90": 4},
            }
            for row in rows
        ],
    )
    cold = tmp_path / "cold.csv"
    with cold.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dimension", "system_id", "initial_condition_set", "n_starts", "n_loss_lt_1e_8", "n_loss_1e_8_to_1e_3", "n_loss_ge_1e_3", "n_sentinel"],
        )
        writer.writeheader()
        writer.writerow({"dimension": 1, "system_id": 1, "initial_condition_set": 1, "n_starts": 10, "n_loss_lt_1e_8": 4, "n_loss_1e_8_to_1e_3": 0, "n_loss_ge_1e_3": 6, "n_sentinel": 0})
    return argparse.Namespace(
        input_dir=starts_dir,
        output_dir=tmp_path / "out",
        c5_oracle_dir=c5_dir,
        registry=registry,
        support=support,
        duplicate_source=duplicate,
        cold_starts=cold,
        allow_incomplete=False,
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_nested_best_of_k_cumulative_cost_thresholds_and_strata(tmp_path: Path) -> None:
    rows = [
        restart_record(
            1,
            42,
            1,
            [
                start(1, 1e-7, 0.1, 10),
                start(2, 1e-9, 0.95, 20),
                start(3, 1e-6, 0.2, 30),
                start(4, 1e-5, 0.3, 40),
                start(5, 1e6, 0.0, 50),
                start(6, 1e-4, 0.4, 60),
                start(7, 1e-3, 0.5, 70),
                start(8, 1e-2, 0.6, 80),
                start(9, 1e-1, 0.7, 90),
                start(10, 1e-13, 0.99, 100),
            ],
            flat_starts(0.5, 0.0, 1),
        ),
        restart_record(
            52,
            42,
            1,
            flat_starts(0.2, 0.2, 10),
            flat_starts(0.3, 0.3, 10),
        ),
        restart_record(
            54,
            42,
            1,
            flat_starts(0.4, 0.4, 10),
            flat_starts(0.5, 0.5, 10),
        ),
    ]
    args = write_fixture(tmp_path, rows)

    aggregate(args)

    curve = read_rows(args.output_dir / "restart_curve.csv")
    feasible_k3 = next(row for row in curve if row["k"] == "3" and row["structure"] == "reference" and row["stratum"] == "all_feasible")
    assert feasible_k3["n_cells"] == "2"
    assert feasible_k3["loss_evals_sum"] == "90"
    assert feasible_k3["r2_gt_0_9_count"] == "1"
    assert feasible_k3["loss_lt_1e-08_count"] == "1"
    assert feasible_k3["loss_lt_1e-10_count"] == "0"

    dim3_special = next(row for row in curve if row["k"] == "10" and row["structure"] == "reference" and row["stratum"] == "dim3_systems_52_57")
    dim3_other = next(row for row in curve if row["k"] == "10" and row["structure"] == "reference" and row["stratum"] == "dim3_other_systems")
    assert dim3_special["n_cells"] == "1"
    assert dim3_other["n_cells"] == "1"

    first_hit = read_rows(args.output_dir / "reference_first_hit_by_cell.csv")
    assert next(row for row in first_hit if row["system_id"] == "1")["first_reference_r2_gt_0_9_k"] == "2"
    assert next(row for row in first_hit if row["system_id"] == "52")["first_reference_r2_gt_0_9_k"] == "not within 10"


def test_incomplete_set_refusal(tmp_path: Path) -> None:
    row = restart_record(1, 42, 1, flat_starts(1.0, 0.0, 1), flat_starts(1.0, 0.0, 1))
    args = write_fixture(tmp_path, [row])
    with args.registry.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["evogrow_v2_2_stage_capped", "capped", "False", 52, "exact", 42, 1])

    result = subprocess.run(
        [
            sys.executable,
            "analysis/scripts/aggregate/aggregate_phasec_restart_curve.py",
            "--input-dir",
            str(args.input_dir),
            "--output-dir",
            str(args.output_dir),
            "--c5-oracle-dir",
            str(args.c5_oracle_dir),
            "--registry",
            str(args.registry),
            "--support",
            str(args.support),
            "--duplicate-source",
            str(args.duplicate_source),
            "--cold-starts",
            str(args.cold_starts),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "incomplete" in result.stderr


def test_control_pass_failure_and_not_comparable(tmp_path: Path) -> None:
    row = restart_record(1, 42, 1, flat_starts(1.0, 0.0, 1), flat_starts(1.0, 0.0, 1))
    args = write_fixture(tmp_path / "pass", [row])
    aggregate(args)
    assert read_rows(args.output_dir / "control_reference_start1_vs_c5.csv")[0]["passed"] == "True"

    fail_args = write_fixture(
        tmp_path / "fail",
        [row],
        c5_rows=[{"cell_key": row["cell_key"], "system_id": 1, "initial_condition_set": 1, "seed": 42, "reference_loss": 2.0, "reference_fit_meta": {"accepted_attempt": 1}}],
    )
    result = subprocess.run(
        [
            sys.executable,
            "analysis/scripts/aggregate/aggregate_phasec_restart_curve.py",
            "--input-dir",
            str(fail_args.input_dir),
            "--output-dir",
            str(fail_args.output_dir),
            "--c5-oracle-dir",
            str(fail_args.c5_oracle_dir),
            "--registry",
            str(fail_args.registry),
            "--support",
            str(fail_args.support),
            "--duplicate-source",
            str(fail_args.duplicate_source),
            "--cold-starts",
            str(fail_args.cold_starts),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "C-5 control failed" in result.stderr

    nc_args = write_fixture(
        tmp_path / "not_comparable",
        [row],
        c5_rows=[{"cell_key": row["cell_key"], "system_id": 1, "initial_condition_set": 1, "seed": 42, "reference_loss": 99.0, "reference_fit_meta": {"accepted_attempt": 2}}],
    )
    aggregate(nc_args)
    control = read_rows(nc_args.output_dir / "control_reference_start1_vs_c5.csv")
    assert control[0]["comparable"] == "False"
    assert control[0]["note"] == "not comparable: C-5 accepted a later attempt"
