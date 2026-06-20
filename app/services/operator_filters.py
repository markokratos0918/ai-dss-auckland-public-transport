from __future__ import annotations

import streamlit as st

from services.operator_data import (
    ALL_DAYS,
    ALL_HOURS,
    PRIMARY_PARQUET,
    SERVICE_TYPES,
    SPECIAL_SERVICE_LABEL,
    parquet_query,
    sql_path,
)


def available_days() -> list[str]:
    source = f"read_parquet('{sql_path(PRIMARY_PARQUET)}')"
    query = f"""
        SELECT DISTINCT CAST(collection_date AS VARCHAR) AS day
        FROM {source}
        WHERE collection_date IS NOT NULL
        ORDER BY day DESC
    """
    df = parquet_query(query)
    return [ALL_DAYS] + df["day"].dropna().astype(str).tolist() if not df.empty else [ALL_DAYS]


def available_hours() -> list[str]:
    source = f"read_parquet('{sql_path(PRIMARY_PARQUET)}')"
    query = f"""
        SELECT DISTINCT TRY_CAST(trip_hour AS INTEGER) AS hour_value
        FROM {source}
        WHERE trip_hour IS NOT NULL
        ORDER BY hour_value
    """
    df = parquet_query(query)
    hours = [f"{int(hour):02d}:00" for hour in df["hour_value"].dropna().tolist()] if not df.empty else []
    return [ALL_HOURS] + hours


def filter_controls(key_prefix: str = "global") -> tuple[str, bool, str, str]:
    left, middle, right = st.columns([1.05, 1, 0.75])
    with left:
        service_type = st.selectbox(
            "Service type",
            SERVICE_TYPES,
            index=0,
            key=f"{key_prefix}_service_type",
            label_visibility="hidden",
        )
    with middle:
        analysis_day = st.selectbox(
            "Day",
            available_days(),
            index=0,
            key=f"{key_prefix}_day",
            label_visibility="hidden",
        )
    with right:
        analysis_hour = st.selectbox(
            "Hour",
            available_hours(),
            index=0,
            key=f"{key_prefix}_hour",
            label_visibility="hidden",
        )
    return service_type, service_type == SPECIAL_SERVICE_LABEL, analysis_day, analysis_hour
