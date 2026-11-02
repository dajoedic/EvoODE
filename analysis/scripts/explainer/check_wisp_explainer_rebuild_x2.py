"""Run two complete display exports/assemblies and require byte identity."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
root=Path(__file__).resolve().parents[3];out=root/'outputs/wisp_explainer_checks';out.mkdir(exist_ok=True)
artifacts=[root/'explainer/wisp/data'/f'{n}.json' for n in ('live','results','manifest')]+[root/'explainer/wisp/dist/wisp_explainer.html']
runs=[]
for iteration in range(2):
    start=time.monotonic()
    for name in ('build_wisp_explainer_x2.py','build_wisp_explainer_html_x2.py'):
        result=subprocess.run([sys.executable,str(root/'analysis/scripts/explainer'/name)],capture_output=True,text=True,timeout=850)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        print(result.stdout.strip(),flush=True)
    runs.append(dict(seconds=time.monotonic()-start,files={str(p.relative_to(root)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in artifacts}))
assert runs[0]['files']==runs[1]['files']
(out/'wp_x2_rebuild.json').write_text(json.dumps(dict(byte_identical=True,runs=runs),indent=2),encoding='utf8')
print('BYTE IDENTICAL',runs,flush=True)
