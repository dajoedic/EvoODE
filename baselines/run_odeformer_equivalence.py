import argparse
import json
import sys
from pathlib import Path

from baselines import harness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ODEFormer on the fixed WP-N21 equivalence cell list.")
    parser.add_argument("--config", default="baselines/configs/wp_n19_smoke.json")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    config_path = harness.resolve_path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["system_ids"] = [1, 2, 24]
    config["methods"] = ["odeformer"]
    temp_config = harness.resolve_path(args.output_dir) / "effective_config.json"
    temp_config.parent.mkdir(parents=True, exist_ok=True)
    temp_config.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records_path = harness.run(temp_config, args.output_dir)
    print(records_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
