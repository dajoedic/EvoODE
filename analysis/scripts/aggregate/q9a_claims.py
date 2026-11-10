"""Protocol Q9-A: the paper's claims, tests, robustness checks, descriptive tables and LaTeX number macros.

Input: the directory written by `build_wisp_paper_cells.py`. Everything the frozen protocol
(`docs/sideproject_residual_growth_protocol_q9_claims.md`) fixes is implemented here and nothing else:
systems as units, cluster bootstrap over systems (10,000, fixed seed), two-sided sign-flip test on per-system rate
differences (exact enumeration up to 20 systems), Holm over the primary family P1-P4 (WISP vs WSINDy), references at
their in-favour configuration per method x stratum x sigma x metric (WSINDy has no configuration choice).

`--strict` (production) requires the full Q9 population (10 noisy conditions x 3 realizations x 2 ICs per system);
without it the script runs on any population (dry run on Q8) and says so in the metadata.

Outputs (refuses to overwrite): claims.csv, primary.csv, secondary.csv, robustness.csv, rates.csv, by_condition.csv,
per_system.csv, dim34.csv, cost.csv, missing.csv, macros.tex, macros.csv, metadata.json.
"""
from __future__ import annotations
import argparse
import json
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 20261110
B = 10_000
NOISY_CONDITIONS = {(s, r) for s in (0.01, 0.02, 0.03, 0.04, 0.05) for r in (0.0, 0.5)}
EXACT12 = ('dim1_exact', 'dim2_exact')
SURR12 = ('dim1_surrogate', 'dim2_surrogate')
FIXED_CONFIG = {'wsindy'}  # W1 on rho = 0, W1-interp on rho = 0.5; no choice is made for it
METRICS = ('structure', 'raw', 'rec', 'gen')


# ----------------------------------------------------------------------------- data
def load(d):
    d = Path(d)
    cells = pd.read_csv(d / 'cells.csv')
    choices = pd.read_csv(d / 'wisp_choices.csv')
    refs = pd.read_csv(d / 'reference_cells.csv')
    meta = json.loads((d / 'build_metadata.json').read_text(encoding='utf8'))
    for f in (choices, refs):
        for m in METRICS:
            f[m] = f[m].map(lambda v: np.nan if pd.isna(v) else float(v in (True, 'True', 1, 1.0)))
    return cells, choices, refs, meta


def sigma_group(row_sigma, row_rho):
    if row_sigma > 0:
        return f's{row_sigma:g}'
    return 'clean' if row_rho == 0 else 'sub'


def in_favour(refs, cells, scope='per_sigma', population=None):
    """Per method x stratum x group x metric: the configuration with the highest hit rate (ties: largest id).

    scope 'per_sigma' (primary, Q-B): group = sigma (both rho pooled), clean and (0, 0.5) apart.
    scope 'per_stratum' (robustness): one configuration per method x stratum x metric over the noisy population.
    """
    r = refs.merge(cells[['cell_id', 'stratum', 'sigma', 'rho']], on='cell_id')
    r['group'] = [sigma_group(s, p) for s, p in zip(r.sigma, r.rho)]
    if scope == 'per_stratum':
        r['group'] = np.where(r.sigma > 0, 'noisy', r.group)
    out = []
    for (method, stratum, group), g in r.groupby(['method', 'stratum', 'group']):
        base = g[['cell_id']].drop_duplicates().set_index('cell_id')
        for m in METRICS:
            if method in FIXED_CONFIG:
                vals = g.set_index('cell_id')[m]
                if vals.index.duplicated().any():
                    raise ValueError('Fixed-configuration reference has two rows per cell: ' + method)
                base[m] = vals
                continue
            scores = g.groupby('config')[m].mean()
            if scores.isna().all():
                base[m] = np.nan
                continue
            best = max(scores.dropna().items(), key=lambda kv: (kv[1], kv[0]))[0]
            base[m] = g[g.config == best].set_index('cell_id')[m]
            base[m + '_config'] = best
        base['method'] = method
        out.append(base.reset_index())
    return pd.concat(out, ignore_index=True)


def long_table(cells, choices, refs, scope='per_sigma'):
    w = choices[choices.size_rule == 'c'][['cell_id', 'status', *METRICS]].copy()
    w['method'] = 'WISP'
    sel = in_favour(refs, cells, scope)
    allm = pd.concat([w, sel], ignore_index=True)
    return allm.merge(cells, on='cell_id', validate='many_to_one')


# ----------------------------------------------------------------------------- statistics
def rate_ci(g, m, rng):
    g = g.dropna(subset=[m])
    if g.empty:
        return dict(rate=np.nan, lo=np.nan, hi=np.nan, n_cells=0, n_systems=0)
    per = g.groupby('system_id')[m].agg(['sum', 'count'])
    s, n = per['sum'].to_numpy(float), per['count'].to_numpy(float)
    idx = rng.integers(0, len(s), size=(B, len(s)))
    boot = s[idx].sum(1) / n[idx].sum(1)
    return dict(rate=s.sum() / n.sum(), lo=np.quantile(boot, .025), hi=np.quantile(boot, .975),
                n_cells=int(n.sum()), n_systems=len(s))


def sign_flip_p(d, rng):
    """Two-sided sign-flip test of the mean per-system difference; exact up to 20 systems."""
    d = np.asarray(d, float)
    n, obs = len(d), abs(d.sum())
    if n == 0 or not np.any(d):
        return 1.0
    if n <= 20:
        hits, total = 0, 1 << n
        for start in range(0, total, 1 << 16):
            k = np.arange(start, min(total, start + (1 << 16)), dtype=np.int64)
            signs = 1 - 2 * ((k[:, None] >> np.arange(n)) & 1)
            hits += int((np.abs(signs @ d) >= obs - 1e-12).sum())
        return hits / total
    signs = rng.choice([-1.0, 1.0], size=(100_000, n))
    return (int((np.abs(signs @ d) >= obs - 1e-12).sum()) + 1) / 100_001


def paired(allm, method_a, method_b, strata, m, rng, mask=None):
    a = allm[(allm.method == method_a) & allm.stratum.isin(strata)]
    b = allm[(allm.method == method_b) & allm.stratum.isin(strata)]
    if mask is not None:
        a, b = a[mask(a)], b[mask(b)]
    j = a.merge(b[['cell_id', m]], on='cell_id', suffixes=('_a', '_b')).dropna(subset=[m + '_a', m + '_b'])
    if j.empty:
        return None
    per = j.groupby('system_id').agg(sa=(m + '_a', 'sum'), sb=(m + '_b', 'sum'), n=(m + '_a', 'size'))
    sa, sb, n = (per[c].to_numpy(float) for c in ('sa', 'sb', 'n'))
    d = sa / n - sb / n
    idx = rng.integers(0, len(n), size=(B, len(n)))
    ra, rb = sa[idx].sum(1) / n[idx].sum(1), sb[idx].sum(1) / n[idx].sum(1)
    rate_a, rate_b = sa.sum() / n.sum(), sb.sum() / n.sum()
    return dict(rate_a=rate_a, rate_b=rate_b, diff=rate_a - rate_b, diff_lo=np.quantile(ra - rb, .025),
                diff_hi=np.quantile(ra - rb, .975), ratio=rate_a / rate_b if rate_b else np.inf,
                p=sign_flip_p(d, rng), n_cells=int(n.sum()), n_systems=len(n), dropped_cells=int(len(a) - len(j)),
                systems_ahead=int((d > 0).sum()), systems_tied=int((d == 0).sum()), systems_behind=int((d < 0).sum()))


def holm(ps):
    order = np.argsort(ps)
    adj, running = np.empty(len(ps)), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, running)
    return adj


def boot_share(num_by_sys, den_by_sys, rng):
    s, n = np.asarray(num_by_sys, float), np.asarray(den_by_sys, float)
    keep = n > 0
    s, n = s[keep], n[keep]
    idx = rng.integers(0, len(n), size=(B, len(n)))
    boot = s[idx].sum(1) / n[idx].sum(1)
    return s.sum() / n.sum(), np.quantile(boot, .025), np.quantile(boot, .975), int(s.sum()), int(n.sum())


# ----------------------------------------------------------------------------- claims
def evaluate(cells, choices, refs, allm, rng):
    noisy = allm[allm.sigma > 0]
    rows, prim = [], []
    for name, stratum, m in (('P1', 'dim1_exact', 'structure'), ('P2', 'dim2_exact', 'structure'),
                             ('P3', 'dim1_exact', 'gen'), ('P4', 'dim2_exact', 'gen')):
        r = paired(noisy, 'WISP', 'wsindy', [stratum], m, rng)
        prim.append(dict(test=name, stratum=stratum, metric=m, reference='wsindy', **r))
    prim = pd.DataFrame(prim)
    prim['p_holm'] = holm(prim.p.to_numpy())
    prim['pass'] = (prim.p_holm < .05) & (prim['diff'] > 0)
    rows.append(dict(claim='C1', verdict=bool(prim.loc[prim.test.isin(['P1', 'P2']), 'pass'].all()),
                     detail='P1, P2 after Holm'))
    rows.append(dict(claim='C2', verdict=bool(prim.loc[prim.test.isin(['P3', 'P4']), 'pass'].all()),
                     detail='P3, P4 after Holm'))

    sec = []
    expected = ['sindy', 'weak_sindy', 'e_sindy', 'weakident_native', 'weakident_trig', 'B1', 'B3']
    present = sorted(set(noisy.method) - {'WISP', 'wsindy'})
    for ref, stratum, m in product(present, EXACT12, ('structure', 'gen')):
        r = paired(noisy, 'WISP', ref, [stratum], m, rng)
        if r:
            sec.append(dict(family='C3', reference=ref, stratum=stratum, metric=m, **r))
    for stratum, m in product(SURR12, ('rec', 'gen')):
        r = paired(noisy, 'WISP', 'wsindy', [stratum], m, rng)
        sec.append(dict(family='C9', reference='wsindy', stratum=stratum, metric=m, **r))
    for stratum, m in product(EXACT12, ('structure', 'rec', 'gen')):
        r = paired(noisy, 'WISP', 'wsindy', [stratum], m, rng)
        sec.append(dict(family='C4', reference='wsindy', stratum=stratum, metric=m, **r))
    sec = pd.DataFrame(sec)
    sec['pass'] = (sec['diff'] > 0) & (sec.p < .05)
    c3 = sec[sec.family == 'C3']
    pending = [e for e in expected if not any(p == e or p.startswith(e + ':') for p in present)]
    failing = sorted(f"{r['reference']}/{r['stratum']}/{r['metric']}" for _, r in c3.iterrows() if not r['pass'])
    rows.append(dict(claim='C3', verdict=(not failing) and not pending,
                     detail=f"failing: {failing or 'none'}; pending references: {pending or 'none'}"))
    c4 = sec[sec.family == 'C4']
    rows.append(dict(claim='C4', verdict=bool((c4.systems_ahead > c4.systems_behind).all()),
                     detail='; '.join(f'{r.stratum}/{r.metric} {r.systems_ahead}/{r.systems_tied}/{r.systems_behind}'
                                      for r in c4.itertuples())))

    # C5: (WISP - WSINDy) structure at sigma = 0.05 minus on clean, exact dim 1-2, systems resampled together
    e = allm[allm.stratum.isin(EXACT12)]
    def diffs(mask):
        a = e[(e.method == 'WISP') & mask(e)]
        b = e[(e.method == 'wsindy') & mask(e)]
        j = a.merge(b[['cell_id', 'structure']], on='cell_id', suffixes=('_a', '_b')).dropna(subset=['structure_a', 'structure_b'])
        return j.groupby('system_id').agg(sa=('structure_a', 'sum'), sb=('structure_b', 'sum'), n=('structure_a', 'size'))
    hi_, cl_ = diffs(lambda f: np.isclose(f.sigma, .05)), diffs(lambda f: (f.sigma == 0) & (f.rho == 0))
    sys_ = sorted(set(hi_.index) & set(cl_.index))
    H, Cc = hi_.loc[sys_].to_numpy(float), cl_.loc[sys_].to_numpy(float)
    idx = rng.integers(0, len(sys_), size=(B, len(sys_)))
    def gap(X):
        return (X[..., 0].sum(-1) - X[..., 1].sum(-1)) / X[..., 2].sum(-1)
    obs = gap(H) - gap(Cc)
    boot = gap(H[idx]) - gap(Cc[idx])
    c5 = dict(gap_005=gap(H), gap_clean=gap(Cc), diff=obs, lo=np.quantile(boot, .025), hi=np.quantile(boot, .975),
              n_systems=len(sys_))
    rows.append(dict(claim='C5', verdict=bool(c5['lo'] > 0), detail=json.dumps({k: round(float(v), 4) for k, v in c5.items()})))

    # C6-C8 from WISP's own diagnostics
    w = choices.merge(cells, on='cell_id')
    wn = w[(w.sigma > 0) & w.stratum.isin(EXACT12) & w.status.eq('complete')]
    c = wn[wn.size_rule == 'c']
    on = c[c.truth_on_path.astype(str).eq('True')]
    g = on.groupby('system_id').agg(s=('raw', 'sum'), n=('raw', 'size'))
    share, lo, hi, num, den = boot_share(g.s, g.n, rng)
    rows.append(dict(claim='C6', verdict=bool(share >= .9 and lo >= .8),
                     detail=f'{num}/{den} = {share:.3f} [{lo:.3f}, {hi:.3f}]'))
    miss = w[(w.sigma > 0) & w.stratum.isin(EXACT12) & (w.size_rule == 'c') & (w.structure == 0)]
    path_fail = (~miss.truth_on_path.astype(str).eq('True'))
    rows.append(dict(claim='C7', verdict=bool(path_fail.mean() >= 2 / 3),
                     detail=f'{int(path_fail.sum())}/{len(miss)} misses without the truth on the path '
                            f'(missing cells count as path failures: {int(miss.status.eq("missing").sum())})'))
    d2 = wn[wn.stratum == 'dim2_exact']
    a = d2[d2.size_rule == 'a'].set_index('cell_id').size_error
    cc = d2[d2.size_rule == 'c'].set_index('cell_id').size_error
    j = pd.DataFrame({'a': (a > 0).astype(float), 'c': (cc > 0).astype(float)}).dropna()
    j['system_id'] = d2.drop_duplicates('cell_id').set_index('cell_id').loc[j.index, 'system_id']
    per = j.groupby('system_id').agg(a=('a', 'sum'), c=('c', 'sum'), n=('a', 'size'))
    A, Cn, N = (per[k].to_numpy(float) for k in ('a', 'c', 'n'))
    idx = rng.integers(0, len(N), size=(B, len(N)))
    boot = (A[idx].sum(1) - Cn[idx].sum(1)) / N[idx].sum(1)
    c8 = dict(oversize_weak=A.sum() / N.sum(), oversize_traj=Cn.sum() / N.sum(), diff=(A.sum() - Cn.sum()) / N.sum(),
              lo=np.quantile(boot, .025), hi=np.quantile(boot, .975), n_cells=int(N.sum()))
    rows.append(dict(claim='C8', verdict=bool(c8['lo'] > 0), detail=json.dumps({k: round(float(v), 4) for k, v in c8.items()})))
    c9 = sec[sec.family == 'C9']
    rows.append(dict(claim='C9', verdict=bool(c9['pass'].all()),
                     detail='; '.join(f'{r.stratum}/{r.metric} diff {r.diff:+.3f} p {r.p:.3g}' for r in c9.itertuples())))
    ratios = prim[prim.metric == 'structure'].set_index('stratum').ratio
    rows.append(dict(claim='wording: roughly doubles (structure)', verdict=bool((ratios >= 1.8).all()),
                     detail='; '.join(f'{k} ratio {v:.2f}' for k, v in ratios.items())))
    return pd.DataFrame(rows), prim, sec, dict(C5=c5, C6=dict(share=share, lo=lo, hi=hi, num=num, den=den), C8=c8)


def robustness(cells, choices, refs, rng):
    base = long_table(cells, choices, refs)
    variants = {'raw structure': (base, lambda f: f, {'structure': 'raw'}),
                'IC 1 only': (base, lambda f: f[f.initial_condition_set == 1], {}),
                'IC 2 only': (base, lambda f: f[f.initial_condition_set == 2], {}),
                'rho = 0 only': (base, lambda f: f[f.rho == 0], {}),
                'references single best per stratum': (long_table(cells, choices, refs, 'per_stratum'), lambda f: f, {}),
                'available case': (base[~base.status.eq('missing') | (base.method != 'WISP')], lambda f: f, {})}
    for r in sorted(cells.realization.unique()):
        variants[f'realization {r} only'] = (base, lambda f, r=r: f[f.realization == r], {})
    out = []
    for name, (tab, filt, swap) in variants.items():
        t = filt(tab)
        t = t[t.sigma > 0]
        if name == 'available case':
            t = t[~t.cell_id.isin(choices[(choices.size_rule == 'c') & choices.status.eq('missing')].cell_id)]
        for test, stratum, m in (('P1', 'dim1_exact', 'structure'), ('P2', 'dim2_exact', 'structure'),
                                 ('P3', 'dim1_exact', 'gen'), ('P4', 'dim2_exact', 'gen')):
            mm = swap.get(m, m)
            r = paired(t, 'WISP', 'wsindy', [stratum], mm, rng)
            if r:
                out.append(dict(variant=name, test=test, metric=mm, **r))
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- descriptive
def descriptive(allm, choices, cells, rng):
    pops = {'noisy': allm.sigma > 0, 'clean': (allm.sigma == 0) & (allm.rho == 0), 'sub': (allm.sigma == 0) & (allm.rho > 0)}
    rates = []
    for pop, mask in pops.items():
        for (method, stratum), g in allm[mask].groupby(['method', 'stratum']):
            for m in METRICS:
                rates.append(dict(population=pop, method=method, stratum=stratum, metric=m, **rate_ci(g, m, rng)))
    bycond = []
    for (method, stratum, sigma, rho), g in allm.groupby(['method', 'stratum', 'sigma', 'rho']):
        for m in ('structure', 'rec', 'gen'):
            bycond.append(dict(method=method, stratum=stratum, sigma=sigma, rho=rho, metric=m, **rate_ci(g, m, rng)))
    persys = allm[allm.sigma > 0].groupby(['method', 'system_id', 'stratum'])[list(METRICS)].mean().reset_index()
    d34 = allm[allm.stratum.str.startswith(('dim3', 'dim4')) & (allm.sigma > 0)]
    d34 = d34.groupby(['system_id', 'stratum', 'method'])[['structure', 'rec', 'gen']].agg(['sum', 'count']).reset_index()
    d34.columns = ['_'.join(c).strip('_') for c in d34.columns]
    w = choices[(choices.size_rule == 'c') & choices.status.eq('complete')].merge(cells, on='cell_id')
    cost = []
    for (stratum, noisy), g in w.groupby(['stratum', w.sigma > 0]):
        for f in ('n_candidates', 'total_loss_evals', 'total_ode_solves'):
            q = g[f].quantile([.1, .5, .9]).to_list()
            cost.append(dict(stratum=stratum, population='noisy' if noisy else 'noise-free', quantity=f,
                             q10=q[0], median=q[1], q90=q[2], n_cells=len(g)))
    missing = choices[(choices.size_rule == 'c') & choices.status.eq('missing')].merge(cells, on='cell_id')
    return (pd.DataFrame(rates), pd.DataFrame(bycond), persys, d34, pd.DataFrame(cost),
            missing[['cell_id', 'system_id', 'stratum', 'sigma', 'rho', 'realization']])


# ----------------------------------------------------------------------------- macros
WORD = {'dim1_exact': 'DimOneExact', 'dim2_exact': 'DimTwoExact', 'dim1_surrogate': 'DimOneSurr',
        'dim2_surrogate': 'DimTwoSurr', 'structure': 'Struct', 'raw': 'Raw', 'rec': 'Rec', 'gen': 'Gen',
        'WISP': 'Wisp', 'wsindy': 'Wsindy', 'sindy': 'Sindy', 'weak_sindy': 'WeakSindy', 'e_sindy': 'Esindy',
        'weakident_native': 'WeakIdentNative', 'weakident_trig': 'WeakIdentTrig'}


def macros(rates, prim, extra):
    out = []
    def add(name, value, source):
        out.append(dict(macro=name, value=value, source=source))
    r = rates[(rates.population == 'noisy') & rates.method.isin(WORD) & rates.stratum.isin(WORD)]
    for x in r.itertuples():
        if pd.isna(x.rate):
            continue
        base = f'{WORD[x.method]}{WORD[x.stratum]}{WORD[x.metric]}Noisy'
        add(base, f'{100 * x.rate:.1f}', 'rates.csv')
        add(base + 'Lo', f'{100 * x.lo:.0f}', 'rates.csv')
        add(base + 'Hi', f'{100 * x.hi:.0f}', 'rates.csv')
    num = {'P1': 'One', 'P2': 'Two', 'P3': 'Three', 'P4': 'Four'}
    for x in prim.itertuples():
        t = 'Primary' + num[x.test]
        add(f'{t}Diff', f'{100 * x.diff:.1f}', 'primary.csv')
        add(f'{t}PHolm', f'{x.p_holm:.3g}', 'primary.csv')
        add(f'{t}Ratio', f'{x.ratio:.2f}', 'primary.csv')
        add(f'{t}SystemsAhead', str(x.systems_ahead), 'primary.csv')
        add(f'{t}SystemsBehind', str(x.systems_behind), 'primary.csv')
    add('SelectionOnPathNum', str(extra['C6']['num']), 'claims.csv C6')
    add('SelectionOnPathDen', str(extra['C6']['den']), 'claims.csv C6')
    add('SelectionOnPathShare', f"{100 * extra['C6']['share']:.1f}", 'claims.csv C6')
    add('OversizeWeakDimTwo', f"{100 * extra['C8']['oversize_weak']:.1f}", 'claims.csv C8')
    add('OversizeTrajDimTwo', f"{100 * extra['C8']['oversize_traj']:.1f}", 'claims.csv C8')
    frame = pd.DataFrame(out)
    if frame.macro.duplicated().any() or not frame.macro.str.fullmatch('[A-Za-z]+').all():
        raise ValueError('Macro names must be unique and alphabetic')
    tex = '% Generated by analysis/scripts/aggregate/q9a_claims.py; do not edit.\n' + ''.join(
        f'\\newcommand{{\\{m}}}{{{v}}}\n' for m, v in zip(frame.macro, frame.value))
    return frame, tex


# ----------------------------------------------------------------------------- main
def run(args):
    out = Path(args.output_dir)
    if out.exists():
        raise FileExistsError('Refusing to overwrite ' + str(out))
    rng = np.random.default_rng(SEED)
    cells, choices, refs, meta = load(args.input_dir)
    present = {(float(s), float(r)) for s, r in cells.loc[cells.sigma > 0, ['sigma', 'rho']].itertuples(index=False)}
    full = present == NOISY_CONDITIONS and set(cells.realization) == {1, 2, 3} and set(cells.initial_condition_set) == {1, 2}
    if args.strict and (not full or meta['protocol'] != 'Q9'):
        raise ValueError('Strict mode needs the full Q9 population')
    allm = long_table(cells, choices, refs)
    claims, prim, sec, extra = evaluate(cells, choices, refs, allm, rng)
    rob = robustness(cells, choices, refs, rng)
    base_sign = prim.set_index('test')['diff'].gt(0)
    rob['sign_flip'] = [bool((r['diff'] > 0) != base_sign[r.test]) for _, r in rob.iterrows()]
    rates, bycond, persys, d34, cost, missing = descriptive(allm, choices, cells, rng)
    mac, tex = macros(rates, prim, extra)
    out.mkdir(parents=True)
    for name, f in dict(claims=claims, primary=prim, secondary=sec, robustness=rob, rates=rates, by_condition=bycond,
                        per_system=persys, dim34=d34, cost=cost, missing=missing, macros=mac).items():
        f.to_csv(out / f'{name}.csv', index=False)
    (out / 'macros.tex').write_text(tex, encoding='utf8')
    md = dict(protocol='Q9-A', input=str(args.input_dir), build=meta, full_population=bool(full), strict=args.strict,
              seed=SEED, bootstrap=B, robustness_sign_flips=int(rob.sign_flip.sum()),
              claims={r.claim: bool(r.verdict) for r in claims.itertuples()})
    (out / 'metadata.json').write_text(json.dumps(md, indent=1, default=str) + '\n', encoding='utf8')
    return md


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--strict', action='store_true')
    print(json.dumps(run(p.parse_args()), indent=1, default=str))
