from __future__ import annotations

import pandas as pd

from services.operator_constants import ALL_DAYS, ALL_HOURS, RISK_ORDER
from services.operator_io import from_primary


def decision_summary(
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> pd.DataFrame:
    query = """
        WITH grouped AS (
            SELECT
                COALESCE(NULLIF(ai_delay_risk, ''), 'Unknown') AS delay_risk,
                COALESCE(NULLIF(ai_recommended_action, ''), 'Unavailable') AS recommended_action,
                COUNT(*) AS records
            FROM {source}
            {where}
            GROUP BY ALL
        ),
        totals AS (SELECT SUM(records) AS total_records FROM grouped)
        SELECT
            delay_risk,
            recommended_action,
            records,
            ROUND(records * 100.0 / NULLIF(total_records, 0), 2) AS share_pct
        FROM grouped, totals
        ORDER BY records DESC
    """
    df = from_primary(query, service_type, include_special, analysis_day, analysis_hour)
    if not df.empty and "delay_risk" in df.columns:
        df["delay_risk"] = pd.Categorical(df["delay_risk"], RISK_ORDER, ordered=True)
        df = df.sort_values("delay_risk")
    return df


def risk_percentages(
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> dict[str, str]:
    decisions = decision_summary(service_type, include_special, analysis_day, analysis_hour)
    if decisions.empty:
        return {risk: "0.00%" for risk in RISK_ORDER}
    total = decisions["records"].sum()
    return {
        risk: f"{(decisions.loc[decisions['delay_risk'].astype(str) == risk, 'records'].sum() / total * 100 if total else 0):.2f}%"
        for risk in RISK_ORDER
    }


def high_severe_risk_percentage(
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> str:
    decisions = decision_summary(service_type, include_special, analysis_day, analysis_hour)
    if decisions.empty:
        return "0.00%"
    risk_rows = decisions[decisions["delay_risk"].astype(str).isin(["High", "Severe"])]
    return f"{risk_rows['share_pct'].sum():.2f}%"
