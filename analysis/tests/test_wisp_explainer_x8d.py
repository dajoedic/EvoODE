"""Page-3 decimal equations and browser geometry acceptance contract."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def test_decimal_equations_preserve_small_coefficients_and_constants():
    script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(process.argv[1],'utf8');
for(const language of ['de','en']){
 const c={language,terms:['1','u','u²','u³','sin u','cos u']};vm.createContext(c);
 vm.runInContext(source.slice(source.indexOf('function workNumber('),source.indexOf('function workTrace(')),c);
 assert.equal(c.workEquation([0],[10]),'du/dt = 10');
 assert.equal(c.workEquation([0],[-10]),'du/dt = −10');
 assert.equal(c.workEquation([],[]),'du/dt = 0');
 for(const v of [-.0000275123,1.234567e-12,123456789,0]){
  const formatted=c.workNumber(v);assert(!/[eE×]/.test(formatted));
  assert.equal(Number(formatted.replace('−','-').replace(',','.')),Number(v.toPrecision(3)));
 }
 assert(!/×|[eE][+-]\d/.test(c.workTruth('0.79*x_0*(1 - 0.0134589502018843*x_0)')));
}
"""
    run = subprocess.run(['node', '-e', script, str(ROOT/'explainer/wisp/src/app.js')],
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr


def test_browser_measures_equations_against_their_column():
    # The no-layout DOM harness checks term boundaries. Real width assertions
    # are part of every DE/EN frame in the browser fit checker.
    source = (ROOT/'explainer/wisp/src/pages.js').read_text(encoding='utf8')
    assert 'rect.width<=container.width+1&&e.scrollWidth<=container.width+1' in source
    assert 'workEquations.every(e=>e.ok)' in source
