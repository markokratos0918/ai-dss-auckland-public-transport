"""Operator card and grid component CSS."""


def get_card_styles() -> str:
    """Return card and operator grid CSS."""
    return """
/* ===== Operator Cards ===== */
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
    background: rgba(12, 16, 24, 0.36);
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
.operator-status-bad {
    color: #fb7185;
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
.operator-risk-legend {
    display: grid;
    gap: 0.35rem;
    margin-top: 0.35rem;
}
.operator-risk-row {
    display: grid;
    grid-template-columns: 0.75rem 1fr;
    column-gap: 0.45rem;
    align-items: start;
}
.operator-risk-dot {
    color: inherit;
}
.operator-risk-label {
    font-size: 0.78rem;
    font-weight: 800;
    color: #a7b5c7;
}
.operator-risk-value {
    font-size: 0.78rem;
    font-weight: 800;
    color: #ffffff;
    margin-top: 0.2rem;
}

/* ===== Light Mode Overrides ===== */
@media (prefers-color-scheme: light) {
    .operator-card, .operator-summary-strip {
        background: #ffffff;
        border-color: rgba(30, 64, 100, 0.28);
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    }
    .operator-label { color: #1e3a5f; }
    .operator-value { color: #0f172a; }
    .operator-status-good { color: #15803d; }
    .operator-status-bad { color: #dc2626; }
}
"""
