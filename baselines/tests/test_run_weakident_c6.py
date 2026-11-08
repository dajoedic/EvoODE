"""Q-B2 mapping/dictionary/hash tests; real Q9 records, no benchmark fits."""
import contextlib
import io
import itertools
import json
import math
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "baselines"))
import run_weakident_c6 as adapter
from scripts.aggregate.run_wp_n6_sindy_baseline import compile_feature_evaluator


@pytest.mark.parametrize("dim", [1, 2, 3, 4])
def test_every_cubic_and_trig_mapping(dim):
    # Exhaustive total-degree dictionary; dim4 mapping is checked even though
    # the reference builder cannot construct that dimension.
    powers = [p for p in itertools.product(range(4), repeat=dim) if sum(p) <= 3]
    assert len(powers) == math.comb(dim + 3, 3)
    names = [adapter.term_name(p) for p in powers]
    names += [adapter.trig_name(f, i) for i in range(dim) for f in ("sin", "cos")]
    assert len(set(names)) == len(names)
    state = np.linspace(-.73, 1.27, dim)
    expected = [np.prod(state ** p) for p in powers]
    expected += [f(state[i]) for i in range(dim) for f in (np.sin, np.cos)]
    np.testing.assert_allclose(compile_feature_evaluator(names)(state), expected, rtol=1e-14, atol=1e-14)
    if dim <= 3:
        tags, _, rhs, _ = adapter.reference.build_feature_vector_tags(
            dim, 1, 0, 3, False, [np.empty((0, dim + 3)) for _ in range(dim)], True)
        assert {tuple(t[:dim]) for t in tags[rhs]} == set(powers)


@pytest.fixture
def real_input():
    folder = ROOT / "outputs/sideproject_q5w_wsindy/matlab_inputs/w1_interp"
    manifest = json.loads((folder / "manifest.json").read_text())
    entry = next(e for e in manifest["cells"] if e["library"] == "L-C6" and
                 e["cell_key"] == dict(system_id=1, initial_condition_set=1, noise_sigma=.05,
                                       subsample_rho=.5, noise_realization=1))
    data = loadmat(folder / entry["input_file"])
    return data["tobs"].reshape(-1), data["xobs"], entry


def test_extension_preserves_native_columns_and_uses_same_kernel(real_input):
    t, x, _ = real_input
    u, xs = x.T[:, None, :], t.reshape(1, 1, -1)
    with contextlib.redirect_stdout(io.StringIO()):
        native = adapter.build_dictionary(u, xs, False)
        extended = adapter.build_dictionary(u, xs, True)
        disabled = adapter.build_dictionary(u, xs, False)
    for i in range(5):
        np.testing.assert_array_equal(native[i], disabled[i])
    assert native[5] == disabled[5]
    for i in (0, 4):
        np.testing.assert_array_equal(native[i], extended[i])
    columns = native[2].shape[1]
    np.testing.assert_array_equal(native[2], extended[2][:, :columns])
    np.testing.assert_array_equal(extended[2], extended[3])
    assert extended[5][-2:] == ["sin(1 x0)", "cos(1 x0)"]
    # Obtain the actual reference kernel/indices, then check by direct circular
    # convolution, independent of its FFT convolution implementation.
    captured = {}
    original = adapter.reference.compute_w_ode
    def capture(tags, state, fft, indices):
        captured.update(kernel=np.fft.ifft(fft[0]).real, indices=indices)
        return original(tags, state, fft, indices)
    with contextlib.redirect_stdout(io.StringIO()), patch.object(adapter.reference, "compute_w_ode", capture):
        adapter.build_dictionary(u, xs, False)
    kernel, indices = captured["kernel"], captured["indices"]
    for i, function in enumerate((np.sin, np.cos)):
        values = function(x[:, 0])
        direct = np.asarray([sum(values[j] * kernel[(k - j) % len(values)] for j in range(len(values)))
                             for k in indices])
        np.testing.assert_allclose(extended[2][:, columns + i], direct, rtol=1e-12, atol=1e-12)


def test_interpolated_hash_checks(real_input):
    t, x, entry = real_input
    adapter.validate_interpolated(t, x, entry)
    for field in ("time_sha256", "state_sha256", "q5w_interpolated_sha256"):
        changed = dict(entry, **{field: "0" * 64})
        with pytest.raises(ValueError, match="hash|sha256"):
            adapter.validate_interpolated(t, x, changed)
    changed = x.copy()
    changed[0, 0] += .01
    with pytest.raises(ValueError, match="state hash"):
        adapter.validate_interpolated(t, changed, entry)


def test_q9_and_actual_observed_hash_checks():
    q9 = ROOT / "outputs/sideproject_q9_inputs/grid/q9_paths.json"
    record = json.loads(q9.read_text())["cells"][0]
    frame = pd.DataFrame([record["export"]])
    adapter.select_q9(frame, q9)
    row = frame.iloc[0]
    root = ROOT / "outputs/phase_c_c6_data_conditions_5dd1df8"
    adapter.baseline.read_index_cell(root, row)
    changed = frame.copy()
    changed.loc[0, "state_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="state_sha256 mismatch"):
        adapter.select_q9(changed, q9)
    with pytest.raises(ValueError, match="sha256|hash"):
        adapter.baseline.read_index_cell(root, changed.iloc[0])


def test_dimension4_marker_never_fits():
    q9 = json.loads((ROOT / "outputs/sideproject_q9_inputs/grid/q9_paths.json").read_text())
    row = pd.Series(next(c["export"] for c in q9["cells"] if c["dim"] == 4))
    systems = adapter.baseline.load_benchmark(ROOT / "benchmarks/data/strogatz_extended.json")
    system = next(s for s in systems if s["id"] == int(row.system_id))
    supports = adapter.baseline.load_phase_c_support(ROOT / "studies/regression/phase_c_support.json").set_index("system_id")
    # No trajectory is read or integrated: the unsupported row must bypass fitting.
    with patch.object(adapter, "fit", side_effect=AssertionError("must not fit")):
        result = adapter.evaluate(adapter.METHODS[0], system, supports.loc[int(row.system_id)].to_dict(), row,
                                  np.arange(2.), np.zeros((2, 4)), np.arange(2.),
                                  {1: np.zeros((2, 4)), 2: np.zeros((2, 4))})
    assert result["fit_status"] == adapter.UNSUPPORTED
    assert result["structure_status"] == adapter.UNSUPPORTED
    assert result["sindy_structure_hit_raw"] == ""
    assert result["reconstruction_r2_variance_weighted_gt_0_9"] == ""
