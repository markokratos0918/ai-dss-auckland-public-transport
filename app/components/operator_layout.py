from __future__ import annotations

import streamlit as st

from services.operator_filters import filter_controls


def page_header(key_prefix: str, sticky: bool = False) -> tuple[str, bool, str, str]:
    if not sticky:
        return _page_header_content(key_prefix)

    st.markdown(
        f"""<style>
[class*="st-key-{key_prefix}_sticky_header"] {{
    position: sticky;
    top: 2.7rem;
    z-index: 1000;
    background: #0e1117;
    border-bottom: 1px solid rgba(93, 125, 160, 0.35);
    padding: 0.35rem 0 0.75rem 0;
    margin-bottom: 0.35rem;
}}
@media (max-width: 900px) {{
    [class*="st-key-{key_prefix}_sticky_header"] {{
        position: static;
    }}
}}
</style>""",
        unsafe_allow_html=True,
    )
    with st.container(key=f"{key_prefix}_sticky_header"):
        return _page_header_content(key_prefix)


def _page_header_content(key_prefix: str) -> tuple[str, bool, str, str]:
    left, right = st.columns([1.15, 0.85])
    with left:
        st.title("AI-Driven Transport Decision Support")
        st.caption(
            "Operational decision-support dashboard using GTFS-Realtime, weather analytics, "
            "AI-predicted delay risk, and SUMO scenario evidence."
        )
    with right:
        return filter_controls(key_prefix)
