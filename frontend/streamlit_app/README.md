# AI Interview System — Frontend (Streamlit)

A HackerRank-style test-taking interface for the AI Interview System backend:
dark assessment-platform chrome, a monospace countdown timer, question-navigator
dots, live webcam attention tracking, and auto-refreshing score panels — all
built with Streamlit but made considerably more *reactive* than a typical
Streamlit app (see "How this stays reactive" below).

## Setup

```bash
cd frontend/streamlit_app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running it

You need **both** the backend and this frontend running at the same time,
in two terminals:

**Terminal 1 — backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 — frontend:**
```bash
cd frontend/streamlit_app
streamlit run app.py
```

Streamlit will open at `http://localhost:8501`. The sidebar has a "Backend
settings" panel — the default backend URL is `http://127.0.0.1:8000`, matching
uvicorn's default. A green/red "backend online/unreachable" indicator in the
sidebar tells you immediately if the two aren't talking to each other.

> **Note on `localhost` vs `127.0.0.1`:** this app defaults to `127.0.0.1`
> deliberately. On some systems `localhost` resolves to the IPv6 loopback
> address first, which can fail to connect if the backend is only listening
> on IPv4 — using the literal IP sidesteps that entirely.

## Pipeline flow

1. **Resume Upload** — `POST /resume/upload`
2. **Job Description** — `POST /job-description/parse` (paste text or upload a file)
3. **Interview Prep** — `POST /match/compare` then `POST /interview/plan`, showing the match score and interview strategy
4. **Live Interview** — the core experience (see below)
5. **Final Report** — runs speech analysis + evaluation for every answered question, then `GET /score/session/{id}` and `GET /report/session/{id}`

State (resume_id, jd_id, match_id, plan_id, session_id, etc.) is carried
across pages via `st.session_state`, so you can move back and forth between
pages without losing progress.

## The Live Interview screen

This is the page built to feel like an online technical assessment:

- **Question panel** — current question, topic/difficulty badges, and the
  question read aloud via autoplaying TTS audio (`st.audio(..., autoplay=True)`)
- **Answer capture** — `st.audio_input`, Streamlit's native mic recorder;
  submitting sends the recording straight to `POST /interview/session/answer`
- **Webcam attention tracking** — a continuous live video feed via
  `streamlit-webrtc` (not a click-to-snapshot camera widget). A background
  frame processor samples roughly one frame every 3 seconds and POSTs it to
  `POST /cv/session/{id}/frame` on a fire-and-forget thread, so the video
  feed itself never stalls waiting on the network.
- **Question navigator** — HackerRank-style numbered dots showing answered
  (green) vs. current (highlighted) vs. upcoming questions

## How this stays reactive

Plain Streamlit reruns the *entire* script on every interaction, which tends
to feel static compared to a real web app. This UI leans on a few mechanisms
to avoid that:

- **`st.fragment(run_every=...)`** — the countdown timer (every 1s) and the
  live attention score panel (every 4s) auto-refresh *without* rerunning the
  whole page. This is the single biggest reactivity upgrade: no manual
  refresh, no full-page flicker, just the specific widget updating in place.
- **Continuous webcam via `streamlit-webrtc`** — rather than Streamlit's
  built-in `camera_input` (which requires clicking "Take Photo" every time),
  the webcam feed streams continuously and samples frames automatically in
  the background.
- **Immediate `st.rerun()` after state-changing actions** — submitting an
  answer, starting the interview, or generating a report all trigger an
  instant rerun so the UI reflects the new state right away rather than
  waiting for the next natural interaction.
- **Session-state-driven navigation** — progress carries across pages
  automatically (see the sidebar's step tracker), so nothing has to be
  re-entered when moving between pages.

## Testing notes

Every page was tested with Streamlit's own `AppTest` framework (headless
script execution with assertions on the resulting element tree) in both
empty-state and populated-state scenarios, plus the real `streamlit run`
server was smoke-tested end-to-end. Two real bugs were caught and fixed
this way before delivery:

1. The backend originally didn't return `resume_id`/`jd_id`/`match_id`/
   `plan_id` in their respective creation responses — only the parsed data.
   Fixed in the backend by adding an ID field to each response schema,
   populated by the API layer (see the main project README's Module 1-4
   sections for details).
2. `get_cv_summary()` (and every other API call) only caught HTTP error
   responses, not connection-level failures (backend unreachable, DNS
   error). A live-attention polling fragment would crash the whole page if
   the backend went down mid-interview. Fixed by routing every request
   through a common wrapper that converts `requests.RequestException` into
   the same `APIError` type used for HTTP errors, so every page's existing
   `except api_client.APIError` handling covers both cases.

`streamlit-webrtc`'s camera widget itself can't be exercised in a headless
test environment (it needs a real browser + camera permission), so that
specific piece is wrapped in a broad `try/except` that degrades to a plain
warning message if it fails to initialize — the rest of the interview
(question, answer submission, scoring) continues working regardless.
