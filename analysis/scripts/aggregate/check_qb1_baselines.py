"""Small Q-B1 controls and cost-only probe. Never starts a full grid."""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import io
import json
import platform
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis"))
from scripts.aggregate import run_phasec_noise_sindy_baselines as runner
from scripts.aggregate.qb1_wisp_library import q9_cells, select_q9, legacy_term
from exploratory.term_relevance.term_relevance import phasec_basis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["control", "cost"])
    parser.add_argument("--limit", type=int, default=4, choices=range(1, 5))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/sideproject_qb1_checks")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fingerprint = {p: importlib.metadata.version(p) for p in
                   ["pysindy", "numpy", "scipy", "pandas", "scikit-learn", "sympy"]}
    fingerprint.update(python=sys.version, platform=platform.platform())
    (args.output_dir / "environment.json").write_text(json.dumps(fingerprint, indent=2))
    q9 = ROOT / "outputs/sideproject_q9_inputs/grid/q9_paths.json"
    index_path = ROOT / "outputs/phase_c_c6_data_conditions_5dd1df8/index.csv"
    index = select_q9(runner.read_export_index(index_path), q9, require_all=True)
    support_path = ROOT / "studies/regression/phase_c_support.json"
    supports = json.loads(support_path.read_text())["systems"]
    exact_ids = {s["system_id"] for s in supports if s["representability"] == "exact" and s["status"] == "ok"}
    support_rows = runner.load_phase_c_support(support_path).set_index("system_id")
    systems = {s["id"]: s for s in runner.load_benchmark(ROOT / "benchmarks/data/strogatz_extended.json")}
    # Audit every exact system explicitly against the existing term mapping.
    mapping = []
    for s in supports:
        if s["system_id"] not in exact_ids:
            continue
        mapped = [{legacy_term(t).replace(" ", "*") for t in eq} for eq in s["support_terms"]]
        if mapped != runner.library_true_terms(systems[s["system_id"]]):
            raise ValueError(f"support mapping mismatch: {s['system_id']}")
        mapping.append(dict(system_id=s["system_id"], dimension=s["dim"],
                            source_terms=s["support_terms"], mapped_terms=[sorted(eq) for eq in mapped]))
    (args.output_dir / "support_mapping.json").write_text(json.dumps(mapping, indent=2))
    config_name = "paper1_phaseC_sindy_baseline.json" if args.mode == "control" else "sideproject_qb1_sindy.json"
    config = runner.load_config(ROOT / "analysis/configs" / config_name)
    configs = runner.library_grid(config)
    if args.mode == "control":
        configs = [c for c in configs if c.library_id.startswith("poly_deg3_sin_cos_")]
    reference = None
    if args.mode == "control":
        # Read only the named four control cells below, not other quality rows.
        reference = ROOT / "outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv"
    all_results = []
    comparison = []
    fits = []
    for dim in range(1, args.limit + 1):
        system_id = min(s["id"] for s in systems.values() if s["dim"] == dim and s["id"] in exact_ids)
        cell = index[(index.system_id == system_id) & (index.initial_condition_set == 1) &
                     (index.noise_sigma == 0.05) & (index.subsample_rho == 0.5) & (index.noise_realization == 1)]
        if len(cell) != 1:
            raise ValueError(f"expected one probe cell, got {len(cell)} for dimension {dim}")
        row = cell.iloc[0]
        observed_t, observed_x = runner.read_index_cell(index_path.parent, row)
        clean_t = np.linspace(0, 10, 512)
        system = systems[system_id]
        clean = {ic: runner.integrate_truth(system, ic - 1, clean_t)[0] for ic in (1, 2)}
        expected = {}
        if reference:
            with reference.open(newline="", encoding="utf-8") as handle:
                for r in csv.DictReader(handle):
                    if (int(r["system_id"]) == system_id and int(r["source_initial_condition_set"]) == 1
                            and float(r["noise_sigma"]) == 0.05 and float(r["subsample_rho"]) == 0.5
                            and int(r["noise_realization"]) == 1):
                        expected[(r["method"], r["library_id"])] = r
        for method in ("sindy", "weak_sindy", "e_sindy"):
            started = time.perf_counter()
            failures = 0
            fit_times = []
            for cfg in configs:
                fit_started = time.perf_counter()
                result = runner.run_one_model(method, cfg, system, support_rows.loc[system_id].to_dict(),
                                              row, observed_t, observed_x, clean_t, clean)
                failures += result["fit_status"] != "success"
                fit_times.append(result["fit_elapsed_s_context"])
                fits.append(dict(dimension=dim, system_id=system_id, method=method,
                                 library_id=cfg.library_id, fit_status=result["fit_status"],
                                 fit_wall_s=result["fit_elapsed_s_context"],
                                 fit_and_evaluation_wall_s=time.perf_counter() - fit_started,
                                 role="planning_context_not_evidence"))
                (args.output_dir / f"{args.mode}_fits.json").write_text(json.dumps(fits, indent=2))
                if reference:
                    old = expected[(method, cfg.library_id)]
                    # Match the actual CSV serialization, including empty fields.
                    text = io.StringIO()
                    writer = csv.DictWriter(text, fieldnames=list(result))
                    writer.writeheader()
                    writer.writerow(result)
                    actual = next(csv.DictReader(io.StringIO(text.getvalue())))
                    for field in old:
                        comparison.append(dict(dimension=dim, system_id=system_id, method=method,
                                               library_id=cfg.library_id, field=field,
                                               equal=actual.get(field, "") == old[field],
                                               generated=field in actual))
                # No access to benchmark quality fields in cost mode.
                del result
            all_results.append(dict(dimension=dim, system_id=system_id, method=method,
                                    fits=len(configs), failures=failures,
                                    cell_wall_s=time.perf_counter() - started,
                                    fit_wall_s=fit_times, role="planning_context_not_evidence"))
            (args.output_dir / f"{args.mode}_cost.json").write_text(json.dumps(all_results, indent=2))
            print(json.dumps({k: v for k, v in all_results[-1].items() if k != "fit_wall_s"}), flush=True)
    if comparison:
        pd.DataFrame(comparison).to_csv(args.output_dir / "control_fields.csv", index=False)
    if args.mode == "cost" and args.limit == 4:
        mix = Counter(c["dim"] for c in q9_cells(q9).values())
        hours = sum(r["cell_wall_s"] * mix[r["dimension"]] for r in all_results) / 3600
        projection = dict(core_hours=hours, laptop_under_one_hour=hours < 1,
                          dimension_counts=dict(mix), role="planning_context_not_evidence")
        (args.output_dir / "projection.json").write_text(json.dumps(projection, indent=2))
        print(json.dumps(projection))


if __name__ == "__main__":
    main()
