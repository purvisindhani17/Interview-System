"""
Pydantic schema for the overall weighted interview score (the "Scoring"
section of the spec, distinct from Step 10's full report which will
embed this alongside strengths/weaknesses/recommendations in Module 10).

Entirely deterministic -- no LLM anywhere in this module. Every input is
already a computed aggregate from an earlier module; this module's only
job is combining them with fixed, documented weights.
"""

from pydantic import BaseModel, Field


class CategoryScore(BaseModel):
    score: float | None = None  # 0-100, None if the underlying data isn't available yet
    weight: float  # this category's weight in the overall score, per the spec
    available: bool = False


class OverallScoreResult(BaseModel):
    session_id: str
    resume_match: CategoryScore
    technical_answers: CategoryScore
    communication: CategoryScore
    computer_vision: CategoryScore
    speech_analysis: CategoryScore
    behavioral_performance: CategoryScore

    overall_score: float = 0.0
    categories_included: list[str] = Field(default_factory=list)
    categories_missing: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "resume_match": {"score": 83.0, "weight": 0.15, "available": True},
                "technical_answers": {"score": 78.3, "weight": 0.35, "available": True},
                "communication": {"score": 85.0, "weight": 0.15, "available": True},
                "computer_vision": {"score": 91.2, "weight": 0.15, "available": True},
                "speech_analysis": {"score": 76.5, "weight": 0.10, "available": True},
                "behavioral_performance": {"score": None, "weight": 0.10, "available": False},
                "overall_score": 82.9,
                "categories_included": [
                    "resume_match", "technical_answers", "communication",
                    "computer_vision", "speech_analysis",
                ],
                "categories_missing": ["behavioral_performance"],
            }
        }
