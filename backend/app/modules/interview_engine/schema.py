"""
Pydantic schema for the interview plan (Step 4 of the workflow).

This plan is the "playbook" the live interview engine (Module 5) will
follow -- but Module 5 adapts dynamically based on live answers, so this
plan is a starting strategy, not a rigid script the candidate ever sees
verbatim.
"""

from pydantic import BaseModel, Field


class TopicPriority(BaseModel):
    topic: str
    importance: str = "medium"  # "high" | "medium" | "low"
    reason: str = ""


class ProjectFollowUp(BaseModel):
    project_name: str
    questions: list[str] = Field(default_factory=list)
    reason: str = ""


class InterviewPlan(BaseModel):
    plan_id: str | None = None  # populated by the API layer
    interview_strategy_summary: str = ""
    starting_difficulty: str = "medium"  # "easy" | "medium" | "hard" -- informed by match score
    opening_questions: list[str] = Field(default_factory=list)
    topic_priorities: list[TopicPriority] = Field(default_factory=list)
    project_follow_ups: list[ProjectFollowUp] = Field(default_factory=list)
    sequence: list[str] = Field(default_factory=list)
    estimated_question_count: int = 10

    class Config:
        json_schema_extra = {
            "example": {
                "interview_strategy_summary": "Candidate has strong backend fundamentals but no "
                "evidenced containerization experience. Start with core Python/FastAPI questions "
                "to confirm depth, probe the caching-layer project for Redis understanding, then "
                "spend meaningful time on Docker since it's a clear gap versus the JD.",
                "starting_difficulty": "medium",
                "opening_questions": [
                    "Walk me through your experience building REST APIs with FastAPI.",
                ],
                "topic_priorities": [
                    {"topic": "Docker / Containerization", "importance": "high", "reason": "Required by JD, no evidence in resume."},
                    {"topic": "System Design", "importance": "medium", "reason": "Not explicitly tested by resume but relevant to seniority level."},
                ],
                "project_follow_ups": [
                    {
                        "project_name": "API Gateway",
                        "questions": ["What made you choose Redis for caching here over alternatives?"],
                        "reason": "Best evidence of preferred-skill experience; worth probing depth.",
                    }
                ],
                "sequence": ["Warm-up", "Core technical skills", "Project deep-dive", "Gap probing", "Behavioral (STAR)", "Wrap-up"],
                "estimated_question_count": 10,
            }
        }


# --- Module 5: Live adaptive voice interview session ---

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


class QuickAssessment(BaseModel):
    """A lightweight, per-turn correctness signal used only to drive adaptive
    difficulty/topic routing during the live interview. This is intentionally
    NOT the full multi-dimensional evaluation (technical accuracy, STAR,
    confidence, etc.) -- that thorough grading is Module 8's job, run after
    the interview (or per-turn in parallel) rather than gating the live flow.
    """

    correctness: str = "partial"  # "correct" | "partial" | "incorrect"
    note: str = ""


class ConversationTurn(BaseModel):
    turn_number: int
    topic: str = ""
    difficulty: str = "medium"
    question: str
    question_audio_path: str | None = None
    answer_transcript: str | None = None
    answer_audio_path: str | None = None
    quick_assessment: QuickAssessment | None = None


class InterviewSession(BaseModel):
    session_id: str
    resume_id: str
    jd_id: str
    match_id: str
    plan_id: str
    current_difficulty: str = "medium"
    current_topic_index: int = 0  # index into the plan's topic_priorities
    max_questions: int = 10
    is_complete: bool = False
    history: list[ConversationTurn] = Field(default_factory=list)


class StartSessionResponse(BaseModel):
    session_id: str
    turn_number: int
    question: str
    topic: str
    difficulty: str
    question_audio_url: str | None = None
    is_complete: bool = False


class AnswerResponse(BaseModel):
    session_id: str
    transcript: str
    quick_assessment: QuickAssessment
    is_complete: bool
    next_question: str | None = None
    next_topic: str | None = None
    next_difficulty: str | None = None
    next_question_audio_url: str | None = None
