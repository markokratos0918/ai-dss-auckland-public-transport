from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from components.weather_impact_styles import RAIN_COLORS, section_title


def render_rain_tiles(severity: pd.DataFrame) -> None:
    order = ["No rain", "Light rain", "Moderate rain", "Heavier rain"]
    values = {row["rain_band"]: row for _, row in severity.iterrows()}
    cols = st.columns(4, gap="small")

    for col, label in zip(cols, order):
        row = values.get(label)
        pct = 0 if row is None else float(row["record_pct"])
        records = 0 if row is None else int(row["records"])
        color = RAIN_COLORS.get(label, "#94A3B8")

        with col:
            st.markdown(
                f"""
                <div class="rain-tile">
                    <div class="rain-label" style="color:{color};">{escape(label)}</div>
                    <div class="rain-pct">{pct:.1f}%</div>
                    <div class="rain-records">{records:,} records</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_rain_distribution_strip(severity: pd.DataFrame) -> None:
    values = {row["rain_band"]: float(row["record_pct"]) for _, row in severity.iterrows()}
    no_rain = values.get("No rain", 0)
    light = values.get("Light rain", 0)
    moderate = values.get("Moderate rain", 0)
    heavy = values.get("Heavier rain", 0)

    st.markdown(
        f"""
        <div class="weather-profile">
            <div class="weather-profile-title">Weather exposure profile</div>
            <div class="weather-profile-bar">
                <div style="width:{no_rain}%; background:#39D353;"></div>
                <div style="width:{light}%; background:#4DB7FF;"></div>
                <div style="width:{moderate}%; background:#FFC857;"></div>
                <div style="width:{heavy}%; background:#FF5B5B;"></div>
            </div>
            <div class="weather-profile-labels">
                <span>No rain {no_rain:.1f}%</span>
                <span>Light {light:.1f}%</span>
                <span>Moderate {moderate:.1f}%</span>
                <span>Heavy {heavy:.1f}%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rain_panel(severity: pd.DataFrame) -> None:
    with st.container(border=True, height=330):
        section_title("Rain Severity Mix")

        if severity.empty:
            st.warning("Rain severity is unavailable for the current filter.")
            return

        render_rain_tiles(severity)
        render_rain_distribution_strip(severity)
