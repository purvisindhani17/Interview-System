import streamlit as st

from utils import api_client
from utils.state import init_state, render_sidebar_steps
from utils.theme import badge, inject_theme, top_bar

st.set_page_config(page_title="Final Report", page_icon="📊", layout="wide")
init_state()
inject_theme()
render_sidebar_steps()

top_bar("Final Report", "Step 5 of 5")

if not st.session_state.get("session_id"):
    st.warning("Complete the live interview first.")
    st.page_link("pages/4_🎤_Live_Interview.py", label="← Back to Live Interview", icon="🎤")
    st.stop()

session_id = st.session_state["session_id"]
answered_turns = st.session_state.get("answered_turns", [])

if not answered_turns:
    st.warning("No answered questions found for this session yet.")
    st.stop()

if not st.session_state.get("report_ready"):
    st.markdown(
        '<div class="hr-card"><div class="hr-card-title">Almost there</div>'
        '<div class="hr-question-text">We\'ll analyze the speech quality and technical/behavioral '
        "content of each answer, then compute your weighted score and final report.</div></div>",
        unsafe_allow_html=True,
    )

    if st.button("▶ Generate Final Report", type="primary"):
        with st.status("Building your report...", expanded=True) as status:
            for turn in answered_turns:
                st.write(f"Analyzing speech for question {turn}...")
                try:
                    api_client.analyze_speech(session_id, turn)
                except api_client.APIError as e:
                    st.write(f"⚠️ Speech analysis skipped for Q{turn}: {e.detail}")

                st.write(f"Evaluating answer content for question {turn}...")
                try:
                    api_client.evaluate_answer(session_id, turn)
                except api_client.APIError as e:
                    st.write(f"⚠️ Evaluation skipped for Q{turn}: {e.detail}")

            st.write("Computing weighted overall score...")
            try:
                st.session_state["overall_score_data"] = api_client.get_overall_score(session_id)
            except api_client.APIError as e:
                st.error(f"Scoring failed: {e.detail}")
                status.update(label="Report generation failed", state="error")
                st.stop()

            st.write("Writing final report narrative...")
            try:
                st.session_state["report_data"] = api_client.get_report(session_id)
            except api_client.APIError as e:
                st.error(f"Report generation failed: {e.detail}")
                status.update(label="Report generation failed", state="error")
                st.stop()

            status.update(label="Report ready", state="complete")

        st.session_state["report_ready"] = True
        st.rerun()

if st.session_state.get("report_ready") and st.session_state.get("report_data"):
    report = st.session_state["report_data"]

    st.markdown(
        f'<div class="hr-card" style="text-align:center;">'
        f'<div class="hr-card-title">Overall Interview Score</div>'
        f'<div class="hr-score-value" style="font-size:3.2rem;">{report["overall_score"]}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### Score breakdown")
    score_fields = [
        ("Resume Match", "resume_match_score"),
        ("Technical", "technical_score"),
        ("Communication", "communication_score"),
        ("Confidence", "confidence_score"),
        ("Eye Contact", "eye_contact_score"),
        ("Attention", "attention_score"),
        ("Behavioral", "behavioral_score"),
        ("Speech Quality", "speech_quality_score"),
    ]
    cols = st.columns(4)
    for i, (label, key) in enumerate(score_fields):
        value = report.get(key)
        with cols[i % 4]:
            display = f"{value}" if value is not None else "N/A"
            st.markdown(
                f'<div class="hr-score-card"><div class="hr-score-value" style="font-size:1.4rem;">{display}</div>'
                f'<div class="hr-score-label">{label}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Weighted category breakdown")
    breakdown = report["performance_breakdown"]
    for cat_key, cat_label in [
        ("resume_match", "Resume Match (15%)"),
        ("technical_answers", "Technical Answers (35%)"),
        ("communication", "Communication (15%)"),
        ("computer_vision", "Computer Vision (15%)"),
        ("speech_analysis", "Speech Analysis (10%)"),
        ("behavioral_performance", "Behavioral Performance (10%)"),
    ]:
        cat = breakdown[cat_key]
        if cat["available"]:
            st.markdown(f"**{cat_label}** — {cat['score']}")
            st.progress(min(cat["score"] / 100, 1.0))
        else:
            st.markdown(f"**{cat_label}** — {badge('not available', 'gray')}", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Interview summary")
    st.markdown(
        f'<div class="hr-card"><div class="hr-question-text" style="font-size:1rem;">{report["interview_summary"]}</div></div>',
        unsafe_allow_html=True,
    )

    col_s, col_w = st.columns(2)
    with col_s:
        st.markdown("#### 💪 Strengths")
        for s in report.get("strengths", []):
            st.markdown(f"- {s}")
    with col_w:
        st.markdown("#### 🔧 Weaknesses")
        for w in report.get("weaknesses", []):
            st.markdown(f"- {w}")

    st.markdown("#### 📚 Recommended learning path")
    for step in report.get("recommended_learning_path", []):
        st.markdown(f"- {step}")

    st.markdown("#### 🎯 Topics to practice")
    for t in report.get("topics_to_practice", []):
        st.markdown(badge(t, "blue"), unsafe_allow_html=True)

    if report.get("missing_skills"):
        st.markdown("#### ❌ Missing skills vs. job description")
        for s in report["missing_skills"]:
            st.markdown(badge(s, "red"), unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Start a new interview"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")
