import sys
import subprocess
from pathlib import Path
from shutil import copyfile

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.evaluate_hypotheses import (  # noqa: E402
    campaign_message,
    classify_dataset,
    sha256_file,
    validate_inputs,
)
from utils.io import load_aggregate  # noqa: E402


def test_phase_a_data_uses_existing_validation_path() -> None:
    aggregate_path = ANALYSIS_ROOT / "data/paper1_phaseA_v1/aggregate_by_variant_system.csv"
    df = load_aggregate(aggregate_path)
    df["system_id"] = pd.to_numeric(df["system_id"], errors="raise").astype(int)

    dataset_kind, reasons = classify_dataset(df, "paper1_phaseA_v1", aggregate_path)

    assert dataset_kind == "phase_a"
    assert "all Phase A variants are present" in reasons
    assert validate_inputs(df) == []


def test_campaign_bridge_data_reports_non_applicable_phase_a_hypotheses() -> None:
    aggregate_path = ANALYSIS_ROOT / "data/wp_a1_campaign_bridge_probe/aggregate_by_variant_system.csv"
    df = load_aggregate(aggregate_path)
    df["system_id"] = pd.to_numeric(df["system_id"], errors="raise").astype(int)

    dataset_kind, reasons = classify_dataset(df, "wp_a2_campaign_bridge_probe", aggregate_path)
    message = campaign_message(df, "wp_a2_campaign_bridge_probe", aggregate_path, reasons)

    assert dataset_kind == "campaign"
    assert "H1-H4 are Phase A hypotheses" in message
    assert "does not define that comparison" in message
    assert "Missing expected variants" not in message


def test_phase_a_evaluation_does_not_overwrite_frozen_artifacts(tmp_path: Path) -> None:
    frozen_dir = tmp_path / "frozen"
    reproduction_dir = tmp_path / "reproduction"
    frozen_dir.mkdir()
    frozen_memo = frozen_dir / "paper1_freeze_memo_phaseA.md"
    frozen_diagnostics = frozen_dir / "h1_h4_diagnostics.json"
    copyfile(REPO_ROOT / "docs/paper1_freeze_memo_phaseA.md", frozen_memo)
    copyfile(
        ANALYSIS_ROOT / "data/paper1_phaseA_v1/h1_h4_diagnostics.json",
        frozen_diagnostics,
    )

    config = tmp_path / "paper1_phaseA_v1.json"
    config.write_text(
        "\n".join(
            [
                "{",
                '  "experiment_id": "paper1_phaseA_v1",',
                f'  "aggregate_path": "{(ANALYSIS_ROOT / "data/paper1_phaseA_v1/aggregate_by_variant_system.csv").as_posix()}",',
                f'  "diagnostics_path": "{frozen_diagnostics.as_posix()}",',
                f'  "freeze_memo_path": "{frozen_memo.as_posix()}",',
                f'  "generalization_summary_path": "{(REPO_ROOT / "debug_results/generalization_summary.csv").as_posix()}"',
                "}",
            ]
        ),
        encoding="utf-8",
    )
    memo_before = sha256_file(frozen_memo)
    diagnostics_before = sha256_file(frozen_diagnostics)

    result = subprocess.run(
        [
            sys.executable,
            str(ANALYSIS_ROOT / "scripts/aggregate/evaluate_hypotheses.py"),
            "--config",
            str(config),
            "--reproduction-dir",
            str(reproduction_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert sha256_file(frozen_memo) == memo_before
    assert sha256_file(frozen_diagnostics) == diagnostics_before
    assert (reproduction_dir / "paper1_freeze_memo_phaseA.md").exists()
    assert (reproduction_dir / "h1_h4_diagnostics.json").exists()
    assert "Frozen artifacts unchanged: yes" in result.stdout
    assert "Reproduction matches frozen diagnostics excluding generated_at: yes" in result.stdout
    assert "Reproduction matches frozen memo excluding Generated line: yes" in result.stdout
