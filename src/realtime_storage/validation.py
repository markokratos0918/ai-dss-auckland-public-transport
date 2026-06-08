"""Validation helpers for final hybrid storage outputs."""

from __future__ import annotations

import pandas as pd

from realtime_storage.config import (
    ALL_PARQUET_PATH,
    COMPLETENESS_PATH,
    MODEL_BASELINE_PARQUET_PATH,
    PARQUET_COLUMNS,
    STORAGE_SUMMARY_PREFIX,
    SUMMARY_DIR,
)


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

    return {
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

