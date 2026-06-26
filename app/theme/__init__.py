"""Theme package: aggregates all CSS modules and provides dashboard styling."""

import streamlit as st

from theme.styles_layout import get_layout_styles
from theme.styles_cards import get_card_styles
from theme.styles_panels import get_panel_styles
from theme.styles_story import get_story_styles
from theme.styles_drilldown import get_drilldown_styles


def get_all_styles() -> str:
    """Aggregate all CSS modules into a single style block."""
    return f"""
<style>
{get_layout_styles()}
{get_card_styles()}
{get_panel_styles()}
{get_story_styles()}
{get_drilldown_styles()}
</style>
"""


def load_dashboard_styles() -> None:
    """Load all dashboard styles into the Streamlit app."""
    st.html(get_all_styles())


__all__ = ["get_all_styles", "load_dashboard_styles"]
