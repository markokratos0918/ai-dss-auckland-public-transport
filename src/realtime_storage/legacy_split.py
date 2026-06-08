"""Optional legacy CSV splitting helper."""

from __future__ import annotations

import pandas as pd

from realtime_storage.cleaning import clean_chunk
from realtime_storage.config import CHUNK_SIZE, DAILY_DIR, EXPECTED_RAW_COLUMNS, LEGACY_CSV


def append_daily(df: pd.DataFrame, overwrite: bool = False) -> None:
    """Append cleaned rows into daily CSV files during explicit legacy splitting."""
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    for collection_date, day_df in df.groupby("collection_date"):
        output_path = DAILY_DIR / f"gtfs_realtime_{collection_date}.csv"
        if output_path.exists() and overwrite:
            output_path.unlink()

        file_exists = output_path.exists()
        day_df = day_df[EXPECTED_RAW_COLUMNS]
        day_df.to_csv(output_path, mode="a", header=not file_exists, index=False)


def split_legacy_csv(overwrite_daily: bool = False) -> None:
    """Split the legacy CSV into daily files. Raw source CSV remains unchanged."""
    if not LEGACY_CSV.exists():
        raise FileNotFoundError(f"Legacy CSV not found: {LEGACY_CSV}")

    print(f"Reading legacy CSV in chunks: {LEGACY_CSV}")
    print(f"Writing daily CSV files to: {DAILY_DIR}")

    total_rows = 0
    for chunk in pd.read_csv(LEGACY_CSV, chunksize=CHUNK_SIZE, low_memory=False):
        chunk = clean_chunk(chunk)
        total_rows += len(chunk)
        append_daily(chunk, overwrite=overwrite_daily)
        overwrite_daily = False
        print(f"Processed rows: {total_rows:,}")

