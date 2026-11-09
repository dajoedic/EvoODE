"""Assemble explainer/wisp/process/ into one self-contained page: explainer/wisp/dist/wisp_process.html.

Data: explainer/wisp/process/data.json from build_wisp_process_data.py and results.json from
build_wisp_process_results.py (run those first when inputs change).
Check: node explainer/wisp/process/check_core.cjs (browser core vs Python weak space).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'explainer/wisp/process'
OUT = ROOT / 'explainer/wisp/dist/wisp_process.html'


def main():
    page = (SRC / 'index.html').read_text(encoding='utf8')
    for key, name in (('/*STYLE*/', 'style.css'), ('/*DATA*/', 'data.json'), ('/*RESULTS*/', 'results.json'), ('/*CORE*/', 'core.js'), ('/*APP*/', 'app.js')):
        text = (SRC / name).read_text(encoding='utf8')
        if name.endswith('.js') or name.endswith('.json'):
            text = text.replace('</script', '<\\/script')
        assert page.count(key) == 1, key
        page = page.replace(key, text)
    OUT.write_text(page, encoding='utf8')
    print('wrote', OUT, OUT.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
