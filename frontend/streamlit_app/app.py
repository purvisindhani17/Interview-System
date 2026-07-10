"""
Home page -- entry point for the Streamlit multi-page app.
Run with: streamlit run app.py
"""

import streamlit as st

from utils.state import init_state, render_sidebar_steps
from utils.theme import badge, inject_theme, top_bar

st.set_page_config(page_title="AI Interview System", page_icon="🟩", layout="wide")
init_state()
inject_theme()
render_sidebar_steps()

top_bar("AI Interview System", "Adaptive technical interview simulator")

st.markdown(
    """
    <div class="hr-card">
        <div class="hr-card-title">Welcome</div>
        <div class="hr-question-text" style="font-size:1.4rem;">
            A full, adaptive mock technical interview &mdash; resume analysis, a live
            voice conversation that adapts to your answers, real-time attention
            tracking, and a scored report at the end.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""
        <div class="hr-card" style="min-height:190px;">
            <div class="hr-card-title">Step 1&ndash;3</div>
            <b>Resume &amp; Job Match</b>
            <p style="color:#8A93A6; font-size:0.9rem;">
                Upload your resume and a job description. We compute a match score,
                strong/missing skills, and an interview strategy.
            </p>
            {badge("skill matching", "blue")}{badge("deterministic scoring", "green")}
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="hr-card" style="min-height:190px;">
            <div class="hr-card-title">Step 4</div>
            <b>Live Adaptive Interview</b>
            <p style="color:#8A93A6; font-size:0.9rem;">
                A voice-based interview that gets harder or easier based on how you
                answer, with webcam attention tracking running throughout.
            </p>
            {badge("voice AI", "blue")}{badge("real-time CV", "amber")}
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="hr-card" style="min-height:190px;">
            <div class="hr-card-title">Step 5</div>
            <b>Scored Final Report</b>
            <p style="color:#8A93A6; font-size:0.9rem;">
                Technical accuracy, communication, confidence, attention, and speech
                quality &mdash; weighted into one overall score with a full breakdown.
            </p>
            {badge("weighted scoring", "green")}{badge("LLM evaluation", "blue")}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state["resume_id"]:
    st.info("You already have progress saved in this session. Use the sidebar to continue where you left off.")

st.page_link("pages/1_📄_Resume_Upload.py", label="▶ Start with your resume", icon="📄")

st.markdown("---")
st.caption(
    "This app talks to the FastAPI backend at the URL set in the sidebar. "
    "Make sure the backend is running (`uvicorn app.main:app --reload`) before you begin."
)
