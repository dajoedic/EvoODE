"""Acceptance 5: deterministic task rows independent of worker count."""

from __future__ import annotations

from experiments.annihilator_gate2a.acceptance.common import Timer, parser, write_result
from experiments.annihilator_gate2a.run_gate2a import run_tasks


def comparable(row: dict) -> dict:
    out = dict(row)
    out.pop("runtime_seconds", None)
    return out


def main() -> None:
    args = parser().parse_args()
    tasks = [("F2", "wide", 0.0, 0, "standard")] if args.limit else [
        ("F2", "wide", 0.0, 0, "standard"),
        ("F2", "wide", 0.01, 0, "standard"),
        ("F7", "narrow", 0.01, 0, "standard"),
    ]
    with Timer() as timer:
        one_worker = [comparable(row) for row in run_tasks(tasks, 1)]
        four_workers = [comparable(row) for row in run_tasks(tasks, 4)]
    write_result(
        "accept_05_determinism",
        {
            "limit": args.limit,
            "workers": [1, 4],
            "tasks": tasks,
            "identical": one_worker == four_workers,
            "one_worker": one_worker,
            "four_workers": four_workers,
            "runtime_seconds": timer.seconds,
        },
    )


if __name__ == "__main__":
    main()
