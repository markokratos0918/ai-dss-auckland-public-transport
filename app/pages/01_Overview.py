import streamlit as st
from html import escape

from components.operator_cards import network_card_row
from components.operator_charts import RISK_COLORS, action_bar, risk_donut, shap_bar, sumo_delay_chart
from components.operator_layout import page_header
from components.operator_tables import delayed_routes_table
from services.operator_data import (
    attention_summary,
    decision_summary,
    high_severe_risk_percentage,
    network_kpis,
    operator_action_summary,
    risk_percentages,
    top_non_special_routes,
)
from services.support_data import sumo_summary, top_features


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


def overview_action_footer(summary: dict[str, str]) -> None:
    st.html(
        f"""<style>
.overview-action-footer {{
    margin-top: 1rem;
    padding: 0.55rem 0.75rem;
    border: 1px solid rgba(93, 125, 160, 0.55);
    border-radius: 0.35rem;
    background: rgba(13, 38, 65, 0.74);
}}
.overview-action-row {{
    display: grid;
    grid-template-columns: 9.5rem minmax(0, 1fr);
    gap: 0.45rem;
    align-items: center;
    padding: 0.28rem 0;
    padding-left: 2rem;
}}
.overview-action-label {{ color: #dbeafe; font-weight: 800; line-height: 1; }}
.overview-action-value {{ color: #ffffff; font-weight: 800; line-height: 1; padding-left: 2.5rem; }}
.overview-action-alert {{ color: #ff4b4b; }}
</style>
<div class="overview-action-footer">
    <div class="overview-action-row">
        <span class="overview-action-label">Most Common:</span>
        <span class="overview-action-value">{summary["common"]}</span>
    </div>
    <div class="overview-action-row">
        <span class="overview-action-label">Current Alerts:</span>
        <span class="overview-action-value"><span class="overview-action-alert">{summary["severe"]}</span> Severe Events</span>
    </div>
</div>"""
    )


def overview_risk_footer(high_severe_pct: str) -> None:
    st.html(
        f"""<style>
.overview-risk-footer {{
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
    padding: 1.15rem 0.9rem;
    border-radius: 0.4rem;
    background: rgba(28, 68, 103, 0.84);
}}
.overview-risk-footer-label {{
    color: #ffffff;
    font-weight: 800;
    padding-left: 3.7rem;
}}
.overview-risk-footer-value {{
    color: #ff4b4b;
    font-weight: 900;
    justify-self: start;
}}
</style>
<div class="overview-risk-footer">
    <span class="overview-risk-footer-label">High + Severe Risk</span>
    <span class="overview-risk-footer-value">{high_severe_pct}</span>
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
    compact = compact[[column for column in columns if column in compact.columns]]
    return compact


def overview_routes_style(routes):
    if routes.empty or "Avg Predicted Delay" not in routes.columns:
        return routes
    return routes.style.set_properties(
        subset=["Avg Predicted Delay"],
        **{"text-align": "center"},
    )


def scenario_delay_value(sumo_df, scenario_name: str) -> str:
    if sumo_df.empty or "scenario_name" not in sumo_df.columns or "avg_delay_min" not in sumo_df.columns:
        return "Unavailable"
    match = sumo_df[sumo_df["scenario_name"].astype(str) == scenario_name]
    if match.empty:
        return "Unavailable"
    return f"{float(match['avg_delay_min'].iloc[0]):.2f} min"


def decision_story_strip(
    observed: dict[str, str],
    ai: dict[str, str],
    action: dict[str, str],
    sumo_df,
    sumo_details: dict[str, str],
) -> None:
    observed_route = escape(observed.get("Top Observed Delayed Route", "Unavailable"))
    ai_route = escape(ai.get("route_id", "Unavailable"))
    primary_action = escape(action.get("common", "Unavailable"))
    high_severe = escape(f"{ai.get('high_count', '0')} / {ai.get('severe_count', '0')}")
    route = escape(sumo_details.get("route_id", "Unavailable"))
    improvement = escape(sumo_details.get("improvement", "Unavailable"))
    baseline = escape(scenario_delay_value(sumo_df, "Baseline Operations"))
    disruption = escape(scenario_delay_value(sumo_df, "Disruption Scenario"))
    intervention = escape(scenario_delay_value(sumo_df, "Intervention Scenario"))
    st.html(
        f"""<style>
.decision-story-grid {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    margin: 0.35rem 0 0.85rem 0;
}}
.decision-story-card {{
    min-height: 245px;
    border: 1px solid rgba(93, 125, 160, 0.55);
    border-radius: 0.55rem;
    background: rgba(12, 16, 24, 0.35);
    padding: 1rem;
    display: flex;
    flex-direction: column;
}}
.decision-story-title {{
    color: #ffffff;
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 1rem;
}}
.decision-story-caption {{
    color: rgba(255,255,255,0.62);
    font-weight: 650;
    margin-bottom: 1rem;
}}
.decision-story-label {{
    color: #ffffff;
    font-weight: 800;
    font-size: 0.92rem;
    margin-top: 0.45rem;
}}
.decision-story-value {{
    color: #ffffff;
    font-size: 2.05rem;
    line-height: 1.2;
    margin: 0.3rem 0 0.85rem 0;
}}
.decision-story-sumo-row {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 0.6rem;
}}
.decision-story-warning {{
    margin-top: auto;
    padding: 0.85rem 1rem;
    border-radius: 0.45rem;
    background: rgba(86, 82, 18, 0.72);
    color: #fff7aa;
    font-weight: 800;
}}
@media (max-width: 900px) {{
    .decision-story-grid {{ grid-template-columns: 1fr; }}
    .decision-story-card {{ min-height: auto; }}
}}
</style>
<div class="decision-story-grid">
    <section class="decision-story-card">
        <div class="decision-story-title">Where is the risk?</div>
        <div class="decision-story-caption">Observed evidence and AI attention can point to different routes.</div>
        <div class="decision-story-label">Top Observed Delayed Route</div>
        <div class="decision-story-value">{observed_route}</div>
        <div class="decision-story-label">Top AI-Risk Route</div>
        <div class="decision-story-value">{ai_route}</div>
    </section>
    <section class="decision-story-card">
        <div class="decision-story-title">What action is recommended?</div>
        <div class="decision-story-caption">Recommendation is based on AI decision-support outputs.</div>
        <div class="decision-story-label">Primary AI Recommendation</div>
        <div class="decision-story-value">{primary_action}</div>
        <div class="decision-story-label">AI High / Severe Risk</div>
        <div class="decision-story-value">{high_severe}</div>
    </section>
    <section class="decision-story-card">
        <div class="decision-story-title">What is the expected impact?</div>
        <div class="decision-story-caption">SUMO scenario route {route} shows {improvement} lower time-loss under the tested intervention.</div>
        <div class="decision-story-sumo-row">
            <div><div class="decision-story-label">Baseline</div><div class="decision-story-value">{baseline}</div></div>
            <div><div class="decision-story-label">Disruption</div><div class="decision-story-value">{disruption}</div></div>
            <div><div class="decision-story-label">Intervention</div><div class="decision-story-value">{intervention}</div></div>
        </div>
        <div class="decision-story-warning">Scenario-estimated only; not real-world operational proof.</div>
    </section>
</div>"""
    )


def operator_judgement_footer() -> None:
    st.html(
        """<style>
.operator-judgement-footer {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 0.45rem;
    background: rgba(28, 68, 103, 0.84);
    color: #dff7ff;
    text-align: center;
    font-weight: 700;
}
</style>
<div class="operator-judgement-footer">
    This system supports operator judgement and does not automatically control transport services.
</div>"""
    )


service_type, include_special, analysis_day, analysis_hour = page_header("overview")

network = network_kpis(service_type, include_special, analysis_day, analysis_hour)
attention = attention_summary(service_type, include_special, analysis_day, analysis_hour)
network_card_row(network)
decision = decision_summary(service_type, include_special, analysis_day, analysis_hour)
summary = operator_action_summary(service_type, include_special, analysis_day, analysis_hour)
sumo, details = sumo_summary()
decision_story_strip(network, attention, summary, sumo, details)

if decision.empty:
    st.warning("AI-DSS summary is unavailable for the current filter.")
else:
    left, middle, right = st.columns([1, 1, 1])
    with left:
        with st.container(border=True, height=510):
            st.subheader("AI Delay Risk Forecast")
            chart_col, legend_col = st.columns([1.6, 1])
            with chart_col:
                st.altair_chart(risk_donut(decision, 68, 114, 305), use_container_width=True)
            with legend_col:
                overview_risk_legend(risk_percentages(service_type, include_special, analysis_day, analysis_hour))
            overview_risk_footer(
                high_severe_risk_percentage(service_type, include_special, analysis_day, analysis_hour)
            )
    with middle:
        with st.container(border=True, height=510):
            st.subheader("At-Risk Routes")
            st.caption("AI prediction route queue")
            routes = delayed_routes_table(
                top_non_special_routes(10, service_type, include_special, analysis_day, analysis_hour)
            )
            st.dataframe(
                overview_routes_style(overview_routes_table(routes)),
                use_container_width=True,
                hide_index=True,
                height=410,
            )
    with right:
        with st.container(border=True, height=510):
            st.subheader("Recommended Actions")
            st.caption("AI-based recommendation. Counts are AI decision-support records.")
            st.altair_chart(action_bar(decision, height=285, compact_axis=True), use_container_width=True)
            overview_action_footer(summary)

    lower_left, lower_right = st.columns([1, 1])
    with lower_left:
        with st.container(border=True, height=455):
            st.subheader("SUMO Scenario Snapshot")
            if sumo.empty:
                st.info("SUMO scenario outputs are unavailable.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Route", details["route_id"])
                c2.metric("Scenario Date", details["scenario_date"])
                c3.metric("Estimated Impact", details["improvement"])
                st.altair_chart(sumo_delay_chart(sumo), use_container_width=True)
                st.caption(
                    "Scenario-estimated impact only; not real-world operational proof. "
                    "SUMO is shown as one selected validation scenario, not a live recommendation for every route."
                )
    with lower_right:
        features = top_features(5)
        with st.container(border=True, height=455):
            st.subheader("Explainability Snapshot")
            if features.empty:
                st.info("SHAP feature summary is unavailable.")
            else:
                st.altair_chart(shap_bar(features), use_container_width=True)
                st.info(
                    "Top explanation features show which route, service, time, or weather patterns most "
                    "influenced the AI risk signal. They do not prove direct causes of delay."
                )

    operator_judgement_footer()
