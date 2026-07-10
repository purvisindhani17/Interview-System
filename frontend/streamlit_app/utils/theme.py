"""
Custom CSS injected into every page to give the app a HackerRank-style
"online assessment" look: a dark fixed top bar with a monospace countdown
timer, green accent color and pill badges, a light content card for the
question panel, and a question-navigator dot strip. Streamlit's own theme
(.streamlit/config.toml) sets the base dark palette; this module layers
the assessment-platform-specific chrome on top via a single injected
<style> block.
"""

import streamlit as st

HACKERRANK_GREEN = "#2EC866"
HACKERRANK_GREEN_DARK = "#22A855"
DARK_BG = "#0B0F19"
DARK_PANEL = "#141A2C"
CARD_BG = "#1B2338"
BORDER = "#26304A"
TEXT_MUTED = "#8A93A6"

CSS = f"""
<style>
/* ---------- Global ---------- */
html, body, [class*="css"] {{
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header[data-testid="stHeader"] {{
    background: {DARK_BG};
    border-bottom: 1px solid {BORDER};
}}

.block-container {{
    padding-top: 1.5rem;
    max-width: 1200px;
}}

/* ---------- Top assessment bar ---------- */
.hr-topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: {DARK_PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 0.75rem 1.25rem;
    margin-bottom: 1.25rem;
}}
.hr-topbar-left {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
}}
.hr-logo-dot {{
    width: 12px; height: 12px; border-radius: 3px;
    background: {HACKERRANK_GREEN};
    display: inline-block;
    transform: rotate(45deg);
}}
.hr-brand {{
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: 0.02em;
    color: #F2F4F8;
}}
.hr-brand-sub {{
    color: {TEXT_MUTED};
    font-size: 0.8rem;
    margin-left: 0.5rem;
}}
.hr-timer {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: {HACKERRANK_GREEN};
    background: rgba(46, 200, 102, 0.08);
    border: 1px solid rgba(46, 200, 102, 0.35);
    padding: 0.25rem 0.9rem;
    border-radius: 6px;
    letter-spacing: 0.05em;
}}

/* ---------- Badges / pills ---------- */
.hr-badge {{
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-right: 0.4rem;
}}
.hr-badge-green {{ background: rgba(46, 200, 102, 0.15); color: {HACKERRANK_GREEN}; border: 1px solid rgba(46, 200, 102, 0.4); }}
.hr-badge-amber {{ background: rgba(240, 173, 78, 0.15); color: #F0AD4E; border: 1px solid rgba(240, 173, 78, 0.4); }}
.hr-badge-red {{ background: rgba(230, 90, 90, 0.15); color: #E65A5A; border: 1px solid rgba(230, 90, 90, 0.4); }}
.hr-badge-gray {{ background: rgba(138, 147, 166, 0.15); color: {TEXT_MUTED}; border: 1px solid rgba(138, 147, 166, 0.35); }}
.hr-badge-blue {{ background: rgba(88, 150, 240, 0.15); color: #5896F0; border: 1px solid rgba(88, 150, 240, 0.4); }}

/* ---------- Question / content card ---------- */
.hr-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
}}
.hr-card-title {{
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {TEXT_MUTED};
    margin-bottom: 0.6rem;
}}
.hr-question-text {{
    font-size: 1.15rem;
    line-height: 1.6;
    color: #F2F4F8;
    font-weight: 500;
}}

/* ---------- Question navigator dots ---------- */
.hr-nav-dot {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px; height: 30px;
    border-radius: 50%;
    font-size: 0.78rem;
    font-weight: 700;
    margin-right: 0.35rem;
    border: 1.5px solid {BORDER};
    color: {TEXT_MUTED};
}}
.hr-nav-dot-done {{ background: {HACKERRANK_GREEN}; border-color: {HACKERRANK_GREEN}; color: #071409; }}
.hr-nav-dot-current {{ border-color: {HACKERRANK_GREEN}; color: {HACKERRANK_GREEN}; box-shadow: 0 0 0 3px rgba(46,200,102,0.18); }}

/* ---------- Score cards ---------- */
.hr-score-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    text-align: center;
}}
.hr-score-value {{
    font-size: 1.9rem;
    font-weight: 800;
    color: {HACKERRANK_GREEN};
    font-family: "SFMono-Regular", Consolas, monospace;
}}
.hr-score-label {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: {TEXT_MUTED};
    margin-top: 0.15rem;
}}

/* ---------- Buttons ---------- */
.stButton > button {{
    border-radius: 8px;
    font-weight: 600;
    border: 1px solid {BORDER};
}}
.stButton > button[kind="primary"] {{
    background: {HACKERRANK_GREEN};
    border-color: {HACKERRANK_GREEN};
    color: #071409;
}}
.stButton > button[kind="primary"]:hover {{
    background: {HACKERRANK_GREEN_DARK};
    border-color: {HACKERRANK_GREEN_DARK};
}}

/* ---------- Sidebar step tracker ---------- */
.hr-step {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.5rem;
    border-radius: 6px;
    font-size: 0.85rem;
    margin-bottom: 0.15rem;
}}
.hr-step-active {{ background: rgba(46, 200, 102, 0.12); color: {HACKERRANK_GREEN}; font-weight: 700; }}
.hr-step-done {{ color: #E7E9EE; }}
.hr-step-pending {{ color: {TEXT_MUTED}; }}

/* ---------- Live pulse indicator (webcam / mic active) ---------- */
.hr-pulse-dot {{
    width: 9px; height: 9px;
    border-radius: 50%;
    background: #E65A5A;
    display: inline-block;
    margin-right: 0.4rem;
    animation: hr-pulse 1.4s infinite;
}}
@keyframes hr-pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(230,90,90,0.55); }}
    70% {{ box-shadow: 0 0 0 8px rgba(230,90,90,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(230,90,90,0); }}
}}

hr {{ border-color: {BORDER}; }}
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def badge(text: str, kind: str = "gray") -> str:
    return f'<span class="hr-badge hr-badge-{kind}">{text}</span>'


def top_bar(title: str, subtitle: str = "", timer_text: str | None = None) -> None:
    timer_html = f'<div class="hr-timer">{timer_text}</div>' if timer_text else ""
    st.markdown(
        f"""
        <div class="hr-topbar">
            <div class="hr-topbar-left">
                <span class="hr-logo-dot"></span>
                <span class="hr-brand">{title}</span>
                <span class="hr-brand-sub">{subtitle}</span>
            </div>
            {timer_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
