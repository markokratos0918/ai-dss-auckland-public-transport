"""Data loading and split helpers for the AI-DSS modeling checkpoint."""

import pandas as pd

from ai_dss_modeling.config import (
    CATEGORICAL_FEATURES,
    INPUT_CSV,
    INPUT_PARQUET,
    MAX_MODEL_ROWS,
    NUMERIC_FEATURES,
    RANDOM_STATE,
    ROOT,
    TEST_DATE_SHARE,
    USE_COLUMNS,
)


def rel(path):
    return path.relative_to(ROOT).as_posix()


def abort(message: str) -> None:
    raise SystemExit(f"AI-DSS modeling failed: {message}")


def input_path():
    if INPUT_PARQUET.exists():
        return INPUT_PARQUET, "parquet"
    if INPUT_CSV.exists():
        return INPUT_CSV, "csv_fallback"
    abort(
        f"`{rel(INPUT_PARQUET)}` is missing, and fallback `{rel(INPUT_CSV)}` is also missing. "
        "Run the Notebook 09 model-baseline export and M1 Parquet conversion first."
    )


def read_input() -> pd.DataFrame:
    path, source = input_path()
    try:
        if source == "parquet":
            df = pd.read_parquet(path, columns=USE_COLUMNS)
        else:
            df = pd.read_csv(path, usecols=USE_COLUMNS)
    except ValueError:
        if source == "parquet":
            columns = pd.read_parquet(path).columns
        else:
            columns = pd.read_csv(path, nrows=0).columns
        missing = sorted(set(USE_COLUMNS) - set(columns))
        abort(f"required modeling columns are missing: {missing}")

    df["collection_time_utc"] = pd.to_datetime(df["collection_time_utc"], errors="coerce", utc=True)
    df["collection_date"] = pd.to_datetime(df["collection_date"], errors="coerce").dt.date.astype(str)
    for column in NUMERIC_FEATURES + ["delay_minutes"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in CATEGORICAL_FEATURES + ["route_short_name", "delay_risk", "recommended_action"]:
        df[column] = df[column].astype("string").fillna("missing")

    df = df.dropna(subset=["collection_time_utc", "collection_date", "delay_minutes", "delay_risk"]).copy()
    df["actionable_delay_risk"] = (df["delay_risk"] != "Low").astype(int)
    return df


def sample_for_modeling(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) <= MAX_MODEL_ROWS:
        return df.copy()
    return (
        df.groupby(["collection_date", "delay_risk"], group_keys=False, dropna=False)
        .sample(frac=MAX_MODEL_ROWS / len(df), random_state=RANDOM_STATE)
        .sort_values("collection_time_utc")
        .reset_index(drop=True)
    )


def time_split(df: pd.DataFrame):
    dates = sorted(df["collection_date"].dropna().unique().tolist())
    if len(dates) < 5:
        abort("not enough collection dates for a defensible time-based split.")
    test_count = max(1, int(round(len(dates) * TEST_DATE_SHARE)))
    train_dates = dates[:-test_count]
    test_dates = dates[-test_count:]
    train_df = df[df["collection_date"].isin(train_dates)].copy()
    test_df = df[df["collection_date"].isin(test_dates)].copy()
    if train_df.empty or test_df.empty:
        abort("time-based split produced an empty train or test set.")
    return train_df, test_df, train_dates, test_dates
