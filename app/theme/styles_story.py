"""Decision story and route context narrative CSS."""


def get_story_styles() -> str:
    """Return decision story narrative CSS."""
    return """
/* ===== Decision Story ===== */
.decision-story-small-label {
    color: #ffffff;
    font-weight: 800;
    font-size: 0.92rem;
}
.decision-story-big-value {
    color: #ffffff;
    font-size: 1.75rem;
    line-height: 1.15;
    margin-bottom: 0.5rem;
}
.decision-story-action-value {
    color: #7dd3fc;
    font-size: 2.35rem;
    font-weight: 850;
    line-height: 1.12;
}
.decision-story-caption {
    color: rgba(255, 255, 255, 0.64);
    font-weight: 700;
    margin: 0.25rem 0 0.9rem 0;
}
.risk-route-story {
    margin-top: 1.1rem;
}
.risk-route-top {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.35rem;
    align-items: start;
    margin-bottom: 1.15rem;
}
.risk-route-id {
    color: #38bdf8;
    font-size: 1.65rem;
    font-weight: 900;
    line-height: 1.15;
    margin: 0.25rem 0 1.15rem 0;
}
.risk-route-delay {
    color: #facc15;
    font-size: 1.65rem;
    font-weight: 900;
    line-height: 1.15;
    margin-top: 0.25rem;
}
.decision-route-detail-label {
    color: rgba(255, 255, 255, 0.62);
    font-size: 0.72rem;
    font-weight: 850;
    text-transform: uppercase;
}
.decision-route-detail-value {
    color: #ffffff;
    font-size: 1.12rem;
    font-weight: 900;
    line-height: 1.25;
    margin-top: 0.22rem;
}
.decision-route-detail-service {
    color: #dbeafe;
    font-size: 0.98rem;
    font-weight: 850;
    margin-top: 0.4rem;
}
.route-action-panel {
    border: 1px solid rgba(93, 125, 160, 0.55);
    border-radius: 0.45rem;
    background: rgba(13, 38, 65, 0.62);
    padding: 1rem 1.05rem;
    margin-top: 1.2rem;
}
.route-context-strip {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.7rem;
    margin-top: 0.85rem;
}
.route-context-cell {
    border: 1px solid rgba(93, 125, 160, 0.42);
    border-radius: 0.45rem;
    background: rgba(8, 19, 32, 0.38);
    padding: 0.65rem 0.75rem;
}
.route-context-label {
    color: rgba(255, 255, 255, 0.62);
    font-size: 0.72rem;
    font-weight: 850;
    text-transform: uppercase;
}
.route-context-value {
    color: #7dd3fc;
    font-size: 1.05rem;
    font-weight: 900;
    margin-top: 0.18rem;
}
"""
