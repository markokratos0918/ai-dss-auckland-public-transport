from __future__ import annotations

from html import escape

import streamlit as st

_KEY = "page_summary"


def set_summary(title: str, lines: list[str]) -> None:
    """Store a per-page contextual summary for the sidebar."""
    st.session_state[_KEY] = {"title": title, "lines": [str(x) for x in lines if x]}


def render_summary() -> None:
    data = st.session_state.get(_KEY)
    if not data:
        return
    items = "".join(f"<li>{escape(line)}</li>" for line in data["lines"])
    st.markdown(
        f"""
        <style>
        .page-summary {{
            border: 1px solid rgba(93,125,160,.45);
            border-radius: .6rem;
            background: rgba(14,38,63,.55);
            padding: .7rem .8rem;
            margin-top: .6rem;
        }}
        .page-summary h4 {{
            color:#7fd1ff; font-size:.72rem; font-weight:850;
            text-transform:uppercase; letter-spacing:.03em; margin:0 0 .45rem 0;
        }}
        .page-summary ul {{ margin:0; padding-left:1rem; }}
        .page-summary li {{
            color:#cdd8e6; font-size:.78rem; margin-bottom:.32rem; line-height:1.25;
        }}
        </style>
        <div class="page-summary">
            <h4>{escape(data['title'])} — summary</h4>
            <ul>{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
