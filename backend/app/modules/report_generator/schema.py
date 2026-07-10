"""
Pydantic schema for the final interview report (Step 10 of the workflow).

Every numeric field is pulled deterministically from earlier modules (see
generator.py) -- the LLM's role here is narrower than it might look:
synthesizing strengths/weaknesses/recommendations/summary from the
already-scored data, not inventing new numbers.
"""

from pydantic import BaseModel, Field

from app.modules.scoring_engine.schema import OverallScoreResult


class InterviewReport(BaseModel):
    session_id: str

    # --- Numeric scores (all deterministic, pulled from Modules 3/6/7/8/9) ---
    resume_match_score: float | None = None
    technical_score: float | None = None
    communication_score: float | None = None
    confidence_score: float | None = None
    eye_contact_score: float | None = None
    attention_score: float | None = None
    behavioral_score: float | None = None
    speech_quality_score: float | None = None
    overall_score: float = 0.0

    # --- Narrative sections (LLM-synthesized, grounded in the data above) ---
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)  # deterministic, from Module 3
    recommended_learning_path: list[str] = Field(default_factory=list)
    topics_to_practice: list[str] = Field(default_factory=list)
    interview_summary: str = ""

    # --- Full weighted breakdown, reused from Module 9 ---
    performance_breakdown: OverallScoreResult

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "resume_match_score": 83.0,
                "technical_score": 78.3,
                "communication_score": 88.0,
                "confidence_score": 79.5,
                "eye_contact_score": 81.0,
                "attention_score": 91.2,
                "behavioral_score": None,
                "speech_quality_score": 76.5,
                "overall_score": 82.6,
                "strengths": ["Strong hands-on Redis experience with clear technical reasoning."],
                "weaknesses": ["Limited depth on trade-off analysis against alternative caching tools."],
                "missing_skills": ["Docker"],
                "recommended_learning_path": ["Docker fundamentals and containerizing an existing API"],
                "topics_to_practice": ["System design", "Caching trade-offs"],
                "interview_summary": "The candidate demonstrated solid backend fundamentals...",
            }
        }
