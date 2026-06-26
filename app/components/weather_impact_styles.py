from __future__ import annotations

from html import escape

import streamlit as st


WEATHER_COLORS = {
    "Normal weather": "#39D353",
    "Rain / precipitation": "#4DB7FF",
    "High wind": "#FFC857",
    "Other": "#94A3B8",
}

RAIN_COLORS = {
    "No rain": "#39D353",
    "Light rain": "#4DB7FF",
    "Moderate rain": "#FFC857",
    "Heavier rain": "#FF5B5B",
}


def inject_weather_css() -> None:
    st.markdown(
        """
        <style>
        .weather-row-spacer {
            height: 1.4rem;
            width: 100%;
            display: block;
        }

        .weather-kpi-card {
            border: 1px solid rgba(120, 150, 190, 0.28);
            border-radius: 12px;
            background: rgba(18, 34, 54, 0.86);
            padding: 0.85rem 1rem;
            min-height: 90px;
            box-sizing: border-box;
        }

        .weather-kpi-label {
            color: #c9d4e2;
            font-size: 0.76rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }

        .weather-kpi-value {
            color: #ffffff;
            font-size: 1.35rem;
            font-weight: 850;
            line-height: 1.1;
        }

        .weather-section-title {
            margin-top: 0 !important;
            margin-bottom: 0.55rem !important;
            font-size: 1.25rem;
            font-weight: 850;
            color: #ffffff;
        }

        .rain-tile {
            border: 1px solid rgba(120, 150, 190, 0.28);
            border-radius: 12px;
            background: rgba(18, 34, 54, 0.78);
            padding: 0.95rem 1rem;
            min-height: 105px;
            box-sizing: border-box;
        }

        .rain-label {
            font-size: 0.8rem;
            font-weight: 850;
            margin-bottom: 0.4rem;
        }

        .rain-pct {
            color: #ffffff;
            font-size: 1.6rem;
            font-weight: 850;
            line-height: 1.1;
        }

        .rain-records {
            color: #aebacc;
            font-size: 0.76rem;
            margin-top: 0.5rem;
        }

        .weather-profile {
            margin-top: 1rem;
            padding: 0.85rem 0.95rem;
            border-radius: 12px;
            background: rgba(18, 34, 54, 0.55);
            border: 1px solid rgba(120, 150, 190, 0.20);
        }

        .weather-profile-title {
            font-size: 0.82rem;
            font-weight: 850;
            color: #c9d4e2;
            margin-bottom: 0.45rem;
        }

        .weather-profile-bar {
            display: flex;
            height: 20px;
            border-radius: 999px;
            overflow: hidden;
            background: #1e293b;
        }

        .weather-profile-labels {
            display: flex;
            justify-content: space-between;
            gap: 0.5rem;
            margin-top: 0.55rem;
            color: #aebacc;
            font-size: 0.74rem;
            font-weight: 750;
        }

        .operator-note {
            border-left: 4px solid #4DB7FF;
            background: rgba(77, 183, 255, 0.10);
            border-radius: 10px;
            padding: 0.75rem 0.9rem;
            color: #cfeeff;
            font-size: 0.86rem;
            line-height: 1.4;
            margin-top: 1rem;
        }

        .operator-note strong {
            color: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str) -> None:
    st.markdown(
        f"<div class='weather-section-title'>{escape(title)}</div>",
        unsafe_allow_html=True,
    )
