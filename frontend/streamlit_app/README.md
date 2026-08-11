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



## Pipeline flow

1. **Resume Upload** — `POST /resume/upload`
2. **Job Description** — `POST /job-description/parse` (paste text or upload a file)
3. **Interview Prep** — `POST /match/compare` then `POST /interview/plan`, showing the match score and interview strategy
4. **Live Interview** — the core experience (see below)
5. **Final Report** — runs speech analysis + evaluation for every answered question, then `GET /score/session/{id}` and `GET /report/session/{id}`


