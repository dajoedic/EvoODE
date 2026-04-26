import pandas as pd


def filter_valid_runs(df: pd.DataFrame) -> pd.DataFrame:
    if "loss" not in df.columns:
        raise ValueError("DataFrame is missing required column: loss")

    return df.loc[df["loss"].notna()].copy()


def check_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        missing_columns = ", ".join(missing)
        raise ValueError(f"DataFrame is missing required columns: {missing_columns}")
