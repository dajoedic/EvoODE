"""Shared helpers for Gate 2A acceptance scripts."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from experiments.annihilator_gate2a_v3.config import RESULTS


ACCEPTANCE_DIR = RESULTS / "acceptance"


def parser() -> argparse.ArgumentParser:
    out = argparse.ArgumentParser()
    out.add_argument("--limit", action="store_true", help="Run a short developer check instead of the full acceptance load.")
    return out


def write_result(name: str, payload: dict) -> None:
    ACCEPTANCE_DIR.mkdir(parents=True, exist_ok=True)
    path = ACCEPTANCE_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"wrote {path}")


def max_abs(values) -> float:
    return float(np.max(np.abs(np.asarray(values, dtype=float))))


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.seconds = time.perf_counter() - self.start
