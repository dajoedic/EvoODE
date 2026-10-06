import json

from experiments.annihilator_odebench_smoke.catalog import load_systems
from experiments.annihilator_odebench_smoke.run import run_command, setup_command


def test_record_fields_come_from_real_run_path(tmp_path):
    results = tmp_path / "results"
    setup_command(results)
    written = run_command(results, [3], [0.0], [0], ["sindy"], workers=1)
    assert written == 1
    record = json.loads((results / "records.jsonl").read_text().splitlines()[0])
    assert record["method"] == "sindy"
    assert record["pysindy_parameters"]["pysindy_version"] == "2.1.0"
    assert record["selected_terms"]
    assert {"term", "coefficient"} <= set(record["selected_terms"][0])
    assert "train_nrmse_x" in record
    assert "test_r2" in record


def test_baseline_noise_stream_differs_between_training_trajectories():
    system = load_systems()[3]
    from experiments.annihilator_odebench_smoke.run import _rng

    rng = _rng(60000, system.system_id, "sindy")
    noise_a = rng.standard_normal(system.x_train[0].size)
    noise_b = rng.standard_normal(system.x_train[1].size)
    assert not (noise_a == noise_b).all()
