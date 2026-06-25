from html import escape

import streamlit as st

from components.operator_charts import RISK_COLORS


def _readable_corridor(value: str) -> str:
    corridor = str(value)
    return corridor.split(" - ", 1)[1] if " - " in corridor else corridor


def overview_risk_legend(values: dict[str, str]) -> None:
    rows = []
    for label in ["Low", "Medium", "High", "Severe"]:
        rows.append(
            f"""<div class="overview-risk-row">
    <span class="overview-risk-dot" style="background:{RISK_COLORS[label]}"></span>
    <span><b>{label}</b><br><b>{values.get(label, "0.00%")}</b></span>
</div>"""
        )
    st.html(f"""<div class="overview-risk-legend">{''.join(rows)}</div>""")


def overview_risk_footer(high_severe_pct: str) -> None:
    st.html(
        f"""<div class="overview-risk-footer">
    <span class="overview-risk-footer-label">High + Severe Risk</span>
    <span class="overview-risk-footer-value">{high_severe_pct}</span>
</div>"""
    )


def overview_action_footer(summary: dict[str, str]) -> None:
    st.html(
        f"""<div class="overview-action-footer">
    <div>
        <div class="overview-action-footer-label">Most Common:</div>
        <div class="overview-action-footer-value">{escape(summary["common"])}</div>
    </div>
    <div>
        <div class="overview-action-footer-label">Current Alerts:</div>
        <div class="overview-action-footer-value"><span class="overview-action-alert">{escape(summary["severe"])}</span> Severe Events</div>
    </div>
</div>"""
    )


def overview_routes_table(routes):
    if routes.empty:
        return routes
    compact = routes.copy().head(10)
    if "Route / Corridor" in compact.columns:
        compact["Corridor Name"] = compact["Route / Corridor"].map(_readable_corridor).str.slice(0, 48)
    if "Average Delay" in compact.columns:
        compact["Avg Predicted Delay"] = compact["Average Delay"].map(lambda value: f"{value:.2f} min")
    columns = ["Route ID", "Corridor Name", "Avg Predicted Delay", "Recommended Action"]
    return compact[[column for column in columns if column in compact.columns]]


def overview_routes_style(routes):
    if routes.empty or "Avg Predicted Delay" not in routes.columns:
        return routes
    return routes.style.set_properties(subset=["Avg Predicted Delay"], **{"text-align": "center"})
