"""
FastAPI entry point.

Module 1 scope: resume upload + parsing only.
Later modules (JD parsing, interview engine, CV analysis, scoring,
report generation) will each register their own router here, but we
add them one at a time as agreed.
"""

import os
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.modules.cv_analysis.aggregator import summarize_session as summarize_cv_session
from app.modules.cv_analysis.face_analyzer import analyze_frame, decode_image
from app.modules.cv_analysis.schema import CVSessionSummary, FrameAnalysisResponse, FrameMetrics
from app.modules.evaluation_engine.aggregator import summarize_session as summarize_evaluation_session
from app.modules.evaluation_engine.evaluator import evaluate_answer
from app.modules.evaluation_engine.schema import AnswerEvaluation, EvaluationSessionSummary
from app.modules.interview_engine.conversation_engine import generate_next_question, quick_evaluate_answer
from app.modules.interview_engine.difficulty_engine import next_difficulty
from app.modules.interview_engine.plan_generator import generate_interview_plan
from app.modules.interview_engine.schema import (
    AnswerResponse,
    ConversationTurn,
    InterviewPlan,
    InterviewSession,
    StartSessionResponse,
)
from app.modules.job_parser.parser import parse_job_description_text
from app.modules.job_parser.schema import ParsedJobDescription
from app.modules.job_parser.text_extractor import JobDescriptionExtractionError, extract_text_from_file
from app.modules.match_engine.matcher import compare_resume_to_job
from app.modules.match_engine.schema import MatchResult
from app.modules.resume_parser.parser import parse_resume_pdf
from app.modules.resume_parser.pdf_extractor import ResumeExtractionError
from app.modules.resume_parser.schema import ParsedResume
from app.modules.report_generator.generator import generate_report
from app.modules.report_generator.schema import InterviewReport
from app.modules.scoring_engine.schema import OverallScoreResult
from app.modules.scoring_engine.scorer import compute_overall_score
from app.modules.speech_analysis.aggregator import summarize_session as summarize_speech_session
from app.modules.speech_analysis.analyzer import analyze_answer_speech
from app.modules.speech_analysis.schema import SpeechAnalysisResult, SpeechSessionSummary
from app.utils.storage import load_json, save_json
from app.utils.voice_client import VoiceError, synthesize_speech, transcribe_audio

app = FastAPI(title="AI Interview System - Backend", version="0.1.0")

# Wide-open CORS is fine here: solo portfolio project, no auth, local dev only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated TTS audio files at /audio/<session_id>/<filename>.mp3
app.mount("/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/resume/upload", response_model=ParsedResume)
async def upload_resume(file: UploadFile = File(...)):
    """Accept a resume PDF, parse it, persist the structured result, and return it."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_RESUME_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max is {settings.MAX_RESUME_SIZE_MB}MB.",
        )

    resume_id = str(uuid.uuid4())
    saved_path = os.path.join(settings.RESUME_UPLOAD_DIR, f"{resume_id}.pdf")
    with open(saved_path, "wb") as f:
        f.write(contents)

    try:
        parsed = parse_resume_pdf(saved_path)
    except ResumeExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {e}")

    parsed.resume_id = resume_id

    # Persist structured JSON so later modules (JD matching, interview
    # engine) can load this candidate's resume by ID without re-parsing.
    save_json(f"{resume_id}.json", parsed.model_dump(), subdir="resumes")

    return parsed


@app.post("/job-description/parse", response_model=ParsedJobDescription)
async def parse_job_description(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    """Accept a job description as pasted text OR an uploaded PDF/.txt file, parse it, persist, and return it.

    Exactly one of `text` or `file` should be provided. If both are given,
    `text` takes priority.
    """
    if not text and not file:
        raise HTTPException(
            status_code=400,
            detail="Provide either pasted job description text or an uploaded file.",
        )

    if text:
        raw_text = text.strip()
        if not raw_text:
            raise HTTPException(status_code=400, detail="Pasted job description text is empty.")
    else:
        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > settings.MAX_RESUME_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({size_mb:.1f}MB). Max is {settings.MAX_RESUME_SIZE_MB}MB.",
            )

        suffix = ".pdf" if file.content_type == "application/pdf" else ".txt"
        temp_path = os.path.join(settings.DATA_DIR, f"_tmp_jd_{uuid.uuid4()}{suffix}")
        with open(temp_path, "wb") as f:
            f.write(contents)

        try:
            raw_text = extract_text_from_file(temp_path, file.content_type)
        except JobDescriptionExtractionError as e:
            raise HTTPException(status_code=422, detail=str(e))
        finally:
            os.remove(temp_path)

    try:
        parsed = parse_job_description_text(raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse job description: {e}")

    jd_id = str(uuid.uuid4())
    parsed.jd_id = jd_id
    save_json(f"{jd_id}.json", parsed.model_dump(), subdir="job_descriptions")

    return parsed


class MatchCompareRequest(BaseModel):
    resume_id: str
    jd_id: str


@app.post("/match/compare", response_model=MatchResult)
async def compare_resume_and_job_description(payload: MatchCompareRequest):
    """Compare a previously-parsed resume against a previously-parsed job description.

    Both must have already been uploaded via /resume/upload and
    /job-description/parse respectively, since this endpoint loads them
    from storage by ID rather than re-parsing raw input.
    """
    try:
        resume_data = load_json(f"{payload.resume_id}.json", subdir="resumes")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No resume found with id '{payload.resume_id}'.")

    try:
        jd_data = load_json(f"{payload.jd_id}.json", subdir="job_descriptions")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"No job description found with id '{payload.jd_id}'."
        )

    resume = ParsedResume(**resume_data)
    jd = ParsedJobDescription(**jd_data)

    try:
        result = compare_resume_to_job(resume, jd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare resume and job description: {e}")

    match_id = str(uuid.uuid4())
    result.match_id = match_id
    save_json(
        f"{match_id}.json",
        {"resume_id": payload.resume_id, "jd_id": payload.jd_id, **result.model_dump()},
        subdir="matches",
    )

    return result


class InterviewPlanRequest(BaseModel):
    resume_id: str
    jd_id: str
    match_id: str


@app.post("/interview/plan", response_model=InterviewPlan)
async def generate_plan(payload: InterviewPlanRequest):
    """Generate an interview strategy from a previously-parsed resume, JD, and match result.

    All three must already exist in storage (via /resume/upload,
    /job-description/parse, and /match/compare respectively).
    """
    try:
        resume_data = load_json(f"{payload.resume_id}.json", subdir="resumes")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No resume found with id '{payload.resume_id}'.")

    try:
        jd_data = load_json(f"{payload.jd_id}.json", subdir="job_descriptions")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"No job description found with id '{payload.jd_id}'."
        )

    try:
        match_data = load_json(f"{payload.match_id}.json", subdir="matches")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No match result found with id '{payload.match_id}'.")

    resume = ParsedResume(**resume_data)
    jd = ParsedJobDescription(**jd_data)
    # match_data also carries resume_id/jd_id fields (for traceability) that
    # aren't part of MatchResult's schema -- Pydantic ignores unknown keys
    # by default, so we can pass the raw dict straight through.
    match = MatchResult(**match_data)

    try:
        plan = generate_interview_plan(resume, jd, match)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate interview plan: {e}")

    plan_id = str(uuid.uuid4())
    plan.plan_id = plan_id
    save_json(
        f"{plan_id}.json",
        {
            "resume_id": payload.resume_id,
            "jd_id": payload.jd_id,
            "match_id": payload.match_id,
            **plan.model_dump(),
        },
        subdir="interview_plans",
    )

    return plan


def _load_plan_bundle(plan_id: str) -> tuple[InterviewPlan, ParsedResume, ParsedJobDescription, dict]:
    """Load an interview plan and everything it was generated from, by plan_id."""
    try:
        plan_data = load_json(f"{plan_id}.json", subdir="interview_plans")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No interview plan found with id '{plan_id}'.")

    plan = InterviewPlan(**plan_data)

    try:
        resume_data = load_json(f"{plan_data['resume_id']}.json", subdir="resumes")
        jd_data = load_json(f"{plan_data['jd_id']}.json", subdir="job_descriptions")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Linked resume or job description missing: {e}")

    resume = ParsedResume(**resume_data)
    jd = ParsedJobDescription(**jd_data)
    return plan, resume, jd, plan_data


def _audio_url(audio_path: str | None) -> str | None:
    if not audio_path:
        return None
    relative = os.path.relpath(audio_path, settings.AUDIO_DIR)
    return f"/audio/{relative}"


class StartSessionRequest(BaseModel):
    plan_id: str


@app.post("/interview/session/start", response_model=StartSessionResponse)
async def start_interview_session(payload: StartSessionRequest):
    """Start a live interview session from a previously-generated interview plan.

    Uses the plan's first opening question (or generates one if the plan
    has none), synthesizes it to speech, and persists a new session.
    """
    plan, resume, jd, plan_data = _load_plan_bundle(payload.plan_id)

    session_id = str(uuid.uuid4())
    session = InterviewSession(
        session_id=session_id,
        resume_id=plan_data["resume_id"],
        jd_id=plan_data["jd_id"],
        match_id=plan_data["match_id"],
        plan_id=payload.plan_id,
        current_difficulty=plan.starting_difficulty,
        current_topic_index=0,
        max_questions=max(plan.estimated_question_count, 1),
        is_complete=False,
        history=[],
    )

    if plan.opening_questions:
        question_text = plan.opening_questions[0]
        topic = plan.sequence[0] if plan.sequence else "Warm-up"
    else:
        try:
            generated = generate_next_question(session, plan, resume, jd)
            question_text = generated["question"]
            topic = generated.get("topic", "Warm-up")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate opening question: {e}")

    audio_path = os.path.join(settings.AUDIO_DIR, session_id, "q_1.mp3")
    try:
        synthesize_speech(question_text, audio_path)
    except VoiceError:
        # Degrade gracefully: the interview can still proceed as text-only
        # if TTS is unavailable (e.g. no API key configured in this environment).
        audio_path = None

    turn = ConversationTurn(
        turn_number=1,
        topic=topic,
        difficulty=session.current_difficulty,
        question=question_text,
        question_audio_path=audio_path,
    )
    session.history.append(turn)

    save_json(f"{session_id}.json", session.model_dump(), subdir="interview_sessions")

    return StartSessionResponse(
        session_id=session_id,
        turn_number=1,
        question=question_text,
        topic=topic,
        difficulty=session.current_difficulty,
        question_audio_url=_audio_url(audio_path),
        is_complete=False,
    )


@app.post("/interview/session/answer", response_model=AnswerResponse)
async def submit_interview_answer(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
):
    """Submit the candidate's spoken answer (audio) to the current question.

    Transcribes the answer via Whisper, runs a quick correctness assessment,
    adapts the difficulty, and generates the next question -- or marks the
    interview complete if the plan has been sufficiently covered.
    """
    try:
        session_data = load_json(f"{session_id}.json", subdir="interview_sessions")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No interview session found with id '{session_id}'.")

    session = InterviewSession(**session_data)

    if session.is_complete:
        raise HTTPException(status_code=400, detail="This interview session is already complete.")

    current_turn = session.history[-1]

    contents = await audio.read()
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    answer_path = os.path.join(
        settings.AUDIO_DIR, session_id, f"a_{current_turn.turn_number}{suffix}"
    )
    os.makedirs(os.path.dirname(answer_path), exist_ok=True)
    with open(answer_path, "wb") as f:
        f.write(contents)

    try:
        transcript = transcribe_audio(answer_path)
    except VoiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        quick = quick_evaluate_answer(current_turn.question, transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate answer: {e}")

    current_turn.answer_transcript = transcript
    current_turn.answer_audio_path = answer_path
    current_turn.quick_assessment = quick
    session.current_difficulty = next_difficulty(session.current_difficulty, quick.correctness)

    next_question_text = None
    next_topic = None
    next_audio_url = None

    if len(session.history) >= session.max_questions:
        session.is_complete = True
    else:
        plan, resume, jd, _ = _load_plan_bundle(session.plan_id)
        try:
            generated = generate_next_question(session, plan, resume, jd)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate next question: {e}")

        if generated.get("is_final_question"):
            session.is_complete = True
        else:
            next_topic = generated.get("topic", current_turn.topic)
            next_question_text = generated["question"]

            if next_topic != current_turn.topic and plan.topic_priorities:
                session.current_topic_index = min(
                    session.current_topic_index + 1, len(plan.topic_priorities) - 1
                )

            next_turn_number = len(session.history) + 1
            next_audio_path = os.path.join(
                settings.AUDIO_DIR, session_id, f"q_{next_turn_number}.mp3"
            )
            try:
                synthesize_speech(next_question_text, next_audio_path)
            except VoiceError:
                next_audio_path = None

            session.history.append(
                ConversationTurn(
                    turn_number=next_turn_number,
                    topic=next_topic,
                    difficulty=session.current_difficulty,
                    question=next_question_text,
                    question_audio_path=next_audio_path,
                )
            )
            next_audio_url = _audio_url(next_audio_path)

    save_json(f"{session_id}.json", session.model_dump(), subdir="interview_sessions")

    return AnswerResponse(
        session_id=session_id,
        transcript=transcript,
        quick_assessment=quick,
        is_complete=session.is_complete,
        next_question=next_question_text,
        next_topic=next_topic,
        next_difficulty=session.current_difficulty if not session.is_complete else None,
        next_question_audio_url=next_audio_url,
    )


def _load_cv_frames(session_id: str) -> list[FrameMetrics]:
    try:
        data = load_json(f"{session_id}.json", subdir="cv_metrics")
    except FileNotFoundError:
        return []
    return [FrameMetrics(**f) for f in data.get("frames", [])]


@app.post("/cv/session/{session_id}/frame", response_model=FrameAnalysisResponse)
async def analyze_interview_frame(session_id: str, frame: UploadFile = File(...)):
    """Analyze a single webcam snapshot captured during a live interview session.

    The frontend is expected to call this periodically (e.g. every 1-2
    seconds) while /interview/session/* is running. Metrics are appended
    to this session's CV log; call /cv/session/{session_id}/summary at any
    time (or after the interview ends) for the aggregated result.
    """
    try:
        load_json(f"{session_id}.json", subdir="interview_sessions")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No interview session found with id '{session_id}'.")

    contents = await frame.read()
    try:
        image = decode_image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing_frames = _load_cv_frames(session_id)
    frame_number = len(existing_frames) + 1

    try:
        metrics = analyze_frame(image, frame_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frame analysis failed: {e}")

    existing_frames.append(metrics)
    save_json(
        f"{session_id}.json",
        {"session_id": session_id, "frames": [f.model_dump() for f in existing_frames]},
        subdir="cv_metrics",
    )

    running_avg = round(sum(f.attention_score for f in existing_frames) / len(existing_frames), 1)

    return FrameAnalysisResponse(frame=metrics, running_average_attention_score=running_avg)


@app.get("/cv/session/{session_id}/summary", response_model=CVSessionSummary)
async def get_cv_session_summary(session_id: str):
    """Return the aggregated computer-vision summary for an interview session."""
    frames = _load_cv_frames(session_id)
    if not frames:
        raise HTTPException(
            status_code=404,
            detail=f"No CV frames recorded yet for session '{session_id}'.",
        )
    return summarize_cv_session(session_id, frames)


def _load_speech_results(session_id: str) -> list[SpeechAnalysisResult]:
    try:
        data = load_json(f"{session_id}.json", subdir="speech_metrics")
    except FileNotFoundError:
        return []
    return [SpeechAnalysisResult(**r) for r in data.get("results", [])]


@app.post("/speech/session/{session_id}/analyze/{turn_number}", response_model=SpeechAnalysisResult)
async def analyze_turn_speech(session_id: str, turn_number: int):
    """Run speech analysis (pace, pauses, filler words, clarity, confidence)
    on a specific answered turn from a Module 5 interview session.

    The turn must already have a submitted answer (via
    /interview/session/answer) since this analyzes the transcript and the
    saved answer audio, not a fresh upload.
    """
    try:
        session_data = load_json(f"{session_id}.json", subdir="interview_sessions")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No interview session found with id '{session_id}'.")

    session = InterviewSession(**session_data)
    turn = next((t for t in session.history if t.turn_number == turn_number), None)

    if turn is None:
        raise HTTPException(
            status_code=404, detail=f"No turn {turn_number} found in session '{session_id}'."
        )
    if not turn.answer_transcript or not turn.answer_audio_path:
        raise HTTPException(
            status_code=400, detail=f"Turn {turn_number} has not been answered yet."
        )
    if not os.path.exists(turn.answer_audio_path):
        raise HTTPException(
            status_code=404, detail=f"Answer audio file for turn {turn_number} is missing on disk."
        )

    try:
        result = analyze_answer_speech(turn_number, turn.answer_transcript, turn.answer_audio_path)
    except VoiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech analysis failed: {e}")

    existing_results = [r for r in _load_speech_results(session_id) if r.turn_number != turn_number]
    existing_results.append(result)
    existing_results.sort(key=lambda r: r.turn_number)

    save_json(
        f"{session_id}.json",
        {"session_id": session_id, "results": [r.model_dump() for r in existing_results]},
        subdir="speech_metrics",
    )

    return result


@app.get("/speech/session/{session_id}/summary", response_model=SpeechSessionSummary)
async def get_speech_session_summary(session_id: str):
    """Return the aggregated speech analysis summary across all turns analyzed so far."""
    results = _load_speech_results(session_id)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No speech analysis recorded yet for session '{session_id}'.",
        )
    return summarize_speech_session(session_id, results)


def _load_evaluations(session_id: str) -> list[AnswerEvaluation]:
    try:
        data = load_json(f"{session_id}.json", subdir="answer_evaluations")
    except FileNotFoundError:
        return []
    return [AnswerEvaluation(**e) for e in data.get("evaluations", [])]


@app.post("/evaluation/session/{session_id}/evaluate/{turn_number}", response_model=AnswerEvaluation)
async def evaluate_turn_answer(session_id: str, turn_number: int):
    """Run the full multi-dimensional LLM evaluation (Step 8) on a specific
    answered turn: technical accuracy, depth, problem solving, behavioral
    skills, STAR adherence, communication, confidence, and explanation
    quality -- each with the LLM's reasoning for that score.

    The turn must already have a submitted answer (via
    /interview/session/answer).
    """
    try:
        session_data = load_json(f"{session_id}.json", subdir="interview_sessions")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No interview session found with id '{session_id}'.")

    session = InterviewSession(**session_data)
    turn = next((t for t in session.history if t.turn_number == turn_number), None)

    if turn is None:
        raise HTTPException(
            status_code=404, detail=f"No turn {turn_number} found in session '{session_id}'."
        )
    if not turn.answer_transcript:
        raise HTTPException(status_code=400, detail=f"Turn {turn_number} has not been answered yet.")

    try:
        resume_data = load_json(f"{session.resume_id}.json", subdir="resumes")
        jd_data = load_json(f"{session.jd_id}.json", subdir="job_descriptions")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Linked resume or job description missing: {e}")

    resume = ParsedResume(**resume_data)
    jd = ParsedJobDescription(**jd_data)

    try:
        evaluation = evaluate_answer(turn.question, turn.answer_transcript, resume, jd, turn_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer evaluation failed: {e}")

    existing = [e for e in _load_evaluations(session_id) if e.turn_number != turn_number]
    existing.append(evaluation)
    existing.sort(key=lambda e: e.turn_number)

    save_json(
        f"{session_id}.json",
        {"session_id": session_id, "evaluations": [e.model_dump() for e in existing]},
        subdir="answer_evaluations",
    )

    return evaluation


@app.get("/evaluation/session/{session_id}/summary", response_model=EvaluationSessionSummary)
async def get_evaluation_session_summary(session_id: str):
    """Return the aggregated answer-evaluation summary across all turns evaluated so far."""
    evaluations = _load_evaluations(session_id)
    if not evaluations:
        raise HTTPException(
            status_code=404,
            detail=f"No answer evaluations recorded yet for session '{session_id}'.",
        )
    return summarize_evaluation_session(session_id, evaluations)


@app.get("/score/session/{session_id}", response_model=OverallScoreResult)
async def get_overall_score(session_id: str):
    """Compute the overall weighted interview score (Resume Match 15%,
    Technical Answers 35%, Communication 15%, Computer Vision 15%,
    Speech Analysis 10%, Behavioral Performance 10%) from whatever
    Modules 3/6/7/8 data is available for this session.

    Categories with no underlying data (e.g. the webcam was never used,
    or no behavioral questions came up) are excluded rather than
    penalized, and the remaining weights are renormalized -- see
    scoring_engine/scorer.py for details.
    """
    try:
        session_data = load_json(f"{session_id}.json", subdir="interview_sessions")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No interview session found with id '{session_id}'.")

    session = InterviewSession(**session_data)

    match_result = None
    try:
        match_data = load_json(f"{session.match_id}.json", subdir="matches")
        match_result = MatchResult(**match_data)
    except FileNotFoundError:
        pass

    evaluations = _load_evaluations(session_id)
    evaluation_summary = summarize_evaluation_session(session_id, evaluations) if evaluations else None

    cv_frames = _load_cv_frames(session_id)
    cv_summary = summarize_cv_session(session_id, cv_frames) if cv_frames else None

    speech_results = _load_speech_results(session_id)
    speech_summary = summarize_speech_session(session_id, speech_results) if speech_results else None

    result = compute_overall_score(session_id, match_result, evaluation_summary, cv_summary, speech_summary)

    save_json(f"{session_id}.json", result.model_dump(), subdir="overall_scores")

    return result


@app.get("/report/session/{session_id}", response_model=InterviewReport)
async def get_interview_report(session_id: str):
    """Generate the final detailed interview report (Step 10): all numeric
    scores pulled deterministically from Modules 3/6/7/8/9, plus an
    LLM-synthesized narrative (strengths, weaknesses, learning path,
    topics to practice, summary) grounded in that data.
    """
    try:
        session_data = load_json(f"{session_id}.json", subdir="interview_sessions")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No interview session found with id '{session_id}'.")

    session = InterviewSession(**session_data)

    try:
        resume_data = load_json(f"{session.resume_id}.json", subdir="resumes")
        jd_data = load_json(f"{session.jd_id}.json", subdir="job_descriptions")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Linked resume or job description missing: {e}")

    resume = ParsedResume(**resume_data)
    jd = ParsedJobDescription(**jd_data)

    match_result = None
    try:
        match_data = load_json(f"{session.match_id}.json", subdir="matches")
        match_result = MatchResult(**match_data)
    except FileNotFoundError:
        pass

    evaluations = _load_evaluations(session_id)
    evaluation_summary = summarize_evaluation_session(session_id, evaluations) if evaluations else None

    cv_frames = _load_cv_frames(session_id)
    cv_summary = summarize_cv_session(session_id, cv_frames) if cv_frames else None

    speech_results = _load_speech_results(session_id)
    speech_summary = summarize_speech_session(session_id, speech_results) if speech_results else None

    overall = compute_overall_score(session_id, match_result, evaluation_summary, cv_summary, speech_summary)

    try:
        report = generate_report(
            session_id, resume, jd, match_result, evaluations,
            evaluation_summary, cv_summary, speech_summary, overall,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    save_json(f"{session_id}.json", report.model_dump(), subdir="reports")

    return report
