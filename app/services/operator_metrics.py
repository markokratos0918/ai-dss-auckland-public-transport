from __future__ import annotations

import pandas as pd

from services.operator_constants import ALL_DAYS, ALL_HOURS
from services.operator_io import from_primary, short_action
from services.operator_risk import decision_summary
from services.operator_routes import top_non_special_routes


def network_kpis(
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> dict[str, str]:
    query = """
        WITH base AS (
            SELECT route_id, TRY_CAST(delay_minutes AS DOUBLE) AS delay_minutes,
                COALESCE(NULLIF(delay_risk, ''), 'Unknown') AS delay_risk
            FROM {source}
            {where}
        ),
        route_ranked AS (
            SELECT route_id, AVG(delay_minutes) AS avg_delay_minutes,
                SUM(CASE WHEN delay_risk IN ('High', 'Severe') THEN 1 ELSE 0 END) AS high_severe_cases
            FROM base
            GROUP BY route_id
            ORDER BY avg_delay_minutes DESC, high_severe_cases DESC
            LIMIT 1
        )
        SELECT COUNT(*) AS total_records, AVG(delay_minutes) AS avg_observed_delay_minutes,
            SUM(CASE WHEN delay_risk IN ('High', 'Severe') THEN 1 ELSE 0 END) AS observed_high_severe_cases,
            (SELECT route_id FROM route_ranked) AS top_observed_route
        FROM base
    """
    df = from_primary(query, service_type, include_special, analysis_day, analysis_hour)
    if df.empty:
        return {
            "Total Observations": "Unavailable",
            "Avg Predicted Delay": "Unavailable",
            "Observed High/Severe Cases": "Unavailable",
            "Top Observed Delayed Route": "Unavailable",
        }
    row = df.iloc[0]
    total = 0 if pd.isna(row.get("total_records")) else int(row.get("total_records"))
    high_severe = 0 if pd.isna(row.get("observed_high_severe_cases")) else int(row.get("observed_high_severe_cases"))
    share = high_severe / total * 100 if total else 0
    avg_delay = row.get("avg_observed_delay_minutes")
    return {
        "Total Observations": f"{total:,}",
        "Avg Predicted Delay": "Unavailable" if pd.isna(avg_delay) else f"{float(avg_delay):.2f} min",
        "Observed High/Severe Cases": f"{high_severe:,} ({share:.2f}%)",
        "Top Observed Delayed Route": str(row.get("top_observed_route") or "Unavailable"),
    }


def attention_summary(
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> dict[str, str]:
    routes = top_non_special_routes(1, service_type, include_special, analysis_day, analysis_hour)
    decisions = decision_summary(service_type, include_special, analysis_day, analysis_hour)
    ai_kpis = from_primary(
        """
        SELECT COUNT(*) AS total_records,
            SUM(COALESCE(TRY_CAST(predicted_actionable_delay_risk AS INTEGER), 0)) AS actionable_records
        FROM {source}
        {where}
        """,
        service_type,
        include_special,
        analysis_day,
        analysis_hour,
    )
    route = routes.iloc[0] if not routes.empty else pd.Series()
    high = decisions.loc[decisions["delay_risk"].astype(str) == "High", "records"].sum() if not decisions.empty else 0
    severe = decisions.loc[decisions["delay_risk"].astype(str) == "Severe", "records"].sum() if not decisions.empty else 0
    total, actionable = 0, 0
    if not ai_kpis.empty:
        row = ai_kpis.iloc[0]
        total = 0 if pd.isna(row.get("total_records")) else int(row.get("total_records"))
        actionable = 0 if pd.isna(row.get("actionable_records")) else int(row.get("actionable_records"))
    primary = "Unavailable"
    if not decisions.empty:
        primary = short_action(str(decisions.sort_values("records", ascending=False).iloc[0]["recommended_action"]))
    return {
        "route": str(route.get("route_display_name", "Unavailable")),
        "route_id": str(route.get("route_id", "Unavailable")),
        "high_count": f"{int(high):,}",
        "severe_count": f"{int(severe):,}",
        "actionable_risk": f"{actionable:,} ({(actionable / total * 100 if total else 0):.2f}%)",
        "action": primary,
        "primary_action": primary,
    }


def operator_action_summary(
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> dict[str, str]:
    decisions = decision_summary(service_type, include_special, analysis_day, analysis_hour)
    if decisions.empty:
        return {"common": "Unavailable", "severe": "0", "risk_pct": "0.0%"}
    common = decisions.sort_values("records", ascending=False).iloc[0]
    severe = decisions.loc[decisions["delay_risk"].astype(str) == "Severe", "records"].sum()
    risk = decisions[decisions["delay_risk"].astype(str).isin(["High", "Severe"])]["records"].sum()
    total = decisions["records"].sum()
    return {
        "common": short_action(str(common["recommended_action"])),
        "severe": f"{int(severe):,}",
        "risk_pct": f"{(risk / total * 100 if total else 0):.1f}%",
    }
