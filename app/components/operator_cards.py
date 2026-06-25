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


def network_card_row(kpis: dict[str, str]) -> None:
    icon_by_label = {
        "Total Observations": ICONS["observations"],
        "Average Delay": ICONS["timer"],
        "Actionable Risk": ICONS["risk"],
        "Most Common Recommendation": ICONS["check"],
        "Dashboard Status": ICONS["status"],
    }
    cards = []
    for label, value in kpis.items():
        icon_data = icon_by_label.get(label, ICONS["status"])
        icon, theme = icon_data
        value_class = "operator-value"
        if label == "Dashboard Status":
            value_class += " operator-status-good" if value == "Active" else " operator-status-bad"
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
    st.html(f"<div class=\"operator-card-grid\">{''.join(cards)}</div>")


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
        f"""<div class="operator-summary-strip">
    <div class="operator-summary-grid">{''.join(cells)}</div>
</div>"""
    )

