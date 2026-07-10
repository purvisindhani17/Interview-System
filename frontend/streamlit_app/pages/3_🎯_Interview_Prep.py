import streamlit as st

from utils import api_client
from utils.state import init_state, render_sidebar_steps
from utils.theme import badge, inject_theme, top_bar

st.set_page_config(page_title="Interview Prep", page_icon="🎯", layout="wide")
init_state()
inject_theme()
render_sidebar_steps()

top_bar("Match & Interview Plan", "Step 3 of 5")

if not st.session_state.get("resume_id") or not st.session_state.get("jd_id"):
    st.warning("Complete the resume and job description steps first.")
    st.page_link("pages/1_📄_Resume_Upload.py", label="← Back to Resume Upload", icon="📄")
    st.stop()

if not st.session_state.get("match_data"):
    if st.button("Run resume ↔ job match ▶", type="primary"):
        with st.spinner("Comparing resume against job description..."):
            try:
                match = api_client.compare_resume_and_jd(
                    st.session_state["resume_id"], st.session_state["jd_id"]
                )
                st.session_state["match_data"] = match
                st.session_state["match_id"] = match["match_id"]
                st.rerun()
            except api_client.APIError as e:
                st.error(f"Match failed ({e.status_code}): {e.detail}")

if st.session_state.get("match_data"):
    match = st.session_state["match_data"]

    st.markdown("### Resume match")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="hr-score-card"><div class="hr-score-value">{match["resume_match_percentage"]}%</div>'
            '<div class="hr-score-label">overall match</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="hr-score-card"><div class="hr-score-value">{match["skill_overlap_percentage"]}%</div>'
            '<div class="hr-score-label">skill overlap</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="hr-score-card"><div class="hr-score-value">{match["semantic_similarity_percentage"]}%</div>'
            '<div class="hr-score-label">semantic similarity</div></div>',
            unsafe_allow_html=True,
        )

    st.progress(min(match["resume_match_percentage"] / 100, 1.0))

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**💪 Strong skills**")
        for s in match.get("strong_skills", []):
            st.markdown(badge(s, "green"), unsafe_allow_html=True)
    with col_b:
        st.markdown("**⚠️ Weak skills**")
        for s in match.get("weak_skills", []) or ["None flagged"]:
            st.markdown(badge(s, "amber"), unsafe_allow_html=True)
    with col_c:
        st.markdown("**❌ Missing skills**")
        for s in match.get("missing_skills", []) or ["None"]:
            st.markdown(badge(s, "red"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="hr-card"><div class="hr-card-title">Assessment summary</div>'
        f'<div class="hr-question-text" style="font-size:1rem;">{match["summary"]}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if not st.session_state.get("plan_data"):
        if st.button("Generate interview strategy ▶", type="primary"):
            with st.spinner("Designing an interview strategy tailored to this candidate..."):
                try:
                    plan = api_client.generate_plan(
                        st.session_state["resume_id"],
                        st.session_state["jd_id"],
                        st.session_state["match_id"],
                    )
                    st.session_state["plan_data"] = plan
                    st.session_state["plan_id"] = plan["plan_id"]
                    st.rerun()
                except api_client.APIError as e:
                    st.error(f"Plan generation failed ({e.status_code}): {e.detail}")

if st.session_state.get("plan_data"):
    plan = st.session_state["plan_data"]
    question_count = plan["estimated_question_count"]
    difficulty_badge = badge("starting difficulty: " + plan["starting_difficulty"], "blue")
    count_badge = badge(f"~{question_count} questions", "gray")

    st.markdown("### Interview strategy")
    st.markdown(
        f'<div class="hr-card"><div class="hr-card-title">Approach</div>'
        f'<div class="hr-question-text" style="font-size:1rem;">{plan["interview_strategy_summary"]}</div>'
        f'<br>{difficulty_badge}{count_badge}</div>',
        unsafe_allow_html=True,
    )

    if plan.get("topic_priorities"):
        st.markdown("**Focus topics**")
        for t in plan["topic_priorities"]:
            kind = {"high": "red", "medium": "amber", "low": "gray"}.get(t["importance"], "gray")
            topic_badge = badge(t["topic"] + " · " + t["importance"], kind)
            st.markdown(
                f'{topic_badge} <span style="color:#8A93A6; font-size:0.85rem;">{t["reason"]}</span>',
                unsafe_allow_html=True,
            )

    if plan.get("sequence"):
        st.markdown("**Interview flow**")
        st.markdown(" → ".join(f"`{s}`" for s in plan["sequence"]))

    st.markdown("---")
    st.page_link("pages/4_🎤_Live_Interview.py", label="▶ Start the live interview", icon="🎤")
