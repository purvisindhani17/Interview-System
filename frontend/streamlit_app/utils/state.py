"""
Central session_state initialization and the sidebar step tracker shown
on every page, so navigation state (which pipeline stage the candidate
has reached) is consistent across the whole multi-page app.
"""

import streamlit as st

from utils.theme import badge

STEPS = [
    ("resume_id", "1. Resume"),
    ("jd_id", "2. Job Description"),
    ("match_id", "3. Match & Plan"),
    ("session_id", "4. Live Interview"),
    ("report_ready", "5. Final Report"),
]


def init_state() -> None:
    defaults = {
        "backend_url": "http://127.0.0.1:8000",
        "resume_id": None,
        "resume_data": None,
        "jd_id": None,
        "jd_data": None,
        "match_id": None,
        "match_data": None,
        "plan_id": None,
        "plan_data": None,
        "session_id": None,
        "current_question": None,
        "current_turn": 1,
        "current_topic": "",
        "current_difficulty": "medium",
        "current_audio_url": None,
        "interview_complete": False,
        "answered_turns": [],
        "cv_enabled": True,
        "report_ready": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar_steps() -> None:
    st.sidebar.markdown("### Interview Pipeline")
    for key, label in STEPS:
        value = st.session_state.get(key)
        if key == "session_id" and st.session_state.get("interview_complete"):
            css_class, icon = "hr-step-done", "✅"
        elif value:
            css_class, icon = "hr-step-done", "✅"
        else:
            css_class, icon = "hr-step-pending", "○"
        st.sidebar.markdown(
            f'<div class="hr-step {css_class}">{icon}&nbsp; {label}</div>',
            unsafe_allow_html=True,
        )
    st.sidebar.markdown("---")

    with st.sidebar.expander("⚙️ Backend settings"):
        st.session_state["backend_url"] = st.text_input(
            "Backend URL", value=st.session_state["backend_url"]
        )
        st.session_state["cv_enabled"] = st.checkbox(
            "Enable webcam attention tracking", value=st.session_state["cv_enabled"]
        )

    from utils.api_client import health_check

    if health_check():
        st.sidebar.markdown(badge("● backend online", "green"), unsafe_allow_html=True)
    else:
        st.sidebar.markdown(badge("● backend unreachable", "red"), unsafe_allow_html=True)
