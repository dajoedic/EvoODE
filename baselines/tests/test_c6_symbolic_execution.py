"""Platform-only tests using records derived from the actual N38/N39 outputs."""
from __future__ import annotations

import copy
import json
import random
import shutil
import sys
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "analysis"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from baselines import harness, run_odeformer_noise as ode, run_pysr_noise as pysr
from baselines.c6_shards import assign_shards, context_id, expected_units, smoke_index, CONFIGS
from baselines.noise_execution import UnitJournal, cell_key, unit_key, load_unit, encoded, digest, atomic_write
from scripts.aggregate.aggregate_c6_symbolic_baselines import aggregate
from scripts.aggregate.compare_c6_symbolic_smoke import compare_records, compare_control
from scripts.aggregate import run_k8s_symbolic_shard as entry

FIXTURES = Path(__file__).parent / "fixtures/wp_n48"
SHA = "a" * 40
IMAGE = "registry/test:" + SHA
REAL_INDEX = ROOT / "outputs/phase_c_c6_data_conditions_5dd1df8/index.csv"


def fixture(name):
    return json.loads((FIXTURES / (name + ".json")).read_text())["records"]


def export_fixture(tmp_path, condition=(0.01, 0.0)):
    # Derive the field inventory and all trajectory bytes from an actual export.
    real = pd.read_csv(REAL_INDEX)
    row = real[(real.system_id == 1) & (real.initial_condition_set == 1) &
               (real.noise_sigma == condition[0]) & (real.subsample_rho == condition[1]) &
               (real.noise_realization == 1)].copy()
    assert len(row) == 1
    export = tmp_path / "export"
    for _, r in row.iterrows():
        source = REAL_INDEX.parent / str(r.cell_dir).replace("\\", "/")
        target = export / str(r.cell_dir).replace("\\", "/")
        for col in ("time_path", "state_path"):
            rel = str(r[col]).replace("\\", "/")
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / rel, target / rel)
    row.to_csv(export / "index.csv", index=False)
    return export / "index.csv", row.iloc[0]


@pytest.mark.parametrize("n_shards", [1, 7, 1512, 4536])
def test_full_index_assignment(n_shards):
    frame = pd.read_csv(REAL_INDEX)
    assigned = assign_shards(frame, n_shards)
    again = assign_shards(frame.sample(frac=1, random_state=45), n_shards)
    pd.testing.assert_frame_equal(assigned, again)
    assert len(assigned) == 4536
    assert assigned.shard_index.nunique() == n_shards
    assert len({cell_key(row) for _, row in assigned.iterrows()}) == 4536
    assert assigned[assigned.dimension <= 2].shard_index.max() <= assigned[assigned.dimension > 2].shard_index.min()
    if n_shards == 1512:
        assert assigned.groupby("shard_index").size().eq(3).all()
        assert assigned[assigned.dimension <= 2].shard_index.max() == 1223
        assert assigned[assigned.dimension > 2].shard_index.min() == 1224


@pytest.mark.parametrize("method", ["odeformer", "pysr"])
def test_runner_resume_and_hash_failure(tmp_path, monkeypatch, method):
    index, row = export_fixture(tmp_path)
    module = ode if method == "odeformer" else pysr
    records = fixture("odeformer_clean" if method == "odeformer" else "pysr")
    monkeypatch.setattr(module, "integrate_truth", lambda system, ic, t: (np.zeros((len(t), int(system["dim"]))), None))
    class Adapter:
        actual_hash = "fake"
        def close(self): pass
        def timeout_phase(self, name): return nullcontext()
        def integrate_expression(self, cell, expression):
            return cell.state.copy() if method == "odeformer" else (cell.state.copy(), "success")
    calls = []
    interrupt = [True]
    def fit(system, source, target, config, adapter):
        calls.append(config["config_id"])
        if len(calls) == 2 and interrupt[0]:
            raise KeyboardInterrupt("Simulated pod eviction")
        record = copy.deepcopy(records[0 if config["config_id"] != "pysr_poly" else 1])
        record["method_config"] = json.dumps(config, sort_keys=True)
        return record
    monkeypatch.setattr(harness, "build_" + method + "_adapter", lambda config: Adapter())
    monkeypatch.setattr(harness, "run_" + method + "_record_with_adapter", fit)
    journal = UnitJournal(tmp_path / "out", "context", SHA, IMAGE)
    def run():
        if method == "odeformer":
            return ode.run_noise_odeformer(CONFIGS[method], [index], tmp_path / "out", repetitions=2,
                                           config_ids={"beam10_noopt"}, execution=journal)
        return pysr.run_noise_pysr(CONFIGS[method], [index], tmp_path / "out", seeds=[1], execution=journal)
    with pytest.raises(KeyboardInterrupt):
        run()
    files = list((tmp_path / "out/units").glob("*.json"))
    assert len(files) == 1
    original = files[0].read_bytes()
    interrupt[0] = False
    paths = run()
    assert len(calls) == 3  # one completed, one interrupted, one resumed; completed unit never refit
    assert files[0].read_bytes() == original
    assert len(pd.read_csv(paths["details"])) == 2
    run()
    assert len(calls) == 3
    assert all(load_unit(p)["record"]["git_hash"] == SHA for p in (tmp_path / "out/units").glob("*.json"))
    # Corrupt trajectory bytes: every requested unit becomes a recorded hash failure, no fit runs.
    row_path = index.parent / str(row.cell_dir).replace("\\", "/") / str(row.state_path).replace("\\", "/")
    row_path.write_bytes(b"broken")
    journal = UnitJournal(tmp_path / "hash_out", "context", SHA, IMAGE)
    if method == "odeformer":
        result = ode.run_noise_odeformer(CONFIGS[method], [index], tmp_path / "hash_out", repetitions=1,
                                        config_ids={"beam10_noopt"}, execution=journal)
    else:
        result = pysr.run_noise_pysr(CONFIGS[method], [index], tmp_path / "hash_out", seeds=[1], execution=journal)
    errors = [json.loads(line) for line in result["records"].read_text().splitlines()]
    assert len(errors) == (1 if method == "odeformer" else 2)
    assert all(r["status"] == "error" and r["export_validation_error"] for r in errors)
    assert not pd.read_csv(result["export_checks"]).hash_verified.any()
    assert len(calls) == 3


def test_journal_partial_and_context(tmp_path):
    record = fixture("odeformer_clean")[0]
    # C-6 clean realization is 1; N38's separate clean control used label 0.
    record["noise_realization"] = 1
    row = dict(system_id=1, initial_condition_set=1, noise_sigma=0.0, subsample_rho=0.0, noise_realization=1,
               time_sha256=record["time_sha256"], state_sha256=record["fit_state_sha256"])
    journal = UnitJournal(tmp_path, "context", SHA, IMAGE)
    path = journal.path(row, "beam10_noopt", 1)
    path.parent.mkdir(parents=True)
    path.with_suffix(".json.tmp").write_text('{"body":')
    assert journal.restore(row, "beam10_noopt", 1) is None
    path.write_text('{"body":')
    assert journal.restore(row, "beam10_noopt", 1) is None
    assert path.with_suffix(".invalid").exists()
    journal.save(row, "beam10_noopt", 1, record, row)
    assert journal.restore(row, "beam10_noopt", 1)["status"] == "success"
    with pytest.raises(ValueError, match="context changed"):
        UnitJournal(tmp_path, "different", SHA, IMAGE).restore(row, "beam10_noopt", 1)
    changed = dict(record, status="error")
    with pytest.raises(ValueError, match="overwrite complete unit"):
        journal.save(row, "beam10_noopt", 1, changed, row)
    # Restart after adapter construction must continue the exact Python/NumPy sampling stream.
    journal.restore(row, "beam10_noopt", 1)
    body = load_unit(path)
    from baselines.noise_execution import restore_rng
    restore_rng(body["rng_state"])
    expected = (random.random(), float(np.random.random()))
    random.seed(90)
    np.random.seed(90)
    journal.before_fit("beam10_noopt")
    assert (random.random(), float(np.random.random())) == expected


def make_shard(tmp_path, method):
    index, row = export_fixture(tmp_path, (0.0, 0.0) if method == "odeformer" else (0.01, 0.0))
    frame = pd.read_csv(index)
    context = context_id(frame, method, 1, SHA, IMAGE, smoke=True)
    shard = tmp_path / "input/shard_0"
    shard.mkdir(parents=True)
    (shard / "plan.json").write_text(json.dumps(dict(context=context, method=method, n_shards=1, shard_index=0,
                                                    smoke=True, git_commit=SHA, image_id=IMAGE)))
    journal = UnitJournal(shard, context, SHA, IMAGE)
    check = dict(export_index=str(index), **{name: row[name].item() if hasattr(row[name], "item") else row[name]
                  for name in ["system_id", "initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization",
                               "time_sha256", "state_sha256", "n_observed_points"]}, hash_verified=True)
    records = fixture("odeformer_clean" if method == "odeformer" else "pysr")
    for record in records:
        record["noise_realization"] = 1
        key = unit_key(record)
        journal.save(row, key[-2], key[-1], record, check)
    return index, shard


@pytest.mark.parametrize("method", ["odeformer", "pysr"])
def test_merge_complete_missing_duplicates_and_overwrite(tmp_path, monkeypatch, method):
    index, shard = make_shard(tmp_path, method)
    # Restrict the test export to one real cell; production smoke_index still requires both ODE controls.
    import scripts.aggregate.aggregate_c6_symbolic_baselines as merger
    monkeypatch.setattr(merger, "smoke_index", lambda frame, method: frame)
    kwargs = dict(input_dir=shard.parent, export_index=index, method=method, git_commit=SHA, image_id=IMAGE,
                  n_shards=1, smoke=True)
    result = aggregate(output_dir=tmp_path / "merged", **kwargs)
    assert result["missing"] == 0
    assert set(p.name for p in (tmp_path / "merged").iterdir()) == {
        "details.csv", "records.jsonl", "summary.csv", "export_checks.csv", "merge_audit.json"}
    with pytest.raises(FileExistsError):
        aggregate(output_dir=tmp_path / "merged", **kwargs)
    duplicate = shard.parent / "shard_0_copy"
    shutil.copytree(shard, duplicate)
    assert aggregate(output_dir=tmp_path / "identical", **kwargs)["missing"] == 0
    path = next((duplicate / "units").glob("*.json"))
    payload = json.loads(path.read_text())
    payload["body"]["record"]["reconstruction_r2_arithmetic_mean"] += 0.001
    payload["sha256"] = digest(payload["body"])
    path.write_bytes(encoded(payload))
    with pytest.raises(ValueError, match="Non-identical duplicate"):
        aggregate(output_dir=tmp_path / "bad_duplicate", **kwargs)
    shutil.rmtree(duplicate)
    if method == "pysr":
        next((shard / "units").glob("*.json")).unlink()
        with pytest.raises(ValueError, match="Missing 1"):
            aggregate(output_dir=tmp_path / "missing", **kwargs)
        assert aggregate(output_dir=tmp_path / "partial", allow_incomplete=True, **kwargs)["missing"] == 1
    else:
        next((shard / "units").glob("*.json")).unlink()
        with pytest.raises(ValueError, match="Missing 1"):
            aggregate(output_dir=tmp_path / "missing", **kwargs)
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("name,control,method", [("odeformer_clean", "odeformer-clean", "odeformer"),
                                                ("odeformer_stage", "odeformer-stage", "odeformer"),
                                                ("pysr", "pysr", "pysr")])
def test_smoke_pass_and_manipulated_fail(name, control, method):
    references = fixture(name)
    candidates = copy.deepcopy(references)
    for r in candidates:
        r["noise_realization"] = 1
    assert all(r["result"] == "PASS" for r in compare_control(references, candidates, control))
    assert all(r["result"] == "FAIL" for r in compare_control(references, [], control))
    for r in candidates:
        r["odeformer_model_canonical" if method == "odeformer" else "pysr_model_canonical"] = "0.123*x_0"
    assert all(r["result"] == "FAIL" for r in compare_control(references, candidates, control))
    changed = dict(references[0], fit_state_sha256="wrong")
    assert compare_records(references[0], changed, method)["result"] == "FAIL"
    if method == "odeformer":
        changed = dict(references[0], reconstruction_r2_arithmetic_mean=0.0)
    else:
        changed = dict(references[0], pysr_model_canonical="-0.29928026*x_0")
    assert compare_records(references[0], changed, method)["result"] == "FAIL"


def test_manifest_and_ci_contracts():
    for method in ["odeformer", "pysr"]:
        for smoke in [False, True]:
            path = ROOT / f"k8s/phase_c_c6_{method}{'_smoke' if smoke else ''}_job.yaml"
            job = yaml.safe_load(path.read_text())
            spec = job["spec"]
            assert spec["completionMode"] == "Indexed"
            assert spec["parallelism"] <= 8 and spec["ttlSecondsAfterFinished"] == 3600
            assert spec["backoffLimit"] == 50
            assert "activeDeadlineSeconds" not in path.read_text()
            container = spec["template"]["spec"]["containers"][0]
            assert container["resources"]["requests"]["cpu"] == container["resources"]["limits"]["cpu"] == "1"
            env = {r["name"]: r["value"] for r in container["env"]}
            for name in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "ODEFORMER_TORCH_THREADS", "JULIA_NUM_THREADS"]:
                assert env[name] == "1"
            assert int(env["EVO_SYMBOLIC_N_SHARDS"]) == spec["completions"]
            assert env["EVOODE_IMAGE_ID"] == container["image"]
            assert any(m["mountPath"] == "/export" and m["readOnly"] for m in container["volumeMounts"])
            assert env["EVO_SYMBOLIC_OUTPUT_DIR"].endswith('/smoke') == smoke
    ci = yaml.safe_load((ROOT / ".gitlab-ci.yml").read_text())
    reference, legacy = ci["build_odeformer_reference_image"], ci["build_pysr_legacy_image"]
    for name in ["services", "rules", "variables", "timeout", "before_script"]:
        assert legacy[name] == reference[name]
    assert 'Dockerfile.pysr-legacy' in legacy['script'][0]
    assert '--provenance=false --sbom=false' in legacy['script'][0]
    assert ci['trivy-pysr-legacy-image']['rules'] == ci['trivy-odeformer-reference-image']['rules']
    assert ci['trivy-pysr-legacy-image']['needs'][0]['job'] == 'build_pysr_legacy_image'
    assert 'build_pysr_legacy_image' in (ROOT / 'CHANGELOG.md').read_text()
    assert 'trivy-pysr-legacy-image' in (ROOT / 'CHANGELOG.md').read_text()


def test_smoke_selection_and_entry_point(tmp_path, monkeypatch):
    frame = pd.read_csv(REAL_INDEX)
    assert len(smoke_index(frame, 'odeformer')) == 2
    assert len(smoke_index(frame, 'pysr')) == 1
    export = REAL_INDEX.parent
    output = tmp_path / 'smoke'
    env = dict(EVO_SYMBOLIC_METHOD='odeformer', JOB_COMPLETION_INDEX='1', EVO_SYMBOLIC_N_SHARDS='2',
               EVO_SYMBOLIC_SMOKE='1', EVOODE_GIT_SHA=SHA, EVOODE_IMAGE_ID=IMAGE,
               EVO_SYMBOLIC_EXPORT_DIR=str(export), EVO_SYMBOLIC_OUTPUT_DIR=str(output))
    for key, value in env.items(): monkeypatch.setenv(key, value)
    captured = {}
    def fake(config, indexes, destination, **kwargs):
        captured.update(kwargs)
        index = ode.read_export_index(indexes[0])
        assert len(index) == 1 and index.iloc[0].noise_sigma == 0.05
        ode.read_index_cell(indexes[0].parent, index.iloc[0])  # absolute paths still pass the original hash validator
        return {}
    monkeypatch.setattr(ode, 'run_noise_odeformer', fake)
    assert entry.main() == 0
    assert captured['config_ids'] == {'beam10_noopt'} and captured['repetitions'] == 1
    assert sorted(p.name for p in output.iterdir()) == ['shard_1']


def test_atomic_publication_never_clobbers(tmp_path):
    path = tmp_path / "unit.json"
    atomic_write(path, b"complete", replace=False)
    with pytest.raises(FileExistsError):
        atomic_write(path, b"different", replace=False)
    assert path.read_bytes() == b"complete"
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("interrupt_at", [2, 6])
def test_resume_preserves_rng_with_multiple_adapters(tmp_path, monkeypatch, interrupt_at):
    index, row = export_fixture(tmp_path)
    reference = fixture('odeformer_clean')[0]
    monkeypatch.setattr(ode, 'integrate_truth', lambda system, ic, t: (np.zeros((len(t), int(system['dim']))), None))
    monkeypatch.setattr(ode, 'clean_eval_fields', lambda *args: {})
    # The fake adapters exercise orchestration/RNG, not the optional optimizer package.
    monkeypatch.setattr(ode.run_odeformer_grid, 'preflight_odeformer_constant_optimization', lambda configs: None)
    class Adapter:
        def __init__(self, config):
            random.seed(config['seed'])
            np.random.seed(config['seed'])
        def close(self): pass
    monkeypatch.setattr(harness, 'build_odeformer_adapter', Adapter)
    calls = [0]
    interrupt = [False]
    def fit(system, source, target, config, adapter):
        calls[0] += 1
        if interrupt[0] and calls[0] == interrupt_at:
            raise KeyboardInterrupt('eviction')
        record = copy.deepcopy(reference)
        record['odeformer_config_id'] = config['config_id']
        record['method_config'] = json.dumps(config)
        record['odeformer_model_canonical'] = f'{random.random() + float(np.random.random())}*x_0'
        return record
    monkeypatch.setattr(harness, 'run_odeformer_record_with_adapter', fit)
    def run(destination):
        return ode.run_noise_odeformer(CONFIGS['odeformer'], [index], destination, repetitions=2,
                    execution=UnitJournal(destination, 'context', SHA, IMAGE))
    continuous = run(tmp_path / 'continuous')
    calls[0] = 0
    interrupt[0] = True
    with pytest.raises(KeyboardInterrupt): run(tmp_path / 'interrupted')
    interrupt[0] = False
    resumed = run(tmp_path / 'interrupted')
    extract = lambda path: [(unit_key(r), r['odeformer_model_canonical']) for r in
                            [json.loads(line) for line in path.read_text().splitlines()]]
    assert extract(continuous['records']) == extract(resumed['records'])
