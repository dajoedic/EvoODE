import copy
import json
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import run_phasec_sindy_baseline as phasec_sindy  # noqa: E402


PILOT_DIR = REPO_ROOT / "outputs" / "phase_c_p9_pilot_records"
PILOT_SYSTEMS = [2, 24, 52, 63]


def read_pilot_records() -> list[dict[str, object]]:
    records = []
    for path in sorted(PILOT_DIR.glob("cell_*.jsonl")):
        if path.name.endswith(".heartbeat.jsonl"):
            continue
        line = path.read_text(encoding="utf-8").splitlines()[0]
        records.append(json.loads(line))
    assert len(records) == 16
    return records


def write_records(tmp_path: Path, records: list[dict[str, object]]) -> Path:
    records_dir = tmp_path / "records"
    records_dir.mkdir()
    for idx, record in enumerate(records, start=1):
        (records_dir / f"cell_{idx:06d}.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    return records_dir


def sindy_fixture(path: Path, systems: list[int] | None = None, invalid_control: bool = False) -> Path:
    systems = systems or PILOT_SYSTEMS
    rows = []
    for system_id in systems:
        dim = 1 if system_id == 2 else 2 if system_id == 24 else 3 if system_id == 52 else 4
        for source_ic, target_ic, direction in [(1, 2, "IC1_to_IC2"), (2, 1, "IC2_to_IC1")]:
            rows.append(
                {
                    "library_id": "poly_deg2_stlsq_0.01",
                    "polynomial_degree": 2,
                    "include_sin_cos": False,
                    "stlsq_threshold": 0.01,
                    "system_id": system_id,
                    "system_name": f"system {system_id}",
                    "dimension": dim,
                    "source_initial_condition_set": source_ic,
                    "target_initial_condition_set": target_ic,
                    "initial_condition_set": target_ic,
                    "direction": direction,
                    "regime": "generalization",
                    "fit_status": "success",
                    "integration_status": "success",
                    "diverged_or_nonfinite": False,
                    "r2": 0.95,
                    "r2_gt_0_9": True,
                    "sindy_structure_hit_raw": True,
                    "sindy_structure_hit_pruned": True,
                    "n_library_terms": 3,
                    "fit_elapsed_s_context": 0.01,
                    "elapsed_s_evidence_role": "context_not_evidence",
                    "n_target_regressions": dim,
                    "n_evaluation_integrations": 1,
                    "reconstruction_control_max_abs": 1.0 if invalid_control else 0.0,
                    "reconstruction_control_valid": not invalid_control,
                    "valid_for_analysis": not invalid_control,
                    "phasec_representability": "exact",
                    "phasec_representability_threeway": "exact",
                    "phasec_support_status": "ok",
                    "phasec_basis_name": "staged_polynomial_basis_with_constant",
                }
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    return path


def pair_args(tmp_path: Path, records_dir: Path, sindy_path: Path, **updates: object):
    class Args:
        sindy_details = str(sindy_path)
        evogrow_records_dir = str(records_dir)
        output = str(tmp_path / "paired.csv")
        expected_systems = ""
        expected_ic_sets = "1,2"
        expected_seeds = ""
        expected_git_hash = ""
        expected_config_fingerprint = ""
        expected_stage_cap_behavior_fingerprint = ""

    args = Args()
    for key, value in updates.items():
        setattr(args, key, value)
    return args


def test_pairing_runs_against_real_pilot_records_and_keeps_directions(tmp_path: Path) -> None:
    records_dir = write_records(tmp_path, read_pilot_records())
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")

    output = phasec_sindy.pair_sindy_evogrow(pair_args(tmp_path, records_dir, sindy_path))
    paired = pd.read_csv(output)

    assert len(paired) == 8
    assert set(paired["direction"]) == {"IC1_to_IC2", "IC2_to_IC1"}
    assert set(paired["evogrow_seed_policy"]) == {"mean_rate_over_available_phasec_seeds"}
    assert paired["git_hash"].nunique() == 1
    assert paired["config_fingerprint"].nunique() == 1
    assert paired["stage_cap_behavior_fingerprint"].nunique() == 1


def test_pairing_rejects_incomplete_evogrow_input(tmp_path: Path) -> None:
    records = read_pilot_records()
    records_dir = write_records(tmp_path, records[:-1])
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")

    try:
        phasec_sindy.pair_sindy_evogrow(
            pair_args(tmp_path, records_dir, sindy_path, expected_systems="2,24,52,63")
        )
    except ValueError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("incomplete EvoGrow input should fail")


def test_pairing_rejects_non_phasec_identity(tmp_path: Path) -> None:
    records = read_pilot_records()
    records[0] = copy.deepcopy(records[0])
    records[0]["basis_name"] = "staged_polynomial_basis"
    records_dir = write_records(tmp_path, records)
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")

    try:
        phasec_sindy.pair_sindy_evogrow(pair_args(tmp_path, records_dir, sindy_path))
    except ValueError as exc:
        assert "staged_polynomial_basis_with_constant" in str(exc)
    else:
        raise AssertionError("non-Phase-C identity should fail")


def test_pairing_excludes_nonzero_reconstruction_control_rows(tmp_path: Path) -> None:
    records_dir = write_records(tmp_path, read_pilot_records())
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")
    frame = pd.read_csv(sindy_path)
    frame.loc[0, "reconstruction_control_max_abs"] = 1.0
    frame.loc[0, "reconstruction_control_valid"] = False
    frame.loc[0, "valid_for_analysis"] = False
    frame.to_csv(sindy_path, index=False)

    output = phasec_sindy.pair_sindy_evogrow(pair_args(tmp_path, records_dir, sindy_path))
    paired = pd.read_csv(output)

    assert len(paired) == 7
    assert paired["reconstruction_control_valid"].all()


def test_summary_is_layered_by_dimension_and_phasec_representability(tmp_path: Path) -> None:
    details = pd.read_csv(sindy_fixture(tmp_path / "unused.csv"))
    summary = phasec_sindy.summarize(details)

    assert not summary.empty
    assert "dimension" in summary.columns
    assert "phasec_representability_threeway" in summary.columns
    assert set(summary["aggregation_scope"]) == {"dimension_by_phasec_representability_threeway"}
    assert "structure_hit_raw_count" in summary.columns
    assert "structure_hit_pruned_count" in summary.columns
    assert "r2_gt_0_9_count" in summary.columns
