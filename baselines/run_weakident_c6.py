"""Q-B2 reference adapter, bounded controls/cost probe, and indexed shard entry point."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
import platform
import sys
import time
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.io import loadmat
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "baselines/third_party/weakident"
for path in (ROOT / "analysis", ROOT / "baselines/third_party/numpy_indexed_pkg"):
    sys.path.insert(0, str(path))


def load_reference():
    """Resolve the authors' absolute utils imports without changing their source."""
    saved = {k: v for k, v in sys.modules.items() if k == "utils" or k.startswith("utils.")}
    bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        for key in saved:
            del sys.modules[key]
        package = types.ModuleType("utils")
        package.__path__ = [str(VENDOR / "utils")]
        sys.modules["utils"] = package
        spec = importlib.util.spec_from_file_location("qb2_weakident_reference", VENDOR / "model.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key in list(sys.modules):
            if key == "utils" or key.startswith("utils."):
                del sys.modules[key]
        sys.modules.update(saved)
        sys.dont_write_bytecode = bytecode


reference = load_reference()
from scripts.aggregate import run_phasec_noise_sindy_baselines as baseline
from scripts.aggregate.qb1_wisp_library import cell_key, select_q9
from scripts.aggregate.run_wp_n6_sindy_baseline import LibraryConfig, term_name_from_monomial

UNSUPPORTED = "not supported by the reference implementation"
METHODS = ("weakident_native", "weakident_trig")
MIX = {1: 1564, 2: 1904, 3: 680}


def term_name(powers):
    """Map all polynomial multi-indices, including mixed cubics, to B1 names."""
    powers = np.asarray(powers)
    if np.any(powers < 0) or np.any(powers != powers.astype(int)):
        raise ValueError("expected nonnegative integer polynomial powers")
    return term_name_from_monomial(tuple(int(p) for p in powers)).replace("*", " ")


def trig_name(function, variable):
    if function not in ("sin", "cos") or variable not in range(4):
        raise ValueError("invalid trigonometric term")
    return f"{function}(1 x{variable})"


def build_dictionary(u, xs, include_trig=False):
    """B2b EXTENSION: append sin/cos weak columns, outside the reference folder.

    Reuse the native FFT test function, convolution, window and sample indices.
    In ODE mode the reference scale matrix is a copy of W. No derivative or
    selection setting changes. Disabling this extension takes the native path.
    """
    dim = len(u)
    empty_truth = [np.empty((0, dim + 3)) for _ in range(dim)]
    tags, lhs, rhs, _ = reference.build_feature_vector_tags(
        dim, 1, 0, 3, False, empty_truth, True)
    names = [term_name(tag[:dim]) for tag in tags[rhs]]
    native_compute = reference.compute_w_ode

    def extended_compute(dict_list, u_hat, fft_phis, sample_indices):
        native = native_compute(dict_list, u_hat, fft_phis, sample_indices)
        columns = [reference.conv_fft_v2(function(u_hat[i]), fft_phis[0].reshape(-1, 1),
                                         sample_indices).flatten()
                   for i in range(dim) for function in (np.sin, np.cos)]
        return np.column_stack([native, *columns])

    with patch.object(reference, "compute_w_ode", extended_compute if include_trig else native_compute):
        w, scales = reference.build_feature_matrix_and_scale_matrix(u, xs, 0, 1, 1, tags, True)
    # The native dynamic-region search uses only native tags/columns.
    region = reference.find_highly_dynamic_region(tags, scales[:, :len(tags)], True, dim, 1, 0)
    if include_trig:
        rhs = np.concatenate([rhs, np.arange(len(tags), len(tags) + 2 * dim)])
        names += [trig_name(function, i) for i in range(dim) for function in ("sin", "cos")]
    return lhs, rhs, w, scales, region, names


class StoredModel:
    def __init__(self, coefficients, names):
        self.coef, self.names = coefficients, names

    def coefficients(self):
        return self.coef

    def get_feature_names(self):
        return self.names


AUTHORS_TAU = .05
# Protocol Q-B amendment 5: the frozen trimming-threshold grid.
TAU_GRID = (0., .005, .01, .02, .05, .1, .2)


def tau_tag(tau):
    """Library-id suffix; 0.05 -> 'tau005' as in the first run, values stay distinct."""
    return "tau" + f"{tau:g}".replace(".", "")


def fit_path(t, x, include_trig=False, taus=(AUTHORS_TAU,), cv_seed=None):
    """Build the weak dictionary once and identify at every trimming threshold.

    tau enters only diff_eqn_identification; the dictionary does not draw random
    numbers, so re-seeding before each identification reproduces a single fit at
    that tau exactly. Inputs are copied per tau so no call can see another's state.
    Returns a list of (StoredModel, seconds) in the order of ``taus``.
    """
    if x.shape[1] not in (1, 2, 3):
        raise ValueError(UNSUPPORTED)
    if not np.allclose(np.diff(t), np.diff(t)[0], rtol=1e-10, atol=1e-14):
        raise ValueError("WeakIdent requires uniform times")
    u = x.T[:, None, :]
    xs = np.asarray(t).reshape(1, 1, -1)
    models = []
    # Suppress reference progress, never its errors. No noise injection is called.
    with contextlib.redirect_stdout(io.StringIO()):
        started = time.perf_counter()
        lhs, rhs, w, scales, region, names = build_dictionary(u, xs, include_trig)
        shared = (time.perf_counter() - started) / len(taus)
        for tau in taus:
            started = time.perf_counter()
            if cv_seed is not None:
                np.random.seed(cv_seed)
            _, _, coefficients = reference.diff_eqn_identification(
                tau, len(u), 1, True, lhs.copy(), rhs.copy(), w.copy(), scales.copy(), np.copy(region))
            models.append((StoredModel(coefficients.T, names), shared + time.perf_counter() - started))
    return models


def fit(t, x, include_trig=False, tau=AUTHORS_TAU):
    return fit_path(t, x, include_trig, (tau,))[0][0]


def array_hash(array):
    return hashlib.sha256(np.asarray(array, dtype="<f8").tobytes(order="C")).hexdigest()


def validate_interpolated(t, x, entry):
    for name, array in (("time", t), ("state", x)):
        if array_hash(array) != entry[f"{name}_sha256"]:
            raise ValueError(f"interpolated {name} hash mismatch")
    digest = hashlib.sha256()
    for array in (t, x):
        digest.update(np.asarray(array, dtype="<f8").tobytes(order="C"))
    if digest.hexdigest() != entry["q5w_interpolated_sha256"]:
        raise ValueError("q5w_interpolated_sha256 mismatch")


INTERP_FIELDS = ("q5w_interpolated_sha256", "q5w_interpolation_points", "q5w_interpolation_dt")


def read_inputs(export_root, row, interp_root, entries):
    # This verifies actual observed bytes, not just index strings.
    t, x = baseline.read_index_cell(export_root, row)
    if float(row.subsample_rho) == 0:
        # Always emit the same columns so appended shard CSVs keep one header.
        return t, x, {k: "" for k in INTERP_FIELDS}
    entry = entries[cell_key(row)]
    payload = loadmat(interp_root / entry["input_file"])
    t, x = payload["tobs"].reshape(-1), payload["xobs"]
    validate_interpolated(t, x, entry)
    return t, x, {k: entry[k] for k in INTERP_FIELDS}


def cell_cv_seed(row):
    key = baseline.sindy_seed_key(row, "qb2_weakident_v1_poly3_native_tau005")
    key["method"] = "weakident"
    return baseline.hash_seed(key)


def evaluate(method, system, support, row, t, x, clean_t, clean, disable_trig=False,
             tau=AUTHORS_TAU, model=None, fit_seconds=None):
    """One evaluated row. With ``model`` given (tau path), that fit is evaluated instead of refitting."""
    trig = method == "weakident_trig" and not disable_trig
    cfg = LibraryConfig(f"qb2_weakident_v1_poly3_{'trig' if trig else 'native'}_{tau_tag(tau)}", 3, trig, .05)
    unsupported = int(system["dim"]) == 4
    # The authors' cross-validation draws np.random.permutation from the global RNG
    # (utils/calculations.py:290). Seed it per cell, as the project seeds E-SINDy and
    # Weak-SINDy: hash of the cell key; identical for both arms so that B2b with the
    # extension disabled reproduces B2a (protocol Q-B, technical amendment 4).
    cv_seed = cell_cv_seed(row)
    def fitting(*args, **kwargs):
        if unsupported:
            raise ValueError(UNSUPPORTED)
        if model is not None:
            return model
        np.random.seed(cv_seed)
        return fit(t, x, trig, tau)
    # Reuse the entire B1 evaluator, including its failure rows and pruning rule.
    with patch.object(baseline, "fit_sindy", side_effect=fitting):
        result = baseline.run_one_model("sindy", cfg, system, support, row, t, x, clean_t, clean)
    result.update(method=method, method_config_id=f"{method}_{cfg.library_id}",
                  stlsq_threshold="", weakident_tau=tau, weakident_max_dt=1, weakident_cv_seed=cv_seed,
                  weakident_source_commit="be14358b38f9cdb40ce1a0aeb127039f91d1410e")
    if model is not None and fit_seconds is not None and result["fit_status"] == "success":
        result["fit_elapsed_s_context"] = fit_seconds
    exact = support.get("phasec_representability") == "exact"
    has_trig = any("sin(" in term or "cos(" in term
                   for eq in baseline.library_true_terms(system) for term in eq)
    eligible = exact and (trig or not has_trig) and not unsupported
    result["structure_status"] = ("scored" if eligible else UNSUPPORTED if unsupported else
                                  "true support outside dictionary" if exact else "non-exact system")
    if not eligible:
        for field in list(result):
            if field.startswith("sindy_structure_"):
                result[field] = ""
    if unsupported:
        result.update(fit_status=UNSUPPORTED, fit_error="", fit_elapsed_s_context=0.)
        for field in list(result):
            if field.startswith(("reconstruction_", "generalization_")):
                result[field] = UNSUPPORTED if field.endswith("integration_status") else ""
    return result


def environment():
    return dict(python=sys.version, platform=platform.platform(),
                packages={name: importlib.metadata.version(name) for name in
                          ("numpy", "scipy", "pandas", "pysindy", "scikit-learn", "sympy", "threadpoolctl")},
                numpy_indexed="0.3.7 (vendored source)", threads=1,
                reference_commit="be14358b38f9cdb40ce1a0aeb127039f91d1410e")


def comparable(row):
    # JSON preserves float representations (including signed zero), and compares
    # repeated NaN failure values consistently without revealing metric values.
    return {k: json.dumps(v, sort_keys=True) for k, v in row.items() if k != "fit_elapsed_s_context"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("probe", "shard"))
    parser.add_argument("--limit", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--export-dir", type=Path, default=ROOT / "outputs/phase_c_c6_data_conditions_5dd1df8")
    parser.add_argument("--q9-paths", type=Path, default=ROOT / "outputs/sideproject_q9_inputs/grid/q9_paths.json")
    parser.add_argument("--interp-dir", type=Path, default=ROOT / "outputs/sideproject_q5w_wsindy/matlab_inputs/w1_interp")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/sideproject_qb2_checks")
    parser.add_argument("--shard-index", type=int, default=int(os.environ.get("JOB_COMPLETION_INDEX", 0)))
    parser.add_argument("--n-shards", type=int, default=240)
    parser.add_argument("--taus", default=str(AUTHORS_TAU),
                        help="comma-separated trimming thresholds (shard mode); 'grid' = protocol amendment 5")
    args = parser.parse_args()
    taus = TAU_GRID if args.taus == "grid" else tuple(float(v) for v in args.taus.split(","))
    if args.mode == "probe" and taus != (AUTHORS_TAU,):
        parser.error("the probe runs at the authors' tau only")
    if not 0 <= args.shard_index < args.n_shards:
        parser.error("invalid shard index/count")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fingerprint = environment()
    (args.output_dir / f"environment_{args.shard_index}.json").write_text(
        json.dumps({method: fingerprint for method in METHODS}, indent=2))
    index = select_q9(baseline.read_export_index(args.export_dir / "index.csv"), args.q9_paths, require_all=True)
    entries = {}
    for entry in json.loads((args.interp_dir / "manifest.json").read_text())["cells"]:
        if entry["library"] == "L-C6":
            key = cell_key(entry["cell_key"])
            if key in entries:
                raise ValueError("duplicate interpolation manifest key")
            entries[key] = entry
    systems = {s["id"]: s for s in baseline.load_benchmark(ROOT / "benchmarks/data/strogatz_extended.json")}
    support = baseline.load_phase_c_support(ROOT / "studies/regression/phase_c_support.json").set_index("system_id")
    if args.mode == "probe":
        selected = []
        for dim in range(1, args.limit + 1):
            sid = min(sid for sid, s in systems.items() if s["dim"] == dim and
                      support.loc[sid, "phasec_representability"] == "exact")
            rows = index[(index.system_id == sid) & (index.initial_condition_set == 1) &
                         (index.noise_sigma == .05) & (index.subsample_rho == .5) & (index.noise_realization == 1)]
            if len(rows) != 1:
                raise ValueError("expected exactly one probe cell per dimension")
            selected.append(rows.iloc[0])
    else:
        selected = [row for i, (_, row) in enumerate(index.iterrows()) if i % args.n_shards == args.shard_index]
    costs, controls = [], []
    details_path = args.output_dir / f"details_{args.shard_index:04d}.csv"
    completed = set()
    if args.mode == "shard" and details_path.exists():
        fields = ["method", "system_id", "source_initial_condition_set", "noise_sigma", "subsample_rho",
                  "noise_realization", "weakident_tau"]
        for _, previous in pd.read_csv(details_path, usecols=fields).iterrows():
            key_row = previous.rename({"source_initial_condition_set": "initial_condition_set"})
            completed.add((previous["method"], float(previous["weakident_tau"]), cell_key(key_row)))
    started_all = time.perf_counter()
    with threadpool_limits(limits=1):
        for row in selected:
            if args.mode == "shard" and all((method, tau, cell_key(row)) in completed
                                            for method in METHODS for tau in taus):
                continue
            if time.perf_counter() - started_all > 840 and args.mode == "probe":
                raise TimeoutError("probe exceeded 14 minutes")
            system = systems[int(row.system_id)]
            t, x, hashes = read_inputs(args.export_dir, row, args.interp_dir, entries)
            clean_t = np.linspace(0, 10, 512)
            clean = {ic: baseline.integrate_truth(system, ic - 1, clean_t)[0] for ic in (1, 2)}
            results = {}
            sys_support = support.loc[int(row.system_id)].to_dict()
            for method in METHODS:
                todo = [tau for tau in taus if not (args.mode == "shard" and (method, tau, cell_key(row)) in completed)]
                if not todo:
                    continue
                started = time.perf_counter()
                path = None
                if args.mode == "shard" and int(system["dim"]) != 4:
                    try:
                        path = fit_path(t, x, method == "weakident_trig", tuple(todo), cell_cv_seed(row))
                    except Exception:
                        path = None  # fall back to per-tau evaluation, which records the failure row
                rows_out, cache = [], {}
                for i, tau in enumerate(todo):
                    model, seconds = path[i] if path else (None, None)
                    key = None if model is None else (np.asarray(model.coef).tobytes(), tuple(model.names))
                    if key is not None and key in cache:
                        # Identical fitted model: identical evaluation; only tau-dependent ids differ.
                        result = dict(cache[key])
                        trig = method == "weakident_trig"
                        library_id = f"qb2_weakident_v1_poly3_{'trig' if trig else 'native'}_{tau_tag(tau)}"
                        result.update(library_id=library_id, method_config_id=f"{method}_{library_id}",
                                      weakident_tau=tau, fit_elapsed_s_context=seconds,
                                      weakident_evaluation_reused_from_tau=cache[key]["weakident_tau"])
                    else:
                        result = evaluate(method, system, sys_support, row, t, x, clean_t, clean,
                                          tau=tau, model=model, fit_seconds=seconds)
                        result.update(hashes)
                        result["weakident_evaluation_reused_from_tau"] = ""
                        if key is not None:
                            cache[key] = result
                    rows_out.append(result)
                results[method] = rows_out[0]
                if args.mode == "shard":
                    baseline.append_csv_rows(details_path, rows_out)
                costs.append(dict(system_id=int(row.system_id), dimension=int(row.dimension), method=method,
                                  fit_status=rows_out[0]["fit_status"], fit_error=rows_out[0]["fit_error"],
                                  fit_wall_s=rows_out[0]["fit_elapsed_s_context"],
                                  cell_wall_s=time.perf_counter() - started,
                                  observed_hash_checked=True, interpolated_hash_checked=bool(hashes["q5w_interpolated_sha256"]),
                                  role="planning_context_not_evidence"))
            if args.mode == "probe":
                native = results[METHODS[0]]
                disabled = evaluate(METHODS[1], system, support.loc[int(row.system_id)].to_dict(), row,
                                    t, x, clean_t, clean, disable_trig=True)
                disabled.update(hashes)
                # Normalize arm labels only; the disabled library id is already native.
                disabled.update(method=native["method"], method_config_id=native["method_config_id"])
                repeat = evaluate(METHODS[0], system, support.loc[int(row.system_id)].to_dict(), row, t, x, clean_t, clean)
                repeat.update(hashes)
                controls.append(dict(dimension=int(row.dimension), system_id=int(row.system_id),
                                     compared_fields=len(comparable(native)),
                                     no_trig_differences=[k for k, v in comparable(native).items() if v != comparable(disabled)[k]],
                                     repeat_differences=[k for k, v in comparable(native).items() if v != comparable(repeat)[k]]))
                (args.output_dir / "controls.json").write_text(json.dumps(controls, indent=2))
                (args.output_dir / "cost.json").write_text(json.dumps(costs, indent=2))
                print(json.dumps(costs[-2:]), flush=True)
    if args.mode == "probe":
        if args.limit == 3:
            hours = {method: sum(c["cell_wall_s"] * MIX[c["dimension"]] for c in costs if c["method"] == method) / 3600
                     for method in METHODS}
            failures = sum(c["fit_status"] != "success" for c in costs)
            summary = dict(core_hours=hours, combined_core_hours=sum(hours.values()),
                           laptop_under_one_hour=sum(hours.values()) < 1, dimension_counts=MIX,
                           excluded_dimension4_cells=136, probe_failures=failures,
                           blocked_failure_fraction=failures / len(costs) > .05,
                           role="planning_context_not_evidence")
            (args.output_dir / "projection.json").write_text(json.dumps(summary, indent=2))
            print(json.dumps(summary))
        if any(c["no_trig_differences"] or c["repeat_differences"] for c in controls):
            raise RuntimeError("identity/determinism control failed")


if __name__ == "__main__":
    main()
