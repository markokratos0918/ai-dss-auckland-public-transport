from __future__ import annotations

import pandas as pd
import streamlit as st
from urllib.error import URLError
from urllib.request import urlopen

from services.operator_constants import ALL_DAYS, ALL_HOURS
from services.operator_io import from_primary, short_action
from services.operator_risk import decision_summary
from services.operator_routes import top_non_special_routes


@st.cache_data(ttl=60)
def dashboard_status() -> str:
    try:
        urlopen("https://www.google.com/generate_204", timeout=1.5).close()
        return "Active"
    except (OSError, URLError):
        return "Offline"


def network_kpis(
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> dict[str, str]:
    status = dashboard_status()
    query = """
        WITH base AS (
            SELECT route_id, TRY_CAST(delay_minutes AS DOUBLE) AS delay_minutes,
                COALESCE(TRY_CAST(predicted_actionable_delay_risk AS INTEGER), 0) AS actionable_risk,
                COALESCE(NULLIF(ai_recommended_action, ''), 'Unavailable') AS recommended_action
            FROM {source}
            {where}
        ),
        recommendation_ranked AS (
            SELECT recommended_action, COUNT(*) AS records
            FROM base
            GROUP BY recommended_action
            ORDER BY records DESC
            LIMIT 1
        )
        SELECT COUNT(*) AS total_records, AVG(delay_minutes) AS avg_delay_minutes,
            SUM(actionable_risk) AS actionable_records,
            (SELECT recommended_action FROM recommendation_ranked) AS most_common_recommendation
        FROM base
    """
    df = from_primary(query, service_type, include_special, analysis_day, analysis_hour)
    if df.empty:
        return {
            "Total Observations": "Unavailable",
            "Average Delay": "Unavailable",
            "Actionable Risk": "Unavailable",
            "Most Common Recommendation": "Unavailable",
            "Dashboard Status": status,
        }
    row = df.iloc[0]
    total = 0 if pd.isna(row.get("total_records")) else int(row.get("total_records"))
    actionable = 0 if pd.isna(row.get("actionable_records")) else int(row.get("actionable_records"))
    share = actionable / total * 100 if total else 0
    avg_delay = row.get("avg_delay_minutes")
    return {
        "Total Observations": f"{total:,}",
        "Average Delay": "Unavailable" if pd.isna(avg_delay) else f"{float(avg_delay):.2f} min",
        "Actionable Risk": f"{actionable:,} ({share:.2f}%)",
        "Most Common Recommendation": short_action(str(row.get("most_common_recommendation") or "Unavailable")),
        "Dashboard Status": status,
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
