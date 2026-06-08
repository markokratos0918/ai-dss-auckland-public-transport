"""GTFS Static route metadata enrichment helpers."""

from __future__ import annotations

import pandas as pd

from realtime_storage.config import (
    ROUTE_METADATA_COLUMNS,
    ROUTES_PATH,
    SERVICE_TYPE_BY_ROUTE_TYPE,
)


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
    expected_columns = ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"]
    missing_columns = [column for column in expected_columns if column not in routes.columns]
    if missing_columns:
        raise ValueError(f"Missing expected route metadata columns: {missing_columns}")

    routes = routes[expected_columns].copy()
    routes["route_type"] = pd.to_numeric(routes["route_type"], errors="coerce").astype("Int64")
    routes["service_type"] = (
        routes["route_type"].map(SERVICE_TYPE_BY_ROUTE_TYPE).fillna("Unknown / unmatched route")
    )
    routes["route_display_name"] = routes.apply(route_display_name, axis=1)
    return routes[ROUTE_METADATA_COLUMNS]


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

