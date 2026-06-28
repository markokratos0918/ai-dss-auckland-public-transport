from __future__ import annotations

from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from components.operator_weather import display_table
from components.weather_impact_rain import render_rain_panel
from components.weather_impact_styles import (
    RAIN_COLORS,
    WEATHER_COLORS,
    inject_weather_css,
    section_title,
)


__all__ = [
    "inject_weather_css",
    "section_title",
    "render_rain_panel",
    "render_weather_kpis",
    "prepare_weather_context",
    "weather_condition_chart",
    "weather_delay_impact_chart",
    "weather_shap_chart",
    "render_route_watchlist",
    "render_operator_note",
]


def render_weather_kpis(summary: dict[str, str]) -> None:
    items = [
        ("Weather Match Rate", summary["Match Rate"]),
        ("Dataset Period", summary["Period"]),
        ("Days", summary["Days"]),
        ("Records", summary["Records"]),
    ]
    cols = st.columns(4)

    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div class="weather-kpi-card">
                    <div class="weather-kpi-label">{escape(label)}</div>
                    <div class="weather-kpi-value">{escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def prepare_weather_context(context: pd.DataFrame) -> pd.DataFrame:
    df = context.copy()
    df["context_label"] = df["weather_rule"].replace(
        {"No adverse weather flag": "Normal weather"}
    )
    df["context_label"] = df["context_label"].fillna("Other")
    return df


def weather_condition_chart(context: pd.DataFrame) -> alt.Chart:
    chart_df = prepare_weather_context(context)

    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("context_label:N", title=None, sort="-y", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("record_pct:Q", title="Share of Records (%)"),
            color=alt.Color(
                "context_label:N",
                scale=alt.Scale(
                    domain=list(WEATHER_COLORS),
                    range=list(WEATHER_COLORS.values()),
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("context_label:N", title="Weather Context"),
                alt.Tooltip("records:Q", title="Records", format=","),
                alt.Tooltip("record_pct:Q", title="Share (%)", format=".1f"),
                alt.Tooltip("avg_observed_delay:Q", title="Avg Delay", format=".2f"),
            ],
        )
        .properties(height=255)
    )


def weather_delay_impact_chart(severity: pd.DataFrame) -> alt.Chart:
    """Avg observed delay by rain band (zero-anchored) with AI risk % labels.

    This is the actual 'impact' view: it shows delay barely moves across rain
    bands, so weather is context rather than a delay driver.
    """
    order = ["No rain", "Light rain", "Moderate rain", "Heavier rain"]
    df = severity.copy()
    df["avg_observed_delay"] = pd.to_numeric(df["avg_observed_delay"], errors="coerce").fillna(0.0)
    df["avg_ai_probability_pct"] = pd.to_numeric(df.get("avg_ai_probability_pct"), errors="coerce").fillna(0.0)
    df["prob_label"] = df["avg_ai_probability_pct"].map(lambda value: f"AI {value:.0f}%")
    x = alt.X("rain_band:N", title=None, sort=order, axis=alt.Axis(labelAngle=0))
    base = alt.Chart(df)
    bars = base.mark_bar(cornerRadiusEnd=4).encode(
        x=x,
        y=alt.Y("avg_observed_delay:Q", title="Avg observed delay (min)"),
        color=alt.Color(
            "rain_band:N",
            scale=alt.Scale(domain=order, range=[RAIN_COLORS.get(band, "#94A3B8") for band in order]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("rain_band:N", title="Rain band"),
            alt.Tooltip("avg_observed_delay:Q", title="Avg delay (min)", format=".2f"),
            alt.Tooltip("avg_ai_probability_pct:Q", title="AI risk prob %", format=".1f"),
            alt.Tooltip("records:Q", title="Records", format=","),
        ],
    )
    labels = base.mark_text(dy=-6, color="#cbd5e1", fontWeight="bold").encode(
        x=x, y=alt.Y("avg_observed_delay:Q"), text="prob_label:N"
    )
    zero = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(color="#5d7da0", strokeDash=[3, 3])
        .encode(y="y:Q")
    )
    return (bars + zero + labels).properties(height=255).configure_view(stroke=None)


def weather_shap_chart(features: pd.DataFrame) -> alt.Chart:
    """Mean |SHAP| importance of weather features in the AI model."""
    df = features.copy()
    df["importance"] = pd.to_numeric(df["importance"], errors="coerce").fillna(0.0)
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, color="#4DB7FF")
        .encode(
            x=alt.X("importance:Q", title="Mean |SHAP| importance"),
            y=alt.Y("feature:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
            tooltip=[
                alt.Tooltip("feature:N", title="Feature"),
                alt.Tooltip("importance:Q", title="Importance", format=".3f"),
            ],
        )
        .properties(height=210)
    )


def render_route_watchlist(route_examples: pd.DataFrame) -> None:
    st.markdown("### Weather-Exposed Route Watchlist")
    st.caption(
        "Routes ranked by how much later (or earlier) they ran during rain / high-wind records "
        "versus their own dry-weather baseline (Weather Δ Delay). Review signals, not proof of causation."
    )

    if route_examples.empty:
        st.warning("Weather-context route examples are unavailable for the current filter.")
        return

    st.dataframe(
        display_table(
            route_examples,
            {
                "route_id": "Route ID",
                "service_type": "Service Type",
                "corridor_name": "Corridor Name",
                "weather_context_records": "Weather Context Records",
                "avg_observed_delay": "Avg Delay · Weather",
                "avg_dry_delay": "Avg Delay · Dry baseline",
                "weather_delay_delta": "Weather Δ Delay (min)",
                "avg_predicted_delay": "Avg Predicted Delay",
                "avg_ai_probability_pct": "Avg AI Risk Probability",
                "max_rain": "Max Rain",
                "max_wind_speed": "Max Wind Speed",
                "common_ai_action": "Common AI Action",
            },
        ),
        use_container_width=True,
        hide_index=True,
        height=330,
    )


def render_operator_note() -> None:
    st.markdown(
        """
        <div class="operator-note">
            <strong>Operator Note:</strong>
            Weather indicators provide operational context only. Rainfall and wind observations
            were matched with GTFS-Realtime operational records and should not be interpreted
            as direct causes of transport delay. They are supporting evidence used by the AI model
            when estimating delay risk.
        </div>
        """,
        unsafe_allow_html=True,
    )
