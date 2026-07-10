import time

import streamlit as st

from utils import api_client
from utils.state import init_state, render_sidebar_steps
from utils.theme import badge, inject_theme

st.set_page_config(page_title="Live Interview", page_icon="🎤", layout="wide")
init_state()
inject_theme()
render_sidebar_steps()

if not st.session_state.get("plan_id"):
    st.warning("Generate an interview plan first.")
    st.page_link("pages/3_🎯_Interview_Prep.py", label="← Back to Interview Prep", icon="🎯")
    st.stop()

DIFFICULTY_KIND = {"easy": "green", "medium": "amber", "hard": "red"}


# ---------- Start session ----------
if not st.session_state.get("session_id"):
    st.markdown(
        '<div class="hr-card"><div class="hr-card-title">Ready when you are</div>'
        '<div class="hr-question-text">The interview will ask you questions one at a time. '
        "Each question is read aloud; record your spoken answer and submit it to continue. "
        "If webcam tracking is enabled, your attention will be monitored throughout.</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("▶ Start Interview", type="primary"):
        with st.spinner("Starting your interview..."):
            try:
                result = api_client.start_session(st.session_state["plan_id"])
                st.session_state["session_id"] = result["session_id"]
                st.session_state["current_question"] = result["question"]
                st.session_state["current_topic"] = result["topic"]
                st.session_state["current_difficulty"] = result["difficulty"]
                st.session_state["current_audio_url"] = result.get("question_audio_url")
                st.session_state["current_turn"] = result["turn_number"]
                st.session_state["interview_start_time"] = time.time()
                st.rerun()
            except api_client.APIError as e:
                st.error(f"Could not start interview ({e.status_code}): {e.detail}")
    st.stop()


# ---------- Reactive top bar: live elapsed timer ----------
@st.fragment(run_every=1)
def render_timer():
    elapsed = int(time.time() - st.session_state.get("interview_start_time", time.time()))
    mins, secs = divmod(elapsed, 60)
    est_total = st.session_state.get("plan_data", {}).get("estimated_question_count", 10)
    answered = len(st.session_state.get("answered_turns", []))
    st.markdown(
        f"""
        <div class="hr-topbar">
            <div class="hr-topbar-left">
                <span class="hr-logo-dot"></span>
                <span class="hr-brand">Live Interview</span>
                <span class="hr-brand-sub">Question {st.session_state['current_turn']} · {answered}/{est_total} answered</span>
            </div>
            <div class="hr-timer">⏱ {mins:02d}:{secs:02d}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_timer()

main_col, side_col = st.columns([2.3, 1])

# ---------- Main panel: question + answer ----------
with main_col:
    if st.session_state.get("interview_complete"):
        st.markdown(
            '<div class="hr-card"><div class="hr-card-title">Interview complete</div>'
            '<div class="hr-question-text">Nice work — that\'s a wrap. '
            "Head to the final report for your full scored breakdown.</div></div>",
            unsafe_allow_html=True,
        )
        st.page_link("pages/5_📊_Final_Report.py", label="▶ View Final Report", icon="📊")
    else:
        topic_b = badge(st.session_state["current_topic"] or "General", "blue")
        diff_b = badge(st.session_state["current_difficulty"], DIFFICULTY_KIND.get(st.session_state["current_difficulty"], "gray"))
        st.markdown(
            f'<div class="hr-card">'
            f'<div class="hr-card-title">Question {st.session_state["current_turn"]}</div>'
            f'{topic_b}{diff_b}'
            f'<div class="hr-question-text" style="margin-top:0.75rem;">{st.session_state["current_question"]}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("current_audio_url"):
            st.audio(api_client.audio_url(st.session_state["current_audio_url"]), autoplay=True)

        st.markdown("#### Your answer")
        audio_value = st.audio_input("Record your answer, then submit below")

        submit_col, skip_col = st.columns([1, 1])
        with submit_col:
            submit_clicked = st.button("Submit Answer ▶", type="primary", disabled=audio_value is None)
        with skip_col:
            end_clicked = st.button("End Interview Early")

        if submit_clicked and audio_value is not None:
            with st.spinner("Transcribing, evaluating, and preparing the next question..."):
                try:
                    result = api_client.submit_answer(
                        st.session_state["session_id"], audio_value.getvalue(), "answer.wav"
                    )
                    st.session_state["answered_turns"].append(st.session_state["current_turn"])
                    st.session_state["last_transcript"] = result["transcript"]
                    st.session_state["last_assessment"] = result["quick_assessment"]

                    if result["is_complete"]:
                        st.session_state["interview_complete"] = True
                    else:
                        st.session_state["current_question"] = result["next_question"]
                        st.session_state["current_topic"] = result["next_topic"]
                        st.session_state["current_difficulty"] = result["next_difficulty"]
                        st.session_state["current_audio_url"] = result.get("next_question_audio_url")
                        st.session_state["current_turn"] += 1

                    st.rerun()
                except api_client.APIError as e:
                    st.error(f"Could not submit answer ({e.status_code}): {e.detail}")

        if end_clicked:
            st.session_state["interview_complete"] = True
            st.rerun()

        if st.session_state.get("last_transcript"):
            assessment = st.session_state.get("last_assessment") or {}
            kind = {"correct": "green", "partial": "amber", "incorrect": "red"}.get(
                assessment.get("correctness"), "gray"
            )
            st.markdown("##### Last answer")
            st.markdown(badge(assessment.get("correctness", "—"), kind), unsafe_allow_html=True)
            st.caption(f'"{st.session_state["last_transcript"]}"')

# ---------- Side panel: webcam + live attention ----------
with side_col:
    st.markdown('<div class="hr-card-title">📷 Attention Tracking</div>', unsafe_allow_html=True)

    if st.session_state.get("cv_enabled") and not st.session_state.get("interview_complete"):
        try:
            from streamlit_webrtc import webrtc_streamer

            from utils.webcam import AttentionTrackingProcessor

            session_id = st.session_state["session_id"]
            backend_url = st.session_state["backend_url"]

            def _make_processor():
                return AttentionTrackingProcessor(session_id, backend_url)

            st.markdown(
                '<span class="hr-pulse-dot"></span><span style="color:#8A93A6; font-size:0.8rem;">live</span>',
                unsafe_allow_html=True,
            )
            webrtc_streamer(
                key="interview-webcam",
                video_processor_factory=_make_processor,
                media_stream_constraints={"video": True, "audio": False},
            )
        except ImportError:
            st.info("Install `streamlit-webrtc` to enable webcam attention tracking.")
        except Exception:
            # Webcam/WebRTC setup is inherently environment-fragile (browser
            # camera permissions, STUN/TURN reachability, etc.). A failure
            # here should never take down the rest of the interview -- the
            # candidate can still answer questions with tracking simply off.
            st.warning("Webcam tracking couldn't start in this environment. Continuing without it.")

        @st.fragment(run_every=4)
        def render_live_attention():
            try:
                summary = api_client.get_cv_summary(st.session_state["session_id"])
            except api_client.APIError:
                summary = None
            if summary:
                st.markdown(
                    f'<div class="hr-score-card"><div class="hr-score-value">{summary["average_attention_score"]}</div>'
                    '<div class="hr-score-label">attention score</div></div>',
                    unsafe_allow_html=True,
                )
                st.caption(summary["dominant_face_orientation"])
                st.caption(f"{summary['total_frames_analyzed']} frames analyzed")
            else:
                st.caption("Waiting for the first frame...")

        render_live_attention()
    else:
        st.caption("Webcam tracking is disabled or the interview has ended.")

    st.markdown("---")
    st.markdown("**Question navigator**")
    est_total = st.session_state.get("plan_data", {}).get("estimated_question_count", 10)
    dots_html = ""
    for i in range(1, max(est_total, st.session_state["current_turn"]) + 1):
        if i in st.session_state.get("answered_turns", []):
            css = "hr-nav-dot hr-nav-dot-done"
        elif i == st.session_state["current_turn"] and not st.session_state.get("interview_complete"):
            css = "hr-nav-dot hr-nav-dot-current"
        else:
            css = "hr-nav-dot"
        dots_html += f'<span class="{css}">{i}</span>'
    st.markdown(dots_html, unsafe_allow_html=True)
