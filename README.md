# AI Interview System

A solo portfolio project demonstrating LLM integration, Voice AI, Computer Vision, and ML-based scoring by simulating a real, adaptive technical interview.

This is **not** a production SaaS app — no auth, no multi-user support, no Docker. Just a clean, modular demonstration of the full pipeline.

---

## Module Checklist (10 backend modules + frontend integration)

1. ✅ Resume Parser
2. ✅ Job Description Parser
3. ✅ Match / Comparison Engine
4. ✅ Interview Plan Generator
5. ✅ Live Adaptive Voice Interview Engine
6. ✅ Computer Vision Analysis (OpenCV + MediaPipe)
7. ✅ Speech Analysis
8. ✅ LLM Answer Evaluation
9. ✅ Scoring Engine
10. ✅ Report Generator

**All 10 backend modules are complete.** Frontend (Next.js) integration is the remaining phase — see "What's Next" at the bottom of this document.

> **Post-completion fix:** building the frontend surfaced a real gap —
> `/resume/upload`, `/job-description/parse`, `/match/compare`, and
> `/interview/plan` returned their parsed data but never included the
> generated `resume_id`/`jd_id`/`match_id`/`plan_id` needed for every
> downstream call. Fixed by adding an optional ID field to each response
> schema (`ParsedResume.resume_id`, `ParsedJobDescription.jd_id`,
> `MatchResult.match_id`, `InterviewPlan.plan_id`), populated by the API
> layer right before each response is returned. Verified with a full
> Module 1→4 regression confirming all four IDs now come through correctly.

---

## Full Planned Architecture

```
ai-interview-system/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, registers all module routers
│   │   ├── config.py                # Central settings (LLM provider, paths, limits)
│   │   ├── modules/
│   │   │   ├── resume_parser/       # ✅ MODULE 1 (done)
│   │   │   │   ├── pdf_extractor.py #   PDF -> raw text
│   │   │   │   ├── parser.py        #   raw text -> structured JSON via LLM
│   │   │   │   └── schema.py        #   Pydantic contract: ParsedResume
│   │   │   ├── job_parser/          # ✅ MODULE 2 (done)
│   │   │   │   ├── text_extractor.py #  PDF/.txt upload -> raw text
│   │   │   │   ├── parser.py        #   raw text -> structured JSON via LLM
│   │   │   │   └── schema.py        #   Pydantic contract: ParsedJobDescription
│   │   │   ├── evaluation_engine/   # ✅ MODULE 8 (done)
│   │   │   │   ├── schema.py        #   AnswerEvaluation, DimensionScore, EvaluationSessionSummary
│   │   │   │   ├── evaluator.py     #   LLM per-dimension scoring + reasoning
│   │   │   │   └── aggregator.py    #   deterministic weighted overall_score + session summary
│   │   │   ├── interview_engine/    # ✅ MODULE 4 (plan) + ✅ MODULE 5 (live voice loop)
│   │   │   │   ├── schema.py        #   InterviewPlan, InterviewSession, ConversationTurn, QuickAssessment
│   │   │   │   ├── plan_generator.py #  resume+JD+match -> LLM -> interview strategy
│   │   │   │   ├── conversation_engine.py # quick answer eval + adaptive next-question generation
│   │   │   │   └── difficulty_engine.py   # deterministic easy/medium/hard state machine
│   │   │   ├── match_engine/        # ✅ MODULE 3 (done)
│   │   │   │   ├── skill_matcher.py #   deterministic skill overlap (fuzzy matching)
│   │   │   │   ├── semantic_similarity.py # scikit-learn TF-IDF cosine similarity
│   │   │   │   ├── matcher.py       #   orchestration: scores + LLM qualitative judgment
│   │   │   │   └── schema.py        #   Pydantic contract: MatchResult
│   │   │   ├── cv_analysis/         # ⏳ MODULE 6 — OpenCV + MediaPipe eye contact,
│   │   │   │                        #     head pose, attention metrics
│   │   │   ├── cv_analysis/         # ✅ MODULE 6 (done)
│   │   │   │   ├── schema.py        #   FrameMetrics, CVSessionSummary
│   │   │   │   ├── geometry.py      #   pure math: head pose (solvePnP), gaze, smile, attention
│   │   │   │   ├── model_setup.py   #   downloads/caches the FaceLandmarker model bundle
│   │   │   │   ├── face_analyzer.py #   MediaPipe FaceLandmarker (Tasks API) I/O wrapper
│   │   │   │   └── aggregator.py    #   per-frame metrics -> session summary
│   │   │   ├── report_generator/    # ✅ MODULE 10 (done)
│   │   │   │   ├── schema.py        #   InterviewReport
│   │   │   │   └── generator.py     #   deterministic scores + LLM-synthesized narrative
│   │   │   ├── scoring_engine/      # ✅ MODULE 9 (done)
│   │   │   │   ├── schema.py        #   CategoryScore, OverallScoreResult
│   │   │   │   └── scorer.py        #   deterministic weighted combination of Modules 3/6/7/8
│   │   │   ├── speech_analysis/     # ✅ MODULE 7 (done)
│   │   │   │   ├── schema.py        #   SpeechAnalysisResult, SpeechSessionSummary
│   │   │   │   ├── filler_words.py  #   regex-based filler/hedge word counting
│   │   │   │   ├── pace_analyzer.py #   WPM + long-pause detection from word timestamps
│   │   │   │   ├── clarity_analyzer.py #  sentence-length heuristics
│   │   │   │   ├── confidence_analyzer.py # hedging-language detection
│   │   │   │   ├── analyzer.py      #   orchestration: Whisper timestamps + all sub-analyzers
│   │   │   │   └── aggregator.py    #   per-turn metrics -> session summary
│   │   │   ├── scoring_engine/      # ⏳ MODULE 9 — weighted scoring across all signals
│   │   │   └── report_generator/    # ⏳ MODULE 10 — final report assembly
│   │   └── utils/
│   │       ├── llm_client.py        # ✅ Swappable LLM call (OpenAI now, others later)
│   │       ├── voice_client.py      # ✅ Swappable TTS/STT (OpenAI now, ElevenLabs/local later)
│   │       └── storage.py           # ✅ Shared JSON read/write helper
│   ├── data/
│   │   ├── resumes/                 # Uploaded resume PDFs (by generated UUID)
│   │   └── storage/                 # Structured JSON output, organized by module
│   ├── requirements.txt
│   └── .env.example
└── frontend/                        # ⏳ Next.js + TypeScript + Tailwind (later module)
    ├── pages/ (Home, Resume Upload, JD Upload, Prep, Live Interview, Report)
    └── components/
```

**Design principle carried through every module:** the LLM call is always
isolated behind `app/utils/llm_client.py`. No module talks to the OpenAI SDK
directly — this is what makes "swap the LLM provider later" a one-file change
instead of a rewrite.

---

## Module 1: Resume Upload & Parsing — ✅ Implemented

### What it does
1. Accepts a resume PDF via `POST /resume/upload`.
2. Extracts raw text with `pdfplumber` (`pdf_extractor.py`).
3. Sends the text to an LLM with a strict JSON-only system prompt (`parser.py`),
   which extracts: name, email, phone, skills, experience, projects, education,
   technologies, certifications, and an estimated total years of experience.
4. Validates the LLM's output against a Pydantic schema (`schema.py`) — if the
   LLM omits a field or returns the wrong type, this fails loudly rather than
   silently passing bad data downstream.
5. Saves the original PDF to `data/resumes/<uuid>.pdf` and the structured
   result to `data/storage/resumes/<uuid>.json`.
6. Returns the structured `ParsedResume` JSON to the caller.

### Why these choices
- **pdfplumber over PyPDF2**: more reliable text extraction on real-world
  resume layouts (columns, tables, bullet indentation).
- **JSON-only LLM output + Pydantic validation**: resumes are unpredictable in
  format; free-text LLM output would be fragile to parse. Forcing structured
  JSON and validating it is the difference between a demo and something you'd
  trust in a pipeline.
- **UUID-based storage, no DB**: this project has one user and a handful of
  interviews — JSON files are simpler to read/debug than standing up SQLite
  for Module 1, and every later module reuses the same `storage.py` helper.

### How to run it

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...

uvicorn app.main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`. Interactive docs (Swagger UI)
are auto-generated at `http://localhost:8000/docs`.

### How to test it

**Option A — Swagger UI**
Go to `http://localhost:8000/docs`, open `POST /resume/upload`, click
"Try it out", upload any resume PDF, and execute.

**Option B — curl**
```bash
curl -X POST "http://localhost:8000/resume/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/resume.pdf"
```

**Option C — health check only (no LLM key needed)**
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

**What a successful response looks like:**
```json
{
  "name": "John Smith",
  "email": "john.smith@example.com",
  "phone": "+1-555-987-6543",
  "skills": ["Python", "FastAPI", "React"],
  "experience": [
    {"company": "Acme Corp", "role": "Backend Engineer", "duration": "2022 - Present", "description": "..."}
  ],
  "projects": [
    {"name": "AI Interview System", "description": "...", "technologies": ["FastAPI", "OpenCV"]}
  ],
  "education": [{"institution": "State University", "degree": "B.Tech CSE", "year": "2022"}],
  "technologies": ["PostgreSQL", "AWS"],
  "certifications": ["AWS Certified Developer Associate"],
  "total_experience_years": 3.5
}
```

This was verified end-to-end in a sandboxed test (PDF extraction → mocked LLM
structuring → schema validation → FastAPI `TestClient` round trip → files
persisted correctly to `data/resumes/` and `data/storage/resumes/`) before
delivery.

### Error handling already in place
- Non-PDF upload → `400 Only PDF files are supported.`
- File over `MAX_RESUME_SIZE_MB` (default 10MB) → `400`
- Scanned/image-only PDF with no text layer → `422` with a clear message
  (OCR is intentionally out of scope for this project)
- LLM/parsing failure → `500` with the underlying error message

---

## Module 2: Job Description Parser — ✅ Implemented

### What it does
1. Accepts a job description via `POST /job-description/parse` — either as
   **pasted text** (`text` form field) or an **uploaded file** (`file`, PDF or
   `.txt`). If both are given, pasted text takes priority.
2. If a file was uploaded, `text_extractor.py` normalizes it to plain text
   (reusing the resume module's PDF extractor for the PDF case, plain read
   for `.txt`).
3. Sends the raw text to an LLM with a strict JSON-only system prompt
   (`parser.py`) that extracts: job title, company, required skills,
   preferred skills, responsibilities, technologies, estimated required
   years of experience, and an inferred seniority level.
4. Validates the result against `ParsedJobDescription` (`schema.py`).
5. Saves the structured result to `data/storage/job_descriptions/<uuid>.json`.
6. Returns the structured JSON to the caller.

### Why these choices
- **Text-or-file, not file-only**: real JDs are usually copy-pasted from a
  job board, not downloaded as a PDF. Supporting both means the frontend's
  "paste or upload" step (per the Step 2 spec) maps directly onto one endpoint.
- **Required vs. preferred skills kept separate**: this distinction is what
  Module 3 (resume-vs-JD matching) needs to compute "missing skills" vs.
  "nice to have but not disqualifying" — merging them now would lose
  information the scoring engine needs later.
- **Reused `resume_parser`'s PDF extractor** rather than duplicating PDF
  logic — one implementation of "get text out of a PDF," shared across
  modules that both happen to accept PDF input.

### How to test it

**Pasted text (curl):**
```bash
curl -X POST "http://localhost:8000/job-description/parse" \
  -F "text=We are hiring a Backend Engineer. 3+ years Python and FastAPI required. Docker and Redis are a plus. You'll design internal APIs and work with frontend engineers."
```

**File upload (curl):**
```bash
curl -X POST "http://localhost:8000/job-description/parse" \
  -F "file=@/path/to/job_description.pdf"
```

**Swagger UI:** same as Module 1 — `http://localhost:8000/docs`, expand
`POST /job-description/parse`, "Try it out", fill in either the `text` field
or `file` field (leave the other blank), execute.

**What a successful response looks like:**
```json
{
  "job_title": "Backend Engineer",
  "company": "Acme Corp",
  "required_skills": ["Python", "FastAPI", "REST APIs"],
  "preferred_skills": ["Docker", "Redis"],
  "responsibilities": ["Design and maintain internal APIs", "Collaborate with frontend engineers"],
  "technologies": ["PostgreSQL", "AWS"],
  "experience_required_years": 3.0,
  "seniority_level": "Mid"
}
```

This was verified end-to-end in a sandboxed test: pasted-text path, file-upload
(.txt) path, and the "no input provided" 400 error path were all exercised
against the real FastAPI app with a mocked LLM response, and the resulting
JSON was confirmed to persist correctly to `data/storage/job_descriptions/`.

### Error handling already in place
- Neither `text` nor `file` provided → `400`
- Pasted text is empty/whitespace-only → `400`
- Unsupported file type (not PDF/.txt) → `422` via `JobDescriptionExtractionError`
- Scanned/image-only PDF with no text layer → `422` (same message as Module 1)
- File over `MAX_RESUME_SIZE_MB` → `400`
- LLM/parsing failure → `500`

---

## Module 3: Resume vs. Job Description Comparison — ✅ Implemented

### What it does
1. Accepts `POST /match/compare` with `{"resume_id": ..., "jd_id": ...}`,
   loading both previously-parsed records from storage (Modules 1 & 2).
2. **Deterministic scoring** (no LLM, fully reproducible):
   - `skill_matcher.py` computes required/preferred skill overlap using
     normalization + fuzzy matching (`difflib`), so "Node.js" matches
     "NodeJS" and "Postgres" matches "PostgreSQL" without a hand-written
     synonym list. Required skills are weighted 2x preferred skills.
   - `semantic_similarity.py` uses **scikit-learn's TF-IDF + cosine
     similarity** over the full resume text (skills, technologies, project
     and experience descriptions) vs. the JD text. This catches signal
     that literal skill-matching misses — e.g. a project description
     saying "built a caching layer" partially supporting a "Redis"
     requirement, even if the word "Redis" never appears in the resume.
   - The two scores are blended (65% skill overlap / 35% semantic
     similarity) into the headline `resume_match_percentage`.
3. **LLM qualitative judgment** (`matcher.py`): given the resume, the JD,
   and the precomputed overlap as context, the LLM refines the final
   `strong_skills` / `missing_skills` lists (it can promote a skill out of
   "missing" if project descriptions clearly demonstrate it), identifies
   `weak_skills` (skills listed but with no supporting evidence in
   experience/projects), picks `interview_focus_topics`, and writes a
   short hiring-manager-style `summary`.
4. Persists the full result to `data/storage/matches/<uuid>.json` (including
   the source `resume_id`/`jd_id` for traceability) and returns it.

### Why the score is deterministic, not LLM-generated
An LLM asked to output a raw percentage will produce a plausible-looking
but non-reproducible number — ask twice, get two different scores. Keeping
the number in code (skill overlap + TF-IDF) means the same resume/JD pair
always produces the same percentage, while the LLM is used for what it's
actually good at: judging *nuance* (does this project really demonstrate
that skill?) rather than arithmetic.

### How to test it

This endpoint depends on Modules 1 and 2 already having run (it loads
by ID, it doesn't re-parse raw input):

```bash
# 1. Upload a resume (Module 1) -> note the resume appears in
#    backend/data/storage/resumes/<resume_id>.json
curl -X POST "http://localhost:8000/resume/upload" -F "file=@/path/to/resume.pdf"

# 2. Parse a job description (Module 2) -> note the jd appears in
#    backend/data/storage/job_descriptions/<jd_id>.json
curl -X POST "http://localhost:8000/job-description/parse" -F "text=Backend Engineer role requiring Python, FastAPI, Docker..."

# 3. Compare them using the IDs (the filenames, minus .json) from steps 1-2
curl -X POST "http://localhost:8000/match/compare" \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "<resume_id_from_step_1>", "jd_id": "<jd_id_from_step_2>"}'
```

Swagger UI (`http://localhost:8000/docs`) works the same way — run the
resume and JD endpoints first, copy the IDs out of `data/storage/`, then
call `/match/compare` with them.

**What a successful response looks like:**
```json
{
  "resume_match_percentage": 45.9,
  "skill_overlap_percentage": 50.0,
  "semantic_similarity_percentage": 38.2,
  "strong_skills": ["Python", "FastAPI", "Redis"],
  "missing_skills": ["Docker"],
  "weak_skills": [],
  "interview_focus_topics": ["Docker/Containerization", "System Design"],
  "summary": "Strong overall fit with one clear gap in containerization tooling."
}
```

This was verified end-to-end in a sandboxed test: `skill_matcher.py`'s fuzzy
matching was checked against naming variations (Node.js/NodeJS,
Postgres/PostgreSQL), `semantic_similarity.py` was checked to score a
closely-related JD meaningfully higher than an unrelated one, and the full
chain — real resume upload → real JD parse → real `/match/compare` call
using the actual persisted IDs — was run through FastAPI's `TestClient`
with the LLM call mocked, confirming the blended percentage arithmetic and
disk persistence both work correctly.

### Error handling already in place
- `resume_id` not found in storage → `404`
- `jd_id` not found in storage → `404`
- Empty resume or JD text (nothing to compare) → semantic similarity safely
  returns `0.0` rather than raising
- LLM/comparison failure → `500`

---

## Module 4: Interview Plan Generation — ✅ Implemented

### What it does
1. Accepts `POST /interview/plan` with `{"resume_id": ..., "jd_id": ..., "match_id": ...}`,
   loading all three previously-computed records from storage (Modules 1-3).
2. Sends the resume, JD, and match analysis to the LLM (`plan_generator.py`),
   which produces a structured `InterviewPlan`:
   - `interview_strategy_summary` — a short, candidate-specific approach (not
     generic advice)
   - `starting_difficulty` — informed by the match percentage from Module 3
   - `opening_questions` — low-pressure warm-up questions
   - `topic_priorities` — ordered, each with an `importance` level and a
     `reason` grounded in the actual missing/weak skills from Module 3
   - `project_follow_ups` — specific named projects pulled from the
     candidate's actual resume data (the prompt explicitly forbids
     inventing projects), each with targeted follow-up questions
   - `sequence` — the overall phase order for the conversation
   - `estimated_question_count`
3. Persists the plan to `data/storage/interview_plans/<uuid>.json`, including
   the source `resume_id`/`jd_id`/`match_id` for full traceability back
   through the pipeline, and returns it.

### Why this module is entirely LLM-driven (unlike Module 3's scoring)
Module 3 kept its headline number deterministic because a percentage should
be reproducible. This module is different: deciding *what to ask* and *how
to sequence a conversation* is inherently a judgment call — there's no
"correct" formula for it, and forcing it into rules would make the
interviewer feel scripted, which is exactly what your spec says to avoid.
This is the right place for the LLM to have full creative control, with the
resume/JD/match data as grounding to prevent invented details.

### How to test it

Requires Modules 1-3 to have already run (resume uploaded, JD parsed, match
computed) since this loads all three by ID:

```bash
# after steps 1-3 from Module 3's testing instructions, using the same IDs:
curl -X POST "http://localhost:8000/interview/plan" \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "<resume_id>", "jd_id": "<jd_id>", "match_id": "<match_id>"}'
```

Swagger UI works the same way: run `/resume/upload`, `/job-description/parse`,
and `/match/compare` first, then feed their IDs into `/interview/plan`.

**What a successful response looks like:**
```json
{
  "interview_strategy_summary": "Focus on confirming backend depth then probing the Docker gap directly.",
  "starting_difficulty": "medium",
  "opening_questions": ["Walk me through your experience with FastAPI."],
  "topic_priorities": [
    {"topic": "Docker/Containerization", "importance": "high", "reason": "Missing skill vs JD."}
  ],
  "project_follow_ups": [
    {"project_name": "API Gateway", "questions": ["Why Redis for caching?"], "reason": "Relevant evidenced project."}
  ],
  "sequence": ["Warm-up", "Core technical", "Project deep-dive", "Gap probing", "Wrap-up"],
  "estimated_question_count": 9
}
```

This was verified end-to-end in a sandboxed test: the schema was validated
in isolation with a mocked LLM response, then the **full chain** — real
resume upload → real JD parse → real match compare → real interview plan
generation, all through FastAPI's `TestClient` with LLM calls mocked at each
step — was run successfully, including the 404 path for an invalid
`match_id`. Storage was confirmed to correctly carry the `resume_id`/
`jd_id`/`match_id` trail through every stage.

### Error handling already in place
- `resume_id` not found → `404`
- `jd_id` not found → `404`
- `match_id` not found → `404`
- LLM/generation failure → `500`

---

## Module 5: Live Adaptive Voice Interview Engine — ✅ Implemented

### What it does

Two endpoints implement the full loop from the spec (LLM → TTS → candidate
speaks → Whisper → transcript → LLM evaluation → next question):

**`POST /interview/session/start`** `{"plan_id": ...}`
1. Loads the interview plan (Module 4) plus the resume and JD it was built from.
2. Uses the plan's first `opening_questions` entry as question 1 (or asks
   the LLM to generate one if the plan has none).
3. Synthesizes it to speech via `voice_client.synthesize_speech` (OpenAI TTS)
   and saves the mp3 under `data/audio/<session_id>/q_1.mp3`, served at
   `/audio/<session_id>/q_1.mp3` (mounted as static files).
4. Persists a new `InterviewSession` to `data/storage/interview_sessions/<session_id>.json`.

**`POST /interview/session/answer`** (multipart: `session_id` + `audio` file)
1. Saves the candidate's uploaded answer audio and transcribes it via
   `voice_client.transcribe_audio` (Whisper).
2. Runs `quick_evaluate_answer` — a fast, single-dimension LLM judgment
   (`correct` / `partial` / `incorrect`) used only for adaptive routing.
   This is intentionally shallow; the thorough multi-dimensional grading
   (technical accuracy, STAR, confidence, etc.) is Module 8's job, not this
   live loop's.
3. Feeds that judgment into `difficulty_engine.next_difficulty` — a
   **deterministic** easy/medium/hard state machine (correct → step up,
   incorrect → step down, partial → stay), so difficulty progression is
   reproducible rather than left to per-call LLM whim.
4. If the plan's `estimated_question_count` has been reached, ends the
   interview. Otherwise calls `generate_next_question`, which is given the
   *full* conversation history, the interview plan, resume, and JD, and
   decides freely: go deeper on the same topic, move to the next plan
   topic, trigger a project follow-up if the candidate mentioned a relevant
   project, or signal the interview is naturally complete
   (`is_final_question`). Per your spec, there is no predefined question
   list anywhere in this path.
5. Synthesizes the next question to speech and appends a new turn to the
   session, or marks `is_complete: true` with no next question.

### Design decisions worth calling out

- **Deterministic difficulty, LLM-judged correctness** — same split as
  Module 3's scoring: the *signal* (was this answer good?) needs language
  understanding so it's LLM-driven; the *state transition* (what difficulty
  comes next) is a fixed rule so two runs with the same answers always
  produce the same difficulty curve.
- **Quick assessment vs. full evaluation are different modules on purpose**
  — gating a live conversation on an expensive, multi-dimensional grading
  pass would slow down the interview loop for no benefit to routing
  decisions. Module 8 will do the real grading, either after the interview
  or per-turn in parallel, without blocking the next question.
- **Graceful TTS degradation** — if speech synthesis fails (e.g. no API
  key configured, rate limit), the endpoint doesn't hard-fail the whole
  interview; it returns the question text with `question_audio_url: null`
  so a text-only interview can still proceed. Transcription failures do
  fail the request, since there's no way to adapt the interview without
  knowing what the candidate said.
- **`current_topic_index` is a soft progress indicator**, not a strict
  pointer into `plan.topic_priorities` — it increments whenever the LLM's
  chosen topic label changes from the previous turn. This gives a rough
  "how far through the plan are we" signal for a future frontend progress
  bar without requiring brittle exact-string matching against the plan.

### How to test it

Requires Modules 1-4 to have already run (resume, JD, match, plan all in storage):

```bash
# after getting a plan_id from Module 4's testing steps:
curl -X POST "http://localhost:8000/interview/session/start" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "<plan_id>"}'
# -> {"session_id": "...", "question": "...", "question_audio_url": "/audio/.../q_1.mp3", ...}

# Play/open the audio URL to hear the question, record your spoken answer,
# then submit it as a file (any format Whisper accepts: mp3, mp4, wav, webm, m4a...):
curl -X POST "http://localhost:8000/interview/session/answer" \
  -F "session_id=<session_id_from_above>" \
  -F "audio=@/path/to/your_answer.webm"
# -> {"transcript": "...", "quick_assessment": {...}, "next_question": "...", "next_question_audio_url": "...", "is_complete": false}
```

Repeat the `/answer` call (using the same `session_id`, answering the new
`next_question` each time) until the response comes back with
`"is_complete": true` and no `next_question`.

This was verified end-to-end in a sandboxed test with the LLM and voice
calls mocked: `difficulty_engine`'s state machine was checked against every
boundary case (capping at "hard"/"easy", "partial" holding steady); a full
session was run through the real FastAPI app — start → answer (with the
mocked transcript correctly triggering a Redis follow-up question via the
plan's `project_follow_ups`, and difficulty correctly escalating
medium→hard on a "correct" quick assessment) — confirming static audio
files are actually served at their returned URLs; a second session with
`estimated_question_count: 1` was run to completion to verify the
`is_complete` path and its guard against answering a finished session
(`400`); and the `404` paths for a missing session or missing plan were
both confirmed.

### Error handling already in place
- `plan_id` not found (or its linked resume/JD missing) → `404`
- `session_id` not found → `404`
- Answering an already-complete session → `400`
- Whisper transcription failure → `500` (fails hard — can't adapt blind)
- TTS synthesis failure → degrades to `question_audio_url: null`, does not fail the request
- LLM evaluation/question-generation failure → `500`

### Practical note on real usage
`voice_client.py` calls OpenAI's real TTS (`tts-1`) and Whisper
(`whisper-1`) endpoints, so this module needs a working `OPENAI_API_KEY`
in `.env` to run against real audio — the sandboxed tests above mock those
calls out since no key is configured in this build environment. The audio
format accepted for answers is whatever Whisper supports (mp3, mp4, wav,
webm, m4a, etc.); a browser's `MediaRecorder` typically produces `.webm`,
which works out of the box.

---

## Module 6: Computer Vision Analysis — ✅ Implemented

### What it does

**`POST /cv/session/{session_id}/frame`** (multipart image upload)
1. Verifies the interview session exists (must have been started via Module 5).
2. Decodes the uploaded webcam snapshot and runs it through MediaPipe
   FaceMesh (478 landmarks, including iris refinement).
3. If a face is found, extracts 6 key landmark points (nose tip, chin, eye
   corners, mouth corners) and computes, all via pure OpenCV/numpy geometry
   — **no LLM involved anywhere in this module**, same "keep it
   reproducible" principle as Module 3's scoring:
   - **Head pose** (pitch/yaw/roll) via the standard 6-point `solvePnP`
     technique with a generic 3D face model
   - **Eye contact** / **looking away** / **looking down** — threshold
     classification on the pose angles
   - **Smiling** — heuristic: mouth width relative to inter-ocular distance
   - **Attention score** (0-100) — a weighted combination of the above for
     this single frame
4. Appends the frame's metrics to `data/storage/cv_metrics/<session_id>.json`
   and returns the frame's metrics plus a running average attention score.

**`GET /cv/session/{session_id}/summary`**
Aggregates every frame recorded so far into a `CVSessionSummary`: face
visibility %, eye contact %, looking-away %, looking-down %, smile
frequency %, average attention score, and a short deterministic label
describing overall camera behavior (e.g. "Mostly centered, good eye
contact" or "Frequently looking away from camera").

The frontend is expected to call `/frame` periodically (e.g. every 1-2
seconds) with a webcam snapshot while a Module 5 interview session is
running, then call `/summary` for the final report (Module 10).

### How the geometry actually got verified (not just "looked reasonable")

Head pose estimation is the trickiest part of this module, so it got the
most rigorous testing:

1. **Synthetic ground-truth test**: the 3D face model was rotated by known
   yaw/pitch/roll angles and re-projected into 2D using `cv2.projectPoints`
   — the exact inverse of what `solvePnP` does. Feeding those synthetic
   landmarks back into `estimate_head_pose` recovers the original angles
   to within ~0.1 degrees across every test case (frontal, ±30° yaw, ±25°
   pitch, combined tilt). This validates the math is correct, independent
   of whether real face detection works.
2. **Real image test**: MediaPipe FaceMesh was run against a real
   photograph (a standard CV test image bundled with OpenCV's own sample
   data, used here only for internal testing — not shipped in this
   deliverable) to confirm actual detection, not just the math. This
   surfaced a real bug: a well-known ambiguity in minimal 6-point
   `solvePnP` produced a mirror-flipped pose (~180° off) on this real,
   somewhat off-axis photo, even though every synthetic test passed. Fixed
   by seeding `solvePnP` with an extrinsic initial guess (facing the
   camera, plausible distance) plus a post-hoc correction folding any
   residual ~180° flip back into the physically plausible range — after
   which the real image produced sensible values (yaw ≈ -34°, correctly
   flagging the subject as not looking at the camera, which matches that
   photo's actual off-axis pose) *and* every synthetic test case still
   passed unchanged.
3. **Full endpoint test**: ran the real face image and a blank (no-face)
   image through the actual `/cv/session/{id}/frame` endpoint via
   `TestClient` (this part not mocked — genuine MediaPipe inference),
   confirmed `face_visible` correctly flips true/false, confirmed the
   `/summary` aggregation math, and confirmed the 404 paths (unknown
   session, no frames recorded yet).

### How to test it

Requires a Module 5 session to already be started:

```bash
# after starting a session via Module 5 and getting a session_id:
curl -X POST "http://localhost:8000/cv/session/<session_id>/frame" \
  -F "frame=@/path/to/webcam_snapshot.jpg"

# call this repeatedly (e.g. every 1-2s) while the interview runs, then:
curl "http://localhost:8000/cv/session/<session_id>/summary"
```

**What a successful `/frame` response looks like:**
```json
{
  "frame": {
    "frame_number": 1,
    "face_visible": true,
    "yaw_degrees": -5.2,
    "pitch_degrees": 3.1,
    "roll_degrees": 0.8,
    "eye_contact": true,
    "looking_away": false,
    "looking_down": false,
    "smiling": false,
    "attention_score": 100.0
  },
  "running_average_attention_score": 100.0
}
```

**What a successful `/summary` response looks like:**
```json
{
  "session_id": "...",
  "total_frames_analyzed": 42,
  "face_visibility_percentage": 97.6,
  "eye_contact_percentage": 81.0,
  "looking_away_percentage": 9.5,
  "looking_down_percentage": 4.8,
  "smile_frequency_percentage": 21.4,
  "average_attention_score": 78.3,
  "dominant_face_orientation": "Mostly centered, good eye contact"
}
```

### Error handling already in place
- Frame submitted for a `session_id` that doesn't exist (in Module 5's
  session store) → `404`
- Undecodable image data (corrupted/unsupported format) → `400`
- `/summary` requested before any frames have been recorded → `404`
- solvePnP failing to converge on a degenerate landmark configuration →
  frame is still recorded as `face_visible: true` with a neutral fallback
  attention score, rather than failing the whole request

### Practical notes
- Thresholds (eye-contact angle range, looking-away/-down cutoffs, smile
  ratio) are heuristics tuned for a typical laptop-webcam interview
  angle, not clinically validated — documented as such directly in
  `geometry.py`.
- `FaceLandmarker` runs in `running_mode=IMAGE` since each API call analyzes
  one independent snapshot rather than a continuous video stream in a
  single process — the right mode for this frame-by-frame HTTP upload
  pattern.
- **Model setup (updated after initial release):** this module originally
  pinned `mediapipe==0.10.13` because that version still shipped the legacy
  `mp.solutions.face_mesh` API with its model bundled in the pip package —
  no download needed. That version isn't available for all platforms
  (notably several newer Mac wheels only start at 0.10.30+), and MediaPipe
  removed the legacy Solutions API entirely from 0.10.18 onward. The module
  now uses MediaPipe's current Tasks API
  (`mediapipe.tasks.python.vision.FaceLandmarker`), which needs a small
  (~4MB) model bundle. `model_setup.py` downloads it automatically on first
  use from Google's official model repository and caches it at
  `app/modules/cv_analysis/models/face_landmarker.task` — nothing to do
  manually in the normal case. If your network blocks
  `storage.googleapis.com`, the first `/cv/session/.../frame` call will
  fail with a clear error message containing the direct download URL and
  the exact local path to save it to. `requirements.txt` now allows any
  `mediapipe>=0.10.30` rather than pinning an exact version, since the
  Tasks API is stable across these releases (unlike the legacy API, which
  had a hard compatibility cliff at 0.10.18).

---

## Module 7: Speech Analysis — ✅ Implemented

### What it does

**`POST /speech/session/{session_id}/analyze/{turn_number}`**
1. Loads the specified turn from a Module 5 interview session (must already
   have a submitted answer — transcript and saved answer audio).
2. Requests **word-level timestamps** from Whisper on the saved answer
   audio (`voice_client.transcribe_with_word_timestamps` — a separate call
   from Module 5's quick transcript; see "Practical notes" below for why).
3. Runs four independent, fully deterministic sub-analyzers — **no LLM
   anywhere in this module**, same principle as Module 6:
   - **`filler_words.py`** — regex word-boundary matching against a filler
     list (um, uh, like, basically, you know, sort of, ...), counted and
     broken down per word.
   - **`pace_analyzer.py`** — speaking rate in WPM from word count over
     speaking duration (first word start → last word end, i.e. excluding
     leading/trailing silence), plus detection of any gap between
     consecutive words ≥1.5s as a "long pause."
   - **`clarity_analyzer.py`** — average sentence length and a clarity
     score that penalizes rambling run-on sentences and overly fragmented
     delivery.
   - **`confidence_analyzer.py`** — detects hedging language ("I think",
     "maybe", "I'm not sure", "kind of") as an established linguistic
     marker of reduced confidence, combined with filler rate and pause
     count into a confidence score.
4. Blends clarity/confidence/pace into a single `communication_quality_score`
   (40/30/30 weighted) and generates a few plain-English `notes` flagging
   anything notable (fast pace, high filler usage, long pauses, rambling).
5. Persists the result to `data/storage/speech_metrics/<session_id>.json`
   (keyed by turn, re-analyzing a turn overwrites its previous result
   rather than duplicating).

**`GET /speech/session/{session_id}/summary`** averages every analyzed
turn into a `SpeechSessionSummary` for the final report (Module 10).

### Why this stays out of Module 8's territory

Your spec lists "Communication" as both a Step 7 speech-analysis concern
and a Step 8 LLM-evaluation dimension. I kept the split intentional rather
than redundant: this module only looks at **how** something was said —
pace, pauses, filler words, hedging phrases, sentence structure — all
measurable from the transcript and audio timing alone. Whether the answer
was actually *correct* or *relevant* content-wise is Module 8's job, which
needs an LLM to judge. A candidate could speak with perfect pace and zero
filler words while giving a technically wrong answer; these are genuinely
different signals, and keeping the speech-pattern half deterministic means
it's reproducible and doesn't burn an LLM call per answer just to notice
"they paused for 3 seconds."

### How to test it

Requires a Module 5 turn to already have a submitted answer:

```bash
# after answering a question via Module 5's /interview/session/answer:
curl -X POST "http://localhost:8000/speech/session/<session_id>/analyze/1"

# then, at any point (or after the interview ends):
curl "http://localhost:8000/speech/session/<session_id>/summary"
```

**What a successful `/analyze` response looks like:**
```json
{
  "turn_number": 1,
  "word_count": 15,
  "speaking_duration_seconds": 6.95,
  "speaking_rate_wpm": 129.5,
  "filler_word_count": 2,
  "filler_word_rate_per_100_words": 13.3,
  "filler_word_breakdown": [{"word": "um", "count": 1}, {"word": "like", "count": 1}],
  "long_pauses": [{"start_seconds": 1.65, "end_seconds": 3.55, "duration_seconds": 1.9}],
  "long_pause_count": 1,
  "total_pause_duration_seconds": 1.9,
  "average_sentence_length_words": 15.0,
  "clarity_score": 100.0,
  "confidence_score": 70.0,
  "communication_quality_score": 91.0,
  "notes": [
    "Speaking pace is within a natural conversational range.",
    "High filler word usage (13.3 per 100 words).",
    "1 long pause(s) detected, totaling 1.9s -- may indicate uncertainty or time spent formulating the answer."
  ]
}
```

This was verified with real (not just plausible-looking) test coverage:
- **`filler_words.py`** tested against a transcript deliberately packed
  with fillers, confirming correct per-phrase breakdown including
  multi-word phrases ("you know", "I mean").
- **`pace_analyzer.py`** tested with synthetic word timestamps: an
  evenly-paced 10-word sequence correctly computed ~154 WPM with zero
  pauses, while injecting a 2.2s gap correctly both dropped the effective
  WPM and detected exactly one long-pause event with the right boundaries.
- **`clarity_analyzer.py`** and **`confidence_analyzer.py`** tested against
  contrasting example transcripts — a concise, hedge-free technical answer
  scored clarity 100 / confidence 100, while a genuinely rambling 77-word
  run-on sentence and a heavily hedged answer ("I think maybe... I'm not
  sure... it could be wrong...") both scored substantially lower, as expected.
- The **full orchestration** and **the actual endpoints** were run
  end-to-end through the real FastAPI app, chained after real Modules
  1-5 calls (LLM/TTS/STT mocked, since no API key is configured in this
  sandbox): submitted an answer, analyzed its speech, fetched the summary,
  and confirmed persistence — plus all error paths (analyzing a
  nonexistent turn, a nonexistent session, an unanswered turn, and
  fetching a summary before any analysis has run).

### Error handling already in place
- `session_id` not found → `404`
- `turn_number` doesn't exist in that session → `404`
- Turn exists but hasn't been answered yet → `400`
- Answer audio file missing from disk → `404`
- Whisper transcription failure → `500`
- `/summary` requested before any turn has been analyzed → `404`

### Practical notes
- **Two Whisper calls per answer, by design.** Module 5 requests a quick
  plain-text transcript to keep the live interview loop responsive; this
  module makes its own separate call requesting `verbose_json` with
  word-level timestamps, since pause/pace detection genuinely needs that
  detail. This is a deliberate decoupling trade-off (documented in
  `voice_client.py`) — it costs a second API call per answer, but means
  Module 7 can analyze any audio independently of whether it went through
  a live Module 5 session, and keeps Module 5's response time from being
  held up by the extra transcription detail it doesn't need.
- All thresholds (long-pause cutoff, ideal WPM range, filler/hedge word
  lists, clarity penalties) are heuristics tuned for a natural
  conversational interview pace — documented as such in each analyzer file.
- Like Module 5, this needs a real `OPENAI_API_KEY` to call Whisper on
  actual audio; the sandboxed tests above mock that call, but every
  scoring/aggregation function around it is tested with real (non-mocked)
  logic against synthetic and hand-crafted inputs.

---

## Module 8: LLM Answer Evaluation — ✅ Implemented

### What it does

**`POST /evaluation/session/{session_id}/evaluate/{turn_number}`**
1. Loads the specified turn from a Module 5 session (must already be
   answered) plus the resume and JD for grounding.
2. Sends the question, transcribed answer, resume, and JD to the LLM
   (`evaluator.py`), which scores each **applicable** dimension 0-100 with
   a `reasoning` string explaining *why* — directly per your spec's "The
   LLM should also explain WHY it assigned each evaluation":
   - **Technical**: `technical_accuracy`, `depth_of_knowledge`, `problem_solving`
   - **Behavioral**: `behavioral_skills`, `star_method_adherence`
   - **Always scored**: `communication`, `confidence`, `explanation_quality`
3. The LLM first decides `is_behavioral_question` and nulls out whichever
   dimension group doesn't apply (a "why did you choose Redis" question
   gets no STAR/behavioral score; a "tell me about a conflict" question
   gets no technical-accuracy score) rather than forcing every question
   into all 8 boxes.
4. `aggregator.py` then computes `overall_score` **deterministically** —
   a weighted average over only the dimensions that were actually scored,
   with weights renormalized so the result stays on a consistent 0-100
   scale regardless of how many dimensions applied. The LLM never states
   this number itself.
5. Persists to `data/storage/answer_evaluations/<session_id>.json`
   (keyed by turn; re-evaluating overwrites rather than duplicates).

**`GET /evaluation/session/{session_id}/summary`** averages each dimension
across every evaluated turn (skipping turns where that dimension didn't
apply) into an `EvaluationSessionSummary` for Module 10's final report.

### How this avoids overlapping with Modules 6/7

Your spec's Step 8 dimension list includes "Communication" and
"Confidence" — which also appear as concerns in Module 7. The system
prompt draws the line explicitly: this module's `communication` dimension
judges the **logical structure and organization of the answer's content**
(did the explanation flow logically?), while Module 7's speech metrics
measure **delivery mechanics** (pace, filler words, pauses). Same split
for `confidence`: here it's about how directly the candidate asserted
their *claims* in the content; Module 7's is about hedging language and
speech patterns. Module 10 will have all three signals (CV attention,
speech delivery, content evaluation) available separately rather than one
blurring into another.

### Why the score-vs-aggregate split matters here specifically

This is the same principle as Module 3's match percentage and Module 5's
difficulty state machine, applied to the highest-stakes number in the
whole pipeline: the LLM's job is judgment calls that need language
understanding (was this technically correct? was STAR followed?), each
individually justified with reasoning. The arithmetic that turns 3-8
scores into one number is fixed, auditable code — so if two answers get
identical dimension scores, they get an identical overall_score, and you
can always see exactly which weights produced it.

### How to test it

Requires a Module 5 turn to already have a submitted answer:

```bash
curl -X POST "http://localhost:8000/evaluation/session/<session_id>/evaluate/1"
curl "http://localhost:8000/evaluation/session/<session_id>/summary"
```

**What a successful `/evaluate` response looks like (technical question):**
```json
{
  "turn_number": 1,
  "question": "Why did you choose Redis for caching?",
  "is_behavioral_question": false,
  "technical_accuracy": {"score": 85.0, "reasoning": "Correctly explains Redis TTL and speed."},
  "depth_of_knowledge": {"score": 70.0, "reasoning": "No trade-off discussion."},
  "problem_solving": {"score": 80.0, "reasoning": "Clear problem framing."},
  "behavioral_skills": null,
  "star_method_adherence": null,
  "communication": {"score": 88.0, "reasoning": "Well organized."},
  "confidence": {"score": 82.0, "reasoning": "Direct claims."},
  "explanation_quality": {"score": 78.0, "reasoning": "Good explanation."},
  "overall_score": 80.3,
  "overall_summary": "Solid technical answer."
}
```

This was verified with the same rigor as the other scoring modules:
- **`aggregator.py`** tested directly against three synthetic cases: a
  technical-only evaluation (behavioral dimensions null), a behavioral-only
  evaluation (technical dimensions null), and confirmed the renormalized
  weighted average was correct in both cases (80.3 and 76.5 respectively)
  — then confirmed the full LLM-mocked `evaluate_answer()` call reproduced
  the *exact same* 80.3 for the technical case, proving the aggregator
  integration is wired correctly end to end.
- Session summary tested with mixed technical/behavioral evaluations,
  confirming per-dimension averages correctly skip turns where that
  dimension didn't apply (nulls excluded, not treated as zero).
- The full endpoint chain was run through the real FastAPI app after real
  Modules 1-5 calls (LLM/TTS/STT mocked): submitted an answer, evaluated
  it, fetched the summary, confirmed persistence, and checked all error
  paths (nonexistent turn, nonexistent session, unanswered turn, summary
  requested before any evaluation exists).

### Error handling already in place
- `session_id` not found → `404`
- `turn_number` doesn't exist in that session → `404`
- Turn exists but hasn't been answered yet → `400`
- Linked resume/JD missing from storage → `404`
- LLM evaluation failure → `500`
- `/summary` requested before any turn has been evaluated → `404`

---

## Module 9: Scoring Engine — ✅ Implemented

### What it does

**`GET /score/session/{session_id}`**
1. Loads the interview session (for `match_id`) plus whatever Module
   3/6/7/8 data exists for it: the match result, evaluation summary, CV
   summary, and speech summary.
2. Maps each onto exactly one of your spec's six weighted categories —
   **entirely deterministic, no LLM anywhere in this module**:

   | Category | Weight | Source |
   |---|---|---|
   | Resume Match | 15% | Module 3's `resume_match_percentage` |
   | Technical Answers | 35% | Module 8's `technical_accuracy` + `depth_of_knowledge` + `problem_solving`, averaged |
   | Communication | 15% | Module 8's `communication` dimension (content structure) |
   | Computer Vision | 15% | Module 6's `average_attention_score` |
   | Speech Analysis | 10% | Module 7's `average_communication_quality_score` (delivery mechanics) |
   | Behavioral Performance | 10% | Module 8's `behavioral_skills` + `star_method_adherence`, averaged |

3. Computes `overall_score` as the weighted average — but if a category's
   underlying data doesn't exist (webcam never used, no behavioral
   questions came up, nothing evaluated yet), that category is marked
   `available: false` and **excluded**, with the remaining weights
   renormalized to sum to 1 rather than penalizing a candidate for a
   component that was never run. `categories_included` /
   `categories_missing` make this transparent in the response.
4. Persists to `data/storage/overall_scores/<session_id>.json`.

### Mapping "Communication" and "Speech Analysis" to two different modules

Your spec's scoring table lists these as two separate 15%/10% categories,
which resolves a question I flagged in Module 7/8's docs: they're meant to
be separate signals, not one blended number. "Communication" (15%) draws
from Module 8's content-structure judgment; "Speech Analysis" (10%) draws
from Module 7's delivery-mechanics judgment (pace, fillers, pauses). This
confirms the Module 7/8 split was the right call, not redundant — the
spec's own scoring weights depend on keeping them apart.

### Why this module has zero LLM calls

Every input arriving here is already a finished, scored aggregate from an
earlier module. There's nothing left to *judge* — only arithmetic to
*combine* — so this is the purest expression of the "LLM judges, code
aggregates" principle used throughout the project (Modules 3, 5, 8): by
the time you reach the top of the pipeline, judgment calls have already
been made and justified downstream; scoring_engine just adds them up
correctly and reproducibly.

### How to test it

Works after any subset of Modules 3/6/7/8 have run for a session — it
degrades gracefully rather than requiring all four:

```bash
curl "http://localhost:8000/score/session/<session_id>"
```

**What a successful response looks like (all categories present):**
```json
{
  "session_id": "...",
  "resume_match": {"score": 83.0, "weight": 0.15, "available": true},
  "technical_answers": {"score": 78.3, "weight": 0.35, "available": true},
  "communication": {"score": 88.0, "weight": 0.15, "available": true},
  "computer_vision": {"score": 60.0, "weight": 0.15, "available": true},
  "speech_analysis": {"score": 97.8, "weight": 0.10, "available": true},
  "behavioral_performance": {"score": null, "weight": 0.10, "available": false},
  "overall_score": 82.6,
  "categories_included": ["resume_match", "technical_answers", "communication", "computer_vision", "speech_analysis"],
  "categories_missing": ["behavioral_performance"]
}
```

This was tested more rigorously than the response above suggests:
- **Manually verified the arithmetic by hand**: with 5 of 6 categories
  available (weights summing to 0.90), computed the weighted sum by hand
  (72.78) and confirmed `72.78 / 0.90 = 80.9` matched the function's
  output exactly.
- **Tested three synthetic scenarios directly against `scorer.py`**: all
  categories present; CV and speech missing (webcam/mic skipped,
  behavioral question present) correctly renormalized around the
  remaining 4 categories; and completely empty input correctly degraded
  to `overall_score: 0.0` with every category marked unavailable, without
  raising an exception.
- **Full pipeline test through the real API**: ran the complete chain —
  real resume upload through real CV frame analysis (genuine MediaPipe
  detection on the same real test image from Module 6, which correctly
  contributed an attention score of 60.0, consistent with that image's
  known off-axis pose) through real speech and evaluation analysis — then
  called `/score/session/{id}` and got a fully-populated, correctly
  weighted result. A second session with only a resume/JD/match (no
  interview activity yet) correctly returned `overall_score: 100.0` with
  only `resume_match` included, proving the renormalization isn't just
  correct in isolation but wired correctly against real persisted data.

### Error handling already in place
- `session_id` not found → `404`
- Any of match/CV/speech/evaluation data missing → gracefully excluded
  from the score rather than erroring (see `categories_missing`)
- Zero categories available → returns `overall_score: 0.0` rather than
  dividing by zero

---

## Module 10: Report Generator — ✅ Implemented

### What it does

**`GET /report/session/{session_id}`**
1. Gathers everything computed across the entire pipeline for this
   session: resume, JD, Module 3's match result, every Module 8
   evaluation (with full per-dimension reasoning), Module 6's CV summary,
   Module 7's speech summary, and Module 9's overall weighted score.
2. Extracts **all nine of the spec's numeric report fields** deterministically:

   | Report field | Source |
   |---|---|
   | Resume Match Score | Module 9 → Module 3 |
   | Technical Score | Module 9 → Module 8 (technical dims) |
   | Communication Score | Module 9 → Module 8 (communication dim) |
   | Confidence Score | **new**: average of Module 7's + Module 8's confidence signals |
   | Eye Contact Score | **new**: Module 6's `eye_contact_percentage` directly |
   | Attention Score | Module 9 → Module 6 |
   | Behavioral Score | Module 9 → Module 8 (behavioral + STAR) |
   | Speech Quality Score | Module 9 → Module 7 |
   | Overall Interview Score | Module 9's `overall_score` directly |

   Two of these (Eye Contact, Confidence) are new at this module — Module
   9 deliberately didn't weight them into the overall score (see Module
   9's docs), but your spec's report still asks for them as standalone
   diagnostic numbers, so they're computed here without touching Module
   9's already-finalized weighting.
3. `missing_skills` is pulled directly from Module 3 — no LLM needed, it's
   already a concrete list.
4. The LLM (`generator.py`) synthesizes the parts that genuinely need
   holistic judgment across everything above: `strengths`, `weaknesses`,
   `recommended_learning_path`, `topics_to_practice`, and
   `interview_summary` — each grounded in the actual evaluation reasoning,
   match analysis, and delivery metrics, not generic filler.
5. `performance_breakdown` embeds Module 9's full `OverallScoreResult`
   (including `categories_included`/`categories_missing`) so the report
   is self-contained.
6. Persists to `data/storage/reports/<session_id>.json`.

### Where the LLM's role narrows down to just synthesis

By the time a request reaches this module, every number has already been
computed and justified by an earlier module — Module 8 already explained
*why* each answer scored what it did; Module 3 already explained *why*
each skill is missing. This module's LLM call isn't re-deriving any of
that judgment; it's doing something narrower and genuinely valuable:
turning a pile of already-correct structured data into the handful of
sentences a hiring manager would actually want to read, while staying
grounded in what's already been established. The prompt explicitly
forbids inventing anything not present in the input for exactly this reason.

### How to test it

Requires at least a resume, JD, and match to exist (session must exist);
works with any subset of Modules 6/7/8 data available, same graceful
degradation as Module 9:

```bash
curl "http://localhost:8000/report/session/<session_id>"
```

This was tested through the **complete pipeline, start to finish**: real
resume upload → real JD parse → real match compare → real interview plan
→ real session start → real answer submission → real CV frame analysis
(genuine MediaPipe detection) → real speech analysis → real answer
evaluation → **real report generation**, all chained through the actual
FastAPI app in one continuous test (LLM/TTS/STT calls mocked, since no API
key is configured in this sandbox). Every score in the resulting report
was cross-checked against the upstream module that produced it — e.g.
`eye_contact_score: 0.0` correctly reflects that the one test frame had
`eye_contact: False` (consistent with Module 6's own findings on that same
test image), and `confidence_score: 91.0` correctly averages the mocked
Module 7 and Module 8 confidence values. The `404` path for a nonexistent
session was also confirmed.

### Error handling already in place
- `session_id` not found → `404`
- Linked resume/JD missing from storage → `404`
- Match/CV/speech/evaluation data missing → gracefully degrades (same as
  Module 9), report is still generated with whatever's available
- LLM narrative generation failure → `500`

---

## All 10 Backend Modules Complete

Every module in the spec's workflow — resume parsing through final report
generation — is implemented, wired into a single FastAPI app, and tested
end-to-end as one continuous pipeline: upload a resume and JD, get a match
score, generate an interview plan, run a live adaptive voice interview
with real-time CV and speech tracking, evaluate every answer, and produce
a final weighted report — 19 endpoints total.

**The recurring design principle worth restating**, since it shows up in
every module: the LLM is used exactly where language understanding is
required (parsing unstructured text, judging answer quality, deciding what
to ask next, writing narrative synthesis) and nowhere else. Every score
that should be reproducible — resume match percentage, difficulty
progression, CV/speech metrics, the weighted overall score — is computed
in plain, auditable code. This isn't just a style preference: it's what
makes the system's numbers trustworthy and its behavior debuggable, which
is exactly what you'd want someone reviewing this on GitHub to notice.

## All 10 Backend Modules Complete + Frontend

Every module in the spec's workflow — resume parsing through final report
generation — is implemented, wired into a single FastAPI app, and tested
end-to-end as one continuous pipeline. A Streamlit frontend (HackerRank-style
assessment UI) now sits on top of it — see `frontend/streamlit_app/README.md`
for details on the UI itself, its reactivity mechanisms, and two real bugs
that testing caught and fixed during integration.

**The recurring design principle worth restating**, since it shows up in
every module: the LLM is used exactly where language understanding is
required (parsing unstructured text, judging answer quality, deciding what
to ask next, writing narrative synthesis) and nowhere else. Every score
that should be reproducible — resume match percentage, difficulty
progression, CV/speech metrics, the weighted overall score — is computed
in plain, auditable code. This isn't just a style preference: it's what
makes the system's numbers trustworthy and its behavior debuggable, which
is exactly what you'd want someone reviewing this on GitHub to notice.

## Frontend

Built with Streamlit rather than Next.js per your request — styled after
HackerRank's online-assessment interface (dark chrome, monospace timer,
question-navigator dots) and made more reactive than typical Streamlit apps
via `st.fragment(run_every=...)` auto-refreshing widgets and a continuous
`streamlit-webrtc` webcam feed instead of click-to-snapshot. Full details,
setup instructions, and the reactivity mechanisms are in
`frontend/streamlit_app/README.md`.

Quick start (two terminals):
```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload

# Terminal 2
cd frontend/streamlit_app && pip install -r requirements.txt && streamlit run app.py
```
