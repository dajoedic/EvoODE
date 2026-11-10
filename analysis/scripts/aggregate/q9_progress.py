"""Q9 progress per dimension, read from the Orion job (read-only).

Each Q9 shard is one cell; shard index i is line i of the cost-descending unit list. The pod's completion index
says which shard it ran, its phase whether that shard is done or still running. Dimension comes from the system
id in the cell name via benchmarks/data/strogatz_extended.json.

Usage: python analysis/scripts/aggregate/q9_progress.py [--json]
Output: a table on stdout; with --json also outputs/q9_progress/q9_progress.json.
"""
import argparse
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UNITS = ROOT / 'outputs/sideproject_q9_inputs/grid/q9_grid.shards_cost_desc.txt'
SYSTEMS = ROOT / 'benchmarks/data/strogatz_extended.json'
OUT = ROOT / 'outputs/q9_progress/q9_progress.json'
JOB, NS = 'evoode-sideproject-q9', 'scch-das'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    units = UNITS.read_text(encoding='utf8').split()
    dim_of = {int(s['id']): int(s['dim']) for s in json.loads(SYSTEMS.read_text(encoding='utf8'))}
    dims = [dim_of[int(u[3:7])] for u in units]
    pods = json.loads(subprocess.run(['oc', 'get', 'pods', '-n', NS, '-l', f'job-name={JOB}', '-o', 'json'],
                                     capture_output=True, text=True, check=True).stdout)['items']
    state, since = {}, {}
    for p in pods:
        i = int(p['metadata']['annotations']['batch.kubernetes.io/job-completion-index'])
        ph = p['status']['phase']
        if ph == 'Succeeded':
            state[i] = 'done'
        elif ph in ('Running', 'Pending') and state.get(i) != 'done':
            state[i] = 'running'
            since[i] = p['status'].get('startTime')
        elif ph == 'Failed' and i not in state:
            state[i] = 'failed'
    rows = defaultdict(Counter)
    for i, d in enumerate(dims):
        rows[d]['total'] += 1
        rows[d][state.get(i, 'open')] += 1
    now = datetime.now(timezone.utc)
    oldest = {}
    for i, s in since.items():
        if s:
            h = (now - datetime.fromisoformat(s.replace('Z', '+00:00'))).total_seconds() / 3600
            oldest[dims[i]] = max(oldest.get(dims[i], 0), h)
    table = []
    for d in sorted(rows):
        r = rows[d]
        table.append({'dim': d, 'total': r['total'], 'done': r['done'], 'running': r['running'],
                      'open': r['open'], 'failed': r['failed'], 'oldest_running_h': round(oldest.get(d, 0), 1)})
    tot = {k: sum(r[k] for r in table) for k in ('total', 'done', 'running', 'open', 'failed')}
    print(f'Q9 progress {now:%Y-%m-%d %H:%M} UTC')
    print(f"{'dim':>4} {'total':>6} {'done':>6} {'%':>6} {'running':>8} {'open':>6} {'failed':>7} {'oldest run h':>13}")
    for r in table:
        print(f"{r['dim']:>4} {r['total']:>6} {r['done']:>6} {100 * r['done'] / r['total']:>5.1f}% {r['running']:>8} {r['open']:>6} {r['failed']:>7} {r['oldest_running_h']:>13}")
    print(f"{'all':>4} {tot['total']:>6} {tot['done']:>6} {100 * tot['done'] / tot['total']:>5.1f}% {tot['running']:>8} {tot['open']:>6} {tot['failed']:>7}")
    if args.json:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({'utc': now.isoformat(timespec='minutes'), 'dims': table, 'all': tot}, indent=1), encoding='utf8')
        print('wrote', OUT)


if __name__ == '__main__':
    main()
