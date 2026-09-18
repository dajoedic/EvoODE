import json
from pathlib import Path

import numpy as np
import pandas as pd

from baselines import harness


CONFIG = harness.REPO_ROOT / "baselines" / "configs" / "wp_n19_smoke.json"


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_hash_mismatch_aborts_before_records(tmp_path: Path) -> None:
    try:
        harness.run(CONFIG, str(tmp_path / "out"), corrupt_manifest_hash=True)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("corrupt manifest hash should abort")


def test_method_failure_writes_error_record(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "out"), force_sindy_failure=True)
    records = read_jsonl(path)
    sindy_records = [record for record in records if record["method"] == "sindy"]
    assert sindy_records
    assert all(record["status"] == "error" for record in sindy_records)
    assert all(record["error_message"] for record in sindy_records)


def test_smoke_writes_sindy_and_odeformer_records(tmp_path: Path) -> None:
    path = harness.run(CONFIG, str(tmp_path / "out"))
    frame = pd.read_csv(path.parent / "records.csv")
    assert set(frame["method"]) == {"sindy", "odeformer"}
    assert len(frame) == 12
    assert {"reconstruction_r2_arithmetic_mean", "reconstruction_r2_variance_weighted"}.issubset(frame.columns)
    assert (path.parent / "trajectory_check.csv").is_file()


def test_r2_aggregations_are_distinct_on_multidimensional_case() -> None:
    reference = np.asarray([[0.0, 0.0], [1.0, 10.0], [2.0, 20.0], [3.0, 30.0]], dtype=float)
    prediction = np.asarray([[0.0, 0.0], [1.0, 15.0], [2.0, 25.0], [3.0, 35.0]], dtype=float)
    scores = harness.aggregate_r2(reference, prediction)
    assert scores["r2_arithmetic_mean"] != scores["r2_variance_weighted"]

