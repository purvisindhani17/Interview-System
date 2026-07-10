"""
Pydantic schema for resume-vs-job-description comparison results.

This is Step 3 of the interview workflow. The interview engine (Step 4)
will consume `interview_focus_topics` and `missing_skills` directly when
building its interview strategy.
"""

from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    match_id: str | None = None  # populated by the API layer
    # Deterministic (scikit-learn + set/fuzzy matching), not LLM-generated --
    # kept reproducible and defensible rather than an LLM's guess at a number.
    resume_match_percentage: float = 0.0
    skill_overlap_percentage: float = 0.0
    semantic_similarity_percentage: float = 0.0

    # LLM-refined qualitative judgment, informed by the deterministic overlap above.
    strong_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_skills: list[str] = Field(default_factory=list)
    interview_focus_topics: list[str] = Field(default_factory=list)
    summary: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "resume_match_percentage": 83.0,
                "skill_overlap_percentage": 80.0,
                "semantic_similarity_percentage": 88.5,
                "strong_skills": ["Python", "FastAPI", "React"],
                "missing_skills": ["Docker", "Redis"],
                "weak_skills": ["System Design"],
                "interview_focus_topics": ["Operating Systems", "Machine Learning", "System Design"],
                "summary": "Strong technical overlap on core backend skills, but no hands-on "
                "evidence of containerization or caching tools mentioned in the JD.",
            }
        }
