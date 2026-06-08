"""Storage summary output helpers."""

from __future__ import annotations

import pandas as pd

from realtime_storage.config import COMPLETENESS_PATH, STORAGE_SUMMARY_PREFIX, SUMMARY_DIR


def create_summaries(
    df: pd.DataFrame,
    completeness: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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

    top_routes = (
        route_summary[~route_summary["is_special_route"]]
        .groupby(["route_id", "service_type", "route_display_name", "is_special_route"], dropna=False)
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

