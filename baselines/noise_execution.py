"""Atomic per-fit persistence for the C-6 platform entry point (no fitting logic)."""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import tempfile
from pathlib import Path

CELL_FIELDS = ("system_id", "initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization")


def cell_key(row):
    source = row.get("initial_condition_set", row.get("source_initial_condition_set"))
    return (int(row["system_id"]), int(source), float(row["noise_sigma"]),
            float(row["subsample_rho"]), int(row["noise_realization"]))


def unit_key(row, config_id=None, repetition=None):
    if config_id is None:
        config_id = row.get("odeformer_config_id") if row["method"] == "odeformer" else row["method"]
    if repetition is None:
        repetition = row["odeformer_noise_repetition"] if row["method"] == "odeformer" else row["pysr_seed"]
    return (*cell_key(row), str(config_id), int(repetition))


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def atomic_write(path, content, replace=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique names also tolerate two infrastructure attempts briefly overlapping.
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            # Same-directory hard-link publication is atomic on NFS/NTFS and,
            # unlike replace(), cannot clobber a completed retry's unit.
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_unit(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    body = payload["body"]
    if payload["sha256"] != digest(body):
        raise ValueError(f"Incomplete/corrupt checkpoint: {path}")
    record, check = body["record"], body["export_check"]
    required = {"status", "method", "method_config", "observed_data_sha256", "image_id", "git_hash"}
    if not required <= record.keys() or record["status"] not in {"success", "error"}:
        raise ValueError(f"Incomplete record: {path}")
    if list(unit_key(record)) != body["key"] or cell_key(check) != cell_key(record):
        raise ValueError(f"Checkpoint key mismatch: {path}")
    return body


def rng_state():
    import numpy as np
    state = np.random.get_state()
    result = dict(python=random.getstate(), numpy=[state[0], state[1].tolist(), *state[2:]])
    torch = sys.modules.get("torch")
    if torch is not None:
        result["torch"] = torch.get_rng_state().tolist()
    return result


def restore_rng(state):
    import numpy as np
    python = state["python"]
    random.setstate((python[0], tuple(python[1]), python[2]))
    numpy = state["numpy"]
    np.random.set_state((numpy[0], np.array(numpy[1], dtype="uint32"), *numpy[2:]))
    if "torch" in state:
        torch = sys.modules.get("torch")
        if torch is None:
            raise ValueError("ODEFormer checkpoint requires torch RNG restoration")
        torch.set_rng_state(torch.tensor(state["torch"], dtype=torch.uint8))


class UnitJournal:
    def __init__(self, output_dir, context, git_commit, image_id):
        self.directory = Path(output_dir) / "units"
        self.context = context
        self.git_commit = git_commit
        self.image_id = image_id
        self.pending_rng = None
        self.seen_configs = set()

    def path(self, row, config_id, repetition):
        return self.directory / (digest(unit_key(row, config_id, repetition)) + ".json")

    def restore(self, row, config_id, repetition):
        path = self.path(row, config_id, repetition)
        if not path.exists():
            return None
        try:
            body = load_unit(path)
        except (ValueError, KeyError, TypeError):
            # An interrupted/invalid final file must never count as complete.
            path.rename(path.with_suffix(".invalid"))
            return None
        if body["context"] != self.context:
            raise ValueError(f"Checkpoint context changed: {path}")
        record = body["record"]
        expected_sha = json.dumps({"time_sha256": str(row["time_sha256"]),
                                   "state_sha256": str(row["state_sha256"])}, sort_keys=True, separators=(",", ":"))
        if record["observed_data_sha256"] != expected_sha:
            raise ValueError(f"Checkpoint data changed: {path}")
        self.pending_rng = body.get("rng_state")
        self.seen_configs.add(config_id)
        return record

    def before_fit(self, config_id):
        # Adapter construction seeds global RNGs. Restore only after construction,
        # so an interrupted shard continues its original sampling stream.
        if self.pending_rng is not None:
            if config_id in self.seen_configs:
                restore_rng(self.pending_rng)
            self.pending_rng = None

    def save(self, row, config_id, repetition, record, check):
        self.seen_configs.add(config_id)
        record.update(git_hash=self.git_commit, code_origin_git_hash=self.git_commit, image_id=self.image_id)
        path = self.path(row, config_id, repetition)
        body = dict(key=list(unit_key(row, config_id, repetition)), context=self.context,
                    record=record, export_check=check)
        if record["method"] == "odeformer":
            body["rng_state"] = rng_state()
            self.pending_rng = body["rng_state"]
        payload = encoded(dict(body=body, sha256=digest(body))) + b"\n"
        if path.exists():
            if path.read_bytes() != payload:
                raise ValueError(f"Refusing to overwrite complete unit: {path}")
            return
        try:
            atomic_write(path, payload, replace=False)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise ValueError(f"Concurrent non-identical unit: {path}")


def export_failure(harness, method, config, fit_cell, target_cell, exc):
    record = harness.record_failure(harness.base_record(method, config, fit_cell, target_cell), exc)
    if method == "odeformer":
        record["odeformer_config_id"] = config["config_id"]
    else:
        record.update(harness.pysr_schema_defaults(config))
    record["export_validation_error"] = str(exc)
    return record
