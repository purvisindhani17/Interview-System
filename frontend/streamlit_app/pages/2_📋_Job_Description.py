import streamlit as st

from utils import api_client
from utils.state import init_state, render_sidebar_steps
from utils.theme import badge, inject_theme, top_bar

st.set_page_config(page_title="Job Description", page_icon="📋", layout="wide")
init_state()
inject_theme()
render_sidebar_steps()

top_bar("Job Description", "Step 2 of 5")

if not st.session_state.get("resume_id"):
    st.warning("Upload your resume first.")
    st.page_link("pages/1_📄_Resume_Upload.py", label="← Back to Resume Upload", icon="📄")
    st.stop()

st.markdown(
    '<div class="hr-card"><div class="hr-card-title">Paste or upload the job description</div>'
    '<div class="hr-question-text">We\'ll extract required/preferred skills, responsibilities, '
    "and experience level.</div></div>",
    unsafe_allow_html=True,
)

tab_text, tab_file = st.tabs(["Paste text", "Upload file"])

jd_text = None
jd_file_bytes = None
jd_filename = "jd.txt"

with tab_text:
    jd_text = st.text_area("Job description text", height=220, placeholder="Paste the full job posting here...")

with tab_file:
    jd_file = st.file_uploader("Job description (PDF or .txt)", type=["pdf", "txt"])
    if jd_file is not None:
        jd_file_bytes = jd_file.getvalue()
        jd_filename = jd_file.name

if st.button("Parse job description ▶", type="primary"):
    if not jd_text and not jd_file_bytes:
        st.error("Paste some text or upload a file first.")
    else:
        with st.spinner("Parsing job description with the LLM..."):
            try:
                result = api_client.parse_job_description(
                    text=jd_text.strip() if jd_text else None,
                    file_bytes=jd_file_bytes,
                    filename=jd_filename,
                )
                st.session_state["jd_data"] = result
                st.session_state["jd_id"] = result["jd_id"]
                st.success("Job description parsed successfully.")
            except api_client.APIError as e:
                st.error(f"Failed to parse job description ({e.status_code}): {e.detail}")

if st.session_state.get("jd_data"):
    data = st.session_state["jd_data"]
    st.markdown("### Parsed job description")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Title:** {data.get('job_title') or '—'}")
        st.markdown(f"**Company:** {data.get('company') or '—'}")
        st.markdown(f"**Seniority:** {data.get('seniority_level') or '—'}")
        st.markdown("**Required skills:** " + ", ".join(data.get("required_skills", [])))
        st.markdown("**Preferred skills:** " + ", ".join(data.get("preferred_skills", [])))
        if data.get("responsibilities"):
            st.markdown("**Responsibilities**")
            for r in data["responsibilities"]:
                st.markdown(f"- {r}")

    with col2:
        years = data.get("experience_required_years")
        st.markdown(
            f'<div class="hr-score-card"><div class="hr-score-value">{years if years is not None else "—"}</div>'
            '<div class="hr-score-label">years required</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(badge(f"{len(data.get('required_skills', []))} required skills", "green"), unsafe_allow_html=True)
        st.markdown(badge(f"{len(data.get('preferred_skills', []))} preferred skills", "blue"), unsafe_allow_html=True)

    st.markdown("---")
    st.page_link("pages/3_🎯_Interview_Prep.py", label="▶ Next: Match & Interview Plan", icon="🎯")
