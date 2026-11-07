"""Q9 path builder: scope and the bit-identity control against Q8 C1000 (protocol Q9 §5)."""
import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/aggregate'))
import build_sideproject_q9_paths as b

Q8_C1000 = b.ROOT/'outputs/sideproject_q8_inputs/grid/q8_C1000_paths.json'


@pytest.fixture(scope='module')
def cells():
    return b.source_cells()


def test_scope_is_4284_cells_all_systems(cells):
    assert len(cells) == 4284
    assert len({c['system_id'] for c in cells}) == 63
    assert len({c['unit_id'] for c in cells}) == 126
    clean = [c for c in cells if c['sigma'] == 0 and c['rho'] == 0]
    assert len(clean) == 126 and all(c['realization'] == 1 for c in clean)
    noisy = [c for c in cells if not (c['sigma'] == 0 and c['rho'] == 0)]
    assert len(noisy) == 126*11*3


def test_blocks_split_dim3_exact(cells):
    blocks = {c['block'] for c in cells}
    assert {'dim3_exact_52_61', 'dim3_exact_54_59', 'dim1_exact', 'dim2_surrogate'} <= blocks
    assert all(c['block'] == 'dim3_exact_52_61' for c in cells if c['system_id'] in (52, 61))


def test_cell_ids_match_q8_convention(cells):
    q8 = json.loads(Q8_C1000.read_bytes())['cells']
    ours = {c['cell_id']: c for c in cells}
    for c in q8:
        assert c['cell_id'] in ours
        assert ours[c['cell_id']]['observed_data_sha256'] == c['observed_data_sha256']


@pytest.mark.parametrize('pick', [0, 101, 333])
def test_paths_reproduce_q8_c1000(cells, pick):
    q8 = sorted(json.loads(Q8_C1000.read_bytes())['cells'], key=lambda c: c['cell_id'])
    old = q8[pick]
    new = b.q8.build_path(next(c for c in cells if c['cell_id'] == old['cell_id']), 'q7')
    fields = ('candidate_id', 'active_idxs', 'p0', 'k', 'equations', 'weak_bic', 'step', 'origin')
    assert [{f: k[f] for f in fields} for k in new['candidates']] == [{f: k[f] for f in fields} for k in old['candidates']]
