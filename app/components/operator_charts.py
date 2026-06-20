from __future__ import annotations

import altair as alt
import pandas as pd


RISK_COLORS = {
    "Low": "#2e7d32",
    "Medium": "#f9a825",
    "High": "#ef6c00",
    "Severe": "#c62828",
}


def risk_donut(df: pd.DataFrame, inner_radius: int = 46, outer_radius: int = 78, height: int = 215) -> alt.Chart:
    chart_df = df.copy()
    chart_df["delay_risk"] = chart_df["delay_risk"].astype(str)
    return (
        alt.Chart(chart_df)
        .mark_arc(innerRadius=inner_radius, outerRadius=outer_radius)
        .encode(
            theta=alt.Theta("records:Q"),
            color=alt.Color(
                "delay_risk:N",
                scale=alt.Scale(domain=list(RISK_COLORS), range=list(RISK_COLORS.values())),
                legend=None,
            ),
            tooltip=["delay_risk:N", "records:Q", "share_pct:Q"],
        )
        .properties(height=height)
    )


def action_bar(df: pd.DataFrame, height: int = 260, compact_axis: bool = False) -> alt.Chart:
    chart_df = df.groupby("recommended_action", as_index=False)["records"].sum()
    chart_df = chart_df.sort_values("records", ascending=False)
    max_records = chart_df["records"].max() if not chart_df.empty else 0
    domain_max = max_records * 1.12 if max_records else 1
    axis = alt.Axis(labelFlush=False)
    x_title = "Records"
    if compact_axis:
        axis = alt.Axis(labelFlush=False, tickCount=4, format="~s")
        x_title = None
    return (
        alt.Chart(chart_df)
        .mark_bar(color="#4db7e9")
        .encode(
            x=alt.X(
                "records:Q",
                title=x_title,
                scale=alt.Scale(domain=[0, domain_max]),
                axis=axis,
            ),
            y=alt.Y(
                "recommended_action:N",
                sort=chart_df["recommended_action"].tolist(),
                title=None,
                axis=alt.Axis(labelLimit=320),
            ),
            tooltip=["recommended_action:N", "records:Q"],
        )
        .properties(height=height)
    )


def shap_bar(df: pd.DataFrame) -> alt.Chart:
    chart_df = df.sort_values("importance", ascending=False)
    return (
        alt.Chart(chart_df)
        .mark_bar(color="#4db7e9")
        .encode(
            x=alt.X("importance:Q", title="Importance"),
            y=alt.Y(
                "feature:N",
                sort=alt.EncodingSortField(field="importance", order="descending"),
                title=None,
                axis=alt.Axis(labelLimit=360),
            ),
            tooltip=["feature:N", "importance:Q", "source:N"],
        )
        .properties(height=300)
    )


def sumo_delay_chart(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(color="#6a7f45")
        .encode(
            x=alt.X(
                "scenario_name:N",
                title=None,
                axis=alt.Axis(labelAngle=0, labelLimit=180),
            ),
            y=alt.Y("avg_delay_min:Q", title=None),
            tooltip=["scenario_name:N", "avg_delay_min:Q", "service_reliability:N"],
        )
        .properties(height=260)
    )
