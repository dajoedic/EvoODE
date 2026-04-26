from pathlib import Path

import pandas as pd


def load_run_registry(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Run registry CSV does not exist: {csv_path}")

    df = pd.read_csv(csv_path, sep=",")
    if df.empty:
        raise ValueError(f"Run registry CSV is empty or contains no data rows: {csv_path}")

    return df


def load_aggregate(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Aggregate CSV does not exist: {csv_path}")

    df = pd.read_csv(csv_path, sep=",")
    if df.empty:
        raise ValueError(f"Aggregate CSV is empty or contains no data rows: {csv_path}")

    return df
