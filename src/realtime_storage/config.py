"""Configuration for final hybrid GTFS-Realtime storage outputs."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
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

