"""Responsive layout and typography CSS for the dashboard."""


def get_layout_styles() -> str:
    """Return responsive layout CSS."""
    return """
/* ===== Layout Adjustments ===== */
@media (min-width: 1200px) {
    .block-container {
        max-width: 96vw;
        padding-top: 2.6rem;
        padding-left: 1.4rem;
        padding-right: 1.4rem;
        padding-bottom: 1.2rem;
    }

    h1 {
        font-size: 2.1rem;
        line-height: 1.15;
    }

    h2, h3 {
        font-size: 1.45rem;
        line-height: 1.2;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.75rem;
    }
}
"""
