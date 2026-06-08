"""Raw daily GTFS-Realtime loading and cleaning helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from realtime_storage.config import DAILY_DIR, EXPECTED_RAW_COLUMNS


def count_csv_rows(path: Path) -> tuple[int, int]:
    """Return data rows and repeated header rows without loading the full file."""
    with path.open("r", encoding="utf-8") as file:
        header = file.readline().rstrip("\n")
        if not header:
            return 0, 0

        rows = 0
        duplicate_headers = 0
        for line in file:
            rows += 1
            if line.rstrip("\n") == header:
                duplicate_headers += 1

    return rows, duplicate_headers


def clean_chunk(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw realtime fields and remove accidental header rows."""
    missing_columns = [column for column in EXPECTED_RAW_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    df = df[df["collection_time_utc"] != "collection_time_utc"].copy()
    df["collection_time_utc"] = pd.to_datetime(
        df["collection_time_utc"],
        errors="coerce",
        utc=True,
    )
    df = df.dropna(subset=["collection_time_utc"])

    numeric_columns = [
        "direction_id",
        "start_date",
        "timestamp",
        "delay_seconds",
        "delay_minutes",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["delay_minutes"])
    df["route_id"] = df["route_id"].astype(str)
    df["trip_id"] = df["trip_id"].astype(str)
    df["collection_date"] = df["collection_time_utc"].dt.strftime("%Y-%m-%d")
    return df


def load_daily_frames() -> tuple[pd.DataFrame, list[dict[str, object]], dict[str, int]]:
    """Load raw daily CSV files, clean types, and return file-level counters."""
    daily_paths = sorted(DAILY_DIR.glob("gtfs_realtime_*.csv"))
    if not daily_paths:
        raise FileNotFoundError(f"No daily CSV files found in: {DAILY_DIR}")

    frames = []
    file_stats: list[dict[str, object]] = []
    raw_rows = 0
    duplicate_header_rows = 0

    for path in daily_paths:
        file_rows, file_duplicate_headers = count_csv_rows(path)
        raw_rows += file_rows
        duplicate_header_rows += file_duplicate_headers

        df = pd.read_csv(path, low_memory=False)
        df = clean_chunk(df)
        if not df.empty:
            df["source_file"] = path.name
            frames.append(df)

        collection_date = path.stem.replace("gtfs_realtime_", "")
        file_stats.append(
            {
                "collection_date": collection_date,
                "source_file": path.name,
                "raw_csv_rows": file_rows,
                "duplicate_header_rows": file_duplicate_headers,
            }
        )

    if not frames:
        raise ValueError("Daily CSV files loaded, but no valid rows remained after cleaning.")

    cleaned = pd.concat(frames, ignore_index=True)
    counters = {
        "daily_files": len(daily_paths),
        "raw_csv_rows": raw_rows,
        "duplicate_header_rows": duplicate_header_rows,
    }
    return cleaned, file_stats, counters

