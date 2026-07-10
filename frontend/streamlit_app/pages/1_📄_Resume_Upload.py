import streamlit as st

from utils import api_client
from utils.state import init_state, render_sidebar_steps
from utils.theme import badge, inject_theme, top_bar

st.set_page_config(page_title="Resume Upload", page_icon="📄", layout="wide")
init_state()
inject_theme()
render_sidebar_steps()

top_bar("Resume Upload", "Step 1 of 5")

st.markdown(
    '<div class="hr-card"><div class="hr-card-title">Upload your resume</div>'
    '<div class="hr-question-text">We\'ll extract your skills, experience, projects, '
    "and education to personalize the interview.</div></div>",
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Resume (PDF)", type=["pdf"])

if uploaded is not None and st.button("Parse resume ▶", type="primary"):
    with st.spinner("Extracting text and parsing with the LLM..."):
        try:
            result = api_client.upload_resume(uploaded.getvalue(), uploaded.name)
            st.session_state["resume_data"] = result
            st.session_state["resume_id"] = result["resume_id"]
            st.success("Resume parsed successfully.")
        except api_client.APIError as e:
            st.error(f"Failed to parse resume ({e.status_code}): {e.detail}")

if st.session_state.get("resume_data"):
    data = st.session_state["resume_data"]
    st.markdown("### Parsed résumé")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Name:** {data.get('name') or '—'}")
        st.markdown(f"**Email:** {data.get('email') or '—'}")
        st.markdown(f"**Skills:** " + ", ".join(data.get("skills", [])))
        st.markdown(f"**Technologies:** " + ", ".join(data.get("technologies", [])))

        if data.get("experience"):
            st.markdown("**Experience**")
            for exp in data["experience"]:
                st.markdown(f"- {exp.get('role')} @ {exp.get('company')} ({exp.get('duration')})")

        if data.get("projects"):
            st.markdown("**Projects**")
            for proj in data["projects"]:
                st.markdown(f"- **{proj.get('name')}** — {proj.get('description')}")

    with col2:
        years = data.get("total_experience_years")
        st.markdown(
            f'<div class="hr-score-card"><div class="hr-score-value">{years if years is not None else "—"}</div>'
            '<div class="hr-score-label">years experience</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(badge(f"{len(data.get('skills', []))} skills extracted", "green"), unsafe_allow_html=True)
        st.markdown(badge(f"{len(data.get('certifications', []))} certifications", "blue"), unsafe_allow_html=True)

    st.markdown("---")
    st.page_link("pages/2_📋_Job_Description.py", label="▶ Next: Job Description", icon="📋")
