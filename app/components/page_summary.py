from __future__ import annotations

from html import escape

import streamlit as st

_KEY = "page_summary"


def set_summary(title: str, body) -> None:
    """Store a per-page paragraph summary for the sidebar.

    `body` may be a paragraph string or a list of phrases (joined into prose
    for pages not yet migrated to hand-written paragraphs).
    """
    if isinstance(body, (list, tuple)):
        parts = [str(x).strip().rstrip(".") for x in body if x]
        body = (". ".join(parts) + ".") if parts else ""
    st.session_state[_KEY] = {"title": title, "body": str(body)}


def render_summary() -> None:
    data = st.session_state.get(_KEY)
    if not data or not data.get("body"):
        return
    st.markdown(
        f"""
        <style>
        .page-summary {{
            border: 1px solid rgba(93,125,160,.40);
            border-radius: .6rem;
            background: rgba(14,38,63,.55);
            padding: .75rem .85rem;
            margin-top: .6rem;
        }}
        .summary-title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: .08em;
            font-weight: 700;
            color: #79C6FF;
            margin-bottom: .55rem;
        }}
        .summary-body {{
            font-size: 12px;
            line-height: 1.55;
            color: #D7E3F2;
        }}
        </style>
        <div class="page-summary">
            <div class="summary-title">{escape(data['title'])}</div>
            <div class="summary-body">{escape(data['body'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
