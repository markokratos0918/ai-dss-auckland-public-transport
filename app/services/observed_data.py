from __future__ import annotations

import pandas as pd

from services.operator_data import (
    ALL_DAYS,
    ALL_HOURS,
    SUMMARY_DIR,
    SPECIAL_SERVICE_LABEL,
    from_primary,
    load_csv,
)


OBSERVED_SOURCE_FULL = "31-day observed storage summary"
OBSERVED_SOURCE_BASELINE = "23-day clean AI baseline"


def _observed_summary_filter(df: pd.DataFrame, service_type: str, include_special: bool, day: str) -> pd.DataFrame:
    filtered = df.copy()
    if day != ALL_DAYS and "collection_date" in filtered.columns:
        filtered = filtered[filtered["collection_date"].astype(str) == day]
    if "is_special_route" in filtered.columns:
        special = filtered["is_special_route"].astype(bool)
        s_prefix = filtered["route_id"].astype(str).str.upper().str.startswith("S") if "route_id" in filtered.columns else False
        if service_type == SPECIAL_SERVICE_LABEL:
            filtered = filtered[special | s_prefix]
        elif not include_special:
            filtered = filtered[~(special | s_prefix)]
    if service_type not in ("All", SPECIAL_SERVICE_LABEL) and "service_type" in filtered.columns:
        filtered = filtered[filtered["service_type"].fillna("Unknown / unmatched route") == service_type]
    return filtered


def _route_corridor_lookup() -> pd.DataFrame:
    summary = load_csv(str(SUMMARY_DIR / "route_delay_risk_summary.csv"))
    if summary.empty or "route_id" not in summary.columns or "route_corridor_name" not in summary.columns:
        return pd.DataFrame(columns=["route_id", "corridor_name"])
    lookup = summary[["route_id", "route_corridor_name"]].dropna().copy()
    lookup["route_id"] = lookup["route_id"].astype(str)
    lookup["route_corridor_name"] = lookup["route_corridor_name"].astype(str)
    lookup = lookup[lookup["route_corridor_name"].str.strip() != ""]
    lookup = lookup.drop_duplicates(subset=["route_id"], keep="first")
    return lookup.rename(columns={"route_corridor_name": "corridor_name"})


def observed_daily(
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
    source_mode: str = OBSERVED_SOURCE_FULL,
) -> pd.DataFrame:
    if source_mode == OBSERVED_SOURCE_BASELINE:
        query = """
            SELECT
                CAST(collection_date AS VARCHAR) AS collection_date,
                COUNT(*) AS records,
                ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
                ROUND(MAX(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS max_observed_delay,
                SUM(CASE WHEN delay_risk IN ('High', 'Severe') THEN 1 ELSE 0 END) AS high_severe_cases
            FROM {source}
            {where}
            GROUP BY collection_date
            ORDER BY collection_date
        """
        return from_primary(query, service_type, include_special, day, hour)

    route_daily = load_csv(str(SUMMARY_DIR / "gtfs_realtime_storage_route_daily_summary.csv"))
    if route_daily.empty:
        return pd.DataFrame()
    route_daily = _observed_summary_filter(route_daily, service_type, include_special, day)
    if route_daily.empty:
        return pd.DataFrame()
    route_daily["records"] = pd.to_numeric(route_daily["records"], errors="coerce").fillna(0)
    route_daily["avg_delay_minutes"] = pd.to_numeric(route_daily["avg_delay_minutes"], errors="coerce")
    route_daily["max_delay_minutes"] = pd.to_numeric(route_daily["max_delay_minutes"], errors="coerce")
    route_daily["weighted_delay"] = route_daily["avg_delay_minutes"] * route_daily["records"]
    daily = (
        route_daily.groupby("collection_date", as_index=False)
        .agg(
            records=("records", "sum"),
            weighted_delay=("weighted_delay", "sum"),
            max_observed_delay=("max_delay_minutes", "max"),
        )
        .sort_values("collection_date")
    )
    daily["avg_observed_delay"] = (daily["weighted_delay"] / daily["records"]).round(3)
    return daily[["collection_date", "records", "avg_observed_delay", "max_observed_delay"]]


def top_observed_routes(
    limit: int,
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
    source_mode: str = OBSERVED_SOURCE_FULL,
) -> pd.DataFrame:
    if source_mode == OBSERVED_SOURCE_BASELINE:
        query = f"""
            SELECT
                route_id,
                COALESCE(NULLIF(service_type, ''), 'Unknown / unmatched route') AS service_type,
                COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id) AS corridor_name,
                COALESCE(NULLIF(route_display_name, ''), route_short_name, route_id) AS route_name,
                COUNT(*) AS records,
                ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
                ROUND(MAX(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS max_observed_delay,
                SUM(CASE WHEN delay_risk IN ('High', 'Severe') THEN 1 ELSE 0 END) AS high_severe_cases
            FROM {{source}}
            {{where}}
            GROUP BY ALL
            ORDER BY avg_observed_delay DESC, high_severe_cases DESC
            LIMIT {int(limit)}
        """
        return from_primary(query, service_type, include_special, day, hour)

    route_daily = load_csv(str(SUMMARY_DIR / "gtfs_realtime_storage_route_daily_summary.csv"))
    if route_daily.empty:
        return pd.DataFrame()
    route_daily = _observed_summary_filter(route_daily, service_type, include_special, day)
    if route_daily.empty:
        return pd.DataFrame()
    route_daily["records"] = pd.to_numeric(route_daily["records"], errors="coerce").fillna(0)
    route_daily["avg_delay_minutes"] = pd.to_numeric(route_daily["avg_delay_minutes"], errors="coerce")
    route_daily["max_delay_minutes"] = pd.to_numeric(route_daily["max_delay_minutes"], errors="coerce")
    route_daily["weighted_delay"] = route_daily["avg_delay_minutes"] * route_daily["records"]
    routes = (
        route_daily.groupby(
            ["route_id", "service_type", "route_display_name", "is_special_route"],
            as_index=False,
        )
        .agg(
            records=("records", "sum"),
            weighted_delay=("weighted_delay", "sum"),
            max_observed_delay=("max_delay_minutes", "max"),
        )
    )
    routes["avg_observed_delay"] = (routes["weighted_delay"] / routes["records"]).round(3)
    lookup = _route_corridor_lookup()
    if not lookup.empty:
        routes["route_id"] = routes["route_id"].astype(str)
        routes = routes.merge(lookup, on="route_id", how="left")
    else:
        routes["corridor_name"] = routes["route_display_name"]
    routes["corridor_name"] = routes["corridor_name"].fillna(routes["route_display_name"])
    routes = routes.sort_values(["avg_observed_delay", "max_observed_delay"], ascending=[False, False]).head(limit)
    return routes[
        [
            "route_id",
            "service_type",
            "corridor_name",
            "route_display_name",
            "is_special_route",
            "records",
            "avg_observed_delay",
            "max_observed_delay",
        ]
    ]
