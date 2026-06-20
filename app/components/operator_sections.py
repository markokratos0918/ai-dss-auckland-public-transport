from __future__ import annotations

from html import escape

import streamlit as st

RISK_COLORS = {
    "Low": "#2e7d32",
    "Medium": "#f9a825",
    "High": "#ef6c00",
    "Severe": "#c62828",
}


def delay_risk_card(chart, risk_percentages: dict[str, str], high_severe_pct: str) -> None:
    with st.container(border=True):
        st.subheader("AI-Predicted Delay Risk")
        chart_col, legend_col = st.columns([2, 1])
        with chart_col:
            st.altair_chart(chart, use_container_width=True)
        with legend_col:
            rows = []
            for risk in ["Low", "Medium", "High", "Severe"]:
                color = RISK_COLORS[risk]
                value = escape(risk_percentages.get(risk, "0.00%"))
                rows.append(
                    f"""
                    <div class="operator-risk-row">
                        <span class="operator-risk-dot" style="color:{color};">&bull;</span>
                        <span>
                            <div class="operator-risk-label">{escape(risk)}</div>
                            <div class="operator-risk-value">{value}</div>
                        </span>
                    </div>
                    """
                )
            st.html(
                f"""<style>
.operator-risk-legend {{
    display: grid;
    gap: 0.35rem;
    margin-top: 0.35rem;
}}
.operator-risk-row {{
    display: grid;
    grid-template-columns: 0.75rem 1fr;
    column-gap: 0.45rem;
    align-items: start;
}}
.operator-risk-dot {{
    line-height: 1;
    margin-top: 0.12rem;
}}
.operator-risk-label,
.operator-risk-value {{
    font-weight: 700;
    line-height: 1.05;
}}
.operator-risk-value {{
    margin-top: 0.1rem;
}}
.operator-risk-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-top: 0.45rem;
    padding: 0.7rem 0.9rem;
    border-radius: 0.45rem;
    background: rgba(28, 68, 103, 0.72);
}}
.operator-risk-footer-label {{
    font-weight: 700;
}}
.operator-risk-footer-value {{
    color: #ff4b4b;
    font-weight: 800;
}}
</style>
<div class="operator-risk-legend"><strong>Risk</strong>{''.join(rows)}</div>"""
            )
        st.html(
            f"""<div class="operator-risk-footer">
    <span class="operator-risk-footer-label">High + Severe Risk</span>
    <span class="operator-risk-footer-value">{escape(high_severe_pct)}</span>
</div>"""
        )


def recommended_actions_card(chart, summary: dict[str, str]) -> None:
    with st.container(border=True):
        st.subheader("AI-Based Recommended Action")
        st.altair_chart(chart, use_container_width=True)
        st.html(
            f"""<style>
.operator-action-footer {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 1.35rem;
    padding: 0.7rem 0.9rem;
    border: 1px solid rgba(93, 125, 160, 0.55);
    border-radius: 0.45rem;
    background: rgba(28, 68, 103, 0.48);
}}
.operator-action-footer-label {{
    color: #dbeafe;
    font-size: 0.82rem;
    font-weight: 800;
}}
.operator-action-footer-value {{
    color: #ffffff;
    font-weight: 800;
    margin-top: 0.2rem;
}}
.operator-action-footer-alert {{
    color: #ff4b4b;
}}
</style>
<div class="operator-action-footer">
    <div>
        <div class="operator-action-footer-label">Most Common Action</div>
        <div class="operator-action-footer-value">{escape(summary["common"])}</div>
    </div>
    <div>
        <div class="operator-action-footer-label">Severe Action Count</div>
        <div class="operator-action-footer-value operator-action-footer-alert">{escape(summary["severe"])}</div>
    </div>
</div>"""
        )


def action_summary_panel(summary: dict[str, str]) -> None:
    with st.container(border=True):
        st.subheader("AI Action Summary")
        st.metric("Most common action", summary["common"])
        st.metric("Severe action count", summary["severe"])
        st.metric("Actionable risk percentage", summary["risk_pct"])
        st.write("")
        st.write("")


def kpi_row(kpis: dict[str, str]) -> None:
    columns = st.columns(5)
    for column, (label, value) in zip(columns, kpis.items()):
        with column:
            st.metric(label, value)


def attention_panel(summary: dict[str, str]) -> None:
    with st.container(border=True):
        st.subheader("Operator Attention Summary")
        left, middle, right = st.columns([1.5, 1, 1.5])
        with left:
            st.metric("Current highest-risk route", summary["route"])
            st.caption(f"Route ID: {summary['route_id']}")
        with middle:
            st.metric("High risk count", summary["high_count"])
            st.metric("Severe risk count", summary["severe_count"])
        with right:
            st.metric("Recommended operator action", summary["action"])
            st.info("Focus operator attention on routes with sustained high average delay and high-risk action signals.")


def sumo_disclaimer() -> None:
    st.warning(
        "SUMO results represent scenario-estimated impacts and do not guarantee operational outcomes."
    )


def explainability_panel() -> None:
    with st.container(border=True):
        st.subheader("Operator Interpretation")
        st.info(
            "Top explanation features show which route, service, time, or weather patterns most influenced "
            "the AI risk signal. They do not prove direct causes of delay."
        )

