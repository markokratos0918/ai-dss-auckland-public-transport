from __future__ import annotations

import pandas as pd

from services.operator_data import from_primary, top_non_special_routes


RISK_FILTERS = ["All", "Low", "Medium", "High", "Severe"]


def format_route_label(route_id: str, corridor_name: str, max_length: int = 30) -> str:
    if corridor_name and corridor_name != route_id:
        return f"{route_id} \u2014 {corridor_name}"
    return route_id



def search_routes(routes_df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    """Filter routes by search text matching route_id or corridor name."""
    if not search_text.strip():
        return routes_df
    search_lower = search_text.lower()
    return routes_df[
        routes_df["route_id"].str.lower().str.contains(search_lower, na=False)
        | routes_df["route_corridor_name"].str.lower().str.contains(search_lower, na=False)
    ]


def route_options_by_risk(
    risk: str,
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
) -> pd.DataFrame:
    risk = risk or "All"
    if risk == "All":
        return top_non_special_routes(100, service_type, include_special, day, hour)
    safe_risk = str(risk).replace("'", "''")
    query = f"""
        WITH base AS (
            SELECT * FROM {{source}} {{where}}
        )
        SELECT
            COALESCE(NULLIF(service_type, ''), 'School/Special or unmatched services') AS service_type,
            route_id,
            REGEXP_REPLACE(COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id), '^[A-Z0-9]+ - ', '') AS route_corridor_name,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 2) AS avg_delay_minutes,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_prediction_probability,
            COALESCE(mode(ai_recommended_action), 'Unavailable') AS recommended_action
        FROM base
        WHERE ai_delay_risk = '{safe_risk}'
        GROUP BY ALL
        ORDER BY records DESC, avg_prediction_probability DESC
        LIMIT 100
    """
    return from_primary(query, service_type, include_special, day, hour)


def table_without_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return df.drop(columns=[column for column in columns if column in df.columns])


PREDICTION_BAND_LEGEND = (
    "**AI reliability risk is a probability band, not minutes late.** It estimates the "
    "chance a trip needs attention: Low <50% · Medium 50–70% · High 70–85% "
    "· Severe ≥85%. So \"High · 73%\" means ~73% probability the trip is an "
    "actionable case — it does **not** mean 15–25 minutes late.\n\n"
    "A **negative delay = early-running**, which still affects schedule reliability "
    "(it is shown explicitly in the *Predicted timing* column rather than hidden under a "
    "\"delay\" label).\n\n"
    "The minute-based observed **Decision Rule Table** (0–5 / 5–15 / 15–25 / "
    ">25 min) is a separate scale shown on the Decision Engine page; it reuses the same "
    "Low/Medium/High/Severe words but measures observed minutes, not probability."
)


def _predicted_timing(minutes: object) -> str:
    try:
        value = float(minutes)
    except (TypeError, ValueError):
        return "Unknown"
    if value < -1:
        return "Early-running"
    if value > 1:
        return "Late-running"
    return "On-time (±1 min)"


def _risk_with_probability(risk: object, probability: object) -> str:
    risk_text = str(risk) if pd.notna(risk) else "Unknown"
    try:
        return f"{risk_text} · {round(float(probability) * 100)}%"
    except (TypeError, ValueError):
        return risk_text


def format_prediction_examples(df: pd.DataFrame) -> pd.DataFrame:
    """Display-only transform for the Route Prediction Examples table.

    Renames columns for clarity, adds an explicit early/late timing column, and
    renders the AI band with its probability (e.g. "High · 73%") so the
    probability-based AI scale is not misread as the minute-based observed scale.
    No data, thresholds, or action mappings are changed.
    """
    if df.empty:
        return df
    out = df.copy()
    if "predicted_delay" in out.columns:
        out["predicted_timing"] = out["predicted_delay"].map(_predicted_timing)
    if {"ai_delay_risk", "ai_probability"}.issubset(out.columns):
        out["ai_delay_risk"] = [
            _risk_with_probability(r, p)
            for r, p in zip(out["ai_delay_risk"], out["ai_probability"])
        ]
    out = out.drop(columns=["ai_probability"], errors="ignore")
    out = out.rename(
        columns={
            "collection_date": "Date",
            "route_id": "Route",
            "service_type": "Service type",
            "corridor_name": "Corridor",
            "observed_delay": "Observed delay (min · +late / −early)",
            "predicted_delay": "Predicted delay (min · +late / −early)",
            "predicted_timing": "Predicted timing",
            "ai_delay_risk": "AI reliability risk (prob. band)",
            "ai_recommended_action": "Recommended action",
        }
    )
    order = [
        "Date",
        "Route",
        "Service type",
        "Corridor",
        "Observed delay (min · +late / −early)",
        "Predicted delay (min · +late / −early)",
        "Predicted timing",
        "AI reliability risk (prob. band)",
        "Recommended action",
    ]
    return out[[column for column in order if column in out.columns]]
