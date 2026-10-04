"""Acceptance 6: smoke timing with early/late function extrapolation."""

from __future__ import annotations

import statistics

from experiments.annihilator_gate2a.acceptance.common import Timer, parser, write_result
from experiments.annihilator_gate2a.config import FUNCTIONS
from experiments.annihilator_gate2a.run_gate2a import one_run


def _complexity(function_key: str) -> int:
    r, d = FUNCTIONS[function_key].reference_class
    return (r + 1) * (d + 1)


def _estimate_function_times(f2_seconds: float, f10_seconds: float) -> dict[str, float]:
    c2 = _complexity("F2")
    c10 = _complexity("F10")
    out = {}
    for key in FUNCTIONS:
        weight = (_complexity(key) - c2) / (c10 - c2)
        weight = min(1.0, max(0.0, weight))
        out[key] = f2_seconds + weight * (f10_seconds - f2_seconds)
    return out


def _workload_seconds(per_function_seconds: dict[str, float], rows_per_function: int) -> float:
    return sum(rows_per_function * per_function_seconds[key] for key in FUNCTIONS)


def _worker_estimates(seconds: float) -> dict[str, float]:
    return {"workers_1": seconds, "workers_8": seconds / 8.0}


def main() -> None:
    args = parser().parse_args()
    tasks = [("F2", "wide", 0.01, 0, "standard")]
    if not args.limit:
        tasks.append(("F10", "wide", 0.0, 0, "standard"))
    with Timer() as timer:
        rows = [one_run(task) for task in tasks]

    measured = {}
    for row in rows:
        measured.setdefault(row["function"], []).append(float(row["runtime_seconds"]))
    f2_seconds = statistics.mean(measured["F2"])
    f10_seconds = statistics.mean(measured.get("F10", measured["F2"]))
    per_function_seconds = _estimate_function_times(f2_seconds, f10_seconds)
    main_seconds = _workload_seconds(per_function_seconds, rows_per_function=82)
    grid_seconds = 11.0 * _workload_seconds(per_function_seconds, rows_per_function=42)
    write_result(
        "accept_06_smoke",
        {
            "limit": args.limit,
            "measured_rows": rows,
            "runtime_seconds": timer.seconds,
            "early_function_seconds": f2_seconds,
            "late_function_seconds": f10_seconds,
            "per_function_estimated_seconds": per_function_seconds,
            "main_workload": {
                "rows": 20 + 400 + 400,
                "estimated_seconds": _worker_estimates(main_seconds),
            },
            "sensitivity_grid": {
                "variants": 11,
                "rows_per_variant": 20 + 400,
                "estimated_seconds": _worker_estimates(grid_seconds),
            },
        },
    )


if __name__ == "__main__":
    main()
