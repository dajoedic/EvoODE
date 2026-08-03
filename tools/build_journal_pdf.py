#!/usr/bin/env python3
"""Render docs/projektjournal.md to docs/projektjournal.pdf.

The first PDF versions of the journal were produced by an ad-hoc browser print,
which left no way to reproduce them. This script does the same thing on purpose:
markdown -> styled HTML -> headless Chromium print-to-PDF.

Usage:
    python tools/build_journal_pdf.py [--keep-html]

Requires the `markdown` package and a Chromium-based browser (Chrome or Edge).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "docs" / "projektjournal.md"
TARGET = REPO / "docs" / "projektjournal.pdf"

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }

html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.5;
  color: #1a1a1a;
  max-width: none;
  margin: 0;
}

h1 { font-size: 21pt; margin: 0 0 0.2em; letter-spacing: -0.01em; }
h2 {
  font-size: 15pt;
  margin: 1.6em 0 0.5em;
  padding-bottom: 0.2em;
  border-bottom: 1.5px solid #2c3e50;
  break-after: avoid;
}
h3 {
  font-size: 12pt;
  margin: 1.3em 0 0.4em;
  color: #2c3e50;
  break-after: avoid;
}
h2, h3 { break-inside: avoid; }

p { margin: 0.55em 0; orphans: 3; widows: 3; }

strong { color: #111; }

code {
  font-family: "Cascadia Mono", Consolas, "DejaVu Sans Mono", monospace;
  font-size: 0.88em;
  background: #f2f4f6;
  padding: 0.08em 0.3em;
  border-radius: 3px;
}

pre {
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  padding: 0.7em 0.9em;
  overflow-x: auto;
  break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: 0.85em; }

table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
  font-size: 9.3pt;
  break-inside: avoid;
}
th, td {
  border: 1px solid #d3d8dd;
  padding: 0.34em 0.55em;
  text-align: left;
  vertical-align: top;
}
th { background: #eef1f4; font-weight: 600; }
tr:nth-child(even) td { background: #fafbfc; }

hr { border: none; border-top: 1px solid #dfe3e7; margin: 1.6em 0; }

blockquote {
  margin: 0.8em 0;
  padding: 0.1em 0 0.1em 1em;
  border-left: 3px solid #c8ced4;
  color: #444;
}

ul, ol { margin: 0.5em 0; padding-left: 1.5em; }
li { margin: 0.22em 0; }

a { color: #1a4f8a; text-decoration: none; }
"""

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>projektjournal</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def find_browser() -> str:
    for candidate in BROWSER_CANDIDATES:
        if os.path.sep in candidate or ":" in candidate:
            if Path(candidate).exists():
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    raise SystemExit(
        "No Chromium-based browser found. Install Chrome or Edge, or extend "
        "BROWSER_CANDIDATES in this script."
    )


def render_html(md_text: str) -> str:
    import markdown

    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    return HTML.format(css=CSS, body=body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-html", action="store_true", help="keep the intermediate HTML file")
    args = parser.parse_args()

    if not SOURCE.exists():
        raise SystemExit(f"missing source: {SOURCE}")

    html = render_html(SOURCE.read_text(encoding="utf-8"))

    tmpdir = Path(tempfile.mkdtemp(prefix="journal_pdf_"))
    html_path = tmpdir / "projektjournal.html"
    html_path.write_text(html, encoding="utf-8")

    browser = find_browser()
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={TARGET}",
        html_path.as_uri(),
    ]
    print("browser:", browser)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not TARGET.exists():
        sys.stderr.write(result.stdout + "\n" + result.stderr + "\n")
        raise SystemExit(f"PDF generation failed (exit {result.returncode})")

    size_kb = TARGET.stat().st_size / 1024
    print(f"wrote {TARGET.relative_to(REPO)} ({size_kb:.0f} kB)")

    if args.keep_html:
        print("html:", html_path)
    else:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
