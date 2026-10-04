"""Acceptance 4: narrow-to-wide transfer angle."""

from __future__ import annotations

from experiments.annihilator_gate2a.acceptance.common import Timer, parser, write_result
from experiments.annihilator_gate2a.config import FUNCTIONS
from experiments.annihilator_gate2a.oracle import reference_for
from experiments.annihilator_gate2a.transfer import angle, transfer_coeffs


def main() -> None:
    args = parser().parse_args()
    keys = list(FUNCTIONS)[:3] if args.limit else list(FUNCTIONS)
    records = {}
    with Timer() as timer:
        for key in keys:
            spec = FUNCTIONS[key]
            (r, d), narrow = reference_for(key, "narrow")
            wide_class, wide = reference_for(key, "wide")
            moved = transfer_coeffs(narrow, r, d, spec.narrow, spec.wide)
            value = angle(moved, wide)
            records[key] = {"class_matches": (r, d) == wide_class, "angle": value, "passed": value < 1e-10}
    write_result("accept_04_transfer", {"limit": args.limit, "records": records, "runtime_seconds": timer.seconds})


if __name__ == "__main__":
    main()
