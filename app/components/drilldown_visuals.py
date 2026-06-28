from __future__ import annotations

from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from theme.colors import FEATURE_COLORS, SUMO_COLORS


def feature_group(feature: str) -> str:
    text = str(feature).lower()
    if "route" in text or "low-frequency" in text:
        return "Route"
    if "service" in text:
        return "Service"
    if "hour" in text or "weekday" in text or "day" in text:
        return "Time"
    if "direction" in text:
        return "Direction"
    if "rain" in text or "wind" in text or "weather" in text or "precip" in text:
        return "Weather"
    return "Other"


def colored_shap_bar(df: pd.DataFrame) -> alt.Chart:
    chart_df = df.sort_values("importance", ascending=False).copy()
    chart_df["group"] = chart_df["feature"].map(feature_group)
    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("importance:Q", title="Importance"),
            y=alt.Y(
                "feature:N",
                sort=alt.EncodingSortField(field="importance", order="descending"),
                title=None,
                axis=alt.Axis(labelLimit=360),
            ),
            color=alt.Color(
                "group:N",
                scale=alt.Scale(domain=list(FEATURE_COLORS), range=list(FEATURE_COLORS.values())),
                legend=alt.Legend(title="Feature type"),
            ),
            tooltip=["feature:N", "group:N", "importance:Q", "source:N"],
        )
        .properties(height=330)
    )


def shap_metric_row(features: pd.DataFrame) -> None:
    if features.empty:
        return
    top = features.iloc[0]
    groups = features["feature"].map(feature_group).nunique()
    c1, c2, c3 = st.columns(3)
    c1.metric("Top Explanation Feature", str(top["feature"]))
    c2.metric("Highest SHAP Importance", f"{float(top['importance']):.3f}")
    c3.metric("Feature Groups Shown", f"{groups}")


def sumo_colored_chart(df: pd.DataFrame) -> alt.Chart:
    chart_df = df.copy()
    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("scenario_name:N", title=None, axis=alt.Axis(labelAngle=0, labelLimit=200)),
            y=alt.Y("avg_delay_min:Q", title="Simulated avg delay (min - scenario indicator)"),
            color=alt.Color(
                "scenario_name:N",
                scale=alt.Scale(domain=list(SUMO_COLORS), range=list(SUMO_COLORS.values())),
                legend=None,
            ),
            tooltip=["scenario_name:N", "avg_delay_min:Q", "max_delay_min:Q", "congestion_index:Q", "service_reliability:N"],
        )
        .properties(height=280)
    )


def route_weather_cards(row: pd.Series) -> None:
    values = [
        ("Avg Rain", f"{float(row.get('avg_rain_pct', 0)):.1f}%"),
        ("Max Wind", f"{float(row.get('max_wind_speed', 0)):.1f} km/h"),
        ("Avg Precipitation", f"{float(row.get('avg_precipitation', 0)):.2f} mm"),
    ]
    cols = st.columns(3)
    for col, (label, value) in zip(cols, values):
        col.markdown(
            f"""
            <div class="mini-evidence-card">
                <div class="mini-evidence-label">{escape(label)}</div>
                <div class="mini-evidence-value">{escape(value)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def diverging_reliability_chart(df: pd.DataFrame, height: int = 260) -> alt.Chart:
    """Diverging bar centred on 'Near on-time': Early extends left, Late right.

    Display-only view of reliability_timing_mix (timing_band, records, share_pct).
    """
    order = ["Early-running", "Near on-time", "Late-running"]
    colors = {"Early-running": "#4db7e9", "Near on-time": "#8fa3b8", "Late-running": "#f4a259"}
    chart_df = df.copy()
    chart_df["share_pct"] = pd.to_numeric(chart_df["share_pct"], errors="coerce").fillna(0.0)

    def _extent(row: pd.Series) -> pd.Series:
        share = float(row["share_pct"])
        band = str(row["timing_band"])
        if band == "Early-running":
            return pd.Series({"start": -share, "end": 0.0})
        if band == "Late-running":
            return pd.Series({"start": 0.0, "end": share})
        return pd.Series({"start": -share / 2, "end": share / 2})

    chart_df[["start", "end"]] = chart_df.apply(_extent, axis=1)
    chart_df["mid"] = (chart_df["start"] + chart_df["end"]) / 2
    chart_df["label"] = chart_df["share_pct"].map(lambda value: f"{value:.0f}%")
    max_ext = max(chart_df["end"].max(), -chart_df["start"].min(), 1.0) * 1.15
    domain = [-max_ext, max_ext]

    base = alt.Chart(chart_df).encode(
        y=alt.Y("timing_band:N", sort=order, title=None, axis=alt.Axis(labelLimit=160)),
    )
    bars = base.mark_bar(height=26).encode(
        x=alt.X(
            "start:Q",
            title="← Early-running   ·   Late-running →",
            scale=alt.Scale(domain=domain),
            axis=alt.Axis(labelExpr="abs(datum.value) + '%'", tickCount=5),
        ),
        x2="end:Q",
        color=alt.Color(
            "timing_band:N",
            scale=alt.Scale(domain=order, range=[colors[band] for band in order]),
            legend=None,
        ),
        tooltip=["timing_band:N", "records:Q", "share_pct:Q"],
    )
    centre = (
        alt.Chart(pd.DataFrame({"x": [0]}))
        .mark_rule(color="#5d7da0", strokeDash=[3, 3])
        .encode(x="x:Q")
    )
    text = base.mark_text(color="#06121f", fontWeight="bold", fontSize=11).encode(
        x=alt.X("mid:Q", scale=alt.Scale(domain=domain)),
        text="label:N",
    )
    return (bars + centre + text).properties(height=height).configure_view(stroke=None)


def decision_rule_cards(logic: pd.DataFrame) -> None:
    if logic.empty:
        return
    cards = ['<div class="decision-rule-grid">']
    for _, row in logic.head(4).iterrows():
        risk = escape(str(row.get("delay_risk", row.get("risk", "Rule"))))
        action = escape(str(row.get("recommended_action", row.get("action", "Review"))))
        note = escape(str(row.get("operator_intervention", row.get("notes", ""))))
        cards.append(
            f'<div class="decision-rule-card"><div class="decision-rule-risk">{risk}</div>'
            f'<div class="decision-rule-action">{action}</div><div class="decision-rule-note">{note}</div></div>'
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)
