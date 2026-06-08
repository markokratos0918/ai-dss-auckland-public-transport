"""Collection completeness manifest helpers."""

from __future__ import annotations

import pandas as pd

from realtime_storage.config import COMPLETE_DAYS, PARTIAL_DAY_NOTES


def build_completeness_manifest(
    df: pd.DataFrame,
    file_stats: list[dict[str, object]],
) -> pd.DataFrame:
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

