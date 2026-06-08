"""
Prepare final hybrid GTFS-Realtime storage outputs.

Purpose:
- Preserve raw daily GTFS-Realtime CSV files as archival evidence.
- Build an all-file cleaned Parquet dataset for descriptive analysis and dashboard coverage.
- Build a complete-day model-baseline Parquet dataset for AI modelling and evaluation.
- Enrich realtime rows with GTFS Static route metadata where available.
- Create GitHub-safe storage summary CSV files.
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
ROUTES_PATH = PROJECT_ROOT / "data" / "raw" / "gtfs_static" / "routes.txt"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PARQUET_DIR = PROCESSED_DIR / "parquet"
SUMMARY_DIR = PROCESSED_DIR / "summaries"

ALL_PARQUET_PATH = PARQUET_DIR / "gtfs_realtime_cleaned.parquet"
MODEL_BASELINE_PARQUET_PATH = PARQUET_DIR / "gtfs_realtime_model_baseline.parquet"
COMPLETENESS_PATH = SUMMARY_DIR / "gtfs_realtime_collection_completeness.csv"
STORAGE_SUMMARY_PREFIX = "gtfs_realtime_storage"

CHUNK_SIZE = 200_000
EXPECTED_RAW_COLUMNS = [
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

COMPLETE_DAYS = {
    "2026-05-09",
    "2026-05-10",
    "2026-05-11",
    "2026-05-15",
    "2026-05-16",
    "2026-05-17",
    "2026-05-18",
    "2026-05-19",
    "2026-05-20",
    "2026-05-21",
    "2026-05-22",
    "2026-05-23",
    "2026-05-24",
    "2026-05-25",
    "2026-05-26",
    "2026-05-28",
    "2026-05-29",
    "2026-05-30",
    "2026-05-31",
    "2026-06-01",
    "2026-06-02",
    "2026-06-03",
    "2026-06-04",
}

PARTIAL_DAY_NOTES = {
    "2026-05-06": "startup partial",
    "2026-05-07": "startup partial",
    "2026-05-08": "startup partial",
    "2026-05-12": "interrupted partial",
    "2026-05-13": "interrupted partial",
    "2026-05-14": "interrupted partial",
    "2026-05-27": "interrupted partial",
    "2026-06-05": "current/incomplete at audit time",
}

SERVICE_TYPE_BY_ROUTE_TYPE = {
    2: "Train / Rail",
    3: "Bus",
    4: "Ferry",
}

ROUTE_METADATA_COLUMNS = [
    "route_id",
    "agency_id",
    "route_short_name",
    "route_long_name",
    "route_type",
    "service_type",
    "route_display_name",
]

DERIVED_COLUMNS = [
    "collection_date",
    "source_file",
    "collection_day_status",
    "collection_coverage_hours",
    "is_partial_day",
    "is_model_baseline_day",
    "agency_id",
    "route_short_name",
    "route_long_name",
    "route_type",
    "service_type",
    "route_display_name",
    "is_special_route",
]

PARQUET_COLUMNS = EXPECTED_RAW_COLUMNS + DERIVED_COLUMNS


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


def route_display_name(row: pd.Series) -> str:
    """Build an operator-readable route label from GTFS Static metadata."""
    short_name = str(row.get("route_short_name", "") or "").strip()
    long_name = str(row.get("route_long_name", "") or "").strip()
    route_id = str(row.get("route_id", "") or "").strip()

    if short_name and long_name and short_name != long_name:
        return f"{short_name} - {long_name}"
    if long_name:
        return long_name
    if short_name:
        return short_name
    return route_id


def load_route_metadata() -> pd.DataFrame:
    """Load GTFS Static route metadata used for dashboard labels and service type."""
    if not ROUTES_PATH.exists():
        raise FileNotFoundError(f"GTFS Static routes file not found: {ROUTES_PATH}")

    routes = pd.read_csv(ROUTES_PATH, dtype=str)
    missing_columns = [
        column
        for column in ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"]
        if column not in routes.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing expected route metadata columns: {missing_columns}")

    routes = routes[["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"]].copy()
    routes["route_type"] = pd.to_numeric(routes["route_type"], errors="coerce").astype("Int64")
    routes["service_type"] = (
        routes["route_type"].map(SERVICE_TYPE_BY_ROUTE_TYPE).fillna("Unknown / unmatched route")
    )
    routes["route_display_name"] = routes.apply(route_display_name, axis=1)
    return routes[ROUTE_METADATA_COLUMNS]


def build_completeness_manifest(df: pd.DataFrame, file_stats: list[dict[str, object]]) -> pd.DataFrame:
    """Create the daily completeness manifest used by hybrid storage outputs."""
    daily_metrics = (
        df.groupby("collection_date")
        .agg(
            cleaned_rows=("trip_id", "size"),
            unique_routes=("route_id", "nunique"),
            unique_trips=("trip_id", "nunique"),
            first_collection_time_utc=("collection_time_utc", "min"),
            last_collection_time_utc=("collection_time_utc", "max"),
            delay_outliers_abs_gt_120=("delay_minutes", lambda values: int(values.abs().gt(120).sum())),
        )
        .reset_index()
    )
    daily_metrics["collection_coverage_hours"] = (
        (
            daily_metrics["last_collection_time_utc"]
            - daily_metrics["first_collection_time_utc"]
        )
        .dt.total_seconds()
        .div(3600)
        .round(2)
    )

    stats = pd.DataFrame(file_stats)
    manifest = daily_metrics.merge(stats, on="collection_date", how="left")
    manifest["collection_day_status"] = manifest["collection_date"].apply(
        lambda value: "likely_complete" if value in COMPLETE_DAYS else "partial_or_interrupted"
    )
    manifest["is_model_baseline_day"] = manifest["collection_date"].isin(COMPLETE_DAYS)
    manifest["is_partial_day"] = ~manifest["is_model_baseline_day"]
    manifest["collection_note"] = manifest["collection_date"].map(PARTIAL_DAY_NOTES).fillna("")

    columns = [
        "collection_date",
        "collection_day_status",
        "collection_note",
        "is_model_baseline_day",
        "is_partial_day",
        "collection_coverage_hours",
        "raw_csv_rows",
        "cleaned_rows",
        "duplicate_header_rows",
        "unique_routes",
        "unique_trips",
        "first_collection_time_utc",
        "last_collection_time_utc",
        "delay_outliers_abs_gt_120",
        "source_file",
    ]
    return manifest[columns].sort_values("collection_date").reset_index(drop=True)


def enrich_with_hybrid_fields(df: pd.DataFrame, completeness: pd.DataFrame) -> pd.DataFrame:
    """Add completeness flags and GTFS Static route metadata."""
    routes = load_route_metadata()
    enriched = df.merge(
        completeness[
            [
                "collection_date",
                "collection_day_status",
                "collection_coverage_hours",
                "is_partial_day",
                "is_model_baseline_day",
            ]
        ],
        on="collection_date",
        how="left",
    )
    enriched = enriched.merge(routes, on="route_id", how="left")
    enriched["route_type"] = enriched["route_type"].astype("Int64")
    enriched["service_type"] = enriched["service_type"].fillna("Unknown / unmatched route")
    enriched["route_display_name"] = enriched["route_display_name"].fillna(enriched["route_id"])
    enriched["is_special_route"] = enriched["route_id"].astype(str).str.startswith("S")
    return enriched


def load_clean_daily_files() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Load raw daily CSV files, clean types, and return validation counters."""
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
    completeness = build_completeness_manifest(cleaned, file_stats)
    enriched = enrich_with_hybrid_fields(cleaned, completeness)

    counters = {
        "daily_files": len(daily_paths),
        "raw_csv_rows": raw_rows,
        "duplicate_header_rows": duplicate_header_rows,
        "cleaned_rows": len(enriched),
        "complete_days": int(completeness["is_model_baseline_day"].sum()),
        "partial_days": int(completeness["is_partial_day"].sum()),
        "model_baseline_rows": int(enriched["is_model_baseline_day"].sum()),
        "delay_outliers_abs_gt_120": int(enriched["delay_minutes"].abs().gt(120).sum()),
    }
    return enriched, completeness, counters


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


def create_summaries(df: pd.DataFrame, completeness: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create storage summary CSVs that are safe to review and commit."""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    completeness.to_csv(COMPLETENESS_PATH, index=False)

    daily_summary = (
        df.groupby(
            [
                "collection_date",
                "collection_day_status",
                "is_model_baseline_day",
                "is_partial_day",
            ],
            dropna=False,
        )
        .agg(
            records=("trip_id", "size"),
            unique_routes=("route_id", "nunique"),
            unique_trips=("trip_id", "nunique"),
            avg_delay_minutes=("delay_minutes", "mean"),
            min_delay_minutes=("delay_minutes", "min"),
            max_delay_minutes=("delay_minutes", "max"),
            delay_outliers_abs_gt_120=("delay_minutes", lambda values: int(values.abs().gt(120).sum())),
        )
        .reset_index()
    )
    daily_summary.to_csv(SUMMARY_DIR / f"{STORAGE_SUMMARY_PREFIX}_daily_summary.csv", index=False)

    route_summary = (
        df.groupby(
            [
                "collection_date",
                "collection_day_status",
                "is_model_baseline_day",
                "route_id",
                "service_type",
                "route_display_name",
                "is_special_route",
            ],
            dropna=False,
        )
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

    default_rank_source = route_summary[~route_summary["is_special_route"]].copy()
    top_routes = (
        default_rank_source.groupby(
            ["route_id", "service_type", "route_display_name", "is_special_route"],
            dropna=False,
        )
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

    return daily_summary, route_summary, top_routes


def validate_outputs(
    expected_rows: int,
    expected_model_rows: int,
    expected_route_summary_rows: int,
    expected_complete_days: int,
    expected_partial_days: int,
) -> dict[str, object]:
    """Load generated outputs and return final storage sanity checks."""
    all_df = pd.read_parquet(ALL_PARQUET_PATH)
    model_df = pd.read_parquet(MODEL_BASELINE_PARQUET_PATH)
    top_routes = pd.read_csv(SUMMARY_DIR / f"{STORAGE_SUMMARY_PREFIX}_top_delayed_routes.csv")
    route_summary = pd.read_csv(SUMMARY_DIR / f"{STORAGE_SUMMARY_PREFIX}_route_daily_summary.csv")
    completeness = pd.read_csv(COMPLETENESS_PATH)

    matched_rows = int(all_df["route_type"].notna().sum())
    special_rows = int(all_df["is_special_route"].sum())
    route_match_rate = round(matched_rows / len(all_df) * 100, 2) if len(all_df) else 0

    validation = {
        "all_parquet_rows": len(all_df),
        "model_baseline_rows": len(model_df),
        "all_row_count_matches": len(all_df) == expected_rows,
        "model_row_count_matches": len(model_df) == expected_model_rows,
        "model_only_complete_days": bool(model_df["is_model_baseline_day"].all()),
        "daily_files": len(completeness),
        "complete_days": int(completeness["is_model_baseline_day"].sum()),
        "partial_days": int(completeness["is_partial_day"].sum()),
        "complete_day_count_matches": int(completeness["is_model_baseline_day"].sum())
        == expected_complete_days,
        "partial_day_count_matches": int(completeness["is_partial_day"].sum())
        == expected_partial_days,
        "duplicate_header_rows": int(completeness["duplicate_header_rows"].sum()),
        "columns_match": list(all_df.columns) == PARQUET_COLUMNS,
        "delay_minutes_numeric": pd.api.types.is_numeric_dtype(all_df["delay_minutes"]),
        "collection_time_utc_datetime": pd.api.types.is_datetime64_any_dtype(
            all_df["collection_time_utc"]
        ),
        "route_metadata_matched_rows": matched_rows,
        "route_metadata_row_match_rate_percent": route_match_rate,
        "service_type_present": "service_type" in all_df.columns,
        "route_display_name_present": "route_display_name" in all_df.columns,
        "route_display_name_missing_rows": int(all_df["route_display_name"].isna().sum()),
        "is_special_route_present": "is_special_route" in all_df.columns,
        "s_prefix_rows_flagged": special_rows,
        "top_routes_excludes_s_prefix": not top_routes["is_special_route"].astype(bool).any(),
        "route_summary_rows": len(route_summary),
        "route_summary_row_count_matches": len(route_summary) == expected_route_summary_rows,
        "all_parquet_size_mb": round(ALL_PARQUET_PATH.stat().st_size / 1024 / 1024, 2),
        "model_parquet_size_mb": round(
            MODEL_BASELINE_PARQUET_PATH.stat().st_size / 1024 / 1024,
            2,
        ),
    }

    return validation


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
    realtime_df, completeness, counters = load_clean_daily_files()

    print(f"Writing Parquet files to: {PARQUET_DIR}")
    all_df, model_df = write_parquet_outputs(realtime_df)

    print(f"Writing summary CSV files to: {SUMMARY_DIR}")
    _, route_summary, _ = create_summaries(all_df, completeness)

    validation = validate_outputs(
        expected_rows=counters["cleaned_rows"],
        expected_model_rows=counters["model_baseline_rows"],
        expected_route_summary_rows=len(route_summary),
        expected_complete_days=counters["complete_days"],
        expected_partial_days=counters["partial_days"],
    )

    print("Done.")
    print("Hybrid storage validation:")
    print(f"- Daily files: {counters['daily_files']:,}")
    print(f"- Raw CSV rows: {counters['raw_csv_rows']:,}")
    print(f"- Duplicate header rows removed: {counters['duplicate_header_rows']:,}")
    print(f"- Delay outliers beyond +/-120 minutes: {counters['delay_outliers_abs_gt_120']:,}")
    print(f"- All-file cleaned rows: {validation['all_parquet_rows']:,}")
    print(f"- Model-baseline rows: {validation['model_baseline_rows']:,}")
    print(f"- Likely complete days: {validation['complete_days']:,}")
    print(f"- Partial/interrupted days: {validation['partial_days']:,}")
    print(f"- All row count matches: {validation['all_row_count_matches']}")
    print(f"- Model row count matches: {validation['model_row_count_matches']}")
    print(f"- Model baseline only complete days: {validation['model_only_complete_days']}")
    print(f"- Columns match expected schema: {validation['columns_match']}")
    print(f"- delay_minutes numeric: {validation['delay_minutes_numeric']}")
    print(f"- collection_time_utc datetime: {validation['collection_time_utc_datetime']}")
    print(
        "- Route metadata row match rate: "
        f"{validation['route_metadata_row_match_rate_percent']}%"
    )
    print(f"- S-prefix rows flagged: {validation['s_prefix_rows_flagged']:,}")
    print(f"- Default top delayed routes exclude S-prefix: {validation['top_routes_excludes_s_prefix']}")
    print(f"- All-file Parquet size MB: {validation['all_parquet_size_mb']}")
    print(f"- Model-baseline Parquet size MB: {validation['model_parquet_size_mb']}")
    print("DuckDB query layer is handled separately by src/create_realtime_duckdb.py")


if __name__ == "__main__":
    main()
