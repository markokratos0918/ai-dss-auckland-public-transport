from __future__ import annotations

import streamlit as st


CATEGORY_COLORS = {
    "Route": "#4DB7FF",
    "Service": "#A78BFA",
    "Time": "#FFC857",
    "Weather": "#39D353",
    "Direction": "#FF9F43",
    "Other": "#94A3B8",
}


def inject_shap_css() -> None:
    st.markdown(
        """
        <style>
        .driver-card {
            border: 1px solid rgba(120, 150, 190, 0.28);
            border-radius: 12px;
            background: rgba(18, 34, 54, 0.86);
            padding: 0.9rem 1rem;
            min-height: 105px;
        }
        .driver-rank {
            color: #aebacc;
            font-size: 0.78rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }
        .driver-feature {
            color: #ffffff;
            font-size: 1rem;
            font-weight: 850;
            line-height: 1.15;
            margin-bottom: 0.45rem;
        }
        .driver-meta {
            display: flex;
            justify-content: space-between;
            gap: 0.8rem;
            color: #c9d4e2;
            font-size: 0.82rem;
            font-weight: 750;
        }
        .interpretation-card {
            border: 1px solid rgba(120, 150, 190, 0.28);
            border-radius: 12px;
            background: rgba(18, 34, 54, 0.75);
            padding: 1rem;
        }
        .interpretation-card h4 {
            margin: 0 0 0.75rem 0;
            color: #ffffff;
        }
        .interpretation-row {
            display: grid;
            grid-template-columns: 1.4rem 1fr;
            gap: 0.55rem;
            margin-bottom: 0.65rem;
            color: #dbeafe;
            line-height: 1.35;
            font-weight: 650;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
