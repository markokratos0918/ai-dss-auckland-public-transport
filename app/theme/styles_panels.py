"""Overview panels, risk legend, and footer component CSS."""


def get_panel_styles() -> str:
    """Return panel, legend, and footer CSS."""
    return """
/* ===== Overview Panels ===== */
.overview-risk-legend {
    display: grid;
    gap: 0.7rem;
    margin-top: 0.5rem;
}
.overview-risk-row {
    display: grid;
    grid-template-columns: 0.8rem 1fr;
    gap: 0.55rem;
    align-items: start;
}
.overview-risk-dot {
    width: 0.62rem;
    height: 0.62rem;
    border-radius: 50%;
    margin-top: 0.25rem;
}
.overview-risk-footer {
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
    padding: 1.15rem 0.9rem;
    border-radius: 0.4rem;
    background: rgba(28, 68, 103, 0.84);
}
.overview-risk-footer-label {
    color: #ffffff;
    font-weight: 800;
    padding-left: 3.7rem;
}
.overview-risk-footer-value {
    color: #ff4b4b;
    font-weight: 900;
    justify-self: start;
}
.overview-action-footer {
    margin-top: 1rem;
    padding: 0.65rem 0.9rem;
    border: 1px solid rgba(93, 125, 160, 0.55);
    border-radius: 0.4rem;
    background: rgba(13, 38, 65, 0.74);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}
.overview-action-footer-label {
    color: #dbeafe;
    font-weight: 800;
}
.overview-action-footer-value {
    color: #ffffff;
    font-weight: 800;
    margin-top: 0.2rem;
}
.overview-action-alert {
    color: #ff4b4b;
    font-weight: 900;
}
"""
