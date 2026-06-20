from __future__ import annotations

import pandas as pd

from services.operator_data import (
    ALL_DAYS,
    ALL_HOURS,
    SUMMARY_DIR,
    SPECIAL_SERVICE_LABEL,
    from_primary,
    load_dataset,
    load_csv,
    numeric,
    top_non_special_routes,
)


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


OBSERVED_SOURCE_FULL = "31-day observed storage summary"
OBSERVED_SOURCE_BASELINE = "23-day clean AI baseline"


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


def ai_prediction_summary(service_type: str, include_special: bool, day: str, hour: str) -> dict[str, str]:
    query = """
        SELECT
            COUNT(*) AS records,
            AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) AS avg_probability,
            AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)) AS avg_predicted_delay,
            SUM(COALESCE(TRY_CAST(predicted_actionable_delay_risk AS INTEGER), 0)) AS predicted_actionable,
            SUM(COALESCE(TRY_CAST(actual_actionable_delay_risk AS INTEGER), 0)) AS actual_actionable
        FROM {source}
        {where}
    """
    df = from_primary(query, service_type, include_special, day, hour)
    if df.empty:
        return {"Records": "Unavailable", "Avg Probability": "Unavailable", "Avg Predicted Delay": "Unavailable"}
    row = df.iloc[0]
    records = 0 if pd.isna(row.get("records")) else int(row.get("records"))
    avg_probability = row.get("avg_probability")
    avg_delay = row.get("avg_predicted_delay")
    predicted = 0 if pd.isna(row.get("predicted_actionable")) else int(row.get("predicted_actionable"))
    actual = 0 if pd.isna(row.get("actual_actionable")) else int(row.get("actual_actionable"))
    return {
        "Records": f"{records:,}",
        "Avg Probability": "Unavailable" if pd.isna(avg_probability) else f"{avg_probability * 100:.1f}%",
        "Avg Predicted Delay": "Unavailable" if pd.isna(avg_delay) else f"{avg_delay:.2f} min",
        "Predicted Actionable": f"{predicted:,}",
        "Observed Actionable": f"{actual:,}",
    }


def ai_prediction_examples(limit: int, service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = f"""
        SELECT
            CAST(collection_date AS VARCHAR) AS collection_date,
            route_id,
            COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id) AS corridor_name,
            ROUND(TRY_CAST(delay_minutes AS DOUBLE), 3) AS observed_delay,
            ROUND(TRY_CAST(predicted_delay_minutes AS DOUBLE), 3) AS predicted_delay,
            ROUND(TRY_CAST(predicted_actionable_probability AS DOUBLE), 3) AS ai_probability,
            COALESCE(NULLIF(ai_delay_risk, ''), 'Unknown') AS ai_delay_risk,
            COALESCE(NULLIF(ai_recommended_action, ''), 'Unavailable') AS ai_recommended_action
        FROM {{source}}
        {{where}}
        ORDER BY ai_probability DESC NULLS LAST
        LIMIT {int(limit)}
    """
    return from_primary(query, service_type, include_special, day, hour)


def route_prediction_examples(
    route_id: str,
    limit: int,
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
) -> pd.DataFrame:
    query = f"""
        WITH base AS (
            SELECT *
            FROM {{source}}
            {{where}}
        )
        SELECT
            CAST(collection_date AS VARCHAR) AS collection_date,
            route_id,
            COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id) AS corridor_name,
            ROUND(TRY_CAST(delay_minutes AS DOUBLE), 3) AS observed_delay,
            ROUND(TRY_CAST(predicted_delay_minutes AS DOUBLE), 3) AS predicted_delay,
            ROUND(TRY_CAST(predicted_actionable_probability AS DOUBLE), 3) AS ai_probability,
            COALESCE(NULLIF(ai_delay_risk, ''), 'Unknown') AS ai_delay_risk,
            COALESCE(NULLIF(ai_recommended_action, ''), 'Unavailable') AS ai_recommended_action
        FROM base
        WHERE route_id = '{route_id.replace("'", "''")}'
        ORDER BY ai_probability DESC NULLS LAST
        LIMIT {int(limit)}
    """
    return from_primary(query, service_type, include_special, day, hour)


def weather_context(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        SELECT
            CASE WHEN COALESCE(TRY_CAST(rain AS DOUBLE), 0) > 0 THEN 'Rain detected' ELSE 'No rain detected' END AS weather_condition,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_ai_probability_pct,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 3) AS avg_predicted_delay,
            ROUND(AVG(TRY_CAST(wind_speed_10m AS DOUBLE)), 2) AS avg_wind_speed,
            ROUND(AVG(TRY_CAST(precipitation AS DOUBLE)), 2) AS avg_precipitation
        FROM {source}
        {where}
        GROUP BY weather_condition
        ORDER BY records DESC
    """
    return from_primary(query, service_type, include_special, day, hour)


def route_options(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    return top_non_special_routes(100, service_type, include_special, day, hour)


def route_focus(route_id: str, service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = f"""
        WITH base AS (
            SELECT *
            FROM {{source}}
            {{where}}
        )
        SELECT
            route_id,
            COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id) AS corridor_name,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 3) AS avg_predicted_delay,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_ai_probability_pct,
            SUM(CASE WHEN ai_delay_risk IN ('High', 'Severe') THEN 1 ELSE 0 END) AS ai_high_severe_cases,
            COALESCE(mode(ai_recommended_action), 'Unavailable') AS recommended_action
        FROM base
        WHERE route_id = '{route_id.replace("'", "''")}'
        GROUP BY ALL
    """
    return from_primary(query, service_type, include_special, day, hour)


def model_metrics() -> pd.DataFrame:
    return numeric(load_dataset("model_metrics"), ["value"])


def intervention_logic() -> pd.DataFrame:
    return load_dataset("intervention_logic")
