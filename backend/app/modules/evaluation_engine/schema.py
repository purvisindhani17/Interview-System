"""
Pydantic schema for per-answer LLM evaluation (Step 8 of the workflow).

Unlike Modules 6/7, this module is deliberately LLM-driven for the
per-dimension scores and reasoning -- judging technical correctness,
depth, and behavioral quality genuinely requires understanding the
content of what was said, not just its surface speech patterns. But,
consistent with the rest of this project, the *aggregate* overall_score
is still computed deterministically in code from whichever dimensions
apply (see aggregator.py) rather than asked of the LLM directly.
"""

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    score: float  # 0-100
    reasoning: str


class AnswerEvaluation(BaseModel):
    turn_number: int
    question: str = ""
    is_behavioral_question: bool = False

    # Technical dimensions -- null for purely behavioral questions.
    technical_accuracy: DimensionScore | None = None
    depth_of_knowledge: DimensionScore | None = None
    problem_solving: DimensionScore | None = None

    # Behavioral dimensions -- null for purely technical questions.
    behavioral_skills: DimensionScore | None = None
    star_method_adherence: DimensionScore | None = None

    # Always-applicable dimensions.
    communication: DimensionScore
    confidence: DimensionScore
    explanation_quality: DimensionScore

    overall_score: float = 0.0  # computed deterministically, see aggregator.py
    overall_summary: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "turn_number": 2,
                "question": "Why did you choose Redis for caching in the API Gateway project?",
                "is_behavioral_question": False,
                "technical_accuracy": {
                    "score": 85.0,
                    "reasoning": "Correctly identifies Redis's in-memory speed and TTL support as relevant to the caching use case.",
                },
                "depth_of_knowledge": {
                    "score": 70.0,
                    "reasoning": "Explains the 'what' well but doesn't discuss trade-offs against alternatives like Memcached.",
                },
                "problem_solving": {
                    "score": 80.0,
                    "reasoning": "Clear articulation of the load problem and how caching addressed it.",
                },
                "behavioral_skills": None,
                "star_method_adherence": None,
                "communication": {
                    "score": 88.0,
                    "reasoning": "Logically structured: states the problem, the solution, then the measured impact.",
                },
                "confidence": {
                    "score": 82.0,
                    "reasoning": "States claims directly without excessive hedging.",
                },
                "explanation_quality": {
                    "score": 78.0,
                    "reasoning": "Good high-level explanation; could go deeper on implementation specifics.",
                },
                "overall_score": 80.6,
                "overall_summary": "Solid technical answer demonstrating real hands-on Redis experience, with room to go deeper on trade-off analysis.",
            }
        }


class EvaluationSessionSummary(BaseModel):
    session_id: str
    turns_evaluated: int = 0
    average_technical_accuracy: float | None = None
    average_depth_of_knowledge: float | None = None
    average_problem_solving: float | None = None
    average_behavioral_skills: float | None = None
    average_star_method_adherence: float | None = None
    average_communication: float = 0.0
    average_confidence: float = 0.0
    average_explanation_quality: float = 0.0
    average_overall_score: float = 0.0
