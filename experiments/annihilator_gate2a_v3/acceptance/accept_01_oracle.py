"""Acceptance 1: Gate 2A v3 oracle cache and v1-cache comparison."""

from __future__ import annotations

import argparse
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from experiments.annihilator_gate2a_v3.config import ALL_FUNCTIONS, CLASSES, FUNCTIONS, RESULTS, calibration_reference_coeffs
from experiments.annihilator_gate2a_v3.operator_search import normalize_coeffs
from experiments.annihilator_gate2a_v3.oracle import ORACLE_METADATA, build_reference
from experiments.annihilator_gate2a_v3.transfer import angle


KNOWN_V1_F10_EXCEPTIONS = {("F10", "narrow", "4,6"), ("F10", "narrow", "5,6"), ("F10", "narrow", "6,6")}
ORACLE_CACHE_NAME = "oracle_reference_v3.json"
V1_CACHE = Path("experiments/annihilator_gate2a/results/oracle_reference.json")
OUTDIR = RESULTS / "acceptance"


def _class_key(r: int, d: int) -> str:
    return f"{r},{d}"


def _part_path(part: str) -> Path:
    return OUTDIR / f"accept_01_oracle_part_{part.replace('/', '_of_')}.json"


def _selected_keys(part: str | None) -> list[str]:
    keys = list(ALL_FUNCTIONS)
    if not part:
        return keys
    index_text, count_text = part.split("/")
    index = int(index_text)
    count = int(count_text)
    if index < 0 or index >= count:
        raise ValueError(f"invalid part {part!r}")
    return [key for i, key in enumerate(keys) if i % count == index]


def _build_part(args: tuple[list[str], Path]) -> dict:
    keys, cache_path = args
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
        if _worker_cache_is_complete(data, keys):
            return data
    return build_reference(cache_path=cache_path, force=True, function_keys=keys)


def _worker_cache_is_complete(data: dict, keys: list[str]) -> bool:
    if data.get("metadata") != ORACLE_METADATA:
        return False
    if data.get("classes") != [list(c) for c in CLASSES]:
        return False
    functions = data.get("functions")
    if not isinstance(functions, dict) or set(functions) != set(keys):
        return False
    for function_key in keys:
        function_data = functions.get(function_key)
        if not isinstance(function_data, dict) or set(function_data) != {"wide", "narrow"}:
            return False
        for domain_data in function_data.values():
            classes = domain_data.get("classes")
            if not isinstance(classes, dict) or set(classes) != {_class_key(r, d) for r, d in CLASSES}:
                return False
    return True


def _v1_comparison(v2_data: dict) -> dict:
    if not V1_CACHE.exists():
        return {"available": False, "passed": False, "missing_path": str(V1_CACHE)}
    v1_data = json.loads(V1_CACHE.read_text())
    differences = []
    known = []
    unexpected = []
    for key in FUNCTIONS:
        for domain in ("wide", "narrow"):
            v1_classes = v1_data["functions"][key][domain]["classes"]
            v2_classes = v2_data["functions"][key][domain]["classes"]
            for r, d in CLASSES:
                class_key = _class_key(r, d)
                old = int(v1_classes[class_key]["n_exact"])
                new = int(v2_classes[class_key]["n_exact"])
                if old == new:
                    continue
                record = {"function": key, "domain": domain, "class": [r, d], "v1": old, "v2": new}
                differences.append(record)
                if (key, domain, class_key) in KNOWN_V1_F10_EXCEPTIONS:
                    known.append(record)
                else:
                    unexpected.append(record)
    return {
        "available": True,
        "known_f10_exceptions": known,
        "unexpected_differences": unexpected,
        "difference_count": len(differences),
        "passed": not unexpected,
    }


def _k_reference_comparison(data: dict) -> dict:
    records = []
    for key, spec in ALL_FUNCTIONS.items():
        if spec.group != "K":
            continue
        for domain in ("wide", "narrow"):
            expected_class, expected_coeffs = calibration_reference_coeffs(key, domain)
            record = data["functions"][key][domain]
            oracle_class = tuple(record["reference_class"])
            if oracle_class != expected_class:
                coeff_angle = None
                passed = False
            else:
                oracle_coeffs = np.asarray(record["reference_coeffs"], dtype=float)
                expected = normalize_coeffs(np.asarray(expected_coeffs, dtype=float), align_to=oracle_coeffs)
                coeff_angle = angle(oracle_coeffs, expected)
                passed = coeff_angle < 1e-20
            records.append(
                {
                    "function": key,
                    "domain": domain,
                    "expected_class": list(expected_class),
                    "oracle_class": list(oracle_class),
                    "coeff_angle": coeff_angle,
                    "passed": passed,
                    "threshold": "< 1e-20",
                }
            )
    return {"records": records, "passed": all(record["passed"] for record in records)}


def _evaluate(data: dict, limit: bool, runtime: float) -> dict:
    keys = list(data["functions"])
    reference_records = {}
    table_differences = {}
    for key in keys:
        reference_records[key] = {}
        wide_classes = data["functions"][key]["wide"]["classes"]
        narrow_classes = data["functions"][key]["narrow"]["classes"]
        diffs = []
        for r, d in CLASSES:
            class_key = _class_key(r, d)
            wide_n = int(wide_classes[class_key]["n_exact"])
            narrow_n = int(narrow_classes[class_key]["n_exact"])
            direct_n = int(narrow_classes[class_key].get("diagnostic_direct_n_exact", narrow_n))
            if wide_n != direct_n:
                diffs.append({"class": [r, d], "wide": wide_n, "diagnostic_direct_narrow": direct_n})
        table_differences[key] = diffs
        for domain in ("wide", "narrow"):
            record = data["functions"][key][domain]
            r, d = record["reference_class"]
            ref_dim = int(record["classes"][_class_key(r, d)]["n_exact"])
            reference_records[key][domain] = {
                "reference_class": record["reference_class"],
                "expected_reference_class": list(ALL_FUNCTIONS[key].reference_class),
                "reference_class_ok": tuple(record["reference_class"]) == ALL_FUNCTIONS[key].reference_class,
                "reference_n_exact": ref_dim,
                "reference_n_exact_one": ref_dim == 1,
                "verification": record["verification"],
            }
    complete = set(keys) == set(ALL_FUNCTIONS)
    v1_comparison = _v1_comparison(data) if complete and not limit else {"available": False, "passed": True, "partial": not complete}
    k_reference = _k_reference_comparison(data) if complete and not limit else {"records": [], "passed": True, "partial": not complete}
    metadata = dict(data.get("metadata", {}))
    metadata.pop("source_cache", None)
    metadata_ok = metadata == ORACLE_METADATA
    reference_passed = all(
        record["reference_class_ok"] and record["reference_n_exact_one"] and record["verification"]["passed"]
        for per_fn in reference_records.values()
        for record in per_fn.values()
    )
    direct_narrow_references_match = all(
        record.get("diagnostic_direct_reference_matches_wide", True)
        for key in keys
        for record in [data["functions"][key]["narrow"]]
    )
    return {
        "limit": limit,
        "complete": complete,
        "metadata": data.get("metadata"),
        "expected_metadata": ORACLE_METADATA,
        "metadata_ok": metadata_ok,
        "reference_records": reference_records,
        "wide_narrow_n_exact_differences": table_differences,
        "wide_narrow_n_exact_policy": "wide table is decisive; direct narrow differences are diagnostic",
        "direct_narrow_references_match": direct_narrow_references_match,
        "v1_cache_comparison": v1_comparison,
        "k_reference_comparison": k_reference,
        "passed": metadata_ok and reference_passed and direct_narrow_references_match and v1_comparison["passed"] and k_reference["passed"],
        "runtime_seconds": runtime,
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"wrote {path}")


def merge_parts(count: int) -> dict:
    missing = []
    data = {"metadata": ORACLE_METADATA, "classes": [list(c) for c in CLASSES], "functions": {}}
    runtime = 0.0
    for index in range(count):
        path = _part_path(f"{index}/{count}")
        if not path.exists():
            missing.append(str(path))
            continue
        payload = json.loads(path.read_text())
        runtime += float(payload.get("runtime_seconds", 0.0))
        if payload.get("metadata") != ORACLE_METADATA:
            raise RuntimeError(f"part metadata mismatch: {path}")
        data["functions"].update(payload["functions"])
    if missing:
        raise RuntimeError(f"incomplete oracle part set; missing {missing}")
    if set(data["functions"]) != set(ALL_FUNCTIONS):
        raise RuntimeError(f"merged oracle has {len(data['functions'])} of {len(ALL_FUNCTIONS)} functions")
    data["runtime_seconds"] = runtime
    cache_path = RESULTS / ORACLE_CACHE_NAME
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, indent=2, sort_keys=True))
    return data


def main() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--limit", action="store_true")
    arg_parser.add_argument("--workers", type=int, default=1)
    arg_parser.add_argument("--part", help="Build only functions where index %% count matches, formatted index/count.")
    arg_parser.add_argument("--merge-parts", type=int, help="Merge this many oracle part files.")
    args = arg_parser.parse_args()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    if args.limit:
        payload = {
            "limit": True,
            "passed": True,
            "note": "Limit mode validates the acceptance entry point only; the full oracle command builds the 100-digit cache.",
        }
        _write(OUTDIR / "accept_01_oracle.json", payload)
        return
    if args.merge_parts:
        data = merge_parts(args.merge_parts)
        payload = _evaluate(data, False, time.perf_counter() - start)
        _write(OUTDIR / "accept_01_oracle.json", payload)
        return
    selected_keys = _selected_keys(args.part)
    if args.workers > 1 and len(selected_keys) > 1:
        chunks = [selected_keys[i:: args.workers] for i in range(args.workers)]
        tasks = [(chunk, OUTDIR / f"accept_01_oracle_worker_{i}.cache.json") for i, chunk in enumerate(chunks) if chunk]
        with Pool(args.workers) as pool:
            parts = pool.map(_build_part, tasks)
        data = {"metadata": ORACLE_METADATA, "classes": [list(c) for c in CLASSES], "functions": {}}
        for part in parts:
            data["functions"].update(part["functions"])
        data["runtime_seconds"] = time.perf_counter() - start
        if not args.part:
            cache_path = RESULTS / ORACLE_CACHE_NAME
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(data, indent=2, sort_keys=True))
    else:
        cache_path = _part_path(args.part) if args.part else RESULTS / ORACLE_CACHE_NAME
        data = build_reference(cache_path=cache_path, force=bool(args.part), function_keys=selected_keys if args.part else None)
    if args.part:
        data["runtime_seconds"] = time.perf_counter() - start
        _write(_part_path(args.part), data)
        payload = _evaluate(data, False, data["runtime_seconds"])
        _write(_part_path(args.part).with_suffix(".summary.json"), payload)
        return
    payload = _evaluate(data, False, time.perf_counter() - start)
    _write(OUTDIR / "accept_01_oracle.json", payload)


if __name__ == "__main__":
    main()
