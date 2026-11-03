"""Decision trace gates use the real teaching observations and recorded candidates."""
import json
from pathlib import Path
import subprocess
import sys
import shutil
import uuid
import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'


@pytest.fixture
def tmp_path():
    parent = ROOT/'outputs/wisp_x8c'
    parent.mkdir(parents=True, exist_ok=True)
    path = (parent/('support_failure_'+uuid.uuid4().hex)).resolve()
    assert path.is_relative_to(parent.resolve())
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path)


def test_compressed_trace_matches_full_design_and_recording():
    run = subprocess.run(['node', str(ROOT/'analysis/scripts/explainer/check_wisp_work.cjs'),
                          str(BASE)], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr


def test_build_refuses_a_changed_recorded_support(tmp_path):
    # Start with the actual exported record, then visibly corrupt one support.
    live = json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    live['featured'][0]['path'][0]['active_idxs'] = [[2]]
    (tmp_path/'src').mkdir()
    (tmp_path/'data').mkdir()
    for name in ('compute.js', 'app.js'):
        (tmp_path/'src'/name).write_bytes((BASE/'src'/name).read_bytes())
    (tmp_path/'data/live.json').write_text(json.dumps(live), encoding='utf8')
    run = subprocess.run([sys.executable, str(ROOT/'analysis/scripts/explainer/build_wisp_explainer_html_x2.py'),
                          '--base', str(tmp_path)], capture_output=True, text=True, timeout=30)
    assert run.returncode != 0
    assert 'Teaching path differs from recorded supports' in run.stderr
    assert not (tmp_path/'dist/wisp_explainer.html').exists()


def test_truth_stroke_and_caption_have_browser_acceptance_gates():
    css = (BASE/'src/pages.css').read_text(encoding='utf8')
    assert '#p-challenge .series-truth{stroke:var(--truth);stroke-width:2.5;stroke-dasharray:5 4}' in css
    assert '#challenge-truth small.caption{font-family:system-ui,sans-serif;font-size:13px;color:var(--muted)' in css
    js = (BASE/'src/pages.js').read_text(encoding='utf8')
    assert "['fontFamily','fontSize','color'].every(k=>label[k]===caption[k])" in js
    assert 'solutionStyle.truthStroke>=2.5' in js
    assert 'i<window.WispWork.frames.length' in js
