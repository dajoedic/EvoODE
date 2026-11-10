"""Unit tests of the Q9-A analysis building blocks on synthetic data (no production result is read)."""
import sys
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'aggregate'))
import q9a_claims as qa  # noqa: E402


def test_sign_flip_exact_matches_brute_force():
    d = np.array([.3, -.1, .2, 0., .05, .4])
    obs = abs(d.sum())
    brute = np.mean([abs(np.dot(s, d)) >= obs - 1e-12 for s in product((-1, 1), repeat=len(d))])
    assert qa.sign_flip_p(d, np.random.default_rng(0)) == pytest.approx(brute)


def test_sign_flip_all_zero_is_one():
    assert qa.sign_flip_p(np.zeros(5), np.random.default_rng(0)) == 1.0


def test_holm():
    adj = qa.holm(np.array([.01, .04, .03, .005]))
    assert np.allclose(adj, [.03, .06, .06, .02])


def cells_frame():
    rows = []
    for s, ic, sig, r in product((1, 2, 3), (1, 2), (0.0, 0.01), (1,)):
        rows.append(dict(cell_id=f'c{s}_{ic}_{sig}', system_id=s, initial_condition_set=ic, sigma=sig, rho=0.0,
                         realization=r, stratum='dim1_exact', representability='exact', dim=1))
    return pd.DataFrame(rows)


def test_in_favour_picks_best_configuration_per_metric():
    cells = cells_frame()
    noisy = cells[cells.sigma > 0].cell_id
    refs = pd.concat([pd.DataFrame(dict(cell_id=noisy, method='sindy', config=cfg,
                                        structure=v1, raw=v1, rec=v2, gen=v2))
                      for cfg, v1, v2 in (('a', 1.0, 0.0), ('b', 0.0, 1.0))], ignore_index=True)
    sel = qa.in_favour(refs, cells)
    assert set(sel.structure_config) == {'a'} and set(sel.gen_config) == {'b'}
    assert sel.structure.eq(1).all() and sel.gen.eq(1).all()


def test_missing_wisp_cell_counts_as_miss_and_can_only_raise_rates():
    cells = cells_frame()
    noisy = cells[cells.sigma > 0]
    base = pd.DataFrame(dict(cell_id=noisy.cell_id, size_rule='c', status='complete',
                             structure=1.0, raw=1.0, rec=1.0, gen=1.0))
    refs = pd.DataFrame(dict(cell_id=noisy.cell_id, method='wsindy', config='W1', structure=0.0, raw=0.0, rec=0.0, gen=0.0))
    missing = base.copy()
    missing.loc[missing.index[0], ['status', 'structure', 'raw', 'rec', 'gen']] = ['missing', 0.0, 0.0, 0.0, 0.0]
    rng = np.random.default_rng(0)
    full = qa.paired(qa.long_table(cells, base, refs)[lambda f: f.sigma > 0], 'WISP', 'wsindy', ['dim1_exact'], 'structure', rng)
    part = qa.paired(qa.long_table(cells, missing, refs)[lambda f: f.sigma > 0], 'WISP', 'wsindy', ['dim1_exact'], 'structure', rng)
    assert part['n_cells'] == full['n_cells']          # the missing cell is not dropped
    assert part['rate_a'] < full['rate_a']             # it counts as a miss
    assert part['diff'] < full['diff']                 # so completing it can only raise the difference


def test_macro_names_are_alphabetic():
    rates = pd.DataFrame([dict(population='noisy', method='WISP', stratum='dim1_exact', metric='structure',
                               rate=.5, lo=.4, hi=.6)])
    prim = pd.DataFrame([dict(test=t, diff=.1, p_holm=.01, ratio=2., systems_ahead=3, systems_behind=0)
                         for t in ('P1', 'P2', 'P3', 'P4')])
    extra = dict(C6=dict(num=1, den=2, share=.5), C8=dict(oversize_weak=.4, oversize_traj=.2))
    frame, tex = qa.macros(rates, prim, extra)
    assert frame.macro.str.fullmatch('[A-Za-z]+').all() and '\\newcommand{\\PrimaryOneDiff}{10.0}' in tex
