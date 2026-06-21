from html import escape

import streamlit as st

from components.operator_charts import RISK_COLORS


def overview_risk_legend(values: dict[str, str]) -> None:
    rows = []
    for label in ["Low", "Medium", "High", "Severe"]:
        rows.append(
            f"""<div class="overview-risk-row">
    <span class="overview-risk-dot" style="background:{RISK_COLORS[label]}"></span>
    <span><b>{label}</b><br><b>{values.get(label, "0.00%")}</b></span>
</div>"""
        )
    st.html(
        f"""<style>
.overview-risk-legend {{ display:grid; gap:0.7rem; margin-top:0.5rem; }}
.overview-risk-row {{ display:grid; grid-template-columns:0.8rem 1fr; gap:0.55rem; align-items:start; }}
.overview-risk-dot {{ width:0.62rem; height:0.62rem; border-radius:50%; margin-top:0.25rem; }}
</style>
<div class="overview-risk-legend">{''.join(rows)}</div>"""
    )


def overview_risk_footer(high_severe_pct: str) -> None:
    st.html(
        f"""<style>
.overview-risk-footer {{
    display:grid; grid-template-columns:1.6fr 1fr; align-items:center; gap:1rem;
    margin-top:1rem; padding:1.15rem 0.9rem; border-radius:0.4rem;
    background:rgba(28, 68, 103, 0.84);
}}
.overview-risk-footer-label {{ color:#ffffff; font-weight:800; padding-left:3.7rem; }}
.overview-risk-footer-value {{ color:#ff4b4b; font-weight:900; justify-self:start; }}
</style>
<div class="overview-risk-footer">
    <span class="overview-risk-footer-label">High + Severe Risk</span>
    <span class="overview-risk-footer-value">{high_severe_pct}</span>
</div>"""
    )


def overview_action_footer(summary: dict[str, str]) -> None:
    st.html(
        f"""<style>
.overview-action-footer {{
    margin-top:1rem; padding:0.65rem 0.9rem; border:1px solid rgba(93,125,160,0.55);
    border-radius:0.4rem; background:rgba(13,38,65,0.74);
    display:grid; grid-template-columns:1fr 1fr; gap:1rem;
}}
.overview-action-footer-label {{ color:#dbeafe; font-weight:800; }}
.overview-action-footer-value {{ color:#ffffff; font-weight:800; margin-top:0.2rem; }}
.overview-action-alert {{ color:#ff4b4b; font-weight:900; }}
</style>
<div class="overview-action-footer">
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
        compact["Corridor Name"] = compact["Route / Corridor"].astype(str).str.slice(0, 48)
    if "Average Delay" in compact.columns:
        compact["Avg Predicted Delay"] = compact["Average Delay"].map(lambda value: f"{value:.2f} min")
    columns = ["Route ID", "Corridor Name", "Avg Predicted Delay", "Recommended Action"]
    return compact[[column for column in columns if column in compact.columns]]


def overview_routes_style(routes):
    if routes.empty or "Avg Predicted Delay" not in routes.columns:
        return routes
    return routes.style.set_properties(subset=["Avg Predicted Delay"], **{"text-align": "center"})
