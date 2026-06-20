from __future__ import annotations

from html import escape

import streamlit as st


ICONS = {
    "observations": ("▦", "theme-data"),
    "timer": ("◷", "theme-time"),
    "risk": ("⚠", "theme-risk"),
    "check": ("🛡", "theme-action"),
    "status": ("▣", "theme-status"),
    "high": ("↗", "theme-high"),
    "severe": ("!", "theme-severe"),
    "bus": ("🚌", "theme-bus"),
}

def _summary_card_css() -> str:
    return """<style>
.operator-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin: 0.75rem 0 0.35rem 0;
}
.operator-card,
.operator-summary-strip {
    border: 1px solid rgba(93, 125, 160, 0.55);
    border-radius: 0.55rem;
    background: rgba(13, 38, 65, 0.72);
}
.operator-card {
    display: flex;
    align-items: center;
    gap: 1.3rem;
    padding: 1.45rem 1.35rem;
    min-height: 6.25rem;
}
.operator-icon {
    position: relative;
    border-radius: 10px;
    background: rgba(33, 94, 156, 0.72);
    color: #ffffff;
    letter-spacing: 0;
    width: 60px;
    height: 60px;
    min-width: 60px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12), 0 0 18px rgba(41, 142, 218, 0.2);
}
.theme-data {
    background: linear-gradient(135deg, #2276d2, #20b8d8);
}
.theme-time {
    background: linear-gradient(135deg, #2468d8, #6f5df4);
}
.theme-risk,
.theme-high {
    background: linear-gradient(135deg, #f59e0b, #ef4444);
}
.theme-action,
.theme-status {
    background: linear-gradient(135deg, #139c63, #2dd4bf);
}
.theme-severe {
    background: linear-gradient(135deg, #dc2626, #fb7185);
}
.theme-bus {
    background: linear-gradient(135deg, #0284c7, #38bdf8);
}
.operator-glyph {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-size: 1.7rem;
    font-weight: 900;
    line-height: 1;
}
.theme-bus .operator-glyph {
    font-size: 1.5rem;
}
.theme-severe .operator-glyph {
    font-size: 1.95rem;
}
.operator-label {
    color: #dbeafe;
    font-size: 1.16rem;
    font-weight: 700;
    line-height: 1.1;
}
.operator-value {
    color: #ffffff;
    font-size: 1.62rem;
    font-weight: 800;
    line-height: 1.2;
    margin-top: 0.2rem;
}
.operator-status-good {
    color: #48f268;
}
.operator-summary-strip {
    padding: 1rem;
    margin-bottom: 1rem;
}
.operator-summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 1.15rem;
}
.operator-summary-item {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    border-right: 1px solid rgba(93, 125, 160, 0.32);
}
</style>"""


def network_card_row(kpis: dict[str, str]) -> None:
    icons = [ICONS["observations"], ICONS["timer"], ICONS["severe"], ICONS["bus"]]
    cards = []
    for icon_data, (label, value) in zip(icons, kpis.items()):
        icon, theme = icon_data
        value_class = "operator-value"
        if label == "Dashboard Status":
            value_class += " operator-status-good"
        cards.append(
            f"""<div class="operator-card">
    <div class="operator-icon {escape(theme)}">
        <span class="operator-glyph">{icon}</span>
    </div>
    <div>
        <div class="operator-label">{escape(label)}</div>
        <div class="{value_class}">{escape(value)}</div>
    </div>
</div>"""
        )
    st.html(f"{_summary_card_css()}<div class=\"operator-card-grid\">{''.join(cards)}</div>")


def operator_summary_strip(summary: dict[str, str], route_label: str = "Top AI-Risk Route") -> None:
    items = [
        (ICONS["check"], "Primary AI Action", summary["primary_action"]),
        (ICONS["risk"], "AI Actionable Risk", summary.get("actionable_risk", summary["high_count"])),
        (ICONS["severe"], "AI Severe Risk Count", summary["severe_count"]),
        (ICONS["bus"], route_label, summary["route_id"]),
    ]
    cells = []
    for icon_data, label, value in items:
        icon, theme = icon_data
        cells.append(
            f"""<div class="operator-summary-item">
    <div class="operator-icon {escape(theme)}">
        <span class="operator-glyph">{icon}</span>
    </div>
    <div>
        <div class="operator-label">{escape(label)}</div>
        <div class="operator-value">{escape(value)}</div>
    </div>
</div>"""
        )
    st.html(
        f"""{_summary_card_css()}
<div class="operator-summary-strip">
    <div class="operator-summary-grid">{''.join(cells)}</div>
</div>"""
    )

