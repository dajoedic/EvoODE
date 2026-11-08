"""Opt-in Q-B1 library and Q9 input validation; no benchmark scoring."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pysindy as ps
from pysindy.feature_library.base import x_sequence_or_item

from exploratory.term_relevance.term_relevance import phasec_basis


def legacy_term(name: str) -> str:
    """Translate WISP names to the existing WP-N47 evaluator vocabulary."""
    text = re.sub(r"u(\d+)", lambda m: f"x{int(m[1]) - 1}", name)
    if text.startswith(("sin(", "cos(")):
        return text.replace("(", "(1 ", 1)
    return text.replace("*", " ")


def _function(term, dim):
    # CustomLibrary enumerates argument combinations. Arity=dim selects exactly
    # one combination (the complete state), allowing the canonical column order.
    args = ",".join(f"v{i}" for i in range(dim))
    if term.kind == "constant":
        expression = "np.ones_like(v0)"
    elif term.kind == "monomial":
        expression = "*".join(f"v{i}**{p}" for i, p in enumerate(term.powers) if p)
    else:
        expression = f"np.{term.kind}(v{term.var})"
    # Only internally generated identifiers, integer powers, and fixed functions.
    return eval(f"lambda {args}: {expression}", {"np": np})


class WispLibrary(ps.CustomLibrary):
    """CustomLibrary with exactly phasec_basis columns, including its bias."""

    def __init__(self):
        super().__init__(library_functions=[], function_names=[])

    @x_sequence_or_item
    def fit(self, x_full, y=None):
        dim = x_full[0].shape[x_full[0].ax_coord]
        if dim not in (1, 2, 3, 4):
            raise ValueError(f"unsupported WISP dimension: {dim}")
        terms = phasec_basis(dim)
        self.functions = [_function(term, dim) for term in terms]
        self.function_names = [lambda *args, name=term.name: name for term in terms]
        return super().fit(x_full, y)


def cell_key(row):
    return (int(row["system_id"]), int(row["initial_condition_set"]),
            float(row["noise_sigma"]), float(row["subsample_rho"]), int(row["noise_realization"]))


def q9_cells(path: Path):
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    if len(cells) != 4284 or len({cell_key(c["export"]) for c in cells}) != 4284:
        raise ValueError("expected exactly 4,284 distinct Q9 cells")
    for cell in cells:
        expected = {key: str(cell["export"][key]) for key in ("time_sha256", "state_sha256")}
        if json.loads(cell["observed_data_sha256"]) != expected:
            raise ValueError(f"Q9 embedded hash mismatch: {cell['cell_id']}")
    return {cell_key(c["export"]): c for c in cells}


def select_q9(frame, path: Path, require_all=False):
    cells = q9_cells(path)
    selected = frame.loc[[cell_key(row) in cells for _, row in frame.iterrows()]].copy()
    if len({cell_key(row) for _, row in selected.iterrows()}) != len(selected):
        raise ValueError("export contains duplicate Q9 cell keys")
    if require_all and len(selected) != len(cells):
        raise ValueError(f"export covers {len(selected)} of {len(cells)} Q9 cells")
    for _, row in selected.iterrows():
        cell = cells[cell_key(row)]
        for field in ("time_sha256", "state_sha256", "dimension", "data_condition_fingerprint", "n_observed_points"):
            if str(row[field]) != str(cell["export"][field]):
                raise ValueError(f"Q9/export {field} mismatch: {cell['cell_id']}")
    return selected
