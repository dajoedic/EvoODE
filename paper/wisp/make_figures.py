"""Figures for the WISP manuscript draft (reads paper/wisp/data/, writes paper/wisp/figures/)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
D, F = HERE / 'data', HERE / 'figures'
F.mkdir(exist_ok=True)

mpl.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7, 'xtick.labelsize': 6.3, 'ytick.labelsize': 6.3,
    'legend.fontsize': 6.3, 'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': '#52514e', 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.labelcolor': '#0b0b0b',
    'text.color': '#0b0b0b', 'pdf.fonttype': 42, 'savefig.dpi': 300, 'axes.titleweight': 'bold',
    'axes.titlelocation': 'left', 'legend.frameon': False,
})
INK, INK2, MUTED, GRID = '#0b0b0b', '#52514e', '#8a8984', '#e4e3df'
COL = {'C1000': '#2a78d6', 'wsindy': '#eb6834', 'weak_sindy': '#1baf7a', 'sindy': '#eda100', 'e_sindy': '#e87ba4'}
LAB = {'C1000': 'WISP', 'wsindy': 'WSINDy (MATLAB)', 'weak_sindy': 'Weak-SINDy', 'sindy': 'SINDy', 'e_sindy': 'E-SINDy'}
METHODS = ['C1000', 'wsindy', 'weak_sindy', 'sindy', 'e_sindy']
STRATA = ['dim1_exact', 'dim2_exact', 'dim1_surrogate', 'dim2_surrogate']
SLAB = {'dim1_exact': 'dim 1\nexact', 'dim2_exact': 'dim 2\nexact', 'dim1_surrogate': 'dim 1\nsurrogate',
        'dim2_surrogate': 'dim 2\nsurrogate', 'dim3_feasible': 'dim 3\n52, 61', 'dim3_infeasible': 'dim 3\n54–59'}
FULL, COLW = 7.0, 3.42


def save(fig, name):
    fig.savefig(F / f'{name}.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(F / f'{name}.png', bbox_inches='tight', pad_inches=0.02, dpi=200)
    plt.close(fig)


def panel_label(ax, s, x=-0.16, y=1.06):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=9, fontweight='bold', va='bottom', ha='left')


def ygrid(ax):
    ax.yaxis.grid(True, color=GRID, lw=0.5)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# Figure 2 - worked example
# ---------------------------------------------------------------------------
def fig_example():
    ex = json.loads((D / 'example.json').read_text())
    t, x = np.array(ex['observed_t']), np.array(ex['observed_x'])
    tt = np.array(ex['tt'])
    tr, te = np.array(ex['truth_train']), np.array(ex['truth_test'])
    wtr, wte = np.array(ex['wisp_train']), np.array(ex['wisp_test'])
    str_, ste = np.array(ex['ws_train']), np.array(ex['ws_test'])
    names = {int(k): v for k, v in ex['term_names'].items()}
    steps, cands = ex['steps'], ex['candidates']

    fig = plt.figure(figsize=(FULL, 4.55))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.35, 1.0], height_ratios=[1, 1], hspace=0.62, wspace=0.42)

    # (a) data
    ax = fig.add_subplot(gs[0, 0])
    cx = ['#2a78d6', '#eb6834']
    for j, lab in enumerate(['$x_0$ (prey)', '$x_1$ (predator)']):
        ax.plot(tt, tr[:, j], color=cx[j], lw=0.8, alpha=0.35)
        ax.plot(t, x[:, j], 'o', ms=1.6, color=cx[j], mew=0, label=lab)
    ax.set_xlabel('time $t$')
    ax.set_ylabel('state')
    ax.set_title('Observed training data')
    ax.set_ylim(-0.2, 8.4)
    ax.legend(loc='upper right', handletextpad=0.2, borderaxespad=0.0, markerscale=2.2)
    ax.text(0.02, 0.99, f'{len(t)}/512 samples\nσ = 5 %', transform=ax.transAxes,
            va='top', fontsize=6, color=INK2)
    panel_label(ax, 'A')

    # (b) growth path as a support map + stop statistic
    sub = gs[0:2, 1].subgridspec(2, 1, height_ratios=[1, 3.3], hspace=0.08)
    axs = fig.add_subplot(sub[0])
    axm = fig.add_subplot(sub[1], sharex=axs)
    n = len(steps)
    xs = np.arange(n)
    for e, c in enumerate(cx):
        r = np.array([s['eq'][e]['max_ratio'] for s in steps])
        axs.plot(xs, r, '-o', color=c, ms=2.8, lw=1.0, mew=0, label=f'eq. $\\dot x_{e}$')
    axs.axhline(6.635, color=INK, lw=0.7, ls=(0, (3, 2)))
    axs.text(n - 0.6, 6.635 * 1.25, r'$\chi^2_{1,0.99}=6.635$', ha='right', va='bottom', fontsize=6)
    axs.set_yscale('log')
    axs.set_ylim(0.6, 1e5)
    axs.set_ylabel('max gain /\nnoise gain', fontsize=6.3)
    axs.set_title('Growth path and stop', pad=4)
    axs.legend(loc='upper right', ncol=2, bbox_to_anchor=(1.0, 1.02), handlelength=1.2, columnspacing=0.8)
    plt.setp(axs.get_xticklabels(), visible=False)
    panel_label(axs, 'B', x=-0.2, y=1.12)
    # rows: equation 1 terms then equation 2 terms that ever appear
    used = [sorted({i for s in steps for i in s['support'][e]}) for e in range(2)]
    rows = [(e, i) for e in range(2) for i in used[e]]
    truth = {(0, i) for i, nm in names.items() if nm in ('u1', 'u1*u2')} | \
            {(1, i) for i, nm in names.items() if nm in ('u2', 'u1*u2')}
    for r_i, (e, i) in enumerate(rows):
        y = len(rows) - 1 - r_i
        for s_i, s in enumerate(steps):
            on = i in s['support'][e]
            prev = s_i > 0 and i in steps[s_i - 1]['support'][e]
            if on:
                axm.add_patch(Rectangle((s_i - 0.42, y - 0.38), 0.84, 0.76, color=cx[e],
                                        alpha=1.0 if (e, i) in truth else 0.45, lw=0))
            elif prev:
                axm.plot(s_i, y, marker='x', color=INK2, ms=3.6, mew=0.9)
        lab = (names[i].replace('u1', 'x_0').replace('u2', 'x_1').replace('*', r'\,')
               .replace('cos', r'\cos').replace('sin', r'\sin'))
        axm.text(-0.75, y, f'${lab}$', ha='right', va='center', fontsize=6.3,
                 fontweight='bold' if (e, i) in truth else 'normal',
                 color=INK if (e, i) in truth else INK2)
    split = len(rows) - len(used[0]) - 0.5
    axm.axhline(split, color=INK2, lw=0.5)
    axm.text(-0.4, len(rows) - 1, r'equation $\dot x_0$', ha='left', va='center', fontsize=6.5, color=cx[0],
             fontweight='bold')
    axm.text(-0.4, len(rows) - len(used[0]) - 2, r'equation $\dot x_1$', ha='left', va='center', fontsize=6.5,
             color=cx[1], fontweight='bold')
    axm.set_ylim(-0.7, len(rows) - 0.3)
    axm.set_xlim(-0.6, n - 0.4)
    axm.set_yticks([])
    axm.spines['left'].set_visible(False)
    axm.set_xticks(xs)
    axm.set_xticklabels([str(i) for i in xs])
    axm.set_xlabel('path state (0 = empty model)')
    ch = next(i for i, c in enumerate(cands) if c['candidate_id'] == ex['chosen']) + 1
    axm.add_patch(Rectangle((ch - 0.5, -0.62), 1.0, len(rows) - 0.76, fill=False, ec=INK, lw=0.9))
    axm.text(ch, len(rows) - 0.32, 'stop', ha='center', va='bottom', fontsize=6, fontweight='bold')
    h = [Rectangle((0, 0), 1, 1, color=INK2), Rectangle((0, 0), 1, 1, color=INK2, alpha=0.45),
         Line2D([], [], marker='x', color=INK2, ls='', ms=3.6, mew=0.9)]
    axm.legend(h, ['true term active', 'spurious term active', 'removed by backward step'], loc='lower center',
               bbox_to_anchor=(0.5, -0.2), ncol=3, handlelength=1.0, columnspacing=1.0)

    # (c) candidate selection: trajectory BIC and weak BIC, two stacked axes
    sub2 = gs[0, 2].subgridspec(2, 1, hspace=0.15)
    a1, a2 = fig.add_subplot(sub2[0]), fig.add_subplot(sub2[1])
    k = np.arange(1, len(cands) + 1)
    tb = np.array([c['traj_bic'] for c in cands])
    wb = np.array([c['weak_bic'] for c in cands])
    colors = [COL['C1000'] if c['candidate_id'] == ex['chosen'] else '#b9c9de' for c in cands]
    a1.bar(k, tb - tb.min(), color=colors, width=0.7)
    a2.bar(k, wb - wb.min(), color=colors, width=0.7)
    for a, v in ((a1, tb), (a2, wb)):
        a.plot(k[int(np.argmin(v))], 0, marker='^', color=COL['C1000'], ms=4, clip_on=False, zorder=4)
    a1.set_ylabel('Δ trajectory\nBIC', fontsize=6.3)
    a2.set_ylabel('Δ weak\nBIC', fontsize=6.3)
    plt.setp(a1.get_xticklabels(), visible=False)
    a2.set_xticks(k)
    a2.set_xlabel('candidate (path state)')
    a1.set_title('Choosing the size', pad=4)
    for a in (a1, a2):
        ygrid(a)
        a.set_xlim(0.3, len(cands) + 0.7)
    panel_label(a1, 'C', x=-0.3, y=1.12)

    # (d) chosen model vs truth (equations) + generalization
    ax = fig.add_subplot(gs[1, 0])
    for j in range(2):
        ax.plot(tt, te[:, j], color=MUTED, lw=2.4, alpha=0.5, solid_capstyle='round')
        ax.plot(tt, wte[:, j], color=cx[j], lw=0.9, ls=(0, (4, 1.5)))
    ax.set_xlabel('time $t$')
    ax.set_ylabel('state')
    ax.set_title('Unseen initial condition')
    hh = [Line2D([], [], color=MUTED, lw=2.4, alpha=0.5), Line2D([], [], color=INK2, lw=0.9, ls=(0, (4, 1.5)))]
    c = next(c for c in cands if c['candidate_id'] == ex['chosen'])
    ax.legend(hh, ['true system', f'WISP model ($R^2$ = {c["gen_r2"]:.3f})'], loc='upper right',
              borderaxespad=0.1)
    ax.set_ylim(0, max(te.max(), np.nanmax(wte)) * 1.45)
    panel_label(ax, 'D')

    ax = fig.add_subplot(gs[1, 2])
    ax.axis('off')
    p = c['params']
    lines = [
        (r'$\bf{True\ system}$', INK),
        (r'$\dot x_0 = 1.840\,x_0 - 1.450\,x_0x_1$', INK),
        (r'$\dot x_1 = -3.000\,x_1 + 1.620\,x_0x_1$', INK),
        (r'$\bf{WISP}$ (4 terms, chosen by trajectory BIC)', COL['C1000']),
        (rf'$\dot x_0 = {p[0]:.3f}\,x_0 {p[1]:+.3f}\,x_0x_1$', INK),
        (rf'$\dot x_1 = {p[2]:.3f}\,x_1 {p[3]:+.3f}\,x_0x_1$', INK),
        (r'$\bf{WSINDy}$ (MATLAB original, same data)', COL['wsindy']),
        (rf'{sum(len(e) for e in ex["ws_coef"])} terms; reconstruction $R^2$ = {ex["ws_rec"]:.1f},', INK),
        (rf'generalization $R^2$ = {ex["ws_gen"]:.1f}', INK),
    ]
    yy = 1.0
    for i, (s, col) in enumerate(lines):
        if i in (3, 6):
            yy -= 0.07
        ax.text(0.0, yy, s, transform=ax.transAxes, fontsize=6.6, color=col, va='top')
        yy -= 0.105
    panel_label(ax, 'E', x=-0.12, y=1.0)
    save(fig, 'fig2_example')


# ---------------------------------------------------------------------------
# Figure 3 - main comparison
# ---------------------------------------------------------------------------
def fig_main():
    s = pd.read_csv(D / 'summary_noisy.csv')
    fig, axes = plt.subplots(1, 3, figsize=(FULL, 2.25), gridspec_kw=dict(width_ratios=[2, 4, 4], wspace=0.28))
    specs = [('structure', 'Exact structure', ['dim1_exact', 'dim2_exact']),
             ('rec', 'Reconstruction ($R^2>0.9$)', STRATA),
             ('gen', 'Generalization ($R^2>0.9$)', STRATA)]
    w = 0.16
    for ax, (m, title, strata), lab in zip(axes, specs, 'ABC'):
        for i, meth in enumerate(METHODS):
            for j, st in enumerate(strata):
                r = s[(s.method == meth) & (s.stratum == st) & (s.metric == m)].iloc[0]
                xpos = j + (i - 2) * w
                ax.bar(xpos, 100 * r.rate, width=w * 0.86, color=COL[meth], lw=0)
                ax.plot([xpos, xpos], [100 * r.lo, 100 * r.hi], color=INK, lw=0.5)
                if meth == 'C1000':
                    ax.text(xpos, 100 * r.hi + 2, f'{100 * r.rate:.0f}', ha='center', va='bottom', fontsize=5.6,
                            color=INK, fontweight='bold')
        ax.set_xticks(range(len(strata)))
        ax.set_xticklabels([SLAB[x] for x in strata])
        ax.set_ylim(0, 108)
        ax.set_title(title)
        ygrid(ax)
        panel_label(ax, lab, x=-0.2 if m == 'structure' else -0.1)
    axes[0].set_ylabel('share of noisy cells (%)')
    h = [Rectangle((0, 0), 1, 1, color=COL[m]) for m in METHODS]
    fig.legend(h, [LAB[m] for m in METHODS], loc='upper center', ncol=5, bbox_to_anchor=(0.5, 1.09),
               handlelength=1.0, columnspacing=1.6)
    save(fig, 'fig3_main')


# ---------------------------------------------------------------------------
# Figure 4 - by condition
# ---------------------------------------------------------------------------
def fig_conditions():
    b = pd.read_csv(D / 'by_condition.csv')
    conds = ['clean', 's0.01_r0.0', 's0.01_r0.5', 's0.05_r0.0', 's0.05_r0.5']
    clab = ['clean', '1 %', '1 %\n½ gone', '5 %', '5 %\n½ gone']
    fig, axes = plt.subplots(2, 4, figsize=(FULL, 3.2), sharey=True, gridspec_kw=dict(hspace=0.5, wspace=0.12))
    for col, st in enumerate(STRATA):
        for row, m in enumerate(['structure', 'gen']):
            ax = axes[row, col]
            if m == 'structure' and 'surrogate' in st:
                ax.text(0.5, 0.5, 'no true structure\n(surrogate systems)', ha='center', va='center',
                        transform=ax.transAxes, color=MUTED, fontsize=6.5)
                ax.set_xticks([])
                ax.spines['bottom'].set_visible(False)
                if col == 2:
                    ax.spines['left'].set_visible(True)
                continue
            for meth in METHODS[::-1]:
                g = b[(b.method == meth) & (b.stratum == st) & (b.metric == m)].set_index('condition').reindex(conds)
                ax.plot(range(5), 100 * g.rate, '-o', color=COL[meth], lw=1.6 if meth == 'C1000' else 1.0,
                        ms=3.6 if meth == 'C1000' else 2.6, mew=0, zorder=3 if meth == 'C1000' else 2)
            ax.set_xticks(range(5))
            ax.set_xticklabels(clab, fontsize=5.8)
            ax.set_ylim(-3, 103)
            ygrid(ax)
            ax.axvspan(0.5, 4.5, color='#f3f2ef', zorder=0, lw=0)
            if row == 0:
                ax.set_title(SLAB[st].replace('\n', ' '))
        axes[0, 0].set_ylabel('exact structure (%)')
        axes[1, 0].set_ylabel('generalization\n$R^2>0.9$ (%)')
    for col in range(4):
        axes[1, col].set_title(SLAB[STRATA[col]].replace('\n', ' '))
    panel_label(axes[0, 0], 'A', x=-0.3)
    panel_label(axes[1, 0], 'B', x=-0.3)
    h = [Line2D([], [], color=COL[m], marker='o', ms=3, lw=1.2, mew=0) for m in METHODS]
    fig.legend(h, [LAB[m] for m in METHODS], loc='upper center', ncol=5, bbox_to_anchor=(0.5, 1.03),
               columnspacing=1.6)
    fig.text(0.5, -0.03, 'noise level σ and missing samples (shaded: noisy conditions that enter the pooled rates)',
             ha='center', fontsize=6.3, color=INK2)
    save(fig, 'fig4_conditions')


# ---------------------------------------------------------------------------
# Figure 5 - per-system paired comparison
# ---------------------------------------------------------------------------
def fig_systems():
    p = pd.read_csv(D / 'per_system_noisy.csv')
    w = p[p.method == 'C1000'].set_index('system_id')
    marker = {'dim1_exact': 'o', 'dim2_exact': 's', 'dim1_surrogate': '^', 'dim2_surrogate': 'D',
              'dim3_feasible': 'P', 'dim3_infeasible': 'X'}
    fig, axes = plt.subplots(1, 2, figsize=(COLW * 2 * 0.86, 2.6), gridspec_kw=dict(wspace=0.32))
    rng = np.random.default_rng(3)
    for ax, ref, lab in zip(axes, ['wsindy', 'weak_sindy'], 'AB'):
        r = p[p.method == ref].set_index('system_id')
        common = w.index.intersection(r.index)
        ahead = behind = 0
        for st, mk in marker.items():
            ids = [i for i in common if w.loc[i, 'stratum'] == st]
            if not ids:
                continue
            xv = 100 * r.loc[ids, 'gen'].to_numpy() + rng.uniform(-1.2, 1.2, len(ids))
            yv = 100 * w.loc[ids, 'gen'].to_numpy() + rng.uniform(-1.2, 1.2, len(ids))
            ax.scatter(xv, yv, marker=mk, s=17, facecolor=COL['C1000'] if 'exact' in st else 'white',
                       edgecolor=COL['C1000'], lw=0.8, alpha=0.9, label=SLAB[st].replace('\n', ' '), zorder=3)
        d = w.loc[common, 'gen'] - r.loc[common, 'gen']
        ahead, behind, tie = (d > 0).sum(), (d < 0).sum(), (d == 0).sum()
        ax.plot([-5, 105], [-5, 105], color=MUTED, lw=0.7, ls=(0, (3, 2)), zorder=1)
        ax.fill_between([-5, 105], [-5, 105], 105, color='#eef4fc', zorder=0)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.set_aspect('equal')
        ax.set_xlabel(f'{LAB[ref]}: generalization rate (%)')
        ax.set_ylabel('WISP: generalization rate (%)')
        ax.set_title(f'WISP vs {LAB[ref]}, per system')
        ax.text(98, 12, f'WISP ahead: {ahead} systems\nbehind: {behind}   tied: {tie}', va='bottom', ha='right',
                fontsize=6.2, bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=GRID, lw=0.5))
        panel_label(ax, lab, x=-0.25)
    axes[1].legend(loc='center left', bbox_to_anchor=(1.02, 0.5), handletextpad=0.3, labelspacing=0.6,
                   title='stratum', title_fontsize=6.3)
    save(fig, 'fig5_systems')


# ---------------------------------------------------------------------------
# Figure 6 - ablations and design arms
# ---------------------------------------------------------------------------
def fig_ablation():
    a = pd.read_csv(D / 'arms_noisy.csv')
    arms = [('C1000', 'WISP (final)'), ('no_foba', '– backward step (FoBa)'), ('no_refit', '– trajectory refit'),
            ('random_start', '– weak-form start (random start)'), ('C10', 'bound 10 instead of 1000'),
            ('A1000', 'initial state not estimated')]
    cols = [('dim1_exact', 'structure'), ('dim1_exact', 'gen'), ('dim2_exact', 'structure'), ('dim2_exact', 'gen'),
            ('dim1_surrogate', 'gen'), ('dim2_surrogate', 'gen')]
    ttl = ['dim 1 exact\nstructure', 'dim 1 exact\ngeneralization', 'dim 2 exact\nstructure',
           'dim 2 exact\ngeneralization', 'dim 1 surrogate\ngeneralization', 'dim 2 surrogate\ngeneralization']
    fig, axes = plt.subplots(1, 6, figsize=(FULL, 1.95), sharey=True, gridspec_kw=dict(wspace=0.2))
    for ax, (st, m), title in zip(axes, cols, ttl):
        base = a[(a.method == 'C1000') & (a.stratum == st) & (a.metric == m)].iloc[0]
        ax.axvline(100 * base.rate, color=COL['C1000'], lw=0.7, alpha=0.6)
        for y, (arm, _) in enumerate(arms):
            r = a[(a.method == arm) & (a.stratum == st) & (a.metric == m)]
            if r.empty:
                continue
            r = r.iloc[0]
            yy = len(arms) - 1 - y
            c = COL['C1000'] if arm == 'C1000' else (INK2 if arm in ('C10', 'A1000') else '#e34948')
            ax.plot([100 * r.lo, 100 * r.hi], [yy, yy], color=c, lw=0.7, alpha=0.6)
            ax.plot(100 * r.rate, yy, 'o', color=c, ms=4.2, mew=0)
            ax.text(100 * r.rate, yy + 0.22, f'{100 * r.rate:.0f}', ha='center', va='bottom', fontsize=5.4,
                    color=INK)
        ax.set_xlim(-8, 108)
        ax.set_xticks([0, 50, 100])
        ax.set_title(title, fontsize=6.3, fontweight='normal', loc='center')
        ax.xaxis.grid(True, color=GRID, lw=0.5)
        ax.set_axisbelow(True)
        ax.spines['left'].set_visible(ax is axes[0])
        if ax is not axes[0]:
            ax.tick_params(axis='y', length=0)
    axes[0].set_yticks(range(len(arms)))
    axes[0].set_yticklabels([n for _, n in arms][::-1])
    axes[0].set_ylim(-0.6, len(arms) - 0.3)
    fig.text(0.55, -0.06, 'share of noisy cells (%), 95 % cluster-bootstrap interval over systems', ha='center',
             fontsize=6.3, color=INK2)
    save(fig, 'fig6_ablation')


# ---------------------------------------------------------------------------
# Figure 7 - size selection and cost
# ---------------------------------------------------------------------------
def fig_selection_cost():
    s = pd.read_csv(D / 'size_rules_exact_C1000.csv')
    s = s[(s.sigma > 0) & s.stratum.isin(['dim1_exact', 'dim2_exact'])]
    allc = pd.read_csv(D / 'wisp_choices_all_rules.csv', low_memory=False)
    c = allc[(allc.method == 'C1000') & (allc.size_rule == 'c') & (allc.sigma > 0)]
    fig, axes = plt.subplots(1, 3, figsize=(FULL, 2.05), gridspec_kw=dict(width_ratios=[1.25, 1.0, 1.25],
                                                                          wspace=0.42))
    # (a) size error by rule, dim 2 exact
    ax = axes[0]
    rules = [('a', 'weak BIC', '#8a8984'), ('c', 'trajectory\nBIC (WISP)', COL['C1000'])]
    bins = np.arange(-2, 6)
    g2 = s[s.stratum == 'dim2_exact']
    for i, (rule, lab, col) in enumerate(rules):
        e = g2[g2.size_rule == rule].size_error.dropna().clip(-2, 5).astype(int)
        cnt = np.array([(e == v).sum() for v in bins]) / len(e) * 100
        ax.bar(bins + (i - 0.5) * 0.38, cnt, width=0.36, color=col, label=lab, lw=0)
    ax.set_xticks(bins)
    ax.set_xticklabels([str(v) if v < 5 else '≥5' for v in bins])
    ax.set_xlabel('chosen size − true size (terms)')
    ax.set_ylabel('share of cells (%)')
    ax.set_title('Size choice, dim 2 exact')
    ax.legend(loc='center right', bbox_to_anchor=(1.03, 0.62), handlelength=1.0)
    ygrid(ax)
    panel_label(ax, 'A', x=-0.22)
    # (b) path vs selection
    ax = axes[1]
    for j, st in enumerate(['dim1_exact', 'dim2_exact']):
        g = s[(s.stratum == st) & (s.size_rule == 'c')]
        on = 100 * g.truth_on_path.astype(bool).mean()
        raw = 100 * g.raw.astype(bool).mean()
        ax.bar(j - 0.19, on, width=0.36, color='#b9c9de', lw=0)
        ax.bar(j + 0.19, raw, width=0.36, color=COL['C1000'], lw=0)
        ax.text(j - 0.19, on + 1.5, f'{on:.0f}', ha='center', fontsize=5.8)
        ax.text(j + 0.19, raw + 1.5, f'{raw:.0f}', ha='center', fontsize=5.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['dim 1 exact', 'dim 2 exact'])
    ax.set_ylim(0, 75)
    ax.set_ylabel('share of cells (%)')
    ax.set_title('Path vs selection')
    ax.legend([Rectangle((0, 0), 1, 1, color='#b9c9de'), Rectangle((0, 0), 1, 1, color=COL['C1000'])],
              ['truth among candidates', 'truth chosen (raw)'], loc='upper left')
    ygrid(ax)
    panel_label(ax, 'B', x=-0.25)
    # (c) cost
    ax = axes[2]
    order = ['dim1_exact', 'dim1_surrogate', 'dim2_exact', 'dim2_surrogate', 'dim3_feasible', 'dim3_infeasible']
    data = [c[c.stratum == st].n_candidates.clip(lower=0.8).to_numpy() for st in order]
    rng = np.random.default_rng(1)
    for i, d in enumerate(data):
        ax.scatter(i + rng.uniform(-0.22, 0.22, len(d)), d, s=3, color=COL['C1000'], alpha=0.35, lw=0)
        ax.plot([i - 0.3, i + 0.3], [np.median(d)] * 2, color=INK, lw=1.1)
    ax.set_yscale('log')
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(['1\nexact', '1\nsurr.', '2\nexact', '2\nsurr.', '3\n52, 61', '3\n54–59'], fontsize=5.8)
    ax.set_xlabel('dimension', labelpad=1)
    ax.set_ylabel('candidates = fits per cell')
    ax.set_title('Cost: one trajectory fit per candidate')
    ax.yaxis.grid(True, color=GRID, lw=0.5, which='major')
    ax.set_axisbelow(True)
    panel_label(ax, 'C', x=-0.22)
    save(fig, 'fig7_selection_cost')


# ---------------------------------------------------------------------------
# Figure 8 - calibration of the chi-square stop (Q-Cal)
# ---------------------------------------------------------------------------
def fig_calibration():
    r = pd.read_csv(HERE.parents[1] / 'analysis/data/sideproject_residual_growth/stop_calibration/rates.csv')
    order = ['dim1', 'dim2', 'dim3_feasible', 'dim3_infeasible', 'dim4']
    lab = ['dim 1', 'dim 2', 'dim 3\n52, 61', 'dim 3\n54–59', 'dim 4\n63']
    fig, axes = plt.subplots(1, 2, figsize=(COLW, 1.85), gridspec_kw=dict(width_ratios=[1.45, 1.15], wspace=0.42))
    ax = axes[0]
    w = 0.26
    for i, (rho, col, name) in enumerate([('rho=0.0', '#86b6ef', 'all samples'), ('rho=0.5', COL['C1000'], 'half missing')]):
        for j, st in enumerate(order):
            g = r[(r.stratum == st) & (r.subset == rho)].iloc[0]
            ax.bar(j + (i - 0.5) * w, 100 * g['N1_hat_6.635'], width=w * 0.9, color=col, lw=0,
                   label=name if j == 0 else None)
            ax.plot(j + (i - 0.5) * w, 100 * g['N1_oracle_6.635'], marker='_', color=INK, ms=6, mew=1.0,
                    label='true noise variance' if (i == 0 and j == 0) else None, ls='')
    ax.axhline(1, color='#e34948', lw=0.8, ls=(0, (3, 2)), label='nominal 1 %')
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(lab, fontsize=5.6)
    ax.set_ylabel('false alarms per term (%)')
    ax.set_title('False alarms at the truth', fontsize=6.6)
    ax.legend(loc='upper left', fontsize=5.2, handlelength=1.0, labelspacing=0.3)
    ax.set_ylim(0, 82)
    ygrid(ax)
    panel_label(ax, 'A', x=-0.3)
    ax = axes[1]
    vals = [100 * r[(r.stratum == st) & (r.subset == 'all')].iloc[0]['P1_hat_6.635'] for st in order]
    ax.bar(range(len(order)), vals, color=COL['C1000'], width=0.6, lw=0)
    for j, v in enumerate(vals):
        ax.text(j, v + 1.5, f'{v:.0f}', ha='center', fontsize=5.4)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(['1', '2', '3\n52,61', '3\n54–59', '4'], fontsize=5.0)
    ax.set_xlabel('dimension', fontsize=6, labelpad=1)
    ax.set_ylim(0, 112)
    ax.set_ylabel('detected (%)')
    ax.set_title('Power', fontsize=6.6)
    ygrid(ax)
    panel_label(ax, 'B', x=-0.42)
    save(fig, 'fig8_calibration')


if __name__ == '__main__':
    fig_calibration()
    fig_example()
    fig_main()
    fig_conditions()
    fig_systems()
    fig_ablation()
    fig_selection_cost()
    print('ok')
