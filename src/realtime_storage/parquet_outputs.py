"""Parquet output helpers for hybrid GTFS-Realtime storage."""

from __future__ import annotations

import pandas as pd

from realtime_storage.config import (
    ALL_PARQUET_PATH,
    MODEL_BASELINE_PARQUET_PATH,
    PARQUET_COLUMNS,
    PARQUET_DIR,
)


def write_parquet_outputs(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Write all-file and model-baseline Parquet datasets."""
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    all_df = df[PARQUET_COLUMNS].copy()
    model_df = all_df[all_df["is_model_baseline_day"]].copy()

    try:
        all_df.to_parquet(ALL_PARQUET_PATH, index=False)
        model_df.to_parquet(MODEL_BASELINE_PARQUET_PATH, index=False)
    except ImportError as exc:
        raise ImportError(
            "Parquet output requires pyarrow or fastparquet. Install project "
            "requirements, then rerun this script."
        ) from exc

    return all_df, model_df

