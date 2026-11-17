"""Q9-ABL control 1 (protocol §4): Q9-ABL records must reproduce the Q8 records bit-for-bit on shared data sets.

Compares, per (cell_id, arm, candidate_id): fitted parameters, training loss, clean reconstruction and generalization
loss (bit patterns of the floats), loss evaluations and ODE solves. Every Q9-ABL record whose cell Q8 also ran must
find its Q8 twin. Exit code 1 on any difference.

Usage: python check_q9abl_q8_identity.py <q9abl records dir or jsonl> [<q8 records dir>]
"""
import glob
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
src = Path(sys.argv[1])
q8dir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT/'outputs/sideproject_q8_512dd5bd534530327b1f5fed3e7892a1e0950016/out_final/out'
files = [src] if src.is_file() else sorted(src.glob('index_*.jsonl'))
ARMS = {'no_foba', 'random_start', 'no_refit', 'C10', 'A1000'}


def bits(x):
    if isinstance(x, list):
        return [bits(v) for v in x]
    return struct.pack('>d', float(x)).hex() if x is not None else None


def view(r):
    m = r['fit_meta'] if isinstance(r['fit_meta'], dict) else {}
    return dict(params=bits(r['params']), train=bits(r['training']['loss']),
                rec=bits(r['reconstruction']['loss']), gen=bits(r['generalization']['loss']),
                loss_evals=m.get('loss_evals'), ode_solves=m.get('ode_solves'))


new = {}
for f in files:
    for line in open(f, encoding='utf8'):
        r = json.loads(line)
        new[r['cell_id'], r['arm'], r['candidate_id']] = view(r)
cells = {k[0] for k in new}
old = {}
for f in glob.glob(str(q8dir/'index_*.jsonl')):
    for line in open(f, encoding='utf8'):
        if '"arm"' not in line:
            continue
        r = json.loads(line)
        if r['arm'] in ARMS and r['cell_id'] in cells:
            old[r['cell_id'], r['arm'], r['candidate_id']] = view(r)
shared = [k for k in new if k[0] in {c for c, _, _ in old}]
diff = [k for k in shared if k not in old or new[k] != old[k]]
print(f'Q9-ABL records {len(new)}, on Q8 cells {len(shared)}, Q8 twins {sum(k in old for k in shared)}, '
      f'differences {len(diff)}')
for k in diff[:10]:
    print('DIFF', k, {f: (new[k][f], old.get(k, {}).get(f)) for f in new[k] if new[k][f] != old.get(k, {}).get(f)})
by_arm = {}
for k in shared:
    by_arm.setdefault(k[1], [0, 0])[0] += 1
    by_arm[k[1]][1] += k not in diff
print('identical per arm:', {a: f'{v[1]}/{v[0]}' for a, v in sorted(by_arm.items())})
sys.exit(1 if diff or not shared else 0)
