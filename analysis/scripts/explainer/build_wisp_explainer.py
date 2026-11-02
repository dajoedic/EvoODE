"""Assemble a deterministic, file:// compatible single-file WISP explainer."""
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "explainer/wisp"


def build(base=BASE):
    src = base / "src"
    page = (src / "index.html").read_text(encoding="utf8")
    data = {name: json.loads((base / "data" / f"{name}.json").read_text(encoding="utf8"))
            for name in ("results", "live", "manifest")}
    for key, value in {
        "STYLE": (src / "style.css").read_text(encoding="utf8"),
        "DATA": json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace("<", "\\u003c"),
        "COMPUTE": (src / "compute.js").read_text(encoding="utf8"),
        "APP": (src / "app.js").read_text(encoding="utf8"),
    }.items():
        page = page.replace("<!--" + key + "-->", value)
    output = base / "dist/wisp_explainer.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(page.encode("utf8"))
    print(json.dumps({"output": str(output), "bytes": output.stat().st_size}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE)
    build(parser.parse_args().base)
