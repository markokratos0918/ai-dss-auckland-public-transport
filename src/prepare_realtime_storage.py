"""
Prepare scalable GTFS-Realtime storage outputs.

Purpose:
- Preserve raw daily GTFS-Realtime CSV files as archival evidence.
- Build a cleaned Parquet file for analysis and dashboard loading.
- Create small summary CSV files that are safe to open in Excel.
- Optionally split the legacy single CSV log into daily CSV files.

Run from project root:
    python src/prepare_realtime_storage.py

Legacy split, only when explicitly needed:
    python src/prepare_realtime_storage.py --split-legacy
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs_realtime"
LEGACY_CSV = RAW_DIR / "gtfs_realtime_log.csv"
DAILY_DIR = RAW_DIR / "daily"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SUMMARY_DIR = PROJECT_ROOT / "data" / "processed" / "summaries"
PARQUET_PATH = PROCESSED_DIR / "gtfs_realtime_cleaned.parquet"
STORAGE_SUMMARY_PREFIX = "gtfs_realtime_storage"

CHUNK_SIZE = 200_000
EXPECTED_COLUMNS = [
    "collection_time_utc",
    "entity_id",
    "trip_id",
    "route_id",
    "direction_id",
    "start_time",
    "start_date",
    "timestamp",
    "delay_seconds",
    "is_deleted",
    "delay_minutes",
]


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
    """Normalize types and remove accidental header rows from appended CSV logs."""
    missing_columns = [column for column in EXPECTED_COLUMNS if column not in df.columns]
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

    df["collection_date"] = df["collection_time_utc"].dt.strftime("%Y-%m-%d")
    return df


def append_daily(df: pd.DataFrame, overwrite: bool = False) -> None:
    """Append cleaned rows into daily CSV files."""
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    for collection_date, day_df in df.groupby("collection_date"):
        output_path = DAILY_DIR / f"gtfs_realtime_{collection_date}.csv"
        if output_path.exists() and overwrite:
            output_path.unlink()

        file_exists = output_path.exists()

        day_df = day_df[EXPECTED_COLUMNS]
        day_df.to_csv(
            output_path,
            mode="a",
            header=not file_exists,
            index=False,
        )


def load_clean_daily_files() -> tuple[pd.DataFrame, dict[str, int]]:
    """Load raw daily CSV files, clean types, and return validation counters."""
    daily_paths = sorted(DAILY_DIR.glob("gtfs_realtime_*.csv"))
    if not daily_paths:
        raise FileNotFoundError(f"No daily CSV files found in: {DAILY_DIR}")

    frames = []
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

    if not frames:
        raise ValueError("Daily CSV files loaded, but no valid rows remained after cleaning.")

    cleaned = pd.concat(frames, ignore_index=True)
    counters = {
        "daily_files": len(daily_paths),
        "raw_csv_rows": raw_rows,
        "duplicate_header_rows": duplicate_header_rows,
        "cleaned_rows": len(cleaned),
    }
    return cleaned, counters


def create_parquet(df: pd.DataFrame) -> None:
    """Write cleaned realtime rows to Parquet for scalable local analytics."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    parquet_columns = EXPECTED_COLUMNS + ["collection_date", "source_file"]
    try:
        df[parquet_columns].to_parquet(PARQUET_PATH, index=False)
    except ImportError as exc:
        raise ImportError(
            "Parquet output requires pyarrow or fastparquet. Install project "
            "requirements, then rerun this script."
        ) from exc


def create_summaries(df: pd.DataFrame) -> None:
    """Create storage-specific CSV summaries that are safe to open in Excel."""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    daily_summary = (
        df.groupby("collection_date")
        .agg(
            records=("trip_id", "size"),
            unique_routes=("route_id", "nunique"),
            unique_trips=("trip_id", "nunique"),
            avg_delay_minutes=("delay_minutes", "mean"),
            min_delay_minutes=("delay_minutes", "min"),
            max_delay_minutes=("delay_minutes", "max"),
        )
        .reset_index()
    )
    daily_summary.to_csv(
        SUMMARY_DIR / f"{STORAGE_SUMMARY_PREFIX}_daily_summary.csv",
        index=False,
    )

    route_summary = (
        df.groupby(["collection_date", "route_id"])
        .agg(
            records=("trip_id", "size"),
            unique_trips=("trip_id", "nunique"),
            avg_delay_minutes=("delay_minutes", "mean"),
            max_delay_minutes=("delay_minutes", "max"),
        )
        .reset_index()
    )
    route_summary.to_csv(
        SUMMARY_DIR / f"{STORAGE_SUMMARY_PREFIX}_route_daily_summary.csv",
        index=False,
    )

    top_routes = (
        route_summary.groupby("route_id")
        .agg(
            records=("records", "sum"),
            avg_delay_minutes=("avg_delay_minutes", "mean"),
            max_delay_minutes=("max_delay_minutes", "max"),
        )
        .sort_values(["avg_delay_minutes", "records"], ascending=[False, False])
        .head(50)
        .reset_index()
    )
    top_routes.to_csv(
        SUMMARY_DIR / f"{STORAGE_SUMMARY_PREFIX}_top_delayed_routes.csv",
        index=False,
    )


def validate_parquet(expected_rows: int) -> dict[str, object]:
    """Load the Parquet file and return storage sanity checks."""
    parquet_df = pd.read_parquet(PARQUET_PATH)
    expected_columns = EXPECTED_COLUMNS + ["collection_date", "source_file"]

    return {
        "parquet_path": str(PARQUET_PATH.relative_to(PROJECT_ROOT)),
        "parquet_rows": len(parquet_df),
        "row_count_matches": len(parquet_df) == expected_rows,
        "columns_match": list(parquet_df.columns) == expected_columns,
        "delay_minutes_numeric": pd.api.types.is_numeric_dtype(parquet_df["delay_minutes"]),
        "collection_time_utc_datetime": pd.api.types.is_datetime64_any_dtype(
            parquet_df["collection_time_utc"]
        ),
        "parquet_size_mb": round(PARQUET_PATH.stat().st_size / 1024 / 1024, 2),
    }


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split-legacy",
        action="store_true",
        help="Split the legacy gtfs_realtime_log.csv into daily CSV files.",
    )
    parser.add_argument(
        "--overwrite-daily",
        action="store_true",
        help="Overwrite daily CSV outputs during --split-legacy.",
    )
    args = parser.parse_args()

    if args.split_legacy:
        split_legacy_csv(overwrite_daily=args.overwrite_daily)

    print(f"Loading daily CSV files from: {DAILY_DIR}")
    realtime_df, counters = load_clean_daily_files()

    print(f"Writing cleaned Parquet file: {PARQUET_PATH}")
    create_parquet(realtime_df)

    print(f"Writing summary CSV files to: {SUMMARY_DIR}")
    create_summaries(realtime_df)

    validation = validate_parquet(expected_rows=counters["cleaned_rows"])
    print("Done.")
    print("Storage validation:")
    print(f"- Daily files: {counters['daily_files']:,}")
    print(f"- Raw CSV rows: {counters['raw_csv_rows']:,}")
    print(f"- Duplicate header rows removed: {counters['duplicate_header_rows']:,}")
    print(f"- Cleaned rows: {counters['cleaned_rows']:,}")
    print(f"- Parquet rows: {validation['parquet_rows']:,}")
    print(f"- Row count matches: {validation['row_count_matches']}")
    print(f"- Columns match expected schema: {validation['columns_match']}")
    print(f"- delay_minutes numeric: {validation['delay_minutes_numeric']}")
    print(f"- collection_time_utc datetime: {validation['collection_time_utc_datetime']}")
    print(f"- Parquet size MB: {validation['parquet_size_mb']}")


if __name__ == "__main__":
    main()
