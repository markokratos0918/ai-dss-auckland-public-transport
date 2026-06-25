from __future__ import annotations

import altair as alt
import pandas as pd

from theme.colors import RISK_COLORS
from utils.formatters import format_count


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


def action_lollipop(df: pd.DataFrame, height: int = 285) -> alt.Chart:
    label_map = {
        "No operational action required": "No action required",
        "Deploy standby bus or supervisor review": "Deploy standby bus / supervisor review",
    }
    color_map = {
        "Monitor route conditions": "#26c6da",
        "No action required": "#48c774",
        "Adjust service headway": "#ff9800",
        "Deploy standby bus / supervisor review": "#ff4b4b",
    }
    chart_df = df.groupby("recommended_action", as_index=False)["records"].sum()
    chart_df = chart_df.sort_values("records", ascending=False)
    chart_df["action_label"] = chart_df["recommended_action"].replace(label_map)
    chart_df["count_label"] = chart_df["records"].apply(format_count)
    sort_order = chart_df["action_label"].tolist()
    max_records = chart_df["records"].max() if not chart_df.empty else 0
    domain_max = max_records * 1.18 if max_records else 1
    base = alt.Chart(chart_df).encode(
        y=alt.Y(
            "action_label:N",
            sort=sort_order,
            title=None,
            axis=alt.Axis(labelLimit=260),
        )
    )
    color = alt.Color(
        "action_label:N",
        scale=alt.Scale(domain=list(color_map), range=list(color_map.values())),
        legend=None,
    )
    rule = base.mark_rule(strokeWidth=3).encode(
        x=alt.X(
            "zero:Q",
            scale=alt.Scale(domain=[0, domain_max]),
            axis=alt.Axis(format="~s", tickCount=4),
            title=None,
        ),
        x2="records:Q",
        color=color,
    ).transform_calculate(zero="0")
    point = base.mark_point(
        filled=True,
        size=185,
        stroke="#f8fafc",
        strokeWidth=1,
    ).encode(
        x=alt.X(
            "records:Q",
            scale=alt.Scale(domain=[0, domain_max]),
            axis=alt.Axis(format="~s", tickCount=4),
            title=None,
        ),
        color=color,
        tooltip=["action_label:N", "records:Q"],
    )
    text = base.mark_text(align="left", dx=12, color="#ffffff", fontWeight="bold").encode(
        x=alt.X(
            "records:Q",
            scale=alt.Scale(domain=[0, domain_max]),
            axis=alt.Axis(format="~s", tickCount=4),
            title=None,
        ),
        text="count_label:N",
    )
    return (rule + point + text).properties(height=height)


def actionable_signal_dumbbell(df: pd.DataFrame) -> alt.Chart:
    chart_df = df.copy()
    chart_df["x_jitter"] = ((chart_df.groupby("Signal").cumcount() % 15) - 7) * 0.028
    chart_df["x_plot"] = chart_df["x_pos"] + chart_df["x_jitter"]
    x = alt.X(
        "x_plot:Q",
        title=None,
        scale=alt.Scale(domain=[0.65, 2.35]),
        axis=alt.Axis(values=[1, 2], labelExpr="datum.value == 1 ? 'Observed Evidence' : 'AI Predicted Risk'"),
    )
    y = alt.Y("Records:Q", axis=alt.Axis(format="~s", tickCount=3), title=None)
    trend = alt.Chart(chart_df).transform_regression("x_plot", "Records").mark_line(
        color="#f8fafc", strokeWidth=3
    ).encode(x=x, y=y)
    points = alt.Chart(chart_df).mark_point(filled=True, size=120, opacity=0.9).encode(
        x=x,
        y=y,
        shape=alt.Shape("Signal:N", scale=alt.Scale(domain=["Observed Evidence", "AI Predicted Risk"], range=["circle", "triangle-up"]), legend=None),
        color=alt.Color("Signal:N", scale=alt.Scale(domain=["Observed Evidence", "AI Predicted Risk"], range=["#1687f8", "#a855f7"]), legend=None),
        tooltip=["route_id:N", "corridor_name:N", "Signal:N", "Records:Q"],
    )
    return (points + trend).properties(height=260).configure_view(stroke=None)


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
