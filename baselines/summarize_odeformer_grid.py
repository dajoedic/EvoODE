import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from baselines import harness


OUTPUT_DIR = harness.REPO_ROOT / "analysis" / "data" / "paper1_phaseC_v1" / "odeformer_baseline"


def read_records(path: Path, environment_id: str | None = None) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    else:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    if "odeformer_environment_id" not in frame.columns:
        frame["odeformer_environment_id"] = environment_id or "unknown"
    if environment_id:
        frame["odeformer_environment_id"] = environment_id
    return frame


def success_mask(frame: pd.DataFrame) -> pd.Series:
    return frame["status"].astype(str).eq("success")


def proportion_gt(frame: pd.DataFrame, column: str) -> float:
    if len(frame) == 0:
        return 0.0
    values = pd.to_numeric(frame[column], errors="coerce") if column in frame.columns else pd.Series([float("nan")] * len(frame))
    return float((values > harness.R2_THRESHOLD).sum()) / float(len(frame))


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if frame.empty:
        return pd.DataFrame(rows)
    for (environment_id, config_id, dimension), group in frame.groupby(["odeformer_environment_id", "odeformer_config_id", "dimension"], dropna=False):
        statuses = group["status"].astype(str)
        rows.append(
            {
                "environment_id": environment_id,
                "config_id": config_id,
                "dimension": int(dimension),
                "record_count": int(len(group)),
                "success_count": int(statuses.eq("success").sum()),
                "error_count": int(statuses.eq("error").sum()),
                "timeout_count": int(statuses.eq("timeout").sum()),
                "reconstruction_r2_arithmetic_gt_0_9_count": int((pd.to_numeric(group["reconstruction_r2_arithmetic_mean"], errors="coerce") > harness.R2_THRESHOLD).sum()),
                "reconstruction_r2_arithmetic_gt_0_9_share": proportion_gt(group, "reconstruction_r2_arithmetic_mean"),
                "reconstruction_r2_variance_weighted_gt_0_9_count": int((pd.to_numeric(group["reconstruction_r2_variance_weighted"], errors="coerce") > harness.R2_THRESHOLD).sum()),
                "reconstruction_r2_variance_weighted_gt_0_9_share": proportion_gt(group, "reconstruction_r2_variance_weighted"),
                "generalization_r2_arithmetic_gt_0_9_count": int((pd.to_numeric(group["generalization_r2_arithmetic_mean"], errors="coerce") > harness.R2_THRESHOLD).sum()),
                "generalization_r2_arithmetic_gt_0_9_share": proportion_gt(group, "generalization_r2_arithmetic_mean"),
                "generalization_r2_variance_weighted_gt_0_9_count": int((pd.to_numeric(group["generalization_r2_variance_weighted"], errors="coerce") > harness.R2_THRESHOLD).sum()),
                "generalization_r2_variance_weighted_gt_0_9_share": proportion_gt(group, "generalization_r2_variance_weighted"),
            }
        )
    return pd.DataFrame(rows).sort_values(["environment_id", "config_id", "dimension"]).reset_index(drop=True)


def expression_identity(reference: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    if reference.empty or candidate.empty:
        return pd.DataFrame(
            columns=[
                "config_id",
                "dimension",
                "paired_cell_count",
                "identical_expression_count",
                "identical_expression_share",
            ]
        )
    keys = ["odeformer_config_id", "system_id", "fit_initial_condition_set", "generalization_initial_condition_set"]
    ref = reference[keys + ["dimension", "odeformer_model_canonical"]].rename(columns={"odeformer_model_canonical": "reference_expression"})
    cand = candidate[keys + ["odeformer_model_canonical"]].rename(columns={"odeformer_model_canonical": "candidate_expression"})
    merged = ref.merge(cand, on=keys, how="inner")
    merged["identical_expression"] = merged["reference_expression"].astype(str).eq(merged["candidate_expression"].astype(str))
    rows = []
    for (config_id, dimension), group in merged.groupby(["odeformer_config_id", "dimension"], dropna=False):
        count = int(len(group))
        identical = int(group["identical_expression"].sum())
        rows.append(
            {
                "config_id": config_id,
                "dimension": int(dimension),
                "paired_cell_count": count,
                "identical_expression_count": identical,
                "identical_expression_share": float(identical) / float(count) if count else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["config_id", "dimension"]).reset_index(drop=True)


def run(reference_records: Path | None, candidate_records: Path | None, output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    frames = []
    reference = pd.DataFrame()
    candidate = pd.DataFrame()
    if reference_records is not None:
        reference = read_records(reference_records, "reference")
        frames.append(reference)
    if candidate_records is not None:
        candidate = read_records(candidate_records, "candidate")
        frames.append(candidate)
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(combined)
    identity = expression_identity(reference, candidate)
    paths = {
        "summary": output_dir / "summary.csv",
        "expression_identity": output_dir / "expression_identity.csv",
    }
    summary.to_csv(paths["summary"], index=False)
    identity.to_csv(paths["expression_identity"], index=False)
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize ODEFormer four-configuration grid records.")
    parser.add_argument("--reference-records", default="")
    parser.add_argument("--candidate-records", default="")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = run(
        harness.resolve_path(args.reference_records) if args.reference_records else None,
        harness.resolve_path(args.candidate_records) if args.candidate_records else None,
        harness.resolve_path(args.output_dir),
    )
    for path in paths.values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
