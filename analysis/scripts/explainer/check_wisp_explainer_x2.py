"""Strict Q7 rule check on featured Q5 dim-one inputs, never Q7 result files."""
import json
import subprocess
from pathlib import Path
import numpy as np
from check_wisp_explainer_js import main as prior_checks
ROOT=Path(__file__).resolve().parents[3]

def main():
    if prior_checks():return 1
    live=json.loads((ROOT/'explainer/wisp/data/live.json').read_text(encoding='utf8'))
    cases=[f['stop_reference'] for f in live['featured'] if 'stop_reference' in f]
    script="const fs=require('fs'),W=require(process.argv[1]);const cases=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(cases.map(r=>W.significancePath(r.t,r.x,r.threshold))));"
    run=subprocess.run(['node','-e',script,str(ROOT/'explainer/wisp/src/compute.js')],input=json.dumps(cases),capture_output=True,text=True,check=True,timeout=120)
    for feature,actual in zip([f for f in live['featured'] if 'stop_reference' in f],json.loads(run.stdout),strict=True):
        reference=feature['stop_reference']
        assert len(actual['steps'])==reference['stop_step'],feature['cell_id']
        assert [s['support'] for s in actual['steps']]==reference['supports'],feature['cell_id']
        np.testing.assert_allclose(actual['variance'],reference['variance'],rtol=1e-9,atol=1e-16)
        print('PASS significance rule',feature['cell_id'],'stop step',len(actual['steps']))
    return 0

if __name__=='__main__':raise SystemExit(main())
