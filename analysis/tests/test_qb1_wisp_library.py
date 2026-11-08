"""Q-B1 checks derived from the real basis, support file, and Q9 records."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from exploratory.term_relevance.term_relevance import evaluate_basis, phasec_basis
from scripts.aggregate.qb1_wisp_library import WispLibrary, legacy_term, select_q9
from scripts.aggregate.run_phasec_noise_sindy_baselines import read_index_cell
from scripts.aggregate.run_wp_n6_sindy_baseline import library_grid, library_true_terms

Q9 = ROOT / "outputs/sideproject_q9_inputs/grid/q9_paths.json"


@pytest.mark.parametrize("dim", [1, 2, 3, 4])
def test_basis_names_order_and_values(dim):
    states = np.random.default_rng(193).normal(size=(40, dim))
    lib = WispLibrary().fit(states)
    assert lib.get_feature_names() == [term.name for term in phasec_basis(dim)]
    np.testing.assert_array_equal(lib.transform(states), evaluate_basis(states, phasec_basis(dim)))


def test_thresholds_and_unique_identifiers():
    config = json.loads((ROOT / "analysis/configs/sideproject_qb1_sindy.json").read_text())
    configs = library_grid(config)
    assert [c.threshold for c in configs] == [10 ** (-3 + k / 4) for k in range(13)]
    assert len({c.library_id for c in configs}) == 13
    assert not {c.library_id for c in configs} & {c.library_id for c in library_grid({})}


def test_every_exact_support_maps_to_existing_truth():
    supports = json.loads((ROOT / "studies/regression/phase_c_support.json").read_text())["systems"]
    systems = {s["id"]: s for s in json.loads((ROOT / "benchmarks/data/strogatz_extended.json").read_text())}
    count = 0
    for support in supports:
        if support["representability"] != "exact" or support["status"] != "ok":
            continue
        mapped = [{legacy_term(t).replace(" ", "*") for t in eq} for eq in support["support_terms"]]
        assert mapped == library_true_terms(systems[support["system_id"]]), support["system_id"]
        count += 1
    assert count == 30


def test_q9_hash_checks_real_record(tmp_path):
    payload = json.loads(Q9.read_text())
    frame = pd.DataFrame([payload["cells"][0]["export"]])
    assert len(select_q9(frame, Q9)) == 1
    with pytest.raises(ValueError, match="duplicate Q9"):
        select_q9(pd.concat([frame, frame]), Q9)
    changed = frame.copy()
    changed.loc[0, "state_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="state_sha256 mismatch"):
        select_q9(changed, Q9)
    payload["cells"][0]["observed_data_sha256"] = '{}'
    path = tmp_path / "bad_q9.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="embedded hash mismatch"):
        select_q9(frame, path)
    with pytest.raises(ValueError, match="export covers"):
        select_q9(frame, Q9, require_all=True)


def test_raw_bytes_hash_rejected(tmp_path):
    # Keep the exact metadata of a real Q9 record and change one exported byte.
    cell = json.loads(Q9.read_text())["cells"][0]
    row = pd.Series(cell["export"])
    root = ROOT / "outputs/phase_c_c6_data_conditions_5dd1df8"
    source = root / row["cell_dir"] / Path(row["time_path"].replace("\\", "/"))
    data = bytearray(source.read_bytes())
    data[0] ^= 1
    target = tmp_path / "time.bin"
    target.write_bytes(data)
    row["cell_dir"] = str(tmp_path)
    row["time_path"] = "time.bin"
    with pytest.raises(ValueError, match="hash mismatch"):
        read_index_cell(tmp_path, row)


def test_q9_shards_cover_the_real_cell_list(tmp_path, monkeypatch):
    from scripts.aggregate.run_k8s_sindy_shard import build_shard_index
    root = ROOT / "outputs/phase_c_c6_data_conditions_5dd1df8"
    frame = pd.read_csv(root / "index.csv")
    expected = select_q9(frame, Q9, require_all=True)
    monkeypatch.setenv("EVO_SINDY_Q9_PATHS", str(Q9))
    monkeypatch.delenv("EVO_SINDY_FILTER_QUERY", raising=False)
    parts = [pd.read_csv(build_shard_index(root, tmp_path, i, 3)) for i in range(3)]
    keys = ["system_id", "initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"]
    actual = pd.concat(parts)
    assert len(actual) == 4284 and not actual.duplicated(keys).any()
    assert set(map(tuple, actual[keys].values)) == set(map(tuple, expected[keys].values))
