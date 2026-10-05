"""Appendix B ex-ante identifiability diagnostic for Gate 2A v3."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import json
import time
from pathlib import Path

from experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration import ex_ante_cell
from experiments.annihilator_gate2a_v3.config import FUNCTIONS, RESULTS


ETAS = (0.01, 0.05)
OUTDIR = RESULTS / "appendix_B"
CALIBRATION_DIR = RESULTS / "calibration"


def _appendix_a_part_paths() -> list[Path]:
    return sorted(
        path
        for path in CALIBRATION_DIR.glob("appendix_A_part_*_of_8.json")
        if "limit" not in path.name
    )


def load_stage_k_parameters() -> dict:
    paths = _appendix_a_part_paths()
    if not paths:
        raise FileNotFoundError(f"no Appendix A part files found in {CALIBRATION_DIR}")
    records = []
    for path in paths:
        payload = json.loads(path.read_text())
        ell_max = payload.get("K_a", {}).get("ell_max")
        tau = payload.get("K_b", {}).get("tau")
        if ell_max is None or tau is None:
            raise RuntimeError(f"missing K_a.ell_max or K_b.tau in {path}")
        records.append({"path": str(path), "ell_max": int(ell_max), "tau": float(tau)})
    first = records[0]
    mismatches = [
        record for record in records
        if record["ell_max"] != first["ell_max"] or record["tau"] != first["tau"]
    ]
    if mismatches:
        raise RuntimeError(f"Appendix A part parameter mismatch: {mismatches}")
    return {
        "ell_max": first["ell_max"],
        "tau": first["tau"],
        "sources": [record["path"] for record in records],
    }


def _cell_job(args: tuple[str, str, float, int, float, int]) -> dict:
    function_key, domain_name, eta, ell_max, tau, n = args
    return ex_ante_cell(function_key, FUNCTIONS[function_key], domain_name, eta, ell_max, tau, n)


def _jobs(n: int, ell_max: int, tau: float) -> list[tuple[str, str, float, int, float, int]]:
    return [
        (function_key, domain_name, eta, ell_max, tau, n)
        for function_key in FUNCTIONS
        for domain_name in ("wide", "narrow")
        for eta in ETAS
    ]


def compute_appendix_b(n: int, ell_max: int, tau: float, workers: int) -> dict:
    records: dict[str, dict[str, dict[str, dict]]] = {
        function_key: {domain_name: {} for domain_name in ("wide", "narrow")}
        for function_key in FUNCTIONS
    }
    jobs = _jobs(n, ell_max, tau)
    if workers == 1:
        for job in jobs:
            record = _cell_job(job)
            records[record["function"]][record["domain"]][str(record["eta"])] = record
            _progress(record)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_cell_job, job): job for job in jobs}
            for future in as_completed(futures):
                record = future.result()
                records[record["function"]][record["domain"]][str(record["eta"])] = record
                _progress(record)
    return records


def k6_diagnostic(records: dict) -> dict:
    affected = []
    for function_key in [f"F{index}" for index in range(1, 9)]:
        ref_r = FUNCTIONS[function_key].reference_class[0]
        if ref_r > 3:
            continue
        record = records[function_key]["wide"]["0.01"]
        if record["class"] in {"N1", "N2"}:
            affected.append(
                {
                    "function": function_key,
                    "domain": "wide",
                    "eta": 0.01,
                    "reference_class": record["reference_class"],
                    "class": record["class"],
                    "theta_hat_c": record["theta_hat_c"],
                    "weakest_earlier": record["weakest_earlier"],
                }
            )
    return {
        "rule": "count wide F1-F8 cells with r_ref <= 3 at eta=0.01 classified N1 or N2; triggers above 1",
        "affected_count": len(affected),
        "would_trigger": len(affected) > 1,
        "affected_cells": affected,
    }


def _progress(record: dict) -> None:
    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] Appendix B completed "
        f"{record['function']}/{record['domain']}/eta={record['eta']} -> {record['class']}",
        flush=True,
    )


def build_payload(n: int, workers: int) -> dict:
    start = time.perf_counter()
    parameters = load_stage_k_parameters()
    records = compute_appendix_b(n, parameters["ell_max"], parameters["tau"], workers)
    payload = {
        "diagnostic_only": True,
        "appendix_A_passed": False,
        "settings": {
            "n": n,
            "workers": workers,
            "etas": list(ETAS),
            "estimator": "AML (L-BFGS)",
        },
        "stage_k_parameters": parameters,
        "records": records,
        "K6_diagnostic": k6_diagnostic(records),
        "runtime_seconds": time.perf_counter() - start,
    }
    return payload


def write_markdown(path: Path, payload: dict) -> None:
    params = payload["stage_k_parameters"]
    k6 = payload["K6_diagnostic"]
    lines = [
        "# Appendix B - Gate 2A v3 Diagnostic",
        "",
        "Appendix A did not pass; this Appendix B run is a diagnostic only, not a Gate result.",
        "",
        f"- ell_max: {params['ell_max']}",
        f"- tau: {params['tau']}",
        f"- parameter_sources: {len(params['sources'])} Appendix A part files",
        f"- estimator: {payload['settings']['estimator']}",
        f"- n: {payload['settings']['n']}",
        f"- workers: {payload['settings']['workers']}",
        f"- runtime_seconds: {payload['runtime_seconds']}",
        "",
        "## Class Table",
        "",
        "| Function | Domain | eta | r_ref | d_ref | Class | theta_hat_c | Weakest earlier | Weakest beta |",
        "|---|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for function_key, by_domain in payload["records"].items():
        for domain_name, by_eta in by_domain.items():
            for eta in sorted(by_eta, key=float):
                record = by_eta[eta]
                weakest = record.get("weakest_earlier")
                weakest_class = "-" if weakest is None else f"({weakest['class'][0]},{weakest['class'][1]})"
                weakest_beta = "-" if weakest is None else weakest["beta"]
                lines.append(
                    f"| {function_key} | {domain_name} | {eta} | {record['reference_class'][0]} | "
                    f"{record['reference_class'][1]} | {record['class']} | {record['theta_hat_c']} | "
                    f"{weakest_class} | {weakest_beta} |"
                )
    lines.extend(
        [
            "",
            "## K6 Diagnostic",
            "",
            f"- affected_count: {k6['affected_count']}",
            f"- would_trigger: {k6['would_trigger']}",
            "",
            "| Function | Class | r_ref | d_ref | theta_hat_c | Weakest earlier | Weakest beta |",
            "|---|---:|---:|---:|---:|---|---:|",
        ]
    )
    for record in k6["affected_cells"]:
        weakest = record.get("weakest_earlier")
        weakest_class = "-" if weakest is None else f"({weakest['class'][0]},{weakest['class'][1]})"
        weakest_beta = "-" if weakest is None else weakest["beta"]
        lines.append(
            f"| {record['function']} | {record['class']} | {record['reference_class'][0]} | "
            f"{record['reference_class'][1]} | {record['theta_hat_c']} | {weakest_class} | {weakest_beta} |"
        )
    path.write_text("\n".join(lines) + "\n")


def write_outputs(payload: dict) -> tuple[Path, Path]:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTDIR / "appendix_B.json"
    md_path = OUTDIR / "appendix_B.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    write_markdown(md_path, payload)
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 6:
        raise ValueError("--workers must be between 1 and 6")
    payload = build_payload(args.n, args.workers)
    json_path, md_path = write_outputs(payload)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
