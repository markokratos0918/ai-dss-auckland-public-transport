"""Drilldown visual components (mini-evidence cards, decision rules) CSS."""


def get_drilldown_styles() -> str:
    """Return drilldown visuals CSS."""
    return """
/* ===== Drilldown Visuals ===== */
.mini-evidence-card {
    border: 1px solid rgba(93, 125, 160, 0.65);
    border-radius: 0.5rem;
    background: rgba(14, 38, 63, 0.72);
    padding: 0.85rem;
}
.mini-evidence-label {
    font-size: 0.72rem;
    color: #a7b5c7;
    text-transform: uppercase;
    font-weight: 800;
}
.mini-evidence-value {
    font-size: 1.15rem;
    color: #38bdf8;
    font-weight: 900;
    margin-top: 0.25rem;
}
.decision-rule-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.8rem;
    margin: 0.5rem 0 1rem 0;
}
.decision-rule-card {
    border: 1px solid rgba(93, 125, 160, 0.55);
    border-radius: 0.55rem;
    background: rgba(14, 38, 63, 0.72);
    padding: 1rem;
}
.decision-rule-risk {
    font-size: 0.8rem;
    text-transform: uppercase;
    color: #9ca3af;
    font-weight: 800;
}
.decision-rule-action {
    font-size: 1.2rem;
    color: #fff;
    font-weight: 800;
    margin: 0.25rem 0;
}
.decision-rule-note {
    color: #cbd5e1;
    font-size: 0.9rem;
}
"""
